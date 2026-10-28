from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
)
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.access import require_clinical_access
from app.records.models import ClinicalEvolution, MedicalRecord
from app.records.repository import RecordRepository
from app.records.schemas import ClinicalEvolutionDraftCreate, ClinicalEvolutionUpdate
from app.security.roles import Role
from app.users.models import User


class RecordService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.repo = RecordRepository(db)
        self.current_user = current_user

        if self.current_user.role is not Role.DENTIST:
            raise ForbiddenError("Apenas profissionais de saúde podem acessar conteúdos clínicos.")

    def _verify_patient_access(self, patient_id: int) -> tuple[Patient, Dentist]:
        """Confere o vínculo antes de ler ou criar conteúdo do prontuário."""
        return require_clinical_access(
            self.db,
            current_user=self.current_user,
            patient_id=patient_id,
        )

    def get_or_create_medical_record(
        self, patient_id: int, general_notes: str | None = None
    ) -> MedicalRecord:
        """Preserva o GET atual; D02 ainda definirá seu efeito de escrita."""
        self._verify_patient_access(patient_id)
        record = self.repo.get_medical_record_by_patient(patient_id)
        if record is not None:
            return record

        try:
            # O bloqueio do paciente serializa aberturas concorrentes.
            if not self.repo.lock_patient(patient_id):
                raise NotFoundError("Paciente não encontrado no sistema.")
            # A confirmação pode ter sido cancelada enquanto aguardávamos o bloqueio.
            self._verify_patient_access(patient_id)
            record = self.repo.get_medical_record_by_patient(patient_id)
            if record is None:
                record = self.repo.add_medical_record(patient_id, general_notes)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            self.db.rollback()
            raise

    def list_evolutions(self, patient_id: int) -> list[ClinicalEvolution]:
        _, dentist = self._verify_patient_access(patient_id)
        record = self.repo.get_medical_record_by_patient(patient_id)
        if record is None:
            raise NotFoundError("Prontuário ainda não foi aberto para este paciente.")
        return self.repo.get_evolutions_by_record(
            record.id,
            dentist_id=dentist.id,
        )

    def create_evolution_draft(
        self, data: ClinicalEvolutionDraftCreate
    ) -> ClinicalEvolution:
        _, dentist = self._verify_patient_access(data.patient_id)
        try:
            if data.appointment_id is not None:
                # A situação permitida para escrita segue pendente em D03.
                appointment = self.repo.get_appointment_for_update(
                    data.appointment_id, self.current_user.clinic_id
                )
                if (
                    appointment is None
                    or appointment.patient_id != data.patient_id
                    or appointment.dentist_id != dentist.id
                ):
                    raise NotFoundError("Consulta vinculada não encontrada para este atendimento.")
                # O estado da consulta pode mudar durante a espera pelo bloqueio.
                self._verify_patient_access(data.patient_id)
                if self.repo.get_evolution_id_for_appointment(data.appointment_id) is not None:
                    raise ConflictError("A consulta já possui evolução clínica.")

            record = self.repo.get_medical_record_by_patient(data.patient_id)
            if record is None:
                # A abertura e o rascunho compartilham o mesmo commit.
                if not self.repo.lock_patient(data.patient_id):
                    raise NotFoundError("Paciente não encontrado no sistema.")
                self._verify_patient_access(data.patient_id)
                record = self.repo.get_medical_record_by_patient(data.patient_id)
                if record is None:
                    record = self.repo.add_medical_record(data.patient_id)

            evolution = ClinicalEvolution(
                medical_record_id=record.id,
                dentist_id=dentist.id,
                appointment_id=data.appointment_id,
                description=data.description,
                procedure_performed=data.procedure_performed,
                notes=data.notes,
                status="DRAFT",
            )
            self.repo.add_evolution(evolution)
            self.db.commit()
            self.db.refresh(evolution)
            return evolution
        except IntegrityError as error:
            self.db.rollback()
            original = error.orig
            sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
            diagnostic = getattr(original, "diag", None)
            if (
                sqlstate == "23505"
                and getattr(diagnostic, "constraint_name", None)
                == "uq_clinical_evolutions_appointment"
            ):
                raise ConflictError("A consulta já possui evolução clínica.") from error
            raise
        except Exception:
            self.db.rollback()
            raise

    def _get_owned_evolution_for_update(self, evolution_id: int) -> ClinicalEvolution:
        """Autoriza sem texto clínico e depois bloqueia o rascunho para mutação."""
        reference = self.repo.get_evolution_reference(evolution_id)
        if reference is None:
            raise NotFoundError("Evolução clínica não encontrada.")
        patient_id, record_id, author_id = reference
        _, dentist = self._verify_patient_access(patient_id)
        if author_id != dentist.id:
            raise ForbiddenError("Você só pode alterar suas próprias evoluções.")

        evolution = self.repo.get_evolution_for_update(evolution_id)
        if (
            evolution is None
            or evolution.medical_record_id != record_id
            or evolution.dentist_id != author_id
        ):
            raise NotFoundError("Evolução clínica não encontrada.")
        return evolution

    def update_draft(self, evolution_id: int, data: ClinicalEvolutionUpdate):
        try:
            evolution = self._get_owned_evolution_for_update(evolution_id)
            if evolution.status != "DRAFT":
                raise InvalidTransitionError("Evoluções finalizadas não podem ser editadas.")
            if data.description is not None:
                evolution.description = data.description
            if data.procedure_performed is not None:
                evolution.procedure_performed = data.procedure_performed
            if data.notes is not None:
                evolution.notes = data.notes
            return self.repo.update_evolution(evolution)
        except Exception:
            self.db.rollback()
            raise

    def finalize_evolution(self, evolution_id: int):
        try:
            evolution = self._get_owned_evolution_for_update(evolution_id)
            if evolution.status != "DRAFT":
                raise InvalidTransitionError("Esta evolução já está finalizada.")
            evolution.status = "FINALIZED"
            evolution.finalized_at = datetime.now(timezone.utc)
            return self.repo.update_evolution(evolution)
        except Exception:
            self.db.rollback()
            raise

    def delete_evolution(self, evolution_id: int):
        try:
            evolution = self._get_owned_evolution_for_update(evolution_id)
            if evolution.status != "DRAFT":
                raise InvalidTransitionError("Evoluções finalizadas não podem ser excluídas.")
            self.repo.delete_evolution(evolution)
        except Exception:
            self.db.rollback()
            raise
