from __future__ import annotations

from datetime import datetime

from sqlmodel import SQLModel

from ..models.follow_up import FollowUpKind, FollowUpStatus


class FollowUpTaskRead(SQLModel):
    id: int
    person_id: int
    parent_message_id: int
    kind: FollowUpKind
    scheduled_for: datetime
    status: FollowUpStatus
    generated_message_id: int | None
    created_at: datetime
