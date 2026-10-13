"""create patients, dentists and appointments"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7a1d9e3b4c5d"
down_revision: Union[str, Sequence[str], None] = "50d77a928a7c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("cpf", sa.String(11), nullable=False),
        sa.Column("medical_record_number", sa.String(30), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("address", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("clinic_id", "cpf", name="uq_patients_clinic_cpf"),
        sa.UniqueConstraint("clinic_id", "medical_record_number", name="uq_patients_clinic_record"),
    )
    op.create_index("ix_patients_clinic_id", "patients", ["clinic_id"])

    op.create_table(
        "dentists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("cro_number", sa.String(30), nullable=False),
        sa.Column("cro_state", sa.String(2), nullable=False),
        sa.Column("specialty", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("user_id", name="uq_dentists_user"),
        sa.UniqueConstraint("cro_number", "cro_state", name="uq_dentists_cro"),
    )
    op.create_index("ix_dentists_user_id", "dentists", ["user_id"])

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("dentist_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="SCHEDULED", nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("duration_minutes", sa.Integer(), server_default="30", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dentist_id"], ["dentists.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "status IN ('SCHEDULED', 'CONFIRMED', 'COMPLETED', 'CANCELED', 'NO_SHOW')",
            name="ck_appointments_status",
        ),
        sa.CheckConstraint("duration_minutes > 0", name="ck_appointments_duration"),
    )
    op.create_index("ix_appointments_clinic_id", "appointments", ["clinic_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_dentist_id", "appointments", ["dentist_id"])
    op.create_index("ix_appointments_scheduled_at", "appointments", ["scheduled_at"])


def downgrade() -> None:
    op.drop_table("appointments")
    op.drop_index("ix_dentists_user_id", table_name="dentists")
    op.drop_table("dentists")
    op.drop_index("ix_patients_clinic_id", table_name="patients")
    op.drop_table("patients")
