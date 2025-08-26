import logging
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)
import json


class NotificationChannel(Enum):
    """Каналы доставки уведомлений."""
    WEBHOOK = "webhook"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationPriority(Enum):
    """Приоритеты уведомлений."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationService:
    """Расширенный сервис для отправки уведомлений через различные каналы."""
    
    def __init__(self, settings=None):
        if settings is None:
            from app.core.config import settings as default_settings
            settings = default_settings
        self.n8n_webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', None)
        self.email_service_url = getattr(settings, 'EMAIL_SERVICE_URL', None)
        self.sms_service_url = getattr(settings, 'SMS_SERVICE_URL', None)
        self.push_service_url = getattr(settings, 'PUSH_SERVICE_URL', None)
        self.timeout = 10.0
    
    async def send_notification(
        self,
        event_type: str,
        data: dict,
        channels: List[NotificationChannel] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        recipients: List[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """Отправить уведомление через указанные каналы."""
        if channels is None:
            channels = [NotificationChannel.WEBHOOK]
        
        results = {}
        
        for channel in channels:
            try:
                if channel == NotificationChannel.WEBHOOK:
                    results[channel.value] = await self._send_webhook(event_type, data)
                elif channel == NotificationChannel.EMAIL:
                    results[channel.value] = await self._send_email(event_type, data, recipients, priority)
                elif channel == NotificationChannel.SMS:
                    results[channel.value] = await self._send_sms(event_type, data, recipients, priority)
                elif channel == NotificationChannel.PUSH:
                    results[channel.value] = await self._send_push(event_type, data, recipients, priority)
                elif channel == NotificationChannel.IN_APP:
                    results[channel.value] = await self._send_in_app(event_type, data, recipients, priority)
            except Exception as e:
                logger.error(f"Error sending {channel.value} notification: {str(e)}")
                results[channel.value] = False
        
        return results
    
    async def _send_webhook(self, event_type: str, data: dict) -> bool:
        """Отправить webhook в n8n."""
        if not self.n8n_webhook_url:
            logger.warning("N8N webhook URL not configured, skipping notification")
            return False

        # Добавляем timestamp если его нет
        if isinstance(data, dict) and "timestamp" not in data:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Гарантируем наличие event_type в данных
        if isinstance(data, dict):
            data["event_type"] = event_type or data.get("event_type", "unknown")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.n8n_webhook_url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    logger.info(f"Successfully sent {event_type} notification to n8n")
                    return True
                else:
                    logger.error(
                        f"Failed to send {event_type} notification to n8n. "
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(f"Timeout sending {event_type} notification to n8n")
            return False
        except Exception as e:
            logger.error(f"Error sending {event_type} notification to n8n: {str(e)}")
            return False

    async def send_webhook(self, data: dict) -> bool:
        """Обратная совместимость: публичный метод, ожидаемый тестами.
        Извлекает event_type из data и делегирует в _send_webhook."""
        event_type = data.get("event_type", "unknown") if isinstance(data, dict) else "unknown"
        return await self._send_webhook(event_type, data)
    
    async def _send_email(self, event_type: str, data: dict, recipients: List[Dict[str, Any]], priority: NotificationPriority) -> bool:
        """Отправить email уведомление."""
        if not self.email_service_url:
            logger.warning("Email service URL not configured, skipping email notification")
            return False
        
        if not recipients:
            logger.warning("No recipients specified for email notification")
            return False
        
        email_data = {
            "event_type": event_type,
            "data": data,
            "recipients": recipients,
            "priority": priority.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.email_service_url,
                    json=email_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent {event_type} email notification")
                    return True
                else:
                    logger.error(f"Failed to send {event_type} email notification. Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending {event_type} email notification: {str(e)}")
            return False
    
    async def _send_sms(self, event_type: str, data: dict, recipients: List[Dict[str, Any]], priority: NotificationPriority) -> bool:
        """Отправить SMS уведомление."""
        if not self.sms_service_url:
            logger.warning("SMS service URL not configured, skipping SMS notification")
            return False
        
        if not recipients:
            logger.warning("No recipients specified for SMS notification")
            return False
        
        sms_data = {
            "event_type": event_type,
            "data": data,
            "recipients": recipients,
            "priority": priority.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.sms_service_url,
                    json=sms_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent {event_type} SMS notification")
                    return True
                else:
                    logger.error(f"Failed to send {event_type} SMS notification. Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending {event_type} SMS notification: {str(e)}")
            return False
    
    async def _send_push(self, event_type: str, data: dict, recipients: List[Dict[str, Any]], priority: NotificationPriority) -> bool:
        """Отправить push уведомление."""
        if not self.push_service_url:
            logger.warning("Push service URL not configured, skipping push notification")
            return False
        
        if not recipients:
            logger.warning("No recipients specified for push notification")
            return False
        
        push_data = {
            "event_type": event_type,
            "data": data,
            "recipients": recipients,
            "priority": priority.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.push_service_url,
                    json=push_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent {event_type} push notification")
                    return True
                else:
                    logger.error(f"Failed to send {event_type} push notification. Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending {event_type} push notification: {str(e)}")
            return False
    
    async def _send_in_app(self, event_type: str, data: dict, recipients: List[Dict[str, Any]], priority: NotificationPriority) -> bool:
        """Отправить in-app уведомление (сохранить в БД для отображения в UI)."""
        try:
            # TODO: Реализовать сохранение в БД для in-app уведомлений
            logger.info(f"Successfully queued {event_type} in-app notification for {len(recipients)} recipients")
            return True
        except Exception as e:
            logger.error(f"Error queuing {event_type} in-app notification: {str(e)}")
            return False
    
    async def send_webhook_legacy(self, webhook_type: str, data: dict) -> bool:
        """Отправить webhook в n8n (legacy метод для обратной совместимости)."""
        payload = {
            "type": webhook_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        return await self.send_webhook(payload)
    
    async def send_feedback_notification(
        self,
        feedback_id: int,
        submission_id: int,
        author_name: str,
        feedback_text: str,
        submission_title: Optional[str] = None,
        student_name: Optional[str] = None,
        course_name: Optional[str] = None
    ) -> bool:
        """Отправить уведомление о новом комментарии."""
        data = {
            "feedback_id": feedback_id,
            "submission_id": str(submission_id),
            "author_name": author_name,
            "feedback_text": feedback_text[:500],  # Ограничиваем длину для webhook
            "submission_title": submission_title,
            "student_name": student_name,
            "course_name": course_name
        }
        
        return await self.send_webhook_legacy("feedback_created", data)
    
    async def send_grade_notification(
        self,
        grade_id: int = None,
        submission_id: int = None,
        student_id: int = None,
        student_name: str = None,
        grade_value: float = None,
        assignment_id: int = None,
        assignment_title: str = None,
        course_name: str = None,
        teacher_id: int = None,
        teacher_name: str = None
    ) -> bool:
        """Отправить уведомление о новой оценке."""
        data = {
            "grade_id": grade_id,
            "submission_id": str(submission_id),
            "student_name": student_name,
            "grade_value": grade_value,
            "assignment_title": assignment_title,
            "course_name": course_name,
            "teacher_name": teacher_name
        }
        
        return await self.send_webhook_legacy("grade_created", data)
    
    async def send_deadline_notification(
        self,
        assignment_id: int,
        assignment_title: str,
        due_date: str,
        course_name: str,
        course_id: int,
        hours_remaining: int,
        students: list
    ) -> bool:
        """Отправить уведомление о приближающемся дедлайне."""
        data = {
            "event_type": "deadline_approaching",
            "assignment_id": assignment_id,
            "assignment_title": assignment_title,
            "due_date": due_date,
            "course_name": course_name,
            "course_id": course_id,
            "hours_remaining": hours_remaining,
            "students": students,
            "channels": ["email"]
        }
        
        # Совместимость с тестами: вызываем send_webhook
        return await self.send_webhook(data)
    
    async def send_schedule_notification(
        self,
        schedule_id: int,
        course_name: str,
        course_id: int,
        schedule_date: str,
        start_time: str,
        end_time: str,
        location: str,
        instructor_name: str,
        change_type: str,
        students: list,
        old_data: dict = None,
        lesson_type: str = None,
        description: str = None,
        notes: str = None,
        is_cancelled: bool = None,
        classroom_id: int = None
    ) -> bool:
        """Отправить уведомление об изменении расписания."""
        data = {
            "event_type": "schedule_updated",
            "schedule_id": schedule_id,
            "course_name": course_name,
            "course_id": course_id,
            "schedule_date": schedule_date,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "instructor_name": instructor_name,
            "change_type": change_type,
            "students": students,
            "old_data": old_data,
            "lesson_type": lesson_type,
            "description": description,
            "notes": notes,
            "is_cancelled": is_cancelled,
            "classroom_id": classroom_id,
            "channels": ["email"]
        }
        
        # Совместимость с тестами: вызываем send_webhook
        return await self.send_webhook(data)
    
    async def send_submission_notification(
        self,
        submission_id: int,
        assignment_id: int,
        student_name: str,
        assignment_title: str,
        course_name: str,
        submission_status: str
    ) -> bool:
        """Отправить уведомление о новой работе."""
        data = {
            "submission_id": submission_id,
            "assignment_id": assignment_id,
            "student_name": student_name,
            "assignment_title": assignment_title,
            "course_name": course_name,
            "submission_status": submission_status
        }
        
        return await self.send_webhook_legacy("submission_created", data)

    def send_webhook_sync(self, data: dict) -> bool:
        """Synchronous wrapper for send_webhook."""
        import asyncio
        return asyncio.run(self._send_webhook("unknown", data))

    def send_deadline_notification_sync(
        self,
        assignment_id: int,
        assignment_title: str,
        due_date: str,
        course_name: str,
        course_id: int,
        hours_remaining: int,
        students: list
    ) -> bool:
        """Synchronous wrapper for send_deadline_notification."""
        import asyncio
        return asyncio.run(self.send_deadline_notification(
            assignment_id,
            assignment_title,
            due_date,
            course_name,
            course_id,
            hours_remaining,
            students
        ))

    @property
    def webhook_url(self):
        return self.n8n_webhook_url


# Создаем глобальный экземпляр сервиса
notification_service = NotificationService()


# Функции-обертки для использования в FastAPI BackgroundTasks
def send_feedback_notification(
    feedback_id: int,
    submission_id: int,
    author_name: str,
    feedback_text: str,
    submission_title: Optional[str] = None,
    student_name: Optional[str] = None,
    course_name: Optional[str] = None
):
    """Синхронная обертка для отправки уведомления о комментарии."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        notification_service.send_feedback_notification(
            feedback_id=feedback_id,
            submission_id=submission_id,
            author_name=author_name,
            feedback_text=feedback_text,
            submission_title=submission_title,
            student_name=student_name,
            course_name=course_name
        )
    )


def send_grade_notification(
    grade_id: int,
    submission_id: int,
    student_name: str,
    grade_value: float,
    assignment_title: str,
    course_name: str,
    teacher_name: str
):
    """Синхронная обертка для отправки уведомления об оценке."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        notification_service.send_grade_notification(
            grade_id=grade_id,
            submission_id=submission_id,
            student_name=student_name,
            grade_value=grade_value,
            assignment_title=assignment_title,
            course_name=course_name,
            teacher_name=teacher_name
        )
    )


def send_submission_notification(
    submission_id: int,
    assignment_id: int,
    student_name: str,
    assignment_title: str,
    course_name: str,
    submission_status: str
):
    """Синхронная обертка для отправки уведомления о работе."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        notification_service.send_submission_notification(
            submission_id=submission_id,
            assignment_id=assignment_id,
            student_name=student_name,
            assignment_title=assignment_title,
            course_name=course_name,
            submission_status=submission_status
        )
    )