from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.models.enrollment import EnrollmentRole, EnrollmentStatus

if TYPE_CHECKING:
    from app.schemas.user import UserRead
    from app.schemas.course import CourseRead


class EnrollmentBase(BaseModel):
    """Базовая схема для Enrollment"""
    role: EnrollmentRole = Field(default=EnrollmentRole.student, description="Роль в курсе")
    status: EnrollmentStatus = Field(default=EnrollmentStatus.active, description="Статус записи")
    grade_override: Optional[str] = Field(None, description="Переопределение итоговой оценки")
    is_admin: bool = Field(default=False, description="Админские права в курсе")


class EnrollmentCreate(EnrollmentBase):
    """Схема для создания записи на курс"""
    user_id: int = Field(..., description="ID пользователя")
    course_id: int = Field(..., description="ID курса")


class EnrollmentUpdate(BaseModel):
    """Схема для обновления записи на курс"""
    role: Optional[EnrollmentRole] = None
    status: Optional[EnrollmentStatus] = None
    grade_override: Optional[str] = None
    is_admin: Optional[bool] = None
    completed_at: Optional[datetime] = None
    dropped_at: Optional[datetime] = None


class EnrollmentResponse(EnrollmentBase):
    """Схема для возврата информации о записи на курс"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    dropped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class EnrollmentWithUser(EnrollmentResponse):
    """Схема записи на курс с информацией о пользователе"""
    user: "UserRead"


class EnrollmentWithCourse(EnrollmentResponse):
    """Схема записи на курс с информацией о курсе"""
    course: "CourseRead"


class EnrollmentFull(EnrollmentResponse):
    """Полная схема записи на курс с пользователем и курсом"""
    user: "UserRead"
    course: "CourseRead"


class EnrollmentStats(BaseModel):
    """Статистика записей на курс"""
    total_enrollments: int = Field(..., description="Всего записей")
    active_students: int = Field(..., description="Активных студентов")
    active_teachers: int = Field(..., description="Активных преподавателей")
    completed_count: int = Field(..., description="Завершивших курс")
    dropped_count: int = Field(..., description="Покинувших курс")
    by_role: dict = Field(..., description="Распределение по ролям")
    by_status: dict = Field(..., description="Распределение по статусам")


class BulkEnrollmentCreate(BaseModel):
    """Схема для массовой записи на курс"""
    course_id: int = Field(..., description="ID курса")
    user_ids: list[int] = Field(..., description="Список ID пользователей")
    role: EnrollmentRole = Field(default=EnrollmentRole.student, description="Роль для всех пользователей")
    status: EnrollmentStatus = Field(default=EnrollmentStatus.active, description="Статус для всех пользователей")


class BulkEnrollmentResponse(BaseModel):
    """Результат массовой записи"""
    created_count: int = Field(..., description="Количество созданных записей")
    skipped_count: int = Field(..., description="Количество пропущенных (уже существуют)")
    errors: list[str] = Field(default_factory=list, description="Ошибки при создании")
    created_enrollments: list[EnrollmentResponse] = Field(default_factory=list, description="Созданные записи")
