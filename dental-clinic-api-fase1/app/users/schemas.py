"""Contratos de entrada/saída (Pydantic) do módulo de usuários e autenticação."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.security.roles import Role


class UserRead(BaseModel):
    """Representação pública de um usuário (nunca inclui hashed_password)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    clinic_id: str
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool


class UserCreate(BaseModel):
    """
    Usado apenas internamente (ex.: script de seed / futura rota
    administrativa de gestão de usuários). Não exposto como endpoint público
    de auto-registro no MVP — cadastro de usuários do sistema é uma
    operação administrativa, fora do escopo de auto-cadastro de pacientes.
    """

    clinic_id: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: Role


class RefreshRequest(BaseModel):
    refresh_token: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Payload decodificado de um JWT (claims relevantes para a aplicação)."""

    sub: str  # user id
    role: Role
    clinic_id: str
    type: str  # "access" | "refresh"
    exp: int
