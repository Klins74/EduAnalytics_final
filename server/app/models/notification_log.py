from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db.base import Base
from enum import Enum


class NotificationLogStatus(str, Enum):
    """Статусы отправки уведомлений"""
    pending = "pending"
    sent = "sent"
    failed = "failed"
    retrying = "retrying"


class NotificationLog(Base):
    """
    Модель для логирования отправленных уведомлений.
    Используется для сбора статистики и отслеживания доставки.
    """
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Основная информация
    event_type = Column(String(100), nullable=False, index=True)
    channel = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), nullable=False, default="normal", index=True)
    
    # Статус отправки
    status = Column(String(20), nullable=False, default=NotificationLogStatus.pending, index=True)
    
    # Получатели (количество)
    recipients_count = Column(Integer, nullable=False, default=0)
    successful_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    
    # Дополнительная информация
    error_message = Column(Text, nullable=True)
    response_data = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    # Время выполнения
    processing_time_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, event_type='{self.event_type}', channel='{self.channel}', status='{self.status}')>"
    
    @property
    def success_rate(self) -> float:
        """Процент успешно отправленных уведомлений"""
        if self.recipients_count == 0:
            return 0.0
        return (self.successful_count / self.recipients_count) * 100
    
    @property
    def is_completed(self) -> bool:
        """Завершена ли отправка (успешно или с ошибкой)"""
        return self.status in [NotificationLogStatus.sent, NotificationLogStatus.failed]

