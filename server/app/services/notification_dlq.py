"""
Dead Letter Queue and Idempotency service for notifications.

Handles failed notification delivery, retry logic, and ensures idempotent processing.
"""

import logging
import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
import redis.asyncio as redis

from app.db.session import AsyncSessionLocal
from app.core.config import settings
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class NotificationStatus(Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    EXPIRED = "expired"
    POISONED = "poisoned"  # Too many failures, moved to poison queue


class RetryStrategy(Enum):
    """Retry strategy types."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    IMMEDIATE = "immediate"


@dataclass
class NotificationMessage:
    """Notification message with delivery metadata."""
    id: str
    idempotency_key: str
    recipient_id: int
    channel: str  # email, sms, telegram, push, etc.
    recipient_address: str
    subject: Optional[str]
    body: str
    template_id: Optional[str]
    template_data: Optional[Dict[str, Any]]
    priority: int  # 1=highest, 5=lowest
    created_at: datetime
    expires_at: Optional[datetime]
    retry_count: int = 0
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    status: NotificationStatus = NotificationStatus.PENDING
    last_error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DeliveryAttempt:
    """Delivery attempt record."""
    attempt_id: str
    message_id: str
    attempt_number: int
    attempted_at: datetime
    status: NotificationStatus
    response_code: Optional[str]
    response_message: Optional[str]
    latency_ms: Optional[int]
    error_details: Optional[str]


class NotificationIdempotencyService:
    """Handles idempotency for notification processing."""
    
    def __init__(self):
        self.redis_client = redis_service.get_client()
        self.idempotency_ttl = 3600 * 24  # 24 hours
    
    def generate_idempotency_key(
        self, 
        recipient_id: int, 
        channel: str, 
        content_hash: str,
        scheduled_time: Optional[datetime] = None
    ) -> str:
        """Generate idempotency key for notification."""
        components = [
            str(recipient_id),
            channel,
            content_hash
        ]
        
        if scheduled_time:
            # Include hour-level granularity for scheduled notifications
            components.append(scheduled_time.strftime("%Y%m%d%H"))
        
        key_data = ":".join(components)
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def hash_content(self, subject: str, body: str, template_data: Optional[Dict] = None) -> str:
        """Create hash of notification content."""
        content = {
            "subject": subject or "",
            "body": body,
            "template_data": template_data or {}
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    async def check_duplicate(self, idempotency_key: str) -> Optional[str]:
        """Check if notification with this idempotency key was already processed."""
        try:
            result = await self.redis_client.get(f"notification:idempotency:{idempotency_key}")
            return result.decode() if result else None
        except Exception as e:
            logger.error(f"Error checking idempotency: {e}")
            return None
    
    async def mark_processed(self, idempotency_key: str, message_id: str, status: NotificationStatus):
        """Mark notification as processed with given status."""
        try:
            data = {
                "message_id": message_id,
                "status": status.value,
                "processed_at": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.setex(
                f"notification:idempotency:{idempotency_key}",
                self.idempotency_ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Error marking notification as processed: {e}")
    
    async def cleanup_expired(self):
        """Clean up expired idempotency keys (handled by Redis TTL)."""
        # Redis automatically handles TTL, but we can scan for manual cleanup if needed
        pass


class NotificationDLQService:
    """Dead Letter Queue service for failed notifications."""
    
    def __init__(self):
        self.redis_client = redis_service.get_client()
        self.idempotency_service = NotificationIdempotencyService()
        
        # Queue names
        self.main_queue = "notifications:main"
        self.retry_queue = "notifications:retry"
        self.dlq_queue = "notifications:dlq"
        self.poison_queue = "notifications:poison"
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delays = {
            RetryStrategy.EXPONENTIAL_BACKOFF: [60, 300, 900],  # 1min, 5min, 15min
            RetryStrategy.LINEAR_BACKOFF: [120, 240, 360],      # 2min, 4min, 6min
            RetryStrategy.FIXED_INTERVAL: [300, 300, 300],      # 5min each
            RetryStrategy.IMMEDIATE: [0, 0, 0]                  # No delay
        }
    
    async def enqueue_notification(self, message: NotificationMessage) -> bool:
        """Enqueue notification for processing."""
        try:
            # Check idempotency
            existing = await self.idempotency_service.check_duplicate(message.idempotency_key)
            if existing:
                logger.info(f"Duplicate notification blocked: {message.idempotency_key}")
                return False
            
            # Add to main queue
            message_data = json.dumps(asdict(message), default=str)
            await self.redis_client.lpush(self.main_queue, message_data)
            
            # Track in database
            await self._store_notification_record(message)
            
            logger.info(f"Notification enqueued: {message.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueuing notification {message.id}: {e}")
            return False
    
    async def dequeue_notification(self, timeout: int = 10) -> Optional[NotificationMessage]:
        """Dequeue notification for processing."""
        try:
            # Try main queue first, then retry queue
            for queue in [self.main_queue, self.retry_queue]:
                result = await self.redis_client.brpop(queue, timeout)
                if result:
                    _, message_data = result
                    message_dict = json.loads(message_data.decode())
                    
                    # Reconstruct datetime objects
                    message_dict['created_at'] = datetime.fromisoformat(message_dict['created_at'])
                    if message_dict.get('expires_at'):
                        message_dict['expires_at'] = datetime.fromisoformat(message_dict['expires_at'])
                    
                    # Reconstruct enums
                    message_dict['status'] = NotificationStatus(message_dict['status'])
                    message_dict['retry_strategy'] = RetryStrategy(message_dict['retry_strategy'])
                    
                    return NotificationMessage(**message_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error dequeuing notification: {e}")
            return None
    
    async def mark_success(self, message: NotificationMessage, response_data: Optional[Dict] = None):
        """Mark notification as successfully delivered."""
        try:
            # Update idempotency tracking
            await self.idempotency_service.mark_processed(
                message.idempotency_key,
                message.id,
                NotificationStatus.SENT
            )
            
            # Record delivery attempt
            attempt = DeliveryAttempt(
                attempt_id=str(uuid.uuid4()),
                message_id=message.id,
                attempt_number=message.retry_count + 1,
                attempted_at=datetime.utcnow(),
                status=NotificationStatus.SENT,
                response_code=response_data.get('code') if response_data else None,
                response_message=response_data.get('message') if response_data else None,
                latency_ms=response_data.get('latency_ms') if response_data else None,
                error_details=None
            )
            
            await self._store_delivery_attempt(attempt)
            await self._update_notification_status(message.id, NotificationStatus.SENT)
            
            logger.info(f"Notification delivered successfully: {message.id}")
            
        except Exception as e:
            logger.error(f"Error marking notification success {message.id}: {e}")
    
    async def mark_failure(
        self, 
        message: NotificationMessage, 
        error: str, 
        should_retry: bool = True,
        response_data: Optional[Dict] = None
    ):
        """Mark notification as failed and handle retry logic."""
        try:
            message.retry_count += 1
            message.last_error = error
            
            # Record delivery attempt
            attempt = DeliveryAttempt(
                attempt_id=str(uuid.uuid4()),
                message_id=message.id,
                attempt_number=message.retry_count,
                attempted_at=datetime.utcnow(),
                status=NotificationStatus.FAILED,
                response_code=response_data.get('code') if response_data else None,
                response_message=response_data.get('message') if response_data else None,
                latency_ms=response_data.get('latency_ms') if response_data else None,
                error_details=error
            )
            
            await self._store_delivery_attempt(attempt)
            
            # Determine next action based on retry policy
            if not should_retry or message.retry_count >= message.max_retries:
                # Move to DLQ or poison queue
                if message.retry_count >= message.max_retries * 2:  # Poison threshold
                    await self._move_to_poison_queue(message)
                    message.status = NotificationStatus.POISONED
                else:
                    await self._move_to_dlq(message)
                    message.status = NotificationStatus.EXPIRED
                
                # Mark as failed in idempotency tracking
                await self.idempotency_service.mark_processed(
                    message.idempotency_key,
                    message.id,
                    message.status
                )
            else:
                # Schedule retry
                await self._schedule_retry(message)
                message.status = NotificationStatus.RETRYING
            
            await self._update_notification_status(message.id, message.status, error)
            
            logger.warning(f"Notification failed: {message.id}, retry: {message.retry_count}/{message.max_retries}")
            
        except Exception as e:
            logger.error(f"Error marking notification failure {message.id}: {e}")
    
    async def _schedule_retry(self, message: NotificationMessage):
        """Schedule notification for retry with appropriate delay."""
        try:
            # Calculate delay based on retry strategy
            delays = self.retry_delays.get(message.retry_strategy, self.retry_delays[RetryStrategy.EXPONENTIAL_BACKOFF])
            
            if message.retry_count <= len(delays):
                delay_seconds = delays[message.retry_count - 1]
            else:
                # Use last delay for additional retries
                delay_seconds = delays[-1]
            
            # Schedule retry
            if delay_seconds > 0:
                retry_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
                
                # Use Redis sorted set for delayed processing
                message_data = json.dumps(asdict(message), default=str)
                await self.redis_client.zadd(
                    f"{self.retry_queue}:delayed",
                    {message_data: retry_time.timestamp()}
                )
            else:
                # Immediate retry - add back to retry queue
                message_data = json.dumps(asdict(message), default=str)
                await self.redis_client.lpush(self.retry_queue, message_data)
            
        except Exception as e:
            logger.error(f"Error scheduling retry for {message.id}: {e}")
    
    async def _move_to_dlq(self, message: NotificationMessage):
        """Move failed notification to dead letter queue."""
        try:
            message_data = json.dumps(asdict(message), default=str)
            await self.redis_client.lpush(self.dlq_queue, message_data)
            logger.warning(f"Notification moved to DLQ: {message.id}")
        except Exception as e:
            logger.error(f"Error moving notification to DLQ {message.id}: {e}")
    
    async def _move_to_poison_queue(self, message: NotificationMessage):
        """Move repeatedly failed notification to poison queue."""
        try:
            message_data = json.dumps(asdict(message), default=str)
            await self.redis_client.lpush(self.poison_queue, message_data)
            logger.error(f"Notification moved to poison queue: {message.id}")
        except Exception as e:
            logger.error(f"Error moving notification to poison queue {message.id}: {e}")
    
    async def process_delayed_retries(self):
        """Process notifications that are ready for retry."""
        try:
            current_time = datetime.utcnow().timestamp()
            
            # Get messages ready for retry
            messages = await self.redis_client.zrangebyscore(
                f"{self.retry_queue}:delayed",
                0,
                current_time,
                withscores=True
            )
            
            for message_data, score in messages:
                try:
                    # Move to retry queue
                    await self.redis_client.lpush(self.retry_queue, message_data)
                    
                    # Remove from delayed queue
                    await self.redis_client.zrem(f"{self.retry_queue}:delayed", message_data)
                    
                except Exception as e:
                    logger.error(f"Error processing delayed retry: {e}")
            
            if messages:
                logger.info(f"Processed {len(messages)} delayed retries")
                
        except Exception as e:
            logger.error(f"Error processing delayed retries: {e}")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics for all notification queues."""
        try:
            stats = {}
            
            # Queue lengths
            stats['main_queue'] = await self.redis_client.llen(self.main_queue)
            stats['retry_queue'] = await self.redis_client.llen(self.retry_queue)
            stats['dlq_queue'] = await self.redis_client.llen(self.dlq_queue)
            stats['poison_queue'] = await self.redis_client.llen(self.poison_queue)
            stats['delayed_retries'] = await self.redis_client.zcard(f"{self.retry_queue}:delayed")
            
            # Database stats
            async with AsyncSessionLocal() as db:
                # Recent notification counts by status
                stats_query = """
                SELECT status, COUNT(*) as count
                FROM notification_log
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY status
                """
                
                result = await db.execute(text(stats_query))
                stats['recent_by_status'] = {row.status: row.count for row in result.fetchall()}
                
                # Success rate
                total_recent = sum(stats['recent_by_status'].values())
                success_count = stats['recent_by_status'].get('sent', 0)
                stats['success_rate'] = (success_count / total_recent * 100) if total_recent > 0 else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}
    
    async def requeue_dlq_messages(self, limit: int = 100) -> int:
        """Requeue messages from DLQ for retry."""
        try:
            requeued = 0
            
            for _ in range(limit):
                result = await self.redis_client.rpop(self.dlq_queue)
                if not result:
                    break
                
                # Reset retry count and add back to main queue
                message_dict = json.loads(result.decode())
                message_dict['retry_count'] = 0
                message_dict['status'] = NotificationStatus.PENDING.value
                message_dict['last_error'] = None
                
                message_data = json.dumps(message_dict)
                await self.redis_client.lpush(self.main_queue, message_data)
                requeued += 1
            
            logger.info(f"Requeued {requeued} messages from DLQ")
            return requeued
            
        except Exception as e:
            logger.error(f"Error requeuing DLQ messages: {e}")
            return 0
    
    async def _store_notification_record(self, message: NotificationMessage):
        """Store notification record in database."""
        try:
            async with AsyncSessionLocal() as db:
                insert_sql = """
                INSERT INTO notification_log (
                    id, idempotency_key, recipient_id, channel, recipient_address,
                    subject, body, template_id, template_data, priority,
                    created_at, expires_at, retry_count, max_retries,
                    retry_strategy, status, metadata
                ) VALUES (
                    :id, :idempotency_key, :recipient_id, :channel, :recipient_address,
                    :subject, :body, :template_id, :template_data, :priority,
                    :created_at, :expires_at, :retry_count, :max_retries,
                    :retry_strategy, :status, :metadata
                ) ON CONFLICT (id) DO UPDATE SET
                    retry_count = EXCLUDED.retry_count,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                """
                
                await db.execute(text(insert_sql), {
                    "id": message.id,
                    "idempotency_key": message.idempotency_key,
                    "recipient_id": message.recipient_id,
                    "channel": message.channel,
                    "recipient_address": message.recipient_address,
                    "subject": message.subject,
                    "body": message.body,
                    "template_id": message.template_id,
                    "template_data": json.dumps(message.template_data) if message.template_data else None,
                    "priority": message.priority,
                    "created_at": message.created_at,
                    "expires_at": message.expires_at,
                    "retry_count": message.retry_count,
                    "max_retries": message.max_retries,
                    "retry_strategy": message.retry_strategy.value,
                    "status": message.status.value,
                    "metadata": json.dumps(message.metadata) if message.metadata else None
                })
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error storing notification record {message.id}: {e}")
    
    async def _store_delivery_attempt(self, attempt: DeliveryAttempt):
        """Store delivery attempt record in database."""
        try:
            async with AsyncSessionLocal() as db:
                insert_sql = """
                INSERT INTO notification_delivery_attempts (
                    attempt_id, message_id, attempt_number, attempted_at,
                    status, response_code, response_message, latency_ms, error_details
                ) VALUES (
                    :attempt_id, :message_id, :attempt_number, :attempted_at,
                    :status, :response_code, :response_message, :latency_ms, :error_details
                )
                """
                
                await db.execute(text(insert_sql), {
                    "attempt_id": attempt.attempt_id,
                    "message_id": attempt.message_id,
                    "attempt_number": attempt.attempt_number,
                    "attempted_at": attempt.attempted_at,
                    "status": attempt.status.value,
                    "response_code": attempt.response_code,
                    "response_message": attempt.response_message,
                    "latency_ms": attempt.latency_ms,
                    "error_details": attempt.error_details
                })
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error storing delivery attempt {attempt.attempt_id}: {e}")
    
    async def _update_notification_status(self, message_id: str, status: NotificationStatus, error: Optional[str] = None):
        """Update notification status in database."""
        try:
            async with AsyncSessionLocal() as db:
                update_sql = """
                UPDATE notification_log 
                SET status = :status, last_error = :error, updated_at = NOW()
                WHERE id = :message_id
                """
                
                await db.execute(text(update_sql), {
                    "message_id": message_id,
                    "status": status.value,
                    "error": error
                })
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error updating notification status {message_id}: {e}")


# Global instances
notification_dlq = NotificationDLQService()
notification_idempotency = NotificationIdempotencyService()
