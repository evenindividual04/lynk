import csv
import io

from sqlmodel import select

from src.lynk.models.person import Person, Position, Source
from src.lynk.services.csv_import import import_csv
from tests.fixtures.sample_csv import make_linkedin_csv_with_notes, make_sample_csv

_HDR = ["First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"]


def _make_csv(*rows: list[str]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(_HDR)
    for row in rows:
        w.writerow(row)
    return buf.getvalue().encode()


def test_import_basic(session):
    csv_bytes = make_sample_csv(5)
    result = import_csv(csv_bytes, session)
    assert result.imported == 5
    assert result.merged == 0
    assert result.skipped == 0
    assert result.errors == []


def test_import_with_linkedin_preamble(session):
    """LinkedIn exports have BOM + notes lines before the header."""
    csv_bytes = make_linkedin_csv_with_notes(3)
    result = import_csv(csv_bytes, session)
    assert result.imported == 3


def test_import_deduplication(session):
    url = "https://www.linkedin.com/in/test-person/"
    csv1 = _make_csv(["Alice", "Smith", url, "alice@example.com", "Acme", "Engineer", "01 Jan 2024"])

    result1 = import_csv(csv1, session)
    assert result1.imported == 1

    result2 = import_csv(csv1, session)
    assert result2.imported == 0
    assert result2.merged == 1


def test_import_url_normalization(session):
    """Different URL variants for the same person should deduplicate."""
    csv1 = _make_csv(
        ["Alice", "Smith", "https://www.linkedin.com/in/test-person/", "a@x.com", "Acme", "Eng", "01 Jan 2024"]
    )
    csv2 = _make_csv(
        [
            "Alice",
            "Smith",
            "http://LinkedIn.COM/in/Test-Person?utm_source=share",
            "a@x.com",
            "Acme",
            "Eng",
            "01 Jan 2024",
        ]
    )
    result1 = import_csv(csv1, session)
    result2 = import_csv(csv2, session)
    assert result1.imported == 1
    assert result2.merged == 1


def test_import_marks_source_as_csv(session):
    import_csv(make_sample_csv(1), session)
    people = list(session.exec(select(Person)).all())
    assert all(p.source == Source.csv_import for p in people)


def test_import_skips_missing_url(session):
    csv_bytes = _make_csv(["Alice", "Smith", "", "alice@example.com", "Acme", "Engineer", "01 Jan 2024"])
    result = import_csv(csv_bytes, session)
    assert result.skipped == 1


def test_import_position_history_on_merge(session):
    """When a person is re-imported with a new job, the old one becomes history."""
    url = "https://www.linkedin.com/in/career-changer/"

    row1 = ["Career", "Changer", url, "cc@example.com", "Old Corp", "Junior Dev", "01 Jan 2024"]
    row2 = ["Career", "Changer", url, "cc@example.com", "New Corp", "Senior Dev", "01 Jan 2024"]
    import_csv(_make_csv(row1), session)
    import_csv(_make_csv(row2), session)

    positions = list(session.exec(select(Position)).all())
    old_pos = next((p for p in positions if not p.is_current), None)
    assert old_pos is not None
    assert old_pos.title == "Junior Dev"
