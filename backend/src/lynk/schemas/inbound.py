from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from ..models.inbound_event import InboundKind


class InboundEventRead(BaseModel):
    id: int
    message_id: int | None
    person_id: int | None
    kind: InboundKind
    gmail_msg_id: str
    subject: str | None
    snippet: str | None
    from_address: str | None
    received_at: datetime
    processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
