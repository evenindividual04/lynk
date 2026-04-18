from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response
from sqlmodel import select

from ...models.message import ClickHit, Message, MessageStatus, PixelHit
from ...models.person import Person, Stage
from ...services.tracking import PIXEL_PNG, hash_ip
from ..deps import SessionDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/t", tags=["tracking"])


@router.get("/pixel/{tracking_id}.png")
def pixel(tracking_id: str, request: Request, session: SessionDep) -> Response:
    """1x1 transparent PNG tracking pixel. Logs the open event."""
    message = session.exec(select(Message).where(Message.tracking_id == tracking_id)).first()
    if message:
        ip = request.client.host if request.client else None
        hit = PixelHit(
            message_id=message.id,  # type: ignore[arg-type]
            user_agent=request.headers.get("user-agent"),
            ip_hash=hash_ip(ip),
        )
        session.add(hit)

        # Advance person stage to 'opened' on first pixel hit
        if message.status == MessageStatus.sent:
            person = session.get(Person, message.person_id)
            if person and person.stage == Stage.contacted_email:
                person.stage = Stage.opened
                session.add(person)

        session.commit()
    else:
        logger.warning("Pixel hit for unknown tracking_id: %s", tracking_id)

    return Response(content=PIXEL_PNG, media_type="image/png")


@router.get("/click/{tracking_id}/{link_id}")
def click(tracking_id: str, link_id: int, url: str, request: Request, session: SessionDep) -> RedirectResponse:
    """Log a link click and redirect to the target URL."""
    message = session.exec(select(Message).where(Message.tracking_id == tracking_id)).first()
    if message:
        ip = request.client.host if request.client else None
        hit = ClickHit(
            message_id=message.id,  # type: ignore[arg-type]
            link_id=link_id,
            target_url=url,
            user_agent=request.headers.get("user-agent"),
            ip_hash=hash_ip(ip),
        )
        session.add(hit)
        session.commit()
    else:
        logger.warning("Click hit for unknown tracking_id: %s", tracking_id)

    return RedirectResponse(url=url, status_code=302)
