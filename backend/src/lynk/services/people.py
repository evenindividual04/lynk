from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlmodel import Session, func, or_, select

from ..models.company import Company
from ..models.note import Note
from ..models.person import Person, Source
from ..models.tag import PersonTag, Tag


def get_people(
    session: Session,
    *,
    q: str | None = None,
    company: str | None = None,
    stage: str | None = None,
    tag: str | None = None,
    connected_from: date | None = None,
    connected_to: date | None = None,
    sort: str = "created_at",
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Person], int]:
    stmt = select(Person)

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Person.full_name.ilike(pattern),  # type: ignore[attr-defined]
                Person.email.ilike(pattern),  # type: ignore[union-attr,attr-defined]
                Person.headline.ilike(pattern),  # type: ignore[union-attr,attr-defined]
            )
        )

    if company:
        stmt = stmt.join(Company, Person.current_company_id == Company.id).where(  # type: ignore[arg-type]
            Company.name.ilike(f"%{company}%")  # type: ignore[attr-defined]
        )

    if stage:
        stmt = stmt.where(Person.stage == stage)

    if tag:
        stmt = (
            stmt.join(PersonTag, Person.id == PersonTag.person_id)  # type: ignore[arg-type]
            .join(Tag, PersonTag.tag_id == Tag.id)  # type: ignore[arg-type]
            .where(Tag.name == tag)
        )

    if connected_from:
        stmt = stmt.where(Person.connected_date >= connected_from)  # type: ignore[operator]
    if connected_to:
        stmt = stmt.where(Person.connected_date <= connected_to)  # type: ignore[operator]

    sort_col: Any = getattr(Person, sort, Person.created_at)
    stmt = stmt.order_by(sort_col.desc())

    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    people = list(session.exec(stmt).all())

    return people, total


def get_person(session: Session, person_id: int) -> Person | None:
    return session.get(Person, person_id)


def create_person(session: Session, data: dict[str, Any]) -> Person:
    person = Person(**data)
    person.source = Source.manual
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


def update_person(session: Session, person: Person, data: dict[str, Any]) -> Person:
    for key, value in data.items():
        setattr(person, key, value)
    person.updated_at = datetime.utcnow()
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


def add_note(session: Session, person_id: int, body: str) -> Note:
    note = Note(person_id=person_id, body=body)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def get_notes(session: Session, person_id: int) -> list[Note]:
    return list(session.exec(select(Note).where(Note.person_id == person_id)).all())


def get_tags_for_person(session: Session, person_id: int) -> list[Tag]:
    stmt = (
        select(Tag)
        .join(PersonTag, Tag.id == PersonTag.tag_id)  # type: ignore[arg-type]
        .where(PersonTag.person_id == person_id)
    )
    return list(session.exec(stmt).all())


def add_tag_to_person(session: Session, person_id: int, tag_name: str) -> Tag:
    tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
    if not tag:
        tag = Tag(name=tag_name)
        session.add(tag)
        session.flush()

    existing = session.get(PersonTag, (person_id, tag.id))
    if not existing:
        person_tag = PersonTag(person_id=person_id, tag_id=tag.id)
        session.add(person_tag)
    session.commit()
    return tag


def remove_tag_from_person(session: Session, person_id: int, tag_id: int) -> bool:
    pt = session.get(PersonTag, (person_id, tag_id))
    if pt:
        session.delete(pt)
        session.commit()
        return True
    return False
