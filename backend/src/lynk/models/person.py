from datetime import date, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class Stage(StrEnum):
    not_contacted = "not_contacted"
    contacted_li = "contacted_li"
    contacted_email = "contacted_email"
    contacted_both = "contacted_both"
    opened = "opened"
    replied = "replied"
    call_scheduled = "call_scheduled"
    offer = "offer"
    rejected = "rejected"
    bounced = "bounced"
    cold = "cold"
    opted_out = "opted_out"


class Source(StrEnum):
    csv_import = "csv_import"
    manual = "manual"
    discovery = "discovery"


class Person(SQLModel, table=True):
    __tablename__ = "person"

    id: int | None = Field(default=None, primary_key=True)
    linkedin_url: str = Field(unique=True, index=True)
    full_name: str
    first_name: str
    last_name: str
    headline: str | None = None
    location: str | None = None
    connected_date: date | None = None
    current_company_id: int | None = Field(default=None, foreign_key="company.id", index=True)
    current_position_title: str | None = None
    email: str | None = None
    priority: int = Field(default=0)
    stage: Stage = Field(default=Stage.not_contacted)
    source: Source = Field(default=Source.manual)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Position(SQLModel, table=True):
    __tablename__ = "position"

    id: int | None = Field(default=None, primary_key=True)
    person_id: int = Field(foreign_key="person.id", index=True)
    company_id: int | None = Field(default=None, foreign_key="company.id")
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = Field(default=True)
