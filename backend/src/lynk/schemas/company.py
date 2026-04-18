from pydantic import BaseModel


class CompanyRead(BaseModel):
    id: int
    name: str
    domain: str | None

    model_config = {"from_attributes": True}
