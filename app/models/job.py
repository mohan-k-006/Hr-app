from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=False, default=list)  # list of strings
    preferred_skills = Column(JSON, nullable=False, default=list)  # list of strings
    min_experience_years = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    screening_results = relationship("ScreeningResult", back_populates="job", cascade="all, delete-orphan")
