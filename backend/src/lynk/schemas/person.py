from datetime import date, datetime

from pydantic import BaseModel

from ..models.person import Source, Stage
from .note import NoteRead
from .tag import TagRead


class PersonCreate(BaseModel):
    linkedin_url: str
    full_name: str
    first_name: str
    last_name: str
    headline: str | None = None
    location: str | None = None
    email: str | None = None
    current_position_title: str | None = None
    priority: int = 0


class PersonUpdate(BaseModel):
    full_name: str | None = None
    headline: str | None = None
    location: str | None = None
    email: str | None = None
    current_position_title: str | None = None
    stage: Stage | None = None
    priority: int | None = None


class PersonRead(BaseModel):
    id: int
    linkedin_url: str
    full_name: str
    first_name: str
    last_name: str
    headline: str | None
    location: str | None
    connected_date: date | None
    current_company_id: int | None
    current_position_title: str | None
    email: str | None
    priority: int
    stage: Stage
    source: Source
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonDetail(PersonRead):
    tags: list[TagRead] = []
    notes: list[NoteRead] = []


class PeopleListResponse(BaseModel):
    items: list[PersonRead]
    total: int
    page: int
    page_size: int
