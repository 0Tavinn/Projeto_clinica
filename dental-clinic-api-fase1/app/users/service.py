"""Serviço de autenticação: orquestra repository + security para login/refresh."""
from sqlalchemy.orm import Session

from app.common.exceptions import UnauthorizedError
from app.security.auth import (
    REFRESH_TOKEN_TYPE,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.users.repository import UserRepository
from app.users.schemas import Token


def login(db: Session, email: str, password: str) -> Token:
    user = authenticate_user(db, email, password)
    return Token(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


def refresh_access_token(db: Session, refresh_token: str) -> Token:
    payload = decode_token(refresh_token)

    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise UnauthorizedError("Token informado não é um refresh token válido.")

    user_id = payload.get("sub")
    repo = UserRepository(db)
    user = repo.get_by_id(user_id) if user_id else None

    if user is None or not user.is_active:
        raise UnauthorizedError("Não foi possível renovar a sessão.")

    return Token(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )
