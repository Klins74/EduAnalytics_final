from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_async_session
from app.schemas.group import GroupCreate, GroupUpdate, GroupRead
from app.crud.group import get_group_by_id, get_all_groups, create_group, update_group, delete_group
from fastapi.security import OAuth2PasswordBearer
from ..routes.users import get_current_user

router = APIRouter()

@router.get("/groups", response_model=List[GroupRead], summary="Получить все группы", status_code=200)
async def read_groups(db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    groups = await get_all_groups(db)
    return groups

@router.get("/groups/{group_id}", response_model=GroupRead, summary="Получить группу по ID", status_code=200)
async def read_group(group_id: int, db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return group

@router.post("/groups", response_model=GroupRead, summary="Создать группу", status_code=201)
async def create_new_group(group_in: GroupCreate, db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    group = await create_group(db, group_in)
    return group

@router.put("/groups/{group_id}", response_model=GroupRead, summary="Обновить группу по ID", status_code=200)
async def update_existing_group(group_id: int, group_in: GroupUpdate, db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    group = await update_group(db, group_id, group_in)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return group

@router.delete("/groups/{group_id}", summary="Удалить группу по ID", status_code=204)
async def delete_existing_group(group_id: int, db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    success = await delete_group(db, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return None