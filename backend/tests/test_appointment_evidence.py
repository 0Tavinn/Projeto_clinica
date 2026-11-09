"""Testes HTTP da evidência vinculada à Agenda."""

import datetime
from unittest.mock import patch

import pytest

from app.appointments.models import Appointment, AppointmentStatus
from app.appointments.repository import AppointmentRepository
from app.common.exceptions import ValidationAppError
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.access_models import ClinicalAccessGrant
from tests.conftest import auth_headers


def _scheduled_appointment(db_session, clinic, dentist_user) -> Appointment:
    patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente de teste",
        cpf="12345678901",
        medical_record_number="PRONT-EVIDENCIA",
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
        scheduled_at=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=1),
        duration_minutes=30,
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    return appointment


@pytest.mark.parametrize("route_suffix", ["", "/status"])
def test_confirmation_persists_and_survives_cancel(
    client, db_session, clinic, receptionist_user, dentist_user, route_suffix
):
    appointment = _scheduled_appointment(db_session, clinic, dentist_user)
    headers = auth_headers(client, receptionist_user.email)

    confirmed = client.patch(
        f"/api/v1/appointments/{appointment.id}{route_suffix}",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "CONFIRMED"

    db_session.expire_all()
    grant = db_session.get(ClinicalAccessGrant, appointment.id)
    assert grant is not None
    assert (
        grant.clinic_id,
        grant.patient_id,
        grant.dentist_id,
    ) == (
        appointment.clinic_id,
        appointment.patient_id,
        appointment.dentist_id,
    )
    assert grant.confirmed_by_user_id == receptionist_user.id
    assert grant.granted_at is not None
    assert grant.care_occurred_at is None
    assert grant.care_recorded_at is None
    assert grant.care_recorded_by_user_id is None
    assert db_session.get(Appointment, appointment.id).status is AppointmentStatus.CONFIRMED

    canceled = client.post(
        f"/api/v1/appointments/{appointment.id}/cancel",
        headers=headers,
    )
    assert canceled.status_code == 200, canceled.text
    db_session.expire_all()
    assert db_session.get(Appointment, appointment.id).status is AppointmentStatus.CANCELED
    assert db_session.get(ClinicalAccessGrant, appointment.id).confirmed_by_user_id == (
        receptionist_user.id
    )


def test_legacy_grant_is_not_promoted(
    client, db_session, clinic, receptionist_user, dentist_user
):
    appointment = _scheduled_appointment(db_session, clinic, dentist_user)
    db_session.add(
        ClinicalAccessGrant(
            appointment_id=appointment.id,
            clinic_id=appointment.clinic_id,
            patient_id=appointment.patient_id,
            dentist_id=appointment.dentist_id,
            granted_at=datetime.datetime.now(datetime.timezone.utc),
            confirmed_by_user_id=None,
        )
    )
    db_session.commit()
    headers = auth_headers(client, receptionist_user.email)

    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/status",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert response.status_code == 409, response.text
    assert "error" in response.json()

    db_session.expire_all()
    assert db_session.get(Appointment, appointment.id).status is AppointmentStatus.SCHEDULED
    assert db_session.get(ClinicalAccessGrant, appointment.id).confirmed_by_user_id is None


def test_confirmation_rolls_back_status_and_evidence(
    client, db_session, clinic, receptionist_user, dentist_user
):
    appointment = _scheduled_appointment(db_session, clinic, dentist_user)
    headers = auth_headers(client, receptionist_user.email)

    # A falha ocorre depois de preparar situação e evidência, antes do commit.
    with patch.object(
        AppointmentRepository,
        "save",
        side_effect=ValidationAppError("Falha simulada."),
    ):
        response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "CONFIRMED"},
            headers=headers,
        )
    assert response.status_code == 422, response.text

    db_session.expire_all()
    assert db_session.get(Appointment, appointment.id).status is AppointmentStatus.SCHEDULED
    assert db_session.get(ClinicalAccessGrant, appointment.id) is None

