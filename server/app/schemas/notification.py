from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models.notification import NotificationStatus, NotificationType, NotificationPriority


class InAppNotificationBase(BaseModel):
    """Базовая схема для in-app уведомлений"""
    title: str = Field(..., description="Заголовок уведомления", max_length=255)
    message: str = Field(..., description="Текст уведомления")
    notification_type: NotificationType = Field(default=NotificationType.system, description="Тип уведомления")
    priority: NotificationPriority = Field(default=NotificationPriority.normal, description="Приоритет")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")
    action_url: Optional[str] = Field(None, description="URL для действия", max_length=512)
    expires_at: Optional[datetime] = Field(None, description="Время истечения")


class InAppNotificationCreate(InAppNotificationBase):
    """Схема для создания in-app уведомления"""
    user_id: int = Field(..., description="ID пользователя-получателя")
    assignment_id: Optional[int] = Field(None, description="ID связанного задания")
    course_id: Optional[int] = Field(None, description="ID связанного курса")
    grade_id: Optional[int] = Field(None, description="ID связанной оценки")
    schedule_id: Optional[int] = Field(None, description="ID связанного расписания")


class InAppNotificationUpdate(BaseModel):
    """Схема для обновления in-app уведомления"""
    status: Optional[NotificationStatus] = None
    read_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


class InAppNotificationResponse(InAppNotificationBase):
    """Схема для возврата in-app уведомления"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    status: NotificationStatus
    assignment_id: Optional[int] = None
    course_id: Optional[int] = None
    grade_id: Optional[int] = None
    schedule_id: Optional[int] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    
    # Computed properties
    is_read: bool = Field(description="Прочитано ли уведомление")
    is_archived: bool = Field(description="Архивировано ли уведомление")
    is_expired: bool = Field(description="Истекло ли уведомление")


class NotificationPreferencesBase(BaseModel):
    """Базовая схема для настроек уведомлений"""
    system_notifications: bool = Field(default=True, description="Системные уведомления")
    assignment_notifications: bool = Field(default=True, description="Уведомления о заданиях")
    grade_notifications: bool = Field(default=True, description="Уведомления об оценках")
    deadline_notifications: bool = Field(default=True, description="Уведомления о дедлайнах")
    reminder_notifications: bool = Field(default=True, description="Напоминания")
    feedback_notifications: bool = Field(default=True, description="Уведомления об обратной связи")
    schedule_notifications: bool = Field(default=True, description="Уведомления о расписании")
    announcement_notifications: bool = Field(default=True, description="Объявления")
    
    email_enabled: bool = Field(default=True, description="Email уведомления")
    push_enabled: bool = Field(default=True, description="Push уведомления")
    in_app_enabled: bool = Field(default=True, description="In-app уведомления")
    
    quiet_hours_start: Optional[str] = Field(None, description="Начало тихих часов (HH:MM)", regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, description="Конец тихих часов (HH:MM)", regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")


class NotificationPreferencesCreate(NotificationPreferencesBase):
    """Схема для создания настроек уведомлений"""
    user_id: int = Field(..., description="ID пользователя")


class NotificationPreferencesUpdate(BaseModel):
    """Схема для обновления настроек уведомлений"""
    system_notifications: Optional[bool] = None
    assignment_notifications: Optional[bool] = None
    grade_notifications: Optional[bool] = None
    deadline_notifications: Optional[bool] = None
    reminder_notifications: Optional[bool] = None
    feedback_notifications: Optional[bool] = None
    schedule_notifications: Optional[bool] = None
    announcement_notifications: Optional[bool] = None
    
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    
    quiet_hours_start: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")


class NotificationPreferencesResponse(NotificationPreferencesBase):
    """Схема для возврата настроек уведомлений"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    """Схема для списка уведомлений с пагинацией"""
    notifications: List[InAppNotificationResponse]
    total: int = Field(..., description="Общее количество уведомлений")
    unread_count: int = Field(..., description="Количество непрочитанных")
    page: int = Field(..., description="Текущая страница")
    per_page: int = Field(..., description="Элементов на странице")
    has_next: bool = Field(..., description="Есть ли следующая страница")
    has_prev: bool = Field(..., description="Есть ли предыдущая страница")


class NotificationStatsResponse(BaseModel):
    """Схема для статистики уведомлений"""
    total_notifications: int = Field(..., description="Всего уведомлений")
    unread_count: int = Field(..., description="Непрочитанных")
    read_count: int = Field(..., description="Прочитанных")
    archived_count: int = Field(..., description="Архивированных")
    by_type: Dict[str, int] = Field(..., description="Распределение по типам")
    by_priority: Dict[str, int] = Field(..., description="Распределение по приоритетам")
    recent_count: int = Field(..., description="Уведомлений за последние 24 часа")


class BulkNotificationAction(BaseModel):
    """Схема для массовых действий с уведомлениями"""
    notification_ids: List[int] = Field(..., description="Список ID уведомлений")
    action: str = Field(..., description="Действие: mark_read, mark_unread, archive, delete")


class BulkNotificationResponse(BaseModel):
    """Результат массового действия"""
    updated_count: int = Field(..., description="Количество обновленных уведомлений")
    errors: List[str] = Field(default_factory=list, description="Ошибки при обработке")


class NotificationCreateRequest(BaseModel):
    """Схема для создания уведомления через API"""
    recipients: List[int] = Field(..., description="Список ID получателей")
    title: str = Field(..., description="Заголовок уведомления")
    message: str = Field(..., description="Текст уведомления")
    notification_type: NotificationType = Field(default=NotificationType.system)
    priority: NotificationPriority = Field(default=NotificationPriority.normal)
    metadata: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    # Связанные объекты
    assignment_id: Optional[int] = None
    course_id: Optional[int] = None
    grade_id: Optional[int] = None
    schedule_id: Optional[int] = None