"""
Scheduler service for deadline and periodic notification tasks.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.user import User
from app.models.enrollment import Enrollment, EnrollmentRole, EnrollmentStatus
from app.db.session import AsyncSessionLocal
import asyncio
import json

logger = logging.getLogger(__name__)

async def check_deadlines(notification_service, session_factory: callable = None) -> None:
    """Check assignments for upcoming deadlines and send notifications."""
    session_factory = session_factory or AsyncSessionLocal
    async with session_factory() as db:
        try:
            now = datetime.now(timezone.utc)
            
            # Получаем дни для уведомлений из настроек
            notification_days_str = getattr(settings, 'DEADLINE_NOTIFICATION_DAYS', '7,3,1')
            if isinstance(notification_days_str, str):
                notification_days = [int(d.strip()) for d in notification_days_str.split(',')]
            else:
                notification_days = notification_days_str
            
            logger.info(f"Checking deadlines for notification days: {notification_days}")
            
            # Получаем все задания с предстоящими дедлайнами
            for days_ahead in notification_days:
                target_date = now + timedelta(days=days_ahead)
                date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # Ищем задания с дедлайном в этот день
                result = await db.execute(
                    select(Assignment)
                    .options(selectinload(Assignment.course))
                    .where(
                        and_(
                            Assignment.due_date >= date_start,
                            Assignment.due_date <= date_end
                        )
                    )
                )
                assignments = result.scalars().all()
                
                logger.info(f"Found {len(assignments)} assignments due in {days_ahead} days")
                
                for assignment in assignments:
                    await _process_assignment_deadline(db, assignment, notification_service, days_ahead)
                    
        except Exception as e:
            logger.error(f"Error in deadline checker: {e}", exc_info=True)

async def _process_assignment_deadline(db, assignment: Assignment, notification_service, days_ahead: int) -> None:
    """Process a single assignment deadline notification."""
    try:
        # Получаем всех активных студентов курса через enrollments
        students_result = await db.execute(
            select(User)
            .join(Enrollment, User.id == Enrollment.user_id)
            .where(
                and_(
                    Enrollment.course_id == assignment.course_id,
                    Enrollment.role == EnrollmentRole.student,
                    Enrollment.status == EnrollmentStatus.active
                )
            )
        )
        students = students_result.scalars().all()
        
        if not students:
            logger.info(f"No active students found for assignment {assignment.id}")
            return
        
        # Подготавливаем данные для уведомления
        notification_data = {
            "event_type": "deadline_approaching",
            "assignment_id": assignment.id,
            "title": assignment.title,
            "due_date": assignment.due_date.isoformat(),
            "days_until_due": days_ahead,
            "course_id": assignment.course_id,
            "course_name": assignment.course.title if assignment.course else "Unknown Course",
            "students_count": len(students),
            "students_list": [
                {
                    "student_id": student.id,
                    "student_name": student.username,
                    "student_email": getattr(student, 'email', None)
                }
                for student in students
            ]
        }
        
        logger.info(f"Sending deadline notification for assignment '{assignment.title}' to {len(students)} students")
        
        # Отправляем уведомление
        try:
            # Используем правильный метод notification service
            from app.services.notification import NotificationChannel, NotificationPriority
            
            await notification_service.send_notification(
                event_type="deadline_approaching",
                data=notification_data,
                channels=[NotificationChannel.WEBHOOK, NotificationChannel.EMAIL],
                priority=NotificationPriority.HIGH,
                recipients=[
                    {
                        "user_id": student.id,
                        "email": getattr(student, 'email', None),
                        "name": student.username
                    }
                    for student in students
                ]
            )
            
            logger.info(f"Successfully sent deadline notification for assignment {assignment.id}")
            
        except Exception as send_error:
            logger.error(f"Failed to send deadline notification for assignment {assignment.id}: {send_error}")
            
    except Exception as e:
        logger.error(f"Error processing assignment {assignment.id} deadline: {e}", exc_info=True)

def start_deadline_scheduler(notification_service, interval: int = None) -> None:
    """Start periodic deadline checking task within running event loop."""
    interval_seconds = interval or getattr(settings, 'DEADLINE_CHECK_INTERVAL', 3600)
    
    logger.info(f"Starting deadline scheduler with interval: {interval_seconds} seconds")

    async def _deadline_runner():
        """Background task runner for deadline checking."""
        logger.info("Deadline scheduler started")
        
        while True:
            try:
                logger.debug("Running deadline check...")
                await check_deadlines(notification_service)
                logger.debug("Deadline check completed")
                
            except Exception as loop_error:
                error_msg = {
                    "event": "deadline_loop_error", 
                    "error": str(loop_error),
                    "error_type": type(loop_error).__name__
                }
                logger.error(json.dumps(error_msg), exc_info=True)
            
            # Ждем до следующей проверки
            await asyncio.sleep(interval_seconds)

    try:
        # Получаем текущий event loop
        loop = asyncio.get_running_loop()
        
        # Создаем задачу в текущем loop
        task = loop.create_task(_deadline_runner())
        logger.info(f"Deadline scheduler task created: {task}")
        
    except RuntimeError as e:
        # Если нет активного event loop, логируем предупреждение
        logger.warning(f"No running event loop found, scheduler not started: {e}")
        logger.warning("Deadline scheduler should be started within an async context")
        
def stop_deadline_scheduler() -> None:
    """Stop the deadline scheduler (placeholder for future implementation)."""
    # В будущем можно добавить механизм остановки задач
    logger.info("Deadline scheduler stop requested (not implemented yet)")

async def run_deadline_check_once(notification_service) -> bool:
    """Run deadline check once (useful for testing and manual triggers)."""
    try:
        logger.info("Running one-time deadline check")
        await check_deadlines(notification_service)
        logger.info("One-time deadline check completed successfully")
        return True
    except Exception as e:
        logger.error(f"One-time deadline check failed: {e}", exc_info=True)
        return False