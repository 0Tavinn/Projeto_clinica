"""Consultas persistentes da agenda."""
import datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, lazyload

from app.appointments.models import Appointment, AppointmentStatus
from app.common.exceptions import (
    AppointmentParticipantConflictError,
    AppointmentTimeConflictError,
    ConflictError,
)
from app.dentists.models import Dentist
from app.records.models import ClinicalEvolution, MedicalRecord


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
        # Bloqueia apenas a consulta. Os relacionamentos são carregados depois,
        # evitando FOR UPDATE sobre os JOINs gerados pelo mapeamento padrão.
        statement = (
            self._base_query(clinic_id)
            .where(Appointment.id == appointment_id)
            .options(
                lazyload(Appointment.patient),
                lazyload(Appointment.dentist),
            )
            .execution_options(populate_existing=True)
            .with_for_update(of=Appointment)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def has_saved_evolution_for_completion(self, appointment: Appointment) -> bool:
        """Confere conteúdo salvo e estabiliza a evolução até concluir.

        NOWAIT evita ciclo de bloqueios: a escrita clínica pode segurar a
        evolução enquanto espera a consulta já bloqueada pela Agenda.
        """
        statement = (
            select(ClinicalEvolution.id, ClinicalEvolution.description)
            .join(MedicalRecord, MedicalRecord.id == ClinicalEvolution.medical_record_id)
            .where(
                ClinicalEvolution.appointment_id == appointment.id,
                ClinicalEvolution.dentist_id == appointment.dentist_id,
                MedicalRecord.patient_id == appointment.patient_id,
            )
            .with_for_update(read=True, nowait=True, of=ClinicalEvolution)
        )
        try:
            row = self.db.execute(statement).one_or_none()
        except OperationalError as error:
            original = error.orig
            if getattr(original, "sqlstate", None) == "55P03":
                raise ConflictError("Evolução clínica em alteração; tente novamente.") from error
            raise
        return row is not None and bool(row.description.strip())

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
            sqlstate = getattr(original, "sqlstate", None) or getattr(
                original, "pgcode", None
            )
            if sqlstate == "23P01":
                raise AppointmentTimeConflictError() from error

            diagnostic = getattr(original, "diag", None)
            constraint_name = getattr(diagnostic, "constraint_name", None)
            if (
                sqlstate == "23503"
                and constraint_name == "fk_clinical_access_grants_origin"
            ):
                # A FK preserva a origem da evidência até haver regra de correção.
                raise AppointmentParticipantConflictError() from error
            raise
