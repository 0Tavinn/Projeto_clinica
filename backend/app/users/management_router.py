"""Endpoints administrativos para gerenciamento de usuários."""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.security.permissions import require_administrator
from app.users import service
from app.users.models import User
from app.users.schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=List[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Lista todos os usuários da clínica do administrador autenticado.",
)
def list_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_administrator)],
) -> List[User]:
    """Retorna a lista de usuários da equipe para a gestão administrativa."""
    return service.list_users_by_clinic(db, clinic_id=current_user.clinic_id)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um usuário na clínica do administrador autenticado.",
)
def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_administrator)],
) -> User:
    try:
        return service.create_user(
            db,
            clinic_id=current_user.clinic_id,
            payload=payload,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error