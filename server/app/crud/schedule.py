from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, func
from fastapi import HTTPException, status
import logging

from app.models.schedule import Schedule
from app.models.course import Course
from app.models.user import User, UserRole
from app.models.student import Student
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.notification import NotificationService

# Настройка логирования
logger = logging.getLogger(__name__)


class CRUDSchedule:
    """CRUD операции для расписания занятий."""

    async def get(self, db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
        """Получить расписание по ID."""
        result = await db.execute(select(Schedule).filter(Schedule.id == schedule_id))
        return result.scalar_one_or_none()

    async def get_with_relations(self, db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
        """Получить расписание по ID с загрузкой связанных данных."""
        result = await db.execute(
            select(Schedule)
            .options(
                selectinload(Schedule.course),
                selectinload(Schedule.instructor)
            )
            .filter(Schedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def get_schedules(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        course_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        instructor_id: Optional[int] = None
    ) -> tuple[List[Schedule], int]:
        """Получить список расписаний с фильтрацией и пагинацией."""
        query = select(Schedule).options(
            selectinload(Schedule.course),
            selectinload(Schedule.instructor)
        )
        
        # Применяем фильтры
        conditions = []
        if course_id:
            conditions.append(Schedule.course_id == course_id)
        if date_from:
            conditions.append(Schedule.schedule_date >= date_from)
        if date_to:
            conditions.append(Schedule.schedule_date <= date_to)
        if instructor_id:
            conditions.append(Schedule.instructor_id == instructor_id)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Подсчет общего количества
        count_query = select(func.count(Schedule.id))
        if conditions:
            count_query = count_query.filter(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Получение данных с пагинацией
        query = query.order_by(Schedule.schedule_date, Schedule.start_time).offset(skip).limit(limit)
        result = await db.execute(query)
        schedules = result.scalars().all()
        
        return schedules, total

    async def create_schedule(
        self,
        db: AsyncSession,
        schedule_data: ScheduleCreate,
        current_user: User
    ) -> Schedule:
        """Создать новое расписание с проверками прав и валидацией."""
        # Проверка прав пользователя
        if current_user.role not in [UserRole.teacher, UserRole.admin]:
            logger.warning(f"Пользователь {current_user.id} пытался создать расписание без прав")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только преподаватели и администраторы могут создавать расписание"
            )
        
        # Проверка существования курса
        course_result = await db.execute(select(Course).filter(Course.id == schedule_data.course_id))
        course = course_result.scalar_one_or_none()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Курс с ID {schedule_data.course_id} не найден"
            )
        
        # Проверка прав на курс (только владелец курса или админ)
        if current_user.role != UserRole.admin and course.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы можете создавать расписание только для своих курсов"
            )
        
        # Проверка существования преподавателя
        instructor_result = await db.execute(select(User).filter(User.id == schedule_data.instructor_id))
        instructor = instructor_result.scalar_one_or_none()
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Преподаватель с ID {schedule_data.instructor_id} не найден"
            )
        
        if instructor.role not in [UserRole.teacher, UserRole.admin]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный пользователь не является преподавателем"
            )
        
        # Проверка на конфликт времени для преподавателя
        conflict_result = await db.execute(
            select(Schedule).filter(
                and_(
                    Schedule.instructor_id == schedule_data.instructor_id,
                    Schedule.schedule_date == schedule_data.schedule_date,
                    Schedule.start_time < schedule_data.end_time,
                    Schedule.end_time > schedule_data.start_time
                )
            )
        )
        if conflict_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="У преподавателя уже есть занятие в это время"
            )
        
        # Создание расписания
        db_schedule = Schedule(**schedule_data.model_dump())
        db.add(db_schedule)
        await db.flush()
        await db.refresh(db_schedule)
        
        # Отправляем уведомление о новом расписании
        try:
            await self._send_schedule_notification(db, db_schedule, current_user, is_new=True)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о новом расписании {db_schedule.id}: {str(e)}")
        
        return db_schedule

    async def update_schedule(
        self,
        db: AsyncSession,
        schedule_id: int,
        schedule_update: ScheduleUpdate,
        current_user: User
    ) -> Optional[Schedule]:
        """Обновить расписание с проверками прав."""
        # Получение существующего расписания
        schedule = await self.get_with_relations(db, schedule_id)
        if not schedule:
            return None
        
        # Проверка прав
        if current_user.role not in [UserRole.teacher, UserRole.admin]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только преподаватели и администраторы могут изменять расписание"
            )
        
        # Проверка прав на курс (только владелец курса или админ)
        if current_user.role != UserRole.admin and schedule.course.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы можете изменять расписание только для своих курсов"
            )
        
        # Обновление полей
        update_data = schedule_update.model_dump(exclude_unset=True)
        
        # Дополнительные проверки при изменении преподавателя
        if 'instructor_id' in update_data:
            instructor_result = await db.execute(select(User).filter(User.id == update_data['instructor_id']))
            instructor = instructor_result.scalar_one_or_none()
            if not instructor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Преподаватель с ID {update_data['instructor_id']} не найден"
                )
            if instructor.role not in [UserRole.teacher, UserRole.admin]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Указанный пользователь не является преподавателем"
                )
        
        # Проверка конфликта времени при изменении времени или даты
        if any(field in update_data for field in ['schedule_date', 'start_time', 'end_time', 'instructor_id']):
            check_date = update_data.get('schedule_date', schedule.schedule_date)
            check_start = update_data.get('start_time', schedule.start_time)
            check_end = update_data.get('end_time', schedule.end_time)
            check_instructor = update_data.get('instructor_id', schedule.instructor_id)
            
            conflict_result = await db.execute(
                select(Schedule).filter(
                    and_(
                        Schedule.id != schedule_id,
                        Schedule.instructor_id == check_instructor,
                        Schedule.schedule_date == check_date,
                        Schedule.start_time < check_end,
                        Schedule.end_time > check_start
                    )
                )
            )
            if conflict_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="У преподавателя уже есть занятие в это время"
                )
        
        # Сохраняем старые значения для сравнения
        old_values = {
            'schedule_date': schedule.schedule_date,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'location': schedule.location
        }
        
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        await db.flush()
        await db.refresh(schedule)
        
        # Отправляем уведомление об изменении расписания
        try:
            await self._send_schedule_notification(db, schedule, current_user, is_new=False, old_values=old_values)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об изменении расписания {schedule.id}: {str(e)}")
        
        return schedule

    async def delete_schedule(
        self,
        db: AsyncSession,
        schedule_id: int,
        current_user: User
    ) -> bool:
        """Удалить расписание с проверками прав."""
        # Получение расписания
        schedule = await self.get_with_relations(db, schedule_id)
        if not schedule:
            return False
        
        # Проверка прав
        if current_user.role not in [UserRole.teacher, UserRole.admin]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только преподаватели и администраторы могут удалять расписание"
            )
        
        # Проверка прав на курс (только владелец курса или админ)
        if current_user.role != UserRole.admin and schedule.course.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы можете удалять расписание только для своих курсов"
            )
        
        await db.delete(schedule)
        await db.flush()
        
        return True

    async def _send_schedule_notification(
        self,
        db: AsyncSession,
        schedule: Schedule,
        current_user: User,
        is_new: bool = True,
        old_values: dict = None
    ) -> None:
        """Отправить уведомление о новом или измененном расписании.
        
        Args:
            db: Сессия базы данных
            schedule: Запись расписания
            current_user: Пользователь, создавший/обновивший расписание
            is_new: True для нового расписания, False для обновления
            old_values: Старые значения полей (для обновления)
        """
        try:
            # Получаем информацию о курсе с загрузкой студентов
            course_result = await db.execute(
                select(Course)
                .options(selectinload(Course.students))
                .filter(Course.id == schedule.course_id)
            )
            course = course_result.scalar_one_or_none()
            if not course:
                logger.warning(f"Course {schedule.course_id} not found for schedule notification")
                return
            
            # Получаем информацию о преподавателе
            instructor_result = await db.execute(
                select(User).filter(User.id == schedule.instructor_id)
            )
            instructor = instructor_result.scalar_one_or_none()
            
            # Формируем список студентов для уведомления
            students_data = []
            for student in course.students:
                student_user_result = await db.execute(
                    select(User).filter(User.id == student.user_id)
                )
                student_user = student_user_result.scalar_one_or_none()
                if student_user:
                    students_data.append({
                        "name": f"{student.first_name} {student.last_name}",
                        "email": student_user.username,
                        "id": student.id
                    })
            
            # Формируем данные для webhook
            notification_service = NotificationService()
            
            webhook_data = {
                "event_type": "schedule_created" if is_new else "schedule_updated",
                "schedule_id": schedule.id,
                "course_name": course.name,
                "course_id": schedule.course_id,
                "instructor_name": instructor.username if instructor else None,
                "instructor_id": schedule.instructor_id,
                "schedule_date": schedule.schedule_date.isoformat(),
                "start_time": schedule.start_time.isoformat(),
                "end_time": schedule.end_time.isoformat(),
                "location": schedule.location,
                "description": schedule.description,
                "students": students_data,
                "changed_by": current_user.username,
                "changed_by_id": current_user.id,
                "channels": ["email"]
            }
            
            # Добавляем информацию об изменениях для обновлений
            if not is_new and old_values:
                changes = {}
                if old_values['schedule_date'] != schedule.schedule_date:
                    changes['date'] = {
                        'old': old_values['schedule_date'].isoformat(),
                        'new': schedule.schedule_date.isoformat()
                    }
                if old_values['start_time'] != schedule.start_time:
                    changes['start_time'] = {
                        'old': old_values['start_time'].isoformat(),
                        'new': schedule.start_time.isoformat()
                    }
                if old_values['end_time'] != schedule.end_time:
                    changes['end_time'] = {
                        'old': old_values['end_time'].isoformat(),
                        'new': schedule.end_time.isoformat()
                    }
                if old_values['location'] != schedule.location:
                    changes['location'] = {
                        'old': old_values['location'],
                        'new': schedule.location
                    }
                webhook_data['changes'] = changes
            
            await notification_service.send_webhook(webhook_data)
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о расписании: {str(e)}")


# Создание экземпляра CRUD
schedule_crud = CRUDSchedule()