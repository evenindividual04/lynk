from datetime import datetime
from unittest.mock import patch

from src.lynk.models.message import Message, MessageStatus
from src.lynk.models.template import Channel
from src.lynk.services import smtp_sender


def _make_message(channel: Channel = Channel.cold_email) -> Message:
    return Message(
        id=1,
        person_id=1,
        channel=channel,
        status=MessageStatus.draft,
        subject="Test subject",
        body='<p>Hello <a href="https://example.com">link</a></p>',
        tracking_id="test-tracking-id",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def test_short_circuits_when_sending_disabled(monkeypatch):
    monkeypatch.setattr(smtp_sender.settings, "sending_enabled", False)
    success, thread_id, error = smtp_sender.send_email(_make_message(), "test@example.com", "Test User")
    assert success is False
    assert error == "sending_disabled"
    assert thread_id is None


def test_returns_error_without_credentials(monkeypatch):
    monkeypatch.setattr(smtp_sender.settings, "sending_enabled", True)
    monkeypatch.setattr(smtp_sender.settings, "gmail_user", "")
    monkeypatch.setattr(smtp_sender.settings, "gmail_app_password", "")
    success, _, error = smtp_sender.send_email(_make_message(), "test@example.com", "Test")
    assert success is False
    assert error is not None


def test_pixel_injected_in_html_body(monkeypatch):
    monkeypatch.setattr(smtp_sender.settings, "sending_enabled", True)
    monkeypatch.setattr(smtp_sender.settings, "gmail_user", "user@test.com")
    monkeypatch.setattr(smtp_sender.settings, "gmail_app_password", "pass")
    monkeypatch.setattr(smtp_sender.settings, "tracking_base_url", "http://localhost:8000")

    captured_body: list[str] = []

    class FakeSMTP:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def login(self, u, p):
            pass

        def sendmail(self, frm, to, msg_str):
            captured_body.append(msg_str)

    with patch("smtplib.SMTP_SSL", return_value=FakeSMTP()):
        smtp_sender.send_email(_make_message(), "recipient@example.com", "Recipient")

    assert len(captured_body) == 1
    assert "/t/pixel/test-tracking-id.png" in captured_body[0]


def test_link_wrapped_in_body(monkeypatch):
    monkeypatch.setattr(smtp_sender.settings, "sending_enabled", True)
    monkeypatch.setattr(smtp_sender.settings, "gmail_user", "user@test.com")
    monkeypatch.setattr(smtp_sender.settings, "gmail_app_password", "pass")
    monkeypatch.setattr(smtp_sender.settings, "tracking_base_url", "http://localhost:8000")

    captured_body: list[str] = []

    class FakeSMTP:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def login(self, u, p):
            pass

        def sendmail(self, frm, to, msg_str):
            captured_body.append(msg_str)

    with patch("smtplib.SMTP_SSL", return_value=FakeSMTP()):
        smtp_sender.send_email(_make_message(), "recipient@example.com", "Recipient")

    assert "/t/click/test-tracking-id/0" in captured_body[0]


def test_threading_headers_set(monkeypatch):
    monkeypatch.setattr(smtp_sender.settings, "sending_enabled", True)
    monkeypatch.setattr(smtp_sender.settings, "gmail_user", "user@test.com")
    monkeypatch.setattr(smtp_sender.settings, "gmail_app_password", "pass")
    monkeypatch.setattr(smtp_sender.settings, "tracking_base_url", "http://localhost:8000")

    captured_body: list[str] = []

    class FakeSMTP:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def login(self, u, p):
            pass

        def sendmail(self, frm, to, msg_str):
            captured_body.append(msg_str)

    msg = _make_message()
    msg.thread_id = "<parent-id@lynk>"

    with patch("smtplib.SMTP_SSL", return_value=FakeSMTP()):
        smtp_sender.send_email(msg, "recipient@example.com", "Recipient")

    assert "In-Reply-To: <parent-id@lynk>" in captured_body[0]
