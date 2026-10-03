import datetime

from sqlalchemy.exc import IntegrityError

from app.appointments.models import Appointment, AppointmentStatus
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.security.roles import Role
from app.users.models import Clinic
from tests.conftest import _make_user, auth_headers


def _patient(db_session, clinic, *, cpf="12345678901", active=True):
    patient = Patient(
        clinic_id=clinic.id,
        full_name=f"Paciente {cpf[-4:]}",
        cpf=cpf,
        medical_record_number=f"PRONT-{cpf[-4:]}",
        birth_date=datetime.date(1990, 1, 1),
        is_active=active,
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


def _dentist(db_session, dentist_user, *, cro="12345"):
    dentist = Dentist(
        user_id=dentist_user.id,
        cro_number=cro,
        cro_state="PE",
        specialty="Ortodontia",
    )
    db_session.add(dentist)
    db_session.commit()
    db_session.refresh(dentist)
    return dentist


def _when(*, days=2, hours=0):
    return (
        datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=days, hours=hours)
    ).replace(microsecond=0)


def _payload(patient, dentist, *, scheduled_at=None, minutes=30):
    return {
        "patient_id": patient.id,
        "dentist_id": dentist.id,
        "scheduled_at": (scheduled_at or _when()).isoformat(),
        "duration_minutes": minutes,
        "notes": "Consulta de teste",
    }


def _appointment(
    db_session,
    clinic,
    patient,
    dentist,
    *,
    scheduled_at=None,
    status=AppointmentStatus.SCHEDULED,
):
    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        scheduled_at=scheduled_at or _when(),
        duration_minutes=30,
        notes="Consulta criada diretamente no teste",
        status=status,
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    return appointment


def test_create_list_filter_and_detail(
    client, db_session, clinic, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic)
    dentist = _dentist(db_session, dentist_user)
    headers = auth_headers(client, receptionist_user.email)
    scheduled_at = _when()

    created = client.post(
        "/api/v1/appointments",
        json=_payload(patient, dentist, scheduled_at=scheduled_at),
        headers=headers,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "SCHEDULED"
    assert body["patient_name"] == patient.full_name
    assert body["dentist_name"] == dentist_user.full_name
    assert "scheduled_period" not in body

    listed = client.get(
        "/api/v1/appointments",
        params={
            "start_date": (scheduled_at - datetime.timedelta(hours=1)).isoformat(),
            "end_date": (scheduled_at + datetime.timedelta(hours=1)).isoformat(),
            "dentist_id": dentist.id,
            "patient_id": patient.id,
            "status": "SCHEDULED",
        },
        headers=headers,
    )
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in listed.json()] == [body["id"]]

    details = client.get(f"/api/v1/appointments/{body['id']}", headers=headers)
    assert details.status_code == 200
    assert details.json()["patient_name"] == patient.full_name

    invalid_period = client.get(
        "/api/v1/appointments",
        params={
            "start_date": scheduled_at.isoformat(),
            "end_date": (scheduled_at - datetime.timedelta(minutes=1)).isoformat(),
        },
        headers=headers,
    )
    assert invalid_period.status_code == 422


