"""
Scheduler service for deadline and periodic notification tasks.
"""
import logging
from datetime import datetime, timezone
from typing import List
from app.core.config import settings
from app.models.assignment import Assignment
from app.models.user import User
from app.db.session import SessionLocal
import asyncio
import json

logger = logging.getLogger(__name__)

async def check_deadlines(notification_service) -> None:
    """Check assignments for upcoming deadlines and send notifications."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        notification_days = getattr(settings, 'DEADLINE_NOTIFICATION_DAYS', [7, 3, 1])
        assignments: List[Assignment] = db.query(Assignment).all()
        for assignment in assignments:
            if not getattr(assignment, 'due_date', None):
                continue
            days_left = (assignment.due_date - now).days
            if days_left in notification_days:
                students = db.query(User).filter(User.courses.any(id=assignment.course_id)).all()
                notification_data = {
                    "event_type": "deadline_approaching",
                    "assignment_id": assignment.id,
                    "title": assignment.title,
                    "due_date": assignment.due_date.isoformat(),
                    "course_name": assignment.course.name if assignment.course else None,
                    "students_list": [
                        {"student_id": s.id, "student_name": getattr(s, 'full_name', None), "student_email": getattr(s, 'email', None)}
                        for s in students
                    ]
                }
                try:
                    await notification_service.send_webhook(notification_data)
                except Exception as send_error:
                    logger.error(f"Failed to send deadline notification: {send_error}")
    except Exception as e:
        logger.error(f"Error in deadline checker: {e}")
    finally:
        db.close()

def start_deadline_scheduler(notification_service, interval: int = None) -> None:
    """Start periodic deadline checking task within running event loop."""
    interval_seconds = interval or getattr(settings, 'DEADLINE_CHECK_INTERVAL', 3600)

    async def _runner():
        while True:
            try:
                await check_deadlines(notification_service)
            except Exception as loop_error:
                logger.error(json.dumps({"event": "deadline_loop_error", "error": str(loop_error)}))
            await asyncio.sleep(interval_seconds)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.create_task(_runner())