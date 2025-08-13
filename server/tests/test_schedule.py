import pytest
import asyncio
import datetime
import time as standard_time
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport
import sys
import os
from fastapi import status

from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.user import User, UserRole
from main import app
from app.models.course import Course
from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.crud.schedule import schedule_crud
from tests.test_utils import (
    init_db,
    create_test_user, 
    create_test_course,
    TestingAsyncSessionLocal,
    override_get_async_session
)
import subprocess

def override_get_current_user(user: User):
    def _override():
        return user
    return _override


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    await init_db()

@pytest.fixture(scope="function")
async def db_session():
    async with TestingAsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
async def async_client(db_session):
    async def override_get_async_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """Создать пользователя-администратора для тестов."""
    return await create_test_user(
        db_session, 
        role=UserRole.admin,
        username="admin"
    )


@pytest.fixture(scope="function")
async def teacher_user(db_session: AsyncSession) -> User:
    """Создать пользователя-преподавателя для тестов."""
    return await create_test_user(
        db_session, 
        role=UserRole.teacher,
        username="teacher"
    )


@pytest.fixture(scope="function")
async def student_user(db_session: AsyncSession) -> User:
    """Создать пользователя-студента для тестов."""
    return await create_test_user(
        db_session, 
        role=UserRole.student,
        username="student"
    )


@pytest.fixture(scope="function")
async def test_course(db_session: AsyncSession, teacher_user: User) -> Course:
    """Создать тестовый курс."""
    return await create_test_course(
        db_session,
        teacher_id=teacher_user.id
    )


@pytest.fixture(scope="function")
async def test_schedule(db_session: AsyncSession, test_course: Course, teacher_user: User) -> Schedule:
    """Создать тестовое расписание."""
    schedule = Schedule(
        course_id=test_course.id,
        schedule_date=date.today() + timedelta(days=1),
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 30),
        location="Room 101",
        instructor_id=teacher_user.id
    )
    db_session.add(schedule)
    await db_session.flush()
    await db_session.refresh(schedule)
    return schedule


class TestScheduleCRUD:
    """Тесты для CRUD операций с расписанием."""

    async def test_create_schedule_success(self, db_session: AsyncSession, test_course: Course, teacher_user: User):
        """Тест успешного создания расписания."""
        schedule_data = ScheduleCreate(
            course_id=test_course.id,
            schedule_date=date.today() + timedelta(days=1),
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 30),
            location="Room 202",
            instructor_id=teacher_user.id
        )
        
        schedule = await schedule_crud.create_schedule(
            db=db_session,
            schedule_data=schedule_data,
            current_user=teacher_user
        )
        
        assert schedule.course_id == test_course.id
        assert schedule.schedule_date == schedule_data.schedule_date
        assert schedule.start_time == schedule_data.start_time
        assert schedule.end_time == schedule_data.end_time
        assert schedule.location == schedule_data.location
        assert schedule.instructor_id == teacher_user.id

    async def test_create_schedule_permission_denied(self, db_session: AsyncSession, test_course: Course, student_user: User):
        """Тест отказа в создании расписания для студента."""
        schedule_data = ScheduleCreate(
            course_id=test_course.id,
            schedule_date=date.today() + timedelta(days=1),
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 30),
            location="Room 202",
            instructor_id=student_user.id
        )
        
        with pytest.raises(Exception) as exc_info:
            await schedule_crud.create_schedule(
                db=db_session,
                schedule_data=schedule_data,
                current_user=student_user
            )
        
        assert "Только преподаватели и администраторы" in str(exc_info.value)

    async def test_create_schedule_time_conflict(self, db_session: AsyncSession, test_course: Course, teacher_user: User, test_schedule: Schedule):
        """Тест конфликта времени при создании расписания."""
        schedule_data = ScheduleCreate(
            course_id=test_course.id,
            schedule_date=test_schedule.schedule_date,
            start_time=datetime.time(10, 30),  # Пересекается с существующим расписанием
            end_time=datetime.time(12, 0),
            location="Аудитория 102",
            instructor_id=test_schedule.instructor_id
        )
        
        with pytest.raises(Exception) as exc_info:
            await schedule_crud.create_schedule(
                db=db_session,
                schedule_data=schedule_data,
                current_user=teacher_user
            )
        
        assert "уже есть занятие в это время" in str(exc_info.value)

    async def test_get_schedules_with_filters(self, db_session: AsyncSession, test_schedule: Schedule):
        """Тест получения расписаний с фильтрацией."""
        # Тест фильтрации по курсу
        schedules, total = await schedule_crud.get_schedules(
            db=db_session,
            course_id=test_schedule.course_id
        )
        assert total == 1
        assert schedules[0].id == test_schedule.id
        
        # Тест фильтрации по дате
        schedules, total = await schedule_crud.get_schedules(
            db=db_session,
            date_from=test_schedule.schedule_date,
            date_to=test_schedule.schedule_date
        )
        assert total == 1
        assert schedules[0].id == test_schedule.id
        
        # Тест фильтрации по преподавателю
        schedules, total = await schedule_crud.get_schedules(
            db=db_session,
            instructor_id=test_schedule.instructor_id
        )
        assert total == 1
        assert schedules[0].id == test_schedule.id

    async def test_update_schedule_success(self, db_session: AsyncSession, test_schedule: Schedule, teacher_user: User):
        """Тест успешного обновления расписания."""
        update_data = ScheduleUpdate(
            location="Updated Room 303",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 30)
        )
        
        updated_schedule = await schedule_crud.update_schedule(
            db=db_session,
            schedule_id=test_schedule.id,
            schedule_update=update_data,
            current_user=teacher_user
        )
        
        assert updated_schedule.location == "Updated Room 303"
        assert updated_schedule.start_time == datetime.time(9, 0)
        assert updated_schedule.end_time == datetime.time(10, 30)

    async def test_delete_schedule_success(self, db_session: AsyncSession, test_schedule: Schedule, teacher_user: User):
        """Тест успешного удаления расписания."""
        deleted = await schedule_crud.delete_schedule(
            db=db_session,
            schedule_id=test_schedule.id,
            current_user=teacher_user
        )
        
        assert deleted is True
        
        # Проверяем, что расписание действительно удалено
        schedule = await schedule_crud.get(db_session, test_schedule.id)
        assert schedule is None


