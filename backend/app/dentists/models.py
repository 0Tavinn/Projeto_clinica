"""Modelo dos dados profissionais do dentista."""
import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Dentist(Base):
    __tablename__ = "dentists"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_dentists_user"),
        UniqueConstraint("cro_number", "cro_state", name="uq_dentists_cro"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
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
