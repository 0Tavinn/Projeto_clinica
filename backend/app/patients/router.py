"""Endpoints do CRUD de pacientes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.patients import service
from app.patients.models import Patient
from app.patients.schemas import PatientCreate, PatientRead, PatientUpdate
from app.security.permissions import (
    require_any_staff,
    require_patient_manager,
    require_patient_editor,  # <-- Nova permissão incluindo o Dentista
)
from app.users.models import User

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post(
    "",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um paciente na clínica do usuário autenticado.",
)
def create_patient(
    payload: PatientCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_patient_editor)],  # <-- Admin, Recepcionista e Dentista
) -> Patient:
    try:
        return service.create_patient(
            db,
            clinic_id=current_user.clinic_id,
            payload=payload,
        )
    except service.PatientConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[PatientRead],
    summary="Lista os pacientes ativos da clínica.",
)
def list_patients(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_any_staff)],
) -> list[Patient]:
    return service.list_patients(db, clinic_id=current_user.clinic_id)


@router.get(
    "/{patient_id}",
    response_model=PatientRead,
    summary="Consulta um paciente ativo pelo identificador.",
)
def get_patient(
    patient_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_any_staff)],
) -> Patient:
    patient = service.get_patient(
        db,
        clinic_id=current_user.clinic_id,
        patient_id=patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente não encontrado.",
        )

    return patient


@router.patch(
    "/{patient_id}",
    response_model=PatientRead,
    summary="Atualiza os dados de um paciente ativo.",
)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_patient_editor)],  # <-- Admin, Recepcionista e Dentista
) -> Patient:
    try:
        patient = service.update_patient(
            db,
            clinic_id=current_user.clinic_id,
            patient_id=patient_id,
            payload=payload,
        )
    except service.PatientValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except service.PatientConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente não encontrado.",
        )

    return patient


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Inativa um paciente sem apagar seu histórico.",
)
def deactivate_patient(
    patient_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_patient_manager)],  # <-- Mantido restrito (Admin e Recepcionista)
) -> Response:
    deactivated = service.deactivate_patient(
        db,
        clinic_id=current_user.clinic_id,
        patient_id=patient_id,
    )

    if not deactivated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente não encontrado.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)