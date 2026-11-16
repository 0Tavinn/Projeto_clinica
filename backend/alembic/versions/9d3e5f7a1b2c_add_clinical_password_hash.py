"""add separate clinical access password"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d3e5f7a1b2c"
down_revision: Union[str, Sequence[str], None] = "8c2f4a1b6d7e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("clinical_password_hash", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "clinical_password_hash")
