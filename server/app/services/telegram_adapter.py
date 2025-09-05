"""
Telegram notification adapter for EduAnalytics.

Provides Telegram Bot API integration for sending notifications via Telegram.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime

from app.core.config import settings
from app.middleware.observability import get_business_metrics

logger = logging.getLogger(__name__)


class TelegramAdapter:
    """Telegram Bot API adapter for sending notifications."""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.enabled = bool(self.bot_token)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.timeout = getattr(settings, 'TELEGRAM_TIMEOUT', 30)
        self.business_metrics = get_business_metrics()
        
        if not self.enabled:
            logger.warning("Telegram adapter disabled: TELEGRAM_BOT_TOKEN not configured")
    
    async def send_message(
        self, 
        chat_id: str, 
        message: str, 
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict] = None,
        disable_web_page_preview: bool = True
    ) -> bool:
        """
        Send a message to a Telegram chat.
        
        Args:
            chat_id: Telegram chat ID or username
            message: Message text
            parse_mode: Message formatting (HTML, Markdown, or None)
            reply_markup: Inline keyboard markup
            disable_web_page_preview: Disable link previews
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            logger.error("Cannot send Telegram message: adapter not configured")
            return False
        
        start_time = datetime.now()
        success = False
        
        try:
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_web_page_preview
            }
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.info(f"Telegram message sent successfully to {chat_id}")
                        success = True
                    else:
                        logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                else:
                    logger.error(f"Telegram HTTP error: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
        
        finally:
            # Track metrics
            duration = (datetime.now() - start_time).total_seconds()
            if self.business_metrics:
                self.business_metrics.track_notification_sent(
                    channel="telegram",
                    success=success,
                    notification_type="message"
                )
        
        return success
    
    async def send_document(
        self,
        chat_id: str,
        document: bytes,
        filename: str,
        caption: Optional[str] = None
    ) -> bool:
        """
        Send a document to a Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            document: Document bytes
            filename: File name
            caption: Optional caption
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            logger.error("Cannot send Telegram document: adapter not configured")
            return False
        
        start_time = datetime.now()
        success = False
        
        try:
            files = {
                "document": (filename, document)
            }
            
            data = {
                "chat_id": chat_id
            }
            
            if caption:
                data["caption"] = caption
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/sendDocument",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.info(f"Telegram document sent successfully to {chat_id}")
                        success = True
                    else:
                        logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                else:
                    logger.error(f"Telegram HTTP error: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Failed to send Telegram document: {str(e)}")
        
        finally:
            # Track metrics
            if self.business_metrics:
                self.business_metrics.track_notification_sent(
                    channel="telegram",
                    success=success,
                    notification_type="document"
                )
        
        return success
    
    async def send_photo(
        self,
        chat_id: str,
        photo: bytes,
        caption: Optional[str] = None
    ) -> bool:
        """
        Send a photo to a Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            photo: Photo bytes
            caption: Optional caption
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            logger.error("Cannot send Telegram photo: adapter not configured")
            return False
        
        try:
            files = {
                "photo": ("photo.jpg", photo)
            }
            
            data = {
                "chat_id": chat_id
            }
            
            if caption:
                data["caption"] = caption
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/sendPhoto",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.info(f"Telegram photo sent successfully to {chat_id}")
                        return True
                    else:
                        logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                else:
                    logger.error(f"Telegram HTTP error: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Failed to send Telegram photo: {str(e)}")
        
        return False
    
    async def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a chat.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Dict with chat information or None if failed
        """
        if not self.enabled:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/getChat",
                    params={"chat_id": chat_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        return result.get("result")
                    else:
                        logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                else:
                    logger.error(f"Telegram HTTP error: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Failed to get Telegram chat info: {str(e)}")
        
        return None
    
    async def validate_bot_token(self) -> bool:
        """
        Validate the bot token by getting bot information.
        
        Returns:
            bool: True if token is valid
        """
        if not self.enabled:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/getMe")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        bot_info = result.get("result", {})
                        logger.info(f"Telegram bot validated: {bot_info.get('username', 'Unknown')}")
                        return True
                    else:
                        logger.error(f"Telegram token validation failed: {result.get('description', 'Unknown error')}")
                else:
                    logger.error(f"Telegram HTTP error during validation: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to validate Telegram bot token: {str(e)}")
        
        return False
    
    def format_assignment_notification(
        self,
        assignment: Dict[str, Any],
        course: Dict[str, Any],
        user: Dict[str, Any],
        notification_type: str = "due_soon"
    ) -> str:
        """
        Format assignment notification for Telegram.
        
        Args:
            assignment: Assignment data
            course: Course data
            user: User data
            notification_type: Type of notification
            
        Returns:
            Formatted message string
        """
        if notification_type == "due_soon":
            emoji = "⏰"
            title = "Assignment Due Soon"
        elif notification_type == "overdue":
            emoji = "🚨"
            title = "Assignment Overdue"
        elif notification_type == "created":
            emoji = "📝"
            title = "New Assignment"
        else:
            emoji = "📚"
            title = "Assignment Update"
        
        message = f"{emoji} <b>{title}</b>\n\n"
        message += f"<b>Course:</b> {course.get('name', 'Unknown')}\n"
        message += f"<b>Assignment:</b> {assignment.get('title', 'Untitled')}\n"
        
        if assignment.get('due_date'):
            message += f"<b>Due Date:</b> {assignment['due_date']}\n"
        
        if assignment.get('points'):
            message += f"<b>Points:</b> {assignment['points']}\n"
        
        if assignment.get('description'):
            description = assignment['description'][:200]
            if len(assignment['description']) > 200:
                description += "..."
            message += f"\n<i>{description}</i>"
        
        return message
    
    def format_grade_notification(
        self,
        assignment: Dict[str, Any],
        grade: Dict[str, Any],
        course: Dict[str, Any],
        user: Dict[str, Any]
    ) -> str:
        """
        Format grade notification for Telegram.
        
        Args:
            assignment: Assignment data
            grade: Grade data
            course: Course data
            user: User data
            
        Returns:
            Formatted message string
        """
        score = grade.get('score', 0)
        max_score = assignment.get('points', 100)
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        if percentage >= 90:
            emoji = "🎉"
        elif percentage >= 80:
            emoji = "👍"
        elif percentage >= 70:
            emoji = "✅"
        elif percentage >= 60:
            emoji = "⚠️"
        else:
            emoji = "❌"
        
        message = f"{emoji} <b>Grade Posted</b>\n\n"
        message += f"<b>Course:</b> {course.get('name', 'Unknown')}\n"
        message += f"<b>Assignment:</b> {assignment.get('title', 'Untitled')}\n"
        message += f"<b>Your Grade:</b> {score}/{max_score} ({percentage:.1f}%)\n"
        
        if grade.get('feedback'):
            feedback = grade['feedback'][:300]
            if len(grade['feedback']) > 300:
                feedback += "..."
            message += f"\n<b>Feedback:</b>\n<i>{feedback}</i>"
        
        return message


class TelegramNotificationService:
    """High-level service for sending educational notifications via Telegram."""
    
    def __init__(self):
        self.adapter = TelegramAdapter()
    
    async def send_assignment_due_soon(
        self,
        user_telegram_id: str,
        assignment: Dict[str, Any],
        course: Dict[str, Any],
        user: Dict[str, Any],
        time_remaining: Optional[str] = None
    ) -> bool:
        """Send assignment due soon notification."""
        message = self.adapter.format_assignment_notification(
            assignment, course, user, "due_soon"
        )
        
        if time_remaining:
            message += f"\n\n⏱️ <b>Time Remaining:</b> {time_remaining}"
        
        # Add action buttons
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "View Assignment", "url": f"{settings.FRONTEND_URL}/assignments/{assignment.get('id')}"},
                    {"text": "Submit Work", "url": f"{settings.FRONTEND_URL}/assignments/{assignment.get('id')}/submit"}
                ]
            ]
        }
        
        return await self.adapter.send_message(
            chat_id=user_telegram_id,
            message=message,
            reply_markup=reply_markup
        )
    
    async def send_grade_posted(
        self,
        user_telegram_id: str,
        assignment: Dict[str, Any],
        grade: Dict[str, Any],
        course: Dict[str, Any],
        user: Dict[str, Any]
    ) -> bool:
        """Send grade posted notification."""
        message = self.adapter.format_grade_notification(
            assignment, grade, course, user
        )
        
        # Add action button
        reply_markup = {
            "inline_keyboard": [
                [{"text": "View Grade Details", "url": f"{settings.FRONTEND_URL}/grades/{grade.get('id')}"}]
            ]
        }
        
        return await self.adapter.send_message(
            chat_id=user_telegram_id,
            message=message,
            reply_markup=reply_markup
        )
    
    async def send_course_announcement(
        self,
        user_telegram_id: str,
        announcement: Dict[str, Any],
        course: Dict[str, Any],
        user: Dict[str, Any]
    ) -> bool:
        """Send course announcement notification."""
        message = f"📢 <b>Course Announcement</b>\n\n"
        message += f"<b>Course:</b> {course.get('name', 'Unknown')}\n"
        message += f"<b>Title:</b> {announcement.get('title', 'Untitled')}\n\n"
        
        content = announcement.get('content', '')[:500]
        if len(announcement.get('content', '')) > 500:
            content += "..."
        
        message += f"<i>{content}</i>"
        
        # Add action button
        reply_markup = {
            "inline_keyboard": [
                [{"text": "View Full Announcement", "url": f"{settings.FRONTEND_URL}/courses/{course.get('id')}/announcements"}]
            ]
        }
        
        return await self.adapter.send_message(
            chat_id=user_telegram_id,
            message=message,
            reply_markup=reply_markup
        )
    
    async def send_weekly_digest(
        self,
        user_telegram_id: str,
        digest_data: Dict[str, Any],
        user: Dict[str, Any]
    ) -> bool:
        """Send weekly academic digest."""
        message = f"📊 <b>Weekly Academic Summary</b>\n\n"
        message += f"Hello {user.get('first_name', user.get('username', 'Student'))}!\n\n"
        
        # Add summary statistics
        message += f"📝 <b>Assignments Completed:</b> {digest_data.get('assignments_completed', 0)}\n"
        message += f"⏳ <b>Assignments Pending:</b> {digest_data.get('assignments_pending', 0)}\n"
        message += f"📈 <b>Average Grade:</b> {digest_data.get('average_grade', 'N/A')}\n"
        message += f"🎓 <b>Active Courses:</b> {digest_data.get('courses_active', 0)}\n"
        
        # Add upcoming deadlines
        upcoming = digest_data.get('upcoming_deadlines', [])
        if upcoming:
            message += f"\n⚡ <b>Upcoming Deadlines:</b>\n"
            for deadline in upcoming[:3]:  # Show top 3
                message += f"• {deadline.get('title', 'Unknown')} - {deadline.get('due_date', 'No date')}\n"
        
        # Add action button
        reply_markup = {
            "inline_keyboard": [
                [{"text": "View Dashboard", "url": f"{settings.FRONTEND_URL}/dashboard"}]
            ]
        }
        
        return await self.adapter.send_message(
            chat_id=user_telegram_id,
            message=message,
            reply_markup=reply_markup
        )


# Global service instance
telegram_service = TelegramNotificationService()