def test_update_and_reschedule_rejects_explicit_nulls(
    client, db_session, clinic, administrator_user, dentist_user
):
    patient = _patient(db_session, clinic, cpf="12345678902")
    dentist = _dentist(db_session, dentist_user)
    appointment = _appointment(db_session, clinic, patient, dentist)
    headers = auth_headers(client, administrator_user.email)
    new_time = _when(days=3)

    updated = client.patch(
        f"/api/v1/appointments/{appointment.id}",
        json={
            "scheduled_at": new_time.isoformat(),
            "duration_minutes": 45,
            "notes": "Reagendada",
        },
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["duration_minutes"] == 45
    assert updated.json()["notes"] == "Reagendada"

    null_time = client.patch(
        f"/api/v1/appointments/{appointment.id}",
        json={"scheduled_at": None},
        headers=headers,
    )
    assert null_time.status_code == 422
    null_time_error = null_time.json()["error"]
    assert null_time_error["code"] == "VALIDATION_ERROR"
    assert isinstance(null_time_error["details"][0]["ctx"]["error"], str)

    null_duration = client.patch(
        f"/api/v1/appointments/{appointment.id}",
        json={"duration_minutes": None},
        headers=headers,
    )
    assert null_duration.status_code == 422
    assert isinstance(
        null_duration.json()["error"]["details"][0]["ctx"]["error"],
        str,
    )


def test_cancel_preserves_appointment_and_frees_slot(
    client, db_session, clinic, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic, cpf="12345678903")
    dentist = _dentist(db_session, dentist_user)
    headers = auth_headers(client, receptionist_user.email)
    payload = _payload(patient, dentist)

    created = client.post("/api/v1/appointments", json=payload, headers=headers)
    appointment_id = created.json()["id"]

    canceled = client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={"status": "CANCELED"},
        headers=headers,
    )
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "CANCELED"

    replacement = client.post("/api/v1/appointments", json=payload, headers=headers)
    assert replacement.status_code == 201

    legacy_cancel = client.post(
        f"/api/v1/appointments/{replacement.json()['id']}/cancel",
        headers=headers,
    )
    assert legacy_cancel.status_code == 200


