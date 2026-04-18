from typing import Annotated

from fastapi import Depends, Query
from sqlmodel import Session

from ..db import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict[str, int]:
    return {"page": page, "page_size": page_size}


PaginationDep = Annotated[dict[str, int], Depends(pagination)]
