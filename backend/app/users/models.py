"""Models ORM de clínica e usuário, alinhados ao schema PostgreSQL oficial."""
import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.security.roles import Role


class Clinic(Base):
    """Mapeia a tabela `clinics` do PostgreSQL."""

    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    users: Mapped[list["User"]] = relationship(back_populates="clinic")


class User(Base):
    """Mapeia a tabela `users` do PostgreSQL."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[Role] = mapped_column(
        SAEnum(
            Role,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [
                member.value for member in enum_cls
            ],
        ),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relacionamentos
    clinic: Mapped["Clinic"] = relationship(back_populates="users")
    
    # 1-para-1 com Dentist. Permite Null pois o usuário pode ser Recepcionista ou Admin
    dentist: Mapped["Dentist" | None] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return (
            f"<User id={self.id} email={self.email} "
            f"role={self.role.value}>"
        )


class Dentist(Base):
    """Mapeia a tabela `dentists` do PostgreSQL."""

    __tablename__ = "dentists"
    __table_args__ = (
        # Impede a repetição de um CRO dentro do mesmo estado
        UniqueConstraint("cro_number", "cro_state", name="uq_dentists_cro"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        unique=True, # Garante que um usuário possua no máximo um perfil de dentista
    )
    cro_number: Mapped[str] = mapped_column(String(30), nullable=False)
    cro_state: Mapped[str] = mapped_column(String(2), nullable=False)
    specialty: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relacionamento inverso para User
    user: Mapped["User"] = relationship(back_populates="dentist")

    def __repr__(self) -> str:
        return f"<Dentist id={self.id} cro={self.cro_number}/{self.cro_state}>"