from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.security.auth import CurrentUser

from app.records.schemas import (
    MedicalRecordResponse, 
    ClinicalEvolutionResponse, 
    ClinicalEvolutionDraftCreate, 
    ClinicalEvolutionUpdate
)
from app.records.service import RecordService

router = APIRouter(prefix="/patients", tags=["Medical Records & Evolutions"])

@router.get("/{patient_id}/record", response_model=MedicalRecordResponse)
def get_or_open_medical_record(
    patient_id: int, 
    current_user: CurrentUser, 
    db: Session = Depends(get_db)
):
    # O RecordService faz o bloqueio de Admin/Recepcionista logo ao instanciar
    service = RecordService(db, current_user)
    return service.get_or_create_medical_record(patient_id)


@router.get("/{patient_id}/evolutions", response_model=List[ClinicalEvolutionResponse])
def list_clinical_evolutions(
    patient_id: int, 
    current_user: CurrentUser, 
    db: Session = Depends(get_db)
):
    service = RecordService(db, current_user)
    return service.list_evolutions(patient_id)


@router.post("/evolutions", response_model=ClinicalEvolutionResponse, status_code=status.HTTP_201_CREATED)
def create_evolution_draft(
    data: ClinicalEvolutionDraftCreate, 
    current_user: CurrentUser, 
    db: Session = Depends(get_db)
):
    service = RecordService(db, current_user)
    # Não precisa passar dentist_id; o serviço extrai ele de forma segura internamente
    return service.create_evolution_draft(data)


@router.patch("/evolutions/{evolution_id}/draft", response_model=ClinicalEvolutionResponse)
def update_evolution_draft(
    evolution_id: int, 
    data: ClinicalEvolutionUpdate, 
    current_user: CurrentUser, 
    db: Session = Depends(get_db)
):
    service = RecordService(db, current_user)
    return service.update_draft(evolution_id, data)


@router.post("/evolutions/{evolution_id}/finalize", response_model=ClinicalEvolutionResponse)
def finalize_evolution(
    evolution_id: int, 
    current_user: CurrentUser, 
    db: Session = Depends(get_db)
):
    service = RecordService(db, current_user)
    return service.finalize_evolution(evolution_id)