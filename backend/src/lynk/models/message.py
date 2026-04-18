from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel

from .template import Channel


class MessageStatus(StrEnum):
    draft = "draft"
    queued = "queued"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


def _new_tracking_id() -> str:
    return str(uuid.uuid4())


class Message(SQLModel, table=True):
    __tablename__ = "message"

    id: int | None = Field(default=None, primary_key=True)
    person_id: int = Field(foreign_key="person.id", index=True)
    template_version_id: int | None = Field(default=None, foreign_key="template_version.id")
    channel: Channel
    status: MessageStatus = Field(default=MessageStatus.draft, index=True)
    subject: str | None = None  # email only
    body: str
    tracking_id: str = Field(default_factory=_new_tracking_id, unique=True, index=True)
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    error: str | None = None
    thread_id: str | None = None  # Gmail thread ID for follow-up threading
    parent_message_id: int | None = Field(default=None, foreign_key="message.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PixelHit(SQLModel, table=True):
    __tablename__ = "pixel_hit"

    id: int | None = Field(default=None, primary_key=True)
    message_id: int = Field(foreign_key="message.id", index=True)
    user_agent: str | None = None
    ip_hash: str | None = None
    opened_at: datetime = Field(default_factory=datetime.utcnow)


class ClickHit(SQLModel, table=True):
    __tablename__ = "click_hit"

    id: int | None = Field(default=None, primary_key=True)
    message_id: int = Field(foreign_key="message.id", index=True)
    link_id: int  # ordinal position of link in body (0-indexed)
    target_url: str
    user_agent: str | None = None
    ip_hash: str | None = None
    clicked_at: datetime = Field(default_factory=datetime.utcnow)
