"""Persistência da evidência de confirmação e atendimento."""

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.appointments.models import Appointment, AppointmentStatus
from app.records.access_models import ClinicalAccessGrant


class ClinicalAccessGrantRepository:
    """Consulta e adiciona evidências sem controlar a transação."""

    def __init__(self, db: Session):
        self.db = db

    def get_for_update(
        self, *, appointment_id: int, clinic_id: int
    ) -> ClinicalAccessGrant | None:
        # O serviço bloqueia primeiro a consulta de origem. Este segundo
        # bloqueio protege a evidência durante a conclusão do atendimento.
        statement = (
            select(ClinicalAccessGrant)
            .where(
                ClinicalAccessGrant.appointment_id == appointment_id,
                ClinicalAccessGrant.clinic_id == clinic_id,
            )
            .execution_options(populate_existing=True)
            .with_for_update(of=ClinicalAccessGrant)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def add(self, grant: ClinicalAccessGrant) -> None:
        # O serviço grava consulta e evidência em um único commit.
        self.db.add(grant)

    def has_valid_origin(
        self, *, clinic_id: int, patient_id: int, dentist_id: int
    ) -> bool:
        """Busca qualquer fundamento válido; a elegibilidade do leitor é separada."""
        same_origin = and_(
            Appointment.id == ClinicalAccessGrant.appointment_id,
            Appointment.clinic_id == ClinicalAccessGrant.clinic_id,
            Appointment.patient_id == ClinicalAccessGrant.patient_id,
            Appointment.dentist_id == ClinicalAccessGrant.dentist_id,
        )
        completed_with_care = and_(
            Appointment.status == AppointmentStatus.COMPLETED,
            ClinicalAccessGrant.care_occurred_at.is_not(None),
            ClinicalAccessGrant.care_recorded_at.is_not(None),
            ClinicalAccessGrant.care_recorded_by_user_id.is_not(None),
        )
        statement = (
            select(ClinicalAccessGrant.appointment_id)
            .join(Appointment, same_origin)
            .where(
                ClinicalAccessGrant.clinic_id == clinic_id,
                ClinicalAccessGrant.patient_id == patient_id,
                ClinicalAccessGrant.dentist_id == dentist_id,
                ClinicalAccessGrant.confirmed_by_user_id.is_not(None),
                or_(
                    Appointment.status == AppointmentStatus.CONFIRMED,
                    completed_with_care,
                ),
            )
            .limit(1)
        )
        return self.db.execute(statement).first() is not None