from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone

from app.models.notification_log import NotificationLog, NotificationLogStatus


class CRUDNotificationLog:
    """CRUD операции для логов уведомлений"""

    async def create_log(
        self,
        db: AsyncSession,
        *,
        event_type: str,
        channel: str,
        priority: str = "normal",
        recipients_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationLog:
        """Создать запись в логе уведомлений"""
        log_entry = NotificationLog(
            event_type=event_type,
            channel=channel,
            priority=priority,
            recipients_count=recipients_count,
            metadata=metadata,
            status=NotificationLogStatus.pending
        )
        
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry

    async def update_log_success(
        self,
        db: AsyncSession,
        *,
        log_id: int,
        successful_count: int,
        processing_time_ms: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ) -> Optional[NotificationLog]:
        """Обновить лог при успешной отправке"""
        result = await db.execute(
            select(NotificationLog).filter(NotificationLog.id == log_id)
        )
        log_entry = result.scalar_one_or_none()
        
        if log_entry:
            log_entry.status = NotificationLogStatus.sent
            log_entry.successful_count = successful_count
            log_entry.failed_count = log_entry.recipients_count - successful_count
            log_entry.sent_at = datetime.now(timezone.utc)
            
            if processing_time_ms is not None:
                log_entry.processing_time_ms = processing_time_ms
            if response_data is not None:
                log_entry.response_data = response_data
            
            await db.commit()
            await db.refresh(log_entry)
        
        return log_entry

    async def update_log_failure(
        self,
        db: AsyncSession,
        *,
        log_id: int,
        error_message: str,
        failed_count: Optional[int] = None,
        processing_time_ms: Optional[int] = None
    ) -> Optional[NotificationLog]:
        """Обновить лог при неудачной отправке"""
        result = await db.execute(
            select(NotificationLog).filter(NotificationLog.id == log_id)
        )
        log_entry = result.scalar_one_or_none()
        
        if log_entry:
            log_entry.status = NotificationLogStatus.failed
            log_entry.error_message = error_message
            log_entry.failed_at = datetime.now(timezone.utc)
            
            if failed_count is not None:
                log_entry.failed_count = failed_count
                log_entry.successful_count = log_entry.recipients_count - failed_count
            else:
                log_entry.failed_count = log_entry.recipients_count
                log_entry.successful_count = 0
            
            if processing_time_ms is not None:
                log_entry.processing_time_ms = processing_time_ms
            
            await db.commit()
            await db.refresh(log_entry)
        
        return log_entry

    async def get_notification_stats(
        self,
        db: AsyncSession,
        *,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Получить статистику уведомлений за указанный период"""
        
        # Определяем временной диапазон
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        # Общая статистика
        total_result = await db.execute(
            select(
                func.count(NotificationLog.id).label('total_notifications'),
                func.sum(NotificationLog.recipients_count).label('total_recipients'),
                func.sum(NotificationLog.successful_count).label('total_successful'),
                func.sum(NotificationLog.failed_count).label('total_failed')
            )
            .filter(NotificationLog.created_at >= start_date)
        )
        totals = total_result.first()
        
        # Статистика по каналам
        channel_stats_result = await db.execute(
            select(
                NotificationLog.channel,
                func.count(NotificationLog.id).label('count'),
                func.sum(NotificationLog.successful_count).label('successful'),
                func.sum(NotificationLog.failed_count).label('failed')
            )
            .filter(NotificationLog.created_at >= start_date)
            .group_by(NotificationLog.channel)
        )
        channel_stats = {
            row.channel: {
                "sent": row.successful or 0,
                "failed": row.failed or 0,
                "total": row.count or 0
            }
            for row in channel_stats_result.all()
        }
        
        # Статистика по приоритетам
        priority_stats_result = await db.execute(
            select(
                NotificationLog.priority,
                func.count(NotificationLog.id).label('count')
            )
            .filter(NotificationLog.created_at >= start_date)
            .group_by(NotificationLog.priority)
        )
        priority_stats = {
            row.priority: row.count or 0
            for row in priority_stats_result.all()
        }
        
        # Статистика по типам событий
        event_stats_result = await db.execute(
            select(
                NotificationLog.event_type,
                func.count(NotificationLog.id).label('count')
            )
            .filter(NotificationLog.created_at >= start_date)
            .group_by(NotificationLog.event_type)
        )
        event_stats = {
            row.event_type: row.count or 0
            for row in event_stats_result.all()
        }
        
        # Статистика за последние 24 часа
        recent_date = end_date - timedelta(hours=24)
        recent_result = await db.execute(
            select(func.count(NotificationLog.id))
            .filter(NotificationLog.created_at >= recent_date)
        )
        recent_count = recent_result.scalar() or 0
        
        # Средняя скорость успеха
        success_rate = 0.0
        if totals.total_recipients and totals.total_recipients > 0:
            success_rate = (totals.total_successful / totals.total_recipients) * 100
        
        return {
            "total_sent": totals.total_successful or 0,
            "total_failed": totals.total_failed or 0,
            "total_notifications": totals.total_notifications or 0,
            "total_recipients": totals.total_recipients or 0,
            "success_rate": round(success_rate, 2),
            "by_channel": channel_stats,
            "by_priority": priority_stats,
            "by_event_type": event_stats,
            "recent_24h": recent_count,
            "period_days": days_back
        }

    async def get_recent_logs(
        self,
        db: AsyncSession,
        *,
        limit: int = 100,
        status: Optional[NotificationLogStatus] = None
    ) -> List[NotificationLog]:
        """Получить последние логи уведомлений"""
        query = select(NotificationLog).order_by(desc(NotificationLog.created_at))
        
        if status:
            query = query.filter(NotificationLog.status == status)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def cleanup_old_logs(
        self,
        db: AsyncSession,
        *,
        days_to_keep: int = 90
    ) -> int:
        """Очистить старые логи (старше указанного количества дней)"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        # Найти старые логи
        result = await db.execute(
            select(NotificationLog)
            .filter(NotificationLog.created_at < cutoff_date)
        )
        old_logs = result.scalars().all()
        
        # Удалить их
        deleted_count = 0
        for log in old_logs:
            await db.delete(log)
            deleted_count += 1
        
        await db.commit()
        return deleted_count

    async def get_performance_metrics(
        self,
        db: AsyncSession,
        *,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Получить метрики производительности"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Средняя скорость обработки
        avg_processing_result = await db.execute(
            select(func.avg(NotificationLog.processing_time_ms))
            .filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.processing_time_ms.is_not(None)
                )
            )
        )
        avg_processing_time = avg_processing_result.scalar() or 0
        
        # Количество повторных попыток
        retry_stats_result = await db.execute(
            select(
                func.sum(NotificationLog.retry_count).label('total_retries'),
                func.count(NotificationLog.id).label('total_notifications')
            )
            .filter(NotificationLog.created_at >= start_date)
        )
        retry_stats = retry_stats_result.first()
        
        return {
            "avg_processing_time_ms": round(avg_processing_time, 2),
            "total_retries": retry_stats.total_retries or 0,
            "retry_rate": round(
                (retry_stats.total_retries / retry_stats.total_notifications * 100) 
                if retry_stats.total_notifications > 0 else 0, 2
            )
        }


# Создаем экземпляр CRUD
notification_log_crud = CRUDNotificationLog()


