"""Testes HTTP da visibilidade do conteúdo clínico."""

import datetime

from app.appointments.models import Appointment, AppointmentStatus
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.access_models import ClinicalAccessGrant
from app.records.models import ClinicalEvolution, MedicalRecord
from app.security.hashing import hash_password
from app.security.roles import Role
from app.users.models import User
from tests.conftest import auth_headers


def test_authorized_dentists_share_finalized_but_not_drafts(
    client, db_session, clinic, dentist_user, receptionist_user
):
    now = datetime.datetime.now(datetime.timezone.utc)
    second_user = User(
        clinic_id=clinic.id,
        full_name="Segundo Dentista",
        email="segundo@clinica.example.com",
        password_hash=hash_password("Senha@1234"),
        cpf="00000000004",
        role=Role.DENTIST,
        is_active=True,
    )
    patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente de teste",
        cpf="12345678901",
        medical_record_number="PRONT-HTTP-ACESSO",
        birth_date=datetime.date(1990, 1, 1),
    )
    db_session.add_all([second_user, patient])
    db_session.flush()

    first_dentist = Dentist(
        user_id=dentist_user.id,
        cro_number="12345",
        cro_state="PE",
    )
    second_dentist = Dentist(
        user_id=second_user.id,
        cro_number="67890",
        cro_state="PE",
    )
    db_session.add_all([first_dentist, second_dentist])
    db_session.flush()

    # As duas confirmações sustentam preparação para a mesma paciente.
    for dentist, days_ahead in ((first_dentist, 1), (second_dentist, 2)):
        appointment = Appointment(
            clinic_id=clinic.id,
            patient_id=patient.id,
            dentist_id=dentist.id,
            scheduled_at=now + datetime.timedelta(days=days_ahead),
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

    record = MedicalRecord(
        patient_id=patient.id,
        general_notes="Observação clínica reservada",
    )
    db_session.add(record)
    db_session.flush()

    for author, status, description in (
        (first_dentist, "DRAFT", "Rascunho próprio"),
        (second_dentist, "DRAFT", "Rascunho reservado"),
        (second_dentist, "FINALIZED", "Histórico finalizado"),
    ):
        db_session.add(
            ClinicalEvolution(
                medical_record_id=record.id,
                dentist_id=author.id,
                status=status,
                description=description,
                finalized_at=now if status == "FINALIZED" else None,
            )
        )
    db_session.commit()

    url = f"/api/v1/patients/{patient.id}/evolutions"
    first_response = client.get(
        url,
        headers=auth_headers(client, dentist_user.email),
    )
    assert first_response.status_code == 200, first_response.text
    assert {item["description"] for item in first_response.json()} == {
        "Rascunho próprio",
        "Histórico finalizado",
    }
    assert "Rascunho reservado" not in first_response.text

    second_response = client.get(
        url,
        headers=auth_headers(client, second_user.email),
    )
    assert second_response.status_code == 200, second_response.text
    assert {item["description"] for item in second_response.json()} == {
        "Rascunho reservado",
        "Histórico finalizado",
    }
    assert "Rascunho próprio" not in second_response.text


def test_dentist_without_origin_cannot_read_or_open_record(
    client, db_session, clinic, dentist_user
):
    now = datetime.datetime.now(datetime.timezone.utc)
    dentist = Dentist(
        user_id=dentist_user.id,
        cro_number="12345",
        cro_state="PE",
    )
    existing_patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente com conteúdo",
        cpf="12345678901",
        medical_record_number="PRONT-COM-CONTEUDO",
        birth_date=datetime.date(1990, 1, 1),
    )
    unopened_patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente sem prontuário",
        cpf="98765432100",
        medical_record_number="PRONT-SEM-ABERTURA",
        birth_date=datetime.date(1991, 1, 1),
    )
    db_session.add_all([dentist, existing_patient, unopened_patient])
    db_session.flush()

    record = MedicalRecord(
        patient_id=existing_patient.id,
        general_notes="SIGILO_NOTAS_GERAIS",
    )
    db_session.add(record)
    db_session.flush()
    db_session.add(
        ClinicalEvolution(
            medical_record_id=record.id,
            dentist_id=dentist.id,
            status="FINALIZED",
            description="SIGILO_EVOLUCAO",
            finalized_at=now,
        )
    )
    db_session.commit()

    headers = auth_headers(client, dentist_user.email)
    for patient_id, suffix in (
        (existing_patient.id, "record"),
        (existing_patient.id, "evolutions"),
        (unopened_patient.id, "record"),
    ):
        response = client.get(
            f"/api/v1/patients/{patient_id}/{suffix}",
            headers=headers,
        )
        assert response.status_code == 403, response.text
        assert "error" in response.json()
        assert "SIGILO_NOTAS_GERAIS" not in response.text
        assert "SIGILO_EVOLUCAO" not in response.text

    db_session.expire_all()
    assert (
        db_session.query(MedicalRecord)
        .filter(MedicalRecord.patient_id == unopened_patient.id)
        .count()
        == 0
    )


