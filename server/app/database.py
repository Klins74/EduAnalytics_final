"""
Модуль для совместимости с тестами и старым кодом.
Предоставляет единый интерфейс для работы с базой данных.
"""

from typing import Generator, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

# Импорт из новых модулей
from app.db.base import Base
from app.db.session import SessionLocal, AsyncSessionLocal, get_async_session

# Синхронная функция get_db для тестов и старого кода
def get_db() -> Generator[Session, None, None]:
    """
    Синхронная функция для получения сессии базы данных.
    Используется в тестах и legacy коде.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Асинхронная версия для deadline_checker и других async задач
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронная функция для получения сессии базы данных.
    Используется в async задачах.
    """
    async with AsyncSessionLocal() as session:
        yield session

# Экспорт всех необходимых символов для совместимости
__all__ = [
    "Base",
    "get_db", 
    "get_async_db",
    "SessionLocal",
    "AsyncSessionLocal",
    "get_async_session"
]