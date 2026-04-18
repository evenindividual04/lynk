from fastapi import APIRouter, UploadFile

from ...schemas.imports import ImportResponse
from ...services.csv_import import import_csv
from ..deps import SessionDep

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("", response_model=ImportResponse)
async def upload_csv(file: UploadFile, session: SessionDep) -> ImportResponse:
    content = await file.read()
    result = import_csv(content, session)
    return ImportResponse(
        imported=result.imported,
        merged=result.merged,
        skipped=result.skipped,
        errors=result.errors[:10],
    )
