import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String
from sqlalchemy.orm import relationship
from app.database.session import Base


class Difficulty(str, enum.Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subjects = Column(ARRAY(String), nullable=False)
    exam_date = Column(DateTime, nullable=False)
    daily_study_hours = Column(Float, nullable=False)
    difficulty = Column(Enum(Difficulty, values_callable=lambda e: [m.value for m in e]), nullable=False)
    ai_explanation = Column(Text, nullable=True)
    study_tips = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="plans")
    tasks = relationship("StudyTask", back_populates="plan", cascade="all, delete-orphan", order_by="StudyTask.date")
