from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session as get_db
from app.core.security import require_role
from app.services.notification import NotificationService, NotificationChannel, NotificationPriority
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationPreferences,
    NotificationTemplate,
    NotificationStats
)

router = APIRouter()

notification_service = NotificationService()


@router.post("/send", response_model=dict)
async def send_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "teacher"]))
):
    """Отправить уведомление через указанные каналы."""
    try:
        # Определяем каналы доставки
        channels = []
        if notification.channels:
            for channel_str in notification.channels:
                try:
                    channels.append(NotificationChannel(channel_str))
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid notification channel: {channel_str}"
                    )
        else:
            channels = [NotificationChannel.WEBHOOK]
        
        # Определяем приоритет
        priority = NotificationPriority.NORMAL
        if notification.priority:
            try:
                priority = NotificationPriority(notification.priority)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid notification priority: {notification.priority}"
                )
        
        # Отправляем уведомление
        results = await notification_service.send_notification(
            event_type=notification.event_type,
            data=notification.data,
            channels=channels,
            priority=priority,
            recipients=notification.recipients
        )
        
        return {
            "message": "Notification sent successfully",
            "results": results,
            "channels_used": [ch.value for ch in channels],
            "priority": priority.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/send-bulk", response_model=dict)
async def send_bulk_notifications(
    notifications: List[NotificationCreate],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"]))
):
    """Отправить несколько уведомлений одновременно."""
    try:
        results = []
        for notification in notifications:
            channels = []
            if notification.channels:
                for channel_str in notification.channels:
                    try:
                        channels.append(NotificationChannel(channel_str))
                    except ValueError:
                        continue
            
            if not channels:
                channels = [NotificationChannel.WEBHOOK]
            
            priority = NotificationPriority.NORMAL
            if notification.priority:
                try:
                    priority = NotificationPriority(notification.priority)
                except ValueError:
                    priority = NotificationPriority.NORMAL
            
            result = await notification_service.send_notification(
                event_type=notification.event_type,
                data=notification.data,
                channels=channels,
                priority=priority,
                recipients=notification.recipients
            )
            
            results.append({
                "notification_id": notification.id if hasattr(notification, 'id') else None,
                "event_type": notification.event_type,
                "results": result
            })
        
        return {
            "message": f"Sent {len(notifications)} notifications",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk notifications: {str(e)}"
        )


@router.get("/templates", response_model=List[NotificationTemplate])
async def get_notification_templates(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "teacher"]))
):
    """Получить доступные шаблоны уведомлений."""
    templates = [
        {
            "id": "deadline_reminder",
            "name": "Напоминание о дедлайне",
            "description": "Уведомление о приближающемся дедлайне задания",
            "event_type": "deadline_approaching",
            "default_channels": ["email", "webhook"],
            "default_priority": "high",
            "variables": ["assignment_title", "due_date", "course_name", "hours_remaining"]
        },
        {
            "id": "grade_notification",
            "name": "Уведомление об оценке",
            "description": "Уведомление студента о полученной оценке",
            "event_type": "grade_created",
            "default_channels": ["email", "webhook"],
            "default_priority": "normal",
            "variables": ["student_name", "grade_value", "assignment_title", "course_name"]
        },
        {
            "id": "schedule_change",
            "name": "Изменение расписания",
            "description": "Уведомление об изменении расписания занятий",
            "event_type": "schedule_updated",
            "default_channels": ["email", "sms", "webhook"],
            "default_priority": "high",
            "variables": ["course_name", "schedule_date", "start_time", "change_type"]
        },
        {
            "id": "new_assignment",
            "name": "Новое задание",
            "description": "Уведомление о новом задании в курсе",
            "event_type": "assignment_created",
            "default_channels": ["email", "webhook"],
            "default_priority": "normal",
            "variables": ["course_name", "assignment_title", "due_date"]
        }
    ]
    
    return templates


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"]))
):
    """Получить статистику по уведомлениям."""
    # TODO: Реализовать подсчет статистики из БД
    stats = {
        "total_sent": 0,
        "total_failed": 0,
        "by_channel": {
            "webhook": {"sent": 0, "failed": 0},
            "email": {"sent": 0, "failed": 0},
            "sms": {"sent": 0, "failed": 0},
            "push": {"sent": 0, "failed": 0}
        },
        "by_priority": {
            "low": 0,
            "normal": 0,
            "high": 0,
            "urgent": 0
        },
        "by_event_type": {
            "deadline_approaching": 0,
            "grade_created": 0,
            "schedule_updated": 0,
            "assignment_created": 0
        }
    }
    
    return stats


@router.post("/test", response_model=dict)
async def test_notification(
    channel: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"]))
):
    """Отправить тестовое уведомление для проверки настроек."""
    try:
        # Проверяем валидность канала
        try:
            notification_channel = NotificationChannel(channel)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification channel: {channel}"
            )
        
        # Отправляем тестовое уведомление
        test_data = {
            "message": "This is a test notification",
            "timestamp": "2024-01-01T00:00:00Z",
            "user_id": current_user.get("id"),
            "test": True
        }
        
        result = await notification_service.send_notification(
            event_type="test_notification",
            data=test_data,
            channels=[notification_channel],
            priority=NotificationPriority.LOW
        )
        
        return {
            "message": f"Test notification sent via {channel}",
            "success": result.get(channel, False),
            "channel": channel
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )


@router.get("/channels", response_model=List[str])
async def get_available_channels(
    current_user: dict = Depends(require_role(["admin", "teacher"]))
):
    """Получить список доступных каналов уведомлений."""
    return [channel.value for channel in NotificationChannel]


@router.get("/priorities", response_model=List[str])
async def get_available_priorities(
    current_user: dict = Depends(require_role(["admin", "teacher"]))
):
    """Получить список доступных приоритетов уведомлений."""
    return [priority.value for priority in NotificationPriority]
