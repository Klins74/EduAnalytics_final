"""
Enhanced notification service with DLQ and idempotency support.

Provides unified interface for sending notifications through various channels
with reliability guarantees.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import jinja2
import json

from app.services.notification_dlq import (
    notification_dlq,
    notification_idempotency,
    NotificationMessage,
    NotificationStatus,
    RetryStrategy
)
from app.services.email_service import email_service
from app.services.sms_service import sms_service
from app.services.telegram_service import telegram_service
from app.services.in_app_notification_service import in_app_notification_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BULK = 5


@dataclass
class NotificationRequest:
    """Request for sending notification."""
    recipient_id: int
    channel: str
    recipient_address: str
    subject: Optional[str] = None
    body: str = ""
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    schedule_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    metadata: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None


class NotificationService:
    """Enhanced notification service with DLQ support."""
    
    def __init__(self):
        self.supported_channels = {
            "email", "sms", "telegram", "push", "in_app"
        }
        
        # Template environment
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("app/templates/notifications"),
            autoescape=True
        )
    
    async def send_notification(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send notification through appropriate channel with DLQ support."""
        try:
            # Validate request
            validation_error = self._validate_request(request)
            if validation_error:
                return {
                    "success": False,
                    "error": validation_error,
                    "message_id": None
                }
            
            # Generate message ID
            message_id = str(uuid.uuid4())
            
            # Generate idempotency key if not provided
            if not request.idempotency_key:
                content_hash = notification_idempotency.hash_content(
                    request.subject or "",
                    request.body,
                    request.template_data
                )
                request.idempotency_key = notification_idempotency.generate_idempotency_key(
                    request.recipient_id,
                    request.channel,
                    content_hash,
                    request.schedule_time
                )
            
            # Create notification message
            message = NotificationMessage(
                id=message_id,
                idempotency_key=request.idempotency_key,
                recipient_id=request.recipient_id,
                channel=request.channel,
                recipient_address=request.recipient_address,
                subject=request.subject,
                body=request.body,
                template_id=request.template_id,
                template_data=request.template_data,
                priority=request.priority.value,
                created_at=datetime.utcnow(),
                expires_at=request.expires_at,
                max_retries=request.max_retries,
                retry_strategy=request.retry_strategy,
                metadata=request.metadata
            )
            
            # If scheduled for future, handle accordingly
            if request.schedule_time and request.schedule_time > datetime.utcnow():
                return await self._schedule_notification(message, request.schedule_time)
            
            # Enqueue for immediate processing
            success = await notification_dlq.enqueue_notification(message)
            
            if success:
                logger.info(f"Notification enqueued successfully: {message_id}")
                return {
                    "success": True,
                    "message_id": message_id,
                    "idempotency_key": request.idempotency_key,
                    "status": "queued"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to enqueue notification",
                    "message_id": message_id
                }
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_id": None
            }
    
    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        recipient_id: Optional[int] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> Dict[str, Any]:
        """Send email notification."""
        request = NotificationRequest(
            recipient_id=recipient_id or 0,
            channel="email",
            recipient_address=recipient_email,
            subject=subject,
            body=body,
            priority=priority,
            **kwargs
        )
        
        return await self.send_notification(request)
    
    async def send_templated_email(
        self,
        recipient_email: str,
        template_id: str,
        template_data: Dict[str, Any],
        recipient_id: Optional[int] = None,
        subject_override: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> Dict[str, Any]:
        """Send templated email notification."""
        request = NotificationRequest(
            recipient_id=recipient_id or 0,
            channel="email",
            recipient_address=recipient_email,
            subject=subject_override,
            template_id=template_id,
            template_data=template_data,
            priority=priority,
            **kwargs
        )
        
        return await self.send_notification(request)
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        recipient_id: Optional[int] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> Dict[str, Any]:
        """Send SMS notification."""
        request = NotificationRequest(
            recipient_id=recipient_id or 0,
            channel="sms",
            recipient_address=phone_number,
            body=message,
            priority=priority,
            **kwargs
        )
        
        return await self.send_notification(request)
    
    async def send_telegram_message(
        self,
        chat_id: str,
        message: str,
        recipient_id: Optional[int] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> Dict[str, Any]:
        """Send Telegram notification."""
        request = NotificationRequest(
            recipient_id=recipient_id or 0,
            channel="telegram",
            recipient_address=chat_id,
            body=message,
            priority=priority,
            **kwargs
        )
        
        return await self.send_notification(request)
    
    async def create_in_app_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "general",
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create in-app notification."""
        request = NotificationRequest(
            recipient_id=user_id,
            channel="in_app",
            recipient_address=str(user_id),  # Use user_id as address
            subject=title,
            body=message,
            priority=priority,
            metadata={
                "notification_type": notification_type,
                **(metadata or {})
            },
            **kwargs
        )
        
        return await self.send_notification(request)
    
    async def send_bulk_notifications(
        self,
        notifications: List[NotificationRequest],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """Send bulk notifications efficiently."""
        try:
            results = {
                "total": len(notifications),
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            # Process in batches
            for i in range(0, len(notifications), batch_size):
                batch = notifications[i:i + batch_size]
                
                # Process batch concurrently
                tasks = [self.send_notification(notification) for notification in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        results["failed"] += 1
                        results["errors"].append({
                            "index": i + j,
                            "error": str(result)
                        })
                    elif result.get("success", False):
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append({
                            "index": i + j,
                            "error": result.get("error", "Unknown error")
                        })
            
            logger.info(f"Bulk notification results: {results['successful']}/{results['total']} successful")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk notification sending: {e}")
            return {
                "total": len(notifications),
                "successful": 0,
                "failed": len(notifications),
                "errors": [{"error": str(e)}]
            }
    
    async def get_notification_status(self, message_id: str) -> Dict[str, Any]:
        """Get status of a notification."""
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as db:
                query = """
                SELECT id, status, retry_count, last_error, created_at, updated_at
                FROM notification_log
                WHERE id = :message_id
                """
                
                result = await db.execute(text(query), {"message_id": message_id})
                notification = result.fetchone()
                
                if not notification:
                    return {"error": "Notification not found"}
                
                # Get delivery attempts
                attempts_query = """
                SELECT attempt_number, attempted_at, status, response_code, 
                       response_message, latency_ms, error_details
                FROM notification_delivery_attempts
                WHERE message_id = :message_id
                ORDER BY attempt_number
                """
                
                attempts_result = await db.execute(text(attempts_query), {"message_id": message_id})
                attempts = [dict(row._mapping) for row in attempts_result.fetchall()]
                
                return {
                    "id": notification.id,
                    "status": notification.status,
                    "retry_count": notification.retry_count,
                    "last_error": notification.last_error,
                    "created_at": notification.created_at.isoformat() if notification.created_at else None,
                    "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
                    "delivery_attempts": attempts
                }
                
        except Exception as e:
            logger.error(f"Error getting notification status: {e}")
            return {"error": str(e)}
    
    async def get_notification_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get notification delivery metrics."""
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as db:
                since_time = datetime.utcnow() - timedelta(hours=hours)
                
                # Overall stats
                stats_query = """
                SELECT 
                    status,
                    channel,
                    COUNT(*) as count,
                    AVG(retry_count) as avg_retries
                FROM notification_log
                WHERE created_at >= :since_time
                GROUP BY status, channel
                ORDER BY channel, status
                """
                
                result = await db.execute(text(stats_query), {"since_time": since_time})
                stats = [dict(row._mapping) for row in result.fetchall()]
                
                # Delivery performance
                perf_query = """
                SELECT 
                    AVG(latency_ms) as avg_latency,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as median_latency,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
                    COUNT(*) as total_attempts
                FROM notification_delivery_attempts
                WHERE attempted_at >= :since_time
                AND latency_ms IS NOT NULL
                """
                
                perf_result = await db.execute(text(perf_query), {"since_time": since_time})
                performance = dict(perf_result.fetchone()._mapping)
                
                # Queue stats
                queue_stats = await notification_dlq.get_queue_stats()
                
                return {
                    "period_hours": hours,
                    "statistics": stats,
                    "performance": performance,
                    "queue_stats": queue_stats
                }
                
        except Exception as e:
            logger.error(f"Error getting notification metrics: {e}")
            return {"error": str(e)}
    
    async def _schedule_notification(self, message: NotificationMessage, schedule_time: datetime) -> Dict[str, Any]:
        """Schedule notification for future delivery."""
        try:
            # For now, use Redis sorted set for scheduled notifications
            # In production, you might want to use a more robust scheduler
            from app.services.redis_service import redis_service
            
            client = redis_service.get_client()
            
            message_data = json.dumps({
                "message": message.__dict__,
                "schedule_time": schedule_time.isoformat()
            }, default=str)
            
            await client.zadd(
                "notifications:scheduled",
                {message_data: schedule_time.timestamp()}
            )
            
            logger.info(f"Notification scheduled for {schedule_time}: {message.id}")
            
            return {
                "success": True,
                "message_id": message.id,
                "idempotency_key": message.idempotency_key,
                "status": "scheduled",
                "scheduled_for": schedule_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling notification: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_id": message.id
            }
    
    def _validate_request(self, request: NotificationRequest) -> Optional[str]:
        """Validate notification request."""
        if not request.channel:
            return "Channel is required"
        
        if request.channel not in self.supported_channels:
            return f"Unsupported channel: {request.channel}"
        
        if not request.recipient_address:
            return "Recipient address is required"
        
        if not request.body and not request.template_id:
            return "Either body or template_id is required"
        
        if request.expires_at and request.expires_at <= datetime.utcnow():
            return "Expiration time must be in the future"
        
        return None


# Global service instance
notification_service = NotificationService()
