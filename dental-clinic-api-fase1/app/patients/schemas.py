"""Schemas de entrada e saída do CRUD de pacientes."""
import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    cpf: str = Field(
        min_length=11,
        max_length=11,
        pattern=r"^\d{11}$",
        description="CPF com 11 dígitos, sem pontuação.",
    )
    medical_record_number: str = Field(min_length=1, max_length=30)
    birth_date: datetime.date
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    address: str | None = None


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    cpf: str | None = Field(
        default=None,
        min_length=11,
        max_length=11,
        pattern=r"^\d{11}$",
    )
    medical_record_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )
    birth_date: datetime.date | None = None
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    address: str | None = None


class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinic_id: int
    full_name: str
    cpf: str
    medical_record_number: str
    birth_date: datetime.date
    phone: str | None
    email: EmailStr | None
    address: str | None
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime