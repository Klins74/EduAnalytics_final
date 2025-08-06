#!/usr/bin/env python3
"""
Конфигурация тестов для EduAnalytics

Этот файл содержит общие фикстуры и настройки для всех тестов.
"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Импорты моделей и схем
from app.database import Base, get_db
from app.models import User, Course, Assignment, Student, GradebookEntry, Schedule, Feedback, Submission
from app.schemas import (
    UserCreate, CourseCreate, AssignmentCreate, StudentCreate,
    GradebookEntryCreate, ScheduleCreate, FeedbackCreate, SubmissionCreate
)
from app.services.notification import NotificationService
from app.tasks.deadline_checker import DeadlineChecker

# Настройка тестовой базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def test_db():
    """Создание тестовой базы данных"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Создание сессии базы данных для тестов"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def override_get_db(db_session):
    """Переопределение зависимости базы данных"""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    return _override_get_db

# Фикстуры для тестовых данных

@pytest.fixture
def test_user_data():
    """Тестовые данные пользователя"""
    return {
        "email": "test@example.com",
        "first_name": "Тест",
        "last_name": "Пользователь",
        "password": "testpassword123",
        "role": "student"
    }

@pytest.fixture
def test_teacher_data():
    """Тестовые данные преподавателя"""
    return {
        "email": "teacher@example.com",
        "first_name": "Преподаватель",
        "last_name": "Тестовый",
        "password": "teacherpassword123",
        "role": "teacher"
    }

@pytest.fixture
def test_course_data():
    """Тестовые данные курса"""
    return {
        "name": "Тестовый курс",
        "code": "TEST-001",
        "description": "Описание тестового курса",
        "credits": 3
    }

@pytest.fixture
def test_assignment_data():
    """Тестовые данные задания"""
    return {
        "title": "Тестовое задание",
        "description": "Описание тестового задания",
        "due_date": datetime.utcnow() + timedelta(days=7),
        "max_score": 100,
        "assignment_type": "homework"
    }

@pytest.fixture
def test_user(db_session, test_user_data):
    """Создание тестового пользователя в базе данных"""
    user = User(
        email=test_user_data["email"],
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
        hashed_password="hashed_" + test_user_data["password"],
        role=test_user_data["role"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_teacher(db_session, test_teacher_data):
    """Создание тестового преподавателя в базе данных"""
    teacher = User(
        email=test_teacher_data["email"],
        first_name=test_teacher_data["first_name"],
        last_name=test_teacher_data["last_name"],
        hashed_password="hashed_" + test_teacher_data["password"],
        role=test_teacher_data["role"]
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher

@pytest.fixture
def test_course(db_session, test_teacher, test_course_data):
    """Создание тестового курса в базе данных"""
    course = Course(
        name=test_course_data["name"],
        code=test_course_data["code"],
        description=test_course_data["description"],
        credits=test_course_data["credits"],
        teacher_id=test_teacher.id
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course

@pytest.fixture
def test_student(db_session, test_user):
    """Создание тестового студента в базе данных"""
    student = Student(
        user_id=test_user.id,
        student_id="STU001",
        enrollment_date=datetime.utcnow().date()
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student

@pytest.fixture
def test_assignment(db_session, test_course, test_assignment_data):
    """Создание тестового задания в базе данных"""
    assignment = Assignment(
        title=test_assignment_data["title"],
        description=test_assignment_data["description"],
        due_date=test_assignment_data["due_date"],
        max_score=test_assignment_data["max_score"],
        assignment_type=test_assignment_data["assignment_type"],
        course_id=test_course.id
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment

@pytest.fixture
def test_submission(db_session, test_assignment, test_student):
    """Создание тестовой работы в базе данных"""
    submission = Submission(
        title="Тестовая работа",
        content="Содержимое тестовой работы",
        assignment_id=test_assignment.id,
        student_id=test_student.id,
        submitted_at=datetime.utcnow()
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)
    return submission

@pytest.fixture
def test_gradebook_entry(db_session, test_assignment, test_student):
    """Создание тестовой записи в журнале оценок"""
    entry = GradebookEntry(
        student_id=test_student.id,
        assignment_id=test_assignment.id,
        score=85,
        comment="Хорошая работа",
        graded_at=datetime.utcnow()
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry

@pytest.fixture
def test_schedule(db_session, test_course, test_teacher):
    """Создание тестового расписания"""
    schedule = Schedule(
        course_id=test_course.id,
        instructor_id=test_teacher.id,
        date=datetime.utcnow().date() + timedelta(days=1),
        start_time=datetime.strptime("10:00", "%H:%M").time(),
        end_time=datetime.strptime("11:30", "%H:%M").time(),
        location="Аудитория 101",
        description="Тестовая лекция"
    )
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    return schedule

@pytest.fixture
def test_feedback(db_session, test_submission, test_teacher):
    """Создание тестовой обратной связи"""
    feedback = Feedback(
        submission_id=test_submission.id,
        author_id=test_teacher.id,
        content="Отличная работа! Продолжайте в том же духе.",
        rating=5,
        created_at=datetime.utcnow()
    )
    db_session.add(feedback)
    db_session.commit()
    db_session.refresh(feedback)
    return feedback

# Фикстуры для сервисов уведомлений

@pytest.fixture
def notification_service():
    """Создание экземпляра сервиса уведомлений"""
    return NotificationService()

@pytest.fixture
def deadline_checker():
    """Создание экземпляра проверки дедлайнов"""
    return DeadlineChecker()

@pytest.fixture
def mock_webhook_response():
    """Mock ответа webhook"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    return mock_response

@pytest.fixture
def mock_requests_post(mock_webhook_response):
    """Mock для requests.post"""
    with patch('requests.post', return_value=mock_webhook_response) as mock_post:
        yield mock_post

# Фикстуры для переменных окружения

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Настройка тестового окружения"""
    # Сохранение оригинальных значений
    original_env = os.environ.copy()
    
    # Установка тестовых значений
    os.environ.update({
        "WEBHOOK_URL": "http://test-webhook.com/notifications",
        "WEBHOOK_TIMEOUT": "30",
        "DEADLINE_NOTIFICATION_DAYS": "1,3,7",
        "NOTIFICATION_ENABLED": "true",
        "LOG_LEVEL": "DEBUG"
    })
    
    yield
    
    # Восстановление оригинальных значений
    os.environ.clear()
    os.environ.update(original_env)

# Маркеры для тестов

def pytest_configure(config):
    """Конфигурация pytest"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "notification: marks tests related to notifications"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )

# Утилиты для тестов

class TestDataFactory:
    """Фабрика для создания тестовых данных"""
    
    @staticmethod
    def create_user_data(role="student", **kwargs):
        """Создание данных пользователя"""
        default_data = {
            "email": f"test_{role}@example.com",
            "first_name": "Тест",
            "last_name": "Пользователь",
            "password": "testpassword123",
            "role": role
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_course_data(**kwargs):
        """Создание данных курса"""
        default_data = {
            "name": "Тестовый курс",
            "code": "TEST-001",
            "description": "Описание тестового курса",
            "credits": 3
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_assignment_data(**kwargs):
        """Создание данных задания"""
        default_data = {
            "title": "Тестовое задание",
            "description": "Описание тестового задания",
            "due_date": datetime.utcnow() + timedelta(days=7),
            "max_score": 100,
            "assignment_type": "homework"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_notification_data(event_type="test_event", **kwargs):
        """Создание данных уведомления"""
        default_data = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": "Тестовое уведомление"
        }
        default_data.update(kwargs)
        return default_data

@pytest.fixture
def test_data_factory():
    """Фикстура фабрики тестовых данных"""
    return TestDataFactory

# Вспомогательные функции

def assert_notification_sent(mock_post, event_type=None, call_count=1):
    """Проверка отправки уведомления"""
    assert mock_post.call_count == call_count
    
    if event_type:
        call_args = mock_post.call_args
        if call_args:
            sent_data = call_args.kwargs.get("json", {})
            assert sent_data.get("event_type") == event_type

def assert_webhook_called_with_data(mock_post, expected_data):
    """Проверка вызова webhook с определенными данными"""
    assert mock_post.called
    call_args = mock_post.call_args
    sent_data = call_args.kwargs.get("json", {})
    
    for key, value in expected_data.items():
        assert sent_data.get(key) == value

# Фикстуры для mock объектов

@pytest.fixture
def mock_logger():
    """Mock для логгера"""
    with patch('app.services.notification.logger') as mock_log:
        yield mock_log

@pytest.fixture
def mock_settings():
    """Mock для настроек"""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.WEBHOOK_URL = "http://test-webhook.com/notifications"
        mock_settings.WEBHOOK_TIMEOUT = 30
        mock_settings.DEADLINE_NOTIFICATION_DAYS = [1, 3, 7]
        mock_settings.NOTIFICATION_ENABLED = True
        yield mock_settings