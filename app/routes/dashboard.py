from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.plan import StudyPlan
from app.models.user import User

router = APIRouter()


class DashboardResponse(BaseModel):
    total_plans: int
    total_tasks: int
    completed_tasks: int
    remaining_tasks: int
    overall_progress_percentage: float
    current_streak_days: int
    nearest_exam_days: Optional[int]


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plans = (
        db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).all()
    )

    all_tasks = [task for plan in plans for task in plan.tasks]
    total_tasks = len(all_tasks)
    completed_tasks = sum(1 for t in all_tasks if t.is_completed)
    remaining_tasks = total_tasks - completed_tasks
    progress = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0.0

    # Streak: count consecutive days (ending today) where at least one task was completed
    streak = 0
    check_date = datetime.utcnow().date()
    while True:
        completed_on_day = any(
            t.completed_at and t.completed_at.date() == check_date
            for t in all_tasks
        )
        if completed_on_day:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Nearest upcoming exam
    now = datetime.utcnow()
    upcoming_plans = [p for p in plans if p.exam_date > now]
    nearest_exam_days: Optional[int] = None
    if upcoming_plans:
        nearest = min(upcoming_plans, key=lambda p: p.exam_date)
        nearest_exam_days = (nearest.exam_date - now).days

    return DashboardResponse(
        total_plans=len(plans),
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        remaining_tasks=remaining_tasks,
        overall_progress_percentage=progress,
        current_streak_days=streak,
        nearest_exam_days=nearest_exam_days,
    )
