from datetime import datetime

from sqlmodel import Field, SQLModel


class Company(SQLModel, table=True):
    __tablename__ = "company"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    domain: str | None = None
    # Phase 3 stubs — schema exists, no writes in Phase 1
    email_pattern: str | None = None
    pattern_confidence: int = Field(default=0)
    pattern_samples: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
