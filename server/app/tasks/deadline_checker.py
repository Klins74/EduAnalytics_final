import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_db
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.user import User
from app.models.student import Student
from app.services.notification import NotificationService
from app.core.config import settings

logger = logging.getLogger(__name__)


class DeadlineChecker:
    """Сервис для проверки приближающихся дедлайнов и отправки уведомлений."""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.check_intervals = [24, 48, 72]  # Часы до дедлайна для уведомлений
        self.tolerance_minutes = 30  # Допустимое отклонение в минутах
    
    async def check_deadlines(self, db: AsyncSession) -> None:
        """Проверить все приближающиеся дедлайны и отправить уведомления."""
        try:
            logger.info("Начинаем проверку дедлайнов")
            
            for hours in self.check_intervals:
                await self._check_deadlines_for_interval(db, hours)
            
            logger.info("Проверка дедлайнов завершена")
            
        except Exception as e:
            logger.error(f"Ошибка при проверке дедлайнов: {str(e)}")
    
    async def _check_deadlines_for_interval(self, db: AsyncSession, hours: int) -> None:
        """Проверить дедлайны для конкретного интервала времени."""
        try:
            # Вычисляем временной диапазон
            now = datetime.utcnow()
            target_time = now + timedelta(hours=hours)
            tolerance = timedelta(minutes=self.tolerance_minutes)
            
            start_time = target_time - tolerance
            end_time = target_time + tolerance
            
            # Ищем задания с дедлайнами в этом диапазоне
            stmt = (
                select(Assignment)
                .join(Course)
                .where(
                    Assignment.due_date >= start_time,
                    Assignment.due_date <= end_time
                )
            )
            
            result = await db.execute(stmt)
            assignments = result.scalars().all()
            
            logger.info(f"Найдено {len(assignments)} заданий с дедлайном через {hours} часов")
            
            for assignment in assignments:
                await self._send_deadline_notification(db, assignment, hours)
                
        except Exception as e:
            logger.error(f"Ошибка при проверке дедлайнов для интервала {hours} часов: {str(e)}")
    
    async def _send_deadline_notification(self, db: AsyncSession, assignment: Assignment, hours: int) -> None:
        """Отправить уведомление о дедлайне для конкретного задания."""
        try:
            # Получаем информацию о курсе
            course_stmt = select(Course).where(Course.id == assignment.course_id)
            course_result = await db.execute(course_stmt)
            course = course_result.scalar_one_or_none()
            
            if not course:
                logger.warning(f"Курс не найден для задания {assignment.id}")
                return
            
            # Получаем список студентов курса
            students = await self._get_course_students(db, course.id)
            
            if not students:
                logger.info(f"Нет студентов для уведомления о задании {assignment.id}")
                return
            
            # Отправляем уведомление
            success = await self.notification_service.send_deadline_notification(
                assignment_id=assignment.id,
                assignment_title=assignment.title,
                due_date=assignment.due_date.isoformat(),
                course_name=course.name,
                course_id=course.id,
                hours_remaining=hours,
                students=students
            )
            
            if success:
                logger.info(
                    f"Уведомление о дедлайне отправлено для задания '{assignment.title}' "
                    f"(через {hours} часов, {len(students)} студентов)"
                )
            else:
                logger.error(
                    f"Не удалось отправить уведомление о дедлайне для задания '{assignment.title}'"
                )
                
        except Exception as e:
            logger.error(
                f"Ошибка при отправке уведомления о дедлайне для задания {assignment.id}: {str(e)}"
            )
    
    async def _get_course_students(self, db: AsyncSession, course_id: int) -> List[dict]:
        """Получить список студентов курса для уведомлений."""
        try:
            # Получаем студентов через связь с группами
            stmt = (
                select(User, Student)
                .join(Student, User.id == Student.user_id)
                .join(Course.groups)
                .join(Student.group)
                .where(Course.id == course_id)
                .distinct()
            )
            
            result = await db.execute(stmt)
            user_student_pairs = result.all()
            
            students = []
            for user, student in user_student_pairs:
                students.append({
                    "user_id": user.id,
                    "student_id": student.id,
                    "name": f"{student.first_name} {student.last_name}",
                    "email": user.username,  # Предполагаем, что username это email
                    "group_id": student.group_id
                })
            
            return students
            
        except Exception as e:
            logger.error(f"Ошибка при получении студентов курса {course_id}: {str(e)}")
            return []
    
    async def check_single_assignment(self, db: AsyncSession, assignment_id: int) -> bool:
        """Проверить дедлайн для конкретного задания (для тестирования)."""
        try:
            stmt = select(Assignment).where(Assignment.id == assignment_id)
            result = await db.execute(stmt)
            assignment = result.scalar_one_or_none()
            
            if not assignment:
                logger.warning(f"Задание {assignment_id} не найдено")
                return False
            
            # Вычисляем часы до дедлайна
            now = datetime.utcnow()
            time_diff = assignment.due_date - now
            hours_remaining = int(time_diff.total_seconds() / 3600)
            
            if hours_remaining > 0 and hours_remaining <= 72:
                await self._send_deadline_notification(db, assignment, hours_remaining)
                return True
            else:
                logger.info(
                    f"Задание {assignment_id} не требует уведомления "
                    f"(часов до дедлайна: {hours_remaining})"
                )
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при проверке задания {assignment_id}: {str(e)}")
            return False

    def _check_deadlines_for_interval_sync(self, hours: int) -> None:
        """Синхронная обёртка для тестов: проверка дедлайнов для интервала."""
        from app.core.database import get_db
        for db in get_db():
            asyncio.run(self._check_deadlines_for_interval(db, hours))

    def _send_deadline_notification_sync(self, assignment, hours: int) -> None:
        """Синхронная обёртка для тестов: отправка уведомления о дедлайне."""
        from app.core.database import get_db
        for db in get_db():
            asyncio.run(self._send_deadline_notification(db, assignment, hours))

    def _get_course_students_sync(self, course_id: int) -> list:
        """Синхронная обёртка для тестов: получить студентов курса."""
        from app.core.database import get_db
        for db in get_db():
            return asyncio.run(self._get_course_students(db, course_id))
        return []


# Глобальный экземпляр для использования в фоновых задачах
deadline_checker = DeadlineChecker()


async def run_deadline_check():
    """Запустить проверку дедлайнов (для использования в планировщике)."""
    async for db in get_async_db():
        try:
            await deadline_checker.check_deadlines(db)
        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче проверки дедлайнов: {str(e)}")
        finally:
            await db.close()


async def start_deadline_scheduler():
    """Запустить планировщик проверки дедлайнов."""
    logger.info("Запуск планировщика проверки дедлайнов")
    
    while True:
        try:
            await run_deadline_check()
            # Проверяем каждые 30 минут
            await asyncio.sleep(30 * 60)
        except Exception as e:
            logger.error(f"Ошибка в планировщике дедлайнов: {str(e)}")
            # При ошибке ждем 5 минут перед повторной попыткой
            await asyncio.sleep(5 * 60)