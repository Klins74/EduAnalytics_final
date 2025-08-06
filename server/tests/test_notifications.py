#!/usr/bin/env python3
"""
Тесты для системы уведомлений EduAnalytics

Этот файл содержит unit и integration тесты для всех компонентов
системы уведомлений.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.notification import NotificationService
from app.tasks.deadline_checker import DeadlineChecker
from app.crud.feedback import CRUDFeedback
from app.crud.gradebook import CRUDGradebook
from app.crud.schedule import CRUDSchedule
from app.models import User, Course, Assignment, Student, GradebookEntry, Schedule, Feedback
from app.schemas import FeedbackCreate, GradebookEntryCreate, ScheduleCreate

class TestNotificationService:
    """Тесты для NotificationService"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.notification_service = NotificationService()
    
    @patch('requests.post')
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
        result = self.notification_service.send_webhook(test_data)
        
        # Проверки
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "json" in call_args.kwargs
        assert call_args.kwargs["json"] == test_data
    
    @patch('requests.post')
    def test_send_webhook_failure(self, mock_post):
        """Тест неудачной отправки webhook"""
        # Настройка mock для ошибки
        mock_post.side_effect = Exception("Connection error")
        
        # Тестовые данные
        test_data = {"event_type": "test_event"}
        
        # Выполнение
        result = self.notification_service.send_webhook(test_data)
        
        # Проверки
        assert result is False
    
    @patch('requests.post')
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
        result = self.notification_service.send_webhook_legacy(event_type, data)
        
        # Проверки
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        sent_data = call_args.kwargs["json"]
        assert sent_data["event_type"] == event_type
        assert sent_data["data"] == data
        assert "timestamp" in sent_data
    
    @patch.object(NotificationService, 'send_webhook')
    def test_send_deadline_notification(self, mock_send_webhook):
        """Тест отправки уведомления о дедлайне"""
        # Настройка mock
        mock_send_webhook.return_value = True
        
        # Выполнение
        result = self.notification_service.send_deadline_notification(
            student_id=1,
            student_name="Иван Иванов",
            student_email="ivan@test.com",
            assignment_id=1,
            assignment_title="Тест",
            course_name="Программирование",
            due_date="2024-01-20T23:59:59Z",
            days_remaining=3
        )
        
        # Проверки
        assert result is True
        mock_send_webhook.assert_called_once()
        call_args = mock_send_webhook.call_args[0][0]
        assert call_args["event_type"] == "deadline_approaching"
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
        self.deadline_checker._check_deadlines_for_interval(3)
        
        # Проверки
        mock_send_notification.assert_called()
    
    @patch('app.database.get_db')
    @patch.object(NotificationService, 'send_deadline_notification')
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
        result = self.deadline_checker._send_deadline_notification(
            mock_assignment, mock_student, 3
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
    def test_feedback_create_with_notification(self, mock_send_webhook, mock_get_db):
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
        crud_feedback = CRUDFeedback(Feedback)
        
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
    
    @patch('app.database.get_db')
    @patch.object(CRUDGradebook, '_send_grade_notification')
    def test_gradebook_create_with_notification(self, mock_send_notification, mock_get_db):
        """Тест создания записи в журнале с уведомлением"""
        # Создание mock базы данных
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Создание mock объектов
        mock_user = Mock()
        mock_user.role = "teacher"
        
        mock_assignment = Mock()
        mock_assignment.id = 1
        mock_assignment.course_id = 1
        
        mock_student = Mock()
        mock_student.id = 1
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_assignment, mock_student, None  # None для проверки дубликатов
        ]
        
        mock_entry = Mock()
        mock_entry.id = 1
        mock_entry.score = 85
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        mock_send_notification.return_value = True
        
        # Создание CRUD объекта
        crud_gradebook = CRUDGradebook(GradebookEntry)
        
        # Тестовые данные
        entry_data = GradebookEntryCreate(
            student_id=1,
            assignment_id=1,
            score=85,
            comment="Хорошая работа"
        )
        
        # Выполнение (с mock'ом создания объекта)
        with patch.object(crud_gradebook, 'create', return_value=mock_entry):
            result = crud_gradebook.create_entry(
                db=mock_db,
                obj_in=entry_data,
                current_user=mock_user
            )
        
        # Проверки
        assert result == mock_entry
        mock_send_notification.assert_called_once()
    
    @patch('app.database.get_db')
    @patch.object(CRUDSchedule, '_send_schedule_notification')
    def test_schedule_create_with_notification(self, mock_send_notification, mock_get_db):
        """Тест создания расписания с уведомлением"""
        # Создание mock базы данных
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Создание mock объектов
        mock_user = Mock()
        mock_user.role = "teacher"
        mock_user.id = 1
        
        mock_course = Mock()
        mock_course.id = 1
        mock_course.teacher_id = 1
        
        mock_instructor = Mock()
        mock_instructor.role = "teacher"
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_course, mock_instructor, None  # None для проверки конфликтов
        ]
        
        mock_schedule = Mock()
        mock_schedule.id = 1
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        mock_send_notification.return_value = True
        
        # Создание CRUD объекта
        crud_schedule = CRUDSchedule(Schedule)
        
        # Тестовые данные
        schedule_data = ScheduleCreate(
            course_id=1,
            instructor_id=1,
            date="2024-01-20",
            start_time="10:00:00",
            end_time="11:30:00",
            location="Аудитория 101",
            description="Лекция"
        )
        
        # Выполнение (с mock'ом создания объекта)
        with patch.object(crud_schedule, 'create', return_value=mock_schedule):
            result = crud_schedule.create_schedule(
                db=mock_db,
                obj_in=schedule_data,
                current_user=mock_user
            )
        
        # Проверки
        assert result == mock_schedule
        mock_send_notification.assert_called_once()

