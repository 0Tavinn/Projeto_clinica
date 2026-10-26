from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, lazyload

from app.appointments.models import Appointment
from app.patients.models import Patient
from app.records.models import ClinicalEvolution, MedicalRecord


class RecordRepository:
    def __init__(self, db: Session):
        self.db = db

    # -- Prontuários --
    def lock_patient(self, patient_id: int) -> bool:
        """Serializa a abertura do prontuário por paciente no PostgreSQL."""
        statement = (
            select(Patient.id)
            .where(Patient.id == patient_id)
            .with_for_update(of=Patient)
        )
        return self.db.execute(statement).scalar_one_or_none() is not None

    def get_medical_record_by_patient(self, patient_id: int) -> MedicalRecord:
        return self.db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).first()

    def add_medical_record(self, patient_id: int, general_notes: str = None) -> MedicalRecord:
        """Insere sem commit para compor abertura e evolução numa transação."""
        record = MedicalRecord(patient_id=patient_id, general_notes=general_notes)
        self.db.add(record)
        self.db.flush()
        return record

    def create_medical_record(self, patient_id: int, general_notes: str = None) -> MedicalRecord:
        record = self.add_medical_record(patient_id, general_notes)
        self.db.commit()
        self.db.refresh(record)
        return record

    # -- Evoluções --
    def get_appointment_for_update(
        self, appointment_id: int, clinic_id: int
    ) -> Appointment | None:
        """Bloqueia só a consulta vinculada, sem JOINs dos relacionamentos."""
        statement = (
            select(Appointment)
            .where(Appointment.id == appointment_id, Appointment.clinic_id == clinic_id)
            .options(lazyload(Appointment.patient), lazyload(Appointment.dentist))
            .execution_options(populate_existing=True)
            .with_for_update(of=Appointment)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_evolution_id_for_appointment(self, appointment_id: int) -> int | None:
        statement = select(ClinicalEvolution.id).where(
            ClinicalEvolution.appointment_id == appointment_id
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_evolutions_by_record(
        self, medical_record_id: int, *, dentist_id: int
    ) -> list[ClinicalEvolution]:
        """Retorna finalizadas e apenas rascunhos do dentista leitor."""
        visible = or_(
            ClinicalEvolution.status == "FINALIZED",
            and_(
                ClinicalEvolution.status == "DRAFT",
                ClinicalEvolution.dentist_id == dentist_id,
            ),
        )
        return (
            self.db.query(ClinicalEvolution)
            .filter(
                ClinicalEvolution.medical_record_id == medical_record_id,
                visible,
            )
            .order_by(ClinicalEvolution.recorded_at.desc())
            .all()
        )

    def get_evolution_reference(self, evolution_id: int) -> tuple[int, int, int] | None:
        """Obtém paciente, prontuário e autor antes de carregar texto clínico."""
        statement = (
            select(
                MedicalRecord.patient_id,
                ClinicalEvolution.medical_record_id,
                ClinicalEvolution.dentist_id,
            )
            .join(
                ClinicalEvolution,
                ClinicalEvolution.medical_record_id == MedicalRecord.id,
            )
            .where(ClinicalEvolution.id == evolution_id)
        )
        row = self.db.execute(statement).one_or_none()
        return tuple(row) if row is not None else None

    def get_patient_id_for_evolution(self, evolution_id: int) -> int | None:
        """Mantém a projeção simples usada por verificações anteriores."""
        reference = self.get_evolution_reference(evolution_id)
        return reference[0] if reference is not None else None

    def get_evolution_for_update(self, evolution_id: int) -> ClinicalEvolution | None:
        """Serializa mutações sem bloquear tabelas relacionadas por JOIN."""
        statement = (
            select(ClinicalEvolution)
            .where(ClinicalEvolution.id == evolution_id)
            .options(
                lazyload(ClinicalEvolution.medical_record),
                lazyload(ClinicalEvolution.dentist),
            )
            .execution_options(populate_existing=True)
            .with_for_update(of=ClinicalEvolution)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_evolution_by_id(self, evolution_id: int) -> ClinicalEvolution:
        return self.db.query(ClinicalEvolution).filter(ClinicalEvolution.id == evolution_id).first()

    def create_evolution(self, evolution: ClinicalEvolution) -> ClinicalEvolution:
        self.add_evolution(evolution)
        self.db.commit()
        self.db.refresh(evolution)
        return evolution

    def add_evolution(self, evolution: ClinicalEvolution) -> ClinicalEvolution:
        """Prepara a evolução sem encerrar a transação do prontuário."""
        self.db.add(evolution)
        self.db.flush()
        return evolution

    def update_evolution(self, evolution: ClinicalEvolution) -> ClinicalEvolution:
        self.db.commit()
        self.db.refresh(evolution)
        return evolution

    def delete_evolution(self, evolution: ClinicalEvolution) -> None:
        self.db.delete(evolution)
        self.db.commit()
