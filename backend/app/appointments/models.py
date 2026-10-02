"""Modelo ORM dos agendamentos."""
import datetime
import enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    NO_SHOW = "NO_SHOW"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clinic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinics.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    dentist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dentists.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    scheduled_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(
            AppointmentStatus,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=AppointmentStatus.SCHEDULED,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
