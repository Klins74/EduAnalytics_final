from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from enum import Enum


class NotificationStatus(str, Enum):
    """Статусы уведомлений"""
    unread = "unread"
    read = "read"
    archived = "archived"


class NotificationType(str, Enum):
    """Типы уведомлений"""
    system = "system"
    assignment = "assignment"
    grade = "grade"
    deadline = "deadline"
    reminder = "reminder"
    feedback = "feedback"
    schedule = "schedule"
    announcement = "announcement"


class NotificationPriority(str, Enum):
    """Приоритеты уведомлений"""
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class InAppNotification(Base):
    """
    Модель для хранения in-app уведомлений пользователей.
    Используется для персистентного хранения уведомлений в интерфейсе.
    """
    __tablename__ = "in_app_notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Получатель уведомления
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Основная информация
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, nullable=False, default=NotificationType.system)
    priority = Column(String, nullable=False, default=NotificationPriority.normal)
    
    # Статус
    status = Column(String, nullable=False, default=NotificationStatus.unread)
    
    # Дополнительные данные (JSON)
    extra_data = Column(JSON, nullable=True)
    
    # Ссылки на связанные объекты (опционально)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    grade_id = Column(Integer, ForeignKey("grades.id"), nullable=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)
    
    # URL для действия (опционально)
    action_url = Column(String(512), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    read_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Автоматическое удаление
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    assignment = relationship("Assignment", backref="notifications")
    course = relationship("Course", backref="notifications")
    grade = relationship("Grade", backref="notifications")
    schedule = relationship("Schedule", backref="notifications")
    
    def __repr__(self):
        return f"<InAppNotification(id={self.id}, user_id={self.user_id}, title='{self.title}', status={self.status})>"
    
    @property
    def is_read(self) -> bool:
        """Проверка, прочитано ли уведомление"""
        return self.status == NotificationStatus.read
    
    @property
    def is_archived(self) -> bool:
        """Проверка, архивировано ли уведомление"""
        return self.status == NotificationStatus.archived
    
    @property
    def is_expired(self) -> bool:
        """Проверка, истекло ли уведомление"""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)
    
    def mark_as_read(self):
        """Отметить уведомление как прочитанное"""
        if self.status == NotificationStatus.unread:
            self.status = NotificationStatus.read
            self.read_at = func.now()
    
    def archive(self):
        """Архивировать уведомление"""
        self.status = NotificationStatus.archived
        self.archived_at = func.now()


class NotificationPreferences(Base):
    """
    Модель для хранения пользовательских настроек уведомлений.
    Позволяет пользователям настраивать, какие типы уведомлений они хотят получать.
    """
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Настройки по типам уведомлений
    system_notifications = Column(Boolean, default=True)
    assignment_notifications = Column(Boolean, default=True)
    grade_notifications = Column(Boolean, default=True)
    deadline_notifications = Column(Boolean, default=True)
    reminder_notifications = Column(Boolean, default=True)
    feedback_notifications = Column(Boolean, default=True)
    schedule_notifications = Column(Boolean, default=True)
    announcement_notifications = Column(Boolean, default=True)
    
    # Настройки каналов доставки
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    
    # Настройки времени
    quiet_hours_start = Column(String(5), nullable=True)  # Формат "22:00"
    quiet_hours_end = Column(String(5), nullable=True)    # Формат "08:00"
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")
    
    def __repr__(self):
        return f"<NotificationPreferences(user_id={self.user_id})>"
    
    def is_notification_enabled(self, notification_type: NotificationType) -> bool:
        """Проверить, включен ли определенный тип уведомлений"""
        type_mapping = {
            NotificationType.system: self.system_notifications,
            NotificationType.assignment: self.assignment_notifications,
            NotificationType.grade: self.grade_notifications,
            NotificationType.deadline: self.deadline_notifications,
            NotificationType.reminder: self.reminder_notifications,
            NotificationType.feedback: self.feedback_notifications,
            NotificationType.schedule: self.schedule_notifications,
            NotificationType.announcement: self.announcement_notifications,
        }
        return type_mapping.get(notification_type, True)
    
    def is_in_quiet_hours(self) -> bool:
        """Проверить, находимся ли мы в тихих часах"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        from datetime import datetime, time
        now = datetime.now().time()
        start = datetime.strptime(self.quiet_hours_start, "%H:%M").time()
        end = datetime.strptime(self.quiet_hours_end, "%H:%M").time()
        
        if start <= end:
            return start <= now <= end
        else:  # Тихие часы переходят через полночь
            return now >= start or now <= end

