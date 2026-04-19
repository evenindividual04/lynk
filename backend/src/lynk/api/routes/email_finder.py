from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...models.email_candidate import EmailCandidate
from ...models.person import Person, Stage
from ...schemas.email_finder import EmailCandidateRead, FindEmailRequest
from ...services import email_finder as finder_svc
from ...services import email_verifier, pattern_learner
from ..deps import SessionDep

router = APIRouter(prefix="/email-finder", tags=["email-finder"])


def _get_person_or_404(session: SessionDep, person_id: int) -> Person:
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


def _get_candidate_or_404(session: SessionDep, candidate_id: int) -> EmailCandidate:
    candidate = session.get(EmailCandidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="EmailCandidate not found")
    return candidate


@router.post("/find", response_model=list[EmailCandidateRead])
def find_email(data: FindEmailRequest, session: SessionDep) -> list[EmailCandidate]:
    person = _get_person_or_404(session, data.person_id)
    if person.stage == Stage.opted_out:
        raise HTTPException(status_code=403, detail="Person has opted out — cannot search for email")
    candidates = finder_svc.find_email(session, person, data.strategies)
    session.commit()
    for c in candidates:
        session.refresh(c)
    return candidates


@router.post("/candidates/{candidate_id}/verify", response_model=EmailCandidateRead)
def verify_candidate(candidate_id: int, session: SessionDep) -> EmailCandidate:
    candidate = _get_candidate_or_404(session, candidate_id)
    email_verifier.verify_candidate(session, candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


@router.post("/candidates/{candidate_id}/accept", response_model=EmailCandidateRead)
def accept_candidate(candidate_id: int, session: SessionDep) -> EmailCandidate:
    candidate = _get_candidate_or_404(session, candidate_id)
    person = _get_person_or_404(session, candidate.person_id)
    person.email = candidate.email
    person.email_valid = True
    session.add(person)
    pattern_learner.record_successful_send(session, person, candidate.email)
    candidate.verified = True
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate
