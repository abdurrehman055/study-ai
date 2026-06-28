import enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator

from app.schemas.task import TaskResponse


class Difficulty(str, enum.Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class PlanCreate(BaseModel):
    subjects: List[str]
    exam_date: datetime
    daily_study_hours: float
    difficulty: Difficulty

    @field_validator("exam_date")
    @classmethod
    def exam_date_must_be_future(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        aware_v = v if v.tzinfo is not None else v.replace(tzinfo=timezone.utc)
        if aware_v <= now:
            raise ValueError("Exam date must be in the future")
        return v

    @field_validator("daily_study_hours")
    @classmethod
    def study_hours_range(cls, v: float) -> float:
        if not (1 <= v <= 16):
            raise ValueError("Daily study hours must be between 1 and 16")
        return v

    @field_validator("subjects")
    @classmethod
    def subjects_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Subjects list cannot be empty")
        cleaned = [s.strip() for s in v if s.strip()]
        if not cleaned:
            raise ValueError("Subjects list cannot contain only empty strings")
        return cleaned


class PlanResponse(BaseModel):
    id: int
    user_id: int
    subjects: List[str]
    exam_date: datetime
    daily_study_hours: float
    difficulty: Difficulty
    ai_explanation: Optional[str]
    study_tips: Optional[str]
    created_at: datetime
    updated_at: datetime
    tasks: List[TaskResponse] = []

    model_config = {"from_attributes": True}


class PlanProgressResponse(BaseModel):
    plan_id: int
    total_tasks: int
    completed_tasks: int
    remaining_tasks: int
    progress_percentage: float
    days_until_exam: int
