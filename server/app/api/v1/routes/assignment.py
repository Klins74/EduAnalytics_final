from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.core.security import require_role
from app.models.user import User, UserRole
from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate, AssignmentList
from app.crud import assignment as crud_assignment

router = APIRouter(
    prefix="/assignments",
    tags=["Assignments"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Assignment not found"},
        400: {"description": "Bad request - validation error"}
    }
)


@router.get(
    "/",
    response_model=AssignmentList,
    summary="Получить список заданий",
    description="Получить список всех заданий с возможностью пагинации и фильтрации по курсу"
)
async def get_assignments(
    course_id: Optional[int] = Query(None, description="ID курса для фильтрации"),
    skip: int = Query(0, ge=0, description="Количество заданий для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество заданий"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить список заданий с пагинацией."""
    assignments, total = crud_assignment.get_assignments(
        db=db,
        course_id=course_id,
        skip=skip,
        limit=limit
    )
    
    return AssignmentList(
        assignments=assignments,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{assignment_id}",
    response_model=AssignmentRead,
    summary="Получить задание по ID",
    description="Получить подробную информацию о задании по его идентификатору"
)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить задание по ID."""
    assignment = crud_assignment.get_assignment_by_id(db=db, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено"
        )
    return assignment


@router.post(
    "/",
    response_model=AssignmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое задание",
    description="Создать новое задание для курса. Доступно только преподавателям и администраторам. Дедлайн должен быть в пределах периода курса."
)
async def create_assignment(
    assignment: AssignmentCreate,
    due_date: datetime = Query(..., description="Дедлайн задания", examples=["2024-03-15T23:59:59"]),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
):
    """Создать новое задание.
    
    Проверки:
    - Пользователь должен быть преподавателем или администратором
    - Курс должен существовать
    - Пользователь должен быть владельцем курса (или администратором)
    - Дедлайн должен быть в пределах периода курса
    """
    # Обновляем дедлайн из query параметра
    assignment.due_date = due_date
    
    return crud_assignment.create_assignment(
        db=db,
        assignment=assignment,
        current_user=current_user
    )


@router.put(
    "/{assignment_id}",
    response_model=AssignmentRead,
    summary="Обновить задание",
    description="Обновить существующее задание. Доступно только владельцу курса или администратору. При обновлении дедлайна проверяется его соответствие периоду курса."
)
async def update_assignment(
    assignment_id: int,
    assignment_update: AssignmentUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Обновить задание.
    
    Проверки:
    - Задание должно существовать
    - Пользователь должен быть владельцем курса или администратором
    - При обновлении дедлайна проверяется период курса
    """
    assignment = crud_assignment.update_assignment(
        db=db,
        assignment_id=assignment_id,
        assignment_update=assignment_update,
        current_user=current_user
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено"
        )
    return assignment


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задание",
    description="Удалить задание. Доступно только владельцу курса или администратору"
)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Удалить задание.
    
    Проверки:
    - Задание должно существовать
    - Пользователь должен быть владельцем курса или администратором
    """
    success = crud_assignment.delete_assignment(
        db=db,
        assignment_id=assignment_id,
        current_user=current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено"
        )