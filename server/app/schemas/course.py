from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.user import UserRead


class CourseBase(BaseModel):
    """Базовая схема курса с общими полями."""
    title: str = Field(..., min_length=1, max_length=200, json_schema_extra={"example": "Введение в AI"})
    description: Optional[str] = Field(None, max_length=1000, json_schema_extra={"example": "Курс по основам искусственного интеллекта"})
    start_date: datetime = Field(..., json_schema_extra={"example": "2024-02-01T09:00:00"})
    end_date: datetime = Field(..., json_schema_extra={"example": "2024-06-30T18:00:00"})
    
    @field_validator('end_date')
    def validate_dates(cls, v, info):
        """Валидация: дата окончания должна быть больше даты начала."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('Дата окончания должна быть больше даты начала')
        return v


class CourseCreate(CourseBase):
    """Схема для создания нового курса."""
    owner_id: int = Field(..., json_schema_extra={"example": 1}, description="ID преподавателя курса")


class CourseUpdate(BaseModel):
    """Схема для обновления курса."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @field_validator('end_date')
    def validate_dates(cls, v, info):
        """Валидация дат при обновлении."""
        if v and 'start_date' in info.data and info.data['start_date'] and v <= info.data['start_date']:
            raise ValueError('Дата окончания должна быть больше даты начала')
        return v


class CourseRead(CourseBase):
    """Схема для чтения курса с дополнительными полями."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    owner: Optional[UserRead] = None
    
    model_config = ConfigDict(from_attributes=True, json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Введение в AI",
                "description": "Курс по основам искусственного интеллекта",
                "start_date": "2024-02-01T09:00:00",
                "end_date": "2024-06-30T18:00:00",
                "owner_id": 1,
                "created_at": "2024-01-15T10:00:00",
                "updated_at": "2024-01-15T10:00:00",
                "owner": {
                    "id": 1,
                    "email": "teacher@example.com",
                    "full_name": "Иван Преподавателев",
                    "role": "teacher"
                }
            }
        })


class CourseList(BaseModel):
    """Схема для списка курсов с пагинацией."""
    courses: list[CourseRead]
    total: int
    skip: int
    limit: int