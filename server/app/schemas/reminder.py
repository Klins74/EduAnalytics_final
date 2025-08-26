from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class ReminderType(str, Enum):
    SCHEDULE_UPCOMING = "schedule_upcoming"
    SCHEDULE_CANCELLED = "schedule_cancelled"
    SCHEDULE_CHANGED = "schedule_changed"
    ASSIGNMENT_DUE = "assignment_due"


class ReminderInterval(str, Enum):
    MINUTES_15 = "15m"
    HOUR_1 = "1h"
    HOURS_2 = "2h"
    DAY_1 = "1d"
    DAYS_3 = "3d"
    WEEK_1 = "1w"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


# Схемы для настроек напоминаний
class ReminderSettingsBase(BaseModel):
    reminder_type: ReminderType = Field(..., description="Тип напоминания")
    is_enabled: bool = Field(default=True, description="Включено ли напоминание")
    interval_before: ReminderInterval = Field(default=ReminderInterval.HOUR_1, description="Интервал до события")
    notification_channel: NotificationChannel = Field(default=NotificationChannel.EMAIL, description="Канал уведомления")


class ReminderSettingsCreate(ReminderSettingsBase):
    user_id: int = Field(..., description="ID пользователя")


class ReminderSettingsUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    interval_before: Optional[ReminderInterval] = None
    notification_channel: Optional[NotificationChannel] = None


class ReminderSettingsResponse(ReminderSettingsBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# Схемы для запланированных напоминаний
class ScheduledReminderBase(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    reminder_type: ReminderType = Field(..., description="Тип напоминания")
    notification_channel: NotificationChannel = Field(..., description="Канал уведомления")
    send_at: datetime = Field(..., description="Время отправки")
    title: str = Field(..., max_length=200, description="Заголовок уведомления")
    message: str = Field(..., max_length=1000, description="Текст уведомления")


class ScheduledReminderCreate(ScheduledReminderBase):
    schedule_id: Optional[int] = None
    assignment_id: Optional[int] = None


class ScheduledReminderResponse(ScheduledReminderBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    schedule_id: Optional[int] = None
    assignment_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    is_sent: bool
    created_at: datetime
    updated_at: datetime


# Схемы для пользовательских настроек
class UserReminderPreferences(BaseModel):
    """Предпочтения пользователя по напоминаниям"""
    schedule_upcoming_enabled: bool = Field(default=True, description="Напоминания о предстоящих занятиях")
    schedule_upcoming_interval: ReminderInterval = Field(default=ReminderInterval.HOUR_1)
    schedule_upcoming_channel: NotificationChannel = Field(default=NotificationChannel.EMAIL)
    
    schedule_changes_enabled: bool = Field(default=True, description="Уведомления об изменениях расписания")
    schedule_changes_channel: NotificationChannel = Field(default=NotificationChannel.EMAIL)
    
    assignment_due_enabled: bool = Field(default=True, description="Напоминания о дедлайнах")
    assignment_due_interval: ReminderInterval = Field(default=ReminderInterval.DAY_1)
    assignment_due_channel: NotificationChannel = Field(default=NotificationChannel.EMAIL)


class ReminderTestRequest(BaseModel):
    """Запрос на отправку тестового напоминания"""
    reminder_type: ReminderType = Field(..., description="Тип напоминания")
    notification_channel: NotificationChannel = Field(..., description="Канал уведомления")
    test_message: Optional[str] = Field(None, description="Тестовое сообщение")
