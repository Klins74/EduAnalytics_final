from pydantic import BaseModel
from typing import Optional

class GradeCreate(BaseModel):
    student_id: int
    value: int
    subject: int

class GradeResponse(BaseModel):
    id: int
    student_id: int
    value: int
    student_name: Optional[str] = None