from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.candidate import CandidateResponse
from app.schemas.job import JobResponse

class ScreeningResultResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    overall_score: float
    skills_score: float
    experience_score: float
    vector_similarity_score: float
    matched_required_skills: List[str]
    missing_required_skills: List[str]
    matched_preferred_skills: List[str]
    missing_preferred_skills: List[str]
    recommendation: str
    reasoning: str
    screened_at: datetime
    
    candidate: Optional[CandidateResponse] = None
    job: Optional[JobResponse] = None

    model_config = ConfigDict(from_attributes=True)

class ScreeningSummary(BaseModel):
    total_screened: int
    shortlisted_count: int
    maybe_count: int
    rejected_count: int
    average_score: float
