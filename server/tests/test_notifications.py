#!/usr/bin/env python3
"""
Тесты для системы уведомлений EduAnalytics

Этот файл содержит unit и integration тесты для всех компонентов
системы уведомлений.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, date, time
from sqlalchemy.orm import Session

import os
os.environ["N8N_WEBHOOK_URL"] = "http://localhost:5678/webhook/test"
from app.core import config
config.settings = config.Settings()
from app.services.notification import NotificationService
from app.tasks.deadline_checker import DeadlineChecker
from app.crud.feedback import CRUDFeedback
from app.crud.gradebook import CRUDGradebook
from app.crud.schedule import CRUDSchedule
from app.models import User, Course, Assignment, Student, GradebookEntry, Schedule, Feedback
from app.schemas import FeedbackCreate, GradebookEntryCreate, ScheduleCreate
from unittest.mock import AsyncMock

class TestNotificationService:
    """Тесты для NotificationService"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        from app.core import config
        self.notification_service = NotificationService(settings=config.settings)
    
    @patch('httpx.AsyncClient.post')
    def test_send_webhook_success(self, mock_post):
        """Тест успешной отправки webhook"""
        # Настройка mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response
        
        # Тестовые данные
        test_data = {
            "event_type": "test_event",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": "Test notification"
        }
        
        # Выполнение
        import asyncio
        result = asyncio.run(self.notification_service.send_webhook(test_data))
        
        # Проверки
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "json" in call_args.kwargs
        assert call_args.kwargs["json"] == test_data
    
    @patch('httpx.AsyncClient.post')
    def test_send_webhook_failure(self, mock_post):
        """Тест неудачной отправки webhook"""
        # Настройка mock для ошибки
        mock_post.side_effect = Exception("Connection error")
        # Тестовые данные
        test_data = {"event_type": "test_event"}
        # Выполнение
        import asyncio
        result = asyncio.run(self.notification_service.send_webhook(test_data))
        # Проверки
        assert result is False
    
    @patch('httpx.AsyncClient.post')
    def test_send_webhook_legacy(self, mock_post):
        """Тест отправки legacy webhook"""
        # Настройка mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        # Тестовые данные
        event_type = "grade_notification"
        data = {"student_id": 1, "grade": 85}
        # Выполнение
        import asyncio
        result = asyncio.run(self.notification_service.send_webhook_legacy(event_type, data))
        # Проверки
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        sent_data = call_args.kwargs["json"]
        assert sent_data["type"] == event_type
        assert sent_data["data"] == data
        assert "timestamp" in sent_data
    
    @patch.object(NotificationService, 'send_webhook_sync')
    def test_send_deadline_notification(self, mock_send_webhook_sync):
        """Тест отправки уведомления о дедлайне"""
        # Настройка mock
        mock_send_webhook_sync.return_value = True
        # Выполнение
        result = self.notification_service.send_deadline_notification_sync(
            assignment_id=1,
            assignment_title="Тест",
            due_date="2024-01-20T23:59:59Z",
            course_name="Программирование",
            course_id=1,
            hours_remaining=3,
            students=[{"student_id": 1, "student_name": "Иван Иванов", "student_email": "ivan@test.com"}]
        )
        # Проверки
        assert result is True
        mock_send_webhook_sync.assert_called_once()
        call_args = mock_send_webhook_sync.call_args[0][0]
        assert call_args["event_type"] == "deadline_approaching"
        assert call_args["students"][0]["student_id"] == 1
        assert call_args["hours_remaining"] == 3
        assert call_args["student_id"] == 1
        assert call_args["days_remaining"] == 3
    
    @patch.object(NotificationService, 'send_webhook_legacy')
    def test_send_grade_notification(self, mock_send_webhook_legacy):
        """Тест отправки уведомления об оценке"""
        # Настройка mock
        mock_send_webhook_legacy.return_value = True
        
        # Выполнение
        result = self.notification_service.send_grade_notification(
            student_id=1,
            assignment_id=1,
            grade_value=85,
            teacher_id=1
        )
        
        # Проверки
        assert result is True
        mock_send_webhook_legacy.assert_called_once()
        call_args = mock_send_webhook_legacy.call_args
        assert call_args[0][0] == "grade_notification"
        data = call_args[0][1]
        assert data["student_id"] == 1
        assert data["grade_value"] == 85

