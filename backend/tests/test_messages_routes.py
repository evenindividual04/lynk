from datetime import datetime
from unittest.mock import patch

from src.lynk.models.follow_up import FollowUpTask
from src.lynk.models.person import Person, Source, Stage
from src.lynk.models.template import Channel, Scenario, Template, TemplateVersion


def _seed_template(session, channel: Channel = Channel.li_dm) -> Template:
    tmpl = Template(
        name="Test template",
        scenario=Scenario.ps_outreach,
        channel=channel,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(tmpl)
    session.flush()
    tv = TemplateVersion(
        template_id=tmpl.id,
        version=1,
        body_template="Hi {{ person.first_name }}!",
        created_at=datetime.utcnow(),
    )
    session.add(tv)
    session.flush()
    tmpl.active_version_id = tv.id
    session.add(tmpl)
    session.commit()
    session.refresh(tmpl)
    return tmpl


def _seed_person(session, email: str | None = "p@test.com") -> Person:
    p = Person(
        linkedin_url="https://www.linkedin.com/in/msgtest/",
        full_name="Msg Test",
        first_name="Msg",
        last_name="Test",
        email=email,
        stage=Stage.not_contacted,
        source=Source.manual,
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def test_draft_message_calls_claude(client, session):
    person = _seed_person(session)
    _seed_template(session)

    with patch("src.lynk.api.routes.messages.claude_client.generate_message") as mock_gen:
        mock_gen.return_value = {"subject": None, "body": "Hi Msg, hope you're well!"}
        resp = client.post(
            "/api/messages/draft",
            json={
                "person_id": person.id,
                "channel": "li_dm",
                "scenario": "ps_outreach",
            },
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "draft"
    assert data["body"] == "Hi Msg, hope you're well!"
    assert data["channel"] == "li_dm"


def test_draft_404_for_missing_person(client, session):
    _seed_template(session)
    with patch("src.lynk.api.routes.messages.claude_client.generate_message") as mock_gen:
        mock_gen.return_value = {"subject": None, "body": "x"}
        resp = client.post(
            "/api/messages/draft",
            json={
                "person_id": 99999,
                "channel": "li_dm",
                "scenario": "ps_outreach",
            },
        )
    assert resp.status_code == 404


def test_update_draft_body(client, session):
    person = _seed_person(session)
    _seed_template(session)

    with patch("src.lynk.api.routes.messages.claude_client.generate_message") as mock_gen:
        mock_gen.return_value = {"subject": None, "body": "original"}
        resp = client.post(
            "/api/messages/draft",
            json={
                "person_id": person.id,
                "channel": "li_dm",
                "scenario": "ps_outreach",
            },
        )
    msg_id = resp.json()["id"]

    resp2 = client.patch(f"/api/messages/{msg_id}", json={"body": "edited body"})
    assert resp2.status_code == 200
    assert resp2.json()["body"] == "edited body"


def test_mark_sent_li_advances_stage(client, session):
    person = _seed_person(session)
    _seed_template(session)

    with patch("src.lynk.api.routes.messages.claude_client.generate_message") as mock_gen:
        mock_gen.return_value = {"subject": None, "body": "hi"}
        resp = client.post(
            "/api/messages/draft",
            json={
                "person_id": person.id,
                "channel": "li_dm",
                "scenario": "ps_outreach",
            },
        )
    msg_id = resp.json()["id"]

    resp2 = client.post(f"/api/messages/{msg_id}/mark-sent")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "sent"

    session.refresh(person)
    assert person.stage == Stage.contacted_li


def test_mark_sent_schedules_follow_ups(client, session):
    person = _seed_person(session)
    _seed_template(session, channel=Channel.li_dm)

    with patch("src.lynk.api.routes.messages.claude_client.generate_message") as mock_gen:
        mock_gen.return_value = {"subject": None, "body": "hi"}
        resp = client.post(
            "/api/messages/draft",
            json={
                "person_id": person.id,
                "channel": "li_dm",
                "scenario": "ps_outreach",
            },
        )
    msg_id = resp.json()["id"]
    client.post(f"/api/messages/{msg_id}/mark-sent")

    from sqlmodel import select as sqlmodel_select

    tasks = list(session.exec(sqlmodel_select(FollowUpTask).where(FollowUpTask.person_id == person.id)).all())
    assert len(tasks) == 2  # Day 3 + Day 7


def test_cancel_message(client, session):
    person = _seed_person(session)
    _seed_template(session)

    with patch("src.lynk.api.routes.messages.claude_client.generate_message") as mock_gen:
        mock_gen.return_value = {"subject": None, "body": "x"}
        resp = client.post(
            "/api/messages/draft",
            json={
                "person_id": person.id,
                "channel": "li_dm",
                "scenario": "ps_outreach",
            },
        )
    msg_id = resp.json()["id"]

    resp2 = client.post(f"/api/messages/{msg_id}/cancel")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "cancelled"


def test_list_messages_filter_by_status(client, session):
    person = _seed_person(session)
    _seed_template(session)

    with patch("src.lynk.api.routes.messages.claude_client.generate_message") as mock_gen:
        mock_gen.return_value = {"subject": None, "body": "x"}
        client.post(
            "/api/messages/draft",
            json={
                "person_id": person.id,
                "channel": "li_dm",
                "scenario": "ps_outreach",
            },
        )

    resp = client.get("/api/messages?status=draft")
    assert resp.status_code == 200
    assert all(m["status"] == "draft" for m in resp.json())
