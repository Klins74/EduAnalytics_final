from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class GradeCreate(BaseModel):
    score: float
    feedback: Optional[str] = None
    graded_by: int
    submission_id: int

class GradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    score: float
    feedback: Optional[str] = None
    graded_at: datetime
    graded_by: int
    submission_id: int