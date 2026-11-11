from pydantic import BaseModel, Field, StrictInt, field_validator
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
    patient_id: int
    appointment_id: int = Field(gt=0)

    @field_validator("description")
    @classmethod
    def require_description(cls, value: str) -> str:
        """Texto composto somente por espaços não descreve o atendimento."""
        if not value.strip():
            raise ValueError("Informe a descrição clínica.")
        return value

class ClinicalEvolutionUpdate(BaseModel):
    # A versão lida é obrigatória: omiti-la contornaria o controle concorrente.
    version: StrictInt = Field(ge=1)
    description: Optional[str] = None
    procedure_performed: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Informe a descrição clínica.")
        return value

class ClinicalEvolutionResponse(ClinicalEvolutionBase):
    id: int
    medical_record_id: int
    status: str
    version: int
    recorded_at: datetime
    finalized_at: Optional[datetime]
    created_at: datetime
    
    # ✅ Substitui o dentist_id isolado pelo objeto completo do profissional
    dentist: DentistInfoResponse

    class Config:
        from_attributes = True
