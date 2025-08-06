import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from tests.test_utils import TestingAsyncSessionLocal, create_test_user, init_db
from datetime import datetime

@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_user_creation():
    """Tests direct database interaction without the HTTP client."""
    async with TestingAsyncSessionLocal() as session:
        username = f"direct_test_user_{datetime.now().timestamp()}"
        user = await create_test_user(session, role="student", username=username)
        assert user.id is not None
        assert user.role == "student"

        # Verify it's in the DB by retrieving it in the same session
        retrieved_user = await session.get(User, user.id)
        assert retrieved_user is not None
        assert retrieved_user.username == username