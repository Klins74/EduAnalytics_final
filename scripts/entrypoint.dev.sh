#!/bin/bash
# Development entrypoint script for EduAnalytics

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting EduAnalytics in development mode...${NC}"

# Wait for database to be ready
echo -e "${YELLOW}Waiting for database...${NC}"
while ! pg_isready -h ${DB_HOST:-postgres-dev} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres}; do
    echo "Database is unavailable - sleeping"
    sleep 2
done
echo -e "${GREEN}Database is ready!${NC}"

# Wait for Redis to be ready
echo -e "${YELLOW}Waiting for Redis...${NC}"
while ! redis-cli -h ${REDIS_HOST:-redis-dev} -p ${REDIS_PORT:-6379} ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo -e "${GREEN}Redis is ready!${NC}"

# Install development dependencies if needed
if [ ! -f "/app/.dev_deps_installed" ]; then
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    pip install -e .
    touch /app/.dev_deps_installed
fi

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
cd /app
python -c "
import asyncio
from app.db.init_db import init_db

async def main():
    await init_db()
    print('Database initialized successfully')

try:
    asyncio.run(main())
except Exception as e:
    print(f'Error initializing database: {e}')
    # Continue anyway in development
"

# Create uploads directory if it doesn't exist
mkdir -p /app/uploads/submissions
mkdir -p /app/uploads/temp
mkdir -p /app/logs

# Create test data in development
echo -e "${YELLOW}Creating test data...${NC}"
python -c "
import asyncio
import os
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.crud.user import create_user
from app.schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def create_test_users():
    async with AsyncSessionLocal() as db:
        # Check if admin exists
        admin_exists = await db.get(User, 1)
        if not admin_exists:
            admin_data = UserCreate(
                username='admin@dev.local',
                email='admin@dev.local',
                password='admin123',
                role=UserRole.admin,
                first_name='Admin',
                last_name='User'
            )
            admin_user = await create_user(db, admin_data)
            print(f'Created admin user: {admin_user.username}')
        
        # Create test teacher
        teacher_exists = await db.get(User, 2)
        if not teacher_exists:
            teacher_data = UserCreate(
                username='teacher@dev.local',
                email='teacher@dev.local',
                password='teacher123',
                role=UserRole.teacher,
                first_name='Test',
                last_name='Teacher'
            )
            teacher_user = await create_user(db, teacher_data)
            print(f'Created teacher user: {teacher_user.username}')
        
        # Create test student
        student_exists = await db.get(User, 3)
        if not student_exists:
            student_data = UserCreate(
                username='student@dev.local',
                email='student@dev.local',
                password='student123',
                role=UserRole.student,
                first_name='Test',
                last_name='Student'
            )
            student_user = await create_user(db, student_data)
            print(f'Created student user: {student_user.username}')

try:
    asyncio.run(create_test_users())
except Exception as e:
    print(f'Error creating test users: {e}')
"

# Start application
echo -e "${GREEN}Starting EduAnalytics development server...${NC}"
echo -e "${YELLOW}Available at: http://localhost:8000${NC}"
echo -e "${YELLOW}API docs at: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}Command: $@${NC}"

# Execute the command passed to the container
exec "$@"
