from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_async_session
from app.schemas.group import GroupCreate, GroupUpdate, GroupRead
from app.crud.group import get_group_by_id, get_all_groups, create_group, update_group, delete_group
from app.core.security import get_current_user, require_role
from app.models.user import UserRole
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.get("/", response_model=List[GroupRead], summary="Получить все группы", status_code=200)
async def read_groups(db: AsyncSession = Depends(get_async_session), current_user = Depends(get_current_user)):
    return await get_all_groups(db)

@router.get("/{group_id}", response_model=GroupRead, summary="Получить группу по ID", status_code=200)
async def read_group(group_id: int, db: AsyncSession = Depends(get_async_session), current_user = Depends(get_current_user)):
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return group

@router.post("/", response_model=GroupRead, summary="Создать группу", status_code=201)
async def create_new_group(group_in: GroupCreate, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.teacher, UserRole.admin))):
    try:
        print("create_new_group input:", group_in)
        group = await create_group(db, group_in)
        print("created group:", group)
        return group
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Группа с именем '{group_in.name}' уже существует.",
        )
    except Exception as e:
        import traceback
        print("Exception in create_new_group:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{group_id}", response_model=GroupRead, summary="Обновить группу по ID", status_code=200)
async def update_existing_group(group_id: int, group_in: GroupUpdate, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.teacher, UserRole.admin))):
    group = await update_group(db, group_id, group_in)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return group

@router.delete("/{group_id}", summary="Удалить группу по ID", status_code=204)
async def delete_existing_group(group_id: int, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.admin))):
    success = await delete_group(db, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return None