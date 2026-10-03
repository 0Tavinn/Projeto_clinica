"""Cadastro dos dados profissionais dos dentistas."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, ValidationAppError
from app.core.database import get_db
from app.dentists.models import Dentist
from app.dentists.schemas import DentistCreate, DentistRead
from app.security.permissions import require_administrator, require_patient_manager
from app.security.roles import Role
from app.users.models import Clinic, User

router = APIRouter(prefix="/dentists", tags=["dentists"])


def _ensure_active_clinic(db: Session, clinic_id: int) -> None:
    clinic = db.get(Clinic, clinic_id)
    if clinic is None or not clinic.is_active:
        raise ValidationAppError("A clínica deve estar ativa.")


@router.get("", response_model=list[DentistRead])
def list_dentists(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_patient_manager)],
) -> list[Dentist]:
    _ensure_active_clinic(db, current_user.clinic_id)
    statement = (
        select(Dentist)
        .join(User, User.id == Dentist.user_id)
        .where(
            User.clinic_id == current_user.clinic_id,
            User.role == Role.DENTIST,
            User.is_active.is_(True),
        )
        .order_by(User.full_name)
    )
    return list(db.execute(statement).scalars().all())


@router.post("", response_model=DentistRead, status_code=201)
def create_dentist(
    payload: DentistCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_administrator)],
) -> Dentist:
    _ensure_active_clinic(db, current_user.clinic_id)
    user = db.execute(
        select(User).where(User.id == payload.user_id, User.clinic_id == current_user.clinic_id)
    ).scalar_one_or_none()
    if user is None or user.role is not Role.DENTIST:
        raise ValidationAppError("O usuário deve ser um dentista da mesma clínica.")
    dentist = Dentist(
        user_id=user.id,
        cro_number=payload.cro_number.strip().upper(),
        cro_state=payload.cro_state.upper(),
        specialty=payload.specialty.strip() if payload.specialty else None,
    )
    db.add(dentist)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ConflictError("O usuário ou o CRO já possui cadastro profissional.") from error
    db.refresh(dentist)
    return dentist
