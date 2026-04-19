from __future__ import annotations

import logging
from datetime import datetime

from sqlmodel import Session, select

from ..models.follow_up import FollowUpStatus, FollowUpTask
from ..models.inbound_event import InboundEvent, InboundKind
from ..models.message import Message
from ..models.person import Person, Stage
from ..models.template import Channel

logger = logging.getLogger(__name__)


def apply_event(session: Session, event: InboundEvent) -> None:
    """Apply the side-effects of an inbound event to person stage and follow-ups."""
    if event.kind == InboundKind.reply:
        _handle_reply(session, event)
    elif event.kind == InboundKind.bounce_hard:
        _handle_bounce_hard(session, event)
    elif event.kind == InboundKind.bounce_soft:
        logger.info("Soft bounce for event %s — no state change", event.id)
    elif event.kind == InboundKind.opt_out:
        _handle_opt_out(session, event)
    elif event.kind == InboundKind.auto_reply:
        logger.info("Auto-reply for event %s — logged only", event.id)


def _handle_reply(session: Session, event: InboundEvent) -> None:
    if not event.person_id:
        return
    person = session.get(Person, event.person_id)
    if not person:
        return
    person.stage = Stage.replied
    person.updated_at = datetime.utcnow()
    session.add(person)
    _cancel_follow_ups(session, event.person_id)
    logger.info("Reply detected — person %d stage → replied, follow-ups cancelled", event.person_id)


def _handle_bounce_hard(session: Session, event: InboundEvent) -> None:
    if not event.person_id:
        return
    person = session.get(Person, event.person_id)
    if not person:
        return
    person.email_valid = False
    person.stage = Stage.bounced
    person.updated_at = datetime.utcnow()
    session.add(person)

    from .pattern_learner import record_bounce

    if person.email:
        record_bounce(session, person, person.email)

    _cancel_follow_ups_for_channel(session, event.person_id, Channel.cold_email)
    logger.info("Hard bounce for person %d — email_valid=False, stage → bounced", event.person_id)


def _handle_opt_out(session: Session, event: InboundEvent) -> None:
    if not event.person_id:
        return
    person = session.get(Person, event.person_id)
    if not person:
        return
    person.stage = Stage.opted_out
    person.opted_out_at = datetime.utcnow()
    person.updated_at = datetime.utcnow()
    session.add(person)
    _cancel_follow_ups(session, event.person_id)
    # Leave event.processed=False so user confirms in UI
    logger.info("Opt-out for person %d — stage → opted_out, pending UI confirmation", event.person_id)


def _cancel_follow_ups(session: Session, person_id: int) -> None:
    tasks = session.exec(
        select(FollowUpTask).where(
            FollowUpTask.person_id == person_id,
            FollowUpTask.status == FollowUpStatus.pending,
        )
    ).all()
    for task in tasks:
        task.status = FollowUpStatus.cancelled
        session.add(task)
    if tasks:
        logger.info("Cancelled %d pending follow-up tasks for person %d", len(tasks), person_id)


def _cancel_follow_ups_for_channel(session: Session, person_id: int, channel: Channel) -> None:
    tasks = session.exec(
        select(FollowUpTask).where(
            FollowUpTask.person_id == person_id,
            FollowUpTask.status == FollowUpStatus.pending,
        )
    ).all()
    cancelled = 0
    for task in tasks:
        parent = session.get(Message, task.parent_message_id)
        if parent and parent.channel == channel:
            task.status = FollowUpStatus.cancelled
            session.add(task)
            cancelled += 1
    if cancelled:
        logger.info("Cancelled %d email-channel follow-ups for person %d", cancelled, person_id)
