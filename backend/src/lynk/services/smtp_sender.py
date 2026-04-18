from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import settings
from ..models.message import Message
from .tracking import inject_pixel, wrap_links

logger = logging.getLogger(__name__)

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465


def send_email(
    message: Message,
    recipient_email: str,
    recipient_name: str,
) -> tuple[bool, str | None, str | None]:
    """
    Send an email via Gmail SMTP.
    Returns (success, thread_id, error_str).
    thread_id is the Gmail Message-ID for threading follow-ups.

    Short-circuits with (False, None, "sending_disabled") when SENDING_ENABLED=false.
    """
    if not settings.sending_enabled:
        logger.info("SENDING_ENABLED=false — skipping SMTP send for message %s", message.id)
        return False, None, "sending_disabled"

    if not settings.gmail_user or not settings.gmail_app_password:
        return False, None, "Gmail credentials not configured"

    body = message.body or ""
    # Wrap links and inject pixel for HTML emails
    body, _ = wrap_links(body, message.tracking_id, settings.tracking_base_url)
    body = inject_pixel(body, message.tracking_id, settings.tracking_base_url)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = message.subject or "(no subject)"
    msg["From"] = settings.gmail_user
    msg["To"] = f"{recipient_name} <{recipient_email}>"
    msg["Message-ID"] = f"<{message.tracking_id}@lynk>"

    # Thread follow-ups by referencing parent message's Message-ID
    if message.thread_id:
        msg["In-Reply-To"] = message.thread_id
        msg["References"] = message.thread_id

    # Send as plain text + HTML alternative
    plain = _html_to_plain(body)
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.sendmail(settings.gmail_user, [recipient_email], msg.as_string())
        thread_id = f"<{message.tracking_id}@lynk>"
        logger.info("Sent email to %s (tracking_id=%s)", recipient_email, message.tracking_id)
        return True, thread_id, None
    except smtplib.SMTPException as exc:
        logger.error("SMTP error for message %s: %s", message.id, exc)
        return False, None, str(exc)


def _html_to_plain(html: str) -> str:
    """Minimal HTML → plain text conversion (strips tags)."""
    import re

    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()
