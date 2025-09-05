from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.canvas_data import (
    CanvasCourse,
    CanvasEnrollment,
    CanvasAssignment,
    CanvasSubmission,
)


class CanvasDataCRUD:
    async def upsert_courses(self, db: AsyncSession, owner_user_id: int, items: Iterable[dict]) -> int:
        count = 0
        for it in items:
            cid = int(it.get('id'))
            res = await db.execute(select(CanvasCourse).where(CanvasCourse.canvas_id == cid))
            obj = res.scalar_one_or_none()
            if obj:
                obj.data = it
                obj.owner_user_id = owner_user_id
            else:
                obj = CanvasCourse(canvas_id=cid, owner_user_id=owner_user_id, data=it)
                db.add(obj)
            count += 1
        await db.commit()
        return count

    async def upsert_assignments(self, db: AsyncSession, course_canvas_id: int, items: Iterable[dict]) -> int:
        count = 0
        for it in items:
            aid = int(it.get('id'))
            res = await db.execute(select(CanvasAssignment).where(CanvasAssignment.canvas_id == aid))
            obj = res.scalar_one_or_none()
            if obj:
                obj.data = it
                obj.course_canvas_id = course_canvas_id
            else:
                obj = CanvasAssignment(canvas_id=aid, course_canvas_id=course_canvas_id, data=it)
                db.add(obj)
            count += 1
        await db.commit()
        return count

    async def upsert_enrollments(self, db: AsyncSession, course_canvas_id: int, items: Iterable[dict]) -> int:
        count = 0
        for it in items:
            eid = int(it.get('id'))
            res = await db.execute(select(CanvasEnrollment).where(CanvasEnrollment.canvas_id == eid))
            obj = res.scalar_one_or_none()
            if obj:
                obj.data = it
                obj.course_canvas_id = course_canvas_id
            else:
                obj = CanvasEnrollment(canvas_id=eid, course_canvas_id=course_canvas_id, data=it)
                db.add(obj)
            count += 1
        await db.commit()
        return count

    async def upsert_submissions(self, db: AsyncSession, course_canvas_id: int, assignment_canvas_id: int, items: Iterable[dict]) -> int:
        count = 0
        for it in items:
            sid = int(it.get('id')) if it.get('id') is not None else int(it.get('user_id', 0)) * 10_000_000 + int(assignment_canvas_id)
            res = await db.execute(select(CanvasSubmission).where(CanvasSubmission.canvas_id == sid))
            obj = res.scalar_one_or_none()
            if obj:
                obj.data = it
                obj.assignment_canvas_id = assignment_canvas_id
                obj.course_canvas_id = course_canvas_id
            else:
                obj = CanvasSubmission(
                    canvas_id=sid,
                    assignment_canvas_id=assignment_canvas_id,
                    course_canvas_id=course_canvas_id,
                    data=it,
                )
                db.add(obj)
            count += 1
        await db.commit()
        return count


canvas_data_crud = CanvasDataCRUD()


