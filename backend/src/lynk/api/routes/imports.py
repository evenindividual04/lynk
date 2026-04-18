from datetime import datetime

from fastapi import APIRouter, UploadFile
from sqlmodel import Field, SQLModel, select

from ...schemas.imports import ImportResponse
from ...services.csv_import import import_csv
from ..deps import SessionDep

router = APIRouter(prefix="/imports", tags=["imports"])


class ImportRecord(SQLModel, table=True):
    __tablename__ = "import_record"

    id: int | None = Field(default=None, primary_key=True)
    filename: str
    imported: int
    merged: int
    skipped: int
    error_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImportRecordRead(SQLModel):
    id: int
    filename: str
    imported: int
    merged: int
    skipped: int
    error_count: int
    created_at: datetime


@router.post("", response_model=ImportResponse)
async def upload_csv(file: UploadFile, session: SessionDep) -> ImportResponse:
    content = await file.read()
    result = import_csv(content, session)

    record = ImportRecord(
        filename=file.filename or "unknown.csv",
        imported=result.imported,
        merged=result.merged,
        skipped=result.skipped,
        error_count=len(result.errors),
    )
    session.add(record)
    session.commit()

    return ImportResponse(
        imported=result.imported,
        merged=result.merged,
        skipped=result.skipped,
        errors=result.errors[:10],
    )


@router.get("", response_model=list[ImportRecordRead])
def list_imports(session: SessionDep) -> list[ImportRecord]:
    return list(
        session.exec(select(ImportRecord).order_by(ImportRecord.created_at.desc()).limit(50)).all()  # type: ignore[attr-defined]
    )
