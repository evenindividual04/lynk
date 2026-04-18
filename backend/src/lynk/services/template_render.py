from __future__ import annotations

from collections.abc import Iterator

from jinja2 import Undefined
from jinja2.sandbox import SandboxedEnvironment


class _SilentUndefined(Undefined):
    """Renders as empty string for missing template variables."""

    def __str__(self) -> str:
        return ""

    def __iter__(self) -> Iterator[object]:  # type: ignore[override]
        return iter([])

    def __bool__(self) -> bool:
        return False


_env = SandboxedEnvironment(
    variable_start_string="{{",
    variable_end_string="}}",
    undefined=_SilentUndefined,
)


def render_template(
    template_str: str,
    person_data: dict[str, str | None],
    company_data: dict[str, str | None] | None = None,
) -> str:
    """
    Render a Jinja2 template string with person and company data.
    Missing variables silently become empty strings.
    Used for preview and as Claude fallback.
    """
    context = {
        "person": person_data,
        "company": company_data or {},
    }
    tmpl = _env.from_string(template_str)
    return tmpl.render(**context)
