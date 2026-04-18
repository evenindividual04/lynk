from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class FollowUpKind(StrEnum):
    nudge_opened = "nudge_opened"
    nudge_unopened = "nudge_unopened"
    final_bump = "final_bump"


class FollowUpStatus(StrEnum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"


class FollowUpTask(SQLModel, table=True):
    __tablename__ = "follow_up_task"

    id: int | None = Field(default=None, primary_key=True)
    person_id: int = Field(foreign_key="person.id", index=True)
    parent_message_id: int = Field(foreign_key="message.id", index=True)
    kind: FollowUpKind
    scheduled_for: datetime = Field(index=True)
    status: FollowUpStatus = Field(default=FollowUpStatus.pending, index=True)
    generated_message_id: int | None = Field(default=None, foreign_key="message.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
