from datetime import datetime

from pydantic import BaseModel


class NoteCreate(BaseModel):
    body: str


class NoteRead(BaseModel):
    id: int
    person_id: int
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}
