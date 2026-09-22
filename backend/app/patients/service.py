"""Regras de negócio do CRUD de pacientes."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.patients.models import Patient
from app.patients.repository import PatientRepository
from app.patients.schemas import PatientCreate, PatientUpdate


class PatientConflictError(Exception):
    """Indica CPF ou prontuário duplicado na mesma clínica."""


class PatientValidationError(Exception):
    """Indica dados insuficientes para atualizar o paciente."""


def list_patients(db: Session, clinic_id: int) -> list[Patient]:
    repository = PatientRepository(db)
    return repository.list_active_by_clinic(clinic_id)


def get_patient(
    db: Session,
    clinic_id: int,
    patient_id: int,
) -> Patient | None:
    repository = PatientRepository(db)
    return repository.get_active_by_id(patient_id, clinic_id)


def create_patient(
    db: Session,
    *,
    clinic_id: int,
    payload: PatientCreate,
) -> Patient:
    repository = PatientRepository(db)

    patient = Patient(
        clinic_id=clinic_id,
        full_name=payload.full_name.strip(),
        cpf=payload.cpf,
        medical_record_number=payload.medical_record_number.strip().upper(),
        birth_date=payload.birth_date,
        phone=payload.phone.strip() if payload.phone else None,
        email=str(payload.email).lower() if payload.email else None,
        address=payload.address.strip() if payload.address else None,
        is_active=True,
    )

    try:
        return repository.create(patient)
    except IntegrityError as error:
        db.rollback()
        raise PatientConflictError(
            "Já existe um paciente com este CPF ou número de prontuário nesta clínica."
        ) from error


def update_patient(
    db: Session,
    *,
    clinic_id: int,
    patient_id: int,
    payload: PatientUpdate,
) -> Patient | None:
    repository = PatientRepository(db)
    patient = repository.get_active_by_id(patient_id, clinic_id)

    if patient is None:
        return None

    changes = payload.model_dump(exclude_unset=True, exclude_none=True)

    if not changes:
        raise PatientValidationError(
            "Informe ao menos um campo para atualizar o paciente."
        )

    if "full_name" in changes:
        changes["full_name"] = changes["full_name"].strip()

    if "medical_record_number" in changes:
        changes["medical_record_number"] = (
            changes["medical_record_number"].strip().upper()
        )

    if "phone" in changes:
        changes["phone"] = changes["phone"].strip()

    if "email" in changes:
        changes["email"] = str(changes["email"]).lower()

    if "address" in changes:
        changes["address"] = changes["address"].strip()

    for field_name, value in changes.items():
        setattr(patient, field_name, value)

    try:
        return repository.save(patient)
    except IntegrityError as error:
        db.rollback()
        raise PatientConflictError(
            "Já existe um paciente com este CPF ou número de prontuário nesta clínica."
        ) from error


def deactivate_patient(
    db: Session,
    *,
    clinic_id: int,
    patient_id: int,
) -> bool:
    repository = PatientRepository(db)
    patient = repository.get_active_by_id(patient_id, clinic_id)

    if patient is None:
        return False

    patient.is_active = False
    repository.save(patient)
    return True