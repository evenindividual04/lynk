from fastapi import APIRouter, HTTPException

from ...schemas.note import NoteCreate, NoteRead
from ...services import people as svc
from ..deps import SessionDep

router = APIRouter(prefix="/people", tags=["notes"])


@router.post("/{person_id}/notes", response_model=NoteRead, status_code=201)
def add_note(person_id: int, body: NoteCreate, session: SessionDep) -> NoteRead:
    person = svc.get_person(session, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    note = svc.add_note(session, person_id, body.body)
    return NoteRead.model_validate(note)
