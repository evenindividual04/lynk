"""phase3: email_candidate, inbound_event, poll_cursor; person email_valid/opted_out_at

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # email_candidate table
    op.create_table(
        "email_candidate",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("person_id", sa.Integer, sa.ForeignKey("person.id"), nullable=False),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("confidence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("verified", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("bounced", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_email_candidate_person_id", "email_candidate", ["person_id"])
    op.create_unique_constraint("uq_email_candidate_person_email", "email_candidate", ["person_id", "email"])

    # inbound_event table
    op.create_table(
        "inbound_event",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("message_id", sa.Integer, sa.ForeignKey("message.id"), nullable=True),
        sa.Column("person_id", sa.Integer, sa.ForeignKey("person.id"), nullable=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("gmail_msg_id", sa.String, nullable=False, unique=True),
        sa.Column("subject", sa.String, nullable=True),
        sa.Column("snippet", sa.String, nullable=True),
        sa.Column("from_address", sa.String, nullable=True),
        sa.Column("received_at", sa.DateTime, nullable=False),
        sa.Column("processed", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_inbound_event_gmail_msg_id", "inbound_event", ["gmail_msg_id"], unique=True)
    op.create_index("ix_inbound_event_person_id", "inbound_event", ["person_id"])
    op.create_index("ix_inbound_event_message_id", "inbound_event", ["message_id"])
    op.create_index("ix_inbound_event_person_kind", "inbound_event", ["person_id", "kind"])

    # poll_cursor table (singleton)
    op.create_table(
        "poll_cursor",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("last_uid_seen", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_polled_at", sa.DateTime, nullable=False),
    )

    # Add email_valid and opted_out_at to person
    op.add_column("person", sa.Column("email_valid", sa.Boolean, nullable=True))
    op.add_column("person", sa.Column("opted_out_at", sa.DateTime, nullable=True))


def downgrade() -> None:
    op.drop_column("person", "opted_out_at")
    op.drop_column("person", "email_valid")
    op.drop_table("poll_cursor")
    op.drop_table("inbound_event")
    op.drop_table("email_candidate")
