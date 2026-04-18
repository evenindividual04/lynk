from src.lynk.services.tracking import PIXEL_PNG, hash_ip, inject_pixel, wrap_links


def test_pixel_png_is_valid():
    assert PIXEL_PNG[:4] == b"\x89PNG"
    assert len(PIXEL_PNG) > 0


def test_wrap_links_basic():
    body = '<p>Click <a href="https://example.com">here</a>.</p>'
    modified, links = wrap_links(body, "abc123", "http://localhost:8000")
    assert "https://example.com" not in modified
    assert "/t/click/abc123/0" in modified
    assert len(links) == 1
    assert links[0].original_url == "https://example.com"
    assert links[0].idx == 0


def test_wrap_links_skips_anchors():
    body = '<a href="#section">anchor</a>'
    modified, links = wrap_links(body, "abc123", "http://localhost:8000")
    assert "#section" in modified
    assert len(links) == 0


def test_wrap_links_skips_mailto():
    body = '<a href="mailto:foo@bar.com">email</a>'
    modified, links = wrap_links(body, "abc123", "http://localhost:8000")
    assert "mailto:" in modified
    assert len(links) == 0


def test_inject_pixel():
    body = "<p>Hello</p>"
    modified = inject_pixel(body, "track-id", "http://localhost:8000")
    assert "/t/pixel/track-id.png" in modified
    assert "display:none" in modified


def test_hash_ip_consistent():
    h1 = hash_ip("192.168.1.1")
    h2 = hash_ip("192.168.1.1")
    assert h1 == h2
    assert h1 is not None
    assert len(h1) == 16


def test_hash_ip_none():
    assert hash_ip(None) is None
