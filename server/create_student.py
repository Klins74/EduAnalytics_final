from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.student import Student
import asyncio

async def create_student():
    async with AsyncSessionLocal() as session:
        # Create user
        user = User(
            username='test_student@example.com', 
            role='student', 
            hashed_password=get_password_hash('student')
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Create student
        student = Student(
            user_id=user.id, 
            full_name='Test Student', 
            email='test_student@example.com', 
            group_id=1
        )
        session.add(student)
        await session.commit()
        
        print(f'Created student with id {student.id}, user_id {user.id}')

if __name__ == "__main__":
    asyncio.run(create_student())

