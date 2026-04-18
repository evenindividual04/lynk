import io

from tests.fixtures.sample_csv import make_linkedin_csv_with_notes, make_sample_csv


def test_import_csv_basic(client):
    csv_bytes = make_sample_csv(3)
    resp = client.post(
        "/api/imports",
        files={"file": ("connections.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 3
    assert data["merged"] == 0
    assert data["errors"] == []


def test_import_csv_with_linkedin_format(client):
    csv_bytes = make_linkedin_csv_with_notes(5)
    resp = client.post(
        "/api/imports",
        files={"file": ("connections.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 200
    assert resp.json()["imported"] == 5


def test_import_csv_dedup(client):
    csv_bytes = make_sample_csv(2)

    resp1 = client.post(
        "/api/imports",
        files={"file": ("connections.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp1.json()["imported"] == 2

    resp2 = client.post(
        "/api/imports",
        files={"file": ("connections.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp2.json()["imported"] == 0
    assert resp2.json()["merged"] == 2


def test_import_errors_capped_at_10(client):
    """Errors list returned should be capped at 10."""
    bad_rows = "".join(f"P{i},L{i},not-a-linkedin-url-{i},,,\n" for i in range(20))
    header = "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
    csv_bytes = (header + bad_rows).encode()
    resp = client.post(
        "/api/imports",
        files={"file": ("connections.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 200
    assert len(resp.json()["errors"]) <= 10
