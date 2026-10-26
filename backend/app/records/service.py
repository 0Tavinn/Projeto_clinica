from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.records.access import require_clinical_access
from app.records.repository import RecordRepository
from app.records.models import ClinicalEvolution, MedicalRecord
from app.records.schemas import ClinicalEvolutionDraftCreate, ClinicalEvolutionUpdate
from app.users.models import User
from app.security.roles import Role

# Importando da sua arquitetura real
from app.common.exceptions import (
    NotFoundError,
    ForbiddenError,
    InvalidTransitionError
)

class RecordService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.repo = RecordRepository(db)
        self.current_user = current_user

        # Trava global
        if self.current_user.role != Role.DENTIST:
            raise ForbiddenError("Apenas profissionais de saúde podem acessar conteúdos clínicos.")

    def _verify_patient_access(self, patient_id: int):
        """Confere o vínculo antes de ler ou criar conteúdo do prontuário."""
        patient, _ = require_clinical_access(
            self.db,
            current_user=self.current_user,
            patient_id=patient_id,
        )
        return patient

    def get_or_create_medical_record(self, patient_id: int, general_notes: str = None):
        self._verify_patient_access(patient_id)
        record = self.repo.get_medical_record_by_patient(patient_id)
        if not record:
            record = self.repo.create_medical_record(patient_id, general_notes)
        return record

    def list_evolutions(self, patient_id: int):
        self._verify_patient_access(patient_id)
        record = self.repo.get_medical_record_by_patient(patient_id)
        if not record:
            raise NotFoundError("Prontuário ainda não foi aberto para este paciente.")
        return self.repo.get_evolutions_by_record(
            record.id,
            dentist_id=self.current_user.dentist.id,
        )

    def create_evolution_draft(self, data: ClinicalEvolutionDraftCreate):
        self._verify_patient_access(data.patient_id)
        record = self.get_or_create_medical_record(patient_id=data.patient_id)
        
        evolution = ClinicalEvolution(
            medical_record_id=record.id,
            dentist_id=self.current_user.dentist.id,
            appointment_id=data.appointment_id,
            description=data.description,
            procedure_performed=data.procedure_performed,
            notes=data.notes,
            status="DRAFT"
        )
        return self.repo.create_evolution(evolution)

    def _verify_evolution_access(self, evolution_id: int) -> ClinicalEvolution:
        """Autoriza pelo paciente antes de carregar o texto da evolução."""
        patient_id = self.repo.get_patient_id_for_evolution(evolution_id)
        if patient_id is None:
            raise NotFoundError("Evolução clínica não encontrada.")

        self._verify_patient_access(patient_id)

        evolution = self.repo.get_evolution_by_id(evolution_id)
        if evolution is None:
            raise NotFoundError("Evolução clínica não encontrada.")
        return evolution

    def update_draft(self, evolution_id: int, data: ClinicalEvolutionUpdate):
        evolution = self._verify_evolution_access(evolution_id)
        
        if evolution.status == "FINALIZED":
            raise InvalidTransitionError("Registro inalterável: Evoluções finalizadas não podem ser editadas.")

        if evolution.dentist_id != self.current_user.dentist.id:
            raise ForbiddenError("Você só pode editar seus próprios rascunhos.")

        if data.description is not None: evolution.description = data.description
        if data.procedure_performed is not None: evolution.procedure_performed = data.procedure_performed
        if data.notes is not None: evolution.notes = data.notes

        return self.repo.update_evolution(evolution)

    def finalize_evolution(self, evolution_id: int):
        evolution = self._verify_evolution_access(evolution_id)
        
        if evolution.dentist_id != self.current_user.dentist.id:
            raise ForbiddenError("Você só pode finalizar suas próprias evoluções.")
        
        if evolution.status == "FINALIZED":
            raise InvalidTransitionError("Esta evolução já está finalizada.")

        evolution.status = "FINALIZED"
        evolution.finalized_at = datetime.now(timezone.utc)
        
        return self.repo.update_evolution(evolution)

    def delete_evolution(self, evolution_id: int):
        evolution = self._verify_evolution_access(evolution_id)

        if evolution.status == "FINALIZED":
            raise InvalidTransitionError("Violação de Prontuário: É legalmente proibido excluir uma evolução clínica finalizada.")

        if evolution.dentist_id != self.current_user.dentist.id:
            raise ForbiddenError("Você só pode excluir seus próprios rascunhos.")

        self.repo.delete_evolution(evolution)