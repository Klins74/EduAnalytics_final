from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate, CourseList
from app.crud import course as crud_course

router = APIRouter(
    tags=["Courses"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Course not found"},
        409: {"description": "Course with this title already exists"}
    }
)


@router.get(
    "/",
    response_model=CourseList,
    summary="Получить список курсов",
    description="Получить список всех курсов с возможностью пагинации и фильтрации по владельцу"
)
async def get_courses(
    skip: int = Query(0, ge=0, description="Количество курсов для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество курсов"),
    owner_id: Optional[int] = Query(None, description="ID владельца для фильтрации"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить список курсов с пагинацией."""
    courses, total = await crud_course.get_courses(
        db=db, 
        skip=skip, 
        limit=limit, 
        owner_id=owner_id
    )
    
    return CourseList(
        courses=courses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{course_id}",
    response_model=CourseRead,
    summary="Получить курс по ID",
    description="Получить подробную информацию о курсе по его идентификатору"
)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить курс по ID."""
    course = await crud_course.get_course_by_id(db=db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    return course


@router.post(
    "/",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый курс",
    description="Создать новый курс. Доступно только преподавателям и администраторам"
)
async def create_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
):
    """Создать новый курс."""
    return await crud_course.create_course(
        db=db, 
        course=course, 
        current_user=current_user
    )


@router.put(
    "/{course_id}",
    response_model=CourseRead,
    summary="Обновить курс",
    description="Обновить существующий курс. Доступно только владельцу курса или администратору"
)
async def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Обновить курс."""
    course = await crud_course.update_course(
        db=db,
        course_id=course_id,
        course_update=course_update,
        current_user=current_user
    )
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    return course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить курс",
    description="Удалить курс. Доступно только владельцу курса или администратору"
)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Удалить курс."""
    success = await crud_course.delete_course(
        db=db,
        course_id=course_id,
        current_user=current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )


@router.get(
    "/{course_id}/assignments",
    summary="Получить задания курса",
    description="Получить все задания для конкретного курса"
)
async def get_course_assignments(
    course_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить задания курса."""
    # Проверяем существование курса
    course = await crud_course.get_course_by_id(db=db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    
    # Получаем задания курса
    from app.crud import assignment as crud_assignment
    assignments = await crud_assignment.get_assignments_by_course_id(db=db, course_id=course_id)
    return {"course_id": course_id, "assignments": assignments}


@router.get(
    "/{course_id}/analytics",
    summary="Получить аналитику курса",
    description="Получить базовую аналитику по курсу - количество студентов, заданий, среднюю успеваемость"
)
async def get_course_analytics(
    course_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить аналитику курса."""
    # Проверяем существование курса
    course = await crud_course.get_course_by_id(db=db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    
    # Проверяем права на просмотр аналитики
    if (current_user.role not in [UserRole.teacher, UserRole.admin] and 
        course.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра аналитики"
        )
    
    # TODO: Реализовать получение аналитики
    return {
        "course_id": course_id,
        "course_title": course.title,
        "students_count": 0,  # TODO: подсчитать из enrollments
        "assignments_count": 0,  # TODO: подсчитать задания
        "average_grade": 0.0,  # TODO: подсчитать среднюю оценку
        "completion_rate": 0.0  # TODO: подсчитать процент выполнения
    }


@router.get(
    "/{course_id}/quizzes",
    summary="Получить квизы курса",
    description="Получить все квизы для конкретного курса"
)
async def get_course_quizzes(
    course_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить квизы курса."""
    # Проверяем существование курса
    course = await crud_course.get_course_by_id(db=db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    
    # Получаем квизы курса
    from sqlalchemy import select
    from app.models.quiz import Quiz
    result = await db.execute(select(Quiz).filter(Quiz.course_id == course_id))
    quizzes = result.scalars().all()
    
    return quizzes