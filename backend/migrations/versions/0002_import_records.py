"""add import_record table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sqlmodel.AutoString(), nullable=False),
        sa.Column("imported", sa.Integer(), nullable=False),
        sa.Column("merged", sa.Integer(), nullable=False),
        sa.Column("skipped", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("import_record")
