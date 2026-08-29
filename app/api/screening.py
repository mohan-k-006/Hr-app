from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.screening import ScreeningResult
from app.schemas.screening import ScreeningResultResponse, ScreeningSummary
from app.services.matcher import evaluate_candidate

router = APIRouter()

@router.post("/screen/{job_id}/{candidate_id}", response_model=ScreeningResultResponse, status_code=status.HTTP_200_OK)
def screen_candidate(job_id: int, candidate_id: int, db: Session = Depends(get_db)):
    """Run AI screening evaluation for a single candidate against a specific job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    eval_data = evaluate_candidate(candidate, job)

    # Check if screening result already exists, update if so
    existing = db.query(ScreeningResult).filter(
        ScreeningResult.job_id == job_id,
        ScreeningResult.candidate_id == candidate_id
    ).first()

    if existing:
        existing.overall_score = eval_data["overall_score"]
        existing.skills_score = eval_data["skills_score"]
        existing.experience_score = eval_data["experience_score"]
        existing.vector_similarity_score = eval_data["vector_similarity_score"]
        existing.matched_required_skills = eval_data["matched_required_skills"]
        existing.missing_required_skills = eval_data["missing_required_skills"]
        existing.matched_preferred_skills = eval_data["matched_preferred_skills"]
        existing.missing_preferred_skills = eval_data["missing_preferred_skills"]
        existing.recommendation = eval_data["recommendation"]
        existing.reasoning = eval_data["reasoning"]
        result = existing
    else:
        result = ScreeningResult(
            candidate_id=candidate.id,
            job_id=job.id,
            overall_score=eval_data["overall_score"],
            skills_score=eval_data["skills_score"],
            experience_score=eval_data["experience_score"],
            vector_similarity_score=eval_data["vector_similarity_score"],
            matched_required_skills=eval_data["matched_required_skills"],
            missing_required_skills=eval_data["missing_required_skills"],
            matched_preferred_skills=eval_data["matched_preferred_skills"],
            missing_preferred_skills=eval_data["missing_preferred_skills"],
            recommendation=eval_data["recommendation"],
            reasoning=eval_data["reasoning"]
        )
        db.add(result)

    db.commit()
    db.refresh(result)
    return result

@router.post("/screen/{job_id}", response_model=List[ScreeningResultResponse])
def screen_all_candidates(job_id: int, db: Session = Depends(get_db)):
    """Run AI screening evaluation for ALL stored candidates against a specific job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    candidates = db.query(Candidate).all()
    if not candidates:
        return []

    results = []
    for cand in candidates:
        eval_data = evaluate_candidate(cand, job)
        existing = db.query(ScreeningResult).filter(
            ScreeningResult.job_id == job_id,
            ScreeningResult.candidate_id == cand.id
        ).first()

        if existing:
            existing.overall_score = eval_data["overall_score"]
            existing.skills_score = eval_data["skills_score"]
            existing.experience_score = eval_data["experience_score"]
            existing.vector_similarity_score = eval_data["vector_similarity_score"]
            existing.matched_required_skills = eval_data["matched_required_skills"]
            existing.missing_required_skills = eval_data["missing_required_skills"]
            existing.matched_preferred_skills = eval_data["matched_preferred_skills"]
            existing.missing_preferred_skills = eval_data["missing_preferred_skills"]
            existing.recommendation = eval_data["recommendation"]
            existing.reasoning = eval_data["reasoning"]
            results.append(existing)
        else:
            res = ScreeningResult(
                candidate_id=cand.id,
                job_id=job.id,
                overall_score=eval_data["overall_score"],
                skills_score=eval_data["skills_score"],
                experience_score=eval_data["experience_score"],
                vector_similarity_score=eval_data["vector_similarity_score"],
                matched_required_skills=eval_data["matched_required_skills"],
                missing_required_skills=eval_data["missing_required_skills"],
                matched_preferred_skills=eval_data["matched_preferred_skills"],
                missing_preferred_skills=eval_data["missing_preferred_skills"],
                recommendation=eval_data["recommendation"],
                reasoning=eval_data["reasoning"]
            )
            db.add(res)
            results.append(res)

    db.commit()
    for r in results:
        db.refresh(r)

    # Sort results by overall score descending
    results.sort(key=lambda x: x.overall_score, reverse=True)
    return results

@router.get("/results", response_model=List[ScreeningResultResponse])
def get_screening_results(
    job_id: Optional[int] = Query(None),
    recommendation: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Fetch ranked screening results with filtering options."""
    query = db.query(ScreeningResult)

    if job_id:
        query = query.filter(ScreeningResult.job_id == job_id)
    if recommendation:
        query = query.filter(ScreeningResult.recommendation == recommendation.upper())
    if min_score is not None:
        query = query.filter(ScreeningResult.overall_score >= min_score)

    return query.order_by(ScreeningResult.overall_score.desc()).all()

@router.get("/summary/{job_id}", response_model=ScreeningSummary)
def get_screening_summary(job_id: int, db: Session = Depends(get_db)):
    """Get screening metrics & breakdown for a specific job."""
    results = db.query(ScreeningResult).filter(ScreeningResult.job_id == job_id).all()
    if not results:
        return ScreeningSummary(
            total_screened=0,
            shortlisted_count=0,
            maybe_count=0,
            rejected_count=0,
            average_score=0.0
        )

    shortlisted = sum(1 for r in results if r.recommendation == "SHORTLIST")
    maybe = sum(1 for r in results if r.recommendation == "MAYBE")
    rejected = sum(1 for r in results if r.recommendation == "REJECT")
    avg_score = round(sum(r.overall_score for r in results) / len(results), 2)

    return ScreeningSummary(
        total_screened=len(results),
        shortlisted_count=shortlisted,
        maybe_count=maybe,
        rejected_count=rejected,
        average_score=avg_score
    )
