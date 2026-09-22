"""Contratos de entrada e saída do módulo de usuários e autenticação."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.security.roles import Role


class UserRead(BaseModel):
    """Representação pública de um usuário, sem expor a senha."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    clinic_id: int
    full_name: str
    email: EmailStr
    cpf: str
    phone: str | None
    role: Role
    is_active: bool


class UserCreate(BaseModel):
    """Dados recebidos para cadastrar um usuário da clínica."""

    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    cpf: str = Field(
        min_length=11,
        max_length=11,
        pattern=r"^\d{11}$",
        description="CPF com 11 dígitos, sem pontuação.",
    )
    phone: str | None = Field(default=None, max_length=20)
    role: Role


class RefreshRequest(BaseModel):
    refresh_token: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Dados relevantes presentes no token JWT."""

    sub: str
    role: Role
    clinic_id: int
    type: str
    exp: int