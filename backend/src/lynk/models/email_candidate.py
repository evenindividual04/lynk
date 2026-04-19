from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class EmailSource(StrEnum):
    csv = "csv"
    pattern_db = "pattern_db"
    permutation = "permutation"
    hunter = "hunter"
    apollo = "apollo"
    skrapp = "skrapp"
    linkedin_contact = "linkedin_contact"
    manual = "manual"


class EmailCandidate(SQLModel, table=True):
    __tablename__ = "email_candidate"

    id: int | None = Field(default=None, primary_key=True)
    person_id: int = Field(foreign_key="person.id", index=True)
    email: str
    source: EmailSource
    confidence: int = Field(default=0)
    verified: bool = Field(default=False)
    bounced: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