@pytest.mark.parametrize("route_suffix", ["", "/status"])
def test_responsible_dentist_completes_with_care_evidence(
    client, db_session, clinic, receptionist_user, dentist_user, route_suffix
):
    appointment = _scheduled_appointment(db_session, clinic, dentist_user)
    appointment_id = appointment.id

    # Representa uma consulta cujo horário já passou.
    appointment.scheduled_at = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    )
    db_session.commit()

    confirmed = client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={"status": "CONFIRMED"},
        headers=auth_headers(client, receptionist_user.email),
    )
    assert confirmed.status_code == 200, confirmed.text

    occurred_at = (
        datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        - datetime.timedelta(minutes=5)
    )
    completed = client.patch(
        f"/api/v1/appointments/{appointment_id}{route_suffix}",
        json={
            "status": "COMPLETED",
            "care_occurred_at": occurred_at.isoformat(),
        },
        headers=auth_headers(client, dentist_user.email),
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"

    db_session.expire_all()
    assert db_session.get(Appointment, appointment_id).status is AppointmentStatus.COMPLETED

    grant = db_session.get(ClinicalAccessGrant, appointment_id)
    assert grant is not None
    assert grant.confirmed_by_user_id == receptionist_user.id
    assert grant.care_occurred_at.replace(tzinfo=datetime.timezone.utc) == occurred_at
    assert grant.care_recorded_at is not None
    assert grant.care_recorded_by_user_id == dentist_user.id

@pytest.mark.parametrize("route_suffix", ["", "/status"])
@pytest.mark.parametrize("actor", ["administrator", "receptionist"])
def test_administration_and_reception_cannot_complete_care(
    client,
    db_session,
    clinic,
    administrator_user,
    receptionist_user,
    dentist_user,
    route_suffix,
    actor,
):
    appointment = _scheduled_appointment(db_session, clinic, dentist_user)
    appointment_id = appointment.id
    appointment.scheduled_at = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    )
    db_session.commit()

    confirmed = client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={"status": "CONFIRMED"},
        headers=auth_headers(client, receptionist_user.email),
    )
    assert confirmed.status_code == 200, confirmed.text

    actor_user = (
        administrator_user if actor == "administrator" else receptionist_user
    )
    occurred_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        minutes=5
    )
    response = client.patch(
        f"/api/v1/appointments/{appointment_id}{route_suffix}",
        json={
            "status": "COMPLETED",
            "care_occurred_at": occurred_at.isoformat(),
        },
        headers=auth_headers(client, actor_user.email),
    )
    assert response.status_code == 403, response.text
    assert "error" in response.json()

    db_session.expire_all()
    assert db_session.get(Appointment, appointment_id).status is AppointmentStatus.CONFIRMED
    grant = db_session.get(ClinicalAccessGrant, appointment_id)
    assert grant is not None
    assert grant.care_occurred_at is None
    assert grant.care_recorded_at is None
    assert grant.care_recorded_by_user_id is None

@pytest.mark.parametrize("route_suffix", ["", "/status"])
@pytest.mark.parametrize(
    "initial_status",
    [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED],
)
def test_completion_requires_confirmation_and_valid_transition(
    client, db_session, clinic, dentist_user, route_suffix, initial_status
):
    appointment = _scheduled_appointment(db_session, clinic, dentist_user)
    appointment_id = appointment.id

    # CONFIRMED sem concessão representa um registro legado sem procedência.
    appointment.status = initial_status
    appointment.scheduled_at = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    )
    db_session.commit()

    occurred_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        minutes=5
    )
    response = client.patch(
        f"/api/v1/appointments/{appointment_id}{route_suffix}",
        json={
            "status": "COMPLETED",
            "care_occurred_at": occurred_at.isoformat(),
        },
        headers=auth_headers(client, dentist_user.email),
    )
    assert response.status_code == 422, response.text
    assert "error" in response.json()

    db_session.expire_all()
    assert db_session.get(Appointment, appointment_id).status is initial_status
    assert db_session.get(ClinicalAccessGrant, appointment_id) is None
