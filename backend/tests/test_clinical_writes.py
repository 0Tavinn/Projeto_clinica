"""Transações e autorização HTTP das mutações clínicas já definidas."""

import datetime
from unittest.mock import patch

from sqlalchemy.dialects import postgresql

from app.appointments.models import Appointment, AppointmentStatus
from app.common.exceptions import ValidationAppError
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.access_models import ClinicalAccessGrant
from app.records.models import ClinicalEvolution, MedicalRecord
from app.records.repository import RecordRepository
from app.security.roles import Role
from app.users.models import Clinic
from tests.conftest import _make_user, auth_headers


def _confirmed_case(db_session, clinic, dentist_user, receptionist_user):
    now = datetime.datetime.now(datetime.timezone.utc)
    patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente de teste clínico",
        cpf="12345678901",
        medical_record_number="PRONT-ESCRITA",
        birth_date=datetime.date(1990, 1, 1),
    )
    dentist = Dentist(user_id=dentist_user.id, cro_number="12345", cro_state="PE")
    db_session.add_all([patient, dentist])
    db_session.flush()

    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        scheduled_at=now + datetime.timedelta(days=1),
        duration_minutes=30,
        status=AppointmentStatus.CONFIRMED,
    )
    db_session.add(appointment)
    db_session.flush()
    db_session.add(
        ClinicalAccessGrant(
            appointment_id=appointment.id,
            clinic_id=clinic.id,
            patient_id=patient.id,
            dentist_id=dentist.id,
            granted_at=now,
            confirmed_by_user_id=receptionist_user.id,
        )
    )
    db_session.commit()
    return patient, dentist, appointment


def _draft_payload(patient_id: int, appointment_id: int) -> dict:
    return {
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "description": "Observação clínica reservada",
        "procedure_performed": None,
        "notes": None,
    }


def test_opening_and_draft_rollback_together(
    client, db_session, clinic, dentist_user, receptionist_user
):
    patient, _, appointment = _confirmed_case(
        db_session, clinic, dentist_user, receptionist_user
    )
    headers = auth_headers(client, dentist_user.email)

    # A falha vem depois do INSERT do prontuário e antes do commit da evolução.
    with patch.object(
        RecordRepository,
        "add_evolution",
        side_effect=ValidationAppError("Falha simulada."),
    ):
        response = client.post(
            "/api/v1/patients/evolutions",
            json=_draft_payload(patient.id, appointment.id),
            headers=headers,
        )
    assert response.status_code == 422, response.text

    db_session.expire_all()
    assert db_session.query(MedicalRecord).filter_by(patient_id=patient.id).count() == 0
    assert db_session.query(ClinicalEvolution).count() == 0


