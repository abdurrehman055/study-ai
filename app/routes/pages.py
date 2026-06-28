from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=RedirectResponse)
def index():
    return RedirectResponse(url="/login")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/app/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/app/plans", response_class=HTMLResponse)
def plans_page(request: Request):
    return templates.TemplateResponse("plans.html", {"request": request})


@router.get("/app/plans/{plan_id}", response_class=HTMLResponse)
def plan_detail_page(request: Request, plan_id: int):
    return templates.TemplateResponse(
        "plan_detail.html", {"request": request, "plan_id": plan_id}
    )


@router.get("/app/status", response_class=HTMLResponse)
def status_page(request: Request):
    return templates.TemplateResponse("status.html", {"request": request})
