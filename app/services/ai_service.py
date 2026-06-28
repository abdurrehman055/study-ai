import json
from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from openai import OpenAI

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _get_client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key is not configured",
        )
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_study_plan(
    subjects: List[str],
    exam_date: datetime,
    daily_study_hours: float,
    difficulty: str,
    preferred_study_time: str,
) -> dict:
    today = datetime.utcnow()
    days_until_exam = (exam_date - today).days

    prompt = f"""You are an expert academic study planner. Create a realistic, actionable day-by-day study plan.

Student details:
- Subjects: {', '.join(subjects)}
- Exam date: {exam_date.strftime('%Y-%m-%d')}
- Days available: {days_until_exam}
- Daily study hours: {daily_study_hours}
- Difficulty level: {difficulty}
- Preferred study time: {preferred_study_time}

Start date: {today.strftime('%Y-%m-%d')}

Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
{{
    "explanation": "A short paragraph explaining the reasoning behind this schedule",
    "study_tips": "3-5 practical, specific study tips as a single string separated by newlines",
    "daily_tasks": [
        {{
            "date": "YYYY-MM-DD",
            "subject": "Subject name",
            "description": "Specific, actionable description of what to study",
            "duration_hours": 1.5
        }}
    ]
}}

Rules:
- Distribute subjects evenly across available days, weighting harder subjects more
- Hard difficulty = more review sessions and problem-solving practice
- Medium difficulty = balanced reading and practice
- Easy difficulty = lighter review with focus on key concepts
- Total duration_hours per day must not exceed {daily_study_hours}
- Each day can have multiple tasks for different subjects
- Do NOT schedule tasks on the exam day itself ({exam_date.strftime('%Y-%m-%d')})
- Descriptions must be specific (e.g. "Read Chapter 4: Calculus Integration, solve 15 practice problems" not "Study Math")
- Add a review/mock test day in the final 2 days before the exam"""

    logger.info(f"Requesting AI plan for subjects={subjects}, difficulty={difficulty}, days={days_until_exam}")

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert study planner. Always respond with valid JSON only. Never include markdown code blocks.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
    )

    content = response.choices[0].message.content.strip()

    # Strip markdown fences if the model wraps the JSON
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse AI response as JSON: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an invalid response. Please try again.",
        )

    task_count = len(result.get("daily_tasks", []))
    logger.info(f"AI plan generated successfully: {task_count} tasks")
    return result
