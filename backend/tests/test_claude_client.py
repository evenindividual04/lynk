from unittest.mock import MagicMock, patch

import pytest

from src.lynk.models.person import Person, Source, Stage
from src.lynk.models.template import Channel, TemplateVersion
from src.lynk.services import claude_client


def _make_person(priority: int = 0) -> Person:
    return Person(
        id=1,
        linkedin_url="https://www.linkedin.com/in/test/",
        full_name="Alice Smith",
        first_name="Alice",
        last_name="Smith",
        priority=priority,
        stage=Stage.not_contacted,
        source=Source.manual,
    )


def _make_tv() -> TemplateVersion:
    return TemplateVersion(
        id=1,
        template_id=1,
        version=1,
        body_template="Hi {{ person.first_name }}, interested in your work.",
    )


def _mock_response(text: str) -> MagicMock:
    content = MagicMock()
    content.text = text
    response = MagicMock()
    response.content = [content]
    return response


def test_uses_haiku_for_normal_priority(monkeypatch):
    monkeypatch.setattr(claude_client.settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(claude_client.settings, "claude_model_default", "claude-haiku-4-5-20251001")

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = _mock_response('{"subject": null, "body": "Hi Alice"}')

        result = claude_client.generate_message(
            person=_make_person(priority=0),
            template_version=_make_tv(),
            scenario_context="ps_outreach",
            channel=Channel.li_dm,
        )
        call_kwargs = instance.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-haiku-4-5-20251001"
        assert result["body"] == "Hi Alice"
        assert result["subject"] is None


def test_uses_sonnet_for_high_priority(monkeypatch):
    monkeypatch.setattr(claude_client.settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(claude_client.settings, "claude_model_high_priority", "claude-sonnet-4-6")

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = _mock_response('{"subject": null, "body": "Hi"}')

        claude_client.generate_message(
            person=_make_person(priority=2),
            template_version=_make_tv(),
            scenario_context="research_gsoc",
            channel=Channel.li_dm,
        )
        call_kwargs = instance.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-6"


def test_prompt_caching_in_system(monkeypatch):
    """System prompt should include cache_control block."""
    monkeypatch.setattr(claude_client.settings, "anthropic_api_key", "test-key")

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = _mock_response('{"subject": null, "body": "x"}')

        claude_client.generate_message(
            person=_make_person(),
            template_version=_make_tv(),
            scenario_context="alumni",
            channel=Channel.li_dm,
        )
        call_kwargs = instance.messages.create.call_args
        system = call_kwargs.kwargs["system"]
        assert isinstance(system, list)
        assert system[0].get("cache_control") == {"type": "ephemeral"}


def test_li_note_truncated_at_300(monkeypatch):
    monkeypatch.setattr(claude_client.settings, "anthropic_api_key", "test-key")
    long_body = "A" * 350

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = _mock_response(f'{{"subject": null, "body": "{long_body}"}}')

        result = claude_client.generate_message(
            person=_make_person(),
            template_version=_make_tv(),
            scenario_context="founder",
            channel=Channel.li_connection_note,
        )
        assert len(result["body"]) <= 300


def test_raises_without_api_key(monkeypatch):
    monkeypatch.setattr(claude_client.settings, "anthropic_api_key", "")
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        claude_client.generate_message(
            person=_make_person(),
            template_version=_make_tv(),
            scenario_context="ps_outreach",
            channel=Channel.cold_email,
        )
