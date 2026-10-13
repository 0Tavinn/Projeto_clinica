"""Contratos do cadastro profissional."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DentistCreate(BaseModel):
    user_id: int = Field(gt=0)
    cro_number: str = Field(min_length=1, max_length=30)
    cro_state: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    specialty: str | None = Field(default=None, max_length=100)


class DentistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    full_name: str
    cro_number: str
    cro_state: str
    specialty: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
