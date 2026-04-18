"""outreach schema: templates, messages, tracking, follow-ups

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "template",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("scenario", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("active_version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "template_version",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("subject_template", sa.String(), nullable=True),
        sa.Column("body_template", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["template.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "version"),
    )
    op.create_index("ix_template_version_template_id", "template_version", ["template_id"])

    # Add FK from template.active_version_id → template_version.id (deferred — SQLite allows)
    # SQLite doesn't support ALTER TABLE ADD FOREIGN KEY, so we leave it as nullable int

    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("template_version_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("tracking_id", sa.String(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("thread_id", sa.String(), nullable=True),
        sa.Column("parent_message_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["template_version_id"], ["template_version.id"]),
        sa.ForeignKeyConstraint(["parent_message_id"], ["message.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_person_id", "message", ["person_id"])
    op.create_index("ix_message_status", "message", ["status"])
    op.create_index("ix_message_tracking_id", "message", ["tracking_id"], unique=True)

    op.create_table(
        "pixel_hit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("ip_hash", sa.String(), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["message.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pixel_hit_message_id", "pixel_hit", ["message_id"])

    op.create_table(
        "click_hit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("link_id", sa.Integer(), nullable=False),
        sa.Column("target_url", sa.String(), nullable=False),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("ip_hash", sa.String(), nullable=True),
        sa.Column("clicked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["message.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_click_hit_message_id", "click_hit", ["message_id"])

    op.create_table(
        "follow_up_task",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("parent_message_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("generated_message_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["parent_message_id"], ["message.id"]),
        sa.ForeignKeyConstraint(["generated_message_id"], ["message.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_follow_up_task_person_id", "follow_up_task", ["person_id"])
    op.create_index("ix_follow_up_task_parent_message_id", "follow_up_task", ["parent_message_id"])
    op.create_index("ix_follow_up_task_scheduled_for", "follow_up_task", ["scheduled_for"])
    op.create_index("ix_follow_up_task_status", "follow_up_task", ["status"])


def downgrade() -> None:
    op.drop_table("follow_up_task")
    op.drop_table("click_hit")
    op.drop_table("pixel_hit")
    op.drop_table("message")
    op.drop_table("template_version")
    op.drop_table("template")
