"""Generates a Faker-based sample LinkedIn CSV for tests."""
import csv
import io
from faker import Faker

fake = Faker()

HEADER = ["First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"]
SAMPLE_CSV_HEADER = ",".join(HEADER) + "\n"


def _make_row(
    first: str | None = None,
    last: str | None = None,
    url: str | None = None,
    email: str | None = None,
    company: str | None = None,
    position: str | None = None,
    connected_on: str | None = None,
) -> list[str]:
    return [
        first or fake.first_name(),
        last or fake.last_name(),
        url or f"https://www.linkedin.com/in/{fake.user_name()}/",
        email or fake.email(),
        company or fake.company(),
        position or fake.job(),
        connected_on or fake.date_between(start_date="-5y").strftime("%d %b %Y"),
    ]


def make_csv_row(**kwargs: str | None) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_make_row(**kwargs))
    return buf.getvalue()


def make_sample_csv(rows: int = 5) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(HEADER)
    for _ in range(rows):
        writer.writerow(_make_row())
    return buf.getvalue().encode()


def make_linkedin_csv_with_notes(rows: int = 3) -> bytes:
    """Simulates LinkedIn's export format with 3 blank/notes lines before header."""
    buf = io.StringIO()
    buf.write("Notes exported from LinkedIn\n\n\n")
    writer = csv.writer(buf)
    writer.writerow(HEADER)
    for _ in range(rows):
        writer.writerow(_make_row())
    return buf.getvalue().encode("utf-8-sig")  # LinkedIn exports with BOM
