from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.user import UserRead
from app.schemas.course import CourseRead


class ScheduleBase(BaseModel):
    """Базовая схема расписания с общими полями."""
    course_id: int = Field(..., json_schema_extra={"example": 1}, description="ID курса")
    schedule_date: date = Field(..., json_schema_extra={"example": "2024-02-15"}, description="Дата занятия")
    start_time: time = Field(..., json_schema_extra={"example": "09:00:00"}, description="Время начала")
    end_time: time = Field(..., json_schema_extra={"example": "10:30:00"}, description="Время окончания")
    location: Optional[str] = Field(None, max_length=200, json_schema_extra={"example": "Аудитория 101"}, description="Место проведения")
    instructor_id: int = Field(..., json_schema_extra={"example": 1}, description="ID преподавателя")
    
    @field_validator('end_time')
    def validate_times(cls, v, info):
        """Валидация: время окончания должно быть больше времени начала."""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('Время окончания должно быть больше времени начала')
        return v


class ScheduleCreate(ScheduleBase):
    """Схема для создания нового расписания."""
    pass


class ScheduleUpdate(BaseModel):
    """Схема для обновления расписания."""
    course_id: Optional[int] = None
    schedule_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = Field(None, max_length=200)
    instructor_id: Optional[int] = None
    
    @field_validator('end_time')
    def validate_times(cls, v, info):
        """Валидация: время окончания должно быть больше времени начала."""
        if 'start_time' in info.data and info.data['start_time'] and v and v <= info.data['start_time']:
            raise ValueError('Время окончания должно быть больше времени начала')
        return v


class ScheduleRead(ScheduleBase):
    """Схема для чтения расписания с дополнительными полями."""
    id: int
    created_at: datetime
    updated_at: datetime
    course: Optional[CourseRead] = None
    instructor: Optional[UserRead] = None
    
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 1,
            "course_id": 1,
            "schedule_date": "2024-02-15",
            "start_time": "09:00:00",
            "end_time": "10:30:00",
            "location": "Аудитория 101",
            "instructor_id": 1,
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-01-15T10:00:00",
            "course": {
                "id": 1,
                "title": "Введение в AI",
                "description": "Курс по основам искусственного интеллекта",
                "start_date": "2024-02-01T09:00:00",
                "end_date": "2024-06-30T18:00:00",
                "owner_id": 1
            },
            "instructor": {
                "id": 1,
                "username": "teacher1",
                "role": "teacher"
            }
        }
    })


class ScheduleList(BaseModel):
    """Схема для списка расписаний с пагинацией."""
    schedules: List[ScheduleRead]
    total: int
    skip: int
    limit: int
    
    model_config = ConfigDict(from_attributes=True)