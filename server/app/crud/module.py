from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.module import Module, ModuleItem, ModuleItemType
from app.schemas.module import ModuleCreate, ModuleItemCreate


async def list_modules(db: AsyncSession, course_id: int) -> List[Module]:
    result = await db.execute(
        select(Module)
        .options(selectinload(Module.items))
        .where(Module.course_id == course_id)
        .order_by(Module.position, Module.id)
    )
    return result.scalars().all()


async def get_module(db: AsyncSession, module_id: int) -> Optional[Module]:
    result = await db.execute(
        select(Module)
        .options(selectinload(Module.items))
        .where(Module.id == module_id)
    )
    return result.scalar_one_or_none()


async def create_module(db: AsyncSession, module_in: ModuleCreate) -> Module:
    module = Module(
        course_id=module_in.course_id,
        name=module_in.name,
        position=module_in.position,
        published=module_in.published,
        unlock_at=module_in.unlock_at,
    )
    db.add(module)
    await db.flush()

    if module_in.items:
        for idx, item in enumerate(module_in.items):
            db.add(ModuleItem(
                module_id=module.id,
                title=item.title,
                type=ModuleItemType(item.type),
                content_id=item.content_id,
                position=item.position if item.position is not None else idx,
                indent=item.indent,
                published=item.published,
            ))

    await db.commit()

    # Re-fetch with eager loading to avoid MissingGreenlet during serialization
    result = await db.execute(
        select(Module)
        .options(selectinload(Module.items))
        .where(Module.id == module.id)
    )
    return result.scalar_one()


async def add_module_item(db: AsyncSession, module_id: int, item_in: ModuleItemCreate) -> Module:
    # Ensure module exists
    module_result = await db.execute(
        select(Module).where(Module.id == module_id)
    )
    module = module_result.scalar_one_or_none()
    if not module:
        raise ValueError("Module not found")

    db.add(ModuleItem(
        module_id=module_id,
        title=item_in.title,
        type=ModuleItemType(item_in.type),
        content_id=item_in.content_id,
        position=item_in.position,
        indent=item_in.indent,
        published=item_in.published,
    ))

    await db.commit()

    # Return module with items
    result = await db.execute(
        select(Module).options(selectinload(Module.items)).where(Module.id == module_id)
    )
    return result.scalar_one()


