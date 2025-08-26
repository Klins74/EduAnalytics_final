from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.db.base import Base


class ReminderType(str, Enum):
    SCHEDULE_UPCOMING = "schedule_upcoming"  # Напоминание о предстоящем занятии
    SCHEDULE_CANCELLED = "schedule_cancelled"  # Уведомление об отмене
    SCHEDULE_CHANGED = "schedule_changed"  # Уведомление об изменении
    ASSIGNMENT_DUE = "assignment_due"  # Напоминание о дедлайне задания


class ReminderInterval(str, Enum):
    MINUTES_15 = "15m"  # За 15 минут
    HOUR_1 = "1h"  # За час
    HOURS_2 = "2h"  # За 2 часа
    DAY_1 = "1d"  # За день
    DAYS_3 = "3d"  # За 3 дня
    WEEK_1 = "1w"  # За неделю


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class ReminderSettings(Base):
    """Настройки напоминаний для пользователя."""
    __tablename__ = "reminder_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reminder_type = Column(SQLEnum(ReminderType), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    interval_before = Column(SQLEnum(ReminderInterval), default=ReminderInterval.HOUR_1, nullable=False)
    notification_channel = Column(SQLEnum(NotificationChannel), default=NotificationChannel.EMAIL, nullable=False)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Связи
    user = relationship("User", back_populates="reminder_settings")

    def __repr__(self):
        return f"<ReminderSettings(user_id={self.user_id}, type={self.reminder_type}, interval={self.interval_before})>"


class ScheduledReminder(Base):
    """Запланированные напоминания для отправки."""
    __tablename__ = "scheduled_reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)  # Может быть None для других типов
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True)
    reminder_type = Column(SQLEnum(ReminderType), nullable=False)
    notification_channel = Column(SQLEnum(NotificationChannel), nullable=False)
    
    # Время отправки
    send_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    is_sent = Column(Boolean, default=False, nullable=False)
    
    # Содержимое уведомления
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=False)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Связи
    user = relationship("User")
    schedule = relationship("Schedule")
    assignment = relationship("Assignment")

    def __repr__(self):
        return f"<ScheduledReminder(id={self.id}, user_id={self.user_id}, type={self.reminder_type}, send_at={self.send_at})>"
