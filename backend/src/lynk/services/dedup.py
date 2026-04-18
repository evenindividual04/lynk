import re
from urllib.parse import urlparse, urlunparse


def normalize_linkedin_url(raw_url: str) -> str:
    """Normalize a LinkedIn profile URL to a canonical form.

    Canonical form: https://www.linkedin.com/in/<slug>/
    - Lowercase
    - Strip query params and fragments
    - Ensure www. prefix
    - Ensure trailing slash
    - Reject non-/in/ paths
    """
    url = raw_url.strip().lower()

    # Handle bare slugs like "john-doe"
    if not url.startswith("http"):
        url = f"https://www.linkedin.com/in/{url}/"

    parsed = urlparse(url)

    # Normalize host
    host = parsed.netloc
    if not host.startswith("www."):
        host = "www." + host.lstrip("m.")

    path = parsed.path
    if not path.endswith("/"):
        path = path + "/"

    # Only /in/ profiles are valid person URLs
    if not re.match(r"^/in/[^/]+/$", path):
        raise ValueError(f"Not a LinkedIn /in/ profile URL: {raw_url!r}")

    normalized = urlunparse(("https", host, path, "", "", ""))
    return normalized


def is_duplicate(url_a: str, url_b: str) -> bool:
    return normalize_linkedin_url(url_a) == normalize_linkedin_url(url_b)
