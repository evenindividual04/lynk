from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ...models.template import Channel, Scenario, Template, TemplateVersion
from ...schemas.template import (
    TemplateCreate,
    TemplateDetail,
    TemplateRead,
    TemplateUpdate,
    TemplateVersionCreate,
    TemplateVersionRead,
)
from ..deps import SessionDep

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateRead])
def list_templates(
    session: SessionDep,
    scenario: Scenario | None = None,
    channel: Channel | None = None,
) -> list[Template]:
    stmt = select(Template)
    if scenario:
        stmt = stmt.where(Template.scenario == scenario)
    if channel:
        stmt = stmt.where(Template.channel == channel)
    stmt = stmt.order_by(Template.name)  # type: ignore[arg-type]
    return list(session.exec(stmt).all())


@router.post("", response_model=TemplateRead, status_code=201)
def create_template(data: TemplateCreate, session: SessionDep) -> Template:
    template = Template(
        name=data.name,
        scenario=data.scenario,
        channel=data.channel,
    )
    session.add(template)
    session.flush()

    version = TemplateVersion(
        template_id=template.id,  # type: ignore[arg-type]
        version=1,
        body_template=data.body_template,
        subject_template=data.subject_template,
        notes=data.notes,
    )
    session.add(version)
    session.flush()

    template.active_version_id = version.id
    template.updated_at = datetime.utcnow()
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateDetail)
def get_template(template_id: int, session: SessionDep) -> TemplateDetail:
    template = session.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    versions = list(
        session.exec(
            select(TemplateVersion).where(TemplateVersion.template_id == template_id).order_by(TemplateVersion.version)  # type: ignore[arg-type]
        ).all()
    )
    return TemplateDetail(
        **template.model_dump(),
        versions=[TemplateVersionRead.model_validate(v.model_dump()) for v in versions],
    )


@router.post("/{template_id}/versions", response_model=TemplateVersionRead, status_code=201)
def add_version(template_id: int, data: TemplateVersionCreate, session: SessionDep) -> TemplateVersion:
    template = session.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    last = session.exec(
        select(TemplateVersion)
        .where(TemplateVersion.template_id == template_id)
        .order_by(TemplateVersion.version.desc())  # type: ignore[attr-defined]
    ).first()
    next_version = (last.version + 1) if last else 1

    version = TemplateVersion(
        template_id=template_id,
        version=next_version,
        body_template=data.body_template,
        subject_template=data.subject_template,
        notes=data.notes,
    )
    session.add(version)
    session.flush()

    template.active_version_id = version.id
    template.updated_at = datetime.utcnow()
    session.add(template)
    session.commit()
    session.refresh(version)
    return version


@router.patch("/{template_id}", response_model=TemplateRead)
def update_template(template_id: int, data: TemplateUpdate, session: SessionDep) -> Template:
    template = session.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if data.active_version_id is not None:
        template.active_version_id = data.active_version_id
    if data.name is not None:
        template.name = data.name
    template.updated_at = datetime.utcnow()
    session.add(template)
    session.commit()
    session.refresh(template)
    return template
