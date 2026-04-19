from __future__ import annotations

import logging

from sqlmodel import Session, select

from ..models.company import Company
from ..models.email_candidate import EmailCandidate
from ..models.person import Person

logger = logging.getLogger(__name__)

_PATTERN_CONFIDENCE_PER_SAMPLE = 15
_BOUNCE_PENALTY = 25


def _derive_pattern(email: str, person: Person) -> str | None:
    """
    Guess which email pattern was used based on person's name.
    Returns a token like 'firstname.lastname', 'firstname', 'flastname', etc.
    """
    local = email.split("@")[0].lower()
    first = (person.first_name or "").lower()
    last = (person.last_name or "").lower()

    if not first or not last:
        return None

    fi = first[0]
    li = last[0]

    candidates = {
        "firstname.lastname": f"{first}.{last}",
        "firstname": first,
        "lastname": last,
        "flastname": f"{fi}{last}",
        "firstnamelastname": f"{first}{last}",
        "firstinitial.lastname": f"{fi}.{last}",
        "lastname.firstname": f"{last}.{first}",
        "firstnamelastinitial": f"{first}{li}",
    }
    for pattern, value in candidates.items():
        if local == value:
            return pattern

    return None


def record_successful_send(session: Session, person: Person, email: str) -> None:
    if not person.current_company_id:
        return

    company = session.get(Company, person.current_company_id)
    if not company or not company.domain:
        return

    pattern = _derive_pattern(email, person)
    if not pattern:
        logger.debug("Could not derive pattern for %s / %s", email, person.full_name)
        return

    if company.email_pattern and company.email_pattern != pattern:
        # Inconsistent with stored pattern — halve confidence
        company.pattern_confidence = max(0, (company.email_pattern and company.pattern_confidence or 0) // 2)
        company.email_pattern = pattern
        company.pattern_samples = 1
        logger.info(
            "Pattern inconsistency at %s: was %s, now %s — confidence halved to %d",
            company.domain,
            company.email_pattern,
            pattern,
            company.pattern_confidence,
        )
    else:
        company.email_pattern = pattern
        company.pattern_samples = (company.pattern_samples or 0) + 1
        company.pattern_confidence = min(100, company.pattern_samples * _PATTERN_CONFIDENCE_PER_SAMPLE)
        logger.info(
            "Pattern %s confirmed for %s (samples=%d, confidence=%d)",
            pattern,
            company.domain,
            company.pattern_samples,
            company.pattern_confidence,
        )

    session.add(company)


def record_bounce(session: Session, person: Person, email: str) -> None:
    if not person.current_company_id:
        return

    company = session.get(Company, person.current_company_id)
    if company and company.email_pattern:
        pattern = _derive_pattern(email, person)
        if pattern == company.email_pattern:
            company.pattern_confidence = max(0, (company.pattern_confidence or 0) - _BOUNCE_PENALTY)
            logger.info(
                "Bounce penalised pattern %s at %s — confidence now %d",
                pattern,
                company.domain,
                company.pattern_confidence,
            )
            session.add(company)

    # Mark the candidate as bounced
    stmt = select(EmailCandidate).where(
        EmailCandidate.person_id == person.id,
        EmailCandidate.email == email,
    )
    candidate = session.exec(stmt).first()
    if candidate:
        candidate.bounced = True
        candidate.verified = False
        session.add(candidate)