class TestDeadlineChecker:
    """Тесты для DeadlineChecker"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.deadline_checker = DeadlineChecker()
    
    @patch('app.database.get_db')
    @patch.object(DeadlineChecker, '_send_deadline_notification')
    def test_check_deadlines_for_interval(self, mock_send_notification, mock_get_db):
        """Тест проверки дедлайнов для определенного интервала"""
        # Создание mock базы данных
        mock_db = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Создание тестовых данных
        future_date = datetime.utcnow() + timedelta(days=3)
        mock_assignment = Mock()
        mock_assignment.id = 1
        mock_assignment.title = "Тестовое задание"
        mock_assignment.due_date = future_date
        mock_assignment.course.name = "Тестовый курс"
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_assignment]
        
        # Выполнение
        self.deadline_checker._check_deadlines_for_interval_sync(3)
        # Проверки
        mock_send_notification.assert_called()
    
    @patch('app.database.get_db')
    @patch.object(NotificationService, 'send_deadline_notification_sync')
    def test_send_deadline_notification(self, mock_send_notification, mock_get_db):
        """Тест отправки уведомления о дедлайне"""
        # Создание mock базы данных
        mock_db = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Создание тестовых данных
        mock_assignment = Mock()
        mock_assignment.id = 1
        mock_assignment.title = "Тестовое задание"
        mock_assignment.course.name = "Тестовый курс"
        
        mock_student = Mock()
        mock_student.id = 1
        mock_student.user.first_name = "Иван"
        mock_student.user.last_name = "Иванов"
        mock_student.user.email = "ivan@test.com"
        
        mock_send_notification.return_value = True
        
        # Выполнение
        result = self.deadline_checker._send_deadline_notification_sync(
            mock_assignment, 3
        )
        
        # Проверки
        assert result is True
        mock_send_notification.assert_called_once()
    
    @patch('app.database.get_db')
    def test_get_course_students(self, mock_get_db):
        """Тест получения студентов курса"""
        # Создание mock базы данных
        mock_db = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Создание тестовых данных
        mock_student1 = Mock()
        mock_student1.id = 1
        mock_student2 = Mock()
        mock_student2.id = 2
        
        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_student1, mock_student2
        ]
        
        # Выполнение
        students = self.deadline_checker._get_course_students(1)
        
        # Проверки
        assert len(students) == 2
        assert students[0].id == 1
        assert students[1].id == 2

class TestCRUDNotificationIntegration:
    """Тесты интеграции уведомлений с CRUD операциями"""
    @patch('app.database.get_db')
    @patch.object(NotificationService, 'send_webhook')
    def test_feedback_create_with_notification(self, mock_get_db, mock_send_webhook):
        """Тест создания обратной связи с уведомлением"""
        # Создание mock базы данных
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Создание mock объектов
        mock_submission = Mock()
        mock_submission.id = 1
        mock_submission.title = "Тестовая работа"
        mock_submission.assignment.title = "Тестовое задание"
        mock_submission.assignment.course.name = "Тестовый курс"
        mock_submission.student.id = 1
        mock_submission.student.user.first_name = "Иван"
        mock_submission.student.user.last_name = "Иванов"
        mock_submission.student.user.email = "ivan@test.com"
        
        mock_author = Mock()
        mock_author.id = 2
        mock_author.first_name = "Петр"
        mock_author.last_name = "Петров"
        mock_author.email = "petr@test.com"
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_submission, mock_author
        ]
        
        mock_feedback = Mock()
        mock_feedback.id = 1
        mock_feedback.content = "Отличная работа!"
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        mock_send_webhook.return_value = True
        
        # Создание CRUD объекта
        feedback_crud = CRUDFeedback
        
        # Тестовые данные
        feedback_data = FeedbackCreate(
            submission_id=1,
            author_id=2,
            content="Отличная работа!",
            rating=5
        )
        
        # Выполнение (с mock'ом создания объекта)
        with patch.object(crud_feedback, 'create', return_value=mock_feedback):
            result = crud_feedback.create_feedback(
                db=mock_db,
                obj_in=feedback_data,
                send_notification=True
            )
        
        # Проверки
        assert result == mock_feedback
        mock_send_webhook.assert_called_once()
        call_args = mock_send_webhook.call_args[0][0]
        assert call_args["event_type"] == "feedback_created"
    
    @patch.object(CRUDGradebook, 'get_entry_by_unique_key', return_value=None)
    @patch.object(CRUDGradebook, '_send_grade_notification')
    @patch('app.database.get_db')
    def test_gradebook_create_with_notification(self, mock_get_db, mock_send_notification, mock_get_entry_by_unique_key):
        """Тест создания записи в журнале с уведомлением"""
        # Patch db.query chains for course, student, assignment, and ensure no duplicate entry
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = Mock()
        mock_user.role = "teacher"
        mock_user.id = 1
        mock_user.username = "teacher@example.com"
        course_mock = MagicMock()
        student_mock = MagicMock()
        assignment_mock = MagicMock()
        course_mock.name = "Математика"
        student_mock.first_name = "Иван"
        student_mock.last_name = "Иванов"
        student_mock.id = 2
        student_user_mock = MagicMock()
        student_user_mock.username = "student@example.com"
        assignment_mock.title = "Домашнее задание 1"
        assignment_mock.id = 3
        # Ensure no duplicate entry by returning None for the duplicate check
        mock_db.query.return_value.filter.return_value.first.side_effect = [course_mock, student_mock, student_user_mock, assignment_mock, None]
        entry_data = GradebookEntryCreate(
            course_id=1,
            student_id=2,
            assignment_id=3,
            grade_value=85.5,
            comment="Отличная работа"
        )
        crud_gradebook = CRUDGradebook()
        result = crud_gradebook.create_entry(
            db=mock_db,
            entry_in=entry_data,
            current_user=mock_user
        )
        assert mock_send_notification.called
    @patch('app.database.get_db')
    def test_schedule_create_with_notification(self, mock_get_db):
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_user = Mock()
        mock_user.role = "teacher"
        mock_user.id = 1
        mock_course = MagicMock()
        mock_course.id = 1
        mock_course.teacher_id = 1
        mock_instructor = MagicMock()
        mock_instructor.role = "teacher"
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_course, mock_instructor, None]
        crud_schedule = CRUDSchedule()
        schedule_data = ScheduleCreate(
            course_id=1,
            instructor_id=1,
            schedule_date=date(2024, 1, 20),
            start_time=time(10, 0, 0),
            end_time=time(11, 30, 0),
            location="Аудитория 101",
            lesson_type="lecture",
            description="Лекция",
            notes=None,
            is_cancelled=False,
            classroom_id=None
        )
        with patch.object(CRUDSchedule, '_send_schedule_notification', new_callable=AsyncMock) as mock_send_schedule_notification, \
             patch('app.crud.schedule.CRUDSchedule._get_classroom', return_value=MagicMock()), \
             patch('app.crud.schedule.CRUDSchedule._get_course', return_value=MagicMock()):
            import asyncio
            result = asyncio.run(crud_schedule.create_schedule(
                db=mock_db,
                schedule_data=schedule_data,
                current_user=mock_user
            ))
            assert mock_send_schedule_notification.called

    # Update feedback test data
    @patch.object(NotificationService, 'send_webhook')
    def test_feedback_create_with_notification(self, mock_send_webhook):
        feedback_data = FeedbackCreate(text="Тестовый комментарий")
        # ... остальной тест ...