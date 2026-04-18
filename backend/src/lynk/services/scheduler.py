from __future__ import annotations

import logging
from datetime import datetime, timedelta

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore  # type: ignore[import-untyped]
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from sqlmodel import Session, select

from ..config import settings
from ..db import engine
from ..models.follow_up import FollowUpKind, FollowUpStatus, FollowUpTask
from ..models.message import Message, MessageStatus
from ..models.person import Person
from ..models.template import Channel

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

# Only schedule two follow-ups: Day 3 nudge (assume unopened until Phase 3 open detection)
# and Day 7 final bump. nudge_opened is set in Phase 3 when pixel data confirms open.
FOLLOW_UP_SCHEDULE = [
    (FollowUpKind.nudge_unopened, 3),
    (FollowUpKind.final_bump, 7),
]


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        jobstores = {"default": SQLAlchemyJobStore(engine=engine)}
        _scheduler = BackgroundScheduler(jobstores=jobstores)
    return _scheduler


def start_scheduler() -> None:
    if not settings.follow_up_scheduler_enabled:
        logger.info("Follow-up scheduler disabled via config")
        return
    sched = get_scheduler()
    if not sched.running:
        sched.add_job(
            process_follow_ups,
            "interval",
            minutes=15,
            id="process_follow_ups",
            replace_existing=True,
        )
        sched.start()
        logger.info("Follow-up scheduler started")


def stop_scheduler() -> None:
    sched = get_scheduler()
    if sched.running:
        sched.shutdown(wait=False)
        logger.info("Follow-up scheduler stopped")


def schedule_follow_ups(session: Session, message: Message) -> list[FollowUpTask]:
    """
    Schedule Day-3 and Day-7 follow-up tasks for a sent message.
    Only for email/LI DM channels (connection notes don't get follow-ups).
    """
    if message.channel == Channel.li_connection_note:
        return []

    sent_at = message.sent_at or datetime.utcnow()
    tasks: list[FollowUpTask] = []

    for kind, days in FOLLOW_UP_SCHEDULE:
        task = FollowUpTask(
            person_id=message.person_id,
            parent_message_id=message.id,  # type: ignore[arg-type]
            kind=kind,
            scheduled_for=sent_at + timedelta(days=days),
            status=FollowUpStatus.pending,
        )
        session.add(task)
        tasks.append(task)

    session.flush()
    return tasks


def process_follow_ups() -> None:
    """
    Background job: find due follow-up tasks and generate draft messages.
    Runs every 15 minutes.
    """
    with Session(engine) as session:
        due = session.exec(
            select(FollowUpTask).where(
                FollowUpTask.scheduled_for <= datetime.utcnow(),
                FollowUpTask.status == FollowUpStatus.pending,
            )
        ).all()

        if not due:
            return

        logger.info("Processing %d due follow-up tasks", len(due))

        for task in due:
            try:
                _generate_follow_up(session, task)
                task.status = FollowUpStatus.completed
                session.add(task)
            except Exception as exc:
                logger.error("Failed to process follow-up task %s: %s", task.id, exc)

        session.commit()


def _generate_follow_up(session: Session, task: FollowUpTask) -> None:
    """Generate a draft follow-up message for a task."""
    parent = session.get(Message, task.parent_message_id)
    person = session.get(Person, task.person_id)
    if not parent or not person:
        logger.warning("Parent message or person not found for task %s", task.id)
        return

    kind_descriptions = {
        FollowUpKind.nudge_unopened: "gentle follow-up (the original email may not have been seen)",
        FollowUpKind.nudge_opened: "gentle follow-up (the original email was opened but not replied to)",
        FollowUpKind.final_bump: "final follow-up (last attempt before marking as cold)",
    }

    body_prompt = (
        f"This is a {kind_descriptions[task.kind]}.\n"
        f"Reference the original message from {parent.sent_at} if relevant.\n"
        f"Keep it very short (2-3 sentences max). Be respectful of their time.\n\n"
        f"Original message body:\n{parent.body}"
    )

    # Generate via Claude if API key is set, otherwise use a simple template
    draft_body = body_prompt
    if settings.anthropic_api_key:
        try:
            from ..models.template import TemplateVersion
            from .claude_client import generate_message

            # Create a minimal TemplateVersion-like object for the follow-up
            mock_tv = TemplateVersion(
                template_id=0,
                version=1,
                body_template=body_prompt,
            )
            result = generate_message(
                person=person,
                template_version=mock_tv,
                scenario_context="follow-up to previous outreach",
                channel=parent.channel,
                custom_instructions=kind_descriptions[task.kind],
            )
            draft_body = result.get("body") or body_prompt
        except Exception as exc:
            logger.warning("Claude generation failed for follow-up %s: %s", task.id, exc)

    follow_up_msg = Message(
        person_id=task.person_id,
        channel=parent.channel,
        status=MessageStatus.draft,
        subject=f"Re: {parent.subject}" if parent.subject else None,
        body=draft_body,
        parent_message_id=parent.id,
        thread_id=parent.thread_id,
    )
    session.add(follow_up_msg)
    session.flush()

    task.generated_message_id = follow_up_msg.id
