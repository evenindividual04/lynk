from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel, UniqueConstraint


class Scenario(StrEnum):
    ps_outreach = "ps_outreach"
    research_gsoc = "research_gsoc"
    referral_request = "referral_request"
    info_call = "info_call"
    alumni = "alumni"
    founder = "founder"


class Channel(StrEnum):
    li_connection_note = "li_connection_note"
    li_dm = "li_dm"
    cold_email = "cold_email"


class Template(SQLModel, table=True):
    __tablename__ = "template"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    scenario: Scenario
    channel: Channel
    active_version_id: int | None = Field(default=None, foreign_key="template_version.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TemplateVersion(SQLModel, table=True):
    __tablename__ = "template_version"

    __table_args__ = (UniqueConstraint("template_id", "version"),)

    id: int | None = Field(default=None, primary_key=True)
    template_id: int = Field(foreign_key="template.id", index=True)
    version: int = Field(default=1)
    subject_template: str | None = None  # only for cold_email channel
    body_template: str  # Jinja2 placeholders: {{ person.full_name }}, {{ company.name }}
    notes: str | None = None  # change notes for this version
    created_at: datetime = Field(default_factory=datetime.utcnow)
