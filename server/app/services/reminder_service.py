import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.crud.reminder import reminder_crud
from app.services.notification import NotificationService
from app.models.reminder import ScheduledReminder, NotificationChannel, ReminderType
from app.schemas.reminder import ReminderTestRequest

logger = logging.getLogger(__name__)


class ReminderService:
    """Сервис для управления автоматическими напоминаниями"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self._running = False

    async def process_pending_reminders(self, db: AsyncSession) -> int:
        """Обработать все готовые к отправке напоминания"""
        try:
            # Получаем готовые к отправке напоминания
            pending = await reminder_crud.get_pending_reminders(db, limit=100)
            
            sent_count = 0
            for reminder in pending:
                try:
                    success = await self._send_reminder(reminder)
                    if success:
                        await reminder_crud.mark_reminder_sent(db, reminder.id)
                        sent_count += 1
                        logger.info(f"Sent reminder {reminder.id} to user {reminder.user_id}")
                    else:
                        logger.error(f"Failed to send reminder {reminder.id}")
                except Exception as e:
                    logger.error(f"Error sending reminder {reminder.id}: {str(e)}")
            
            if sent_count > 0:
                logger.info(f"Processed {sent_count} reminders")
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error processing reminders: {str(e)}")
            return 0

    async def _send_reminder(self, reminder: ScheduledReminder) -> bool:
        """Отправить конкретное напоминание"""
        try:
            # Подготавливаем данные для уведомления
            notification_data = {
                "user_id": reminder.user_id,
                "title": reminder.title,
                "message": reminder.message,
                "reminder_type": reminder.reminder_type.value,
                "timestamp": datetime.now().isoformat()
            }
            
            # Добавляем специфичные данные в зависимости от типа
            if reminder.schedule_id:
                notification_data["schedule_id"] = reminder.schedule_id
            if reminder.assignment_id:
                notification_data["assignment_id"] = reminder.assignment_id
            
            # Выбираем метод отправки в зависимости от канала
            if reminder.notification_channel == NotificationChannel.EMAIL:
                await self.notification_service.send_notification(
                    notification_type="reminder",
                    data=notification_data,
                    channel="email"
                )
            elif reminder.notification_channel == NotificationChannel.SMS:
                await self.notification_service.send_notification(
                    notification_type="reminder",
                    data=notification_data,
                    channel="sms"
                )
            elif reminder.notification_channel == NotificationChannel.PUSH:
                await self.notification_service.send_notification(
                    notification_type="reminder",
                    data=notification_data,
                    channel="push"
                )
            elif reminder.notification_channel == NotificationChannel.IN_APP:
                await self.notification_service.send_notification(
                    notification_type="reminder",
                    data=notification_data,
                    channel="in_app"
                )
            else:
                # Дефолт - webhook
                await self.notification_service.send_notification(
                    notification_type="reminder",
                    data=notification_data,
                    channel="webhook"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error in _send_reminder: {str(e)}")
            return False

    async def send_test_reminder(
        self, 
        db: AsyncSession, 
        user_id: int, 
        test_request: ReminderTestRequest
    ) -> bool:
        """Отправить тестовое напоминание"""
        try:
            # Создаем тестовое напоминание
            test_message = test_request.test_message or "Это тестовое напоминание от системы EduAnalytics"
            
            notification_data = {
                "user_id": user_id,
                "title": "Тестовое напоминание",
                "message": test_message,
                "reminder_type": test_request.reminder_type.value,
                "timestamp": datetime.now().isoformat(),
                "is_test": True
            }
            
            # Отправляем через выбранный канал
            channel_map = {
                NotificationChannel.EMAIL: "email",
                NotificationChannel.SMS: "sms", 
                NotificationChannel.PUSH: "push",
                NotificationChannel.IN_APP: "in_app"
            }
            
            channel = channel_map.get(test_request.notification_channel, "webhook")
            
            await self.notification_service.send_notification(
                notification_type="test_reminder",
                data=notification_data,
                channel=channel
            )
            
            logger.info(f"Sent test reminder to user {user_id} via {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending test reminder: {str(e)}")
            return False

    async def schedule_reminder_for_new_schedule(
        self, 
        db: AsyncSession, 
        schedule_id: int
    ) -> int:
        """Запланировать напоминания для нового занятия"""
        try:
            from app.crud.schedule import schedule_crud
            
            # Получаем информацию о занятии
            schedule = await schedule_crud.get_with_relations(db, schedule_id)
            if not schedule:
                logger.warning(f"Schedule {schedule_id} not found")
                return 0
            
            # Создаем напоминания
            reminders = await reminder_crud.schedule_reminders_for_schedule(db, schedule)
            
            logger.info(f"Scheduled {len(reminders)} reminders for schedule {schedule_id}")
            return len(reminders)
            
        except Exception as e:
            logger.error(f"Error scheduling reminders for schedule {schedule_id}: {str(e)}")
            return 0

    async def cancel_reminders_for_schedule(
        self, 
        db: AsyncSession, 
        schedule_id: int
    ) -> int:
        """Отменить напоминания для занятия"""
        try:
            count = await reminder_crud.cancel_reminders_for_schedule(db, schedule_id)
            logger.info(f"Cancelled {count} reminders for schedule {schedule_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error cancelling reminders for schedule {schedule_id}: {str(e)}")
            return 0

    async def start_reminder_worker(self, interval_seconds: int = 60):
        """Запустить фоновый процесс обработки напоминаний"""
        self._running = True
        logger.info("Starting reminder worker")
        
        while self._running:
            try:
                async for db in get_async_session():
                    await self.process_pending_reminders(db)
                    break
                    
                # Ждем указанный интервал
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in reminder worker: {str(e)}")
                await asyncio.sleep(interval_seconds)  # Ждем даже при ошибке

    def stop_reminder_worker(self):
        """Остановить фоновый процесс"""
        self._running = False
        logger.info("Stopping reminder worker")

    async def get_user_upcoming_reminders(
        self, 
        db: AsyncSession, 
        user_id: int, 
        days_ahead: int = 7
    ) -> List[ScheduledReminder]:
        """Получить предстоящие напоминания пользователя"""
        try:
            from sqlalchemy import select, and_
            
            end_date = datetime.now().replace(tzinfo=None) + timedelta(days=days_ahead)
            
            result = await db.execute(
                select(ScheduledReminder)
                .filter(
                    and_(
                        ScheduledReminder.user_id == user_id,
                        ScheduledReminder.is_sent == False,
                        ScheduledReminder.send_at <= end_date
                    )
                )
                .order_by(ScheduledReminder.send_at)
            )
            
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting upcoming reminders for user {user_id}: {str(e)}")
            return []


# Глобальный экземпляр сервиса
reminder_service = ReminderService()
