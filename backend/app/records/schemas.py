from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List
from datetime import datetime

# --- Schemas Auxiliares ---
class DentistInfoResponse(BaseModel):
    """Sub-schema para exibir os dados do autor da evolução."""
    id: int
    full_name: str
    cro_number: str
    cro_state: str

    class Config:
        from_attributes = True

# --- Medical Record Schemas ---
class MedicalRecordBase(BaseModel):
    general_notes: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    patient_id: int

class MedicalRecordResponse(MedicalRecordBase):
    id: int
    patient_id: int
    opened_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Clinical Evolution Schemas ---
class ClinicalEvolutionBase(BaseModel):
    description: str
    procedure_performed: Optional[str] = None
    notes: Optional[str] = None
    appointment_id: Optional[int] = None

# ✅ Recebe o patient_id em vez do medical_record_id
class ClinicalEvolutionDraftCreate(ClinicalEvolutionBase):
    model_config = ConfigDict(extra="forbid")

    patient_id: int = Field(gt=0)
    appointment_id: int | None = Field(default=None, gt=0)

class ClinicalEvolutionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Optional[str] = None
    procedure_performed: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("description")
    @classmethod
    def reject_null_description(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("A descrição não pode ser nula.")
        return value

class ClinicalEvolutionResponse(ClinicalEvolutionBase):
    id: int
    medical_record_id: int
    status: str
    recorded_at: datetime
    finalized_at: Optional[datetime]
    created_at: datetime
    
    # ✅ Substitui o dentist_id isolado pelo objeto completo do profissional
    dentist: DentistInfoResponse

    class Config:
        from_attributes = True
