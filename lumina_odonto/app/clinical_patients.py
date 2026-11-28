"""Rotas de identificação mínima para o próprio dentista autenticado."""

from fastapi import APIRouter, Depends, Path, Query
from app.clinical_patients_schemas import ClinicalPatient, ClinicalPatientPage
from app import clinical_patients_service as service

router=APIRouter(prefix="/api/v1/clinical/patients",tags=["Pacientes clínicos"])


def install(app):
    """Registra antes da política de logging capturar as rotas estáticas."""
    from app import main as m

    @router.get("",response_model=ClinicalPatientPage)
    def patients(
        limit:int=Query(50,ge=1,le=100),after_id:int=Query(0,ge=0),
        q:str|None=Query(None,min_length=1,max_length=128),
        user=Depends(m.clinical_user),db=Depends(m.db_dep),
    ):
        return service.list_patients(db,user,limit=limit,after_id=after_id,query=q)

    @router.get("/{patient_id}",response_model=ClinicalPatient)
    def patient(
        patient_id:int=Path(gt=0),
        user=Depends(m.clinical_user),db=Depends(m.db_dep),
    ):
        return service.get_patient(db,user,patient_id)

    app.include_router(router)
