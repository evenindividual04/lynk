from pydantic import BaseModel


class ImportResponse(BaseModel):
    imported: int
    merged: int
    skipped: int
    errors: list[dict[str, str]]
