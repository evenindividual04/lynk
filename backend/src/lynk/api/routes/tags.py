from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ...models.tag import Tag
from ...schemas.tag import TagCreate, TagRead
from ...services import people as svc
from ..deps import SessionDep

router = APIRouter(tags=["tags"])

tags_router = APIRouter(prefix="/tags")
people_tags_router = APIRouter(prefix="/people")


@tags_router.get("", response_model=list[TagRead])
def list_tags(session: SessionDep) -> list[Tag]:
    return list(session.exec(select(Tag)).all())


@tags_router.post("", response_model=TagRead, status_code=201)
def create_tag(body: TagCreate, session: SessionDep) -> Tag:
    tag = Tag(name=body.name, color=body.color)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@people_tags_router.post("/{person_id}/tags", response_model=TagRead, status_code=201)
def add_tag(person_id: int, body: TagCreate, session: SessionDep) -> Tag:
    person = svc.get_person(session, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return svc.add_tag_to_person(session, person_id, body.name)


@people_tags_router.delete("/{person_id}/tags/{tag_id}", status_code=204)
def remove_tag(person_id: int, tag_id: int, session: SessionDep) -> None:
    removed = svc.remove_tag_from_person(session, person_id, tag_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Tag association not found")
