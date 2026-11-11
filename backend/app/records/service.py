from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.appointments.models import AppointmentStatus
from app.common.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
    ValidationAppError,
)
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.access import require_clinical_access
from app.records.access_repository import ClinicalAccessGrantRepository
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

    def get_medical_record(self, patient_id: int) -> MedicalRecord:
        """Consulta sem criar; 404 permite oferecer abertura ao dentista."""
        self._verify_patient_access(patient_id)
        record = self.repo.get_medical_record_by_patient(patient_id)
        if record is None:
            raise NotFoundError("Prontuário ainda não foi aberto para este paciente.")
        return record

    def open_medical_record(self, patient_id: int) -> tuple[MedicalRecord, bool]:
        """Serializa aberturas e conserva o registro já confirmado."""
        _, dentist = self._verify_patient_access(patient_id)
        try:
            if not self.repo.lock_patient(patient_id):
                raise NotFoundError("Paciente não encontrado no sistema.")
            # Mantém estáveis as origens até o commit da abertura.
            ClinicalAccessGrantRepository(self.db).lock_origin_appointments(
                clinic_id=self.current_user.clinic_id,
                patient_id=patient_id,
                dentist_id=dentist.id,
            )
            # A autorização pode ter mudado enquanto aguardávamos os bloqueios.
            self._verify_patient_access(patient_id)
            record = self.repo.get_medical_record_by_patient(patient_id)
            created = record is None
            if record is None:
                record = self.repo.add_medical_record(patient_id)
            self.db.commit()
            self.db.refresh(record)
            return record, created
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
            self._require_writable_appointment(
                data.appointment_id, data.patient_id, dentist.id, finalizing=False
            )
            if self.repo.get_evolution_id_for_appointment(data.appointment_id) is not None:
                raise ConflictError("A consulta já possui evolução clínica.")

            record = self.repo.get_medical_record_by_patient(data.patient_id)
            if record is None:
                raise NotFoundError("Abra o prontuário antes de registrar a evolução.")

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
        # A consulta pode ter sido cancelada enquanto aguardávamos a evolução.
        # Bloquear as origens impede nova mudança de situação até o commit;
        # a consulta de acesso seguinte usa um snapshot PostgreSQL atualizado.
        ClinicalAccessGrantRepository(self.db).lock_origin_appointments(
            clinic_id=self.current_user.clinic_id,
            patient_id=patient_id,
            dentist_id=dentist.id,
        )
        self._verify_patient_access(patient_id)
        return evolution

    def _require_writable_appointment(
        self, appointment_id: int | None, patient_id: int,
        dentist_id: int, *, finalizing: bool,
    ) -> None:
        """O vínculo da evolução, e não outra origem, define o estado de escrita."""
        if appointment_id is None:
            raise InvalidTransitionError("Evolução sem consulta vinculada exige regularização.")
        # A criação também estabiliza todas as origens. Nas mutações de uma
        # evolução existente, este bloqueio já foi obtido antes de chegar aqui.
        ClinicalAccessGrantRepository(self.db).lock_origin_appointments(
            clinic_id=self.current_user.clinic_id,
            patient_id=patient_id,
            dentist_id=dentist_id,
        )
        appointment = self.repo.get_appointment_for_update(
            appointment_id, self.current_user.clinic_id
        )
        if (appointment is None or appointment.patient_id != patient_id
                or appointment.dentist_id != dentist_id):
            raise NotFoundError("Consulta vinculada não encontrada para este atendimento.")
        # Esperar a consulta pode ter invalidado o último fundamento de acesso.
        self._verify_patient_access(patient_id)
        allowed = ({AppointmentStatus.COMPLETED} if finalizing else
                   {AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED})
        if appointment.status not in allowed:
            raise InvalidTransitionError("Situação da consulta não permite esta escrita clínica.")

    def update_draft(self, evolution_id: int, data: ClinicalEvolutionUpdate):
        try:
            evolution = self._get_owned_evolution_for_update(evolution_id)
            if evolution.status != "DRAFT":
                raise InvalidTransitionError("Evoluções finalizadas não podem ser editadas.")
            patient_id = self.repo.get_patient_id_for_evolution(evolution_id)
            self._require_writable_appointment(
                evolution.appointment_id, patient_id, evolution.dentist_id, finalizing=False
            )
            if evolution.version != data.version:
                raise ConflictError("O rascunho foi alterado. Recarregue antes de editar novamente.")
            if not (data.description if data.description is not None else evolution.description).strip():
                raise ValidationAppError("Informe a descrição clínica.")
            if data.description is not None:
                evolution.description = data.description
            if data.procedure_performed is not None:
                evolution.procedure_performed = data.procedure_performed
            if data.notes is not None:
                evolution.notes = data.notes
            evolution.version += 1
            return self.repo.update_evolution(evolution)
        except Exception:
            self.db.rollback()
            raise

    def finalize_evolution(self, evolution_id: int):
        try:
            evolution = self._get_owned_evolution_for_update(evolution_id)
            if evolution.status != "DRAFT":
                raise InvalidTransitionError("Esta evolução já está finalizada.")
            patient_id = self.repo.get_patient_id_for_evolution(evolution_id)
            self._require_writable_appointment(
                evolution.appointment_id, patient_id, evolution.dentist_id, finalizing=True
            )
            if not evolution.description.strip():
                raise ValidationAppError("Informe a descrição clínica.")
            evolution.status = "FINALIZED"
            evolution.finalized_at = datetime.now(timezone.utc)
            evolution.version += 1
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
