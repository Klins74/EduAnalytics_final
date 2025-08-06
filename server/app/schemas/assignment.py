from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.course import CourseRead


class AssignmentBase(BaseModel):
    """Базовая схема задания с общими полями."""
    title: str = Field(..., min_length=1, max_length=200, json_schema_extra={"example": "Домашнее задание 1"})
    description: Optional[str] = Field(None, max_length=2000, json_schema_extra={"example": "Решить задачи по линейной алгебре"})
    due_date: datetime = Field(..., json_schema_extra={"example": "2024-03-15T23:59:59"})


class AssignmentCreate(AssignmentBase):
    """Схема для создания нового задания."""
    course_id: int = Field(..., json_schema_extra={"example": 1}, description="ID курса")


class AssignmentUpdate(BaseModel):
    """Схема для обновления задания."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[datetime] = None


class AssignmentRead(AssignmentBase):
    """Схема для чтения задания с дополнительными полями."""
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime
    course: Optional[CourseRead] = None
    
    model_config = ConfigDict(from_attributes=True, json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Домашнее задание 1",
                "description": "Решить задачи по линейной алгебре",
                "due_date": "2024-03-15T23:59:59",
                "course_id": 1,
                "created_at": "2024-02-01T10:00:00",
                "updated_at": "2024-02-01T10:00:00",
                "course": {
                    "id": 1,
                    "title": "Введение в AI",
                    "description": "Курс по основам искусственного интеллекта",
                    "start_date": "2024-02-01T09:00:00",
                    "end_date": "2024-06-30T18:00:00",
                    "owner_id": 1
                }
            }
        })


class AssignmentList(BaseModel):
    """Схема для списка заданий с пагинацией."""
    assignments: list[AssignmentRead]
    total: int
    skip: int
    limit: int