def test_administration_and_reception_cannot_read_clinical_content(
    client,
    db_session,
    clinic,
    administrator_user,
    receptionist_user,
    dentist_user,
):
    now = datetime.datetime.now(datetime.timezone.utc)
    patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente com conteúdo",
        cpf="12345678901",
        medical_record_number="PRONT-PERFIS",
        birth_date=datetime.date(1990, 1, 1),
    )
    dentist = Dentist(
        user_id=dentist_user.id,
        cro_number="12345",
        cro_state="PE",
    )
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

    record = MedicalRecord(
        patient_id=patient.id,
        general_notes="SIGILO_NOTAS_POR_PERFIL",
    )
    db_session.add(record)
    db_session.flush()
    db_session.add(
        ClinicalEvolution(
            medical_record_id=record.id,
            dentist_id=dentist.id,
            status="FINALIZED",
            description="SIGILO_EVOLUCAO_POR_PERFIL",
            finalized_at=now,
        )
    )
    db_session.commit()

    for actor in (administrator_user, receptionist_user):
        headers = auth_headers(client, actor.email)
        for suffix in ("record", "evolutions"):
            response = client.get(
                f"/api/v1/patients/{patient.id}/{suffix}",
                headers=headers,
            )
            assert response.status_code == 403, response.text
            assert "error" in response.json()
            assert "SIGILO_NOTAS_POR_PERFIL" not in response.text
            assert "SIGILO_EVOLUCAO_POR_PERFIL" not in response.text


def test_confirmed_dentist_get_opens_record_once_under_current_contract(
    client, db_session, clinic, dentist_user, receptionist_user
):
    now = datetime.datetime.now(datetime.timezone.utc)
    patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente aguardando prontuário",
        cpf="12345678901",
        medical_record_number="PRONT-ABERTURA-ATUAL",
        birth_date=datetime.date(1990, 1, 1),
    )
    dentist = Dentist(
        user_id=dentist_user.id,
        cro_number="12345",
        cro_state="PE",
    )
    db_session.add_all([patient, dentist])
    db_session.flush()

    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        scheduled_at=now + datetime.timedelta(days=1),
        duration_minutes=30,
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(appointment)
    db_session.commit()

    assert (
        db_session.query(MedicalRecord)
        .filter(MedicalRecord.patient_id == patient.id)
        .count()
        == 0
    )

    confirmed = client.patch(
        f"/api/v1/appointments/{appointment.id}/status",
        json={"status": "CONFIRMED"},
        headers=auth_headers(client, receptionist_user.email),
    )
    assert confirmed.status_code == 200, confirmed.text

    url = f"/api/v1/patients/{patient.id}/record"
    dentist_headers = auth_headers(client, dentist_user.email)
    first = client.get(url, headers=dentist_headers)
    assert first.status_code == 200, first.text
    assert first.json()["patient_id"] == patient.id
    assert first.json()["general_notes"] is None
    record_id = first.json()["id"]

    db_session.expire_all()
    record = (
        db_session.query(MedicalRecord)
        .filter(MedicalRecord.patient_id == patient.id)
        .one()
    )
    assert record.id == record_id
    record.general_notes = "SIGILO_NOTAS_AUTORIZADAS"
    db_session.commit()

    second = client.get(url, headers=dentist_headers)
    assert second.status_code == 200, second.text
    assert second.json()["id"] == record_id
    assert second.json()["general_notes"] == "SIGILO_NOTAS_AUTORIZADAS"
    assert (
        db_session.query(MedicalRecord)
        .filter(MedicalRecord.patient_id == patient.id)
        .count()
        == 1
    )