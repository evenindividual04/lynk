from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class InboundKind(StrEnum):
    reply = "reply"
    bounce_hard = "bounce_hard"
    bounce_soft = "bounce_soft"
    opt_out = "opt_out"
    auto_reply = "auto_reply"


class InboundEvent(SQLModel, table=True):
    __tablename__ = "inbound_event"

    id: int | None = Field(default=None, primary_key=True)
    message_id: int | None = Field(default=None, foreign_key="message.id", index=True)
    person_id: int | None = Field(default=None, foreign_key="person.id", index=True)
    kind: InboundKind
    gmail_msg_id: str = Field(unique=True, index=True)
    subject: str | None = None
    snippet: str | None = None
    from_address: str | None = None
    received_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PollCursor(SQLModel, table=True):
    __tablename__ = "poll_cursor"

    id: int | None = Field(default=None, primary_key=True)
    last_uid_seen: int = Field(default=0)
    last_polled_at: datetime = Field(default_factory=datetime.utcnow)
