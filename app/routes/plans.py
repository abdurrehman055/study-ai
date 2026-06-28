from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.plan import StudyPlan
from app.models.task import StudyTask
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanResponse, PlanProgressResponse
from app.services.plan_service import create_plan_with_tasks, regenerate_plan
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _get_user_plan(plan_id: int, user: User, db: Session) -> StudyPlan:
    plan = (
        db.query(StudyPlan)
        .filter(StudyPlan.id == plan_id, StudyPlan.user_id == user.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router.post("/generate", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def generate_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = StudyPlan(
        user_id=current_user.id,
        subjects=payload.subjects,
        exam_date=payload.exam_date,
        daily_study_hours=payload.daily_study_hours,
        difficulty=payload.difficulty,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    logger.info(f"Generating plan for user {current_user.id}, subjects={payload.subjects}")
    return create_plan_with_tasks(db, plan, current_user)


@router.post("/{plan_id}/regenerate", response_model=PlanResponse)
def regenerate_study_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = _get_user_plan(plan_id, current_user, db)
    logger.info(f"Regenerating plan {plan_id} for user {current_user.id}")
    return regenerate_plan(db, plan, current_user)


@router.get("/", response_model=List[PlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(StudyPlan)
        .filter(StudyPlan.user_id == current_user.id)
        .order_by(StudyPlan.created_at.desc())
        .all()
    )


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_user_plan(plan_id, current_user, db)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = _get_user_plan(plan_id, current_user, db)
    db.delete(plan)
    db.commit()
    logger.info(f"Plan {plan_id} deleted by user {current_user.id}")


@router.get("/{plan_id}/progress", response_model=PlanProgressResponse)
def get_plan_progress(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = _get_user_plan(plan_id, current_user, db)

    total = len(plan.tasks)
    completed = sum(1 for t in plan.tasks if t.is_completed)
    remaining = total - completed
    progress_pct = round((completed / total * 100), 2) if total > 0 else 0.0
    days_until_exam = max(0, (plan.exam_date - datetime.utcnow()).days)

    return PlanProgressResponse(
        plan_id=plan_id,
        total_tasks=total,
        completed_tasks=completed,
        remaining_tasks=remaining,
        progress_percentage=progress_pct,
        days_until_exam=days_until_exam,
    )
