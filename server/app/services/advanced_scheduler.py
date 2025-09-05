"""
Advanced scheduler service using APScheduler.

Provides cron-like scheduling, job persistence, and advanced timing for notifications.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.notification import NotificationService
from app.services.quiet_hours import quiet_hours_service
from app.middleware.observability import get_business_metrics

logger = logging.getLogger(__name__)


class AdvancedSchedulerService:
    """Advanced scheduler service with APScheduler backend."""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.notification_service = NotificationService(settings)
        self.business_metrics = get_business_metrics()
        self._setup_scheduler()
    
    def _setup_scheduler(self):
        """Initialize APScheduler with appropriate configuration."""
        try:
            # Configure job stores
            job_stores = {
                'default': MemoryJobStore()
            }
            
            # Use Redis for job persistence if available
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                try:
                    job_stores['redis'] = RedisJobStore(
                        host=settings.REDIS_URL.split('://')[1].split(':')[0],
                        port=int(settings.REDIS_URL.split(':')[-1]),
                        db=2  # Use different DB for scheduler
                    )
                    job_stores['default'] = job_stores['redis']
                    logger.info("Using Redis job store for scheduler persistence")
                except Exception as e:
                    logger.warning(f"Failed to setup Redis job store, using memory: {e}")
            
            # Configure executors
            executors = {
                'default': AsyncIOExecutor()
            }
            
            # Job defaults
            job_defaults = {
                'coalesce': True,  # Combine multiple pending executions
                'max_instances': 3,  # Max concurrent instances of same job
                'misfire_grace_time': 300  # 5 minutes grace for misfired jobs
            }
            
            # Create scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores=job_stores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='UTC'
            )
            
            # Add event listeners
            self.scheduler.add_listener(
                self._job_executed_listener, 
                EVENT_JOB_EXECUTED
            )
            self.scheduler.add_listener(
                self._job_error_listener, 
                EVENT_JOB_ERROR
            )
            
            logger.info("Advanced scheduler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            self.scheduler = None
    
    def _job_executed_listener(self, event):
        """Handle successful job execution."""
        job_id = event.job_id
        logger.debug(f"Job {job_id} executed successfully")
        
        # Track metrics
        if self.business_metrics:
            # Extract job type from job_id if follows naming convention
            job_type = job_id.split('_')[0] if '_' in job_id else 'unknown'
            # You could add custom metrics here
    
    def _job_error_listener(self, event):
        """Handle job execution errors."""
        job_id = event.job_id
        exception = event.exception
        logger.error(f"Job {job_id} failed: {exception}")
        
        # Track error metrics
        if self.business_metrics:
            # Could track job failure metrics here
            pass
    
    async def start(self):
        """Start the scheduler."""
        if self.scheduler and not self.scheduler.running:
            try:
                self.scheduler.start()
                logger.info("Advanced scheduler started")
                
                # Schedule default jobs
                await self._schedule_default_jobs()
                
            except Exception as e:
                logger.error(f"Failed to start scheduler: {e}")
    
    async def stop(self):
        """Stop the scheduler."""
        if self.scheduler and self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=False)
                logger.info("Advanced scheduler stopped")
            except Exception as e:
                logger.error(f"Failed to stop scheduler: {e}")
    
    async def _schedule_default_jobs(self):
        """Schedule default system jobs."""
        try:
            # Deadline checker - every hour
            if getattr(settings, 'DEADLINE_CHECK_ENABLED', False):
                self.scheduler.add_job(
                    func=self._deadline_check_job,
                    trigger=IntervalTrigger(
                        seconds=getattr(settings, 'DEADLINE_CHECK_INTERVAL', 3600)
                    ),
                    id='deadline_checker',
                    name='Deadline Checker',
                    replace_existing=True
                )
                logger.info("Scheduled deadline checker job")
            
            # Weekly digest - every Sunday at 9 AM
            self.scheduler.add_job(
                func=self._weekly_digest_job,
                trigger=CronTrigger(day_of_week='sun', hour=9, minute=0),
                id='weekly_digest',
                name='Weekly Digest Generator',
                replace_existing=True
            )
            logger.info("Scheduled weekly digest job")
            
            # Daily summary - every day at 8 PM
            self.scheduler.add_job(
                func=self._daily_summary_job,
                trigger=CronTrigger(hour=20, minute=0),
                id='daily_summary',
                name='Daily Summary Generator',
                replace_existing=True
            )
            logger.info("Scheduled daily summary job")
            
            # Canvas sync jobs if enabled
            if getattr(settings, 'CANVAS_REST_SYNC_ENABLED', False):
                self.scheduler.add_job(
                    func=self._canvas_sync_job,
                    trigger=IntervalTrigger(
                        seconds=getattr(settings, 'CANVAS_REST_SYNC_INTERVAL', 3600)
                    ),
                    id='canvas_sync',
                    name='Canvas Data Sync',
                    replace_existing=True
                )
                logger.info("Scheduled Canvas sync job")
            
            # System maintenance - daily at 3 AM
            self.scheduler.add_job(
                func=self._system_maintenance_job,
                trigger=CronTrigger(hour=3, minute=0),
                id='system_maintenance',
                name='System Maintenance',
                replace_existing=True
            )
            logger.info("Scheduled system maintenance job")
            
        except Exception as e:
            logger.error(f"Failed to schedule default jobs: {e}")
    
    async def _deadline_check_job(self):
        """Job function for checking upcoming deadlines."""
        try:
            logger.info("Starting deadline check job")
            async with AsyncSessionLocal() as db:
                await self._check_deadlines(db)
            logger.info("Deadline check job completed")
        except Exception as e:
            logger.error(f"Deadline check job failed: {e}")
    
    async def _weekly_digest_job(self):
        """Job function for generating weekly digests."""
        try:
            logger.info("Starting weekly digest job")
            async with AsyncSessionLocal() as db:
                await self._generate_weekly_digests(db)
            logger.info("Weekly digest job completed")
        except Exception as e:
            logger.error(f"Weekly digest job failed: {e}")
    
    async def _daily_summary_job(self):
        """Job function for generating daily summaries."""
        try:
            logger.info("Starting daily summary job")
            async with AsyncSessionLocal() as db:
                await self._generate_daily_summaries(db)
            logger.info("Daily summary job completed")
        except Exception as e:
            logger.error(f"Daily summary job failed: {e}")
    
    async def _canvas_sync_job(self):
        """Job function for Canvas data synchronization."""
        try:
            logger.info("Starting Canvas sync job")
            # Import here to avoid circular imports
            from app.services.canvas_sync import canvas_sync_service
            await canvas_sync_service.sync_all_data()
            logger.info("Canvas sync job completed")
        except Exception as e:
            logger.error(f"Canvas sync job failed: {e}")
    
    async def _system_maintenance_job(self):
        """Job function for system maintenance tasks."""
        try:
            logger.info("Starting system maintenance job")
            async with AsyncSessionLocal() as db:
                await self._perform_maintenance(db)
            logger.info("System maintenance job completed")
        except Exception as e:
            logger.error(f"System maintenance job failed: {e}")
    
    async def _check_deadlines(self, db: AsyncSession):
        """Check for upcoming deadlines and send notifications."""
        try:
            from sqlalchemy import select, and_
            from app.models.assignment import Assignment
            from app.models.user import User
            from app.models.enrollment import Enrollment
            
            # Get deadline notification days from settings
            deadline_days_str = getattr(settings, 'DEADLINE_NOTIFICATION_DAYS', '[7,3,1]')
            deadline_days = json.loads(deadline_days_str)
            
            now = datetime.utcnow()
            
            for days in deadline_days:
                # Calculate deadline range
                start_time = now + timedelta(days=days)
                end_time = start_time + timedelta(hours=1)  # 1-hour window
                
                # Find assignments due in this window
                assignments_result = await db.execute(
                    select(Assignment).where(
                        and_(
                            Assignment.due_date >= start_time,
                            Assignment.due_date <= end_time
                        )
                    )
                )
                assignments = assignments_result.scalars().all()
                
                for assignment in assignments:
                    # Get enrolled students
                    students_result = await db.execute(
                        select(User).join(Enrollment).where(
                            and_(
                                Enrollment.course_id == assignment.course_id,
                                User.role == 'student'
                            )
                        )
                    )
                    students = students_result.scalars().all()
                    
                    # Filter by quiet hours
                    student_ids = [student.id for student in students]
                    filtered_users = await quiet_hours_service.bulk_filter_users_by_quiet_hours(
                        student_ids, db, now
                    )
                    
                    # Send notifications to allowed users
                    for student_id in filtered_users['allowed']:
                        student = next(s for s in students if s.id == student_id)
                        await self._send_deadline_notification(
                            student, assignment, days, db
                        )
                    
                    # Schedule notifications for users in quiet hours
                    for student_id in filtered_users['quiet']:
                        student = next(s for s in students if s.id == student_id)
                        next_allowed = await quiet_hours_service.get_next_allowed_time(
                            student_id, db, now
                        )
                        await self.schedule_delayed_notification(
                            student, assignment, days, next_allowed
                        )
        
        except Exception as e:
            logger.error(f"Error checking deadlines: {e}")
    
    async def _send_deadline_notification(
        self, 
        student: Any, 
        assignment: Any, 
        days_until: int,
        db: AsyncSession
    ):
        """Send deadline notification to a student."""
        try:
            notification_data = {
                'type': 'assignment_due_soon',
                'user_id': student.id,
                'assignment_id': assignment.id,
                'days_until': days_until,
                'assignment_title': assignment.title,
                'due_date': assignment.due_date.isoformat()
            }
            
            # Use notification service to send via configured channels
            success = await self.notification_service.send_notification(
                user_id=student.id,
                notification_type='assignment_due_soon',
                data=notification_data,
                db=db
            )
            
            if success:
                logger.info(f"Deadline notification sent to user {student.id} for assignment {assignment.id}")
            else:
                logger.warning(f"Failed to send deadline notification to user {student.id}")
                
        except Exception as e:
            logger.error(f"Error sending deadline notification: {e}")
    
    async def schedule_delayed_notification(
        self, 
        student: Any, 
        assignment: Any, 
        days_until: int,
        send_at: datetime
    ):
        """Schedule a delayed notification for later delivery."""
        try:
            job_id = f"delayed_notification_{student.id}_{assignment.id}_{days_until}"
            
            self.scheduler.add_job(
                func=self._delayed_notification_job,
                trigger=DateTrigger(run_date=send_at),
                args=[student.id, assignment.id, days_until],
                id=job_id,
                name=f'Delayed notification for user {student.id}',
                replace_existing=True
            )
            
            logger.info(f"Scheduled delayed notification for user {student.id} at {send_at}")
            
        except Exception as e:
            logger.error(f"Error scheduling delayed notification: {e}")
    
    async def _delayed_notification_job(self, student_id: int, assignment_id: int, days_until: int):
        """Job function for delayed notifications."""
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                from app.models.user import User
                from app.models.assignment import Assignment
                
                # Get student and assignment
                student_result = await db.execute(select(User).where(User.id == student_id))
                student = student_result.scalar_one_or_none()
                
                assignment_result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
                assignment = assignment_result.scalar_one_or_none()
                
                if student and assignment:
                    await self._send_deadline_notification(student, assignment, days_until, db)
                
        except Exception as e:
            logger.error(f"Delayed notification job failed: {e}")
    
    async def _generate_weekly_digests(self, db: AsyncSession):
        """Generate and send weekly digests to users."""
        try:
            from sqlalchemy import select
            from app.models.user import User
            
            # Get all active users
            users_result = await db.execute(
                select(User).where(User.role.in_(['student', 'teacher']))
            )
            users = users_result.scalars().all()
            
            for user in users:
                # Check quiet hours
                if await quiet_hours_service.is_quiet_time(user.id, db):
                    # Schedule for later
                    next_allowed = await quiet_hours_service.get_next_allowed_time(user.id, db)
                    self.scheduler.add_job(
                        func=self._delayed_digest_job,
                        trigger=DateTrigger(run_date=next_allowed),
                        args=[user.id],
                        id=f"delayed_digest_{user.id}",
                        replace_existing=True
                    )
                else:
                    # Send immediately
                    await self._send_weekly_digest(user, db)
                    
        except Exception as e:
            logger.error(f"Error generating weekly digests: {e}")
    
    async def _send_weekly_digest(self, user: Any, db: AsyncSession):
        """Send weekly digest to a user."""
        try:
            # Generate digest data (placeholder implementation)
            digest_data = {
                'user_id': user.id,
                'week_start': datetime.utcnow() - timedelta(days=7),
                'week_end': datetime.utcnow(),
                'assignments_completed': 5,  # Would query actual data
                'assignments_pending': 2,
                'average_grade': 85.5,
                'courses_active': 3
            }
            
            success = await self.notification_service.send_notification(
                user_id=user.id,
                notification_type='weekly_digest',
                data=digest_data,
                db=db
            )
            
            if success:
                logger.info(f"Weekly digest sent to user {user.id}")
            else:
                logger.warning(f"Failed to send weekly digest to user {user.id}")
                
        except Exception as e:
            logger.error(f"Error sending weekly digest: {e}")
    
    async def _delayed_digest_job(self, user_id: int):
        """Job function for delayed digest delivery."""
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                from app.models.user import User
                
                user_result = await db.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()
                
                if user:
                    await self._send_weekly_digest(user, db)
                    
        except Exception as e:
            logger.error(f"Delayed digest job failed: {e}")
    
    async def _generate_daily_summaries(self, db: AsyncSession):
        """Generate daily summaries for users."""
        # Placeholder for daily summary logic
        logger.info("Daily summary generation completed (placeholder)")
    
    async def _perform_maintenance(self, db: AsyncSession):
        """Perform system maintenance tasks."""
        try:
            # Clean up old notification logs
            from sqlalchemy import delete
            from app.models.notification_log import NotificationLog
            
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            delete_stmt = delete(NotificationLog).where(
                NotificationLog.created_at < cutoff_date
            )
            result = await db.execute(delete_stmt)
            await db.commit()
            
            logger.info(f"Cleaned up {result.rowcount} old notification logs")
            
            # Add other maintenance tasks here
            # - Clean up temporary files
            # - Vacuum database
            # - Update statistics
            
        except Exception as e:
            logger.error(f"System maintenance failed: {e}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs."""
        if not self.scheduler:
            return {"status": "disabled", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "max_instances": job.max_instances,
                "coalesce": job.coalesce
            })
        
        return {
            "status": "running" if self.scheduler.running else "stopped",
            "jobs": jobs,
            "job_count": len(jobs)
        }


# Global scheduler service instance
advanced_scheduler = AdvancedSchedulerService()
