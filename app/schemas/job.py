from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class JobBase(BaseModel):
    title: str
    department: Optional[str] = "Engineering"
    description: str
    required_skills: List[str]
    preferred_skills: List[str] = []
    min_experience_years: Optional[int] = 0

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
