import datetime

from app.dentists.models import Dentist
from app.patients.models import Patient
from tests.conftest import auth_headers


def _patient(db_session, clinic, *, cpf="12345678901"):
    patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente Agenda",
        cpf=cpf,
        medical_record_number=f"PRONT-{cpf[-4:]}",
        birth_date=datetime.date(1990, 1, 1),
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


def _dentist(db_session, dentist_user):
    dentist = Dentist(
        user_id=dentist_user.id,
        cro_number="12345",
        cro_state="PE",
        specialty="Ortodontia",
    )
    db_session.add(dentist)
    db_session.commit()
    db_session.refresh(dentist)
    return dentist


def _payload(patient, dentist, *, minutes=30, hour=10):
    scheduled_at = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=hour, minute=0, second=0, microsecond=0
    ) + datetime.timedelta(days=2)
    return {
        "patient_id": patient.id,
        "dentist_id": dentist.id,
        "scheduled_at": scheduled_at.isoformat(),
        "duration_minutes": minutes,
    }


def test_create_rejects_overlapping_appointment(
    client, db_session, clinic, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic)
    dentist = _dentist(db_session, dentist_user)
    headers = auth_headers(client, receptionist_user.email)

    first = client.post("/api/v1/appointments", json=_payload(patient, dentist), headers=headers)
    assert first.status_code == 201, first.text

    second_payload = _payload(patient, dentist, hour=10)
    second = client.post("/api/v1/appointments", json=second_payload, headers=headers)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CONFLICTERROR"


def test_cancel_preserves_appointment_and_frees_slot(
    client, db_session, clinic, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic, cpf="12345678902")
    dentist = _dentist(db_session, dentist_user)
    headers = auth_headers(client, receptionist_user.email)
    created = client.post("/api/v1/appointments", json=_payload(patient, dentist), headers=headers)
    appointment_id = created.json()["id"]

    canceled = client.post(f"/api/v1/appointments/{appointment_id}/cancel", headers=headers)
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "CANCELED"

    replacement = client.post("/api/v1/appointments", json=_payload(patient, dentist), headers=headers)
    assert replacement.status_code == 201
    assert replacement.json()["id"] != appointment_id


def test_dentist_can_only_complete_own_appointment(
    client, db_session, clinic, dentist_user, receptionist_user
):
    patient = _patient(db_session, clinic, cpf="12345678903")
    dentist = _dentist(db_session, dentist_user)
    receptionist_headers = auth_headers(client, receptionist_user.email)
    created = client.post(
        "/api/v1/appointments",
        json=_payload(patient, dentist),
        headers=receptionist_headers,
    )

    dentist_headers = auth_headers(client, dentist_user.email)
    updated = client.patch(
        f"/api/v1/appointments/{created.json()['id']}",
        json={"status": "COMPLETED"},
        headers=dentist_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "COMPLETED"

    forbidden = client.patch(
        f"/api/v1/appointments/{created.json()['id']}",
        json={"duration_minutes": 60},
        headers=dentist_headers,
    )
    assert forbidden.status_code == 403
