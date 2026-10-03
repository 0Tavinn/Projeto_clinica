"""Regras de negócio da agenda."""
import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.appointments.models import Appointment, AppointmentStatus
from app.appointments.repository import AppointmentRepository
from app.common.exceptions import (
    AppointmentTimeConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.security.roles import Role
from app.users.models import Clinic, User


_ALLOWED_TRANSITIONS = {
    AppointmentStatus.SCHEDULED: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELED,
        AppointmentStatus.NO_SHOW,
    },
}
_ROLE_STATUS_TARGETS = {
    Role.ADMINISTRATOR: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELED,
        AppointmentStatus.NO_SHOW,
    },
    Role.RECEPTIONIST: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELED,
        AppointmentStatus.NO_SHOW,
    },
    Role.DENTIST: {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW,
    },
}
_FINAL_STATUSES = {
    AppointmentStatus.COMPLETED,
    AppointmentStatus.CANCELED,
    AppointmentStatus.NO_SHOW,
}


def _utc(value: datetime.datetime) -> datetime.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(datetime.timezone.utc)


def _active_clinic(db: Session, clinic_id: int) -> Clinic:
    clinic = db.get(Clinic, clinic_id)
    if clinic is None or not clinic.is_active:
        raise ValidationAppError("A clínica deve estar ativa.")
    return clinic


def _participants(
    db: Session, *, clinic_id: int, patient_id: int, dentist_id: int
) -> tuple[Patient, Dentist, User]:
    patient = db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
        )
    ).scalar_one_or_none()
    dentist_data = db.execute(
        select(Dentist, User)
        .join(User, User.id == Dentist.user_id)
        .where(Dentist.id == dentist_id, User.clinic_id == clinic_id)
    ).one_or_none()
    if patient is None or dentist_data is None:
        raise NotFoundError("Paciente ou dentista não pertence à clínica.")
    dentist, user = dentist_data
    if not patient.is_active or not user.is_active:
        raise ValidationAppError("Paciente e dentista devem estar ativos.")
    if user.role is not Role.DENTIST:
        raise ValidationAppError("O profissional selecionado não possui perfil de dentista.")
    return patient, dentist, user


def _validate_slot(
    db: Session,
    *,
    clinic_id: int,
    dentist_id: int,
    scheduled_at: datetime.datetime,
    duration_minutes: int,
    excluding_id: int | None = None,
) -> datetime.datetime:
    scheduled_at = _utc(scheduled_at)
    if scheduled_at <= datetime.datetime.now(datetime.timezone.utc):
        raise ValidationAppError("O agendamento deve ocorrer em um horário futuro.")
    if duration_minutes <= 0:
        raise ValidationAppError("A duração deve ser maior que zero.")
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        lock_key = clinic_id * 1_000_000 + dentist_id
        db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key})
    if AppointmentRepository(db).has_conflict(
        clinic_id=clinic_id,
        dentist_id=dentist_id,
        scheduled_at=scheduled_at,
        duration_minutes=duration_minutes,
        excluding_id=excluding_id,
    ):
        raise AppointmentTimeConflictError()
    return scheduled_at


def list_appointments(
    db: Session,
    *,
    clinic_id: int,
    current_user: User,
    start_date: datetime.datetime | None = None,
    end_date: datetime.datetime | None = None,
    dentist_id: int | None = None,
    patient_id: int | None = None,
    status: AppointmentStatus | None = None,
) -> list[Appointment]:
    _active_clinic(db, clinic_id)
    if start_date is not None:
        start_date = _utc(start_date)
    if end_date is not None:
        end_date = _utc(end_date)
    if start_date is not None and end_date is not None and start_date >= end_date:
        raise ValidationAppError("start_date deve ser anterior a end_date.")
    return AppointmentRepository(db).list(
        clinic_id,
        start=start_date,
        end=end_date,
        dentist_id=dentist_id,
        patient_id=patient_id,
        status=status,
        responsible_user_id=current_user.id if current_user.role is Role.DENTIST else None,
    )


def get_appointment(
    db: Session, *, clinic_id: int, appointment_id: int, current_user: User
) -> Appointment:
    _active_clinic(db, clinic_id)
    repository = AppointmentRepository(db)
    appointment = repository.get(appointment_id, clinic_id)
    if appointment is None:
        raise NotFoundError("Agendamento não encontrado.")
    if current_user.role is Role.DENTIST:
        if appointment.dentist.user_id != current_user.id:
            raise NotFoundError("Agendamento não encontrado.")
    return appointment


