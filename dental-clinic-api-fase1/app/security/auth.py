"""
Autenticação: emissão/validação de JWT (access + refresh) e a dependency
`get_current_user` usada por todos os endpoints protegidos.
"""
import datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.common.exceptions import InactiveUserError, UnauthorizedError
from app.core.config import get_settings
from app.core.database import get_db
from app.security.hashing import verify_password
from app.security.roles import Role
from app.users.models import User
from app.users.repository import UserRepository

settings = get_settings()

# tokenUrl aponta para o endpoint de login relativo ao prefixo /api/v1 —
# usado apenas para a UI do Swagger/OpenAPI construir o fluxo "Authorize".
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _create_token(*, subject: str, role: Role, clinic_id: str, token_type: str, expires_delta: datetime.timedelta) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": subject,
        "role": role.value,
        "clinic_id": clinic_id,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user: User) -> str:
    return _create_token(
        subject=user.id,
        role=user.role,
        clinic_id=user.clinic_id,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user: User) -> str:
    return _create_token(
        subject=user.id,
        role=user.role,
        clinic_id=user.clinic_id,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=datetime.timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise UnauthorizedError("Token inválido ou expirado.")
    return payload


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Autentica por email/senha.

    Mensagem de erro é deliberadamente genérica e idêntica tanto para
    "usuário não existe" quanto para "senha incorreta" quanto para "usuário
    inativo" — isso evita enumeração de contas por diferença de resposta.
    O caso de usuário inativo é sinalizado à parte via InactiveUserError
    apenas depois de confirmar a senha, para não vazar "conta existe mas
    está inativa" a quem não sabe a senha.
    """
    repo = UserRepository(db)
    user = repo.get_by_email(email)

    generic_error = UnauthorizedError("Email ou senha inválidos.")

    if user is None:
        # Executa um hash "dummy" para manter tempo de resposta similar ao
        # caso de usuário existente (mitigação simples de timing attack).
        verify_password(password, "$argon2id$v=19$m=65536,t=3,p=4$" + "0" * 22)
        raise generic_error

    if not verify_password(password, user.hashed_password):
        raise generic_error

    if not user.is_active:
        raise InactiveUserError()

    return user


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if token is None:
        raise UnauthorizedError("Token de autenticação não informado.")

    payload = decode_token(token)

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise UnauthorizedError("Tipo de token inválido para esta operação.")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token inválido.")

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Usuário do token não encontrado.")
    if not user.is_active:
        raise InactiveUserError()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
