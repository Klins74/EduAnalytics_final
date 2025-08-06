import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.submission import Submission
from datetime import datetime, timedelta, timezone

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
TestingAsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def override_get_async_session():
    async with TestingAsyncSessionLocal() as session:
        yield session

async def create_test_user(session: AsyncSession, role: str, username: str) -> User:
    user = User(username=username, role=role, hashed_password="password")
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user

async def create_test_course(session: AsyncSession, teacher_id: int) -> Course:
    course = Course(
        title=f"Test Course by {teacher_id}", 
        description="A course for testing", 
        owner_id=teacher_id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30)
    )
    session.add(course)
    await session.flush()
    await session.refresh(course)
    return course

async def create_test_assignment(session: AsyncSession, course_id: int) -> Assignment:
    assignment = Assignment(
        title="Test Assignment", 
        description="An assignment for testing", 
        course_id=course_id,
        due_date=datetime.now(timezone.utc) + timedelta(days=15)
    )
    session.add(assignment)
    await session.flush()
    await session.refresh(assignment)
    return assignment

async def create_test_submission(session: AsyncSession, student_id: int, assignment_id: int) -> Submission:
    submission = Submission(content="Test submission content", student_id=student_id, assignment_id=assignment_id)
    session.add(submission)
    await session.flush()
    await session.refresh(submission)
    return submission