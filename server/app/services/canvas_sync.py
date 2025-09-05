from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.crud.canvas_sync import canvas_sync_crud
from app.services.canvas_client import canvas_client
from app.crud.canvas_data import canvas_data_crud
from datetime import datetime, timedelta, timezone


class CanvasSyncService:
    async def sync_courses(self, user_id: int) -> int:
        """Sync basic courses list for a user (placeholder to persist as needed)."""
        data = await canvas_client.list_paginated("/api/v1/courses", user_id=user_id)
        async with AsyncSessionLocal() as db:
            await canvas_data_crud.upsert_courses(db, owner_user_id=user_id, items=data)
            await canvas_sync_crud.update(db, scope=f"courses:user:{user_id}", extra={"count": len(data)})
        return len(data)

    async def sync_course_enrollments(self, user_id: int, course_id: int) -> int:
        since_days = getattr(settings, 'CANVAS_SYNC_SINCE_DAYS', 7)
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        data = await canvas_client.list_since(f"/api/v1/courses/{course_id}/enrollments", user_id=user_id, since_iso=since)
        async with AsyncSessionLocal() as db:
            n = await canvas_data_crud.upsert_enrollments(db, course_canvas_id=course_id, items=data)
            await canvas_sync_crud.update(db, scope=f"course:{course_id}:enrollments", extra={"count": n})
            return n

    async def sync_course_assignments(self, user_id: int, course_id: int) -> int:
        since_days = getattr(settings, 'CANVAS_SYNC_SINCE_DAYS', 7)
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        data = await canvas_client.list_since(f"/api/v1/courses/{course_id}/assignments", user_id=user_id, since_iso=since)
        async with AsyncSessionLocal() as db:
            n = await canvas_data_crud.upsert_assignments(db, course_canvas_id=course_id, items=data)
            await canvas_sync_crud.update(db, scope=f"course:{course_id}:assignments", extra={"count": n})
            return n

    async def sync_assignment_submissions(self, user_id: int, course_id: int, assignment_id: int) -> int:
        since_days = getattr(settings, 'CANVAS_SYNC_SINCE_DAYS', 7)
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        data = await canvas_client.list_since(
            f"/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions",
            user_id=user_id,
            since_iso=since
        )
        async with AsyncSessionLocal() as db:
            n = await canvas_data_crud.upsert_submissions(db, course_canvas_id=course_id, assignment_canvas_id=assignment_id, items=data)
            await canvas_sync_crud.update(db, scope=f"course:{course_id}:assignment:{assignment_id}:submissions", extra={"count": n})
            return n


canvas_sync_service = CanvasSyncService()


