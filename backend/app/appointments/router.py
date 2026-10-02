"""Rotas HTTP da agenda."""
import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.appointments import service
from app.appointments.models import Appointment, AppointmentStatus
from app.appointments.schemas import AppointmentCreate, AppointmentRead, AppointmentUpdate
from app.core.database import get_db
from app.security.auth import get_current_user
from app.security.permissions import require_any_staff, require_patient_manager
from app.users.models import User

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_patient_manager)],
) -> Appointment:
    return service.create_appointment(db, clinic_id=current_user.clinic_id, payload=payload)


@router.get("", response_model=list[AppointmentRead])
def list_appointments(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_any_staff)],
    start: datetime.datetime | None = Query(default=None),
    end: datetime.datetime | None = Query(default=None),
    dentist_id: int | None = Query(default=None, gt=0),
    patient_id: int | None = Query(default=None, gt=0),
    appointment_status: AppointmentStatus | None = Query(default=None, alias="status"),
) -> list[Appointment]:
    return service.list_appointments(
        db,
        clinic_id=current_user.clinic_id,
        current_user=current_user,
        start=start,
        end=end,
        dentist_id=dentist_id,
        patient_id=patient_id,
        status=appointment_status,
    )


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(
    appointment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_any_staff)],
) -> Appointment:
    return service.get_appointment(
        db, clinic_id=current_user.clinic_id, appointment_id=appointment_id, current_user=current_user
    )


@router.patch("/{appointment_id}", response_model=AppointmentRead)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Appointment:
    return service.update_appointment(
        db,
        clinic_id=current_user.clinic_id,
        appointment_id=appointment_id,
        current_user=current_user,
        payload=payload,
    )


@router.post("/{appointment_id}/cancel", response_model=AppointmentRead)
def cancel_appointment(
    appointment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_patient_manager)],
) -> Appointment:
    return service.cancel_appointment(
        db, clinic_id=current_user.clinic_id, appointment_id=appointment_id
    )
