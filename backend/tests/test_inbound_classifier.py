import email
from email.mime.text import MIMEText
from unittest.mock import MagicMock

from src.lynk.models.inbound_event import InboundKind
from src.lynk.services.inbound_classifier import classify


def _build_msg(from_addr: str, subject: str, body: str, extra_headers: dict | None = None) -> email.message.Message:
    msg = MIMEText(body)
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg["Message-Id"] = "<test@example.com>"
    if extra_headers:
        for k, v in extra_headers.items():
            msg[k] = v
    return msg


def _mock_session():
    session = MagicMock()
    session.exec.return_value.first.return_value = None
    session.exec.return_value.all.return_value = []
    return session


def test_classify_bounce_hard():
    msg = _build_msg("mailer-daemon@gmail.com", "Delivery Status Notification", "5.1.1 User unknown")
    kind, person_id, msg_id = classify(msg, _mock_session())
    assert kind == InboundKind.bounce_hard


def test_classify_bounce_soft():
    msg = _build_msg("mailer-daemon@gmail.com", "Delivery Status Notification", "4.2.2 Mailbox full")
    kind, person_id, msg_id = classify(msg, _mock_session())
    assert kind == InboundKind.bounce_soft


def test_classify_auto_reply():
    msg = _build_msg("user@company.com", "Out of Office: Re: Hello", "I am away", {"Auto-Submitted": "auto-replied"})
    kind, person_id, msg_id = classify(msg, _mock_session())
    assert kind == InboundKind.auto_reply


def test_classify_auto_reply_by_subject():
    msg = _build_msg("user@company.com", "Automatic reply: Hi", "I will be back")
    kind, person_id, msg_id = classify(msg, _mock_session())
    assert kind == InboundKind.auto_reply


def test_classify_opt_out():
    msg = _build_msg("person@company.com", "Re: Outreach", "Please unsubscribe me from your emails")
    kind, person_id, msg_id = classify(msg, _mock_session())
    assert kind == InboundKind.opt_out


def test_classify_reply():
    msg = _build_msg("person@company.com", "Re: Outreach", "Thanks for reaching out!")
    kind, person_id, msg_id = classify(msg, _mock_session())
    assert kind == InboundKind.reply
