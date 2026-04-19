from unittest.mock import MagicMock, patch

from src.lynk.services.email_verifier import verify_smtp, verify_syntax


def test_verify_syntax_valid():
    assert verify_syntax("user@example.com") is True


def test_verify_syntax_invalid():
    assert verify_syntax("not-an-email") is False
    assert verify_syntax("@nodomain") is False


def test_verify_smtp_returns_true_on_catch_all():
    import dns.resolver as _resolver

    with patch.object(_resolver, "resolve", side_effect=Exception("nxdomain")):
        ok, reason = verify_smtp("user@example.com")
    assert ok is True


def _make_dns_mock(rcpt_code: int, rcpt_msg: bytes):
    import dns.resolver as _resolver

    mock_mx = MagicMock()
    mock_mx.preference = 10
    mock_mx.exchange = MagicMock()
    mock_mx.exchange.__str__ = lambda self: "mail.example.com."

    mock_smtp = MagicMock()
    mock_smtp.__enter__ = lambda s: s
    mock_smtp.__exit__ = MagicMock(return_value=False)
    mock_smtp.rcpt.return_value = (rcpt_code, rcpt_msg)

    return _resolver, [mock_mx], mock_smtp


def test_verify_smtp_rejects_on_5xx():
    _resolver, mx_list, mock_smtp = _make_dns_mock(550, b"User unknown")
    with (
        patch.object(_resolver, "resolve", return_value=mx_list),
        patch("src.lynk.services.email_verifier.smtplib.SMTP", return_value=mock_smtp),
    ):
        ok, reason = verify_smtp("bad@example.com")

    assert ok is False
    assert "550" in reason


def test_verify_smtp_passes_on_250():
    _resolver, mx_list, mock_smtp = _make_dns_mock(250, b"OK")
    with (
        patch.object(_resolver, "resolve", return_value=mx_list),
        patch("src.lynk.services.email_verifier.smtplib.SMTP", return_value=mock_smtp),
    ):
        ok, reason = verify_smtp("good@example.com")

    assert ok is True
