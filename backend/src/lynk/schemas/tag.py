from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    color: str | None = None


class TagRead(BaseModel):
    id: int
    name: str
    color: str | None

    model_config = {"from_attributes": True}
