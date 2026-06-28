from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TaskResponse(BaseModel):
    id: int
    plan_id: int
    date: datetime
    subject: str
    description: str
    duration_hours: float
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
