"""Consultas persistentes da agenda."""
import datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.appointments.models import Appointment, AppointmentStatus
from app.appointments.conflict_detection import detect_conflict, interval
from app.common.exceptions import AppointmentTimeConflictError
from app.dentists.models import Dentist


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
        statement = select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.dentist_id == dentist_id,
            Appointment.status.not_in(
                [AppointmentStatus.CANCELED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW]
            ),
        )
        # Os filtros e a exclusão do próprio ID continuam no repositório.
        # yield_per limita os objetos carregados enquanto o comparador loteia.
        result = self.db.execute(statement.execution_options(yield_per=1024))
        try:
            candidates = (
                interval(appointment.scheduled_at, appointment.duration_minutes)
                for appointment in result.scalars()
                if excluding_id is None or appointment.id != excluding_id
            )
            return detect_conflict(
                candidates, interval(scheduled_at, duration_minutes)
            ).conflict
        finally:
            # Um conflito pode encerrar o consumo antes do último lote.
            # Fecha o cursor antes do commit que mantém a autoridade do banco.
            result.close()

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self._commit()
        self.db.refresh(appointment)
        return appointment

    def save(self, appointment: Appointment) -> Appointment:
        self._commit()
        self.db.refresh(appointment)
        return appointment

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            original = error.orig
            sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
            if sqlstate == "23P01":
                raise AppointmentTimeConflictError() from error
            raise
