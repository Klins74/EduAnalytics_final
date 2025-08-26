from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.page import PageCreate, PageUpdate, PageRead
from app.crud import page as crud_page


router = APIRouter(prefix="/pages", tags=["Pages"])


@router.get("/course/{course_id}", response_model=List[PageRead])
async def list_pages(course_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_page.list_pages(db, course_id)


@router.post("/", response_model=PageRead, status_code=status.HTTP_201_CREATED)
async def create_page(page: PageCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_page.create_page(db, page, author_id=current_user.id)


@router.put("/{page_id}", response_model=PageRead)
async def update_page(page_id: int, page: PageUpdate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    updated = await crud_page.update_page(db, page_id, page)
    if not updated:
        raise HTTPException(status_code=404, detail="Page not found")
    return updated