def test_draft_opens_record_once_and_duplicate_appointment_returns_conflict(
    client, db_session, clinic, dentist_user, receptionist_user
):
    patient, dentist, appointment = _confirmed_case(
        db_session, clinic, dentist_user, receptionist_user
    )
    headers = auth_headers(client, dentist_user.email)
    payload = _draft_payload(patient.id, appointment.id)
    payload["dentist_id"] = 99999  # O cliente não escolhe a autoria.

    created = client.post("/api/v1/patients/evolutions", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    assert created.json()["dentist"]["id"] == dentist.id

    duplicate = client.post("/api/v1/patients/evolutions", json=payload, headers=headers)
    assert duplicate.status_code == 409, duplicate.text
    assert duplicate.json()["error"]["message"] == "A consulta já possui evolução clínica."

    db_session.expire_all()
    assert db_session.query(MedicalRecord).filter_by(patient_id=patient.id).count() == 1
    assert db_session.query(ClinicalEvolution).filter_by(appointment_id=appointment.id).count() == 1


def test_draft_rejects_appointment_with_other_patient_or_dentist(
    client, db_session, clinic, dentist_user, receptionist_user
):
    patient, dentist, _ = _confirmed_case(
        db_session, clinic, dentist_user, receptionist_user
    )
    other_patient = Patient(
        clinic_id=clinic.id,
        full_name="Outro paciente",
        cpf="12345678902",
        medical_record_number="PRONT-OUTRO",
        birth_date=datetime.date(1991, 1, 1),
    )
    other_user = _make_user(
        db_session,
        clinic,
        email="outro.clinico@clinica.example.com",
        cpf="00000000033",
        role=Role.DENTIST,
    )
    other_dentist = Dentist(user_id=other_user.id, cro_number="54321", cro_state="PE")
    db_session.add_all([other_patient, other_dentist])
    db_session.flush()
    now = datetime.datetime.now(datetime.timezone.utc)
    appointments = [
        Appointment(
            clinic_id=clinic.id,
            patient_id=other_patient.id,
            dentist_id=dentist.id,
            scheduled_at=now + datetime.timedelta(days=2),
            duration_minutes=30,
            status=AppointmentStatus.SCHEDULED,
        ),
        Appointment(
            clinic_id=clinic.id,
            patient_id=patient.id,
            dentist_id=other_dentist.id,
            scheduled_at=now + datetime.timedelta(days=3),
            duration_minutes=30,
            status=AppointmentStatus.SCHEDULED,
        ),
    ]
    db_session.add_all(appointments)
    db_session.commit()
    headers = auth_headers(client, dentist_user.email)

    for appointment in appointments:
        response = client.post(
            "/api/v1/patients/evolutions",
            json=_draft_payload(patient.id, appointment.id),
            headers=headers,
        )
        assert response.status_code == 404, response.text

    db_session.expire_all()
    assert db_session.query(MedicalRecord).filter_by(patient_id=patient.id).count() == 0
    assert db_session.query(ClinicalEvolution).count() == 0


def test_only_author_mutates_draft_and_finalized_text_stays_unchanged(
    client, db_session, clinic, dentist_user, receptionist_user
):
    patient, _, appointment = _confirmed_case(
        db_session, clinic, dentist_user, receptionist_user
    )
    other_user = _make_user(
        db_session,
        clinic,
        email="segundo.clinico@clinica.example.com",
        cpf="00000000034",
        role=Role.DENTIST,
    )
    other_dentist = Dentist(user_id=other_user.id, cro_number="67890", cro_state="PE")
    db_session.add(other_dentist)
    db_session.flush()
    other_appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=other_dentist.id,
        scheduled_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2),
        duration_minutes=30,
        status=AppointmentStatus.CONFIRMED,
    )
    db_session.add(other_appointment)
    db_session.flush()
    db_session.add(
        ClinicalAccessGrant(
            appointment_id=other_appointment.id,
            clinic_id=clinic.id,
            patient_id=patient.id,
            dentist_id=other_dentist.id,
            granted_at=datetime.datetime.now(datetime.timezone.utc),
            confirmed_by_user_id=receptionist_user.id,
        )
    )
    db_session.commit()

    own_headers = auth_headers(client, dentist_user.email)
    created = client.post(
        "/api/v1/patients/evolutions",
        json=_draft_payload(patient.id, appointment.id),
        headers=own_headers,
    )
    assert created.status_code == 201, created.text
    evolution_id = created.json()["id"]
    other_headers = auth_headers(client, other_user.email)

    denied_edit = client.patch(
        f"/api/v1/patients/evolutions/{evolution_id}/draft",
        json={"description": "Tentativa indevida"},
        headers=other_headers,
    )
    denied_finalize = client.post(
        f"/api/v1/patients/evolutions/{evolution_id}/finalize",
        headers=other_headers,
    )
    for response in (denied_edit, denied_finalize):
        assert response.status_code == 403, response.text
        assert "Observação clínica reservada" not in response.text

    finalized = client.post(
        f"/api/v1/patients/evolutions/{evolution_id}/finalize",
        headers=own_headers,
    )
    assert finalized.status_code == 200, finalized.text
    assert finalized.json()["status"] == "FINALIZED"

    immutable = client.patch(
        f"/api/v1/patients/evolutions/{evolution_id}/draft",
        json={"description": "Alteração após finalização"},
        headers=own_headers,
    )
    assert immutable.status_code == 422, immutable.text
    assert immutable.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
    db_session.expire_all()
    stored = db_session.get(ClinicalEvolution, evolution_id)
    assert stored.description == "Observação clínica reservada"
    assert stored.status == "FINALIZED"


