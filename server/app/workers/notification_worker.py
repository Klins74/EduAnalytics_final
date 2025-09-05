"""
Notification processing worker with DLQ and retry logic.

Handles the asynchronous processing of notifications from queues.
"""

import logging
import asyncio
import signal
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

from app.services.notification_dlq import (
    notification_dlq,
    NotificationMessage,
    NotificationStatus,
    RetryStrategy
)
from app.services.notification_service import notification_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationWorker:
    """Worker for processing notification queues."""
    
    def __init__(self, worker_id: str = "default"):
        self.worker_id = worker_id
        self.running = False
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "retried": 0,
            "started_at": None
        }
        
        # Processing configuration
        self.batch_size = 10
        self.poll_interval = 5  # seconds
        self.max_processing_time = 300  # 5 minutes per message
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Worker {self.worker_id} received signal {signum}, shutting down...")
        self.running = False
    
    async def start(self):
        """Start the notification worker."""
        logger.info(f"Starting notification worker {self.worker_id}")
        self.running = True
        self.stats["started_at"] = datetime.utcnow()
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._process_notifications()),
            asyncio.create_task(self._process_delayed_retries()),
            asyncio.create_task(self._cleanup_expired()),
            asyncio.create_task(self._report_stats())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Worker {self.worker_id} error: {e}")
        finally:
            logger.info(f"Worker {self.worker_id} stopped")
    
    async def _process_notifications(self):
        """Main notification processing loop."""
        logger.info(f"Worker {self.worker_id} started processing notifications")
        
        while self.running:
            try:
                # Process a batch of notifications
                processed_count = 0
                
                for _ in range(self.batch_size):
                    if not self.running:
                        break
                    
                    # Dequeue notification
                    message = await notification_dlq.dequeue_notification(timeout=1)
                    if not message:
                        break
                    
                    # Process the notification
                    await self._process_single_notification(message)
                    processed_count += 1
                
                if processed_count == 0:
                    # No messages processed, wait before next poll
                    await asyncio.sleep(self.poll_interval)
                    
            except Exception as e:
                logger.error(f"Error in notification processing loop: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def _process_single_notification(self, message: NotificationMessage):
        """Process a single notification message."""
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Processing notification {message.id} (attempt {message.retry_count + 1})")
            
            # Check if message has expired
            if message.expires_at and datetime.utcnow() > message.expires_at:
                logger.warning(f"Notification {message.id} has expired")
                await notification_dlq.mark_failure(
                    message,
                    "Message expired",
                    should_retry=False
                )
                self.stats["failed"] += 1
                return
            
            # Process with timeout
            try:
                success = await asyncio.wait_for(
                    self._deliver_notification(message),
                    timeout=self.max_processing_time
                )
                
                if success:
                    # Calculate delivery time
                    delivery_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    await notification_dlq.mark_success(message, {
                        "latency_ms": int(delivery_time),
                        "worker_id": self.worker_id
                    })
                    
                    self.stats["successful"] += 1
                    logger.info(f"Notification {message.id} delivered successfully")
                else:
                    await notification_dlq.mark_failure(
                        message,
                        "Delivery failed - unknown error",
                        should_retry=True
                    )
                    self.stats["failed"] += 1
                    
            except asyncio.TimeoutError:
                await notification_dlq.mark_failure(
                    message,
                    f"Processing timeout after {self.max_processing_time}s",
                    should_retry=True
                )
                self.stats["failed"] += 1
                logger.error(f"Notification {message.id} processing timed out")
                
        except Exception as e:
            await notification_dlq.mark_failure(
                message,
                f"Processing error: {str(e)}",
                should_retry=True
            )
            self.stats["failed"] += 1
            logger.error(f"Error processing notification {message.id}: {e}")
        
        finally:
            self.stats["processed"] += 1
    
    async def _deliver_notification(self, message: NotificationMessage) -> bool:
        """Deliver notification using appropriate channel."""
        try:
            if message.channel == "email":
                return await self._deliver_email(message)
            elif message.channel == "sms":
                return await self._deliver_sms(message)
            elif message.channel == "telegram":
                return await self._deliver_telegram(message)
            elif message.channel == "push":
                return await self._deliver_push(message)
            elif message.channel == "in_app":
                return await self._deliver_in_app(message)
            else:
                logger.error(f"Unknown notification channel: {message.channel}")
                return False
                
        except Exception as e:
            logger.error(f"Delivery error for {message.id}: {e}")
            raise
    
    async def _deliver_email(self, message: NotificationMessage) -> bool:
        """Deliver email notification."""
        try:
            if message.template_id:
                # Use template
                success = await notification_service.send_templated_email(
                    recipient_email=message.recipient_address,
                    template_id=message.template_id,
                    template_data=message.template_data or {},
                    subject_override=message.subject
                )
            else:
                # Direct email
                success = await notification_service.send_email(
                    recipient_email=message.recipient_address,
                    subject=message.subject or "Notification",
                    body=message.body,
                    is_html=True
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Email delivery error for {message.id}: {e}")
            raise
    
    async def _deliver_sms(self, message: NotificationMessage) -> bool:
        """Deliver SMS notification."""
        try:
            success = await notification_service.send_sms(
                phone_number=message.recipient_address,
                message=message.body
            )
            return success
            
        except Exception as e:
            logger.error(f"SMS delivery error for {message.id}: {e}")
            raise
    
    async def _deliver_telegram(self, message: NotificationMessage) -> bool:
        """Deliver Telegram notification."""
        try:
            # For Telegram, recipient_address should be chat_id
            success = await notification_service.send_telegram_message(
                chat_id=message.recipient_address,
                message=message.body
            )
            return success
            
        except Exception as e:
            logger.error(f"Telegram delivery error for {message.id}: {e}")
            raise
    
    async def _deliver_push(self, message: NotificationMessage) -> bool:
        """Deliver push notification."""
        try:
            # Push notification implementation would go here
            # For now, simulate success
            logger.info(f"Push notification simulated for {message.id}")
            return True
            
        except Exception as e:
            logger.error(f"Push delivery error for {message.id}: {e}")
            raise
    
    async def _deliver_in_app(self, message: NotificationMessage) -> bool:
        """Deliver in-app notification."""
        try:
            success = await notification_service.create_in_app_notification(
                user_id=message.recipient_id,
                title=message.subject or "Notification",
                message=message.body,
                notification_type="general",
                metadata=message.metadata
            )
            return success
            
        except Exception as e:
            logger.error(f"In-app delivery error for {message.id}: {e}")
            raise
    
    async def _process_delayed_retries(self):
        """Process delayed retry queue."""
        logger.info(f"Worker {self.worker_id} started delayed retry processor")
        
        while self.running:
            try:
                await notification_dlq.process_delayed_retries()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error processing delayed retries: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _cleanup_expired(self):
        """Clean up expired notifications and tracking data."""
        logger.info(f"Worker {self.worker_id} started cleanup processor")
        
        while self.running:
            try:
                # Clean up expired idempotency keys
                await notification_dlq.idempotency_service.cleanup_expired()
                
                # Clean up old notification records (keep for 30 days)
                await self._cleanup_old_records()
                
                # Sleep for 1 hour between cleanups
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in cleanup process: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_old_records(self):
        """Clean up old notification records from database."""
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as db:
                # Delete old notification logs (keep for 30 days)
                cleanup_date = datetime.utcnow() - timedelta(days=30)
                
                # Delete delivery attempts first (foreign key constraint)
                delete_attempts_sql = """
                DELETE FROM notification_delivery_attempts 
                WHERE message_id IN (
                    SELECT id FROM notification_log 
                    WHERE created_at < :cleanup_date
                    AND status IN ('sent', 'expired', 'poisoned')
                )
                """
                
                result = await db.execute(text(delete_attempts_sql), {"cleanup_date": cleanup_date})
                attempts_deleted = result.rowcount
                
                # Delete notification logs
                delete_logs_sql = """
                DELETE FROM notification_log 
                WHERE created_at < :cleanup_date
                AND status IN ('sent', 'expired', 'poisoned')
                """
                
                result = await db.execute(text(delete_logs_sql), {"cleanup_date": cleanup_date})
                logs_deleted = result.rowcount
                
                await db.commit()
                
                if logs_deleted > 0 or attempts_deleted > 0:
                    logger.info(f"Cleaned up {logs_deleted} notification logs and {attempts_deleted} delivery attempts")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
    
    async def _report_stats(self):
        """Report worker statistics periodically."""
        while self.running:
            try:
                await asyncio.sleep(300)  # Report every 5 minutes
                
                if self.stats["processed"] > 0:
                    uptime = datetime.utcnow() - self.stats["started_at"]
                    success_rate = (self.stats["successful"] / self.stats["processed"]) * 100
                    
                    logger.info(
                        f"Worker {self.worker_id} stats: "
                        f"processed={self.stats['processed']}, "
                        f"successful={self.stats['successful']}, "
                        f"failed={self.stats['failed']}, "
                        f"success_rate={success_rate:.1f}%, "
                        f"uptime={uptime}"
                    )
                
            except Exception as e:
                logger.error(f"Error reporting stats: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get current worker statistics."""
        uptime = None
        if self.stats["started_at"]:
            uptime = (datetime.utcnow() - self.stats["started_at"]).total_seconds()
        
        success_rate = 0
        if self.stats["processed"] > 0:
            success_rate = (self.stats["successful"] / self.stats["processed"]) * 100
        
        return {
            "worker_id": self.worker_id,
            "running": self.running,
            "uptime_seconds": uptime,
            "processed": self.stats["processed"],
            "successful": self.stats["successful"],
            "failed": self.stats["failed"],
            "retried": self.stats["retried"],
            "success_rate": round(success_rate, 2),
            "queue_stats": await notification_dlq.get_queue_stats()
        }


async def main():
    """Main worker entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Notification Worker')
    parser.add_argument('--worker-id', default='default', help='Worker ID')
    parser.add_argument('--log-level', default='INFO', help='Log level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start worker
    worker = NotificationWorker(worker_id=args.worker_id)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