class TestNotificationConfiguration:
    """Тесты конфигурации уведомлений"""
    
    def test_notification_service_initialization(self):
        """Тест инициализации сервиса уведомлений"""
        service = NotificationService()
        assert service.webhook_url is not None
        assert service.timeout > 0
    
    @patch('app.core.config.settings')
    def test_notification_service_with_custom_config(self, mock_settings):
        """Тест сервиса с пользовательской конфигурацией"""
        mock_settings.WEBHOOK_URL = "http://custom-webhook.com"
        mock_settings.WEBHOOK_TIMEOUT = 60
        
        service = NotificationService()
        assert "custom-webhook" in service.webhook_url
        assert service.timeout == 60

class TestNotificationErrorHandling:
    """Тесты обработки ошибок в уведомлениях"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.notification_service = NotificationService()
    
    @patch('requests.post')
    def test_webhook_timeout_handling(self, mock_post):
        """Тест обработки таймаута webhook"""
        # Настройка mock для таймаута
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        # Тестовые данные
        test_data = {"event_type": "test_event"}
        
        # Выполнение
        result = self.notification_service.send_webhook(test_data)
        
        # Проверки
        assert result is False
    
    @patch('requests.post')
    def test_webhook_connection_error_handling(self, mock_post):
        """Тест обработки ошибки подключения webhook"""
        # Настройка mock для ошибки подключения
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Тестовые данные
        test_data = {"event_type": "test_event"}
        
        # Выполнение
        result = self.notification_service.send_webhook(test_data)
        
        # Проверки
        assert result is False
    
    @patch('requests.post')
    def test_webhook_http_error_handling(self, mock_post):
        """Тест обработки HTTP ошибок webhook"""
        # Настройка mock для HTTP ошибки
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("HTTP 500 Error")
        mock_post.return_value = mock_response
        
        # Тестовые данные
        test_data = {"event_type": "test_event"}
        
        # Выполнение
        result = self.notification_service.send_webhook(test_data)
        
        # Проверки
        assert result is False

# Фикстуры для тестов

@pytest.fixture
def mock_db_session():
    """Фикстура для mock сессии базы данных"""
    return Mock(spec=Session)

@pytest.fixture
def sample_user():
    """Фикстура для тестового пользователя"""
    user = Mock(spec=User)
    user.id = 1
    user.first_name = "Иван"
    user.last_name = "Иванов"
    user.email = "ivan@test.com"
    user.role = "student"
    return user

@pytest.fixture
def sample_course():
    """Фикстура для тестового курса"""
    course = Mock(spec=Course)
    course.id = 1
    course.name = "Тестовый курс"
    course.code = "TEST-001"
    return course

@pytest.fixture
def sample_assignment(sample_course):
    """Фикстура для тестового задания"""
    assignment = Mock(spec=Assignment)
    assignment.id = 1
    assignment.title = "Тестовое задание"
    assignment.course = sample_course
    assignment.due_date = datetime.utcnow() + timedelta(days=3)
    assignment.max_score = 100
    return assignment

# Интеграционные тесты

class TestNotificationIntegration:
    """Интеграционные тесты системы уведомлений"""
    
    @pytest.mark.integration
    @patch('requests.post')
    def test_full_notification_flow(self, mock_post):
        """Тест полного потока уведомлений"""
        # Настройка mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Создание сервиса
        service = NotificationService()
        
        # Тест различных типов уведомлений
        test_cases = [
            {
                "method": service.send_deadline_notification,
                "args": {
                    "student_id": 1,
                    "student_name": "Иван Иванов",
                    "student_email": "ivan@test.com",
                    "assignment_id": 1,
                    "assignment_title": "Тест",
                    "course_name": "Программирование",
                    "due_date": "2024-01-20T23:59:59Z",
                    "days_remaining": 3
                }
            },
            {
                "method": service.send_grade_notification,
                "args": {
                    "student_id": 1,
                    "assignment_id": 1,
                    "grade_value": 85,
                    "teacher_id": 1
                }
            }
        ]
        
        # Выполнение тестов
        for test_case in test_cases:
            result = test_case["method"](**test_case["args"])
            assert result is True
        
        # Проверка количества вызовов
        assert mock_post.call_count == len(test_cases)

if __name__ == "__main__":
    # Запуск тестов
    pytest.main(["-v", __file__])