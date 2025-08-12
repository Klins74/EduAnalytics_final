from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
from app.schemas.user import UserRead
from app.schemas.course import CourseRead


class LessonType(str, Enum):
    """Типы занятий."""
    LECTURE = "lecture"
    SEMINAR = "seminar"
    LABORATORY = "laboratory"
    PRACTICAL = "practical"
    EXAM = "exam"
    CONSULTATION = "consultation"
    OTHER = "other"


class ScheduleBase(BaseModel):
    """Базовая схема расписания с общими полями."""
    course_id: int = Field(..., json_schema_extra={"example": 1}, description="ID курса")
    schedule_date: date = Field(..., json_schema_extra={"example": "2024-02-15"}, description="Дата занятия")
    start_time: time = Field(..., json_schema_extra={"example": "09:00:00"}, description="Время начала")
    end_time: time = Field(..., json_schema_extra={"example": "10:30:00"}, description="Время окончания")
    location: Optional[str] = Field(None, max_length=200, json_schema_extra={"example": "Аудитория 101"}, description="Место проведения")
    instructor_id: int = Field(..., json_schema_extra={"example": 1}, description="ID преподавателя")
    lesson_type: LessonType = Field(default=LessonType.LECTURE, description="Тип занятия")
    description: Optional[str] = Field(None, description="Описание занятия, тема")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")
    is_cancelled: bool = Field(default=False, description="Отменено ли занятие")
    classroom_id: Optional[int] = Field(None, description="ID аудитории")
    
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
    lesson_type: Optional[LessonType] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    is_cancelled: Optional[bool] = None
    classroom_id: Optional[int] = None
    
    @field_validator('end_time')
    def validate_times(cls, v, info):
        """Валидация: время окончания должно быть больше времени начала."""
        if 'start_time' in info.data and info.data['start_time'] and v and v <= info.data['start_time']:
            raise ValueError('Время окончания должно быть больше времени начала')
        return v


class ClassroomBase(BaseModel):
    name: str
    building: Optional[str] = None
    floor: Optional[int] = None
    capacity: Optional[int] = None
    equipment: Optional[str] = Field(None, description="JSON строка с оборудованием")
    is_available: bool = True


class ClassroomRead(ClassroomBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: date
    start_time: time
    end_time: time
    location: Optional[str] = None
    organizer_id: int
    is_public: bool = True


class EventRead(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


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
            "lesson_type": "lecture",
            "description": "Введение в нейронные сети",
            "notes": "Принести тетрадь",
            "is_cancelled": False,
            "classroom_id": 2,
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