from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.database.session import get_db

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy",
        database=db_status,
        version="1.0.0",
    )
