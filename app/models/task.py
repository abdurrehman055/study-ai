from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


class StudyTask(Base):
    __tablename__ = "study_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    subject = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    duration_hours = Column(Float, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    plan = relationship("StudyPlan", back_populates="tasks")