def test_mutation_rechecks_active_user_professional_and_clinic(
    client, db_session, clinic, dentist_user, receptionist_user
):
    patient, dentist, appointment = _confirmed_case(
        db_session, clinic, dentist_user, receptionist_user
    )
    headers = auth_headers(client, dentist_user.email)
    created = client.post(
        "/api/v1/patients/evolutions",
        json=_draft_payload(patient.id, appointment.id),
        headers=headers,
    )
    assert created.status_code == 201, created.text
    evolution_id = created.json()["id"]
    url = f"/api/v1/patients/evolutions/{evolution_id}/draft"

    dentist_user.is_active = False
    db_session.commit()
    inactive = client.patch(url, json={"description": "Mudança indevida"}, headers=headers)
    assert inactive.status_code == 401, inactive.text

    dentist_user.is_active = True
    dentist.cro_number = "  "
    db_session.commit()
    no_profile = client.patch(url, json={"description": "Mudança indevida"}, headers=headers)
    assert no_profile.status_code == 403, no_profile.text

    dentist.cro_number = "12345"
    clinic.is_active = False
    db_session.commit()
    inactive_clinic = client.patch(url, json={"description": "Mudança indevida"}, headers=headers)
    assert inactive_clinic.status_code == 403, inactive_clinic.text

    db_session.expire_all()
    assert db_session.get(ClinicalEvolution, evolution_id).description == (
        "Observação clínica reservada"
    )


def test_other_clinic_cannot_read_or_write_clinical_content(
    client, db_session, clinic, dentist_user, receptionist_user
):
    patient, _, appointment = _confirmed_case(
        db_session, clinic, dentist_user, receptionist_user
    )
    own_headers = auth_headers(client, dentist_user.email)
    opened = client.get(f"/api/v1/patients/{patient.id}/record", headers=own_headers)
    assert opened.status_code == 200, opened.text
    record = db_session.get(MedicalRecord, opened.json()["id"])
    record.general_notes = "SIGILO_ENTRE_CLINICAS"
    db_session.commit()

    other_clinic = Clinic(
        name="Outra clínica",
        cnpj="00000000000272",
        email="outra-clinica@clinica.example.com",
    )
    db_session.add(other_clinic)
    db_session.commit()
    other_user = _make_user(
        db_session,
        other_clinic,
        email="dentista.externo@clinica.example.com",
        cpf="00000000035",
        role=Role.DENTIST,
    )
    db_session.add(Dentist(user_id=other_user.id, cro_number="11223", cro_state="PE"))
    db_session.commit()
    other_headers = auth_headers(client, other_user.email)

    requests = (
        client.get(f"/api/v1/patients/{patient.id}/record", headers=other_headers),
        client.get(f"/api/v1/patients/{patient.id}/evolutions", headers=other_headers),
        client.post(
            "/api/v1/patients/evolutions",
            json=_draft_payload(patient.id, appointment.id),
            headers=other_headers,
        ),
    )
    for response in requests:
        assert response.status_code == 403, response.text
        assert "SIGILO_ENTRE_CLINICAS" not in response.text


def test_evolution_lock_targets_only_its_table():
    class Capture:
        def execute(self, statement):
            self.statement = statement
            return self

        def scalar_one_or_none(self):
            return None

    capture = Capture()
    assert RecordRepository(capture).get_evolution_for_update(1) is None
    sql = str(capture.statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE OF clinical_evolutions" in sql
    assert "JOIN" not in sql
