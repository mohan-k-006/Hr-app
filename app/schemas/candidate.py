from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class CandidateResponse(BaseModel):
    id: int
    name: Optional[str] = "Unknown"
    email: Optional[str] = None
    phone: Optional[str] = None
    filename: str
    file_type: str
    raw_text: Optional[str] = ""
    extracted_skills: List[str] = []
    extracted_education: List[str] = []
    experience_years: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
