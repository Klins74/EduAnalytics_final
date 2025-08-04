from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.schemas.group import GroupRead, GroupCreate, GroupUpdate
from app.crud import group as crud_group
from app.db.session import get_async_session

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.get(
    "/",
    response_model=List[GroupRead],
    summary="Получить список групп",
    description="Возвращает список всех групп. Поддерживает фильтрацию по имени через query-параметр name."
)
async def get_all_groups(name: Optional[str] = None, session: AsyncSession = Depends(get_async_session)):
    """
    Получение всех групп с возможной фильтрацией по имени.
    - Если name не указан, возвращаются все группы
    - Использует асинхронную сессию SQLAlchemy
    """
    # Фильтрация по имени, если параметр передан
    return await crud_group.get_all_groups(session, name=name)

@router.get(
    "/{group_id}",
    response_model=GroupRead,
    summary="Получить группу по ID",
    description="Возвращает группу по её уникальному идентификатору. Если группа не найдена — 404."
)
async def get_group_by_id(group_id: int, session: AsyncSession = Depends(get_async_session)):
    """
    Получение группы по ID.
    - Проверяет существование группы
    - Возвращает 404, если не найдена
    """
    group = await crud_group.get_group_by_id(session, group_id)
    if not group:
        # Если группа не найдена, выбрасываем исключение
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group

@router.post(
    "/",
    response_model=GroupRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую группу",
    description="Создаёт новую группу на основе переданных данных. Возвращает созданную группу."
)
async def create_group(group_in: GroupCreate, session: AsyncSession = Depends(get_async_session)):
    """
    Создание новой группы.
    - Проверяет валидность входных данных
    - Возвращает созданную группу
    """
    return await crud_group.create_group(session, group_in)

@router.put(
    "/{group_id}",
    response_model=GroupRead,
    summary="Обновить группу",
    description="Обновляет данные группы по ID. Если группа не найдена — 404."
)
async def update_group(group_id: int, group_in: GroupUpdate, session: AsyncSession = Depends(get_async_session)):
    """
    Обновление группы по ID.
    - Обновляет только переданные поля
    - Возвращает 404, если группа не найдена
    """
    group = await crud_group.update_group(session, group_id, group_in)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group

@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить группу",
    description="Удаляет группу по ID. Если группа не найдена — 404. Возвращает пустой ответ при успехе."
)
async def delete_group(group_id: int, session: AsyncSession = Depends(get_async_session)):
    """
    Удаление группы по ID.
    - Удаляет группу, если найдена
    - Возвращает 404, если группа не найдена
    """
    result = await crud_group.delete_group(session, group_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return None