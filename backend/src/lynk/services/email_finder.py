from __future__ import annotations

import logging

import requests  # type: ignore[import-untyped]
from sqlmodel import Session, select

from ..config import settings
from ..models.company import Company
from ..models.email_candidate import EmailCandidate, EmailSource
from ..models.person import Person

logger = logging.getLogger(__name__)

_HIGH_CONFIDENCE = 80


def find_email(session: Session, person: Person, strategies: list[str] | None = None) -> list[EmailCandidate]:
    """
    Run email-finding strategies in priority order.
    Persists all candidates found. Stops early on first high-confidence verified hit.
    """
    all_strategies = [
        "existing",
        "pattern_db",
        "permutation",
        "hunter",
        "apollo",
        "skrapp",
        "linkedin_contact",
    ]
    active = strategies if strategies else all_strategies

    results: list[EmailCandidate] = []

    company: Company | None = None
    if person.current_company_id:
        company = session.get(Company, person.current_company_id)

    for strategy in active:
        candidates: list[EmailCandidate] = []

        if strategy == "existing":
            candidates = _from_existing(session, person)
        elif strategy == "pattern_db":
            candidates = _from_pattern_db(session, person, company)
        elif strategy == "permutation":
            candidates = _from_permutation(person, company)
        elif strategy == "hunter":
            candidates = _from_hunter(person, company)
        elif strategy == "apollo":
            candidates = _from_apollo(person, company)
        elif strategy == "skrapp":
            candidates = _from_skrapp(person, company)
        elif strategy == "linkedin_contact":
            candidates = _from_linkedin_contact(person)

        for c in candidates:
            existing = session.exec(
                select(EmailCandidate).where(
                    EmailCandidate.person_id == person.id,
                    EmailCandidate.email == c.email,
                )
            ).first()
            if existing:
                # Update confidence if the new source has higher confidence
                if c.confidence > existing.confidence:
                    existing.confidence = c.confidence
                    session.add(existing)
                results.append(existing)
            else:
                session.add(c)
                session.flush()
                results.append(c)

        # Short-circuit on a high-confidence verified candidate
        if any(c.confidence >= _HIGH_CONFIDENCE and c.verified for c in results):
            break

    return results


def _from_existing(session: Session, person: Person) -> list[EmailCandidate]:
    if person.email:
        return [
            EmailCandidate(  # type: ignore[arg-type]
                person_id=person.id, email=person.email, source=EmailSource.csv, confidence=90, verified=True
            )
        ]
    prior = session.exec(
        select(EmailCandidate).where(
            EmailCandidate.person_id == person.id,
            EmailCandidate.verified == True,  # noqa: E712
        )
    ).all()
    return list(prior)


def _from_pattern_db(session: Session, person: Person, company: Company | None) -> list[EmailCandidate]:
    if not company or not company.domain or not company.email_pattern or (company.pattern_confidence or 0) < 60:
        return []

    email = _apply_pattern(person, company.email_pattern, company.domain)
    if not email:
        return []

    return [
        EmailCandidate(
            person_id=person.id,  # type: ignore[arg-type]
            email=email,
            source=EmailSource.pattern_db,
            confidence=company.pattern_confidence or 60,
        )
    ]


def _from_permutation(person: Person, company: Company | None) -> list[EmailCandidate]:
    if not company or not company.domain:
        return []

    domain = company.domain
    first = (person.first_name or "").lower()
    last = (person.last_name or "").lower()

    if not first or not last:
        return []

    fi = first[0]
    patterns = [
        f"{first}.{last}@{domain}",
        f"{first}@{domain}",
        f"{fi}{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{fi}.{last}@{domain}",
        f"{last}.{first}@{domain}",
        f"{last}@{domain}",
    ]
    return [
        EmailCandidate(
            person_id=person.id,  # type: ignore[arg-type]
            email=email,
            source=EmailSource.permutation,
            confidence=30,
        )
        for email in patterns
    ]


def _from_hunter(person: Person, company: Company | None) -> list[EmailCandidate]:
    if not settings.hunter_api_key:
        return []
    if not company or not company.domain:
        return []

    try:
        resp = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": company.domain,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "api_key": settings.hunter_api_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        email = data.get("email")
        score = data.get("score", 0)
        if email:
            return [
                EmailCandidate(
                    person_id=person.id,  # type: ignore[arg-type]
                    email=email,
                    source=EmailSource.hunter,
                    confidence=int(score),
                )
            ]
    except Exception as exc:
        logger.warning("Hunter.io lookup failed for %s: %s", person.full_name, exc)

    return []


def _from_apollo(person: Person, company: Company | None) -> list[EmailCandidate]:
    if not settings.apollo_api_key:
        return []
    if not company:
        return []

    try:
        resp = requests.post(
            "https://api.apollo.io/api/v1/people/match",
            json={
                "first_name": person.first_name,
                "last_name": person.last_name,
                "organization_name": company.name,
                "reveal_personal_emails": False,
            },
            headers={"x-api-key": settings.apollo_api_key, "Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        matched = resp.json().get("person", {})
        email = matched.get("email")
        if email:
            return [
                EmailCandidate(
                    person_id=person.id,  # type: ignore[arg-type]
                    email=email,
                    source=EmailSource.apollo,
                    confidence=70,
                )
            ]
    except Exception as exc:
        logger.warning("Apollo lookup failed for %s: %s", person.full_name, exc)

    return []


def _from_skrapp(person: Person, company: Company | None) -> list[EmailCandidate]:
    if not settings.skrapp_api_key:
        return []
    if not company or not company.domain:
        return []

    try:
        resp = requests.get(
            "https://api.skrapp.io/api/v1/find",
            params={
                "firstName": person.first_name,
                "lastName": person.last_name,
                "domain": company.domain,
            },
            headers={"X-Access-Key": settings.skrapp_api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("email", {})
        email = data.get("email")
        accuracy = data.get("accuracy", 0)
        if email:
            return [
                EmailCandidate(
                    person_id=person.id,  # type: ignore[arg-type]
                    email=email,
                    source=EmailSource.skrapp,
                    confidence=int(accuracy),
                )
            ]
    except Exception as exc:
        logger.warning("Skrapp lookup failed for %s: %s", person.full_name, exc)

    return []


def _from_linkedin_contact(person: Person) -> list[EmailCandidate]:
    logger.info(
        "LinkedIn Contact Info is a manual fallback — open %s's LI profile and paste their email",
        person.full_name,
    )
    return []


def _apply_pattern(person: Person, pattern: str, domain: str) -> str | None:
    first = (person.first_name or "").lower()
    last = (person.last_name or "").lower()
    if not first or not last:
        return None
    fi = first[0]
    mapping = {
        "firstname.lastname": f"{first}.{last}",
        "firstname": first,
        "lastname": last,
        "flastname": f"{fi}{last}",
        "firstnamelastname": f"{first}{last}",
        "firstinitial.lastname": f"{fi}.{last}",
        "lastname.firstname": f"{last}.{first}",
        "firstnamelastinitial": f"{first}{last[0]}",
    }
    local = mapping.get(pattern)
    if not local:
        return None
    return f"{local}@{domain}"
