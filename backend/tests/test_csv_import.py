from tests.fixtures.sample_csv import make_linkedin_csv_with_notes, make_sample_csv

from src.lynk.services.csv_import import import_csv
from src.lynk.models.person import Source


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
    csv1 = make_sample_csv(0)
    # Make a single-row CSV with a known URL
    import io, csv as csv_mod
    buf = io.StringIO()
    w = csv_mod.writer(buf)
    w.writerow(["First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"])
    w.writerow(["Alice", "Smith", url, "alice@example.com", "Acme", "Engineer", "01 Jan 2024"])
    csv1 = buf.getvalue().encode()

    result1 = import_csv(csv1, session)
    assert result1.imported == 1

    # Re-import the same person
    result2 = import_csv(csv1, session)
    assert result2.imported == 0
    assert result2.merged == 1


def test_import_url_normalization(session):
    """Different URL variants for the same person should deduplicate."""
    import io, csv as csv_mod

    def make_one(url: str, first: str = "Alice", last: str = "Smith") -> bytes:
        buf = io.StringIO()
        w = csv_mod.writer(buf)
        w.writerow(["First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"])
        w.writerow([first, last, url, f"{first.lower()}@example.com", "Acme", "Engineer", "01 Jan 2024"])
        return buf.getvalue().encode()

    csv1 = make_one("https://www.linkedin.com/in/test-person/")
    csv2 = make_one("http://LinkedIn.COM/in/Test-Person?utm_source=share")

    result1 = import_csv(csv1, session)
    result2 = import_csv(csv2, session)
    assert result1.imported == 1
    assert result2.merged == 1


def test_import_marks_source_as_csv(session):
    from sqlmodel import select
    from src.lynk.models.person import Person

    csv_bytes = make_sample_csv(1)
    import_csv(csv_bytes, session)
    people = list(session.exec(select(Person)).all())
    assert all(p.source == Source.csv_import for p in people)


def test_import_skips_missing_url(session):
    import io, csv as csv_mod
    buf = io.StringIO()
    w = csv_mod.writer(buf)
    w.writerow(["First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"])
    w.writerow(["Alice", "Smith", "", "alice@example.com", "Acme", "Engineer", "01 Jan 2024"])
    csv_bytes = buf.getvalue().encode()
    result = import_csv(csv_bytes, session)
    assert result.skipped == 1


def test_import_position_history_on_merge(session):
    """When a person is re-imported with a new job, the old one becomes history."""
    import io, csv as csv_mod
    from sqlmodel import select
    from src.lynk.models.person import Position

    url = "https://www.linkedin.com/in/career-changer/"

    def make_one(company: str, position: str) -> bytes:
        buf = io.StringIO()
        w = csv_mod.writer(buf)
        w.writerow(["First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"])
        w.writerow(["Career", "Changer", url, "cc@example.com", company, position, "01 Jan 2024"])
        return buf.getvalue().encode()

    import_csv(make_one("Old Corp", "Junior Dev"), session)
    import_csv(make_one("New Corp", "Senior Dev"), session)

    positions = list(session.exec(select(Position)).all())
    old_pos = next((p for p in positions if not p.is_current), None)
    assert old_pos is not None
    assert old_pos.title == "Junior Dev"
