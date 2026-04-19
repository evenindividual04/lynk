import pytest
from sqlmodel import Session, SQLModel, StaticPool, create_engine

import src.lynk.models.email_candidate  # noqa: F401
import src.lynk.models.message  # noqa: F401
import src.lynk.models.template  # noqa: F401
from src.lynk.models.company import Company
from src.lynk.models.email_candidate import EmailCandidate, EmailSource
from src.lynk.models.person import Person, Source, Stage
from src.lynk.services.pattern_learner import record_bounce, record_successful_send


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _make_person(session: Session, first: str = "Jane", last: str = "Doe") -> Person:
    company = Company(name="Acme Corp", domain="acme.com")
    session.add(company)
    session.flush()
    person = Person(
        linkedin_url=f"https://linkedin.com/in/{first.lower()}{last.lower()}",
        full_name=f"{first} {last}",
        first_name=first,
        last_name=last,
        stage=Stage.not_contacted,
        source=Source.manual,
        current_company_id=company.id,
    )
    session.add(person)
    session.flush()
    return person


def test_record_successful_send_sets_pattern(session):
    person = _make_person(session)
    record_successful_send(session, person, "jane.doe@acme.com")
    session.flush()

    company = session.get(Company, person.current_company_id)
    assert company.email_pattern == "firstname.lastname"
    assert company.pattern_samples == 1
    assert company.pattern_confidence == 15


def test_record_successful_send_increments_samples(session):
    person = _make_person(session)
    record_successful_send(session, person, "jane.doe@acme.com")
    record_successful_send(session, person, "jane.doe@acme.com")
    session.flush()

    company = session.get(Company, person.current_company_id)
    assert company.pattern_samples == 2
    assert company.pattern_confidence == 30


def test_record_successful_send_halves_on_inconsistency(session):
    person = _make_person(session)
    record_successful_send(session, person, "jane.doe@acme.com")
    session.flush()

    # Now a different pattern — halves confidence
    record_successful_send(session, person, "jane@acme.com")
    session.flush()

    company = session.get(Company, person.current_company_id)
    assert company.email_pattern == "firstname"
    assert company.pattern_confidence <= 15


def test_record_bounce_penalises_confidence(session):
    person = _make_person(session)
    record_successful_send(session, person, "jane.doe@acme.com")
    session.flush()

    company = session.get(Company, person.current_company_id)
    assert company.pattern_confidence == 15

    record_bounce(session, person, "jane.doe@acme.com")
    session.flush()

    company = session.get(Company, person.current_company_id)
    assert company.pattern_confidence == 0


def test_record_bounce_marks_candidate_bounced(session):
    person = _make_person(session)
    candidate = EmailCandidate(
        person_id=person.id, email="jane.doe@acme.com", source=EmailSource.permutation, confidence=30
    )
    session.add(candidate)
    session.flush()

    record_bounce(session, person, "jane.doe@acme.com")
    session.flush()

    session.refresh(candidate)
    assert candidate.bounced is True
