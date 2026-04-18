from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from ..models.person import Source, Stage
from .note import NoteRead
from .tag import TagRead


class PersonCreate(BaseModel):
    linkedin_url: str
    full_name: str
    first_name: str
    last_name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    current_position_title: Optional[str] = None
    priority: int = 0


class PersonUpdate(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    current_position_title: Optional[str] = None
    stage: Optional[Stage] = None
    priority: Optional[int] = None


class PersonRead(BaseModel):
    id: int
    linkedin_url: str
    full_name: str
    first_name: str
    last_name: str
    headline: Optional[str]
    location: Optional[str]
    connected_date: Optional[date]
    current_company_id: Optional[int]
    current_position_title: Optional[str]
    email: Optional[str]
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
