from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.rubric import RubricCreate, RubricRead
from app.crud import rubric as crud_rubric


router = APIRouter(prefix="/rubrics", tags=["Rubrics"])


@router.get("/course/{course_id}", response_model=List[RubricRead], summary="List rubrics for a course")
async def list_rubrics(course_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_rubric.list_rubrics(db, course_id)


@router.get("/{rubric_id}", response_model=RubricRead, summary="Get rubric")
async def get_rubric(rubric_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    rb = await crud_rubric.get_rubric(db, rubric_id)
    if not rb:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return rb


@router.post("/", response_model=RubricRead, status_code=status.HTTP_201_CREATED, summary="Create rubric")
async def create_rubric(rubric: RubricCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_rubric.create_rubric(db, rubric)




