from contextlib import asynccontextmanager
from fastapi import FastAPI
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.api.v1.routes import users, group, student, grades, course, assignment, submission, gradebook, feedback, auth, schedule, webhook, analytics, notifications, reminders, ai, module as module_routes, assignment_group as assignment_group_routes, rubric as rubric_routes, page as page_routes, discussion as discussion_routes, quiz as quiz_routes
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
from app.core.config import settings
from app.services.notification import NotificationService
from app.services.scheduler import start_deadline_scheduler
import sys
import json

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

# Sentry initialization (safe: no PII)
from app.core.config import settings as app_settings
sentry_dsn = os.getenv("SENTRY_DSN", app_settings.SENTRY_DSN)
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
        send_default_pii=False,
    )

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4028", "http://127.0.0.1:4028", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# Подключение маршрутов аналитики
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
# Подключение маршрутов электронного журнала
app.include_router(gradebook.router, prefix="/api/gradebook", tags=["Gradebook"])
# Подключение маршрутов комментариев
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(schedule.router, prefix="/api", tags=["Schedule"])
app.include_router(webhook.router, prefix="/api/v1/n8n", tags=["n8n"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["Reminders"])
app.include_router(ai.router, prefix="/api", tags=["AI"])

app.include_router(module_routes.router, prefix="/api")
app.include_router(quiz_routes.router, prefix="/api")
app.include_router(assignment_group_routes.router, prefix="/api")
app.include_router(rubric_routes.router, prefix="/api")
app.include_router(page_routes.router, prefix="/api")
app.include_router(discussion_routes.router, prefix="/api")

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

# Настройка структурированного логирования
logging.basicConfig(
    level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(getattr(settings, 'LOG_FILE_PATH', 'notifications.log'))
    ]
)

notification_service = NotificationService(settings=settings)

# Удаляем устаревший startup_event
@app.on_event("startup")
async def startup_event():
    logging.basicConfig(level=logging.INFO)
    logging.info("FastAPI startup event triggered.")
    await create_initial_data()
    logging.info(json.dumps({"event": "startup", "status": "ok", "db_url": settings.DB_URL, "db_url_sync": getattr(settings, "DB_URL_SYNC", None)}))
    if settings.DEADLINE_CHECK_ENABLED:
        start_deadline_scheduler(notification_service, interval=settings.DEADLINE_CHECK_INTERVAL)
    logging.info(json.dumps({"event": "startup", "status": "ok"}))