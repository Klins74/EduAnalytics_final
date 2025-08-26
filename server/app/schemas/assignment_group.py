from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AssignmentGroupBase(BaseModel):
    name: str
    weight: float = Field(1.0, ge=0)
    drop_lowest: int = 0
    is_weighted: bool = False


class AssignmentGroupCreate(AssignmentGroupBase):
    course_id: int


class AssignmentGroupUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = Field(None, ge=0)
    drop_lowest: Optional[int] = None
    is_weighted: Optional[bool] = None


class AssignmentGroupRead(AssignmentGroupBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)




