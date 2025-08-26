from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.core.database import get_db
from app.schemas.webhook import (
    WebhookNotifyRequest,
    WebhookResponse,
    WebhookEventType,
    DeadlineNotificationData,
    GradeNotificationData,
    FeedbackNotificationData,
    ScheduleNotificationData
)
from app.services.notification import NotificationService
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/notify", response_model=WebhookResponse)
async def webhook_n8n_notify(
    request: WebhookNotifyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint для получения уведомлений от n8n.
    
    Этот endpoint принимает различные типы событий и обрабатывает их
    в фоновом режиме для отправки уведомлений пользователям.
    """
    try:
        logger.info(f"Получен webhook запрос: {request.event_type}")
        
        # Валидация данных в зависимости от типа события
        validated_data = await _validate_event_data(request, db)
        
        # Добавляем задачу в фоновую обработку
        background_tasks.add_task(
            _process_webhook_event,
            request.event_type,
            validated_data,
            request.notification_channels or ["email"],
            db
        )
        
        return WebhookResponse(
            success=True,
            message=f"Событие {request.event_type} принято к обработке",
            event_id=f"{request.event_type}_{datetime.now().timestamp()}"
        )
        
    except ValueError as e:
        logger.error(f"Ошибка валидации webhook данных: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/test/notify", response_model=WebhookResponse)
async def test_webhook_notify(
    request: WebhookNotifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Тестовый endpoint для проверки webhook уведомлений.
    Требует аутентификации.
    """
    try:
        logger.info(f"Тестовый webhook запрос от пользователя {current_user.id}: {request.event_type}")
        
        # Валидация данных
        validated_data = await _validate_event_data(request, db)
        
        # Обработка в синхронном режиме для тестирования
        await _process_webhook_event(
            request.event_type,
            validated_data,
            request.notification_channels or ["email"],
            db
        )
        
        return WebhookResponse(
            success=True,
            message=f"Тестовое событие {request.event_type} обработано",
            event_id=f"test_{request.event_type}_{datetime.now().timestamp()}"
        )
        
    except Exception as e:
        logger.error(f"Ошибка тестового webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _validate_event_data(request: WebhookNotifyRequest, db: Session) -> Dict[str, Any]:
    """
    Валидация данных события в зависимости от типа.
    """
    try:
        if request.event_type == WebhookEventType.DEADLINE_APPROACHING:
            data = DeadlineNotificationData(**request.data)
            return data.model_dump()
            
        elif request.event_type == WebhookEventType.GRADE_CREATED:
            data = GradeNotificationData(**request.data)
            return data.model_dump()
            
        elif request.event_type == WebhookEventType.FEEDBACK_CREATED:
            data = FeedbackNotificationData(**request.data)
            return data.model_dump()
            
        elif request.event_type == WebhookEventType.SCHEDULE_UPDATED:
            data = ScheduleNotificationData(**request.data)
            return data.model_dump()
            
        elif request.event_type == WebhookEventType.TEST_NOTIFICATION:
            # Для тестового события просто возвращаем данные как есть
            return request.data
            
        else:
            raise ValueError(f"Неподдерживаемый тип события: {request.event_type}")
            
    except Exception as e:
        raise ValueError(f"Ошибка валидации данных для {request.event_type}: {str(e)}")


async def _process_webhook_event(
    event_type: WebhookEventType,
    data: Dict[str, Any],
    channels: list,
    db: Session
):
    """
    Обработка webhook события.
    """
    try:
        notification_service = NotificationService()
        
        if event_type == WebhookEventType.DEADLINE_APPROACHING:
            await _process_deadline_notification(notification_service, data, channels)
            
        elif event_type == WebhookEventType.GRADE_CREATED:
            await _process_grade_notification(notification_service, data, channels)
            
        elif event_type == WebhookEventType.FEEDBACK_CREATED:
            await _process_feedback_notification(notification_service, data, channels)
            
        elif event_type == WebhookEventType.SCHEDULE_UPDATED:
            await _process_schedule_notification(notification_service, data, channels)
            
        elif event_type == WebhookEventType.TEST_NOTIFICATION:
            # Для тестового события просто логируем
            logger.info(f"Обработано тестовое событие с данными: {data}")
            
        logger.info(f"Событие {event_type} успешно обработано")
        
    except Exception as e:
        logger.error(f"Ошибка обработки события {event_type}: {str(e)}")
        raise


async def _process_deadline_notification(
    service: NotificationService, 
    data: Dict[str, Any], 
    channels: list
):
    """Обработка уведомления о дедлайне."""
    webhook_data = {
        "event_type": "deadline_approaching",
        "assignment_title": data["assignment_title"],
        "due_date": data["due_date"],
        "course_name": data["course_name"],
        "hours_remaining": data["hours_remaining"],
        "students": data["students"],
        "channels": channels
    }
    await service.send_webhook(webhook_data)


async def _process_grade_notification(
    service: NotificationService, 
    data: Dict[str, Any], 
    channels: list
):
    """Обработка уведомления о новой оценке."""
    webhook_data = {
        "event_type": "grade_created",
        "student_name": data["student_name"],
        "student_email": data["student_email"],
        "assignment_title": data["assignment_title"],
        "grade_value": data["grade_value"],
        "max_grade": data.get("max_grade"),
        "course_name": data["course_name"],
        "teacher_name": data["teacher_name"],
        "channels": channels
    }
    await service.send_webhook(webhook_data)


async def _process_feedback_notification(
    service: NotificationService, 
    data: Dict[str, Any], 
    channels: list
):
    """Обработка уведомления о новом комментарии."""
    webhook_data = {
        "event_type": "feedback_created",
        "author_name": data["author_name"],
        "feedback_text": data["feedback_text"],
        "student_name": data.get("student_name"),
        "student_email": data.get("student_email"),
        "course_name": data.get("course_name"),
        "submission_title": data.get("submission_title"),
        "channels": channels
    }
    await service.send_webhook(webhook_data)


async def _process_schedule_notification(
    service: NotificationService, 
    data: Dict[str, Any], 
    channels: list
):
    """Обработка уведомления об изменении расписания."""
    webhook_data = {
        "event_type": "schedule_updated",
        "course_name": data["course_name"],
        "schedule_date": data["schedule_date"],
        "start_time": data["start_time"],
        "end_time": data["end_time"],
        "location": data["location"],
        "instructor_name": data["instructor_name"],
        "change_type": data["change_type"],
        "students": data["students"],
        "old_data": data.get("old_data"),
        "channels": channels
    }
    await service.send_webhook(webhook_data)


@router.get("/health")
async def webhook_health():
    """Проверка состояния webhook сервиса."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}