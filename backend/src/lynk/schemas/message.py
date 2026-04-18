from __future__ import annotations

from datetime import datetime

from sqlmodel import SQLModel

from ..models.message import MessageStatus
from ..models.template import Channel


class MessageRead(SQLModel):
    id: int
    person_id: int
    template_version_id: int | None
    channel: Channel
    status: MessageStatus
    subject: str | None
    body: str
    tracking_id: str
    scheduled_for: datetime | None
    sent_at: datetime | None
    error: str | None
    thread_id: str | None
    parent_message_id: int | None
    created_at: datetime
    updated_at: datetime


class DraftRequest(SQLModel):
    person_id: int
    channel: Channel
    scenario: str
    template_id: int | None = None
    custom_instructions: str | None = None


class MessageUpdate(SQLModel):
    subject: str | None = None
    body: str | None = None


class SendResponse(SQLModel):
    message: MessageRead
    sending_enabled: bool
    warning: str | None = None
