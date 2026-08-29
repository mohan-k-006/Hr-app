from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse

router = APIRouter()

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    """Create a new Job Description requirement."""
    job = Job(
        title=job_in.title,
        department=job_in.department,
        description=job_in.description,
        required_skills=job_in.required_skills,
        preferred_skills=job_in.preferred_skills,
        min_experience_years=job_in.min_experience_years
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("/", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    """List all Job descriptions."""
    return db.query(Job).order_by(Job.created_at.desc()).all()

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific Job description by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job_in: JobCreate, db: Session = Depends(get_db)):
    """Update an existing Job Description requirement."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    job.title = job_in.title
    job.department = job_in.department
    job.description = job_in.description
    job.required_skills = job_in.required_skills
    job.preferred_skills = job_in.preferred_skills
    job.min_experience_years = job_in.min_experience_years
    
    db.commit()
    db.refresh(job)
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a Job description and its associated screening results."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    db.delete(job)
    db.commit()
    return None
