from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.canvas_sync import CanvasSyncState


class CanvasSyncCRUD:
    async def get_or_create(self, db: AsyncSession, scope: str) -> CanvasSyncState:
        res = await db.execute(select(CanvasSyncState).where(CanvasSyncState.scope == scope))
        state = res.scalar_one_or_none()
        if state:
            return state
        state = CanvasSyncState(scope=scope)
        db.add(state)
        await db.commit()
        await db.refresh(state)
        return state

    async def update(self, db: AsyncSession, scope: str, **kwargs) -> CanvasSyncState:
        state = await self.get_or_create(db, scope)
        for k, v in kwargs.items():
            setattr(state, k, v)
        await db.commit()
        await db.refresh(state)
        return state


canvas_sync_crud = CanvasSyncCRUD()


