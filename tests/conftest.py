"""
Test configuration.

Requirements:
- PostgreSQL must be running.
- Set TEST_DATABASE_URL in your environment, or create a 'study_planner_test' database
  using the default credentials (postgres/password on localhost:5432).
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/study_planner_test",
)

from app.database.session import Base, get_db  # noqa: E402
from main import app  # noqa: E402

test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(create_tables):
    """Each test runs inside a transaction that is rolled back on teardown."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Shared helpers ────────────────────────────────────────────────────────────

def register_user(client, email: str = "test@example.com", password: str = "password123"):
    return client.post("/auth/register", json={
        "name": "Test User",
        "email": email,
        "password": password,
        "preferred_study_time": "Morning",
    })


def get_auth_headers(client, email: str = "test@example.com", password: str = "password123") -> dict:
    res = client.post("/auth/login", json={"email": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
