from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.enrollment import Enrollment, EnrollmentRole, EnrollmentStatus
from app.models.user import User
from app.models.course import Course
from app.schemas.enrollment import (
    EnrollmentCreate, 
    EnrollmentUpdate, 
    BulkEnrollmentCreate,
    EnrollmentStats
)


class CRUDEnrollment:
    """CRUD операции для Enrollment"""

    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: EnrollmentCreate
    ) -> Enrollment:
        """Создать запись на курс"""
        # Проверяем, не существует ли уже такая запись
        existing = await self.get_by_user_and_course(
            db, user_id=obj_in.user_id, course_id=obj_in.course_id, role=obj_in.role
        )
        if existing:
            # Обновляем существующую запись
            return await self.update(db, db_obj=existing, obj_in=obj_in)
        
        db_obj = Enrollment(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: int) -> Optional[Enrollment]:
        """Получить запись по ID"""
        result = await db.execute(
            select(Enrollment)
            .options(selectinload(Enrollment.user))
            .options(selectinload(Enrollment.course))
            .filter(Enrollment.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_course(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        course_id: int, 
        role: Optional[EnrollmentRole] = None
    ) -> Optional[Enrollment]:
        """Получить запись пользователя на курс"""
        query = select(Enrollment).filter(
            and_(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id
            )
        )
        
        if role:
            query = query.filter(Enrollment.role == role)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_enrollments(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int,
        status: Optional[EnrollmentStatus] = None,
        role: Optional[EnrollmentRole] = None
    ) -> List[Enrollment]:
        """Получить все записи пользователя на курсы"""
        query = select(Enrollment).filter(Enrollment.user_id == user_id)
        
        if status:
            query = query.filter(Enrollment.status == status)
        if role:
            query = query.filter(Enrollment.role == role)
            
        query = query.options(
            selectinload(Enrollment.course)
        ).order_by(Enrollment.enrolled_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_course_enrollments(
        self, 
        db: AsyncSession, 
        *, 
        course_id: int,
        status: Optional[EnrollmentStatus] = None,
        role: Optional[EnrollmentRole] = None
    ) -> List[Enrollment]:
        """Получить все записи на курс"""
        query = select(Enrollment).filter(Enrollment.course_id == course_id)
        
        if status:
            query = query.filter(Enrollment.status == status)
        if role:
            query = query.filter(Enrollment.role == role)
            
        query = query.options(
            selectinload(Enrollment.user)
        ).order_by(Enrollment.enrolled_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_course_students(
        self, 
        db: AsyncSession, 
        course_id: int,
        active_only: bool = True
    ) -> List[Enrollment]:
        """Получить всех студентов курса"""
        query = select(Enrollment).filter(
            and_(
                Enrollment.course_id == course_id,
                Enrollment.role == EnrollmentRole.student
            )
        )
        
        if active_only:
            query = query.filter(Enrollment.status == EnrollmentStatus.active)
            
        query = query.options(selectinload(Enrollment.user))
        result = await db.execute(query)
        return result.scalars().all()

    async def get_course_teachers(
        self, 
        db: AsyncSession, 
        course_id: int,
        active_only: bool = True
    ) -> List[Enrollment]:
        """Получить всех преподавателей курса"""
        query = select(Enrollment).filter(
            and_(
                Enrollment.course_id == course_id,
                Enrollment.role.in_([EnrollmentRole.teacher, EnrollmentRole.ta])
            )
        )
        
        if active_only:
            query = query.filter(Enrollment.status == EnrollmentStatus.active)
            
        query = query.options(selectinload(Enrollment.user))
        result = await db.execute(query)
        return result.scalars().all()

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Enrollment, 
        obj_in: EnrollmentUpdate
    ) -> Enrollment:
        """Обновить запись на курс"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Автоматически устанавливаем даты при смене статуса
        if "status" in update_data:
            if update_data["status"] == EnrollmentStatus.completed:
                update_data["completed_at"] = datetime.utcnow()
            elif update_data["status"] == EnrollmentStatus.dropped:
                update_data["dropped_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """Удалить запись на курс"""
        result = await db.execute(select(Enrollment).filter(Enrollment.id == id))
        obj = result.scalar_one_or_none()
        
        if obj:
            await db.delete(obj)
            await db.commit()
            return True
        return False

    async def bulk_create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: BulkEnrollmentCreate
    ) -> Dict[str, Any]:
        """Массовое создание записей на курс"""
        created_count = 0
        skipped_count = 0
        errors = []
        created_enrollments = []
        
        for user_id in obj_in.user_ids:
            try:
                # Проверяем существование записи
                existing = await self.get_by_user_and_course(
                    db, user_id=user_id, course_id=obj_in.course_id, role=obj_in.role
                )
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Создаем новую запись
                enrollment_data = EnrollmentCreate(
                    user_id=user_id,
                    course_id=obj_in.course_id,
                    role=obj_in.role,
                    status=obj_in.status
                )
                
                enrollment = await self.create(db, obj_in=enrollment_data)
                created_enrollments.append(enrollment)
                created_count += 1
                
            except Exception as e:
                errors.append(f"User {user_id}: {str(e)}")
        
        return {
            "created_count": created_count,
            "skipped_count": skipped_count,
            "errors": errors,
            "created_enrollments": created_enrollments
        }

    async def get_enrollment_stats(
        self, 
        db: AsyncSession, 
        course_id: int
    ) -> EnrollmentStats:
        """Получить статистику записей на курс"""
        # Общее количество записей
        total_result = await db.execute(
            select(func.count(Enrollment.id))
            .filter(Enrollment.course_id == course_id)
        )
        total_enrollments = total_result.scalar()
        
        # Активные студенты
        students_result = await db.execute(
            select(func.count(Enrollment.id))
            .filter(
                and_(
                    Enrollment.course_id == course_id,
                    Enrollment.role == EnrollmentRole.student,
                    Enrollment.status == EnrollmentStatus.active
                )
            )
        )
        active_students = students_result.scalar()
        
        # Активные преподаватели
        teachers_result = await db.execute(
            select(func.count(Enrollment.id))
            .filter(
                and_(
                    Enrollment.course_id == course_id,
                    Enrollment.role.in_([EnrollmentRole.teacher, EnrollmentRole.ta]),
                    Enrollment.status == EnrollmentStatus.active
                )
            )
        )
        active_teachers = teachers_result.scalar()
        
        # Завершившие курс
        completed_result = await db.execute(
            select(func.count(Enrollment.id))
            .filter(
                and_(
                    Enrollment.course_id == course_id,
                    Enrollment.status == EnrollmentStatus.completed
                )
            )
        )
        completed_count = completed_result.scalar()
        
        # Покинувшие курс
        dropped_result = await db.execute(
            select(func.count(Enrollment.id))
            .filter(
                and_(
                    Enrollment.course_id == course_id,
                    Enrollment.status == EnrollmentStatus.dropped
                )
            )
        )
        dropped_count = dropped_result.scalar()
        
        # Распределение по ролям
        role_stats_result = await db.execute(
            select(Enrollment.role, func.count(Enrollment.id))
            .filter(Enrollment.course_id == course_id)
            .group_by(Enrollment.role)
        )
        by_role = {role: count for role, count in role_stats_result.all()}
        
        # Распределение по статусам
        status_stats_result = await db.execute(
            select(Enrollment.status, func.count(Enrollment.id))
            .filter(Enrollment.course_id == course_id)
            .group_by(Enrollment.status)
        )
        by_status = {status: count for status, count in status_stats_result.all()}
        
        return EnrollmentStats(
            total_enrollments=total_enrollments,
            active_students=active_students,
            active_teachers=active_teachers,
            completed_count=completed_count,
            dropped_count=dropped_count,
            by_role=by_role,
            by_status=by_status
        )

    async def check_user_enrollment(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        course_id: int,
        required_roles: Optional[List[EnrollmentRole]] = None
    ) -> Optional[Enrollment]:
        """Проверить запись пользователя на курс с определенными ролями"""
        query = select(Enrollment).filter(
            and_(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
                Enrollment.status == EnrollmentStatus.active
            )
        )
        
        if required_roles:
            query = query.filter(Enrollment.role.in_(required_roles))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Создаем экземпляр CRUD
enrollment_crud = CRUDEnrollment()

