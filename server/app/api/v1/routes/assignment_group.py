from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.assignment_group import AssignmentGroupCreate, AssignmentGroupUpdate, AssignmentGroupRead
from app.crud import assignment_group as crud_group


router = APIRouter(prefix="/assignment-groups", tags=["Assignment Groups"])


@router.get("/course/{course_id}", response_model=List[AssignmentGroupRead], summary="List assignment groups for a course")
async def list_groups(course_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_group.list_groups(db, course_id)


@router.post("/", response_model=AssignmentGroupRead, status_code=status.HTTP_201_CREATED, summary="Create assignment group")
async def create_group(group: AssignmentGroupCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_group.create_group(db, group)


@router.put("/{group_id}", response_model=AssignmentGroupRead, summary="Update assignment group")
async def update_group(group_id: int, group: AssignmentGroupUpdate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    updated = await crud_group.update_group(db, group_id, group)
    if not updated:
        raise HTTPException(status_code=404, detail="Assignment group not found")
    return updated




