"""Alterações da evidência vinculada à consulta da Agenda."""

import datetime

from sqlalchemy.orm import Session

from app.appointments.models import Appointment, AppointmentStatus
from app.common.exceptions import ConflictError, ValidationAppError
from app.records.access_models import ClinicalAccessGrant
from app.records.access_repository import ClinicalAccessGrantRepository


def add_confirmation(
    db: Session,
    *,
    appointment: Appointment,
    confirmed_by_user_id: int,
) -> ClinicalAccessGrant:
    """Registra uma nova confirmação sem sobrescrever procedência existente."""
    if appointment.status is not AppointmentStatus.SCHEDULED:
        raise ValidationAppError("Transição de situação não permitida.")

    repository = ClinicalAccessGrantRepository(db)
    existing = repository.get_for_update(
        appointment_id=appointment.id,
        clinic_id=appointment.clinic_id,
    )
    if existing is not None:
        # O tratamento de evidências antigas depende de decisão específica.
        raise ConflictError("A consulta já possui evidência de confirmação.")

    grant = ClinicalAccessGrant(
        appointment_id=appointment.id,
        clinic_id=appointment.clinic_id,
        patient_id=appointment.patient_id,
        dentist_id=appointment.dentist_id,
        granted_at=datetime.datetime.now(datetime.timezone.utc),
        confirmed_by_user_id=confirmed_by_user_id,
    )
    repository.add(grant)
    return grant


def register_care(
    db: Session,
    *,
    appointment: Appointment,
    care_occurred_at: datetime.datetime,
    care_recorded_by_user_id: int,
) -> ClinicalAccessGrant:
    """Registra a realização após confirmação confiável da mesma consulta."""
    if appointment.status is not AppointmentStatus.CONFIRMED:
        raise ValidationAppError("Transição de situação não permitida.")

    now = datetime.datetime.now(datetime.timezone.utc)
    if care_occurred_at.utcoffset() is None or care_occurred_at > now:
        raise ValidationAppError("Horário da realização inválido.")

    repository = ClinicalAccessGrantRepository(db)
    grant = repository.get_for_update(
        appointment_id=appointment.id,
        clinic_id=appointment.clinic_id,
    )
    if grant is None or grant.confirmed_by_user_id is None:
        raise ValidationAppError("A consulta não possui confirmação confiável.")

    origin = (
        grant.appointment_id,
        grant.clinic_id,
        grant.patient_id,
        grant.dentist_id,
    )
    participants = (
        appointment.id,
        appointment.clinic_id,
        appointment.patient_id,
        appointment.dentist_id,
    )
    if origin != participants:
        raise ConflictError("Participantes da evidência não correspondem à consulta.")

    if any(
        value is not None
        for value in (
            grant.care_occurred_at,
            grant.care_recorded_at,
            grant.care_recorded_by_user_id,
        )
    ):
        raise ConflictError("Realização já registrada para esta consulta.")

    grant.care_occurred_at = care_occurred_at
    grant.care_recorded_at = now
    grant.care_recorded_by_user_id = care_recorded_by_user_id
    return grant