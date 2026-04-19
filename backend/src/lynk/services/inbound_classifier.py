from __future__ import annotations

import email
import logging
import re

from sqlmodel import Session, select

from ..models.inbound_event import InboundKind
from ..models.message import Message, MessageStatus
from ..models.person import Person
from ..models.template import Channel

logger = logging.getLogger(__name__)

_OPT_OUT_RE = re.compile(
    r"\b(unsubscribe|stop contacting|remove me|not interested|do not email|please remove)\b",
    re.IGNORECASE,
)
_BOUNCE_FROM_RE = re.compile(r"(mailer-daemon|postmaster)@", re.IGNORECASE)
_BOUNCE_SUBJECT_RE = re.compile(
    r"^(Delivery Status Notification|Undeliverable|Mail delivery failed|Failed to deliver)",
    re.IGNORECASE,
)
_DSN_HARD_RE = re.compile(r"\b5\.\d+\.\d+\b")
_AUTO_SUBJECT_RE = re.compile(r"(out of office|automatic reply|auto[- ]reply)", re.IGNORECASE)


def classify(
    raw_msg: email.message.Message,
    session: Session,
) -> tuple[InboundKind, int | None, int | None]:
    """
    Classify an IMAP message.
    Returns (kind, person_id | None, message_id | None).
    """
    from_addr = raw_msg.get("From", "")
    subject = raw_msg.get("Subject", "")
    auto_submitted = raw_msg.get("Auto-Submitted", "")
    in_reply_to = raw_msg.get("In-Reply-To", "")
    references = raw_msg.get("References", "")
    body = _get_body(raw_msg)

    # 1. Bounce detection
    if _BOUNCE_FROM_RE.search(from_addr) or _BOUNCE_SUBJECT_RE.search(subject):
        kind = InboundKind.bounce_hard if _DSN_HARD_RE.search(body) else InboundKind.bounce_soft
        person_id = _find_person_by_original_recipient(raw_msg, session)
        return kind, person_id, None

    # 2. Auto-reply detection
    if auto_submitted == "auto-replied" or _AUTO_SUBJECT_RE.search(subject):
        person_id = _find_person_by_sender(from_addr, session)
        return InboundKind.auto_reply, person_id, None

    # 3. Opt-out detection
    if _OPT_OUT_RE.search(body):
        person_id = _find_person_by_sender(from_addr, session)
        return InboundKind.opt_out, person_id, None

    # 4. Reply — match via In-Reply-To / References
    person_id, message_id = _find_reply_linkage(in_reply_to, references, from_addr, session)
    return InboundKind.reply, person_id, message_id


def _get_body(msg: email.message.Message) -> str:
    body_parts: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    body_parts.append(payload.decode(errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if isinstance(payload, bytes):
            body_parts.append(payload.decode(errors="replace"))
    return "\n".join(body_parts)[:2000]


def _find_person_by_sender(from_addr: str, session: Session) -> int | None:
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", from_addr)
    if not email_match:
        return None
    sender_email = email_match.group().lower()
    person = session.exec(select(Person).where(Person.email == sender_email)).first()
    return person.id if person else None  # type: ignore[return-value]


def _find_person_by_original_recipient(msg: email.message.Message, session: Session) -> int | None:
    # Try To/Delivered-To headers to find who the original message was for
    for header in ("To", "Delivered-To", "X-Original-To"):
        val = msg.get(header, "")
        person_id = _find_person_by_sender(val, session)
        if person_id:
            return person_id
    return None


def _find_reply_linkage(
    in_reply_to: str,
    references: str,
    from_addr: str,
    session: Session,
) -> tuple[int | None, int | None]:
    # Try to match thread_id from headers
    all_refs = f"{in_reply_to} {references}"
    msgs = session.exec(
        select(Message).where(
            Message.status == MessageStatus.sent,
            Message.channel == Channel.cold_email,
        )
    ).all()

    for msg in msgs:
        if msg.thread_id and msg.thread_id in all_refs:
            return msg.person_id, msg.id  # type: ignore[return-value]

    # Fallback: sender email → person → most recent sent email message
    person_id = _find_person_by_sender(from_addr, session)
    if person_id:
        recent = session.exec(
            select(Message)
            .where(
                Message.person_id == person_id,
                Message.status == MessageStatus.sent,
                Message.channel == Channel.cold_email,
            )
            .order_by(Message.sent_at.desc())  # type: ignore[union-attr]
            .limit(1)
        ).first()
        if recent:
            return person_id, recent.id  # type: ignore[return-value]

    return person_id, None
