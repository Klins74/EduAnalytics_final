from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import select
from app.api.v1.routes import users, group, student, grades, course, assignment, submission, gradebook, feedback, auth, schedule, webhook
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.group import Group
from app.crud.user import create_user as create_user_crud
from app.schemas.user import UserCreate
from passlib.context import CryptContext
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError
import logging

# Создаем контекст для хеширования пароля
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_initial_data():
    """Создает администратора и тестовую группу, если их нет."""
    async with AsyncSessionLocal() as session:
        # Проверяем, есть ли уже пользователь-админ
        result = await session.execute(select(User).where(User.role == "admin"))
        if not result.scalars().first():
            print("--- Создание начального администратора ---")
            admin_user_in = UserCreate(
                username="admin@example.com",
                role="admin",
                password="admin"
            )
            # В реальном приложении пароль нужно брать из .env
            hashed_password = pwd_context.hash(admin_user_in.password)
            admin_user = User(username=admin_user_in.username, role=admin_user_in.role, hashed_password=hashed_password)
            session.add(admin_user)
            print("--- Администратор создан ---")

        # Проверяем, есть ли уже группы
        result = await session.execute(select(Group))
        if not result.scalars().first():
            print("--- Создание тестовой группы ---")
            test_group = Group(name="Test Group")
            session.add(test_group)
            print("--- Тестовая группа создана ---")

        await session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_initial_data()
    yield

app = FastAPI(title="EduAnalytics API", lifespan=lifespan)

# Подключение маршрутов пользователей
app.include_router(users.router, prefix="/api/users", tags=["Users"])
# Подключение маршрутов групп
app.include_router(group.router, prefix="/api/groups", tags=["Groups"])
# Подключение маршрутов студентов
app.include_router(student.router, prefix="/api/students", tags=["Students"])
# Подключение маршрутов оценок
app.include_router(grades.router, prefix="/api/grades", tags=["Grades"])
# Подключение маршрутов курсов
app.include_router(course.router, prefix="/api/courses", tags=["Courses"])
# Подключение маршрутов заданий
app.include_router(assignment.router, prefix="/api/assignments", tags=["Assignments"])
# Подключение маршрутов сдач заданий
app.include_router(submission.router, prefix="/api/submissions", tags=["Submissions"])
# Подключение маршрутов электронного журнала
app.include_router(gradebook.router, prefix="/api/gradebook", tags=["Gradebook"])
# Подключение маршрутов комментариев
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(schedule.router, tags=["Schedule"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Health check endpoint
@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc.errors()} | Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
# Для расширения: добавьте middlewares, обработчики ошибок и т.д.