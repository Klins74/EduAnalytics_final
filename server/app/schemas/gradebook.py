from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID


class GradebookEntryBase(BaseModel):
    """Базовая схема для записи в электронном журнале."""
    course_id: int = Field(..., description="ID курса")
    student_id: int = Field(..., description="ID студента")
    assignment_id: Optional[int] = Field(None, description="ID задания (опционально для общих оценок)")
    grade_value: float = Field(..., ge=0, le=100, description="Оценка (0-100)")
    comment: Optional[str] = Field(None, max_length=1000, description="Комментарий к оценке")

    @field_validator('grade_value')
    def validate_grade_value(cls, v):
        """Валидация оценки."""
        if v < 0 or v > 100:
            raise ValueError('Оценка должна быть в диапазоне от 0 до 100')
        return round(v, 2)  # Округляем до 2 знаков после запятой

    @field_validator('comment')
    def validate_comment(cls, v):
        """Валидация комментария."""
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class GradebookEntryCreate(GradebookEntryBase):
    """Схема для создания записи в электронном журнале."""
    model_config = ConfigDict(json_schema_extra = {
            "example": {
                "course_id": 1,
                "student_id": 2,
                "assignment_id": 3,
                "grade_value": 85.5,
                "comment": "Отличная работа, но есть небольшие замечания"
            }
        })


class GradebookEntryUpdate(BaseModel):
    """Схема для обновления записи в электронном журнале."""
    grade_value: Optional[float] = Field(None, ge=0, le=100, description="Новая оценка")
    comment: Optional[str] = Field(None, max_length=1000, description="Новый комментарий")

    @field_validator('grade_value')
    def validate_grade_value(cls, v):
        """Валидация оценки."""
        if v is not None:
            if v < 0 or v > 100:
                raise ValueError('Оценка должна быть в диапазоне от 0 до 100')
            return round(v, 2)
        return v

    @field_validator('comment')
    def validate_comment(cls, v):
        """Валидация комментария."""
        if v is not None and len(v.strip()) == 0:
            return None
        return v

    model_config = ConfigDict(json_schema_extra = {
            "example": {
                "grade_value": 90.0,
                "comment": "Исправлены все замечания"
            }
        })


class GradebookEntryRead(GradebookEntryBase):
    """Схема для чтения записи из электронного журнала."""
    id: int = Field(..., description="ID записи")
    created_by: int = Field(..., description="ID пользователя, создавшего запись")
    created_at: datetime = Field(..., description="Дата и время создания")
    updated_at: datetime = Field(..., description="Дата и время последнего обновления")

    model_config = ConfigDict(from_attributes=True, json_schema_extra = {
            "example": {
                "id": 1,
                "course_id": 1,
                "student_id": 2,
                "assignment_id": 3,
                "grade_value": 85.5,
                "comment": "Отличная работа",
                "created_by": 1,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        })


class GradebookHistoryRead(BaseModel):
    """Схема для чтения истории изменений записи."""
    id: int = Field(..., description="ID записи истории")
    entry_id: int = Field(..., description="ID записи в журнале")
    course_id: int = Field(..., description="ID курса")
    student_id: int = Field(..., description="ID студента")
    assignment_id: Optional[int] = Field(None, description="ID задания")
    grade_value: float = Field(..., description="Оценка")
    comment: Optional[str] = Field(None, description="Комментарий")
    operation: Literal["create", "update", "delete"] = Field(..., description="Тип операции")
    changed_by: int = Field(..., description="ID пользователя, внесшего изменение")
    changed_at: datetime = Field(..., description="Дата и время изменения")

    model_config = ConfigDict(from_attributes=True, json_schema_extra = {
            "example": {
                "id": 1,
                "entry_id": 1,
                "course_id": 1,
                "student_id": 2,
                "assignment_id": 3,
                "grade_value": 85.5,
                "comment": "Отличная работа",
                "operation": "create",
                "changed_by": 1,
                "changed_at": "2024-01-15T10:30:00"
            }
        })


class GradebookEntryList(BaseModel):
    """Схема для списка записей с пагинацией."""
    items: List[GradebookEntryRead] = Field(..., description="Список записей")
    total: int = Field(..., description="Общее количество записей")
    page: int = Field(..., description="Номер страницы")
    size: int = Field(..., description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц")

    model_config = ConfigDict(json_schema_extra = {
            "example": {
                "items": [],
                "total": 50,
                "page": 1,
                "size": 10,
                "pages": 5
            }
        })


class GradebookStats(BaseModel):
    """Схема для статистики по оценкам."""
    average_grade: float = Field(..., description="Средняя оценка")
    min_grade: float = Field(..., description="Минимальная оценка")
    max_grade: float = Field(..., description="Максимальная оценка")
    total_entries: int = Field(..., description="Общее количество записей")
    graded_assignments: int = Field(..., description="Количество оцененных заданий")

    model_config = ConfigDict(json_schema_extra = {
            "example": {
                "average_grade": 78.5,
                "min_grade": 45.0,
                "max_grade": 98.0,
                "total_entries": 25,
                "graded_assignments": 15
            }
        })