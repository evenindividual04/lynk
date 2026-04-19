from __future__ import annotations

import logging
import smtplib

from sqlmodel import Session

from ..models.email_candidate import EmailCandidate

logger = logging.getLogger(__name__)

_CATCH_ALL_REASON = "unknown/catch-all — treating as deliverable"


def verify_syntax(email: str) -> bool:
    try:
        from email_validator import validate_email

        validate_email(email, check_deliverability=False)
        return True
    except Exception:
        return False


def verify_smtp(email: str, timeout: int = 8) -> tuple[bool, str]:
    """
    MX lookup + SMTP RCPT TO handshake.
    Only rejects on explicit 5xx — catch-all / unknown treated as deliverable.
    Returns (is_deliverable, reason).
    """
    try:
        import dns.resolver

        domain = email.split("@", 1)[1]
        try:
            mx_records = dns.resolver.resolve(domain, "MX")
            mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange).rstrip(".")
        except Exception as exc:
            logger.debug("MX lookup failed for %s: %s", domain, exc)
            return True, _CATCH_ALL_REASON

        try:
            with smtplib.SMTP(timeout=timeout) as smtp:
                smtp.connect(mx_host, 25)
                smtp.helo("localhost")
                smtp.mail("")
                code, msg = smtp.rcpt(email)
                reason = msg.decode(errors="replace") if isinstance(msg, bytes) else str(msg)
                if code >= 500:
                    return False, f"SMTP {code}: {reason}"
                return True, f"SMTP {code}: {reason}"
        except smtplib.SMTPConnectError as exc:
            logger.debug("SMTP connect error for %s: %s", email, exc)
            return True, _CATCH_ALL_REASON
        except TimeoutError:
            logger.debug("SMTP timeout for %s", email)
            return True, _CATCH_ALL_REASON
        except Exception as exc:
            logger.debug("SMTP check error for %s: %s", email, exc)
            return True, _CATCH_ALL_REASON

    except Exception as exc:
        logger.warning("verify_smtp unexpected error for %s: %s", email, exc)
        return True, _CATCH_ALL_REASON


def verify_candidate(session: Session, candidate: EmailCandidate) -> EmailCandidate:
    if not verify_syntax(candidate.email):
        candidate.verified = False
        candidate.bounced = True
        session.add(candidate)
        return candidate

    deliverable, reason = verify_smtp(candidate.email)
    candidate.verified = deliverable
    if not deliverable:
        candidate.bounced = True
    logger.info("SMTP verify %s → %s (%s)", candidate.email, deliverable, reason)
    session.add(candidate)
    return candidate
