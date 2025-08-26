from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class WebhookEventType(str, Enum):
    """Типы событий для webhook уведомлений."""
    DEADLINE_APPROACHING = "deadline_approaching"
    GRADE_CREATED = "grade_created"
    FEEDBACK_CREATED = "feedback_created"
    SCHEDULE_UPDATED = "schedule_updated"
    TEST_NOTIFICATION = "test_notification"


class WebhookNotifyRequest(BaseModel):
    """Запрос для webhook уведомления от n8n."""
    event_type: WebhookEventType = Field(..., description="Тип события")
    data: Dict[str, Any] = Field(..., description="Данные события")
    timestamp: Optional[datetime] = Field(default=None, description="Время события")
    user_id: Optional[int] = Field(default=None, description="ID пользователя")
    notification_channels: Optional[List[str]] = Field(
        default=["email"], 
        description="Каналы уведомлений (email, telegram, push)"
    )


class WebhookResponse(BaseModel):
    """Ответ webhook."""
    success: bool = Field(..., description="Успешность обработки")
    message: str = Field(..., description="Сообщение о результате")
    event_id: Optional[str] = Field(default=None, description="ID события")


class DeadlineNotificationData(BaseModel):
    """Данные для уведомления о приближающемся дедлайне."""
    assignment_id: int = Field(..., description="ID задания")
    assignment_title: str = Field(..., description="Название задания")
    due_date: datetime = Field(..., description="Дедлайн")
    course_name: str = Field(..., description="Название курса")
    course_id: int = Field(..., description="ID курса")
    hours_remaining: int = Field(..., description="Часов до дедлайна")
    students: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Список студентов для уведомления"
    )


class GradeNotificationData(BaseModel):
    """Данные для уведомления о новой оценке."""
    grade_id: int = Field(..., description="ID оценки")
    student_id: int = Field(..., description="ID студента")
    student_name: str = Field(..., description="Имя студента")
    student_email: str = Field(..., description="Email студента")
    assignment_title: str = Field(..., description="Название задания")
    assignment_id: int = Field(..., description="ID задания")
    grade_value: float = Field(..., description="Значение оценки")
    max_grade: Optional[float] = Field(default=None, description="Максимальная оценка")
    course_name: str = Field(..., description="Название курса")
    teacher_name: str = Field(..., description="Имя преподавателя")


class FeedbackNotificationData(BaseModel):
    """Данные для уведомления о новом комментарии."""
    feedback_id: int = Field(..., description="ID комментария")
    submission_id: int = Field(..., description="ID работы")
    author_name: str = Field(..., description="Автор комментария")
    author_id: int = Field(..., description="ID автора")
    feedback_text: str = Field(..., description="Текст комментария")
    submission_title: Optional[str] = Field(default=None, description="Название работы")
    student_name: Optional[str] = Field(default=None, description="Имя студента")
    student_id: Optional[int] = Field(default=None, description="ID студента")
    student_email: Optional[str] = Field(default=None, description="Email студента")
    course_name: Optional[str] = Field(default=None, description="Название курса")


class ScheduleNotificationData(BaseModel):
    """Данные для уведомления об изменении расписания."""
    schedule_id: int = Field(..., description="ID расписания")
    course_name: str = Field(..., description="Название курса")
    course_id: int = Field(..., description="ID курса")
    schedule_date: str = Field(..., description="Дата занятия")
    start_time: str = Field(..., description="Время начала")
    end_time: str = Field(..., description="Время окончания")
    location: str = Field(..., description="Место проведения")
    instructor_name: str = Field(..., description="Имя преподавателя")
    change_type: str = Field(..., description="Тип изменения (created, updated, deleted)")
    lesson_type: Optional[str] = Field(None, description="Тип занятия")
    description: Optional[str] = Field(None, description="Описание занятия")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")
    is_cancelled: Optional[bool] = Field(None, description="Отменено ли занятие")
    classroom_id: Optional[int] = Field(None, description="ID аудитории")
    students: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Список студентов для уведомления"
    )
    old_data: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Старые данные (для обновлений)"
    )


class NotificationSettings(BaseModel):
    """Настройки уведомлений пользователя."""
    user_id: int = Field(..., description="ID пользователя")
    email_enabled: bool = Field(default=True, description="Email уведомления")
    telegram_enabled: bool = Field(default=False, description="Telegram уведомления")
    push_enabled: bool = Field(default=True, description="Push уведомления")
    deadline_hours: List[int] = Field(
        default=[24, 48], 
        description="За сколько часов уведомлять о дедлайнах"
    )
    event_types: List[WebhookEventType] = Field(
        default_factory=lambda: list(WebhookEventType), 
        description="Типы событий для уведомлений"
    )