from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from app.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    file_path = Column(String(500), nullable=True)
    raw_text = Column(Text, nullable=False)
    
    # Extracted metadata
    extracted_skills = Column(JSON, nullable=False, default=list)
    extracted_education = Column(JSON, nullable=False, default=list)
    experience_years = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    screening_results = relationship("ScreeningResult", back_populates="candidate", cascade="all, delete-orphan")
