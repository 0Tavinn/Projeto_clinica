"""Acesso clínico provisório, restrito a atendimentos atribuídos ao dentista."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.appointments.models import Appointment, AppointmentStatus
from app.common.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
    ValidationAppError,
)
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.models import ClinicalEvolution
from app.records.repository import RecordRepository
from app.records.schemas import ClinicalEvolutionDraftCreate, ClinicalEvolutionUpdate
from app.security.roles import Role
from app.users.models import Clinic, User


class RecordService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.repo = RecordRepository(db)
        self.current_user = current_user
        if current_user.role is not Role.DENTIST:
            raise ForbiddenError("Apenas dentistas podem acessar conteúdo clínico.")
        clinic = db.get(Clinic, current_user.clinic_id)
        if clinic is None or not clinic.is_active:
            raise ForbiddenError("A clínica deve estar ativa para acessar conteúdo clínico.")
        self.dentist = db.execute(
            select(Dentist).where(Dentist.user_id == current_user.id)
        ).scalar_one_or_none()
        if self.dentist is None:
            raise ForbiddenError("Perfil profissional de dentista não encontrado.")

    def _patient(self, patient_id: int) -> Patient:
        patient = self.db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.clinic_id == self.current_user.clinic_id,
                Patient.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if patient is None:
            raise NotFoundError("Paciente não encontrado.")
        return patient

    def _require_assigned_appointment(self, patient_id: int) -> None:
        # Sem regra aprovada para atendimento sem agendamento, não há acesso.
        allowed = self.db.execute(
            select(Appointment.id).where(
                Appointment.clinic_id == self.current_user.clinic_id,
                Appointment.patient_id == patient_id,
                Appointment.dentist_id == self.dentist.id,
                Appointment.status.in_((
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.COMPLETED,
                )),
            ).limit(1)
        ).scalar_one_or_none()
        if allowed is None:
            raise ForbiddenError("Não há atendimento atribuído a este dentista para o paciente.")

    def _require_completed_appointment(self, appointment_id: int | None, patient_id: int) -> None:
        if appointment_id is None:
            raise ValidationAppError("Informe uma consulta concluída sob sua responsabilidade.")
        appointment = self.db.execute(
            select(Appointment.id).where(
                Appointment.id == appointment_id,
                Appointment.clinic_id == self.current_user.clinic_id,
                Appointment.patient_id == patient_id,
                Appointment.dentist_id == self.dentist.id,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
        ).scalar_one_or_none()
        if appointment is None:
            raise ForbiddenError("A consulta não autoriza este registro clínico.")

    def get_medical_record(self, patient_id: int) -> dict:
        self._patient(patient_id)
        self._require_assigned_appointment(patient_id)
        record = self.repo.get_medical_record_by_patient(patient_id)
        if record is None:
            raise NotFoundError("Prontuário ainda não aberto para este paciente.")
        # Observações gerais e histórico de outros autores dependem de regra da equipe.
        return {
            "id": record.id,
            "patient_id": record.patient_id,
            "general_notes": None,
            "opened_at": record.opened_at,
            "updated_at": record.updated_at,
        }

    def list_evolutions(self, patient_id: int) -> list[ClinicalEvolution]:
        self._patient(patient_id)
        self._require_assigned_appointment(patient_id)
        record = self.repo.get_medical_record_by_patient(patient_id)
        if record is None:
            raise NotFoundError("Prontuário ainda não aberto para este paciente.")
        return self.repo.list_own_evolutions(
            medical_record_id=record.id,
            dentist_id=self.dentist.id,
            patient_id=patient_id,
            clinic_id=self.current_user.clinic_id,
        )

    def create_evolution_draft(self, data: ClinicalEvolutionDraftCreate) -> ClinicalEvolution:
        self._patient(data.patient_id)
        self._require_completed_appointment(data.appointment_id, data.patient_id)
        record = self.repo.get_medical_record_by_patient(data.patient_id)
        if record is None:
            raise NotFoundError("Prontuário ainda não aberto para este paciente.")
        evolution = ClinicalEvolution(
            medical_record_id=record.id,
            dentist_id=self.dentist.id,
            appointment_id=data.appointment_id,
            description=data.description,
            procedure_performed=data.procedure_performed,
            notes=data.notes,
            status="DRAFT",
        )
        self.db.add(evolution)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Esta consulta já possui uma evolução clínica.") from error
        self.db.refresh(evolution)
        return evolution

    def _own_evolution_for_update(self, evolution_id: int) -> ClinicalEvolution:
        evolution = self.repo.get_own_evolution_for_update(
            evolution_id=evolution_id,
            dentist_id=self.dentist.id,
            clinic_id=self.current_user.clinic_id,
        )
        if evolution is None:
            raise NotFoundError("Evolução clínica não encontrada.")
        self._patient(evolution.medical_record.patient_id)
        return evolution

    def update_draft(self, evolution_id: int, data: ClinicalEvolutionUpdate) -> ClinicalEvolution:
        evolution = self._own_evolution_for_update(evolution_id)
        if evolution.status != "DRAFT":
            raise InvalidTransitionError("Evoluções finalizadas não podem ser editadas.")
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            raise ValidationAppError("Informe ao menos um campo para atualizar o rascunho.")
        for field, value in changes.items():
            setattr(evolution, field, value)
        self.db.commit()
        self.db.refresh(evolution)
        return evolution

    def finalize_evolution(self, evolution_id: int) -> ClinicalEvolution:
        evolution = self._own_evolution_for_update(evolution_id)
        if evolution.status != "DRAFT":
            raise InvalidTransitionError("Esta evolução já está finalizada.")
        if not evolution.description.strip():
            raise ValidationAppError("Informe a descrição clínica antes de finalizar.")
        evolution.status = "FINALIZED"
        evolution.finalized_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(evolution)
        return evolution
