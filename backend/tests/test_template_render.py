import pytest

from src.lynk.services.template_render import render_template


def test_basic_substitution():
    result = render_template(
        "Hi {{ person.first_name }}, you work at {{ company.name }}.",
        {"first_name": "Alice", "last_name": "Smith"},
        {"name": "Acme Corp"},
    )
    assert result == "Hi Alice, you work at Acme Corp."


def test_missing_variable_is_empty():
    result = render_template(
        "Hi {{ person.first_name }}, role: {{ person.current_position }}.",
        {"first_name": "Bob"},
    )
    assert "Bob" in result
    assert "{{ " not in result  # placeholders resolved


def test_no_code_execution():
    """Jinja sandbox should block arbitrary code execution."""
    with pytest.raises(Exception):
        render_template("{{ ''.__class__.__mro__[1].__subclasses__() }}", {})


def test_empty_company():
    result = render_template("Hello {{ person.full_name }}!", {"full_name": "Jane Doe"})
    assert result == "Hello Jane Doe!"
