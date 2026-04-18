from typing import Optional

from fastapi import APIRouter
from sqlmodel import select

from ...models.company import Company
from ...schemas.company import CompanyRead
from ..deps import SessionDep

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
def list_companies(session: SessionDep, q: Optional[str] = None) -> list[Company]:
    stmt = select(Company)
    if q:
        stmt = stmt.where(Company.name.ilike(f"%{q}%"))  # type: ignore[union-attr]
    stmt = stmt.order_by(Company.name).limit(50)  # type: ignore[arg-type]
    return list(session.exec(stmt).all())
