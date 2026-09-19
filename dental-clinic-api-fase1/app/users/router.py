"""Endpoints de autenticação."""
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.security.auth import CurrentUser
from app.security.rate_limit import enforce_login_rate_limit
from app.users import service
from app.users.schemas import RefreshRequest, Token, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Token,
    summary="Autentica um usuário ativo e emite tokens JWT.",
    dependencies=[Depends(enforce_login_rate_limit)],
)
def login(
    db: Annotated[Session, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Perfil autorizado: qualquer usuário ativo (autenticação em si não exige
    role específica — a autorização por perfil acontece nos demais
    endpoints).

    `form_data.username` é o email do usuário (padrão OAuth2 Password
    Bearer do FastAPI usa o campo `username`).

    Respostas:
    - 200: tokens emitidos.
    - 401: email ou senha inválidos, ou usuário inativo.
    - 429: número de tentativas excedido (rate limit do endpoint).
    """
    return service.login(db, email=form_data.username, password=form_data.password)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renova o par access/refresh token a partir de um refresh token válido.",
)
def refresh(
    payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]
) -> Token:
    """
    Respostas:
    - 200: novo par de tokens emitido.
    - 401: refresh token inválido, expirado, ou usuário inativo/inexistente.
    """
    return service.refresh_access_token(db, refresh_token=payload.refresh_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Retorna os dados do usuário autenticado.",
)
def read_me(current_user: CurrentUser) -> UserRead:
    """
    Perfil autorizado: qualquer usuário autenticado ativo.

    Respostas:
    - 200: dados do usuário atual.
    - 401: token ausente, inválido, expirado, ou usuário inativo.
    """
    return UserRead.model_validate(current_user)
