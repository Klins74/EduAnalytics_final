"""
Модуль для асинхронных CRUD-операций с сущностью User.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from typing import List, Optional
from passlib.context import CryptContext

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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """
    Создать нового пользователя с хешированием пароля.
    """
    try:
        print("[CRUD] create_user input:", user_in)
        user_data = user_in.dict(exclude={"password"})
        hashed_password = pwd_context.hash(user_in.password)
        user = User(**user_data, hashed_password=hashed_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print("[CRUD] created user:", user)
        return user
    except Exception as e:
        import traceback
        print("[CRUD] Exception in create_user:", e)
        traceback.print_exc()
        await db.rollback()
        raise

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