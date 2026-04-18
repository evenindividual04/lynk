from datetime import datetime

from sqlmodel import Field, SQLModel


class Note(SQLModel, table=True):
    __tablename__ = "note"

    id: int | None = Field(default=None, primary_key=True)
    person_id: int = Field(foreign_key="person.id", index=True)
    body: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
