"""Contratos HTTP dos agendamentos."""
import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.appointments.models import AppointmentStatus

# Validação de horário de realização do atendimento
def _validate_care_time(
    status: AppointmentStatus | None,
    care_occurred_at: datetime.datetime | None,
    *,
    supplied: bool,
) -> None:
    """Exige horário informado somente na solicitação de conclusão."""
    if status is AppointmentStatus.COMPLETED:
        if care_occurred_at is None:
            raise ValueError("Informe o horário da realização do atendimento.")
    elif supplied:
        raise ValueError("O horário da realização só pode acompanhar COMPLETED.")


class AppointmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int = Field(gt=0)
    dentist_id: int = Field(gt=0)
    scheduled_at: datetime.datetime
    duration_minutes: int = Field(default=30, gt=0)
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int | None = Field(default=None, gt=0)
    dentist_id: int | None = Field(default=None, gt=0)
    scheduled_at: datetime.datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    notes: str | None = None
    status: AppointmentStatus | None = None
    care_occurred_at: AwareDatetime | None = None


    @field_validator("scheduled_at", "duration_minutes")
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError("O campo não pode ser nulo quando informado.")
        return value
# Validação de horário de realização do atendimento
    @model_validator(mode="after")
    def validate_care_time(self):
        _validate_care_time(
            self.status,
            self.care_occurred_at,
            supplied="care_occurred_at" in self.model_fields_set,
        )
        return self


class AppointmentStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AppointmentStatus
    # Validação de horário de realização do atendimento
    care_occurred_at: AwareDatetime | None = None

    # Validação de horário de realização do atendimento
    @model_validator(mode="after")
    def validate_care_time(self):
        _validate_care_time(
            self.status,
            self.care_occurred_at,
            supplied="care_occurred_at" in self.model_fields_set,
        )
        return self


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinic_id: int
    patient_id: int
    patient_name: str
    dentist_id: int
    dentist_name: str
    scheduled_at: datetime.datetime
    status: AppointmentStatus
    notes: str | None
    duration_minutes: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
