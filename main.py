from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import auth, plans, tasks, dashboard, health, pages
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Study Planner API starting up")
    yield
    logger.info("AI Study Planner API shutting down")


app = FastAPI(
    title="AI Study Planner API",
    description="AI-powered study plan generation and daily task management",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Pages first so "/" doesn't conflict with API routes
app.include_router(pages.router, tags=["UI"])
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(plans.router, prefix="/plans", tags=["Study Plans"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(dashboard.router, tags=["Dashboard"])