class TestScheduleAPI:
    """Тесты для API эндпоинтов расписания."""

    async def test_get_schedules_endpoint(self, async_client: AsyncClient, test_schedule: Schedule, teacher_user: User):
        """Тест эндпоинта получения списка расписаний."""
        app.dependency_overrides[get_current_user] = override_get_current_user(teacher_user)
        
        response = await async_client.get("/api/schedule/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "schedules" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_get_schedules_with_filters_endpoint(self, async_client: AsyncClient, test_schedule: Schedule, teacher_user: User):
        """Тест эндпоинта получения расписаний с фильтрами."""
        app.dependency_overrides[get_current_user] = override_get_current_user(teacher_user)
        
        response = await async_client.get(
            f"/api/schedule/?course_id={test_schedule.course_id}&date_from={test_schedule.schedule_date}&date_to={test_schedule.schedule_date}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1

    async def test_get_schedule_by_id_endpoint(self, async_client: AsyncClient, test_schedule: Schedule, teacher_user: User):
        """Тест эндпоинта получения расписания по ID."""
        app.dependency_overrides[get_current_user] = override_get_current_user(teacher_user)
        
        response = await async_client.get(f"/api/schedule/{test_schedule.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_schedule.id
        assert data["course_id"] == test_schedule.course_id

    async def test_create_schedule_endpoint(self, async_client: AsyncClient, test_course: Course, teacher_user: User):
        """Тест эндпоинта создания расписания."""
        app.dependency_overrides[get_current_user] = override_get_current_user(teacher_user)
        
        schedule_data = {
            "course_id": test_course.id,
            "schedule_date": str(date.today() + timedelta(days=1)),
            "start_time": datetime.time(14, 0).strftime("%H:%M:%S"),
            "end_time": datetime.time(15, 30).strftime("%H:%M:%S"),
            "location": "Room 202",
            "instructor_id": teacher_user.id
        }
        
        response = await async_client.post("/api/schedule/", json=schedule_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["course_id"] == test_course.id
        assert data["location"] == "Room 202"

    async def test_create_schedule_permission_denied_endpoint(self, async_client: AsyncClient, test_course: Course, student_user: User):
        """Тест запрета создания расписания студентом."""
        app.dependency_overrides[get_current_user] = override_get_current_user(student_user)
        
        schedule_data = {
            "course_id": test_course.id,
            "schedule_date": str(date.today() + timedelta(days=1)),
            "start_time": datetime.time(14, 0).strftime("%H:%M:%S"),
            "end_time": datetime.time(15, 30).strftime("%H:%M:%S"),
            "location": "Room 202",
            "instructor_id": student_user.id
        }
        
        response = await async_client.post("/api/schedule/", json=schedule_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_schedule_endpoint(self, async_client: AsyncClient, test_schedule: Schedule, teacher_user: User):
        """Тест эндпоинта обновления расписания."""
        app.dependency_overrides[get_current_user] = override_get_current_user(teacher_user)
        
        update_data = {
            "location": "Updated Room 505",
            "start_time": datetime.time(9, 0).strftime("%H:%M:%S"),
        }
        
        response = await async_client.put(f"/api/schedule/{test_schedule.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["location"] == "Updated Room 505"
        assert data["start_time"] == "09:00:00"

    async def test_delete_schedule_endpoint(self, async_client: AsyncClient, test_schedule: Schedule, teacher_user: User):
        """Тест эндпоинта удаления расписания."""
        app.dependency_overrides[get_current_user] = override_get_current_user(teacher_user)
        
        response = await async_client.delete(f"/api/schedule/{test_schedule.id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Проверяем, что расписание действительно удалено
        get_response = await async_client.get(f"/api/schedule/{test_schedule.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_schedule_permission_denied_endpoint(self, async_client: AsyncClient, test_schedule: Schedule, student_user: User):
        """Тест запрета обновления расписания студентом."""
        app.dependency_overrides[get_current_user] = override_get_current_user(student_user)
        
        update_data = {
            "location": "Hacked Room"
        }
        
        response = await async_client.put(f"/api/schedule/{test_schedule.id}", json=update_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_invalid_date_range_filter(self, async_client: AsyncClient, teacher_user: User):
        """Тест валидации некорректного диапазона дат."""
        app.dependency_overrides[get_current_user] = override_get_current_user(teacher_user)
        
        response = await async_client.get(
            f"/api/schedule/?date_from={date.today() + timedelta(days=5)}&date_to={date.today()}"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Начальная дата не может быть больше конечной" in response.json()["detail"]