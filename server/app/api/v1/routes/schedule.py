from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.crud.schedule import schedule_crud
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleRead,
    ScheduleList
)

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


def require_teacher_or_admin(current_user: User = Depends(get_current_user)):
    """Зависимость для проверки прав преподавателя или администратора."""
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только преподавателям и администраторам"
        )
    return current_user


@router.get("/", response_model=ScheduleList)
async def get_schedules(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    course_id: Optional[int] = Query(None, description="Фильтр по ID курса"),
    date_from: Optional[date] = Query(None, description="Фильтр по дате начала"),
    date_to: Optional[date] = Query(None, description="Фильтр по дате окончания"),
    instructor_id: Optional[int] = Query(None, description="Фильтр по ID преподавателя"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить список расписаний с фильтрацией.
    
    Доступно всем авторизованным пользователям.
    Поддерживает фильтрацию по курсу, дате и преподавателю.
    """
    # Валидация дат
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Начальная дата не может быть больше конечной"
        )
    
    schedules, total = await schedule_crud.get_schedules(
        db=db,
        skip=skip,
        limit=limit,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
        instructor_id=instructor_id
    )
    
    return ScheduleList(
        schedules=schedules,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{schedule_id}", response_model=ScheduleRead)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить расписание по ID.
    
    Доступно всем авторизованным пользователям.
    """
    schedule = await schedule_crud.get_with_relations(db, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Расписание с ID {schedule_id} не найдено"
        )
    
    return schedule


@router.post("/", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Создать новое расписание.
    
    Доступно только преподавателям и администраторам.
    Преподаватели могут создавать расписание только для своих курсов.
    """
    schedule = await schedule_crud.create_schedule(
        db=db,
        schedule_data=schedule_data,
        current_user=current_user
    )
    
    # Получаем созданное расписание с загруженными связями
    created_schedule = await schedule_crud.get_with_relations(db, schedule.id)
    
    return created_schedule


@router.put("/{schedule_id}", response_model=ScheduleRead)
async def update_schedule(
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Обновить расписание.
    
    Доступно только преподавателям и администраторам.
    Преподаватели могут изменять расписание только для своих курсов.
    """
    schedule = await schedule_crud.update_schedule(
        db=db,
        schedule_id=schedule_id,
        schedule_update=schedule_update,
        current_user=current_user
    )
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Расписание с ID {schedule_id} не найдено"
        )
    
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Удалить расписание.
    
    Доступно только преподавателям и администраторам.
    Преподаватели могут удалять расписание только для своих курсов.
    """
    deleted = await schedule_crud.delete_schedule(
        db=db,
        schedule_id=schedule_id,
        current_user=current_user
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Расписание с ID {schedule_id} не найдено"
        )