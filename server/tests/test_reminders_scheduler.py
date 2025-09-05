#!/usr/bin/env python3
"""
Тесты для системы напоминаний и планировщика EduAnalytics

Этот файл содержит unit и integration тесты для:
- ReminderService
- Scheduler (check_deadlines)
- ReminderCRUD
- Интеграции с NotificationService
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone, date, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Настройка окружения для тестов
import os
os.environ["N8N_WEBHOOK_URL"] = "http://localhost:5678/webhook/test"
os.environ["DEADLINE_NOTIFICATION_DAYS"] = "7,3,1"

from app.core import config
config.settings = config.Settings()

from app.services.reminder_service import ReminderService
from app.services.scheduler import check_deadlines, run_deadline_check_once
from app.services.notification import NotificationService
from app.crud.reminder import reminder_crud
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.schedule import Schedule
from app.models.reminder import ReminderSettings, ScheduledReminder, ReminderType, ReminderInterval
from app.models.enrollment import Enrollment, EnrollmentRole, EnrollmentStatus
from app.schemas.reminder import (
    ReminderSettingsCreate, 
    ReminderSettingsUpdate,
    ReminderTestRequest,
    NotificationChannel
)


class TestReminderService:
    """Тесты для ReminderService"""

    @pytest.fixture
    def mock_notification_service(self):
        """Mock NotificationService для тестов"""
        mock_service = AsyncMock(spec=NotificationService)
        mock_service.send_notification = AsyncMock(return_value={"webhook": True})
        return mock_service

    @pytest.fixture
    def reminder_service(self, mock_notification_service):
        """Создать ReminderService с mock зависимостями"""
        service = ReminderService()
        service.notification_service = mock_notification_service
        return service

    @pytest.mark.asyncio
    async def test_process_pending_reminders_success(self, reminder_service, mock_notification_service):
        """Тест успешной обработки ожидающих напоминаний"""
        
        # Mock базы данных
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock данных
        mock_reminder = Mock()
        mock_reminder.id = 1
        mock_reminder.user_id = 123
        mock_reminder.title = "Test Reminder"
        mock_reminder.message = "Test message"
        mock_reminder.reminder_type = ReminderType.ASSIGNMENT_DUE
        mock_reminder.notification_channel = NotificationChannel.EMAIL
        mock_reminder.send_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        mock_reminder.schedule_id = None
        mock_reminder.assignment_id = None
        
        # Mock CRUD операций
        with patch.object(reminder_crud, 'get_pending_reminders', return_value=[mock_reminder]):
            with patch.object(reminder_crud, 'mark_reminder_sent', return_value=True):
                
                result = await reminder_service.process_pending_reminders(mock_db)
                
                # Проверяем результат (метод возвращает количество обработанных)
                assert result == 1
                
                # Проверяем, что NotificationService был вызван
                mock_notification_service.send_notification.assert_called_once()
                
                # Проверяем параметры вызова
                call_args = mock_notification_service.send_notification.call_args
                assert call_args[1]["event_type"] == "reminder"
                assert call_args[1]["channels"][0].value == "email"

    @pytest.mark.asyncio
    async def test_send_test_reminder_success(self, reminder_service, mock_notification_service):
        """Тест отправки тестового напоминания"""
        
        test_request = ReminderTestRequest(
            reminder_type=ReminderType.ASSIGNMENT_DUE,
            notification_channel=NotificationChannel.EMAIL,
            title="Test Reminder",
            message="This is a test reminder"
        )
        
        result = await reminder_service.send_test_reminder(123, test_request)
        
        assert result is True
        mock_notification_service.send_notification.assert_called_once()
        
        # Проверяем параметры вызова
        call_args = mock_notification_service.send_notification.call_args
        assert call_args[1]["event_type"] == "test_reminder"
        assert call_args[1]["data"]["title"] == "Test Reminder"
        assert call_args[1]["data"]["is_test"] is True

    @pytest.mark.asyncio
    async def test_schedule_reminders_for_schedule(self, reminder_service):
        """Тест создания напоминаний для нового занятия"""
        
        # Mock данных
        mock_schedule = Mock()
        mock_schedule.id = 1
        mock_schedule.course_id = 1
        mock_schedule.schedule_date = date.today() + timedelta(days=1)
        mock_schedule.start_time = time(10, 0)
        mock_schedule.course = Mock()
        mock_schedule.course.title = "Test Course"
        
        # Mock базы данных для создания напоминаний
        with patch.object(reminder_crud, 'schedule_reminders_for_schedule', return_value=[]):
            
            result = await reminder_service.schedule_reminders_for_schedule(
                Mock(spec=AsyncSession), 
                mock_schedule
            )
            
            # Проверяем, что метод был вызван
            reminder_crud.schedule_reminders_for_schedule.assert_called_once_with(
                reminder_service.db, mock_schedule
            )


class TestScheduler:
    """Тесты для планировщика дедлайнов"""

    @pytest.fixture
    def mock_notification_service(self):
        """Mock NotificationService для тестов"""
        mock_service = AsyncMock(spec=NotificationService)
        mock_service.send_notification = AsyncMock(return_value={"webhook": True, "email": True})
        return mock_service

    @pytest.mark.asyncio
    async def test_check_deadlines_no_assignments(self, mock_notification_service):
        """Тест проверки дедлайнов когда нет заданий"""
        
        # Mock базы данных - нет заданий
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        async def _factory():
            class _Ctx:
                async def __aenter__(self):
                    return mock_db
                async def __aexit__(self, exc_type, exc, tb):
                    return False
            return _Ctx()
        
        # Выполняем проверку с подмененным session_factory
        await check_deadlines(mock_notification_service, session_factory=lambda: _factory())
            
            # Проверяем, что NotificationService не был вызван
            mock_notification_service.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_deadlines_with_assignments(self, mock_notification_service):
        """Тест проверки дедлайнов с заданиями"""
        
        # Создаем mock задания
        mock_assignment = Mock()
        mock_assignment.id = 1
        mock_assignment.title = "Test Assignment"
        mock_assignment.course_id = 1
        mock_assignment.due_date = datetime.now(timezone.utc) + timedelta(days=3)
        mock_assignment.course = Mock()
        mock_assignment.course.title = "Test Course"
        
        # Mock студентов
        mock_student = Mock()
        mock_student.id = 123
        mock_student.username = "test_student"
        
        # Mock базы данных
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock для поиска заданий
        mock_assignments_result = AsyncMock()
        mock_assignments_result.scalars.return_value.all.return_value = [mock_assignment]
        
        # Mock для поиска студентов
        mock_students_result = AsyncMock()
        mock_students_result.scalars.return_value.all.return_value = [mock_student]
        
        # Настраиваем последовательность вызовов execute
        mock_db.execute = AsyncMock(side_effect=[mock_assignments_result, mock_students_result])
        
        async def _factory():
            class _Ctx:
                async def __aenter__(self):
                    return mock_db
                async def __aexit__(self, exc_type, exc, tb):
                    return False
            return _Ctx()

        # Выполняем проверку с подмененным session_factory
        await check_deadlines(mock_notification_service, session_factory=lambda: _factory())
            
            # Проверяем, что NotificationService был вызван
            mock_notification_service.send_notification.assert_called()
            
            # Проверяем параметры вызова
            call_args = mock_notification_service.send_notification.call_args
            assert call_args[1]["event_type"] == "deadline_approaching"
            assert call_args[1]["data"]["assignment_id"] == 1
            assert call_args[1]["data"]["title"] == "Test Assignment"

    @pytest.mark.asyncio
    async def test_run_deadline_check_once_success(self, mock_notification_service):
        """Тест одноразового запуска проверки дедлайнов"""
        
        with patch('app.services.scheduler.check_deadlines', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = None
            
            result = await run_deadline_check_once(mock_notification_service)
            
            assert result is True
            mock_check.assert_called_once_with(mock_notification_service)

    @pytest.mark.asyncio
    async def test_run_deadline_check_once_failure(self, mock_notification_service):
        """Тест одноразового запуска проверки дедлайнов с ошибкой"""
        
        with patch('app.services.scheduler.check_deadlines', new_callable=AsyncMock) as mock_check:
            mock_check.side_effect = Exception("Test error")
            
            result = await run_deadline_check_once(mock_notification_service)
            
            assert result is False
            mock_check.assert_called_once_with(mock_notification_service)


class TestReminderCRUD:
    """Тесты для CRUD операций с напоминаниями"""

    @pytest.mark.asyncio
    async def test_get_user_reminder_setting_exists(self):
        """Тест получения существующей настройки напоминаний пользователя"""
        
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = AsyncMock()
        
        # Mock настройки
        mock_setting = Mock()
        mock_setting.id = 1
        mock_setting.user_id = 123
        mock_setting.reminder_type = ReminderType.ASSIGNMENT_DUE
        mock_setting.is_enabled = True
        
        mock_result.scalar_one_or_none.return_value = mock_setting
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await reminder_crud.get_user_reminder_setting(
            mock_db, 123, ReminderType.ASSIGNMENT_DUE
        )
        
        assert result == mock_setting
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_reminder_setting(self):
        """Тест создания новой настройки напоминаний"""
        
        mock_db = AsyncMock(spec=AsyncSession)
        
        setting_data = ReminderSettingsCreate(
            user_id=123,
            reminder_type=ReminderType.ASSIGNMENT_DUE,
            is_enabled=True,
            interval_before=ReminderInterval.ONE_DAY,
            notification_channel=NotificationChannel.EMAIL
        )
        
        with patch('app.crud.reminder.ReminderSettings') as mock_model:
            mock_instance = Mock()
            mock_model.return_value = mock_instance
            
            result = await reminder_crud.create_reminder_setting(mock_db, setting_data)
            
            # Проверяем, что модель была создана
            mock_model.assert_called_once()
            mock_db.add.assert_called_once_with(mock_instance)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_instance)

    @pytest.mark.asyncio
    async def test_get_pending_reminders(self):
        """Тест получения ожидающих напоминаний"""
        
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = AsyncMock()
        
        # Mock напоминаний
        mock_reminder1 = Mock()
        mock_reminder1.id = 1
        mock_reminder1.send_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        mock_reminder2 = Mock()
        mock_reminder2.id = 2
        mock_reminder2.send_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        
        mock_result.scalars.return_value.all.return_value = [mock_reminder1, mock_reminder2]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await reminder_crud.get_pending_reminders(mock_db)
        
        assert len(result) == 2
        assert result[0] == mock_reminder1
        assert result[1] == mock_reminder2
        mock_db.execute.assert_called_once()


class TestReminderIntegration:
    """Интеграционные тесты для системы напоминаний"""

    @pytest.mark.asyncio
    async def test_full_reminder_flow(self):
        """Тест полного потока напоминаний: создание -> обработка -> отправка"""
        
        # Этот тест требует настройки тестовой базы данных
        # Для демонстрации используем mocks
        
        mock_db = AsyncMock(spec=AsyncSession)
        mock_notification_service = AsyncMock(spec=NotificationService)
        mock_notification_service.send_notification = AsyncMock(return_value={"email": True})
        
        reminder_service = ReminderService(notification_service=mock_notification_service)
        
        # 1. Создаем настройку напоминаний
        with patch.object(reminder_crud, 'create_reminder_setting') as mock_create:
            setting_data = ReminderSettingsCreate(
                user_id=123,
                reminder_type=ReminderType.ASSIGNMENT_DUE,
                is_enabled=True,
                interval_before=ReminderInterval.ONE_DAY,
                notification_channel=NotificationChannel.EMAIL
            )
            
            await reminder_crud.create_reminder_setting(mock_db, setting_data)
            mock_create.assert_called_once()
        
        # 2. Создаем запланированное напоминание
        mock_reminder = Mock()
        mock_reminder.id = 1
        mock_reminder.user_id = 123
        mock_reminder.title = "Assignment Due Tomorrow"
        mock_reminder.message = "Don't forget your assignment!"
        mock_reminder.reminder_type = ReminderType.ASSIGNMENT_DUE
        mock_reminder.notification_channel = NotificationChannel.EMAIL
        mock_reminder.send_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        mock_reminder.schedule_id = None
        mock_reminder.assignment_id = 456
        
        # 3. Обрабатываем напоминание
        with patch.object(reminder_crud, 'get_pending_reminders', return_value=[mock_reminder]):
            with patch.object(reminder_crud, 'mark_reminder_as_sent', return_value=True):
                
                result = await reminder_service.process_pending_reminders()
                
                # Проверяем успешную обработку
                assert result["processed"] == 1
                assert result["errors"] == 0
                
                # Проверяем отправку уведомления
                mock_notification_service.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_scheduler_with_enrollments(self):
        """Тест планировщика с использованием enrollments"""
        
        mock_notification_service = AsyncMock(spec=NotificationService)
        mock_notification_service.send_notification = AsyncMock(return_value={"webhook": True})
        
        # Mock задания
        mock_assignment = Mock()
        mock_assignment.id = 1
        mock_assignment.title = "Test Assignment"
        mock_assignment.course_id = 1
        mock_assignment.due_date = datetime.now(timezone.utc) + timedelta(days=3)
        mock_assignment.course = Mock()
        mock_assignment.course.title = "Test Course"
        
        # Mock студентов через enrollments
        mock_student = Mock()
        mock_student.id = 123
        mock_student.username = "test_student"
        
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Настраиваем mock для поиска заданий и студентов
        mock_assignments_result = AsyncMock()
        mock_assignments_result.scalars.return_value.all.return_value = [mock_assignment]
        
        mock_students_result = AsyncMock()
        mock_students_result.scalars.return_value.all.return_value = [mock_student]
        
        # Последовательность вызовов: задания, потом студенты для каждого задания
        mock_db.execute = AsyncMock(side_effect=[mock_assignments_result, mock_students_result])
        
        with patch('app.services.scheduler.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__.return_value = mock_db
            
            await check_deadlines(mock_notification_service)
            
            # Проверяем, что уведомление было отправлено
            mock_notification_service.send_notification.assert_called()
            
            # Проверяем, что в данных есть информация о студентах
            call_args = mock_notification_service.send_notification.call_args
            data = call_args[1]["data"]
            assert data["students_count"] == 1
            assert len(data["students_list"]) == 1
            assert data["students_list"][0]["student_id"] == 123


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])
