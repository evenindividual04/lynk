from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ...models.inbound_event import InboundEvent, InboundKind
from ...schemas.inbound import InboundEventRead
from ...services.inbound_poller import poll_inbox
from ..deps import SessionDep

router = APIRouter(prefix="/inbound", tags=["inbound"])


@router.get("/events", response_model=list[InboundEventRead])
def list_events(
    session: SessionDep,
    kind: InboundKind | None = None,
    person_id: int | None = None,
    processed: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[InboundEvent]:
    stmt = select(InboundEvent).order_by(InboundEvent.received_at.desc())  # type: ignore[attr-defined]
    if kind is not None:
        stmt = stmt.where(InboundEvent.kind == kind)
    if person_id is not None:
        stmt = stmt.where(InboundEvent.person_id == person_id)
    if processed is not None:
        stmt = stmt.where(InboundEvent.processed == processed)
    stmt = stmt.offset(offset).limit(limit)
    return list(session.exec(stmt).all())


@router.post("/events/{event_id}/mark-processed", response_model=InboundEventRead)
def mark_processed(event_id: int, session: SessionDep) -> InboundEvent:
    event = session.get(InboundEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="InboundEvent not found")
    event.processed = True
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.post("/poll-now")
def poll_now() -> dict[str, str]:
    """Manually trigger an IMAP poll (dev/debug aid)."""
    try:
        poll_inbox()
        return {"status": "ok", "polled_at": datetime.utcnow().isoformat()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