def test_confirmation_and_invalid_terminal_transition(
    client, db_session, clinic, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic, cpf="12345678904")
    dentist = _dentist(db_session, dentist_user)
    appointment = _appointment(db_session, clinic, patient, dentist)
    headers = auth_headers(client, receptionist_user.email)

    confirmed = client.patch(
        f"/api/v1/appointments/{appointment.id}/status",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMED"

    canceled = client.patch(
        f"/api/v1/appointments/{appointment.id}/status",
        json={"status": "CANCELED"},
        headers=headers,
    )
    assert canceled.status_code == 200

    reopened = client.patch(
        f"/api/v1/appointments/{appointment.id}/status",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert reopened.status_code == 422


def test_completion_permissions_and_start_time(
    client,
    db_session,
    clinic,
    administrator_user,
    receptionist_user,
    dentist_user,
):
    patient = _patient(db_session, clinic, cpf="12345678905")
    dentist = _dentist(db_session, dentist_user)
    past = _appointment(
        db_session,
        clinic,
        patient,
        dentist,
        scheduled_at=_when(days=-1),
    )
    admin_headers = auth_headers(client, administrator_user.email)

    completed = client.patch(
        f"/api/v1/appointments/{past.id}/status",
        json={"status": "COMPLETED"},
        headers=admin_headers,
    )
    assert completed.status_code == 200

    future = _appointment(db_session, clinic, patient, dentist, scheduled_at=_when(days=4))
    too_soon = client.patch(
        f"/api/v1/appointments/{future.id}/status",
        json={"status": "COMPLETED"},
        headers=admin_headers,
    )
    assert too_soon.status_code == 422

    receptionist_headers = auth_headers(client, receptionist_user.email)
    forbidden = client.patch(
        f"/api/v1/appointments/{future.id}/status",
        json={"status": "COMPLETED"},
        headers=receptionist_headers,
    )
    assert forbidden.status_code == 403


def test_receptionist_and_dentist_can_register_no_show_after_start(
    client, db_session, clinic, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic, cpf="12345678906")
    dentist = _dentist(db_session, dentist_user)
    receptionist_appointment = _appointment(
        db_session,
        clinic,
        patient,
        dentist,
        scheduled_at=_when(days=-2),
    )
    receptionist_headers = auth_headers(client, receptionist_user.email)

    no_show = client.patch(
        f"/api/v1/appointments/{receptionist_appointment.id}/status",
        json={"status": "NO_SHOW"},
        headers=receptionist_headers,
    )
    assert no_show.status_code == 200

    dentist_appointment = _appointment(
        db_session,
        clinic,
        patient,
        dentist,
        scheduled_at=_when(days=-1),
    )
    dentist_headers = auth_headers(client, dentist_user.email)
    dentist_no_show = client.patch(
        f"/api/v1/appointments/{dentist_appointment.id}/status",
        json={"status": "NO_SHOW"},
        headers=dentist_headers,
    )
    assert dentist_no_show.status_code == 200


def test_dentist_sees_and_changes_only_own_appointments(
    client, db_session, clinic, dentist_user, receptionist_user
):
    patient = _patient(db_session, clinic, cpf="12345678907")
    own_dentist = _dentist(db_session, dentist_user)
    other_user = _make_user(
        db_session,
        clinic,
        email="outro.dentista@clinica.example.com",
        cpf="00000000030",
        role=Role.DENTIST,
    )
    other_dentist = _dentist(db_session, other_user, cro="54321")
    own = _appointment(
        db_session,
        clinic,
        patient,
        own_dentist,
        scheduled_at=_when(days=-2),
    )
    other = _appointment(
        db_session,
        clinic,
        patient,
        other_dentist,
        scheduled_at=_when(days=-1),
    )
    headers = auth_headers(client, dentist_user.email)

    listed = client.get("/api/v1/appointments", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [own.id]

    assert client.get(f"/api/v1/appointments/{other.id}", headers=headers).status_code == 404
    assert (
        client.patch(
            f"/api/v1/appointments/{other.id}/status",
            json={"status": "COMPLETED"},
            headers=headers,
        ).status_code
        == 404
    )

    completed = client.patch(
        f"/api/v1/appointments/{own.id}/status",
        json={"status": "COMPLETED"},
        headers=headers,
    )
    assert completed.status_code == 200

    administrative_change = client.patch(
        f"/api/v1/appointments/{other.id}",
        json={"duration_minutes": 60},
        headers=headers,
    )
    assert administrative_change.status_code == 404

    receptionist_headers = auth_headers(client, receptionist_user.email)
    assert (
        client.get(f"/api/v1/appointments/{other.id}", headers=receptionist_headers).status_code
        == 200
    )


def test_only_administrator_and_receptionist_create_appointments(
    client,
    db_session,
    clinic,
    administrator_user,
    receptionist_user,
    dentist_user,
):
    patient = _patient(db_session, clinic, cpf="12345678908")
    dentist = _dentist(db_session, dentist_user)

    dentist_headers = auth_headers(client, dentist_user.email)
    denied = client.post(
        "/api/v1/appointments",
        json=_payload(patient, dentist),
        headers=dentist_headers,
    )
    assert denied.status_code == 403

    admin_headers = auth_headers(client, administrator_user.email)
    allowed = client.post(
        "/api/v1/appointments",
        json=_payload(patient, dentist),
        headers=admin_headers,
    )
    assert allowed.status_code == 201


def test_inactive_clinic_patient_and_dentist_are_rejected(
    client,
    db_session,
    clinic,
    receptionist_user,
    dentist_user,
):
    active_patient = _patient(db_session, clinic, cpf="12345678909")
    inactive_patient = _patient(
        db_session,
        clinic,
        cpf="12345678910",
        active=False,
    )
    dentist = _dentist(db_session, dentist_user)
    headers = auth_headers(client, receptionist_user.email)

    patient_response = client.post(
        "/api/v1/appointments",
        json=_payload(inactive_patient, dentist),
        headers=headers,
    )
    assert patient_response.status_code == 422

    dentist_user.is_active = False
    db_session.commit()
    dentist_response = client.post(
        "/api/v1/appointments",
        json=_payload(active_patient, dentist, scheduled_at=_when(days=3)),
        headers=headers,
    )
    assert dentist_response.status_code == 422

    dentist_user.is_active = True
    clinic.is_active = False
    db_session.commit()
    clinic_response = client.post(
        "/api/v1/appointments",
        json=_payload(active_patient, dentist, scheduled_at=_when(days=4)),
        headers=headers,
    )
    assert clinic_response.status_code == 422


def test_participants_from_another_clinic_are_rejected(
    client, db_session, clinic, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic, cpf="12345678914")
    dentist = _dentist(db_session, dentist_user)
    other_clinic = Clinic(
        name="Clínica Externa",
        cnpj="00000000000353",
        email="externa@clinica.example.com",
        is_active=True,
    )
    db_session.add(other_clinic)
    db_session.commit()
    db_session.refresh(other_clinic)
    other_patient = _patient(db_session, other_clinic, cpf="12345678915")
    other_user = _make_user(
        db_session,
        other_clinic,
        email="dentista.externo@clinica.example.com",
        cpf="00000000031",
        role=Role.DENTIST,
    )
    other_dentist = _dentist(db_session, other_user, cro="67890")
    headers = auth_headers(client, receptionist_user.email)

    wrong_patient = client.post(
        "/api/v1/appointments",
        json=_payload(other_patient, dentist, scheduled_at=_when(days=5)),
        headers=headers,
    )
    assert wrong_patient.status_code == 404

    wrong_dentist = client.post(
        "/api/v1/appointments",
        json=_payload(patient, other_dentist, scheduled_at=_when(days=6)),
        headers=headers,
    )
    assert wrong_dentist.status_code == 404


def test_past_time_and_server_managed_fields_are_rejected(
    client, db_session, clinic, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic, cpf="12345678911")
    dentist = _dentist(db_session, dentist_user)
    headers = auth_headers(client, receptionist_user.email)

    past = client.post(
        "/api/v1/appointments",
        json=_payload(patient, dentist, scheduled_at=_when(days=-1)),
        headers=headers,
    )
    assert past.status_code == 422

    for forbidden_field, value in (
        ("clinic_id", clinic.id),
        ("status", "CONFIRMED"),
        ("scheduled_period", "[2026-10-01,2026-10-02)"),
    ):
        payload = _payload(patient, dentist, scheduled_at=_when(days=5))
        payload[forbidden_field] = value
        response = client.post("/api/v1/appointments", json=payload, headers=headers)
        assert response.status_code == 422


def test_preventive_overlap_returns_stable_409(
    client, db_session, clinic, receptionist_user, dentist_user
):
    patient = _patient(db_session, clinic, cpf="12345678912")
    dentist = _dentist(db_session, dentist_user)
    headers = auth_headers(client, receptionist_user.email)
    scheduled_at = _when(days=6)
    payload = _payload(patient, dentist, scheduled_at=scheduled_at, minutes=60)

    assert client.post("/api/v1/appointments", json=payload, headers=headers).status_code == 201
    conflict = client.post(
        "/api/v1/appointments",
        json=_payload(
            patient,
            dentist,
            scheduled_at=scheduled_at + datetime.timedelta(minutes=30),
        ),
        headers=headers,
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"] == {
        "code": "APPOINTMENT_TIME_CONFLICT",
        "message": "O dentista já possui uma consulta agendada nesse período.",
        "details": None,
    }


def test_postgresql_exclusion_violation_is_translated_to_conflict(
    client,
    db_session,
    clinic,
    receptionist_user,
    dentist_user,
    monkeypatch,
):
    patient = _patient(db_session, clinic, cpf="12345678913")
    dentist = _dentist(db_session, dentist_user)
    headers = auth_headers(client, receptionist_user.email)

    class ExclusionViolation(Exception):
        sqlstate = "23P01"

    def fail_commit():
        raise IntegrityError("insert", {}, ExclusionViolation())

    monkeypatch.setattr(db_session, "commit", fail_commit)
    response = client.post(
        "/api/v1/appointments",
        json=_payload(patient, dentist, scheduled_at=_when(days=7)),
        headers=headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "APPOINTMENT_TIME_CONFLICT"


def test_required_agenda_routes_are_present_in_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"get", "post"} <= set(paths["/api/v1/appointments"])
    assert {"get", "patch"} <= set(paths["/api/v1/appointments/{appointment_id}"])
    assert "patch" in paths["/api/v1/appointments/{appointment_id}/status"]
    assert "get" in paths["/api/v1/dentists"]
    assert "post" in paths["/api/v1/users"]

    parameters = {
        parameter["name"]
        for parameter in paths["/api/v1/appointments"]["get"]["parameters"]
    }
    assert {"start_date", "end_date", "dentist_id", "patient_id", "status"} <= parameters
