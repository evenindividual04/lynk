from datetime import date

from fastapi import APIRouter, HTTPException, Query

from ...models.person import Person
from ...schemas.person import (
    PeopleListResponse,
    PersonCreate,
    PersonDetail,
    PersonRead,
    PersonUpdate,
)
from ...services import people as svc
from ...services.dedup import normalize_linkedin_url
from ..deps import PaginationDep, SessionDep

router = APIRouter(prefix="/people", tags=["people"])


@router.get("", response_model=PeopleListResponse)
def list_people(
    session: SessionDep,
    pagination: PaginationDep,
    q: str | None = None,
    company: str | None = None,
    stage: str | None = None,
    tag: str | None = None,
    connected_from: date | None = None,
    connected_to: date | None = None,
    sort: str = Query("created_at", pattern="^(created_at|connected_date|full_name|priority)$"),
) -> PeopleListResponse:
    items, total = svc.get_people(
        session,
        q=q,
        company=company,
        stage=stage,
        tag=tag,
        connected_from=connected_from,
        connected_to=connected_to,
        sort=sort,
        **pagination,
    )
    return PeopleListResponse(items=items, total=total, **pagination)


@router.post("", response_model=PersonRead, status_code=201)
def create_person(body: PersonCreate, session: SessionDep) -> Person:
    try:
        normalized_url = normalize_linkedin_url(body.linkedin_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    data = body.model_dump()
    data["linkedin_url"] = normalized_url
    return svc.create_person(session, data)


@router.get("/{person_id}", response_model=PersonDetail)
def get_person(person_id: int, session: SessionDep) -> PersonDetail:
    person = svc.get_person(session, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    tags = svc.get_tags_for_person(session, person_id)
    notes = svc.get_notes(session, person_id)
    return PersonDetail.model_validate({**person.model_dump(), "tags": tags, "notes": notes})


@router.patch("/{person_id}", response_model=PersonRead)
def update_person(person_id: int, body: PersonUpdate, session: SessionDep) -> Person:
    person = svc.get_person(session, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return svc.update_person(session, person, body.model_dump(exclude_none=True))
