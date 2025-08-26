from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    """Схема для создания уведомления."""
    event_type: str = Field(..., description="Тип события уведомления")
    data: Dict[str, Any] = Field(..., description="Данные уведомления")
    channels: Optional[List[str]] = Field(None, description="Каналы доставки")
    priority: Optional[str] = Field(None, description="Приоритет уведомления")
    recipients: Optional[List[Dict[str, Any]]] = Field(None, description="Получатели уведомления")
    scheduled_at: Optional[datetime] = Field(None, description="Время запланированной отправки")


class NotificationResponse(BaseModel):
    """Схема ответа уведомления."""
    id: int
    event_type: str
    data: Dict[str, Any]
    channels: List[str]
    priority: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    results: Dict[str, bool]
    
    model_config = {
        "from_attributes": True
    }


class NotificationPreferences(BaseModel):
    """Схема предпочтений пользователя по уведомлениям."""
    user_id: int
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    webhook_enabled: bool = True
    in_app_enabled: bool = True
    quiet_hours_start: Optional[str] = None  # HH:MM
    quiet_hours_end: Optional[str] = None    # HH:MM
    timezone: str = "UTC"
    
    model_config = {
        "from_attributes": True
    }


class NotificationTemplate(BaseModel):
    """Схема шаблона уведомления."""
    id: str
    name: str
    description: str
    event_type: str
    default_channels: List[str]
    default_priority: str
    variables: List[str]
    is_active: bool = True


class NotificationStats(BaseModel):
    """Схема статистики уведомлений."""
    total_sent: int
    total_failed: int
    by_channel: Dict[str, Dict[str, int]]
    by_priority: Dict[str, int]
    by_event_type: Dict[str, int]
    success_rate: float = 0.0


class NotificationChannel(BaseModel):
    """Схема канала уведомлений."""
    name: str
    is_enabled: bool
    config: Dict[str, Any]
    last_test: Optional[datetime] = None
    status: str = "unknown"


class NotificationTest(BaseModel):
    """Схема для тестирования уведомлений."""
    channel: str
    recipient: str
    test_data: Optional[Dict[str, Any]] = None
