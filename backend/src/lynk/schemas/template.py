from __future__ import annotations

from datetime import datetime

from sqlmodel import SQLModel

from ..models.template import Channel, Scenario


class TemplateVersionRead(SQLModel):
    id: int
    template_id: int
    version: int
    subject_template: str | None
    body_template: str
    notes: str | None
    created_at: datetime


class TemplateRead(SQLModel):
    id: int
    name: str
    scenario: Scenario
    channel: Channel
    active_version_id: int | None
    created_at: datetime
    updated_at: datetime


class TemplateDetail(TemplateRead):
    versions: list[TemplateVersionRead] = []


class TemplateCreate(SQLModel):
    name: str
    scenario: Scenario
    channel: Channel
    body_template: str
    subject_template: str | None = None
    notes: str | None = None


class TemplateVersionCreate(SQLModel):
    body_template: str
    subject_template: str | None = None
    notes: str | None = None


class TemplateUpdate(SQLModel):
    active_version_id: int | None = None
    name: str | None = None
