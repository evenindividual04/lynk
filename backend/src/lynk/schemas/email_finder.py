from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from ..models.email_candidate import EmailSource


class EmailCandidateRead(BaseModel):
    id: int
    person_id: int
    email: str
    source: EmailSource
    confidence: int
    verified: bool
    bounced: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FindEmailRequest(BaseModel):
    person_id: int
    strategies: list[str] | None = None
