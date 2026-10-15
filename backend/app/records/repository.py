from sqlalchemy.orm import Session
from app.records.models import MedicalRecord, ClinicalEvolution

class RecordRepository:
    def __init__(self, db: Session):
        self.db = db

    # -- Prontuários --
    def get_medical_record_by_patient(self, patient_id: int) -> MedicalRecord:
        return self.db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).first()

    def create_medical_record(self, patient_id: int, general_notes: str = None) -> MedicalRecord:
        record = MedicalRecord(patient_id=patient_id, general_notes=general_notes)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    # -- Evoluções --
    def get_evolutions_by_record(self, medical_record_id: int) -> list[ClinicalEvolution]:
        # Traz as mais recentes primeiro
        return self.db.query(ClinicalEvolution).filter(
            ClinicalEvolution.medical_record_id == medical_record_id
        ).order_by(ClinicalEvolution.recorded_at.desc()).all()

    def get_evolution_by_id(self, evolution_id: int) -> ClinicalEvolution:
        return self.db.query(ClinicalEvolution).filter(ClinicalEvolution.id == evolution_id).first()

    def create_evolution(self, evolution: ClinicalEvolution) -> ClinicalEvolution:
        self.db.add(evolution)
        self.db.commit()
        self.db.refresh(evolution)
        return evolution

    def update_evolution(self, evolution: ClinicalEvolution) -> ClinicalEvolution:
        self.db.commit()
        self.db.refresh(evolution)
        return evolution