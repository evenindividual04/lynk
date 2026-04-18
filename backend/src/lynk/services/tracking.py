from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

# 1x1 transparent PNG (constant, no external dependency)
PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@dataclass
class WrappedLink:
    idx: int
    original_url: str
    wrapped_url: str


def wrap_links(body: str, tracking_id: str, base_url: str) -> tuple[str, list[WrappedLink]]:
    """
    Replace all <a href="URL"> in body with tracking redirect URLs.
    Returns (modified_body, list_of_wrapped_links).
    """
    wrapped: list[WrappedLink] = []
    idx = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal idx
        original_url = match.group(1)
        # Skip anchor fragments and mailto
        if original_url.startswith("#") or original_url.startswith("mailto:"):
            return match.group(0)
        from urllib.parse import quote

        wrapped_url = f"{base_url}/t/click/{tracking_id}/{idx}?url={quote(original_url, safe='')}"
        wrapped.append(WrappedLink(idx=idx, original_url=original_url, wrapped_url=wrapped_url))
        idx += 1
        return f'<a href="{wrapped_url}"'

    modified = re.sub(r'<a\s+href="([^"]+)"', replace, body)
    return modified, wrapped


def inject_pixel(body: str, tracking_id: str, base_url: str) -> str:
    """Append a 1x1 tracking pixel to an HTML email body."""
    pixel_tag = f'<img src="{base_url}/t/pixel/{tracking_id}.png" width="1" height="1" style="display:none" alt="" />'
    return body + "\n" + pixel_tag


def hash_ip(ip: str | None) -> str | None:
    """One-way hash of IP for privacy-preserving storage."""
    if not ip:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()[:16]
