"""Consultas persistentes da agenda."""
import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.appointments.models import Appointment, AppointmentStatus
from app.dentists.models import Dentist
from app.users.models import User


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self, clinic_id: int) -> Select:
        return select(Appointment).where(Appointment.clinic_id == clinic_id)

    def list(
        self,
        clinic_id: int,
        *,
        start: datetime.datetime | None = None,
        end: datetime.datetime | None = None,
        dentist_id: int | None = None,
        patient_id: int | None = None,
        status: AppointmentStatus | None = None,
        responsible_user_id: int | None = None,
    ) -> list[Appointment]:
        statement = self._base_query(clinic_id)
        if start is not None:
            statement = statement.where(Appointment.scheduled_at >= start)
        if end is not None:
            statement = statement.where(Appointment.scheduled_at < end)
        if dentist_id is not None:
            statement = statement.where(Appointment.dentist_id == dentist_id)
        if patient_id is not None:
            statement = statement.where(Appointment.patient_id == patient_id)
        if status is not None:
            statement = statement.where(Appointment.status == status)
        if responsible_user_id is not None:
            statement = statement.join(Dentist).where(
                Dentist.id == Appointment.dentist_id,
                Dentist.user_id == responsible_user_id,
            )
        statement = statement.order_by(Appointment.scheduled_at)
        return list(self.db.execute(statement).scalars().all())

    def get(self, appointment_id: int, clinic_id: int) -> Appointment | None:
        return self.db.execute(
            self._base_query(clinic_id).where(Appointment.id == appointment_id)
        ).scalar_one_or_none()

    def get_for_update(self, appointment_id: int, clinic_id: int) -> Appointment | None:
        return self.db.execute(
            self._base_query(clinic_id)
            .where(Appointment.id == appointment_id)
            .with_for_update()
        ).scalar_one_or_none()

    def has_conflict(
        self,
        *,
        clinic_id: int,
        dentist_id: int,
        scheduled_at: datetime.datetime,
        duration_minutes: int,
        excluding_id: int | None = None,
    ) -> bool:
        new_end = scheduled_at + datetime.timedelta(minutes=duration_minutes)
        statement = select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.dentist_id == dentist_id,
            Appointment.status.not_in(
                [AppointmentStatus.CANCELED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW]
            ),
        )
        for appointment in self.db.execute(statement).scalars():
            if excluding_id is not None and appointment.id == excluding_id:
                continue
            existing_start = appointment.scheduled_at
            if existing_start.tzinfo is None:
                existing_start = existing_start.replace(tzinfo=datetime.timezone.utc)
            existing_end = existing_start + datetime.timedelta(minutes=appointment.duration_minutes)
            if existing_start < new_end and scheduled_at < existing_end:
                return True
        return False

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def save(self, appointment: Appointment) -> Appointment:
        self.db.commit()
        self.db.refresh(appointment)
        return appointment
