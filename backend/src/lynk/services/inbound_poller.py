from __future__ import annotations

import email
import imaplib
import logging
from datetime import datetime

from sqlmodel import Session, select

from ..config import settings
from ..db import engine
from ..models.inbound_event import InboundEvent, PollCursor
from .inbound_classifier import classify
from .inbound_handler import apply_event

logger = logging.getLogger(__name__)


def poll_inbox() -> None:
    """
    IMAP poll job: fetch UNSEEN messages since last UID, classify, persist, apply.
    Runs every 10 minutes via APScheduler.
    """
    if not settings.gmail_user or not settings.gmail_app_password:
        logger.debug("IMAP credentials not set — skipping poll")
        return

    with Session(engine) as session:
        cursor = _get_or_create_cursor(session)
        new_uid = cursor.last_uid_seen

        try:
            with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as imap:
                imap.login(settings.gmail_user, settings.gmail_app_password)
                imap.select("INBOX")

                # Fetch by UID > last_uid_seen
                search_cmd = f"UID {cursor.last_uid_seen + 1}:*" if cursor.last_uid_seen else "ALL"
                status, data = imap.uid("search", None, search_cmd)  # type: ignore[arg-type]
                if status != "OK" or not data[0]:
                    return

                uid_list = data[0].split()
                logger.info("Inbound poll: %d new messages", len(uid_list))

                for uid_bytes in uid_list:
                    uid = int(uid_bytes)
                    _, msg_data = imap.uid("fetch", uid_bytes, "(RFC822)")
                    if not msg_data or not msg_data[0]:
                        continue
                    raw = msg_data[0][1]  # type: ignore[index]
                    parsed = email.message_from_bytes(raw)  # type: ignore[arg-type]
                    _process_message(session, parsed, uid)
                    new_uid = max(new_uid, uid)

        except Exception as exc:
            logger.error("IMAP poll error: %s", exc)
            return

        cursor.last_uid_seen = new_uid
        cursor.last_polled_at = datetime.utcnow()
        session.add(cursor)
        session.commit()


def _get_or_create_cursor(session: Session) -> PollCursor:
    cursor = session.exec(select(PollCursor)).first()
    if not cursor:
        cursor = PollCursor()
        session.add(cursor)
        session.flush()
    return cursor


def _process_message(session: Session, parsed: email.message.Message, uid: int) -> None:
    gmail_msg_id = parsed.get("Message-Id", f"uid-{uid}").strip()

    # Deduplicate
    existing = session.exec(select(InboundEvent).where(InboundEvent.gmail_msg_id == gmail_msg_id)).first()
    if existing:
        return

    try:
        kind, person_id, message_id = classify(parsed, session)
    except Exception as exc:
        logger.error("Classification error for UID %d: %s", uid, exc)
        return

    subject = parsed.get("Subject", "")
    from_addr = parsed.get("From", "")

    from .inbound_classifier import _get_body

    body = _get_body(parsed)
    snippet = body[:500] if body else ""

    date_str = parsed.get("Date", "")
    try:
        from email.utils import parsedate_to_datetime

        received_at = parsedate_to_datetime(date_str) if date_str else datetime.utcnow()
        received_at = received_at.replace(tzinfo=None)
    except Exception:
        received_at = datetime.utcnow()

    event = InboundEvent(
        message_id=message_id,
        person_id=person_id,
        kind=kind,
        gmail_msg_id=gmail_msg_id,
        subject=subject[:500] if subject else None,
        snippet=snippet or None,
        from_address=from_addr[:500] if from_addr else None,
        received_at=received_at,
    )
    session.add(event)
    session.flush()

    try:
        apply_event(session, event)
    except Exception as exc:
        logger.error("Error applying event for UID %d: %s", uid, exc)
