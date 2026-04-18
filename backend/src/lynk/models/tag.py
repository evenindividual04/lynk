from typing import Optional

from sqlmodel import Field, SQLModel


class Tag(SQLModel, table=True):
    __tablename__ = "tag"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    color: Optional[str] = None


class PersonTag(SQLModel, table=True):
    __tablename__ = "person_tag"

    person_id: int = Field(foreign_key="person.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)
