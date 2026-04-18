from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ...config import settings
from ...models.company import Company
from ...models.message import Message, MessageStatus
from ...models.person import Person, Stage
from ...models.template import Channel, Template, TemplateVersion
from ...schemas.message import DraftRequest, MessageRead, MessageUpdate, SendResponse
from ...services import claude_client
from ...services.scheduler import schedule_follow_ups
from ...services.smtp_sender import send_email
from ..deps import SessionDep

router = APIRouter(prefix="/messages", tags=["messages"])


def _get_person_or_404(session: SessionDep, person_id: int) -> Person:
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


def _get_message_or_404(session: SessionDep, message_id: int) -> Message:
    message = session.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.get("", response_model=list[MessageRead])
def list_messages(
    session: SessionDep,
    person_id: int | None = None,
    status: MessageStatus | None = None,
    channel: Channel | None = None,
) -> list[Message]:
    stmt = select(Message)
    if person_id is not None:
        stmt = stmt.where(Message.person_id == person_id)
    if status is not None:
        stmt = stmt.where(Message.status == status)
    if channel is not None:
        stmt = stmt.where(Message.channel == channel)
    stmt = stmt.order_by(Message.created_at.desc())  # type: ignore[attr-defined]
    return list(session.exec(stmt).all())


@router.post("/draft", response_model=MessageRead, status_code=201)
def draft_message(data: DraftRequest, session: SessionDep) -> Message:
    person = _get_person_or_404(session, data.person_id)

    company_name: str | None = None
    if person.current_company_id:
        company = session.get(Company, person.current_company_id)
        if company:
            company_name = company.name

    template_version: TemplateVersion | None = None
    if data.template_id is not None:
        template = session.get(Template, data.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        if template.active_version_id:
            template_version = session.get(TemplateVersion, template.active_version_id)

    if template_version is None:
        # Auto-select the first matching template for scenario + channel if none specified
        stmt = select(Template).where(Template.scenario == data.scenario, Template.channel == data.channel).limit(1)
        template = session.exec(stmt).first()
        if template and template.active_version_id:
            template_version = session.get(TemplateVersion, template.active_version_id)

    if template_version is None:
        raise HTTPException(
            status_code=422,
            detail=f"No template found for scenario={data.scenario}, channel={data.channel}. "
            "Create one at POST /api/templates first.",
        )

    result = claude_client.generate_message(
        person=person,
        template_version=template_version,
        scenario_context=data.scenario,
        channel=data.channel,
        company_name=company_name,
        custom_instructions=data.custom_instructions,
    )

    message = Message(
        person_id=person.id,  # type: ignore[arg-type]
        template_version_id=template_version.id,
        channel=data.channel,
        status=MessageStatus.draft,
        subject=result.get("subject"),
        body=result.get("body") or "",
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


@router.patch("/{message_id}", response_model=MessageRead)
def update_message(message_id: int, data: MessageUpdate, session: SessionDep) -> Message:
    message = _get_message_or_404(session, message_id)
    if message.status not in (MessageStatus.draft, MessageStatus.queued):
        raise HTTPException(status_code=400, detail="Only draft/queued messages can be edited")
    if data.subject is not None:
        message.subject = data.subject
    if data.body is not None:
        message.body = data.body
    message.updated_at = datetime.utcnow()
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


@router.post("/{message_id}/send", response_model=SendResponse)
def send_message(message_id: int, session: SessionDep) -> SendResponse:
    message = _get_message_or_404(session, message_id)
    if message.status not in (MessageStatus.draft, MessageStatus.queued):
        raise HTTPException(status_code=400, detail="Message is not in a sendable state")

    person = _get_person_or_404(session, message.person_id)

    # LinkedIn channels: mark sent immediately (user copies to LI manually)
    if message.channel in (Channel.li_connection_note, Channel.li_dm):
        return _mark_sent_linkedin(session, message, person)

    # Email channel: SMTP send (or short-circuit if disabled)
    if not person.email:
        raise HTTPException(status_code=422, detail="Person has no email address")

    success, thread_id, error = send_email(message, person.email, person.full_name)

    if not settings.sending_enabled:
        return SendResponse(
            message=MessageRead.model_validate(message.model_dump()),
            sending_enabled=False,
            warning="SENDING_ENABLED=false — set it to true and provide Gmail credentials to send real email",
        )

    if success:
        message.status = MessageStatus.sent
        message.sent_at = datetime.utcnow()
        message.thread_id = thread_id
        _advance_stage(person, message.channel)
        session.add(person)
        schedule_follow_ups(session, message)
    else:
        message.status = MessageStatus.failed
        message.error = error

    message.updated_at = datetime.utcnow()
    session.add(message)
    session.commit()
    session.refresh(message)
    return SendResponse(
        message=MessageRead.model_validate(message.model_dump()),
        sending_enabled=True,
        warning=error if not success else None,
    )


@router.post("/{message_id}/mark-sent", response_model=MessageRead)
def mark_sent(message_id: int, session: SessionDep) -> MessageRead:
    """Mark a LinkedIn message as sent by the user (user sent it manually in LI)."""
    message = _get_message_or_404(session, message_id)
    if message.status not in (MessageStatus.draft, MessageStatus.queued):
        raise HTTPException(status_code=400, detail="Message is not in a sendable state")
    person = _get_person_or_404(session, message.person_id)
    return _mark_sent_linkedin(session, message, person).message


@router.post("/{message_id}/cancel", response_model=MessageRead)
def cancel_message(message_id: int, session: SessionDep) -> Message:
    message = _get_message_or_404(session, message_id)
    if message.status == MessageStatus.sent:
        raise HTTPException(status_code=400, detail="Cannot cancel a sent message")
    message.status = MessageStatus.cancelled
    message.updated_at = datetime.utcnow()
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def _mark_sent_linkedin(session: SessionDep, message: Message, person: Person) -> SendResponse:
    message.status = MessageStatus.sent
    message.sent_at = datetime.utcnow()
    _advance_stage(person, message.channel)
    session.add(person)
    message.updated_at = datetime.utcnow()
    session.add(message)
    schedule_follow_ups(session, message)
    session.commit()
    session.refresh(message)
    return SendResponse(
        message=MessageRead.model_validate(message.model_dump()),
        sending_enabled=settings.sending_enabled,
        warning=None,
    )


def _advance_stage(person: Person, channel: Channel) -> None:
    """Move person to the appropriate 'contacted' stage."""
    current = person.stage
    if channel == Channel.cold_email:
        if current == Stage.not_contacted:
            person.stage = Stage.contacted_email
        elif current == Stage.contacted_li:
            person.stage = Stage.contacted_both
    elif channel in (Channel.li_connection_note, Channel.li_dm):
        if current == Stage.not_contacted:
            person.stage = Stage.contacted_li
        elif current == Stage.contacted_email:
            person.stage = Stage.contacted_both
