"""
Модуль для асинхронных CRUD-операций с сущностью Group.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.group import Group
from app.models.student import Student
from app.schemas.group import GroupCreate, GroupUpdate
from typing import List, Optional

async def get_group_by_id(db: AsyncSession, group_id: int) -> Optional[Group]:
    """
    Получить группу по её ID с подгрузкой студентов.
    :param db: Асинхронная сессия БД
    :param group_id: ID группы
    :return: Объект Group или None
    """
    result = await db.execute(
        select(Group).options(selectinload(Group.students)).where(Group.id == group_id)
    )
    return result.scalar_one_or_none()

async def get_all_groups(db: AsyncSession, name: Optional[str] = None) -> List[Group]:
    """
    Получить список всех групп, опционально фильтруя по имени.
    :param db: Асинхронная сессия БД
    :param name: (Необязательно) фильтр по имени группы
    :return: Список объектов Group
    """
    query = select(Group).options(selectinload(Group.students))
    if name:
        query = query.where(Group.name.ilike(f"%{name}%"))
    result = await db.execute(query)
    return result.scalars().all()

async def create_group(db: AsyncSession, group_in: GroupCreate) -> Group:
    """
    Создать новую группу.
    :param db: Асинхронная сессия БД
    :param group_in: Данные для создания группы
    :return: Созданный объект Group
    """
    group = Group(**group_in.dict())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group

async def update_group(db: AsyncSession, group_id: int, group_in: GroupUpdate) -> Optional[Group]:
    """
    Обновить данные группы по её ID.
    :param db: Асинхронная сессия БД
    :param group_id: ID группы
    :param group_in: Данные для обновления
    :return: Обновлённый объект Group или None
    """
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        return None
    update_data = group_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group

async def delete_group(db: AsyncSession, group_id: int) -> bool:
    """
    Удалить группу по её ID.
    :param db: Асинхронная сессия БД
    :param group_id: ID группы
    :return: True, если удаление прошло успешно, иначе False
    """
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        return False
    await db.delete(group)
    await db.commit()
    return True