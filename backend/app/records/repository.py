"""Consultas do prontuário usadas pelo serviço clínico."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.appointments.models import Appointment, AppointmentStatus
from app.records.models import ClinicalEvolution, MedicalRecord


class RecordRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_medical_record_by_patient(self, patient_id: int) -> MedicalRecord | None:
        return self.db.execute(
            select(MedicalRecord).where(MedicalRecord.patient_id == patient_id)
        ).scalar_one_or_none()

    def list_own_evolutions(
        self, *, medical_record_id: int, dentist_id: int, patient_id: int, clinic_id: int
    ) -> list[ClinicalEvolution]:
        statement = (
            select(ClinicalEvolution)
            .join(Appointment, Appointment.id == ClinicalEvolution.appointment_id)
            .where(
                ClinicalEvolution.medical_record_id == medical_record_id,
                ClinicalEvolution.dentist_id == dentist_id,
                Appointment.clinic_id == clinic_id,
                Appointment.patient_id == patient_id,
                Appointment.dentist_id == dentist_id,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
            .order_by(ClinicalEvolution.recorded_at.desc(), ClinicalEvolution.id.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def get_own_evolution_for_update(
        self, *, evolution_id: int, dentist_id: int, clinic_id: int
    ) -> ClinicalEvolution | None:
        statement = (
            select(ClinicalEvolution)
            .join(MedicalRecord, MedicalRecord.id == ClinicalEvolution.medical_record_id)
            .join(Appointment, Appointment.id == ClinicalEvolution.appointment_id)
            .where(
                ClinicalEvolution.id == evolution_id,
                ClinicalEvolution.dentist_id == dentist_id,
                Appointment.clinic_id == clinic_id,
                Appointment.dentist_id == dentist_id,
                Appointment.patient_id == MedicalRecord.patient_id,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
            .with_for_update(of=ClinicalEvolution)
        )
        return self.db.execute(statement).scalar_one_or_none()
