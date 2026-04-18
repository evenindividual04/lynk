import pytest

from src.lynk.services.dedup import is_duplicate, normalize_linkedin_url


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://www.linkedin.com/in/john-doe", "https://www.linkedin.com/in/john-doe/"),
        ("https://www.linkedin.com/in/john-doe/", "https://www.linkedin.com/in/john-doe/"),
        ("http://linkedin.com/in/john-doe", "https://www.linkedin.com/in/john-doe/"),
        ("https://LINKEDIN.COM/in/John-Doe/", "https://www.linkedin.com/in/john-doe/"),
        ("https://www.linkedin.com/in/john-doe?utm_source=share", "https://www.linkedin.com/in/john-doe/"),
        ("https://www.linkedin.com/in/john-doe/#about", "https://www.linkedin.com/in/john-doe/"),
        ("john-doe", "https://www.linkedin.com/in/john-doe/"),
    ],
)
def test_normalize(raw, expected):
    assert normalize_linkedin_url(raw) == expected


def test_normalize_invalid_path():
    with pytest.raises(ValueError):
        normalize_linkedin_url("https://www.linkedin.com/company/acme")


def test_is_duplicate():
    assert is_duplicate(
        "https://www.linkedin.com/in/alice",
        "http://linkedin.com/in/Alice/",
    )


def test_not_duplicate():
    assert not is_duplicate(
        "https://www.linkedin.com/in/alice",
        "https://www.linkedin.com/in/bob",
    )
