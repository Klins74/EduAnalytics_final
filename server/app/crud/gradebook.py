from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status
import logging

from app.models.gradebook import GradebookEntry, GradebookHistory, OperationType
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.student import Student
from app.schemas.gradebook import (
    GradebookEntryCreate,
    GradebookEntryUpdate,
    GradebookStats
)
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


class CRUDGradebook:
    """CRUD операции для электронного журнала."""

    def get_entries(
        self,
        db: Session,
        *,
        course_id: Optional[int] = None,
        student_id: Optional[int] = None,
        assignment_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[GradebookEntry]:
        """Получить список записей журнала с фильтрацией.
        
        Args:
            db: Сессия базы данных
            course_id: ID курса для фильтрации
            student_id: ID студента для фильтрации
            assignment_id: ID задания для фильтрации
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список записей журнала
        """
        query = db.query(GradebookEntry)
        
        # Применяем фильтры
        if course_id is not None:
            query = query.filter(GradebookEntry.course_id == course_id)
        if student_id is not None:
            query = query.filter(GradebookEntry.student_id == student_id)
        if assignment_id is not None:
            query = query.filter(GradebookEntry.assignment_id == assignment_id)
            
        return query.order_by(desc(GradebookEntry.created_at)).offset(skip).limit(limit).all()

    def get_entry(self, db: Session, *, entry_id: int) -> Optional[GradebookEntry]:
        """Получить запись журнала по ID.
        
        Args:
            db: Сессия базы данных
            entry_id: ID записи
            
        Returns:
            Запись журнала или None
        """
        return db.query(GradebookEntry).filter(GradebookEntry.id == entry_id).first()

    def get_entry_by_unique_key(
        self,
        db: Session,
        *,
        course_id: int,
        student_id: int,
        assignment_id: Optional[int] = None
    ) -> Optional[GradebookEntry]:
        """Получить запись по уникальному ключу (курс + студент + задание).
        
        Args:
            db: Сессия базы данных
            course_id: ID курса
            student_id: ID студента
            assignment_id: ID задания (может быть None для общих оценок)
            
        Returns:
            Запись журнала или None
        """
        query = db.query(GradebookEntry).filter(
            and_(
                GradebookEntry.course_id == course_id,
                GradebookEntry.student_id == student_id,
                GradebookEntry.assignment_id == assignment_id
            )
        )
        return query.first()

    def create_entry(
        self,
        db: Session,
        *,
        entry_in: GradebookEntryCreate,
        current_user: User
    ) -> GradebookEntry:
        """Создать новую запись в журнале.
        
        Args:
            db: Сессия базы данных
            entry_in: Данные для создания записи
            current_user: Текущий пользователь
            
        Returns:
            Созданная запись
            
        Raises:
            HTTPException: При конфликте или ошибке валидации
        """
        # Проверяем права доступа
        if current_user.role not in ["teacher", "admin"]:
            logger.warning(f"User {current_user.id} attempted to create gradebook entry without permission")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для создания записи в журнале"
            )

        # Проверяем существование связанных объектов
        self._validate_related_objects(db, entry_in)

        # Проверяем на дублирование
        existing_entry = self.get_entry_by_unique_key(
            db,
            course_id=entry_in.course_id,
            student_id=entry_in.student_id,
            assignment_id=entry_in.assignment_id
        )
        
        if existing_entry:
            logger.warning(f"Duplicate gradebook entry attempted: course={entry_in.course_id}, student={entry_in.student_id}, assignment={entry_in.assignment_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Запись для данного студента и задания уже существует"
            )

        # Создаем запись
        db_entry = GradebookEntry(
            **entry_in.model_dump(),
            created_by=current_user.id
        )
        
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        
        # Создаем запись в истории
        self._create_history_entry(
            db,
            entry=db_entry,
            operation=OperationType.create,
            changed_by=current_user.id
        )
        
        # Отправляем уведомление о новой оценке
        try:
            self._send_grade_notification(db, db_entry, current_user, is_new=True)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о новой оценке {db_entry.id}: {str(e)}")
        
        logger.info(f"Created gradebook entry {db_entry.id} by user {current_user.id}")
        return db_entry

    def update_entry(
        self,
        db: Session,
        *,
        entry_id: int,
        entry_in: GradebookEntryUpdate,
        current_user: User
    ) -> GradebookEntry:
        """Обновить запись в журнале.
        
        Args:
            db: Сессия базы данных
            entry_id: ID записи для обновления
            entry_in: Новые данные
            current_user: Текущий пользователь
            
        Returns:
            Обновленная запись
            
        Raises:
            HTTPException: При отсутствии записи или недостатке прав
        """
        # Проверяем права доступа
        if current_user.role not in ["teacher", "admin"]:
            logger.warning(f"User {current_user.id} attempted to update gradebook entry without permission")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для обновления записи в журнале"
            )

        # Получаем существующую запись
        db_entry = self.get_entry(db, entry_id=entry_id)
        if not db_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись в журнале не найдена"
            )

        # Обновляем только переданные поля
        update_data = entry_in.dict(exclude_unset=True)
        if not update_data:
            return db_entry

        for field, value in update_data.items():
            setattr(db_entry, field, value)
        
        db.commit()
        db.refresh(db_entry)
        
        # Создаем запись в истории
        self._create_history_entry(
            db,
            entry=db_entry,
            operation=OperationType.update,
            changed_by=current_user.id
        )
        
        # Отправляем уведомление об обновлении оценки
        try:
            self._send_grade_notification(db, db_entry, current_user, is_new=False)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об обновлении оценки {db_entry.id}: {str(e)}")
        
        logger.info(f"Updated gradebook entry {entry_id} by user {current_user.id}")
        return db_entry

    def delete_entry(
        self,
        db: Session,
        *,
        entry_id: int,
        current_user: User
    ) -> None:
        """Удалить запись из журнала.
        
        Args:
            db: Сессия базы данных
            entry_id: ID записи для удаления
            current_user: Текущий пользователь
            
        Raises:
            HTTPException: При отсутствии записи или недостатке прав
        """
        # Проверяем права доступа
        if current_user.role not in ["teacher", "admin"]:
            logger.warning(f"User {current_user.id} attempted to delete gradebook entry without permission")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для удаления записи из журнала"
            )

        # Получаем существующую запись
        db_entry = self.get_entry(db, entry_id=entry_id)
        if not db_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись в журнале не найдена"
            )

        # Создаем запись в истории перед удалением
        self._create_history_entry(
            db,
            entry=db_entry,
            operation=OperationType.delete,
            changed_by=current_user.id
        )
        
        db.delete(db_entry)
        db.commit()
        
        logger.info(f"Deleted gradebook entry {entry_id} by user {current_user.id}")

    def get_entry_history(
        self,
        db: Session,
        *,
        entry_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[GradebookHistory]:
        """Получить историю изменений записи.
        
        Args:
            db: Сессия базы данных
            entry_id: ID записи
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список записей истории
        """
        return (
            db.query(GradebookHistory)
            .filter(GradebookHistory.entry_id == entry_id)
            .order_by(desc(GradebookHistory.changed_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_stats(
        self,
        db: Session,
        *,
        course_id: Optional[int] = None,
        student_id: Optional[int] = None
    ) -> GradebookStats:
        """Получить статистику по оценкам.
        
        Args:
            db: Сессия базы данных
            course_id: ID курса для фильтрации
            student_id: ID студента для фильтрации
            
        Returns:
            Статистика по оценкам
        """
        query = db.query(GradebookEntry)
        
        if course_id is not None:
            query = query.filter(GradebookEntry.course_id == course_id)
        if student_id is not None:
            query = query.filter(GradebookEntry.student_id == student_id)
        
        # Получаем агрегированные данные
        stats_query = query.with_entities(
            func.avg(GradebookEntry.grade_value).label('avg_grade'),
            func.min(GradebookEntry.grade_value).label('min_grade'),
            func.max(GradebookEntry.grade_value).label('max_grade'),
            func.count(GradebookEntry.id).label('total_entries'),
            func.count(GradebookEntry.assignment_id).label('graded_assignments')
        ).first()
        
        return GradebookStats(
            average_grade=round(stats_query.avg_grade or 0, 2),
            min_grade=stats_query.min_grade or 0,
            max_grade=stats_query.max_grade or 0,
            total_entries=stats_query.total_entries or 0,
            graded_assignments=stats_query.graded_assignments or 0
        )

    def _validate_related_objects(self, db: Session, entry_in: GradebookEntryCreate) -> None:
        """Валидация связанных объектов.
        
        Args:
            db: Сессия базы данных
            entry_in: Данные записи для валидации
            
        Raises:
            HTTPException: При отсутствии связанных объектов
        """
        # Проверяем курс
        course = db.query(Course).filter(Course.id == entry_in.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Курс не найден"
            )
        
        # Проверяем студента
        student = db.query(User).filter(
            and_(User.id == entry_in.student_id, User.role == "student")
        ).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Студент не найден"
            )
        
        # Проверяем задание (если указано)
        if entry_in.assignment_id is not None:
            assignment = db.query(Assignment).filter(
                and_(
                    Assignment.id == entry_in.assignment_id,
                    Assignment.course_id == entry_in.course_id
                )
            ).first()
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Задание не найдено или не принадлежит указанному курсу"
                )

    def _create_history_entry(
        self,
        db: Session,
        *,
        entry: GradebookEntry,
        operation: OperationType,
        changed_by: int
    ) -> None:
        """Создать запись в истории изменений.
        
        Args:
            db: Сессия базы данных
            entry: Запись журнала
            operation: Тип операции
            changed_by: ID пользователя, внесшего изменение
        """
        history_entry = GradebookHistory(
            entry_id=entry.id,
            course_id=entry.course_id,
            student_id=entry.student_id,
            assignment_id=entry.assignment_id,
            grade_value=entry.grade_value,
            comment=entry.comment,
            operation=operation,
            changed_by=changed_by
        )
        
        db.add(history_entry)
        db.commit()

    def _send_grade_notification(
        self,
        db: Session,
        entry: GradebookEntry,
        current_user: User,
        is_new: bool = True
    ) -> None:
        """Отправить уведомление о новой или обновленной оценке.
        
        Args:
            db: Сессия базы данных
            entry: Запись оценки
            current_user: Пользователь, создавший/обновивший оценку
            is_new: True для новой оценки, False для обновления
        """
        try:
            # Получаем информацию о студенте
            student = db.query(Student).filter(Student.id == entry.student_id).first()
            if not student:
                logger.warning(f"Student {entry.student_id} not found for grade notification")
                return
            
            student_user = db.query(User).filter(User.id == student.user_id).first()
            if not student_user:
                logger.warning(f"User for student {entry.student_id} not found for grade notification")
                return
            
            # Получаем информацию о курсе и задании
            course = db.query(Course).filter(Course.id == entry.course_id).first()
            assignment = db.query(Assignment).filter(Assignment.id == entry.assignment_id).first()
            
            # Формируем данные для webhook
            notification_service = NotificationService()
            
            webhook_data = {
                "event_type": "grade_created" if is_new else "grade_updated",
                "grade_id": entry.id,
                "student_name": f"{student.first_name} {student.last_name}",
                "student_id": student.id,
                "student_email": student_user.username,
                "course_name": course.name if course else None,
                "course_id": entry.course_id,
                "assignment_title": assignment.title if assignment else None,
                "assignment_id": entry.assignment_id,
                "grade_value": entry.grade_value,
                "comment": entry.comment,
                "teacher_name": current_user.username,
                "teacher_id": current_user.id,
                "channels": ["email"]
            }
            
            notification_service.send_webhook(webhook_data)
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о оценке: {str(e)}")


# Создаем экземпляр для использования в роутерах
gradebook = CRUDGradebook()