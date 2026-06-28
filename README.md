# StudyAI

An AI-powered study planning platform that generates personalized study schedules, tracks progress, and helps students prepare efficiently for exams.

**Live Demo:** https://study-ai-9qp9.onrender.com

**API Docs:** https://study-ai-9qp9.onrender.com/docs

---

## Screenshots

### Login

![Login](screenshots/login.png)

### Dashboard

![Dashboard](screenshots/dashboard.png)

### Study Plans

![Plans](screenshots/plans.png)

### Study Plan Detail

![Plan Detail](screenshots/plan-detail.png)

### Status

![Status](screenshots/status.png)

---

## Features

* JWT authentication with secure registration and login
* AI-generated study plans powered by OpenAI GPT-4o-mini
* Personalized schedules based on subjects, exam date, and study hours
* Daily task generation and management
* Progress tracking and completion analytics
* Study streak monitoring
* Exam countdown tracking
* Plan regeneration
* Task completion management
* Dashboard with statistics
* PostgreSQL persistence
* Swagger API documentation
* Responsive dark-themed interface
* Render deployment

---

## Tech Stack

### Backend

* Python 3.12
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic

### Authentication

* JWT
* OAuth2
* Passlib
* bcrypt

### AI

* OpenAI GPT-4o-mini

### Frontend

* Jinja2
* HTML5
* CSS3
* Bootstrap 5
* JavaScript

### Deployment

* Render
* Docker (optional)

---

## Live Application

Frontend

https://study-ai-9qp9.onrender.com

Dashboard

https://study-ai-9qp9.onrender.com/app/dashboard

Plans

https://study-ai-9qp9.onrender.com/app/plans

Status

https://study-ai-9qp9.onrender.com/app/status

Swagger

https://study-ai-9qp9.onrender.com/docs

---

## Frontend Routes

| Route             | Description      |
| ----------------- | ---------------- |
| `/login`          | Login page       |
| `/register`       | Register page    |
| `/app/dashboard`  | Dashboard        |
| `/app/plans`      | Plans page       |
| `/app/plans/{id}` | Plan details     |
| `/app/status`     | Status page      |
| `/docs`           | Swagger API docs |

---

## Local Setup

Clone repository

```bash
git clone https://github.com/abdurrehman055/study-ai.git

cd study-ai
```

Create virtual environment

```bash
python -m venv venv

venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create `.env`

```env
OPENAI_API_KEY=your_openai_key

DATABASE_URL=your_postgresql_url

SECRET_KEY=your_secret_key
```

Run migrations

```bash
alembic upgrade head
```

Run application

```bash
uvicorn main:app --reload
```

Visit

```text
http://localhost:8000
```

Swagger

```text
http://localhost:8000/docs
```

---

## Project Structure

```text
study-ai/

app/
templates/
static/
alembic/
tests/

main.py
requirements.txt
README.md
```

---

## Future Improvements

* Google Calendar integration
* Email reminders
* AI recommendations
* User profiles
* Pomodoro timer
* Analytics dashboard
* SaaS subscriptions
* Team study groups

---

## Author

Abdurrehman Masood

Computer Engineering Student — COMSATS Lahore
