"""
User preferences model for notification settings and quiet hours.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class UserPreferences(Base):
    """User preferences for notifications, quiet hours, and other settings."""
    
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Email notification preferences
    email_notifications_enabled = Column(Boolean, default=True)
    email_assignment_reminders = Column(Boolean, default=True)
    email_grade_notifications = Column(Boolean, default=True)
    email_course_announcements = Column(Boolean, default=True)
    email_weekly_digest = Column(Boolean, default=True)
    email_system_notifications = Column(Boolean, default=True)
    
    # SMS notification preferences
    sms_notifications_enabled = Column(Boolean, default=False)
    sms_phone_number = Column(String(20), nullable=True)
    sms_phone_verified = Column(Boolean, default=False)
    sms_urgent_only = Column(Boolean, default=True)
    sms_assignment_due_soon = Column(Boolean, default=False)
    sms_grade_notifications = Column(Boolean, default=False)
    
    # Telegram notification preferences
    telegram_notifications_enabled = Column(Boolean, default=False)
    telegram_chat_id = Column(String(100), nullable=True)
    telegram_username = Column(String(100), nullable=True)
    telegram_verified = Column(Boolean, default=False)
    telegram_assignment_reminders = Column(Boolean, default=False)
    telegram_grade_notifications = Column(Boolean, default=False)
    telegram_course_announcements = Column(Boolean, default=False)
    telegram_weekly_digest = Column(Boolean, default=False)
    
    # Push notification preferences
    push_notifications_enabled = Column(Boolean, default=True)
    push_assignment_reminders = Column(Boolean, default=True)
    push_grade_notifications = Column(Boolean, default=True)
    push_course_announcements = Column(Boolean, default=True)
    
    # Quiet hours settings
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(Time, nullable=True)  # e.g., 22:00
    quiet_hours_end = Column(Time, nullable=True)    # e.g., 08:00
    quiet_hours_timezone = Column(String(50), default="UTC")
    quiet_hours_days = Column(JSON, nullable=True)   # e.g., [0,1,2,3,4,5,6] for all days
    
    # Reminder timing preferences
    assignment_reminder_days = Column(JSON, default=[7, 3, 1])  # Days before due date
    deadline_reminder_time = Column(Time, nullable=True)  # Preferred time for reminders
    
    # Language and locale preferences
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    
    # Frequency preferences
    digest_frequency = Column(String(20), default="weekly")  # daily, weekly, monthly
    reminder_frequency = Column(String(20), default="normal")  # minimal, normal, frequent
    
    # Notification channels priority
    preferred_channel = Column(String(20), default="email")  # email, sms, telegram, push
    fallback_channel = Column(String(20), default="email")
    
    # Opt-out settings
    opted_out_all = Column(Boolean, default=False)
    opted_out_marketing = Column(Boolean, default=False)
    opt_out_reason = Column(Text, nullable=True)
    opted_out_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, email={self.email_notifications_enabled})>"
    
    def to_dict(self):
        """Convert preferences to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email_notifications_enabled": self.email_notifications_enabled,
            "email_assignment_reminders": self.email_assignment_reminders,
            "email_grade_notifications": self.email_grade_notifications,
            "email_course_announcements": self.email_course_announcements,
            "email_weekly_digest": self.email_weekly_digest,
            "email_system_notifications": self.email_system_notifications,
            "sms_notifications_enabled": self.sms_notifications_enabled,
            "sms_phone_number": self.sms_phone_number,
            "sms_phone_verified": self.sms_phone_verified,
            "sms_urgent_only": self.sms_urgent_only,
            "sms_assignment_due_soon": self.sms_assignment_due_soon,
            "sms_grade_notifications": self.sms_grade_notifications,
            "telegram_notifications_enabled": self.telegram_notifications_enabled,
            "telegram_chat_id": self.telegram_chat_id,
            "telegram_username": self.telegram_username,
            "telegram_verified": self.telegram_verified,
            "telegram_assignment_reminders": self.telegram_assignment_reminders,
            "telegram_grade_notifications": self.telegram_grade_notifications,
            "telegram_course_announcements": self.telegram_course_announcements,
            "telegram_weekly_digest": self.telegram_weekly_digest,
            "push_notifications_enabled": self.push_notifications_enabled,
            "push_assignment_reminders": self.push_assignment_reminders,
            "push_grade_notifications": self.push_grade_notifications,
            "push_course_announcements": self.push_course_announcements,
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "quiet_hours_start": self.quiet_hours_start.strftime("%H:%M") if self.quiet_hours_start else None,
            "quiet_hours_end": self.quiet_hours_end.strftime("%H:%M") if self.quiet_hours_end else None,
            "quiet_hours_timezone": self.quiet_hours_timezone,
            "quiet_hours_days": self.quiet_hours_days,
            "assignment_reminder_days": self.assignment_reminder_days,
            "deadline_reminder_time": self.deadline_reminder_time.strftime("%H:%M") if self.deadline_reminder_time else None,
            "preferred_language": self.preferred_language,
            "timezone": self.timezone,
            "digest_frequency": self.digest_frequency,
            "reminder_frequency": self.reminder_frequency,
            "preferred_channel": self.preferred_channel,
            "fallback_channel": self.fallback_channel,
            "opted_out_all": self.opted_out_all,
            "opted_out_marketing": self.opted_out_marketing,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def is_notification_allowed(self, notification_type: str, channel: str) -> bool:
        """
        Check if a specific notification type is allowed for a channel.
        
        Args:
            notification_type: Type of notification (assignment_reminder, grade_posted, etc.)
            channel: Notification channel (email, sms, telegram, push)
            
        Returns:
            bool: True if notification is allowed
        """
        # Check global opt-out
        if self.opted_out_all:
            return False
        
        # Check channel-specific enabled status
        if channel == "email" and not self.email_notifications_enabled:
            return False
        elif channel == "sms" and not self.sms_notifications_enabled:
            return False
        elif channel == "telegram" and not self.telegram_notifications_enabled:
            return False
        elif channel == "push" and not self.push_notifications_enabled:
            return False
        
        # Check notification type specific settings
        if notification_type == "assignment_reminder":
            if channel == "email":
                return self.email_assignment_reminders
            elif channel == "sms":
                return self.sms_assignment_due_soon
            elif channel == "telegram":
                return self.telegram_assignment_reminders
            elif channel == "push":
                return self.push_assignment_reminders
        
        elif notification_type == "grade_posted":
            if channel == "email":
                return self.email_grade_notifications
            elif channel == "sms":
                return self.sms_grade_notifications
            elif channel == "telegram":
                return self.telegram_grade_notifications
            elif channel == "push":
                return self.push_grade_notifications
        
        elif notification_type == "course_announcement":
            if channel == "email":
                return self.email_course_announcements
            elif channel == "sms":
                return False  # SMS typically not used for announcements
            elif channel == "telegram":
                return self.telegram_course_announcements
            elif channel == "push":
                return self.push_course_announcements
        
        elif notification_type == "weekly_digest":
            if channel == "email":
                return self.email_weekly_digest
            elif channel == "telegram":
                return self.telegram_weekly_digest
            else:
                return False  # Digest typically only via email/telegram
        
        elif notification_type == "system_notification":
            if channel == "email":
                return self.email_system_notifications
            else:
                return True  # System notifications generally allowed
        
        # Default: allow if channel is enabled
        return True
    
    def is_in_quiet_hours(self, current_time=None) -> bool:
        """
        Check if current time is within quiet hours.
        
        Args:
            current_time: datetime object (defaults to now in user's timezone)
            
        Returns:
            bool: True if in quiet hours
        """
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        if current_time is None:
            from datetime import datetime
            import pytz
            
            try:
                user_tz = pytz.timezone(self.quiet_hours_timezone)
                current_time = datetime.now(user_tz).time()
            except:
                # Fallback to UTC
                current_time = datetime.utcnow().time()
        else:
            current_time = current_time.time()
        
        start_time = self.quiet_hours_start
        end_time = self.quiet_hours_end
        
        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start_time > end_time:
            return current_time >= start_time or current_time <= end_time
        else:
            return start_time <= current_time <= end_time
