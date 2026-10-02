"""Regras de negócio da agenda."""
import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.appointments.models import Appointment, AppointmentStatus
from app.appointments.repository import AppointmentRepository
from app.common.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.security.roles import Role
from app.users.models import User


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
_ACTIVE_STATUSES = {AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED}


def _utc(value: datetime.datetime) -> datetime.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(datetime.timezone.utc)


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
        raise ConflictError("O dentista já possui atendimento neste intervalo.")
    return scheduled_at


def list_appointments(
    db: Session,
    *,
    clinic_id: int,
    current_user: User,
    start: datetime.datetime | None = None,
    end: datetime.datetime | None = None,
    dentist_id: int | None = None,
    patient_id: int | None = None,
    status: AppointmentStatus | None = None,
) -> list[Appointment]:
    return AppointmentRepository(db).list(
        clinic_id,
        start=start,
        end=end,
        dentist_id=dentist_id,
        patient_id=patient_id,
        status=status,
        responsible_user_id=current_user.id if current_user.role is Role.DENTIST else None,
    )


def get_appointment(db: Session, *, clinic_id: int, appointment_id: int, current_user: User) -> Appointment:
    repository = AppointmentRepository(db)
    appointment = repository.get(appointment_id, clinic_id)
    if appointment is None:
        raise NotFoundError("Agendamento não encontrado.")
    if current_user.role is Role.DENTIST:
        dentist = db.get(Dentist, appointment.dentist_id)
        if dentist is None or dentist.user_id != current_user.id:
            raise NotFoundError("Agendamento não encontrado.")
    return appointment


def create_appointment(db: Session, *, clinic_id: int, payload) -> Appointment:
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


def update_appointment(
    db: Session, *, clinic_id: int, appointment_id: int, current_user: User, payload
) -> Appointment:
    appointment = get_appointment(db, clinic_id=clinic_id, appointment_id=appointment_id, current_user=current_user)
    changes = payload.model_dump(exclude_unset=True)
    requested_status = changes.pop("status", None)
    if current_user.role is Role.DENTIST:
        if set(changes):
            raise ForbiddenError("Dentistas só podem alterar a situação do próprio atendimento.")
        if requested_status not in {AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW}:
            raise ForbiddenError("Dentistas só podem registrar conclusão ou ausência.")
    elif requested_status is not None and requested_status not in _ALLOWED_TRANSITIONS.get(appointment.status, set()):
        raise ValidationAppError("Transição de situação não permitida.")

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
        appointment.status = requested_status
    return AppointmentRepository(db).save(appointment)


def cancel_appointment(db: Session, *, clinic_id: int, appointment_id: int) -> Appointment:
    repository = AppointmentRepository(db)
    appointment = repository.get(appointment_id, clinic_id)
    if appointment is None:
        raise NotFoundError("Agendamento não encontrado.")
    if appointment.status not in _ACTIVE_STATUSES:
        raise ValidationAppError("Somente agendamentos ativos podem ser cancelados.")
    appointment.status = AppointmentStatus.CANCELED
    return repository.save(appointment)
