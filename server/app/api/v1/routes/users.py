from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_async_session
from app.schemas.user import UserCreate, UserUpdate, UserRead
from app.crud.user import get_user_by_id, get_all_users, create_user, update_user, delete_user

router = APIRouter()

@router.get("/users", response_model=List[UserRead], summary="Получить всех пользователей", description="Возвращает список всех пользователей.", status_code=200)
async def read_users(db: AsyncSession = Depends(get_async_session)):
    users = await get_all_users(db)
    return users

@router.get("/users/{user_id}", response_model=UserRead, summary="Получить пользователя по ID", description="Возвращает пользователя по его уникальному идентификатору.", status_code=200)
async def read_user(user_id: int, db: AsyncSession = Depends(get_async_session)):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.post("/users", response_model=UserRead, summary="Создать пользователя", description="Создаёт нового пользователя.", status_code=201)
async def create_new_user(user_in: UserCreate, db: AsyncSession = Depends(get_async_session)):
    user = await create_user(db, user_in)
    return user

@router.put("/users/{user_id}", response_model=UserRead, summary="Обновить пользователя по ID", description="Обновляет данные пользователя по его ID.", status_code=200)
async def update_existing_user(user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(get_async_session)):
    user = await update_user(db, user_id, user_in)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.delete("/users/{user_id}", summary="Удалить пользователя по ID", description="Удаляет пользователя по его ID.", status_code=204)
async def delete_existing_user(user_id: int, db: AsyncSession = Depends(get_async_session)):
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return None