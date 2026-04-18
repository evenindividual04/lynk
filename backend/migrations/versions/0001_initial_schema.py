"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(), nullable=False),
        sa.Column("domain", sqlmodel.AutoString(), nullable=True),
        sa.Column("email_pattern", sqlmodel.AutoString(), nullable=True),
        sa.Column("pattern_confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pattern_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_company_name", "company", ["name"])

    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(), nullable=False),
        sa.Column("color", sqlmodel.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tag_name", "tag", ["name"])

    op.create_table(
        "person",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("linkedin_url", sqlmodel.AutoString(), nullable=False),
        sa.Column("full_name", sqlmodel.AutoString(), nullable=False),
        sa.Column("first_name", sqlmodel.AutoString(), nullable=False),
        sa.Column("last_name", sqlmodel.AutoString(), nullable=False),
        sa.Column("headline", sqlmodel.AutoString(), nullable=True),
        sa.Column("location", sqlmodel.AutoString(), nullable=True),
        sa.Column("connected_date", sa.Date(), nullable=True),
        sa.Column("current_company_id", sa.Integer(), nullable=True),
        sa.Column("current_position_title", sqlmodel.AutoString(), nullable=True),
        sa.Column("email", sqlmodel.AutoString(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stage", sqlmodel.AutoString(), nullable=False, server_default="not_contacted"),
        sa.Column("source", sqlmodel.AutoString(), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["current_company_id"], ["company.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("linkedin_url"),
    )
    op.create_index("ix_person_linkedin_url", "person", ["linkedin_url"])
    op.create_index("ix_person_current_company_id", "person", ["current_company_id"])
    op.create_index("ix_person_connected_date", "person", ["connected_date"])
    op.create_index("ix_person_stage", "person", ["stage"])

    op.create_table(
        "position",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("title", sqlmodel.AutoString(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["company_id"], ["company.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_position_person_id", "position", ["person_id"])

    op.create_table(
        "person_tag",
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"]),
        sa.PrimaryKeyConstraint("person_id", "tag_id"),
    )

    op.create_table(
        "note",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("body", sqlmodel.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_note_person_id", "note", ["person_id"])


def downgrade() -> None:
    op.drop_table("note")
    op.drop_table("person_tag")
    op.drop_table("position")
    op.drop_table("person")
    op.drop_table("tag")
    op.drop_table("company")
