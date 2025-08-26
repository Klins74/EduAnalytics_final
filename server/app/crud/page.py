from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.page import Page
from app.schemas.page import PageCreate, PageUpdate


async def list_pages(db: AsyncSession, course_id: int) -> List[Page]:
    result = await db.execute(select(Page).where(Page.course_id == course_id).order_by(Page.id))
    return result.scalars().all()


async def create_page(db: AsyncSession, page_in: PageCreate, author_id: Optional[int]) -> Page:
    page = Page(
        course_id=page_in.course_id,
        title=page_in.title,
        slug=page_in.slug,
        body=page_in.body,
        published=page_in.published,
        author_id=author_id,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


async def update_page(db: AsyncSession, page_id: int, page_in: PageUpdate) -> Optional[Page]:
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        return None
    for field, value in page_in.model_dump(exclude_unset=True).items():
        setattr(page, field, value)
    await db.commit()
    await db.refresh(page)
    return page




