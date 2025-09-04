from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_async_session
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.enrollment import EnrollmentRole, EnrollmentStatus
from app.crud.enrollment import enrollment_crud
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    EnrollmentWithUser,
    EnrollmentWithCourse,
    EnrollmentFull,
    EnrollmentStats,
    BulkEnrollmentCreate,
    BulkEnrollmentResponse
)
from app.services.cache import analytics_cache

router = APIRouter()


@router.post("/", response_model=EnrollmentResponse)
async def create_enrollment(
    *,
    db: AsyncSession = Depends(get_async_session),
    enrollment_in: EnrollmentCreate,
    current_user: User = Depends(require_role([UserRole.admin, UserRole.teacher]))
):
    """Создать запись пользователя на курс"""
    try:
        enrollment = await enrollment_crud.create(db=db, obj_in=enrollment_in)
        # Invalidate course and student analytics caches
        await analytics_cache.invalidate_course(enrollment_in.course_id)
        await analytics_cache.invalidate_student(enrollment_in.user_id)
        return enrollment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании записи на курс: {str(e)}"
        )


@router.get("/{enrollment_id}", response_model=EnrollmentFull)
async def get_enrollment(
    enrollment_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить информацию о записи на курс"""
    enrollment = await enrollment_crud.get(db=db, id=enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись на курс не найдена"
        )
    
    # Проверяем права доступа
    if (current_user.role not in [UserRole.admin, UserRole.teacher] and 
        enrollment.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этой записи"
        )
    
    return enrollment


@router.put("/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: int,
    enrollment_update: EnrollmentUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.teacher]))
):
    """Обновить запись на курс"""
    enrollment = await enrollment_crud.get(db=db, id=enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись на курс не найдена"
        )
    
    updated_enrollment = await enrollment_crud.update(
        db=db, db_obj=enrollment, obj_in=enrollment_update
    )
    # Invalidate course and student analytics caches
    await analytics_cache.invalidate_course(enrollment.course_id)
    await analytics_cache.invalidate_student(enrollment.user_id)
    return updated_enrollment


@router.delete("/{enrollment_id}")
async def delete_enrollment(
    enrollment_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.teacher]))
):
    """Удалить запись на курс"""
    # Fetch before delete for invalidation
    existing = await enrollment_crud.get(db=db, id=enrollment_id)
    success = await enrollment_crud.delete(db=db, id=enrollment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись на курс не найдена"
        )
    if existing:
        await analytics_cache.invalidate_course(existing.course_id)
        await analytics_cache.invalidate_student(existing.user_id)
    return {"message": "Запись на курс успешно удалена"}


@router.get("/user/{user_id}", response_model=List[EnrollmentWithCourse])
async def get_user_enrollments(
    user_id: int,
    status: Optional[EnrollmentStatus] = Query(None, description="Фильтр по статусу"),
    role: Optional[EnrollmentRole] = Query(None, description="Фильтр по роли"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить все записи пользователя на курсы"""
    # Проверяем права доступа
    if (current_user.role not in [UserRole.admin, UserRole.teacher] and 
        user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра записей этого пользователя"
        )
    
    enrollments = await enrollment_crud.get_user_enrollments(
        db=db, user_id=user_id, status=status, role=role
    )
    return enrollments


@router.get("/course/{course_id}", response_model=List[EnrollmentWithUser])
async def get_course_enrollments(
    course_id: int,
    status: Optional[EnrollmentStatus] = Query(None, description="Фильтр по статусу"),
    role: Optional[EnrollmentRole] = Query(None, description="Фильтр по роли"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.teacher]))
):
    """Получить все записи на курс"""
    enrollments = await enrollment_crud.get_course_enrollments(
        db=db, course_id=course_id, status=status, role=role
    )
    return enrollments


@router.get("/course/{course_id}/students", response_model=List[EnrollmentWithUser])
async def get_course_students(
    course_id: int,
    active_only: bool = Query(True, description="Только активные студенты"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.teacher]))
):
    """Получить всех студентов курса"""
    students = await enrollment_crud.get_course_students(
        db=db, course_id=course_id, active_only=active_only
    )
    return students


@router.get("/course/{course_id}/teachers", response_model=List[EnrollmentWithUser])
async def get_course_teachers(
    course_id: int,
    active_only: bool = Query(True, description="Только активные преподаватели"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить всех преподавателей курса"""
    teachers = await enrollment_crud.get_course_teachers(
        db=db, course_id=course_id, active_only=active_only
    )
    return teachers


@router.get("/course/{course_id}/stats", response_model=EnrollmentStats)
async def get_enrollment_stats(
    course_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.teacher]))
):
    """Получить статистику записей на курс"""
    stats = await enrollment_crud.get_enrollment_stats(db=db, course_id=course_id)
    return stats


@router.post("/bulk", response_model=BulkEnrollmentResponse)
async def bulk_create_enrollments(
    bulk_enrollment: BulkEnrollmentCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.teacher]))
):
    """Массовая запись пользователей на курс"""
    try:
        result = await enrollment_crud.bulk_create(db=db, obj_in=bulk_enrollment)
        return BulkEnrollmentResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при массовой записи на курс: {str(e)}"
        )


@router.post("/check-access")
async def check_user_access(
    user_id: int,
    course_id: int,
    required_roles: Optional[List[EnrollmentRole]] = Query(None),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Проверить доступ пользователя к курсу"""
    # Проверяем права на проверку доступа
    if (current_user.role not in [UserRole.admin, UserRole.teacher] and 
        user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для проверки доступа"
        )
    
    enrollment = await enrollment_crud.check_user_enrollment(
        db=db, user_id=user_id, course_id=course_id, required_roles=required_roles
    )
    
    return {
        "has_access": enrollment is not None,
        "enrollment": enrollment,
        "user_id": user_id,
        "course_id": course_id,
        "required_roles": required_roles
    }

