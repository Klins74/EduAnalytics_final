from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import func, desc, and_, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback
from app.models.user import User
from app.models.submission import Submission
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.student import Student
from app.schemas.feedback import FeedbackCreate, FeedbackUpdate
from app.services.notification import NotificationService


class CRUDFeedback:
    """CRUD операции для комментариев."""

    async def get(self, db: AsyncSession, feedback_id: int) -> Optional[Feedback]:
        """Получить комментарий по ID."""
        result = await db.execute(select(Feedback).filter(Feedback.id == feedback_id))
        return result.scalar_one_or_none()

    async def get_with_author(self, db: AsyncSession, feedback_id: int) -> Optional[Feedback]:
        """Получить комментарий с информацией об авторе."""
        result = await db.execute(
            select(Feedback)
            .options(joinedload(Feedback.author))
            .filter(Feedback.id == feedback_id)
        )
        return result.scalar_one_or_none()

    async def get_feedbacks_by_submission(
        self, 
        db: AsyncSession, 
        submission_id: int, 
        skip: int = 0, 
        limit: int = 100,
        include_author: bool = True
    ) -> List[Feedback]:
        """Получить комментарии для конкретного задания."""
        query = select(Feedback).filter(Feedback.submission_id == submission_id)
        
        if include_author:
            query = query.options(joinedload(Feedback.author))
        
        query = (
            query
            .order_by(desc(Feedback.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_feedback_by_id(self, db: AsyncSession, feedback_id: int) -> Optional[Feedback]:
        """Получить комментарий по ID с загрузкой автора."""
        from sqlalchemy.orm import selectinload
        query = (
            select(Feedback)
            .options(selectinload(Feedback.author))
            .filter(Feedback.id == feedback_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_feedbacks_by_user(
        self, 
        db: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Feedback]:
        """Получить комментарии конкретного пользователя."""
        query = (
            select(Feedback)
            .options(joinedload(Feedback.submission))
            .filter(Feedback.user_id == user_id)
            .order_by(desc(Feedback.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        return result.scalars().all()

    async def count_by_submission(self, db: AsyncSession, submission_id: int) -> int:
        """Подсчитать количество комментариев для задания."""
        result = await db.execute(
            select(func.count(Feedback.id)).filter(Feedback.submission_id == submission_id)
        )
        return result.scalar()

    async def create_feedback(
        self, 
        db: AsyncSession, 
        submission_id: int, 
        user_id: int, 
        feedback_data: FeedbackCreate,
        send_notification: bool = True
    ) -> Feedback:
        """Создать новый комментарий."""
        # Проверяем существование задания
        submission_result = await db.execute(
            select(Submission)
            .options(joinedload(Submission.assignment).joinedload(Assignment.course))
            .filter(Submission.id == submission_id)
        )
        submission = submission_result.scalar_one_or_none()
        if not submission:
            raise ValueError(f"Submission with id {submission_id} not found")
        
        # Проверяем существование пользователя
        user_result = await db.execute(select(User).filter(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Получаем информацию о студенте, если submission принадлежит студенту
        student_info = None
        if submission.student_id:
            student_result = await db.execute(
                select(Student, User)
                .join(User, Student.id == User.id)
                .filter(Student.id == submission.student_id)
            )
            student_data = student_result.first()
            if student_data:
                student, student_user = student_data
                student_info = {
                    "name": f"{student.first_name} {student.last_name}",
                    "email": getattr(student_user, "email", student_user.username),
                    "id": student.id
                }
        
        db_feedback = Feedback(
            submission_id=submission_id,
            user_id=user_id,
            text=feedback_data.text
        )
        
        db.add(db_feedback)
        await db.flush()
        await db.refresh(db_feedback)
        
        # Отправляем уведомление
        if send_notification:
            try:
                notification_service = NotificationService()
                
                # Формируем данные для webhook
                webhook_data = {
                    "event_type": "feedback_created",
                    "feedback_id": db_feedback.id,
                    "submission_id": submission_id,
                    "author_name": user.username,
                    "author_id": user.id,
                    "feedback_text": feedback_data.text[:500],  # Ограничиваем длину
                    "submission_title": getattr(submission.assignment, 'title', None),
                    "student_name": student_info["name"] if student_info else None,
                    "student_id": student_info["id"] if student_info else None,
                    "student_email": student_info["email"] if student_info else None,
                    "course_name": getattr(submission.assignment.course, 'name', None) if submission.assignment else None,
                    "channels": ["email"]
                }
                
                await notification_service.send_webhook(webhook_data)
                
            except Exception as e:
                # Логируем ошибку, но не прерываем создание комментария
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка отправки уведомления о комментарии {db_feedback.id}: {str(e)}")
        
        return db_feedback

    async def update_feedback(
        self, 
        db: AsyncSession, 
        feedback_id: int, 
        feedback_data: FeedbackUpdate,
        current_user_id: int
    ) -> Optional[Feedback]:
        """Обновить комментарий."""
        db_feedback = await self.get_feedback_by_id(db, feedback_id=feedback_id)
        
        if not db_feedback or db_feedback.user_id != current_user_id:
            return None
        
        update_data = feedback_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_feedback, field, value)
        
        await db.flush()
        await db.refresh(db_feedback)
        # Отправляем уведомление об обновлении комментария
        try:
            notification_service = NotificationService()
            # Получаем информацию о пользователе и submission
            user_result = await db.execute(select(User).filter(User.id == current_user_id))
            user = user_result.scalar_one_or_none()
            submission_result = await db.execute(
                select(Submission)
                .options(joinedload(Submission.assignment).joinedload(Assignment.course))
                .filter(Submission.id == db_feedback.submission_id)
            )
            submission = submission_result.scalar_one_or_none()
            student_info = None
            if submission and submission.student_id:
                student_result = await db.execute(
                    select(Student, User)
                    .join(User, Student.id == User.id)
                    .filter(Student.id == submission.student_id)
                )
                student_data = student_result.first()
                if student_data:
                    student, student_user = student_data
                    student_info = {
                        "name": f"{student.first_name} {student.last_name}",
                        "email": student_user.username,
                        "id": student.id
                    }
            webhook_data = {
                "event_type": "feedback_updated",
                "feedback_id": db_feedback.id,
                "submission_id": db_feedback.submission_id,
                "author_name": user.username if user else None,
                "author_id": user.id if user else None,
                "feedback_text": db_feedback.text[:500],
                "submission_title": getattr(submission.assignment, 'title', None) if submission and submission.assignment else None,
                "student_name": student_info["name"] if student_info else None,
                "student_id": student_info["id"] if student_info else None,
                "student_email": student_info["email"] if student_info else None,
                "course_name": getattr(submission.assignment.course, 'name', None) if submission and submission.assignment else None,
                "channels": ["email"]
            }
            await notification_service.send_webhook(webhook_data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка отправки уведомления об обновлении комментария {feedback_id}: {str(e)}")
        return db_feedback

    async def delete_feedback(
        self, 
        db: AsyncSession, 
        feedback_id: int,
        current_user_id: int,
        is_admin: bool
    ) -> bool:
        """Удалить комментарий."""
        db_feedback = await self.get_feedback_by_id(db, feedback_id=feedback_id)
        
        if not db_feedback:
            return False

        if not is_admin and db_feedback.user_id != current_user_id:
            return False
        
        await db.delete(db_feedback)
        await db.flush()
        return True

    async def get_recent_feedbacks(
        self, 
        db: AsyncSession, 
        days: int = 7, 
        limit: int = 50
    ) -> List[Feedback]:
        """Получить недавние комментарии."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        result = await db.execute(
            select(Feedback)
            .options(joinedload(Feedback.author), joinedload(Feedback.submission))
            .filter(Feedback.created_at >= since_date)
            .order_by(desc(Feedback.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_feedback_stats(self, db: AsyncSession, course_id: Optional[int] = None) -> dict:
        """Получить статистику комментариев."""
        base_query = select(Feedback)
        
        if course_id:
            from app.models.assignment import Assignment
            base_query = (
                base_query
                .join(Submission)
                .join(Assignment)
                .filter(Assignment.course_id == course_id)
            )
        
        # Total feedbacks count
        total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
        total_feedbacks = total_result.scalar()
        
        # Статистика по заданиям
        submission_stats_query = (
            base_query
            .join(Submission)
            .with_entities(
                Submission.id.label('submission_id'),
                func.count(Feedback.id).label('feedback_count')
            )
            .group_by(Submission.id)
        )
        submission_result = await db.execute(submission_stats_query)
        feedbacks_by_submission = submission_result.all()
        
        # Недавние комментарии (за последние 7 дней)
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_query = base_query.filter(Feedback.created_at >= recent_date)
        recent_result = await db.execute(select(func.count()).select_from(recent_query.subquery()))
        recent_feedbacks_count = recent_result.scalar()
        
        # Средняя длина комментария
        avg_query = base_query.with_entities(func.avg(func.length(Feedback.text)))
        avg_result = await db.execute(avg_query)
        avg_length_result = avg_result.scalar()
        
        return {
            "total_feedbacks": total_feedbacks,
            "feedbacks_by_submission": {
                str(item.submission_id): item.feedback_count 
                for item in feedbacks_by_submission
            },
            "recent_feedbacks_count": recent_feedbacks_count,
            "average_feedback_length": float(avg_length_result or 0)
        }


# Создаем экземпляр для использования
feedback = CRUDFeedback()