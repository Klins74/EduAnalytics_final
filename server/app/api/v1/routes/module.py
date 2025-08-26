from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.module import ModuleCreate, ModuleRead, ModuleItemCreate
from app.crud import module as crud_module


router = APIRouter(prefix="/modules", tags=["Modules"])


@router.get("/course/{course_id}", response_model=List[ModuleRead], summary="List modules for a course")
async def list_modules(course_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_module.list_modules(db, course_id)


@router.post("/", response_model=ModuleRead, status_code=status.HTTP_201_CREATED, summary="Create module")
async def create_module(module: ModuleCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_module.create_module(db, module)


@router.post("/{module_id}/items", response_model=ModuleRead, status_code=status.HTTP_201_CREATED, summary="Add item to module")
async def add_module_item(module_id: int, item: ModuleItemCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    try:
        return await crud_module.add_module_item(db, module_id, item)
    except ValueError:
        raise HTTPException(status_code=404, detail="Module not found")


