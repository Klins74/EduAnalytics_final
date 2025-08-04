from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.user import UserRead, UserCreate, UserUpdate
from app.crud import user as crud_user
from app.db.session import get_async_session

router = APIRouter(prefix="/users", tags=["Users"])

@router.get(
    "/",
    response_model=List[UserRead],
    summary="Получить список пользователей",
    description="Возвращает список всех пользователей в базе данных. Поддерживает асинхронный доступ и безопасное подключение к сессии."
)
async def get_all_users(session: AsyncSession = Depends(get_async_session)):
    """
    Получение всех пользователей из базы данных.
    - Использует асинхронную сессию SQLAlchemy
    - Возвращает список моделей UserRead
    """
    # Получаем всех пользователей через CRUD-слой
    return await crud_user.get_all_users(session)

@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Получить пользователя по ID",
    description="Возвращает пользователя по его уникальному идентификатору. Если пользователь не найден — 404."
)
async def get_user_by_id(user_id: int, session: AsyncSession = Depends(get_async_session)):
    """
    Получение пользователя по ID.
    - Проверяет существование пользователя
    - Возвращает 404, если не найден
    """
    user = await crud_user.get_user_by_id(session, user_id)
    if not user:
        # Если пользователь не найден, выбрасываем исключение
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать нового пользователя",
    description="Создаёт нового пользователя на основе переданных данных. Возвращает созданного пользователя."
)
async def create_user(user_in: UserCreate, session: AsyncSession = Depends(get_async_session)):
    """
    Создание нового пользователя.
    - Проверяет валидность входных данных
    - Возвращает созданного пользователя
    """
    return await crud_user.create_user(session, user_in)

@router.put(
    "/{user_id}",
    response_model=UserRead,
    summary="Обновить пользователя",
    description="Обновляет данные пользователя по ID. Если пользователь не найден — 404."
)
async def update_user(user_id: int, user_in: UserUpdate, session: AsyncSession = Depends(get_async_session)):
    """
    Обновление пользователя по ID.
    - Обновляет только переданные поля
    - Возвращает 404, если пользователь не найден
    """
    user = await crud_user.update_user(session, user_id, user_in)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользователя",
    description="Удаляет пользователя по ID. Если пользователь не найден — 404. Возвращает пустой ответ при успехе."
)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_async_session)):
    """
    Удаление пользователя по ID.
    - Удаляет пользователя, если найден
    - Возвращает 404, если пользователь не найден
    """
    result = await crud_user.delete_user(session, user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None