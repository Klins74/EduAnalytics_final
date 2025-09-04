from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.models.notification import (
    InAppNotification, 
    NotificationPreferences, 
    NotificationStatus, 
    NotificationType,
    NotificationPriority
)
from app.models.user import User
from app.schemas.notification import (
    InAppNotificationCreate,
    InAppNotificationUpdate,
    NotificationPreferencesUpdate
)


class CRUDNotification:
    """CRUD операции для in-app уведомлений"""

    async def create_notification(
        self, 
        db: AsyncSession, 
        notification_data: InAppNotificationCreate
    ) -> InAppNotification:
        """Создать новое уведомление"""
        db_notification = InAppNotification(
            user_id=notification_data.user_id,
            title=notification_data.title,
            message=notification_data.message,
            notification_type=notification_data.notification_type,
            priority=notification_data.priority,
            extra_data=notification_data.extra_data,
            assignment_id=notification_data.assignment_id,
            course_id=notification_data.course_id,
            grade_id=notification_data.grade_id,
            expires_at=notification_data.expires_at
        )
        
        db.add(db_notification)
        await db.commit()
        await db.refresh(db_notification)
        return db_notification

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 20,
        offset: int = 0,
        include_expired: bool = False
    ) -> List[InAppNotification]:
        """Получить уведомления пользователя"""
        query = select(InAppNotification).where(InAppNotification.user_id == user_id)
        
        # Фильтр по статусу
        if status:
            query = query.where(InAppNotification.status == status)
        
        # Фильтр по типу
        if notification_type:
            query = query.where(InAppNotification.notification_type == notification_type)
        
        # Фильтр по истечению срока
        if not include_expired:
            current_time = datetime.now()
            query = query.where(
                or_(
                    InAppNotification.expires_at.is_(None),
                    InAppNotification.expires_at > current_time
                )
            )
        
        # Сортировка и пагинация
        query = query.order_by(desc(InAppNotification.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_notification(
        self, 
        db: AsyncSession, 
        notification_id: int, 
        user_id: int
    ) -> Optional[InAppNotification]:
        """Получить конкретное уведомление пользователя"""
        result = await db.execute(
            select(InAppNotification).where(
                and_(
                    InAppNotification.id == notification_id,
                    InAppNotification.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def mark_as_read(
        self, 
        db: AsyncSession, 
        notification_id: int, 
        user_id: int
    ) -> Optional[InAppNotification]:
        """Отметить уведомление как прочитанное"""
        notification = await self.get_notification(db, notification_id, user_id)
        if notification and notification.status == NotificationStatus.unread:
            notification.status = NotificationStatus.read
            notification.read_at = datetime.now()
            await db.commit()
            await db.refresh(notification)
        return notification

    async def mark_as_unread(
        self, 
        db: AsyncSession, 
        notification_id: int, 
        user_id: int
    ) -> Optional[InAppNotification]:
        """Отметить уведомление как непрочитанное"""
        notification = await self.get_notification(db, notification_id, user_id)
        if notification and notification.status == NotificationStatus.read:
            notification.status = NotificationStatus.unread
            notification.read_at = None
            await db.commit()
            await db.refresh(notification)
        return notification

    async def archive_notification(
        self, 
        db: AsyncSession, 
        notification_id: int, 
        user_id: int
    ) -> Optional[InAppNotification]:
        """Архивировать уведомление"""
        notification = await self.get_notification(db, notification_id, user_id)
        if notification and notification.status != NotificationStatus.archived:
            notification.status = NotificationStatus.archived
            notification.archived_at = datetime.now()
            await db.commit()
            await db.refresh(notification)
        return notification

    async def delete_notification(
        self, 
        db: AsyncSession, 
        notification_id: int, 
        user_id: int
    ) -> bool:
        """Удалить уведомление"""
        notification = await self.get_notification(db, notification_id, user_id)
        if notification:
            await db.delete(notification)
            await db.commit()
            return True
        return False

    async def mark_all_as_read(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> int:
        """Отметить все непрочитанные уведомления как прочитанные"""
        from sqlalchemy import update
        
        result = await db.execute(
            update(InAppNotification)
            .where(
                and_(
                    InAppNotification.user_id == user_id,
                    InAppNotification.status == NotificationStatus.unread
                )
            )
            .values(
                status=NotificationStatus.read,
                read_at=datetime.now()
            )
        )
        await db.commit()
        return result.rowcount

    async def delete_all_read(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> int:
        """Удалить все прочитанные уведомления"""
        from sqlalchemy import delete
        
        result = await db.execute(
            delete(InAppNotification)
            .where(
                and_(
                    InAppNotification.user_id == user_id,
                    InAppNotification.status.in_([NotificationStatus.read, NotificationStatus.archived])
                )
            )
        )
        await db.commit()
        return result.rowcount

    async def get_notification_stats(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Dict[str, Any]:
        """Получить статистику уведомлений пользователя"""
        # Общее количество
        total_result = await db.execute(
            select(func.count(InAppNotification.id))
            .where(InAppNotification.user_id == user_id)
        )
        total_notifications = total_result.scalar()

        # Непрочитанные
        unread_result = await db.execute(
            select(func.count(InAppNotification.id))
            .where(
                and_(
                    InAppNotification.user_id == user_id,
                    InAppNotification.status == NotificationStatus.unread
                )
            )
        )
        unread_count = unread_result.scalar()

        # Архивированные
        archived_result = await db.execute(
            select(func.count(InAppNotification.id))
            .where(
                and_(
                    InAppNotification.user_id == user_id,
                    InAppNotification.status == NotificationStatus.archived
                )
            )
        )
        archived_count = archived_result.scalar()

        return {
            "total_notifications": total_notifications,
            "unread_count": unread_count,
            "read_count": total_notifications - unread_count - archived_count,
            "archived_count": archived_count
        }

    async def cleanup_expired_notifications(
        self, 
        db: AsyncSession
    ) -> int:
        """Очистить истекшие уведомления"""
        from sqlalchemy import delete
        
        current_time = datetime.now()
        result = await db.execute(
            delete(InAppNotification)
            .where(
                and_(
                    InAppNotification.expires_at.is_not(None),
                    InAppNotification.expires_at < current_time
                )
            )
        )
        await db.commit()
        return result.rowcount


class CRUDNotificationPreferences:
    """CRUD операции для настроек уведомлений"""

    async def get_user_preferences(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[NotificationPreferences]:
        """Получить настройки уведомлений пользователя"""
        result = await db.execute(
            select(NotificationPreferences)
            .where(NotificationPreferences.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update_preferences(
        self,
        db: AsyncSession,
        user_id: int,
        preferences_data: NotificationPreferencesUpdate
    ) -> NotificationPreferences:
        """Создать или обновить настройки уведомлений"""
        existing = await self.get_user_preferences(db, user_id)
        
        if existing:
            # Обновляем существующие настройки
            for field, value in preferences_data.dict(exclude_unset=True).items():
                setattr(existing, field, value)
            existing.updated_at = datetime.now()
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Создаем новые настройки
            new_preferences = NotificationPreferences(
                user_id=user_id,
                **preferences_data.dict(exclude_unset=True)
            )
            db.add(new_preferences)
            await db.commit()
            await db.refresh(new_preferences)
            return new_preferences


# Создаем экземпляры CRUD классов
notification_crud = CRUDNotification()
notification_preferences_crud = CRUDNotificationPreferences()


