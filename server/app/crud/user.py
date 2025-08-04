"""
Модуль для асинхронных CRUD-операций с сущностью User.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from typing import List, Optional

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Получить пользователя по его ID.
    :param db: Асинхронная сессия БД
    :param user_id: ID пользователя
    :return: Объект User или None
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_all_users(db: AsyncSession) -> List[User]:
    """
    Получить список всех пользователей.
    :param db: Асинхронная сессия БД
    :return: Список объектов User
    """
    result = await db.execute(select(User))
    return result.scalars().all()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """
    Создать нового пользователя.
    :param db: Асинхронная сессия БД
    :param user_in: Данные для создания пользователя
    :return: Созданный объект User
    """
    user = User(**user_in.dict())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_user(db: AsyncSession, user_id: int, user_in: UserUpdate) -> Optional[User]:
    """
    Обновить данные пользователя по его ID.
    :param db: Асинхронная сессия БД
    :param user_id: ID пользователя
    :param user_in: Данные для обновления
    :return: Обновлённый объект User или None
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    update_data = user_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    Удалить пользователя по его ID.
    :param db: Асинхронная сессия БД
    :param user_id: ID пользователя
    :return: True, если удаление прошло успешно, иначе False
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True