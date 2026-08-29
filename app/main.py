import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import init_db, get_db
from app.api import api_router
from app.api.auth import router as auth_router
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.screening import ScreeningResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database schema
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RecruitFlow - Candidate Parser and Screening Engine",
    version="1.0.0"
)

# Session Middleware for Google OAuth & User Auth
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(api_router)
app.include_router(auth_router)

@app.get("/")
def home(request: Request, error: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Main entrypoint.
    STRICT AUTHENTICATION GUARD:
    - If user is NOT authenticated -> Renders dual-auth login page (Email/Password & Google One-Tap).
    - If user IS authenticated -> Renders main recruitment dashboard index.html.
    """
    user = request.session.get("user")
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": error,
                "google_auth_configured": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
            }
        )
    return dashboard_view(request, db)

@app.get("/dashboard")
def dashboard_view(request: Request, db: Session = Depends(get_db)):
    """
    Main HR Dashboard view. Protected by authentication guard.
    """
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/")
        
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    candidates_count = db.query(Candidate).count()
    screened_count = db.query(ScreeningResult).count()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "jobs": jobs,
            "candidates_count": candidates_count,
            "screened_count": screened_count,
            "user": user,
            "google_auth_configured": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
        }
    )

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
