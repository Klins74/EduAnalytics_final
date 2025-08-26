from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator, ConfigDict
from app.models.submission import SubmissionStatus
from app.schemas.assignment import AssignmentRead
from app.schemas.user import UserRead


class SubmissionBase(BaseModel):
    """Базовая схема сдачи задания с общими полями."""
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=10000, 
        json_schema_extra={"example": "Решение задачи находится в репозитории: https://github.com/student/homework1"}
    )


class SubmissionCreate(SubmissionBase):
    """Схема для создания новой сдачи задания."""
    assignment_id: int = Field(..., json_schema_extra={"example": 1}, description="ID задания")
    submitted_at: Optional[datetime] = Field(
        None, 
        json_schema_extra={"example": "2024-03-14T20:30:00"},
        description="Время сдачи (если не указано, используется текущее время)"
    )


class SubmissionUpdate(BaseModel):
    """Схема для обновления сдачи задания."""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    submitted_at: Optional[datetime] = None


class SubmissionRead(SubmissionBase):
    """Схема для чтения сдачи задания с дополнительными полями."""
    id: int
    submitted_at: datetime
    status: SubmissionStatus
    student_id: int
    assignment_id: int
    created_at: datetime
    updated_at: datetime
    
    # Вложенные объекты
    assignment: Optional[AssignmentRead] = None
    student: Optional[UserRead] = None
    
    model_config = ConfigDict(from_attributes=True, json_schema_extra = {
            "example": {
                "id": 1,
                "content": "Решение задачи находится в репозитории: https://github.com/student/homework1",
                "submitted_at": "2024-03-14T20:30:00",
                "status": "submitted",
                "student_id": 2,
                "assignment_id": 1,
                "created_at": "2024-03-14T20:30:00",
                "updated_at": "2024-03-14T20:30:00",
                "assignment": {
                    "id": 1,
                    "title": "Домашнее задание 1",
                    "description": "Решить задачи по линейной алгебре",
                    "due_date": "2024-03-15T23:59:59",
                    "course_id": 1
                },
                "student": {
                    "id": 2,
                    "email": "student@example.com",
                    "full_name": "Иван Студентов",
                    "role": "student"
                }
            }
        })


class SubmissionList(BaseModel):
    """Схема для списка сдач заданий с пагинацией."""
    submissions: list[SubmissionRead]
    total: int
    skip: int
    limit: int


# Импортируем схемы оценок из основного модуля grade
from .grade import GradeCreate, GradeResponse