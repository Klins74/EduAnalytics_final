"""
Модуль для совместимости с кодом, который импортирует app.core.database.
Предоставляет ожидаемые функции для deadline_checker и webhook кода.
"""

from typing import Generator
from sqlalchemy.orm import Session

# Импорт из модуля database для совместимости
from app.database import get_db as get_db_sync

# Синхронная версия get_db для использования в webhook.py и других синхронных компонентах
def get_db() -> Generator[Session, None, None]:
    """
    Синхронная функция для получения сессии базы данных.
    Совместимость с кодом webhook и FastAPI Depends.
    """
    yield from get_db_sync()

# Экспорт для совместимости
__all__ = ["get_db"]