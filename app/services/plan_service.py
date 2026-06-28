from datetime import datetime
from sqlalchemy.orm import Session

from app.models.plan import StudyPlan
from app.models.task import StudyTask
from app.models.user import User
from app.services.ai_service import generate_study_plan
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _build_tasks_from_ai(db: Session, plan: StudyPlan, ai_result: dict) -> None:
    plan.ai_explanation = ai_result.get("explanation", "")
    plan.study_tips = ai_result.get("study_tips", "")

    for task_data in ai_result.get("daily_tasks", []):
        task = StudyTask(
            plan_id=plan.id,
            date=datetime.strptime(task_data["date"], "%Y-%m-%d"),
            subject=task_data["subject"],
            description=task_data["description"],
            duration_hours=float(task_data["duration_hours"]),
        )
        db.add(task)


def create_plan_with_tasks(db: Session, plan: StudyPlan, user: User) -> StudyPlan:
    ai_result = generate_study_plan(
        subjects=plan.subjects,
        exam_date=plan.exam_date,
        daily_study_hours=plan.daily_study_hours,
        difficulty=plan.difficulty.value,
        preferred_study_time=user.preferred_study_time.value,
    )

    _build_tasks_from_ai(db, plan, ai_result)
    db.commit()
    db.refresh(plan)

    logger.info(f"Plan {plan.id} created with {len(plan.tasks)} tasks for user {user.id}")
    return plan


def regenerate_plan(db: Session, plan: StudyPlan, user: User) -> StudyPlan:
    db.query(StudyTask).filter(StudyTask.plan_id == plan.id).delete()
    plan.updated_at = datetime.utcnow()
    db.flush()

    ai_result = generate_study_plan(
        subjects=plan.subjects,
        exam_date=plan.exam_date,
        daily_study_hours=plan.daily_study_hours,
        difficulty=plan.difficulty.value,
        preferred_study_time=user.preferred_study_time.value,
    )

    _build_tasks_from_ai(db, plan, ai_result)
    db.commit()
    db.refresh(plan)

    logger.info(f"Plan {plan.id} regenerated with {len(plan.tasks)} tasks for user {user.id}")
    return plan
