"""Serviços de autenticação e cadastro de usuários."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import UnauthorizedError
from app.security.auth import (
    REFRESH_TOKEN_TYPE,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.security.hashing import hash_password
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import Token, UserCreate


def list_users_by_clinic(db: Session, clinic_id: int) -> list[User]:
    """Retorna todos os utilizadores cadastrados na clínica do administrador autenticado."""
    repository = UserRepository(db)
    # Se o seu UserRepository já tiver um método para filtrar por clínica, utilize-o. 
    # Caso contrário, pode usar uma consulta direta via SQLAlchemy através da sessão:
    return db.query(User).filter(User.clinic_id == clinic_id).all()

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
    repository = UserRepository(db)
    user = repository.get_by_id(user_id) if user_id else None

    if user is None or not user.is_active:
        raise UnauthorizedError("Não foi possível renovar a sessão.")

    return Token(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


def create_user(
    db: Session,
    *,
    clinic_id: int,
    payload: UserCreate,
) -> User:
    """Cria um usuário vinculado à clínica do administrador autenticado."""
    repository = UserRepository(db)

    if repository.get_by_email(str(payload.email)):
        raise ValueError("Já existe um usuário cadastrado com este e-mail.")

    if repository.get_by_cpf(payload.cpf):
        raise ValueError("Já existe um usuário cadastrado com este CPF.")

    user = User(
        clinic_id=clinic_id,
        full_name=payload.full_name.strip(),
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        cpf=payload.cpf,
        phone=payload.phone,
        role=payload.role,
        is_active=True,
    )

    try:
        return repository.create(user)
    except IntegrityError as error:
        db.rollback()
        raise ValueError(
            "Não foi possível cadastrar o usuário. E-mail ou CPF já existe."
        ) from error