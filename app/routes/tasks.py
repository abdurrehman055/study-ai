from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.plan import StudyPlan
from app.models.task import StudyTask
from app.models.user import User
from app.schemas.task import TaskResponse
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _get_user_task(task_id: int, user: User, db: Session) -> StudyTask:
    task = (
        db.query(StudyTask)
        .join(StudyPlan, StudyTask.plan_id == StudyPlan.id)
        .filter(StudyTask.id == task_id, StudyPlan.user_id == user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}/complete", response_model=TaskResponse)
def mark_complete(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_user_task(task_id, current_user, db)
    task.is_completed = True
    task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    logger.info(f"Task {task_id} marked complete by user {current_user.id}")
    return task


@router.patch("/{task_id}/incomplete", response_model=TaskResponse)
def mark_incomplete(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_user_task(task_id, current_user, db)
    task.is_completed = False
    task.completed_at = None
    db.commit()
    db.refresh(task)
    logger.info(f"Task {task_id} marked incomplete by user {current_user.id}")
    return task
