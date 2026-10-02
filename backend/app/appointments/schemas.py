"""Contratos HTTP dos agendamentos."""
import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.appointments.models import AppointmentStatus


class AppointmentCreate(BaseModel):
    patient_id: int = Field(gt=0)
    dentist_id: int = Field(gt=0)
    scheduled_at: datetime.datetime
    duration_minutes: int = Field(default=30, gt=0)
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    patient_id: int | None = Field(default=None, gt=0)
    dentist_id: int | None = Field(default=None, gt=0)
    scheduled_at: datetime.datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    notes: str | None = None
    status: AppointmentStatus | None = None


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinic_id: int
    patient_id: int
    dentist_id: int
    scheduled_at: datetime.datetime
    status: AppointmentStatus
    notes: str | None
    duration_minutes: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
