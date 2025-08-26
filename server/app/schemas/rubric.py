from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RubricCriterionBase(BaseModel):
    description: str
    points: float = Field(0, ge=0)
    position: int = 0


class RubricCriterionCreate(RubricCriterionBase):
    pass


class RubricCriterionRead(RubricCriterionBase):
    id: int
    rubric_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RubricBase(BaseModel):
    title: str
    description: Optional[str] = None
    total_points: float = Field(100, ge=0)


class RubricCreate(RubricBase):
    course_id: int
    criteria: Optional[List[RubricCriterionCreate]] = None


class RubricRead(RubricBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime
    criteria: List[RubricCriterionRead] = []
    model_config = ConfigDict(from_attributes=True)




