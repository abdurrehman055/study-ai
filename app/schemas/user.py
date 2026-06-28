import enum
from pydantic import BaseModel, EmailStr, field_validator


class StudyTimePreference(str, enum.Enum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    NIGHT = "Night"


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    preferred_study_time: StudyTimePreference = StudyTimePreference.MORNING

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    preferred_study_time: StudyTimePreference

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
