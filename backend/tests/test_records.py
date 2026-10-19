"""Contrato clínico provisório e isolamento dos registros."""
import datetime

from app.appointments.models import Appointment, AppointmentStatus
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.models import ClinicalEvolution, MedicalRecord
from app.security.roles import Role
from app.users.models import Clinic
from tests.conftest import _make_user, auth_headers


def _patient(db, clinic, *, cpf="12345678901"):
    patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente Clínico",
        cpf=cpf,
        medical_record_number=f"CLIN-{cpf[-4:]}",
        birth_date=datetime.date(1990, 1, 1),
        is_active=True,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _dentist(db, user, *, cro="12345"):
    dentist = Dentist(user_id=user.id, cro_number=cro, cro_state="PE")
    db.add(dentist)
    db.commit()
    db.refresh(dentist)
    return dentist


def _appointment(db, clinic, patient, dentist, *, status=AppointmentStatus.COMPLETED):
    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        scheduled_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1),
        duration_minutes=30,
        status=status,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def _record(db, patient, *, notes="Observação restrita"):
    record = MedicalRecord(patient_id=patient.id, general_notes=notes)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_clinical_routes_are_registered_under_api_prefix(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "get" in paths["/api/v1/patients/{patient_id}/record"]
    assert "get" in paths["/api/v1/patients/{patient_id}/evolutions"]
    assert "post" in paths["/api/v1/patients/evolutions"]
    assert "patch" in paths["/api/v1/patients/evolutions/{evolution_id}/draft"]
    assert "post" in paths["/api/v1/patients/evolutions/{evolution_id}/finalize"]


def test_record_read_requires_assigned_appointment_and_does_not_create_record(
    client, db_session, clinic, dentist_user
):
    patient = _patient(db_session, clinic)
    dentist = _dentist(db_session, dentist_user)
    headers = auth_headers(client, dentist_user.email)
    path = f"/api/v1/patients/{patient.id}/record"

    assert client.get(path, headers=headers).status_code == 403
    _appointment(db_session, clinic, patient, dentist, status=AppointmentStatus.SCHEDULED)
    response = client.get(path, headers=headers)
    assert response.status_code == 404
    assert db_session.query(MedicalRecord).count() == 0

    record = _record(db_session, patient)
    response = client.get(path, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == record.id
    assert response.json()["general_notes"] is None


def test_roles_and_other_clinic_cannot_read_clinical_content(
    client, db_session, clinic, administrator_user, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic)
    dentist = _dentist(db_session, dentist_user)
    _appointment(db_session, clinic, patient, dentist)
    _record(db_session, patient)
    path = f"/api/v1/patients/{patient.id}/record"
    for user in (administrator_user, receptionist_user):
        assert client.get(path, headers=auth_headers(client, user.email)).status_code == 403

    other_clinic = Clinic(
        name="Outra Clínica", cnpj="00000000000272", email="outra@clinica.example.com"
    )
    db_session.add(other_clinic)
    db_session.commit()
    db_session.refresh(other_clinic)
    outsider = _make_user(
        db_session, other_clinic, email="outro@clinica.example.com",
        cpf="00000000030", role=Role.DENTIST,
    )
    _dentist(db_session, outsider, cro="54321")
    assert client.get(path, headers=auth_headers(client, outsider.email)).status_code == 404


def test_draft_requires_matching_completed_appointment_and_preserves_author(
    client, db_session, clinic, dentist_user
):
    patient = _patient(db_session, clinic)
    dentist = _dentist(db_session, dentist_user)
    _record(db_session, patient)
    scheduled = _appointment(
        db_session, clinic, patient, dentist, status=AppointmentStatus.SCHEDULED
    )
    headers = auth_headers(client, dentist_user.email)
    path = "/api/v1/patients/evolutions"
    payload = {"patient_id": patient.id, "description": "Avaliação inicial"}

    assert client.post(path, headers=headers, json=payload).status_code == 422
    assert client.post(
        path, headers=headers, json={**payload, "appointment_id": scheduled.id}
    ).status_code == 403

    scheduled.status = AppointmentStatus.COMPLETED
    db_session.commit()
    created = client.post(
        path, headers=headers, json={**payload, "appointment_id": scheduled.id}
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "DRAFT"
    assert body["dentist"]["id"] == dentist.id
    assert body["dentist"]["cro_number"] == dentist.cro_number
    assert body["dentist"]["full_name"] == dentist_user.full_name
    assert client.post(
        path, headers=headers, json={**payload, "appointment_id": scheduled.id}
    ).status_code == 409
    assert db_session.query(ClinicalEvolution).count() == 1

    updated = client.patch(
        f"{path}/{body['id']}/draft", headers=headers, json={"description": "Texto revisto"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["description"] == "Texto revisto"
    finalized = client.post(f"{path}/{body['id']}/finalize", headers=headers)
    assert finalized.status_code == 200, finalized.text
    assert finalized.json()["status"] == "FINALIZED"
    assert finalized.json()["finalized_at"] is not None
    assert client.patch(
        f"{path}/{body['id']}/draft", headers=headers, json={"description": "Alteração"}
    ).status_code == 422
    assert client.post(f"{path}/{body['id']}/finalize", headers=headers).status_code == 422
    assert db_session.get(ClinicalEvolution, body["id"]).description == "Texto revisto"


def test_other_dentist_sees_only_own_linked_evolutions(
    client, db_session, clinic, dentist_user
):
    patient = _patient(db_session, clinic)
    first_dentist = _dentist(db_session, dentist_user)
    record = _record(db_session, patient)
    first_appointment = _appointment(db_session, clinic, patient, first_dentist)
    evolution = ClinicalEvolution(
        medical_record_id=record.id, dentist_id=first_dentist.id,
        appointment_id=first_appointment.id, description="Conteúdo do autor", status="FINALIZED",
        finalized_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(evolution)
    db_session.commit()
    db_session.refresh(evolution)

    other_user = _make_user(
        db_session, clinic, email="segundo@clinica.example.com",
        cpf="00000000031", role=Role.DENTIST,
    )
    other_dentist = _dentist(db_session, other_user, cro="54321")
    _appointment(db_session, clinic, patient, other_dentist)
    headers = auth_headers(client, other_user.email)
    listed = client.get(f"/api/v1/patients/{patient.id}/evolutions", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json() == []
    assert client.patch(
        f"/api/v1/patients/evolutions/{evolution.id}/draft",
        headers=headers, json={"description": "Tentativa"},
    ).status_code == 404
    assert client.post(
        "/api/v1/patients/evolutions",
        headers=headers,
        json={
            "patient_id": patient.id,
            "appointment_id": first_appointment.id,
            "description": "Tentativa com consulta de outro dentista",
        },
    ).status_code == 403
    assert db_session.query(ClinicalEvolution).count() == 1


def test_draft_rejects_appointment_for_another_patient(
    client, db_session, clinic, dentist_user
):
    patient = _patient(db_session, clinic)
    other_patient = _patient(db_session, clinic, cpf="12345678902")
    dentist = _dentist(db_session, dentist_user)
    _record(db_session, patient)
    appointment = _appointment(db_session, clinic, other_patient, dentist)
    response = client.post(
        "/api/v1/patients/evolutions",
        headers=auth_headers(client, dentist_user.email),
        json={
            "patient_id": patient.id,
            "appointment_id": appointment.id,
            "description": "Registro incompatível",
        },
    )
    assert response.status_code == 403
    assert db_session.query(ClinicalEvolution).count() == 0
