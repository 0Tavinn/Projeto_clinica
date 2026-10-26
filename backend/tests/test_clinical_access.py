"""Testes da seleção de origens de acesso clínico."""

import datetime

import pytest

from app.appointments.models import Appointment, AppointmentStatus
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.access_models import ClinicalAccessGrant
from app.records.access_repository import ClinicalAccessGrantRepository


@pytest.mark.parametrize(
    "status, trusted, care_recorded, expected",
    [
        (AppointmentStatus.SCHEDULED, True, False, False),
        (AppointmentStatus.CONFIRMED, False, False, False),
        (AppointmentStatus.CONFIRMED, True, False, True),
        (AppointmentStatus.CANCELED, True, False, False),
        (AppointmentStatus.NO_SHOW, True, False, False),
        (AppointmentStatus.COMPLETED, True, False, False),
        (AppointmentStatus.COMPLETED, True, True, True),
    ],
)
def test_origin_requires_current_state_and_trustworthy_evidence(
    db_session,
    clinic,
    dentist_user,
    receptionist_user,
    status,
    trusted,
    care_recorded,
    expected,
):
    now = datetime.datetime.now(datetime.timezone.utc)
    patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente de teste",
        cpf="12345678901",
        medical_record_number="PRONT-ACESSO",
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
        scheduled_at=now - datetime.timedelta(hours=1),
        duration_minutes=30,
        status=status,
    )
    db_session.add(appointment)
    db_session.flush()

    repository = ClinicalAccessGrantRepository(db_session)
    lookup = {
        "clinic_id": clinic.id,
        "patient_id": patient.id,
        "dentist_id": dentist.id,
    }

    # Estado da consulta, sozinho, nunca concede acesso.
    assert not repository.has_valid_origin(**lookup)

    grant = ClinicalAccessGrant(
        appointment_id=appointment.id,
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        granted_at=now - datetime.timedelta(hours=2),
        confirmed_by_user_id=receptionist_user.id if trusted else None,
        care_occurred_at=(
            now - datetime.timedelta(minutes=10) if care_recorded else None
        ),
        care_recorded_at=now if care_recorded else None,
        care_recorded_by_user_id=dentist_user.id if care_recorded else None,
    )
    db_session.add(grant)
    db_session.commit()

    assert repository.has_valid_origin(**lookup) is expected
    assert not repository.has_valid_origin(
        clinic_id=clinic.id + 999,
        patient_id=patient.id,
        dentist_id=dentist.id,
    )
    assert not repository.has_valid_origin(
        clinic_id=clinic.id,
        patient_id=patient.id + 999,
        dentist_id=dentist.id,
    )
    assert not repository.has_valid_origin(
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id + 999,
    )


def test_other_origin_preserves_access_after_cancel_or_absence(
    db_session, clinic, dentist_user, receptionist_user
):
    now = datetime.datetime.now(datetime.timezone.utc)
    patient = Patient(
        clinic_id=clinic.id,
        full_name="Paciente com várias consultas",
        cpf="12345678901",
        medical_record_number="PRONT-MULTIPLAS-ORIGENS",
        birth_date=datetime.date(1990, 1, 1),
    )
    dentist = Dentist(
        user_id=dentist_user.id,
        cro_number="12345",
        cro_state="PE",
    )
    db_session.add_all([patient, dentist])
    db_session.flush()

    repository = ClinicalAccessGrantRepository(db_session)
    lookup = {
        "clinic_id": clinic.id,
        "patient_id": patient.id,
        "dentist_id": dentist.id,
    }

    def add_origin(
        status: AppointmentStatus, hours_ago: int, *, care_recorded: bool = False
    ) -> Appointment:
        # Monta estados persistidos para testar a busca, sem simular a rota.
        appointment = Appointment(
            clinic_id=clinic.id,
            patient_id=patient.id,
            dentist_id=dentist.id,
            scheduled_at=now - datetime.timedelta(hours=hours_ago),
            duration_minutes=30,
            status=status,
        )
        db_session.add(appointment)
        db_session.flush()
        db_session.add(
            ClinicalAccessGrant(
                appointment_id=appointment.id,
                clinic_id=clinic.id,
                patient_id=patient.id,
                dentist_id=dentist.id,
                granted_at=now - datetime.timedelta(days=1),
                confirmed_by_user_id=receptionist_user.id,
                care_occurred_at=(
                    now - datetime.timedelta(minutes=45) if care_recorded else None
                ),
                care_recorded_at=now if care_recorded else None,
                care_recorded_by_user_id=(
                    dentist_user.id if care_recorded else None
                ),
            )
        )
        db_session.commit()
        return appointment

    first = add_origin(AppointmentStatus.CONFIRMED, 3)
    second = add_origin(AppointmentStatus.CONFIRMED, 2)
    assert repository.has_valid_origin(**lookup)

    first.status = AppointmentStatus.CANCELED
    db_session.commit()
    assert repository.has_valid_origin(**lookup)

    second.status = AppointmentStatus.NO_SHOW
    db_session.commit()
    assert not repository.has_valid_origin(**lookup)
    assert db_session.get(ClinicalAccessGrant, first.id) is not None
    assert db_session.get(ClinicalAccessGrant, second.id) is not None

    add_origin(AppointmentStatus.COMPLETED, 1, care_recorded=True)
    assert repository.has_valid_origin(**lookup)

    later = add_origin(AppointmentStatus.CONFIRMED, 4)
    later.status = AppointmentStatus.CANCELED
    db_session.commit()
    assert repository.has_valid_origin(**lookup)
