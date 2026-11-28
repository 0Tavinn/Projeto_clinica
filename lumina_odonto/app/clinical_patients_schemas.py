"""DTOs mínimos para selecionar um paciente no painel clínico."""

from pydantic import BaseModel


class ClinicalPatient(BaseModel):
    patient_id: int
    full_name: str
    medical_record_number: str
    medical_record_id: int | None
    access_link_id: int


class ClinicalPatientPage(BaseModel):
    items: list[ClinicalPatient]
    limit: int
    next_after_id: int | None
