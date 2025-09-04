from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_async_session
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.notification import NotificationStatus, NotificationType
from app.crud.notification import notification_crud, notification_preferences_crud
from app.schemas.notification import (
    InAppNotificationResponse,
    InAppNotificationCreate,
    InAppNotificationUpdate,
    NotificationListResponse,
    NotificationStatsResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    BulkNotificationAction,
    BulkNotificationResponse,
    NotificationCreateRequest
)

router = APIRouter()


@router.get("/", response_model=NotificationListResponse)
async def get_user_notifications(
    status: Optional[NotificationStatus] = Query(None, description="Фильтр по статусу"),
    notification_type: Optional[NotificationType] = Query(None, description="Фильтр по типу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Элементов на странице"),
    include_expired: bool = Query(False, description="Включать истекшие уведомления"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить список уведомлений текущего пользователя"""
    offset = (page - 1) * per_page
    
    # Получаем уведомления
    notifications = await notification_crud.get_user_notifications(
        db=db,
        user_id=current_user.id,
        status=status,
        notification_type=notification_type,
        limit=per_page,
        offset=offset,
        include_expired=include_expired
    )
    
    # Получаем общее количество и количество непрочитанных
    stats = await notification_crud.get_notification_stats(db, current_user.id)
    total = stats["total_notifications"]
    unread_count = stats["unread_count"]
    
    return NotificationListResponse(
        notifications=notifications,
        total=total,
        unread_count=unread_count,
        page=page,
        per_page=per_page,
        has_next=offset + len(notifications) < total,
        has_prev=page > 1
    )


@router.get("/unread/count")
async def get_unread_count(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить количество непрочитанных уведомлений"""
    count = await notification_crud.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить статистику уведомлений пользователя"""
    stats = await notification_crud.get_notification_stats(db, current_user.id)
    return NotificationStatsResponse(**stats)


@router.get("/{notification_id}", response_model=InAppNotificationResponse)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить конкретное уведомление"""
    notification = await notification_crud.get(db=db, id=notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено"
        )
    
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этого уведомления"
        )
    
    return notification


@router.patch("/{notification_id}/read", response_model=InAppNotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Отметить уведомление как прочитанное"""
    notification = await notification_crud.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено"
        )
    
    return notification


@router.patch("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Отметить все уведомления как прочитанные"""
    updated_count = await notification_crud.mark_all_as_read(
        db=db,
        user_id=current_user.id
    )
    
    return {"message": f"Отмечено как прочитанные {updated_count} уведомлений"}


@router.patch("/{notification_id}/archive", response_model=InAppNotificationResponse)
async def archive_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Архивировать уведомление"""
    notification = await notification_crud.archive_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено"
        )
    
    return notification


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Удалить уведомление"""
    success = await notification_crud.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено"
        )
    
    return {"message": "Уведомление удалено"}


@router.post("/bulk-action", response_model=BulkNotificationResponse)
async def bulk_notification_action(
    action_data: BulkNotificationAction,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Выполнить массовое действие с уведомлениями"""
    if not action_data.notification_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не указаны ID уведомлений"
        )
    
    valid_actions = ["mark_read", "mark_unread", "archive", "delete"]
    if action_data.action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимое действие. Доступны: {', '.join(valid_actions)}"
        )
    
    result = await notification_crud.bulk_action(
        db=db,
        user_id=current_user.id,
        action_data=action_data
    )
    
    return BulkNotificationResponse(**result)


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить настройки уведомлений пользователя"""
    preferences = await notification_preferences_crud.get_or_create(
        db=db,
        user_id=current_user.id
    )
    return preferences


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferencesUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Обновить настройки уведомлений пользователя"""
    preferences = await notification_preferences_crud.update(
        db=db,
        user_id=current_user.id,
        obj_in=preferences_update
    )
    return preferences


# Административные эндпоинты
@router.post("/admin/create", response_model=List[InAppNotificationResponse])
async def create_notifications(
    notification_request: NotificationCreateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.teacher]))
):
    """Создать уведомления для пользователей (только для админов/преподавателей)"""
    if not notification_request.recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не указаны получатели"
        )
    
    # Создаем уведомления для каждого получателя
    notifications_data = []
    for user_id in notification_request.recipients:
        notification_data = InAppNotificationCreate(
            user_id=user_id,
            title=notification_request.title,
            message=notification_request.message,
            notification_type=notification_request.notification_type,
            priority=notification_request.priority,
            extra_data=notification_request.metadata,
            action_url=notification_request.action_url,
            expires_at=notification_request.expires_at,
            assignment_id=notification_request.assignment_id,
            course_id=notification_request.course_id,
            grade_id=notification_request.grade_id,
            schedule_id=notification_request.schedule_id
        )
        notifications_data.append(notification_data)
    
    # Создаем уведомления в базе данных
    notifications = await notification_crud.create_multiple(
        db=db,
        notifications=notifications_data
    )
    
    return notifications


@router.delete("/admin/cleanup-expired")
async def cleanup_expired_notifications(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    """Очистить истекшие уведомления (только для админов)"""
    deleted_count = await notification_crud.cleanup_expired(db=db)
    return {"message": f"Удалено {deleted_count} истекших уведомлений"}

