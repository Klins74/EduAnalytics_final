from fastapi import FastAPI
from app.api.v1.routes import users, group, student, auth

app = FastAPI(title="EduAnalytics API")

# Подключение маршрутов пользователей
app.include_router(users.router, prefix="/api", tags=["Users"])
# Подключение маршрутов групп
app.include_router(group.router, prefix="/api/groups", tags=["Groups"])
# Подключение маршрутов студентов
app.include_router(student.router, prefix="/api/students", tags=["Students"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Health check endpoint
@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok"}

# Для расширения: добавьте middlewares, обработчики ошибок и т.д.