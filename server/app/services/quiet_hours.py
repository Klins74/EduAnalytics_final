"""
Quiet hours service for managing notification timing and user preferences.
"""

import logging
from datetime import datetime, time, timedelta
from typing import Optional, List, Dict, Any
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user_preferences import UserPreferences
from app.models.user import User

logger = logging.getLogger(__name__)


class QuietHoursService:
    """Service for managing quiet hours and notification timing."""
    
    def __init__(self):
        self.default_quiet_start = time(22, 0)  # 10:00 PM
        self.default_quiet_end = time(8, 0)     # 8:00 AM
        self.default_timezone = "UTC"
    
    async def is_quiet_time(
        self, 
        user_id: int, 
        db: AsyncSession,
        check_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if it's currently quiet time for a user.
        
        Args:
            user_id: User ID to check
            db: Database session
            check_time: Time to check (defaults to now)
            
        Returns:
            bool: True if it's quiet time
        """
        try:
            # Get user preferences
            result = await db.execute(
                select(UserPreferences).where(UserPreferences.user_id == user_id)
            )
            preferences = result.scalar_one_or_none()
            
            if not preferences or not preferences.quiet_hours_enabled:
                return False
            
            # Use current time if not specified
            if check_time is None:
                check_time = datetime.utcnow()
            
            # Convert to user's timezone
            user_timezone = preferences.quiet_hours_timezone or self.default_timezone
            try:
                tz = pytz.timezone(user_timezone)
                local_time = check_time.replace(tzinfo=pytz.UTC).astimezone(tz)
            except Exception as e:
                logger.warning(f"Invalid timezone {user_timezone}, using UTC: {e}")
                local_time = check_time
            
            # Check if current day is included in quiet hours
            if preferences.quiet_hours_days:
                current_weekday = local_time.weekday()  # 0=Monday, 6=Sunday
                if current_weekday not in preferences.quiet_hours_days:
                    return False
            
            # Check time range
            current_time = local_time.time()
            start_time = preferences.quiet_hours_start or self.default_quiet_start
            end_time = preferences.quiet_hours_end or self.default_quiet_end
            
            # Handle overnight quiet hours (e.g., 22:00 to 08:00)
            if start_time > end_time:
                return current_time >= start_time or current_time <= end_time
            else:
                return start_time <= current_time <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet time for user {user_id}: {e}")
            return False
    
    async def get_next_allowed_time(
        self, 
        user_id: int, 
        db: AsyncSession,
        from_time: Optional[datetime] = None
    ) -> datetime:
        """
        Get the next time when notifications are allowed for a user.
        
        Args:
            user_id: User ID
            db: Database session
            from_time: Starting time (defaults to now)
            
        Returns:
            datetime: Next allowed notification time
        """
        if from_time is None:
            from_time = datetime.utcnow()
        
        # Check if quiet hours are enabled
        if not await self.is_quiet_time(user_id, db, from_time):
            return from_time
        
        try:
            # Get user preferences
            result = await db.execute(
                select(UserPreferences).where(UserPreferences.user_id == user_id)
            )
            preferences = result.scalar_one_or_none()
            
            if not preferences:
                return from_time
            
            # Convert to user's timezone
            user_timezone = preferences.quiet_hours_timezone or self.default_timezone
            try:
                tz = pytz.timezone(user_timezone)
                local_time = from_time.replace(tzinfo=pytz.UTC).astimezone(tz)
            except Exception:
                local_time = from_time
            
            # Get quiet hours settings
            start_time = preferences.quiet_hours_start or self.default_quiet_start
            end_time = preferences.quiet_hours_end or self.default_quiet_end
            
            # Calculate next allowed time
            if start_time > end_time:
                # Overnight quiet hours
                if local_time.time() >= start_time:
                    # Currently in evening quiet period, wait until end_time next day
                    next_day = local_time.date() + timedelta(days=1)
                    next_allowed = datetime.combine(next_day, end_time)
                else:
                    # Currently in morning quiet period, wait until end_time today
                    next_allowed = datetime.combine(local_time.date(), end_time)
            else:
                # Same-day quiet hours
                if local_time.time() < end_time:
                    # Still in quiet period, wait until end_time today
                    next_allowed = datetime.combine(local_time.date(), end_time)
                else:
                    # After quiet period, next restriction starts at start_time
                    next_day = local_time.date() + timedelta(days=1)
                    next_allowed = datetime.combine(next_day, end_time)
            
            # Convert back to UTC
            try:
                next_allowed_utc = tz.localize(next_allowed).astimezone(pytz.UTC)
                return next_allowed_utc.replace(tzinfo=None)
            except Exception:
                return next_allowed
                
        except Exception as e:
            logger.error(f"Error calculating next allowed time for user {user_id}: {e}")
            return from_time
    
    async def bulk_filter_users_by_quiet_hours(
        self, 
        user_ids: List[int], 
        db: AsyncSession,
        check_time: Optional[datetime] = None
    ) -> Dict[str, List[int]]:
        """
        Filter users by quiet hours status.
        
        Args:
            user_ids: List of user IDs to check
            db: Database session
            check_time: Time to check (defaults to now)
            
        Returns:
            Dict with 'allowed' and 'quiet' lists of user IDs
        """
        if check_time is None:
            check_time = datetime.utcnow()
        
        allowed_users = []
        quiet_users = []
        
        try:
            # Get all preferences in one query
            result = await db.execute(
                select(UserPreferences).where(UserPreferences.user_id.in_(user_ids))
            )
            preferences_map = {pref.user_id: pref for pref in result.scalars().all()}
            
            for user_id in user_ids:
                preferences = preferences_map.get(user_id)
                
                if not preferences or not preferences.quiet_hours_enabled:
                    allowed_users.append(user_id)
                    continue
                
                # Check if in quiet hours
                is_quiet = await self._check_quiet_hours_for_preferences(
                    preferences, check_time
                )
                
                if is_quiet:
                    quiet_users.append(user_id)
                else:
                    allowed_users.append(user_id)
                    
        except Exception as e:
            logger.error(f"Error bulk filtering users by quiet hours: {e}")
            # Default to allowing all users if error
            allowed_users = user_ids
        
        return {
            "allowed": allowed_users,
            "quiet": quiet_users
        }
    
    def _check_quiet_hours_for_preferences(
        self, 
        preferences: UserPreferences, 
        check_time: datetime
    ) -> bool:
        """Helper method to check quiet hours for given preferences."""
        try:
            # Convert to user's timezone
            user_timezone = preferences.quiet_hours_timezone or self.default_timezone
            try:
                tz = pytz.timezone(user_timezone)
                local_time = check_time.replace(tzinfo=pytz.UTC).astimezone(tz)
            except Exception:
                local_time = check_time
            
            # Check if current day is included
            if preferences.quiet_hours_days:
                current_weekday = local_time.weekday()
                if current_weekday not in preferences.quiet_hours_days:
                    return False
            
            # Check time range
            current_time = local_time.time()
            start_time = preferences.quiet_hours_start or self.default_quiet_start
            end_time = preferences.quiet_hours_end or self.default_quiet_end
            
            if start_time > end_time:
                return current_time >= start_time or current_time <= end_time
            else:
                return start_time <= current_time <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet hours for preferences: {e}")
            return False
    
    async def get_user_notification_windows(
        self, 
        user_id: int, 
        db: AsyncSession,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming notification windows for a user.
        
        Args:
            user_id: User ID
            db: Database session
            days_ahead: Number of days to look ahead
            
        Returns:
            List of notification windows
        """
        try:
            result = await db.execute(
                select(UserPreferences).where(UserPreferences.user_id == user_id)
            )
            preferences = result.scalar_one_or_none()
            
            if not preferences or not preferences.quiet_hours_enabled:
                return [{
                    "start": datetime.utcnow(),
                    "end": datetime.utcnow() + timedelta(days=days_ahead),
                    "type": "always_available"
                }]
            
            windows = []
            current_date = datetime.utcnow().date()
            
            for day_offset in range(days_ahead):
                check_date = current_date + timedelta(days=day_offset)
                weekday = check_date.weekday()
                
                # Skip if day is in quiet hours
                if preferences.quiet_hours_days and weekday in preferences.quiet_hours_days:
                    continue
                
                # Calculate available window for this day
                start_time = preferences.quiet_hours_end or self.default_quiet_end
                end_time = preferences.quiet_hours_start or self.default_quiet_start
                
                if start_time < end_time:
                    # Normal day window
                    window_start = datetime.combine(check_date, start_time)
                    window_end = datetime.combine(check_date, end_time)
                    
                    windows.append({
                        "start": window_start,
                        "end": window_end,
                        "type": "daily_window",
                        "duration_hours": (window_end - window_start).total_seconds() / 3600
                    })
            
            return windows
            
        except Exception as e:
            logger.error(f"Error getting notification windows for user {user_id}: {e}")
            return []


# Global service instance
quiet_hours_service = QuietHoursService()
