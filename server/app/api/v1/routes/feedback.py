import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user, require_role
from app.crud.feedback import feedback as crud_feedback
from app.models.user import User
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackRead,
    FeedbackReadWithAuthor,
    FeedbackUpdate,
    FeedbackList,
    FeedbackStats
)
from app.services.notification import send_feedback_notification

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Feedback"])


@router.get(
    "/submission/{submission_id}",
    response_model=FeedbackList,
    summary="Получить комментарии для задания",
    description="Получить список комментариев для конкретного задания с пагинацией"
)
async def get_feedbacks_for_submission(
    submission_id: int,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить комментарии для конкретного задания."""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be greater than 0"
        )
    
    if size < 1 or size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100"
        )
    
    skip = (page - 1) * size
    
    try:
        feedbacks = await crud_feedback.get_feedbacks_by_submission(
            db=db,
            submission_id=submission_id,
            skip=skip,
            limit=size,
            include_author=True
        )
        
        total = await crud_feedback.count_by_submission(db=db, submission_id=submission_id)
        pages = (total + size - 1) // size
        
        # Преобразуем в схему с информацией об авторе
        feedback_items = []
        for feedback_item in feedbacks:
            feedback_dict = {
                "id": feedback_item.id,
                "submission_id": feedback_item.submission_id,
                "user_id": feedback_item.user_id,
                "text": feedback_item.text,
                "created_at": feedback_item.created_at,
                "updated_at": feedback_item.updated_at,
                "author_name": feedback_item.author.username if feedback_item.author else None,
                "author_email": None  # Email not available in User model
            }
            feedback_items.append(FeedbackReadWithAuthor(**feedback_dict))
        
        return FeedbackList(
            items=feedback_items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting feedbacks for submission {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedbacks"
        )


@router.post(
    "/submission/{submission_id}",
    response_model=FeedbackReadWithAuthor,
    status_code=status.HTTP_201_CREATED,
    summary="Создать комментарий",
    description="Создать новый комментарий к заданию"
)
async def create_feedback(
    submission_id: int,
    feedback_data: FeedbackCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Создать новый комментарий к заданию."""
    try:
        feedback_item = await crud_feedback.create_feedback(
            db=db,
            submission_id=submission_id,
            user_id=current_user.id,
            feedback_data=feedback_data
        )
        
        # Добавляем задачу отправки уведомления в фоновом режиме
        background_tasks.add_task(
            send_feedback_notification,
            feedback_id=feedback_item.id,
            submission_id=submission_id,
            author_name=current_user.username,
            feedback_text=feedback_data.text
        )
        
        # Формируем ответ с информацией об авторе
        feedback_dict = {
            "id": feedback_item.id,
            "submission_id": feedback_item.submission_id,
            "user_id": feedback_item.user_id,
            "text": feedback_item.text,
            "created_at": feedback_item.created_at,
            "updated_at": feedback_item.updated_at,
            "author_name": feedback_item.author.username if feedback_item.author else None,
            "author_email": None  # Email not available in User model
        }
        
        return FeedbackReadWithAuthor(**feedback_dict)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        logger.error(f"Error creating feedback: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create feedback"
        )


@router.put(
    "/{feedback_id}",
    response_model=FeedbackReadWithAuthor,
    summary="Обновить комментарий",
    description="Обновить существующий комментарий (только автор)"
)
async def update_feedback(
    feedback_id: int,
    feedback_data: FeedbackUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Обновить комментарий (только автор может редактировать)."""
    feedback_item = await crud_feedback.update_feedback(
        db=db,
        feedback_id=feedback_id,
        feedback_data=feedback_data,
        current_user_id=current_user.id
    )
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found or you don't have permission to edit it"
        )
    
    feedback_dict = {
        "id": feedback_item.id,
        "submission_id": feedback_item.submission_id,
        "user_id": feedback_item.user_id,
        "text": feedback_item.text,
        "created_at": feedback_item.created_at,
        "updated_at": feedback_item.updated_at,
        "author_name": feedback_item.author.username if feedback_item.author else "N/A",
        "author_email": None
    }
    
    return FeedbackReadWithAuthor(**feedback_dict)


@router.delete(
    "/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить комментарий",
    description="Удалить комментарий (автор или администратор/преподаватель)"
)
async def delete_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Удалить комментарий."""
    is_admin = current_user.role in ["admin", "teacher"]
    
    success = await crud_feedback.delete_feedback(
        db=db,
        feedback_id=feedback_id,
        current_user_id=current_user.id,
        is_admin=is_admin
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found or you don't have permission to delete it"
        )


@router.get(
    "/{feedback_id}",
    response_model=FeedbackReadWithAuthor,
    summary="Получить комментарий по ID",
    description="Получить один комментарий по его ID"
)
async def get_feedback_by_id(
    feedback_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить комментарий по ID."""
    feedback_item = await crud_feedback.get_feedback_by_id(db=db, feedback_id=feedback_id)
    if not feedback_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    # Проверка прав доступа: только автор или администратор/преподаватель
    if feedback_item.user_id != current_user.id and current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    feedback_dict = {
        "id": feedback_item.id,
        "submission_id": feedback_item.submission_id,
        "user_id": feedback_item.user_id,
        "text": feedback_item.text,
        "created_at": feedback_item.created_at,
        "updated_at": feedback_item.updated_at,
        "author_name": feedback_item.author.username if feedback_item.author else "N/A",
        "author_email": None
    }
    return FeedbackReadWithAuthor(**feedback_dict)


@router.get(
    "/user/{user_id}",
    response_model=List[FeedbackRead],
    summary="Получить комментарии пользователя",
    description="Получить все комментарии конкретного пользователя"
)
async def get_user_feedbacks(
    user_id: int,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить комментарии конкретного пользователя."""
    # Пользователи могут видеть только свои комментарии, кроме администраторов/преподавателей
    if current_user.id != user_id and current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own feedbacks"
        )
    
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be greater than 0"
        )
    
    skip = (page - 1) * size
    
    try:
        feedbacks = await crud_feedback.get_feedbacks_by_user(
            db=db,
            user_id=user_id,
            skip=skip,
            limit=size
        )
        
        return [FeedbackRead.model_validate(feedback) for feedback in feedbacks]
        
    except Exception as e:
        logger.error(f"Error getting feedbacks for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user feedbacks"
        )


@router.get(
    "/recent",
    response_model=List[FeedbackRead],
    dependencies=[Depends(require_role("teacher", "admin"))],
    summary="Получить недавние комментарии",
    description="Получить недавние комментарии (только для преподавателей и администраторов)"
)
async def get_recent_feedbacks(
    days: int = 7,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_session)
):
    """Получить недавние комментарии."""
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 365"
        )
    
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )
    
    try:
        feedbacks = await crud_feedback.get_recent_feedbacks(
            db=db,
            days=days,
            limit=limit
        )
        
        return [FeedbackRead.model_validate(feedback) for feedback in feedbacks]
        
    except Exception as e:
        logger.error(f"Error getting recent feedbacks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent feedbacks"
        )


@router.get(
    "/stats",
    response_model=FeedbackStats,
    dependencies=[Depends(require_role("teacher", "admin"))],
    summary="Получить статистику комментариев",
    description="Получить статистику комментариев (только для преподавателей и администраторов)"
)
async def get_feedback_stats(
    course_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Получить статистику комментариев."""
    try:
        stats = await crud_feedback.get_feedback_stats(db=db, course_id=course_id)
        return FeedbackStats(**stats)
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback statistics"
        )