from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.assignment_group import AssignmentGroup
from app.schemas.assignment_group import AssignmentGroupCreate, AssignmentGroupUpdate


async def list_groups(db: AsyncSession, course_id: int) -> List[AssignmentGroup]:
    result = await db.execute(
        select(AssignmentGroup).where(AssignmentGroup.course_id == course_id).order_by(AssignmentGroup.id)
    )
    return result.scalars().all()


async def create_group(db: AsyncSession, group_in: AssignmentGroupCreate) -> AssignmentGroup:
    group = AssignmentGroup(
        course_id=group_in.course_id,
        name=group_in.name,
        weight=group_in.weight,
        drop_lowest=group_in.drop_lowest,
        is_weighted=group_in.is_weighted,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def update_group(db: AsyncSession, group_id: int, group_in: AssignmentGroupUpdate) -> Optional[AssignmentGroup]:
    result = await db.execute(select(AssignmentGroup).where(AssignmentGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        return None
    for field, value in group_in.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    await db.commit()
    await db.refresh(group)
    return group




