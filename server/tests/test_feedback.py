import pytest
import asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport
import sys
import os

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.feedback import Feedback
from tests.test_utils import (
    init_db,
    create_test_user, 
    create_test_course, 
    create_test_assignment, 
    create_test_submission,
    TestingAsyncSessionLocal,
    override_get_async_session
)





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

    del app.dependency_overrides[get_async_session]

@pytest.fixture(scope="function")
async def test_teacher(db_session: AsyncSession):
    return await create_test_user(db_session, role="teacher", username=f"test_teacher_{datetime.now().timestamp()}")

@pytest.fixture(scope="function")
async def test_student(db_session: AsyncSession):
    return await create_test_user(db_session, role="student", username=f"test_student_{datetime.now().timestamp()}")

@pytest.fixture(scope="function")
async def test_admin(db_session: AsyncSession):
    return await create_test_user(db_session, role="admin", username="test_admin")

@pytest.fixture(scope="function")
async def test_course(db_session: AsyncSession, test_teacher: User):
    return await create_test_course(db_session, test_teacher.id)

@pytest.fixture(scope="function")
async def test_assignment(db_session: AsyncSession, test_course: Course):
    return await create_test_assignment(db_session, test_course.id)

@pytest.fixture(scope="function")
async def test_submission(db_session: AsyncSession, test_student: User, test_assignment: Assignment):
    return await create_test_submission(db_session, test_student.id, test_assignment.id)

def override_get_current_user(user: User):
    def _override():
        return user
    return _override

@pytest.mark.asyncio
async def test_create_feedback_success(async_client: AsyncClient, test_submission: Submission, test_teacher: User):
    app.dependency_overrides[get_current_user] = override_get_current_user(test_teacher)
    
    feedback_data = {"text": "Great work! Well done."}
    response = await async_client.post(f"/api/feedback/submission/{test_submission.id}", json=feedback_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == feedback_data["text"]
    assert data["submission_id"] == test_submission.id
    assert data["user_id"] == test_teacher.id

@pytest.mark.asyncio
async def test_update_feedback_by_author(async_client: AsyncClient, db_session: AsyncSession, test_submission: Submission, test_teacher: User):
    app.dependency_overrides[get_current_user] = override_get_current_user(test_teacher)
    
    feedback = Feedback(submission_id=test_submission.id, user_id=test_teacher.id, text="Original feedback")
    db_session.add(feedback)
    await db_session.flush()
    await db_session.refresh(feedback)
    
    update_data = {"text": "Updated text"}
    response = await async_client.put(f"/api/feedback/{feedback.id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Updated text"

@pytest.mark.asyncio
async def test_delete_feedback_by_author(async_client: AsyncClient, db_session: AsyncSession, test_submission: Submission, test_teacher: User):
    app.dependency_overrides[get_current_user] = override_get_current_user(test_teacher)
    
    feedback = Feedback(submission_id=test_submission.id, user_id=test_teacher.id, text="To be deleted")
    db_session.add(feedback)
    await db_session.flush()
    await db_session.refresh(feedback)
    
    response = await async_client.delete(f"/api/feedback/{feedback.id}")
    
    assert response.status_code == 204