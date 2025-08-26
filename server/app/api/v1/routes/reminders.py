from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_async_session
from app.crud.reminder import reminder_crud
from app.services.reminder_service import reminder_service
from app.schemas.reminder import (
    ReminderSettingsResponse, 
    ReminderSettingsUpdate, 
    UserReminderPreferences,
    ScheduledReminderResponse,
    ReminderTestRequest
)
from app.models.reminder import ReminderType
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/settings", response_model=List[ReminderSettingsResponse])
async def get_reminder_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получить настройки напоминаний текущего пользователя"""
    settings = await reminder_crud.get_user_reminder_settings(db, current_user.id)
    return settings


@router.get("/settings/{reminder_type}", response_model=ReminderSettingsResponse)
async def get_reminder_setting(
    reminder_type: ReminderType,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получить конкретную настройку напоминания"""
    setting = await reminder_crud.get_user_reminder_setting(db, current_user.id, reminder_type)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Настройка напоминания {reminder_type} не найдена"
        )
    return setting


@router.put("/settings/{reminder_type}", response_model=ReminderSettingsResponse)
async def update_reminder_setting(
    reminder_type: ReminderType,
    settings: ReminderSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Обновить настройку напоминания"""
    updated_setting = await reminder_crud.create_or_update_reminder_setting(
        db, current_user.id, reminder_type, settings
    )
    return updated_setting


@router.put("/preferences", response_model=List[ReminderSettingsResponse])
async def update_reminder_preferences(
    preferences: UserReminderPreferences,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Обновить все предпочтения напоминаний пользователя"""
    updated_settings = await reminder_crud.update_user_preferences(db, current_user.id, preferences)
    return updated_settings


@router.get("/upcoming", response_model=List[ScheduledReminderResponse])
async def get_upcoming_reminders(
    days_ahead: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получить предстоящие напоминания пользователя"""
    reminders = await reminder_service.get_user_upcoming_reminders(db, current_user.id, days_ahead)
    return reminders


@router.post("/test")
async def send_test_reminder(
    test_request: ReminderTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Отправить тестовое напоминание"""
    success = await reminder_service.send_test_reminder(db, current_user.id, test_request)
    
    if success:
        return {"message": "Тестовое напоминание отправлено успешно"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки тестового напоминания"
        )


@router.post("/process")
async def process_pending_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Принудительно обработать готовые к отправке напоминания (только для админов)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступно только администраторам"
        )
    
    sent_count = await reminder_service.process_pending_reminders(db)
    return {"message": f"Обработано {sent_count} напоминаний"}


@router.get("/stats")
async def get_reminder_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получить статистику напоминаний пользователя"""
    # Простая статистика
    settings = await reminder_crud.get_user_reminder_settings(db, current_user.id)
    upcoming = await reminder_service.get_user_upcoming_reminders(db, current_user.id, 30)
    
    stats = {
        "total_settings": len(settings),
        "enabled_settings": len([s for s in settings if s.is_enabled]),
        "upcoming_reminders": len(upcoming),
        "settings_by_type": {
            setting.reminder_type.value: {
                "enabled": setting.is_enabled,
                "interval": setting.interval_before.value,
                "channel": setting.notification_channel.value
            }
            for setting in settings
        }
    }
    
    return stats
