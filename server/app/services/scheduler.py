"""
Scheduler service for deadline and periodic notification tasks.
"""
import logging
from datetime import datetime, timedelta
from typing import List
from app.core.config import settings
from app.services.notification import NotificationService
from app.models.assignment import Assignment
from app.models.user import User
from app.db.session import SessionLocal
import asyncio
import json

logger = logging.getLogger(__name__)

async def check_deadlines(notification_service):
    """Check assignments for upcoming deadlines and send notifications."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        notification_days = getattr(settings, 'DEADLINE_NOTIFICATION_DAYS', [7, 3, 1])
        assignments: List[Assignment] = db.query(Assignment).all()
        for assignment in assignments:
            if not assignment.due_date:
                continue
            days_left = (assignment.due_date - now).days
            if days_left in notification_days:
                # Get students for the course
                students = db.query(User).filter(User.courses.any(id=assignment.course_id)).all()
                notification_data = {
                    "event_type": "deadline_approaching",
                    "assignment_id": assignment.id,
                    "title": assignment.title,
                    "due_date": assignment.due_date.isoformat(),
                    "course_name": assignment.course.name,
                    "students_list": [
                        {"student_id": s.id, "student_name": s.full_name, "student_email": s.email}
                        for s in students
                    ]
                }
                service = NotificationService()
                await service.send_webhook(notification_data)
    except Exception as e:
        logger.error(f"Error in deadline checker: {e}")
    finally:
        db.close()

async def start_deadline_scheduler():
    """Start periodic deadline checking task."""
    interval = getattr(settings, 'DEADLINE_CHECK_INTERVAL', 3600)
    while True:
        await check_deadlines()
        await asyncio.sleep(interval)

def check_deadlines(notification_service):
    """Check assignments for upcoming deadlines and send notifications."""
    try:
        # Пример: отправка уведомлений по дедлайнам
        for assignment in get_assignments_with_upcoming_deadlines():
            for student in assignment.students:
                sent = notification_service.send_webhook(
                    event_type="deadline_reminder",
                    data={"assignment_id": assignment.id, "due": assignment.due_date},
                    user_id=student.id,
                    channels=["email", "web"]
                )
                logging.info(json.dumps({
                    "event": "deadline_notification",
                    "assignment_id": assignment.id,
                    "user_id": student.id,
                    "status": "sent" if sent else "failed"
                }))
    except Exception as e:
        logging.error(json.dumps({
            "event": "deadline_check_failed",
            "error": str(e)
        }))