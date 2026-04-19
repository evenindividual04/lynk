from unittest.mock import patch

from src.lynk.models.company import Company
from src.lynk.models.person import Person, Source, Stage


def _seed_person(session, email=None):
    company = Company(name="Finder Corp", domain="findercorp.com")
    session.add(company)
    session.flush()
    person = Person(
        linkedin_url="https://linkedin.com/in/finder-test",
        full_name="Finder Test",
        first_name="Finder",
        last_name="Test",
        stage=Stage.not_contacted,
        source=Source.manual,
        current_company_id=company.id,
        email=email,
    )
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


def test_find_email_returns_candidates(client, session):
    person = _seed_person(session)

    with patch("src.lynk.services.email_finder._from_hunter", return_value=[]):
        with patch("src.lynk.services.email_finder._from_apollo", return_value=[]):
            with patch("src.lynk.services.email_finder._from_skrapp", return_value=[]):
                resp = client.post("/api/email-finder/find", json={"person_id": person.id})

    assert resp.status_code == 200
    candidates = resp.json()
    assert isinstance(candidates, list)
    assert len(candidates) > 0
    assert all("email" in c for c in candidates)


def test_find_email_opted_out_403(client, session):
    person = _seed_person(session)
    person.stage = Stage.opted_out
    session.add(person)
    session.commit()

    resp = client.post("/api/email-finder/find", json={"person_id": person.id})
    assert resp.status_code == 403


def test_find_email_person_not_found(client):
    resp = client.post("/api/email-finder/find", json={"person_id": 99999})
    assert resp.status_code == 404


def test_verify_candidate(client, session):
    person = _seed_person(session)

    with patch("src.lynk.services.email_finder._from_hunter", return_value=[]):
        with patch("src.lynk.services.email_finder._from_apollo", return_value=[]):
            with patch("src.lynk.services.email_finder._from_skrapp", return_value=[]):
                candidates = client.post("/api/email-finder/find", json={"person_id": person.id}).json()

    cid = candidates[0]["id"]
    with patch("src.lynk.services.email_verifier.verify_smtp", return_value=(True, "OK")):
        resp = client.post(f"/api/email-finder/candidates/{cid}/verify")

    assert resp.status_code == 200
    assert resp.json()["verified"] is True


def test_accept_candidate_sets_person_email(client, session):
    person = _seed_person(session)

    with patch("src.lynk.services.email_finder._from_hunter", return_value=[]):
        with patch("src.lynk.services.email_finder._from_apollo", return_value=[]):
            with patch("src.lynk.services.email_finder._from_skrapp", return_value=[]):
                candidates = client.post("/api/email-finder/find", json={"person_id": person.id}).json()

    cid = candidates[0]["id"]
    resp = client.post(f"/api/email-finder/candidates/{cid}/accept")
    assert resp.status_code == 200

    person_resp = client.get(f"/api/people/{person.id}").json()
    assert person_resp["email"] == candidates[0]["email"]