def create_appointment(db: Session, *, clinic_id: int, payload) -> Appointment:
    _active_clinic(db, clinic_id)
    _participants(
        db, clinic_id=clinic_id, patient_id=payload.patient_id, dentist_id=payload.dentist_id
    )
    scheduled_at = _validate_slot(
        db,
        clinic_id=clinic_id,
        dentist_id=payload.dentist_id,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
    )
    return AppointmentRepository(db).create(
        Appointment(
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            dentist_id=payload.dentist_id,
            scheduled_at=scheduled_at,
            duration_minutes=payload.duration_minutes,
            notes=payload.notes,
            status=AppointmentStatus.SCHEDULED,
        )
    )


def _apply_status_transition(
    appointment: Appointment,
    *,
    current_user: User,
    requested_status: AppointmentStatus,
) -> None:
    allowed_targets = _ROLE_STATUS_TARGETS.get(current_user.role, set())
    if requested_status not in allowed_targets:
        raise ForbiddenError("Usuário não tem permissão para registrar esta situação.")
    if requested_status not in _ALLOWED_TRANSITIONS.get(appointment.status, set()):
        raise ValidationAppError("Transição de situação não permitida.")
    if requested_status in {AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW}:
        if _utc(appointment.scheduled_at) > datetime.datetime.now(datetime.timezone.utc):
            raise ValidationAppError(
                "Conclusão e ausência só podem ser registradas após o início da consulta."
            )
    appointment.status = requested_status


def change_appointment_status(
    db: Session,
    *,
    clinic_id: int,
    appointment_id: int,
    current_user: User,
    requested_status: AppointmentStatus,
) -> Appointment:
    appointment = get_appointment(
        db,
        clinic_id=clinic_id,
        appointment_id=appointment_id,
        current_user=current_user,
    )
    _participants(
        db,
        clinic_id=clinic_id,
        patient_id=appointment.patient_id,
        dentist_id=appointment.dentist_id,
    )
    _apply_status_transition(
        appointment,
        current_user=current_user,
        requested_status=requested_status,
    )
    return AppointmentRepository(db).save(appointment)


def update_appointment(
    db: Session, *, clinic_id: int, appointment_id: int, current_user: User, payload
) -> Appointment:
    appointment = get_appointment(
        db,
        clinic_id=clinic_id,
        appointment_id=appointment_id,
        current_user=current_user,
    )
    changes = payload.model_dump(exclude_unset=True)
    requested_status = changes.pop("status", None)

    if current_user.role is Role.DENTIST:
        if changes:
            raise ForbiddenError("Dentistas só podem alterar a situação do próprio atendimento.")
        if requested_status is None:
            raise ForbiddenError("Dentistas só podem registrar conclusão ou ausência.")
        _participants(
            db,
            clinic_id=clinic_id,
            patient_id=appointment.patient_id,
            dentist_id=appointment.dentist_id,
        )
        _apply_status_transition(
            appointment,
            current_user=current_user,
            requested_status=requested_status,
        )
        return AppointmentRepository(db).save(appointment)

    if current_user.role not in {Role.ADMINISTRATOR, Role.RECEPTIONIST}:
        raise ForbiddenError("Usuário não tem permissão para alterar agendamentos.")
    if changes and appointment.status in _FINAL_STATUSES:
        raise ValidationAppError("Agendamentos finalizados não podem ser editados.")

    if changes:
        patient_id = changes.get("patient_id", appointment.patient_id)
        dentist_id = changes.get("dentist_id", appointment.dentist_id)
        scheduled_at = changes.get("scheduled_at", appointment.scheduled_at)
        duration = changes.get("duration_minutes", appointment.duration_minutes)
        _participants(db, clinic_id=clinic_id, patient_id=patient_id, dentist_id=dentist_id)
        changes["scheduled_at"] = _validate_slot(
            db,
            clinic_id=clinic_id,
            dentist_id=dentist_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration,
            excluding_id=appointment.id,
        )
        for field_name, value in changes.items():
            setattr(appointment, field_name, value)

    if requested_status is not None:
        if not changes:
            _participants(
                db,
                clinic_id=clinic_id,
                patient_id=appointment.patient_id,
                dentist_id=appointment.dentist_id,
            )
        _apply_status_transition(
            appointment,
            current_user=current_user,
            requested_status=requested_status,
        )
    return AppointmentRepository(db).save(appointment)


def cancel_appointment(
    db: Session, *, clinic_id: int, appointment_id: int, current_user: User
) -> Appointment:
    return change_appointment_status(
        db,
        clinic_id=clinic_id,
        appointment_id=appointment_id,
        current_user=current_user,
        requested_status=AppointmentStatus.CANCELED,
    )
