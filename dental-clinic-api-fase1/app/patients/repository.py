"""Acesso a dados para pacientes."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.patients.models import Patient


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_active_by_clinic(self, clinic_id: int) -> list[Patient]:
        statement = (
            select(Patient)
            .where(
                Patient.clinic_id == clinic_id,
                Patient.is_active.is_(True),
            )
            .order_by(Patient.full_name)
        )
        return list(self.db.execute(statement).scalars().all())

    def get_active_by_id(
        self,
        patient_id: int,
        clinic_id: int,
    ) -> Patient | None:
        statement = select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
            Patient.is_active.is_(True),
        )
        return self.db.execute(statement).scalar_one_or_none()

    def create(self, patient: Patient) -> Patient:
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def save(self, patient: Patient) -> Patient:
        self.db.commit()
        self.db.refresh(patient)
        return patient