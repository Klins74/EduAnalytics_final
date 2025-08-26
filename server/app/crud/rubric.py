from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.rubric import Rubric, RubricCriterion
from app.schemas.rubric import RubricCreate


async def list_rubrics(db: AsyncSession, course_id: int) -> List[Rubric]:
    result = await db.execute(
        select(Rubric)
        .options(selectinload(Rubric.criteria))
        .where(Rubric.course_id == course_id)
        .order_by(Rubric.id)
    )
    return result.scalars().all()


async def get_rubric(db: AsyncSession, rubric_id: int) -> Optional[Rubric]:
    result = await db.execute(
        select(Rubric)
        .options(selectinload(Rubric.criteria))
        .where(Rubric.id == rubric_id)
    )
    return result.scalar_one_or_none()


async def create_rubric(db: AsyncSession, rubric_in: RubricCreate) -> Rubric:
    rubric = Rubric(
        course_id=rubric_in.course_id,
        title=rubric_in.title,
        description=rubric_in.description,
        total_points=rubric_in.total_points,
    )
    db.add(rubric)
    await db.flush()

    if rubric_in.criteria:
        for idx, c in enumerate(rubric_in.criteria):
            db.add(RubricCriterion(
                rubric_id=rubric.id,
                description=c.description,
                points=c.points,
                position=c.position if c.position is not None else idx,
            ))

    await db.commit()

    # Re-fetch with eager loading to avoid MissingGreenlet during serialization
    result = await db.execute(
        select(Rubric)
        .options(selectinload(Rubric.criteria))
        .where(Rubric.id == rubric.id)
    )
    return result.scalar_one()


