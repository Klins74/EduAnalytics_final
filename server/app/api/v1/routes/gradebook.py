from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_async_session
from app.core.security import get_current_user, require_role
from app.crud.gradebook import gradebook
from app.models.user import User
from app.schemas.gradebook import (
    GradebookEntryCreate,
    GradebookEntryUpdate,
    GradebookEntryRead,
    GradebookHistoryRead,
    GradebookEntryList,
    GradebookStats
)



router = APIRouter(prefix="/gradebook", tags=["Gradebook"])


@router.get(
    "/",
    response_model=List[GradebookEntryRead],
    summary="Получить список записей журнала",
    description="""Получить список записей электронного журнала с возможностью фильтрации.
    
    **Права доступа:**
    - Учителя и администраторы: могут просматривать все записи
    - Студенты: могут просматривать только свои записи
    
    **Фильтры:**
    - course_id: фильтр по курсу
    - student_id: фильтр по студенту (игнорируется для студентов)
    - assignment_id: фильтр по заданию
    """
)
async def list_entries(
    course_id: Optional[int] = Query(None, description="ID курса для фильтрации"),
    student_id: Optional[int] = Query(None, description="ID студента для фильтрации"),
    assignment_id: Optional[int] = Query(None, description="ID задания для фильтрации"),
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получить список записей журнала."""
    try:
        # Для студентов ограничиваем доступ только к их записям
        if current_user.role == "student":
            student_id = current_user.id
            logger.info(f"Student {current_user.id} accessing their gradebook entries")
        elif current_user.role not in ["teacher", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра журнала"
            )
        
        entries = gradebook.get_entries(
            db,
            course_id=course_id,
            student_id=student_id,
            assignment_id=assignment_id,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"Retrieved {len(entries)} gradebook entries for user {current_user.id}")
        return entries
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving gradebook entries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении записей журнала"
        )


@router.get(
    "/{entry_id}",
    response_model=GradebookEntryRead,
    summary="Получить запись журнала",
    description="""Получить конкретную запись электронного журнала по ID.
    
    **Права доступа:**
    - Учителя и администраторы: могут просматривать любые записи
    - Студенты: могут просматривать только свои записи
    """
)
async def get_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получить запись журнала по ID."""
    try:
        entry = gradebook.get_entry(db, entry_id=entry_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись в журнале не найдена"
            )
        
        # Проверяем права доступа
        if current_user.role == "student" and entry.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра этой записи"
            )
        elif current_user.role not in ["student", "teacher", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра журнала"
            )
        
        logging.info(f"Retrieved gradebook entry {entry_id} for user {current_user.id}")
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving gradebook entry {entry_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении записи журнала"
        )


@router.post(
    "/",
    response_model=GradebookEntryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать запись в журнале",
    description="""Создать новую запись в электронном журнале.
    
    **Права доступа:** только учителя и администраторы
    
    **Валидация:**
    - Оценка должна быть в диапазоне 0-100
    - Проверяется существование курса, студента и задания
    - Предотвращается создание дублирующих записей
    
    **Audit Trail:** автоматически создается запись в истории изменений
    """
)
async def create_entry(
    entry_in: GradebookEntryCreate,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: AsyncSession = Depends(get_async_session)
):
    """Создать новую запись в журнале."""
    try:
        entry = gradebook.create_entry(
            db,
            entry_in=entry_in,
            current_user=current_user
        )
        
        logging.info(f"Created gradebook entry {entry.id} by user {current_user.id}")
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating gradebook entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании записи в журнале"
        )


@router.put(
    "/{entry_id}",
    response_model=GradebookEntryRead,
    summary="Обновить запись в журнале",
    description="""Обновить существующую запись в электронном журнале.
    
    **Права доступа:** только учителя и администраторы
    
    **Валидация:**
    - Оценка должна быть в диапазоне 0-100 (если указана)
    - Обновляются только переданные поля
    
    **Audit Trail:** автоматически создается запись в истории изменений
    """
)
async def update_entry(
    entry_id: int,
    entry_in: GradebookEntryUpdate,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: AsyncSession = Depends(get_async_session)
):
    """Обновить запись в журнале."""
    try:
        entry = gradebook.update_entry(
            db,
            entry_id=entry_id,
            entry_in=entry_in,
            current_user=current_user
        )
        
        logging.info(f"Updated gradebook entry {entry_id} by user {current_user.id}")
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating gradebook entry {entry_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении записи в журнале"
        )


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить запись из журнала",
    description="""Удалить запись из электронного журнала.
    
    **Права доступа:** только учителя и администраторы
    
    **Audit Trail:** автоматически создается запись в истории изменений
    
    **Внимание:** удаление необратимо, но история изменений сохраняется
    """
)
async def delete_entry(
    entry_id: int,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: AsyncSession = Depends(get_async_session)
):
    """Удалить запись из журнала."""
    try:
        gradebook.delete_entry(
            db,
            entry_id=entry_id,
            current_user=current_user
        )
        
        logging.info(f"Deleted gradebook entry {entry_id} by user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting gradebook entry {entry_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении записи из журнала"
        )


@router.get(
    "/history/{entry_id}",
    response_model=List[GradebookHistoryRead],
    summary="Получить историю изменений записи",
    description="""Получить полную историю изменений конкретной записи журнала.
    
    **Права доступа:**
    - Учителя и администраторы: могут просматривать историю любых записей
    - Студенты: могут просматривать историю только своих записей
    
    **Информация в истории:**
    - Все изменения оценок и комментариев
    - Информация о том, кто и когда внес изменения
    - Тип операции (создание, обновление, удаление)
    """
)
async def get_entry_history(
    entry_id: int,
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получить историю изменений записи."""
    try:
        # Сначала проверяем существование записи и права доступа
        entry = gradebook.get_entry(db, entry_id=entry_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись в журнале не найдена"
            )
        
        # Проверяем права доступа
        if current_user.role == "student" and entry.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра истории этой записи"
            )
        elif current_user.role not in ["student", "teacher", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра истории журнала"
            )
        
        history = gradebook.get_entry_history(
            db,
            entry_id=entry_id,
            skip=skip,
            limit=limit
        )
        
        logging.info(f"Retrieved history for gradebook entry {entry_id} by user {current_user.id}")
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving history for gradebook entry {entry_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении истории записи"
        )


@router.get(
    "/stats/",
    response_model=GradebookStats,
    summary="Получить статистику по оценкам",
    description="""Получить статистику по оценкам с возможностью фильтрации.
    
    **Права доступа:**
    - Учителя и администраторы: могут получать статистику по любым курсам и студентам
    - Студенты: могут получать статистику только по своим оценкам
    
    **Статистика включает:**
    - Средняя оценка
    - Минимальная и максимальная оценки
    - Общее количество записей
    - Количество оцененных заданий
    """
)
async def get_stats(
    course_id: Optional[int] = Query(None, description="ID курса для фильтрации"),
    student_id: Optional[int] = Query(None, description="ID студента для фильтрации"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получить статистику по оценкам."""
    try:
        # Для студентов ограничиваем доступ только к их статистике
        if current_user.role == "student":
            student_id = current_user.id
            logging.info(f"Student {current_user.id} accessing their grade statistics")
        elif current_user.role not in ["teacher", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра статистики"
            )
        
        stats = gradebook.get_stats(
            db,
            course_id=course_id,
            student_id=student_id
        )
        
        logging.info(f"Retrieved grade statistics for user {current_user.id}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving grade statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статистики по оценкам"
        )