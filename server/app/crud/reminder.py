from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.models.reminder import ReminderSettings, ScheduledReminder, ReminderType, ReminderInterval, NotificationChannel
from app.models.user import User
from app.models.schedule import Schedule
from app.schemas.reminder import ReminderSettingsCreate, ReminderSettingsUpdate, ScheduledReminderCreate, UserReminderPreferences

logger = logging.getLogger(__name__)


class CRUDReminder:
    """CRUD операции для системы напоминаний"""

    async def get_user_reminder_settings(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[ReminderSettings]:
        """Получить все настройки напоминаний пользователя"""
        result = await db.execute(
            select(ReminderSettings).filter(ReminderSettings.user_id == user_id)
        )
        return result.scalars().all()

    async def get_user_reminder_setting(
        self, 
        db: AsyncSession, 
        user_id: int, 
        reminder_type: ReminderType
    ) -> Optional[ReminderSettings]:
        """Получить конкретную настройку напоминания пользователя"""
        result = await db.execute(
            select(ReminderSettings).filter(
                and_(
                    ReminderSettings.user_id == user_id,
                    ReminderSettings.reminder_type == reminder_type
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_or_update_reminder_setting(
        self, 
        db: AsyncSession, 
        user_id: int, 
        reminder_type: ReminderType,
        settings: ReminderSettingsUpdate
    ) -> ReminderSettings:
        """Создать или обновить настройку напоминания"""
        # Попробуем найти существующую настройку
        existing = await self.get_user_reminder_setting(db, user_id, reminder_type)
        
        if existing:
            # Обновляем существующую
            update_data = settings.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing, field, value)
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Создаем новую
            db_setting = ReminderSettings(
                user_id=user_id,
                reminder_type=reminder_type,
                is_enabled=settings.is_enabled if settings.is_enabled is not None else True,
                interval_before=settings.interval_before or ReminderInterval.HOUR_1,
                notification_channel=settings.notification_channel or NotificationChannel.EMAIL
            )
            db.add(db_setting)
            await db.commit()
            await db.refresh(db_setting)
            return db_setting

    async def update_user_preferences(
        self, 
        db: AsyncSession, 
        user_id: int, 
        preferences: UserReminderPreferences
    ) -> List[ReminderSettings]:
        """Обновить все предпочтения пользователя"""
        settings_to_update = [
            (ReminderType.SCHEDULE_UPCOMING, ReminderSettingsUpdate(
                is_enabled=preferences.schedule_upcoming_enabled,
                interval_before=preferences.schedule_upcoming_interval,
                notification_channel=preferences.schedule_upcoming_channel
            )),
            (ReminderType.SCHEDULE_CHANGED, ReminderSettingsUpdate(
                is_enabled=preferences.schedule_changes_enabled,
                notification_channel=preferences.schedule_changes_channel
            )),
            (ReminderType.ASSIGNMENT_DUE, ReminderSettingsUpdate(
                is_enabled=preferences.assignment_due_enabled,
                interval_before=preferences.assignment_due_interval,
                notification_channel=preferences.assignment_due_channel
            ))
        ]
        
        updated_settings = []
        for reminder_type, update_data in settings_to_update:
            setting = await self.create_or_update_reminder_setting(db, user_id, reminder_type, update_data)
            updated_settings.append(setting)
        
        return updated_settings

    async def create_scheduled_reminder(
        self, 
        db: AsyncSession, 
        reminder_data: ScheduledReminderCreate
    ) -> ScheduledReminder:
        """Создать запланированное напоминание"""
        db_reminder = ScheduledReminder(**reminder_data.model_dump())
        db.add(db_reminder)
        await db.commit()
        await db.refresh(db_reminder)
        return db_reminder

    async def get_pending_reminders(
        self, 
        db: AsyncSession, 
        limit: int = 100
    ) -> List[ScheduledReminder]:
        """Получить напоминания, готовые к отправке"""
        current_time = datetime.now().replace(tzinfo=None)
        result = await db.execute(
            select(ScheduledReminder)
            .options(selectinload(ScheduledReminder.user))
            .options(selectinload(ScheduledReminder.schedule))
            .options(selectinload(ScheduledReminder.assignment))
            .filter(
                and_(
                    ScheduledReminder.is_sent == False,
                    ScheduledReminder.send_at <= current_time
                )
            )
            .limit(limit)
        )
        return result.scalars().all()

    async def mark_reminder_sent(
        self, 
        db: AsyncSession, 
        reminder_id: int
    ) -> bool:
        """Отметить напоминание как отправленное"""
        result = await db.execute(
            select(ScheduledReminder).filter(ScheduledReminder.id == reminder_id)
        )
        reminder = result.scalar_one_or_none()
        
        if reminder:
            reminder.is_sent = True
            reminder.sent_at = datetime.now().replace(tzinfo=None)
            await db.commit()
            return True
        return False

    def _calculate_send_time(self, target_time: datetime, interval: ReminderInterval) -> datetime:
        """Рассчитать время отправки напоминания"""
        if interval == ReminderInterval.MINUTES_15:
            return target_time - timedelta(minutes=15)
        elif interval == ReminderInterval.HOUR_1:
            return target_time - timedelta(hours=1)
        elif interval == ReminderInterval.HOURS_2:
            return target_time - timedelta(hours=2)
        elif interval == ReminderInterval.DAY_1:
            return target_time - timedelta(days=1)
        elif interval == ReminderInterval.DAYS_3:
            return target_time - timedelta(days=3)
        elif interval == ReminderInterval.WEEK_1:
            return target_time - timedelta(weeks=1)
        else:
            return target_time - timedelta(hours=1)  # Дефолт

    async def schedule_reminders_for_schedule(
        self, 
        db: AsyncSession, 
        schedule: Schedule
    ) -> List[ScheduledReminder]:
        """Создать напоминания для нового занятия"""
        # Получаем всех студентов курса
        from app.models.student import Student
        from app.models.course import Course
        
        result = await db.execute(
            select(Student)
            .join(Course, Student.groups.any())  # Упрощенно, нужно доработать связи
            .filter(Course.id == schedule.course_id)
        )
        students = result.scalars().all()
        
        scheduled_reminders = []
        
        # Создаем время занятия
        schedule_datetime = datetime.combine(
            schedule.schedule_date, 
            schedule.start_time
        )
        
        for student in students:
            # Получаем настройки напоминаний студента
            setting = await self.get_user_reminder_setting(
                db, 
                student.user_id, 
                ReminderType.SCHEDULE_UPCOMING
            )
            
            if setting and setting.is_enabled:
                send_time = self._calculate_send_time(schedule_datetime, setting.interval_before)
                
                # Создаем напоминание только если время еще не прошло
                if send_time > datetime.now().replace(tzinfo=None):
                    reminder_data = ScheduledReminderCreate(
                        user_id=student.user_id,
                        schedule_id=schedule.id,
                        reminder_type=ReminderType.SCHEDULE_UPCOMING,
                        notification_channel=setting.notification_channel,
                        send_at=send_time,
                        title=f"Предстоящее занятие: {schedule.course.title if schedule.course else 'Курс'}",
                        message=f"Напоминаем, что у вас запланировано занятие {schedule.lesson_type} "
                               f"в {schedule.start_time.strftime('%H:%M')} "
                               f"в аудитории {schedule.location or 'TBD'}."
                    )
                    
                    reminder = await self.create_scheduled_reminder(db, reminder_data)
                    scheduled_reminders.append(reminder)
        
        return scheduled_reminders

    async def cancel_reminders_for_schedule(
        self, 
        db: AsyncSession, 
        schedule_id: int
    ) -> int:
        """Отменить напоминания для занятия (при удалении или отмене)"""
        result = await db.execute(
            select(ScheduledReminder).filter(
                and_(
                    ScheduledReminder.schedule_id == schedule_id,
                    ScheduledReminder.is_sent == False
                )
            )
        )
        reminders = result.scalars().all()
        
        count = 0
        for reminder in reminders:
            await db.delete(reminder)
            count += 1
        
        await db.commit()
        return count


# Создание экземпляра CRUD
reminder_crud = CRUDReminder()
