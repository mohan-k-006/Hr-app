from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Match Scores (Percentages 0-100)
    overall_score = Column(Float, nullable=False, index=True)
    skills_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    vector_similarity_score = Column(Float, nullable=False, default=0.0)
    
    # Skill breakdown
    matched_required_skills = Column(JSON, nullable=False, default=list)
    missing_required_skills = Column(JSON, nullable=False, default=list)
    matched_preferred_skills = Column(JSON, nullable=False, default=list)
    missing_preferred_skills = Column(JSON, nullable=False, default=list)
    
    # AI Verdict
    recommendation = Column(String(50), nullable=False)  # SHORTLIST, MAYBE, REJECT
    reasoning = Column(Text, nullable=False)
    
    screened_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="screening_results")
    job = relationship("Job", back_populates="screening_results")
