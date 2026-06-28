import enum
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.database.session import Base


class StudyTimePreference(str, enum.Enum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    NIGHT = "Night"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    preferred_study_time = Column(
        Enum(StudyTimePreference, values_callable=lambda obj: [e.value for e in obj]),
        default=StudyTimePreference.MORNING,
        nullable=False,
    )

    plans = relationship("StudyPlan", back_populates="owner", cascade="all, delete-orphan")
