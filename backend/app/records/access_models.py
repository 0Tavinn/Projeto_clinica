"""Evidência persistente de confirmação e realização por consulta."""

import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    FetchedValue,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ClinicalAccessGrant(Base):
    """Preserva a origem da preparação e da continuidade do cuidado.

    A linha, isoladamente, não autoriza acesso. O serviço deverá conferir
    procedência, situação atual da consulta, leitor e participantes.
    """

    __tablename__ = "clinical_access_grants"
    __table_args__ = (
        PrimaryKeyConstraint(
            "appointment_id",
            name="pk_clinical_access_grants",
        ),
        ForeignKeyConstraint(
            ["appointment_id", "clinic_id", "patient_id", "dentist_id"],
            [
                "appointments.id",
                "appointments.clinic_id",
                "appointments.patient_id",
                "appointments.dentist_id",
            ],
            name="fk_clinical_access_grants_origin",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "(care_occurred_at IS NULL AND care_recorded_at IS NULL "
            "AND care_recorded_by_user_id IS NULL) OR "
            "(confirmed_by_user_id IS NOT NULL "
            "AND care_occurred_at IS NOT NULL "
            "AND care_recorded_at IS NOT NULL "
            "AND care_recorded_by_user_id IS NOT NULL)",
            name="ck_clinical_access_grants_care_complete",
        ),
        Index(
            "idx_clinical_access_grants_lookup",
            "clinic_id",
            "dentist_id",
            "patient_id",
        ),
    )

    appointment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clinic_id: Mapped[int] = mapped_column(Integer, nullable=False)
    patient_id: Mapped[int] = mapped_column(Integer, nullable=False)
    dentist_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # O SQL preparado fornece clock_timestamp(); o ORM reconhece o valor
    # gerado pelo banco sem tentar recriar esse esquema.
    granted_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=FetchedValue(),
    )
    confirmed_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_clinical_access_grants_confirmed_by",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    care_occurred_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    care_recorded_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    care_recorded_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_clinical_access_grants_care_recorded_by",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )