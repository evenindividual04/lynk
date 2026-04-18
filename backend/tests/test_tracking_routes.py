from datetime import datetime

from src.lynk.models.message import ClickHit, Message, MessageStatus, PixelHit
from src.lynk.models.person import Person, Source, Stage
from src.lynk.models.template import Channel


def _seed_person(session) -> Person:
    p = Person(
        linkedin_url="https://www.linkedin.com/in/tracktest/",
        full_name="Track Test",
        first_name="Track",
        last_name="Test",
        stage=Stage.contacted_email,
        source=Source.manual,
    )
    session.add(p)
    session.flush()
    return p


def _seed_message(session, person_id: int, tracking_id: str) -> Message:
    m = Message(
        person_id=person_id,
        channel=Channel.cold_email,
        status=MessageStatus.sent,
        body="Hello",
        tracking_id=tracking_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


def test_pixel_logs_hit(client, session):
    person = _seed_person(session)
    msg = _seed_message(session, person.id, "pixel-test-id")

    resp = client.get("/t/pixel/pixel-test-id.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    from sqlmodel import select as sqlmodel_select

    hits = list(session.exec(sqlmodel_select(PixelHit).where(PixelHit.message_id == msg.id)).all())
    assert len(hits) == 1


def test_pixel_advances_stage_to_opened(client, session):
    person = _seed_person(session)
    _seed_message(session, person.id, "stage-advance-id")

    client.get("/t/pixel/stage-advance-id.png")

    session.refresh(person)
    assert person.stage == Stage.opened


def test_pixel_unknown_tracking_id_returns_png(client):
    resp = client.get("/t/pixel/no-such-id.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_click_logs_hit_and_redirects(client, session):
    person = _seed_person(session)
    msg = _seed_message(session, person.id, "click-test-id")

    resp = client.get("/t/click/click-test-id/0?url=https://example.com", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "https://example.com"

    from sqlmodel import select as sqlmodel_select

    hits = list(session.exec(sqlmodel_select(ClickHit).where(ClickHit.message_id == msg.id)).all())
    assert len(hits) == 1
    assert hits[0].link_id == 0
    assert hits[0].target_url == "https://example.com"
