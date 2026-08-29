from fastapi import APIRouter
from app.api import jobs, candidates, screening, auth

api_router = APIRouter(prefix="/api")
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["Candidates"])
api_router.include_router(screening.router, prefix="/screening", tags=["Screening"])
api_router.include_router(auth.router, tags=["Authentication"])
