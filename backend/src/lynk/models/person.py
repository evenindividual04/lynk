from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class Stage(str, Enum):
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


class Source(str, Enum):
    csv_import = "csv_import"
    manual = "manual"
    discovery = "discovery"


class Person(SQLModel, table=True):
    __tablename__ = "person"

    id: Optional[int] = Field(default=None, primary_key=True)
    linkedin_url: str = Field(unique=True, index=True)
    full_name: str
    first_name: str
    last_name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    connected_date: Optional[date] = None
    current_company_id: Optional[int] = Field(default=None, foreign_key="company.id", index=True)
    current_position_title: Optional[str] = None
    email: Optional[str] = None
    priority: int = Field(default=0)
    stage: Stage = Field(default=Stage.not_contacted)
    source: Source = Field(default=Source.manual)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Position(SQLModel, table=True):
    __tablename__ = "position"

    id: Optional[int] = Field(default=None, primary_key=True)
    person_id: int = Field(foreign_key="person.id", index=True)
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = Field(default=True)
