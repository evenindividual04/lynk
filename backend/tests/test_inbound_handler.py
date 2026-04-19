from datetime import datetime

import pytest
from sqlmodel import Session, SQLModel, StaticPool, create_engine

import src.lynk.models.email_candidate  # noqa: F401
import src.lynk.models.inbound_event  # noqa: F401
import src.lynk.models.message  # noqa: F401
import src.lynk.models.template  # noqa: F401
from src.lynk.models.company import Company
from src.lynk.models.follow_up import FollowUpKind, FollowUpStatus, FollowUpTask
from src.lynk.models.inbound_event import InboundEvent, InboundKind
from src.lynk.models.message import Message, MessageStatus
from src.lynk.models.person import Person, Source, Stage
from src.lynk.models.template import Channel
from src.lynk.services.inbound_handler import apply_event


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _make_person(session: Session, stage: Stage = Stage.contacted_email) -> Person:
    company = Company(name="Acme", domain="acme.com")
    session.add(company)
    session.flush()
    person = Person(
        linkedin_url="https://linkedin.com/in/test",
        full_name="Test User",
        first_name="Test",
        last_name="User",
        stage=stage,
        source=Source.manual,
        current_company_id=company.id,
        email="test@acme.com",
    )
    session.add(person)
    session.flush()
    return person


def _make_message(session: Session, person_id: int, channel: Channel = Channel.cold_email) -> Message:
    msg = Message(
        person_id=person_id,
        channel=channel,
        status=MessageStatus.sent,
        body="Hello",
        sent_at=datetime.utcnow(),
    )
    session.add(msg)
    session.flush()
    return msg


def _make_follow_up(session: Session, person_id: int, parent_id: int) -> FollowUpTask:
    task = FollowUpTask(
        person_id=person_id,
        parent_message_id=parent_id,
        kind=FollowUpKind.nudge_unopened,
        scheduled_for=datetime.utcnow(),
        status=FollowUpStatus.pending,
    )
    session.add(task)
    session.flush()
    return task


def test_handle_reply_advances_stage_and_cancels_follow_ups(session):
    person = _make_person(session)
    msg = _make_message(session, person.id)  # type: ignore[arg-type]
    task = _make_follow_up(session, person.id, msg.id)  # type: ignore[arg-type]

    event = InboundEvent(
        kind=InboundKind.reply,
        gmail_msg_id="<reply1@test>",
        person_id=person.id,
        received_at=datetime.utcnow(),
    )
    session.add(event)
    session.flush()

    apply_event(session, event)
    session.flush()

    session.refresh(person)
    session.refresh(task)
    assert person.stage == Stage.replied
    assert task.status == FollowUpStatus.cancelled


def test_handle_bounce_hard(session):
    person = _make_person(session)
    msg = _make_message(session, person.id)  # type: ignore[arg-type]
    task = _make_follow_up(session, person.id, msg.id)  # type: ignore[arg-type]

    event = InboundEvent(
        kind=InboundKind.bounce_hard,
        gmail_msg_id="<bounce1@test>",
        person_id=person.id,
        received_at=datetime.utcnow(),
    )
    session.add(event)
    session.flush()

    apply_event(session, event)
    session.flush()

    session.refresh(person)
    session.refresh(task)
    assert person.stage == Stage.bounced
    assert person.email_valid is False
    assert task.status == FollowUpStatus.cancelled


def test_handle_opt_out(session):
    person = _make_person(session)
    msg = _make_message(session, person.id)  # type: ignore[arg-type]
    task = _make_follow_up(session, person.id, msg.id)  # type: ignore[arg-type]

    event = InboundEvent(
        kind=InboundKind.opt_out,
        gmail_msg_id="<optout1@test>",
        person_id=person.id,
        received_at=datetime.utcnow(),
    )
    session.add(event)
    session.flush()

    apply_event(session, event)
    session.flush()

    session.refresh(person)
    session.refresh(task)
    session.refresh(event)
    assert person.stage == Stage.opted_out
    assert person.opted_out_at is not None
    assert task.status == FollowUpStatus.cancelled
    # processed=False — requires manual confirmation
    assert event.processed is False
