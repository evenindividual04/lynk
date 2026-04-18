from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ...models.follow_up import FollowUpStatus, FollowUpTask
from ...schemas.follow_up import FollowUpTaskRead
from ..deps import SessionDep

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


@router.get("", response_model=list[FollowUpTaskRead])
def list_follow_ups(
    session: SessionDep,
    person_id: int | None = None,
    status: FollowUpStatus | None = None,
) -> list[FollowUpTask]:
    stmt = select(FollowUpTask)
    if person_id is not None:
        stmt = stmt.where(FollowUpTask.person_id == person_id)
    if status is not None:
        stmt = stmt.where(FollowUpTask.status == status)
    stmt = stmt.order_by(FollowUpTask.scheduled_for)  # type: ignore[arg-type]
    return list(session.exec(stmt).all())


@router.post("/{task_id}/cancel", response_model=FollowUpTaskRead)
def cancel_follow_up(task_id: int, session: SessionDep) -> FollowUpTask:
    task = session.get(FollowUpTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    if task.status != FollowUpStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending tasks can be cancelled")
    task.status = FollowUpStatus.cancelled
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.post("/{task_id}/trigger-now", response_model=FollowUpTaskRead)
def trigger_follow_up(task_id: int, session: SessionDep) -> FollowUpTask:
    """Manually trigger a pending follow-up task right now."""
    task = session.get(FollowUpTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    if task.status != FollowUpStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending tasks can be triggered")

    from ...services.scheduler import _generate_follow_up

    _generate_follow_up(session, task)
    task.status = FollowUpStatus.completed
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
