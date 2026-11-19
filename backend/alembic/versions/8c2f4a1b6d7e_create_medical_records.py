"""create medical records and clinical evolutions"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c2f4a1b6d7e"
down_revision: Union[str, Sequence[str], None] = "7a1d9e3b4c5d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "medical_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("general_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("patient_id", name="uq_medical_records_patient"),
    )
    op.create_table(
        "clinical_evolutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("medical_record_id", sa.Integer(), nullable=False),
        sa.Column("dentist_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT", nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("procedure_performed", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("finalized_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["medical_record_id"], ["medical_records.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dentist_id"], ["dentists.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("appointment_id", name="uq_clinical_evolutions_appointment"),
        sa.CheckConstraint("status IN ('DRAFT', 'FINALIZED')", name="ck_clinical_evolutions_status"),
    )


def downgrade() -> None:
    op.drop_table("clinical_evolutions")
    op.drop_table("medical_records")
