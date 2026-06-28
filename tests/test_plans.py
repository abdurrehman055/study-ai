import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import register_user, get_auth_headers


FUTURE_DATE = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
PAST_DATE = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")

MOCK_AI_RESULT = {
    "explanation": "Balanced plan covering all subjects evenly.",
    "study_tips": "Take a 5-minute break every 25 minutes.\nReview notes before each session.",
    "daily_tasks": [
        {
            "date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "subject": "Math",
            "description": "Review Chapter 1: Algebra fundamentals, solve 10 practice problems",
            "duration_hours": 2.0,
        },
        {
            "date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "subject": "Physics",
            "description": "Read Chapter 2: Newton's Laws, complete end-of-chapter exercises",
            "duration_hours": 2.0,
        },
    ],
}

VALID_PLAN_PAYLOAD = {
    "subjects": ["Math", "Physics"],
    "exam_date": FUTURE_DATE,
    "daily_study_hours": 4,
    "difficulty": "Medium",
}


def mock_ai_client():
    mock = MagicMock()
    mock.chat.completions.create.return_value.choices[0].message.content = json.dumps(MOCK_AI_RESULT)
    return mock


@pytest.fixture
def auth(client):
    register_user(client)
    return get_auth_headers(client)


class TestGeneratePlan:
    @patch("app.services.ai_service._get_client")
    def test_generate_plan_success(self, mock_get_client, client, auth):
        mock_get_client.return_value = mock_ai_client()

        res = client.post("/plans/generate", json=VALID_PLAN_PAYLOAD, headers=auth)
        assert res.status_code == 201
        body = res.json()
        assert body["subjects"] == ["Math", "Physics"]
        assert body["difficulty"] == "Medium"
        assert body["ai_explanation"] == MOCK_AI_RESULT["explanation"]
        assert len(body["tasks"]) == 2

    @patch("app.services.ai_service._get_client")
    def test_generate_plan_tasks_are_ordered_by_date(self, mock_get_client, client, auth):
        mock_get_client.return_value = mock_ai_client()
        res = client.post("/plans/generate", json=VALID_PLAN_PAYLOAD, headers=auth)
        tasks = res.json()["tasks"]
        dates = [t["date"] for t in tasks]
        assert dates == sorted(dates)

    def test_generate_plan_past_exam_date(self, client, auth):
        payload = {**VALID_PLAN_PAYLOAD, "exam_date": PAST_DATE}
        res = client.post("/plans/generate", json=payload, headers=auth)
        assert res.status_code == 422

    def test_generate_plan_zero_study_hours(self, client, auth):
        payload = {**VALID_PLAN_PAYLOAD, "daily_study_hours": 0}
        res = client.post("/plans/generate", json=payload, headers=auth)
        assert res.status_code == 422

    def test_generate_plan_too_many_study_hours(self, client, auth):
        payload = {**VALID_PLAN_PAYLOAD, "daily_study_hours": 17}
        res = client.post("/plans/generate", json=payload, headers=auth)
        assert res.status_code == 422

    def test_generate_plan_empty_subjects(self, client, auth):
        payload = {**VALID_PLAN_PAYLOAD, "subjects": []}
        res = client.post("/plans/generate", json=payload, headers=auth)
        assert res.status_code == 422

    def test_generate_plan_requires_auth(self, client):
        res = client.post("/plans/generate", json=VALID_PLAN_PAYLOAD)
        assert res.status_code == 401


class TestListAndGetPlans:
    @patch("app.services.ai_service._get_client")
    def test_list_plans(self, mock_get_client, client, auth):
        mock_get_client.return_value = mock_ai_client()
        client.post("/plans/generate", json=VALID_PLAN_PAYLOAD, headers=auth)

        res = client.get("/plans/", headers=auth)
        assert res.status_code == 200
        assert len(res.json()) >= 1

    @patch("app.services.ai_service._get_client")
    def test_get_plan_by_id(self, mock_get_client, client, auth):
        mock_get_client.return_value = mock_ai_client()
        create_res = client.post("/plans/generate", json=VALID_PLAN_PAYLOAD, headers=auth)
        plan_id = create_res.json()["id"]

        res = client.get(f"/plans/{plan_id}", headers=auth)
        assert res.status_code == 200
        assert res.json()["id"] == plan_id

    def test_get_nonexistent_plan(self, client, auth):
        res = client.get("/plans/99999", headers=auth)
        assert res.status_code == 404

    @patch("app.services.ai_service._get_client")
    def test_users_cannot_see_other_users_plans(self, mock_get_client, client):
        mock_get_client.return_value = mock_ai_client()

        register_user(client, email="user1@example.com")
        headers1 = get_auth_headers(client, email="user1@example.com")
        create_res = client.post("/plans/generate", json=VALID_PLAN_PAYLOAD, headers=headers1)
        plan_id = create_res.json()["id"]

        register_user(client, email="user2@example.com")
        headers2 = get_auth_headers(client, email="user2@example.com")
        res = client.get(f"/plans/{plan_id}", headers=headers2)
        assert res.status_code == 404


class TestDeletePlan:
    @patch("app.services.ai_service._get_client")
    def test_delete_plan(self, mock_get_client, client, auth):
        mock_get_client.return_value = mock_ai_client()
        create_res = client.post("/plans/generate", json=VALID_PLAN_PAYLOAD, headers=auth)
        plan_id = create_res.json()["id"]

        del_res = client.delete(f"/plans/{plan_id}", headers=auth)
        assert del_res.status_code == 204

        get_res = client.get(f"/plans/{plan_id}", headers=auth)
        assert get_res.status_code == 404

    def test_delete_nonexistent_plan(self, client, auth):
        res = client.delete("/plans/99999", headers=auth)
        assert res.status_code == 404


class TestPlanProgress:
    @patch("app.services.ai_service._get_client")
    def test_plan_progress(self, mock_get_client, client, auth):
        mock_get_client.return_value = mock_ai_client()
        create_res = client.post("/plans/generate", json=VALID_PLAN_PAYLOAD, headers=auth)
        plan_id = create_res.json()["id"]
        task_id = create_res.json()["tasks"][0]["id"]

        client.patch(f"/tasks/{task_id}/complete", headers=auth)

        res = client.get(f"/plans/{plan_id}/progress", headers=auth)
        assert res.status_code == 200
        body = res.json()
        assert body["total_tasks"] == 2
        assert body["completed_tasks"] == 1
        assert body["remaining_tasks"] == 1
        assert body["progress_percentage"] == 50.0
