import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import register_user, get_auth_headers


FUTURE_DATE = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")

MOCK_AI_RESULT = {
    "explanation": "Test plan.",
    "study_tips": "Study consistently.",
    "daily_tasks": [
        {
            "date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "subject": "Biology",
            "description": "Read Chapter 1: Cell Structure",
            "duration_hours": 1.5,
        },
        {
            "date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "subject": "Biology",
            "description": "Read Chapter 2: Photosynthesis",
            "duration_hours": 1.5,
        },
    ],
}


@pytest.fixture
def auth_and_plan(client):
    register_user(client, email="tasks@example.com")
    headers = get_auth_headers(client, email="tasks@example.com")

    with patch("app.services.ai_service._get_client") as mock_get_client:
        mock = MagicMock()
        mock.chat.completions.create.return_value.choices[0].message.content = json.dumps(MOCK_AI_RESULT)
        mock_get_client.return_value = mock

        res = client.post(
            "/plans/generate",
            json={
                "subjects": ["Biology"],
                "exam_date": FUTURE_DATE,
                "daily_study_hours": 2,
                "difficulty": "Easy",
            },
            headers=headers,
        )

    plan = res.json()
    return headers, plan


class TestMarkComplete:
    def test_mark_task_complete(self, client, auth_and_plan):
        headers, plan = auth_and_plan
        task_id = plan["tasks"][0]["id"]

        res = client.patch(f"/tasks/{task_id}/complete", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["is_completed"] is True
        assert body["completed_at"] is not None

    def test_mark_task_complete_twice(self, client, auth_and_plan):
        headers, plan = auth_and_plan
        task_id = plan["tasks"][0]["id"]

        client.patch(f"/tasks/{task_id}/complete", headers=headers)
        res = client.patch(f"/tasks/{task_id}/complete", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_completed"] is True

    def test_mark_nonexistent_task_complete(self, client, auth_and_plan):
        headers, _ = auth_and_plan
        res = client.patch("/tasks/99999/complete", headers=headers)
        assert res.status_code == 404

    def test_mark_complete_requires_auth(self, client, auth_and_plan):
        _, plan = auth_and_plan
        task_id = plan["tasks"][0]["id"]
        res = client.patch(f"/tasks/{task_id}/complete")
        assert res.status_code == 401


class TestMarkIncomplete:
    def test_mark_task_incomplete(self, client, auth_and_plan):
        headers, plan = auth_and_plan
        task_id = plan["tasks"][0]["id"]

        client.patch(f"/tasks/{task_id}/complete", headers=headers)
        res = client.patch(f"/tasks/{task_id}/incomplete", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["is_completed"] is False
        assert body["completed_at"] is None

    def test_mark_incomplete_on_already_incomplete_task(self, client, auth_and_plan):
        headers, plan = auth_and_plan
        task_id = plan["tasks"][0]["id"]

        res = client.patch(f"/tasks/{task_id}/incomplete", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_completed"] is False


class TestTaskOwnership:
    def test_cannot_complete_another_users_task(self, client, auth_and_plan):
        _, plan = auth_and_plan
        task_id = plan["tasks"][0]["id"]

        register_user(client, email="other@example.com")
        other_headers = get_auth_headers(client, email="other@example.com")

        res = client.patch(f"/tasks/{task_id}/complete", headers=other_headers)
        assert res.status_code == 404
