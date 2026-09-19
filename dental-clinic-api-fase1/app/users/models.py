"""
Models ORM de usuário e clínica.

`clinic_id` é incluído em `User` desde já (mesmo com uma única clínica em
uso no MVP) para permitir evolução futura para multiclínica sem migração
estrutural disruptiva.
"""
import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.security.roles import Role


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Clinic(Base):
    """
    Entidade mínima de clínica.

    Modelada agora apenas o suficiente para servir de FK em `User` e demais
    entidades futuras (Patient, Appointment, MedicalRecord). Gestão completa
    de multiclínica fica para fase 2.
    """

    __tablename__ = "clinics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    users: Mapped[list["User"]] = relationship(back_populates="clinic")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    clinic_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clinics.id"), nullable=False, index=True
    )

    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[Role] = mapped_column(
        SAEnum(
            Role,
            name="user_role",
            native_enum=False,
            length=32,
            # Por padrão o SQLAlchemy persistiria `Role.RECEPTIONIST.name`
            # ("RECEPTIONIST"). Forçamos persistir `.value` ("receptionist")
            # para ficar consistente com o valor usado no payload do JWT e
            # em qualquer serialização externa.
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    clinic: Mapped["Clinic"] = relationship(back_populates="users")

    def __repr__(self) -> str:  # pragma: no cover - apenas debug
        return f"<User id={self.id} email={self.email} role={self.role}>"
