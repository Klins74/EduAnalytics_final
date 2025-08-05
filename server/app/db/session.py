from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from typing import AsyncGenerator
import os

# Создание асинхронного движка SQLAlchemy
async_engine = create_async_engine(settings.DB_URL, future=True, echo=True)

# Создание асинхронной фабрики сессий
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# Dependency для FastAPI: получение асинхронной сессии
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Используем отдельный синхронный движок для создания таблиц
SYNC_DB_URL = os.getenv('DB_URL_SYNC', None) or getattr(settings, 'DB_URL_SYNC', None)
if not SYNC_DB_URL:
    # fallback: try to replace asyncpg with psycopg2 in DB_URL
    SYNC_DB_URL = (settings.DB_URL or '').replace('+asyncpg', '+psycopg2')
engine = create_engine(SYNC_DB_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)