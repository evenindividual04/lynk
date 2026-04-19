from datetime import datetime

from src.lynk.models.inbound_event import InboundEvent, InboundKind


def test_list_events_empty(client):
    resp = client.get("/api/inbound/events")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_events_with_filter(client, session):
    event = InboundEvent(
        kind=InboundKind.reply,
        gmail_msg_id="<test1@example.com>",
        received_at=datetime.utcnow(),
        processed=False,
    )
    session.add(event)
    session.commit()

    resp = client.get("/api/inbound/events?kind=reply")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["kind"] == "reply"


def test_mark_processed(client, session):
    event = InboundEvent(
        kind=InboundKind.opt_out,
        gmail_msg_id="<optout@example.com>",
        received_at=datetime.utcnow(),
        processed=False,
    )
    session.add(event)
    session.commit()
    session.refresh(event)

    resp = client.post(f"/api/inbound/events/{event.id}/mark-processed")
    assert resp.status_code == 200
    assert resp.json()["processed"] is True


def test_mark_processed_404(client):
    resp = client.post("/api/inbound/events/99999/mark-processed")
    assert resp.status_code == 404
