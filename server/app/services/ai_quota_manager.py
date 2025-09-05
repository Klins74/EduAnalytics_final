"""
AI Quota Manager for controlling AI request usage by user role and time period.

Implements quotas, rate limiting, and usage tracking for AI services.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import asyncio

from app.core.config import settings
from app.models.user import UserRole
from app.services.redis_service import redis_client

logger = logging.getLogger(__name__)


class QuotaPeriod(Enum):
    """Time periods for quota enforcement."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class QuotaConfig:
    """Configuration for a specific quota."""
    requests_per_period: int
    tokens_per_period: Optional[int] = None
    period: QuotaPeriod = QuotaPeriod.DAY
    burst_allowance: int = 0  # Extra requests allowed in short bursts


@dataclass
class UsageStats:
    """Current usage statistics."""
    requests_used: int
    tokens_used: int
    period_start: datetime
    period_end: datetime
    remaining_requests: int
    remaining_tokens: Optional[int] = None


class AIQuotaManager:
    """Manager for AI service quotas and rate limiting."""
    
    def __init__(self):
        self.redis = redis_client
        self.quota_configs = self._load_quota_configs()
        
    def _load_quota_configs(self) -> Dict[UserRole, Dict[str, QuotaConfig]]:
        """Load quota configurations for different user roles and AI services."""
        return {
            UserRole.student: {
                "chat": QuotaConfig(
                    requests_per_period=50,
                    tokens_per_period=10000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=10
                ),
                "analytics": QuotaConfig(
                    requests_per_period=20,
                    tokens_per_period=5000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=5
                ),
                "recommendations": QuotaConfig(
                    requests_per_period=10,
                    tokens_per_period=2000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=2
                )
            },
            UserRole.teacher: {
                "chat": QuotaConfig(
                    requests_per_period=200,
                    tokens_per_period=50000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=50
                ),
                "analytics": QuotaConfig(
                    requests_per_period=100,
                    tokens_per_period=25000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=20
                ),
                "recommendations": QuotaConfig(
                    requests_per_period=50,
                    tokens_per_period=10000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=10
                ),
                "batch_analysis": QuotaConfig(
                    requests_per_period=20,
                    tokens_per_period=100000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=5
                )
            },
            UserRole.admin: {
                "chat": QuotaConfig(
                    requests_per_period=1000,
                    tokens_per_period=200000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=200
                ),
                "analytics": QuotaConfig(
                    requests_per_period=500,
                    tokens_per_period=100000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=100
                ),
                "recommendations": QuotaConfig(
                    requests_per_period=200,
                    tokens_per_period=50000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=50
                ),
                "batch_analysis": QuotaConfig(
                    requests_per_period=100,
                    tokens_per_period=500000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=20
                ),
                "system_maintenance": QuotaConfig(
                    requests_per_period=50,
                    tokens_per_period=100000,
                    period=QuotaPeriod.DAY,
                    burst_allowance=10
                )
            }
        }
    
    def _get_period_key(self, period: QuotaPeriod, timestamp: datetime) -> str:
        """Generate a key for the current time period."""
        if period == QuotaPeriod.HOUR:
            return timestamp.strftime("%Y-%m-%d-%H")
        elif period == QuotaPeriod.DAY:
            return timestamp.strftime("%Y-%m-%d")
        elif period == QuotaPeriod.WEEK:
            # Use ISO week number
            year, week, _ = timestamp.isocalendar()
            return f"{year}-W{week:02d}"
        elif period == QuotaPeriod.MONTH:
            return timestamp.strftime("%Y-%m")
        else:
            raise ValueError(f"Unsupported period: {period}")
    
    def _get_period_bounds(self, period: QuotaPeriod, timestamp: datetime) -> tuple[datetime, datetime]:
        """Get start and end times for the current period."""
        if period == QuotaPeriod.HOUR:
            start = timestamp.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        elif period == QuotaPeriod.DAY:
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == QuotaPeriod.WEEK:
            # Start of ISO week (Monday)
            days_since_monday = timestamp.weekday()
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
            end = start + timedelta(weeks=1)
        elif period == QuotaPeriod.MONTH:
            start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start.replace(month=start.month + 1) if start.month < 12 else start.replace(year=start.year + 1, month=1)
            end = next_month
        else:
            raise ValueError(f"Unsupported period: {period}")
        
        return start, end
    
    async def check_quota(
        self,
        user_id: int,
        user_role: UserRole,
        service: str,
        estimated_tokens: Optional[int] = None
    ) -> tuple[bool, Optional[UsageStats]]:
        """
        Check if user can make an AI request within their quota.
        
        Args:
            user_id: User ID
            user_role: User's role
            service: AI service name (chat, analytics, etc.)
            estimated_tokens: Estimated token usage for this request
            
        Returns:
            Tuple of (allowed, current_usage_stats)
        """
        try:
            # Get quota config for this role and service
            if user_role not in self.quota_configs:
                logger.warning(f"No quota config for role {user_role}")
                return False, None
            
            if service not in self.quota_configs[user_role]:
                logger.warning(f"No quota config for service {service} and role {user_role}")
                return False, None
            
            quota_config = self.quota_configs[user_role][service]
            now = datetime.utcnow()
            period_key = self._get_period_key(quota_config.period, now)
            
            # Redis keys for tracking usage
            requests_key = f"ai_quota:requests:{user_id}:{service}:{period_key}"
            tokens_key = f"ai_quota:tokens:{user_id}:{service}:{period_key}"
            burst_key = f"ai_quota:burst:{user_id}:{service}"
            
            # Get current usage
            pipe = self.redis.pipeline()
            pipe.get(requests_key)
            pipe.get(tokens_key)
            pipe.get(burst_key)
            results = await pipe.execute()
            
            current_requests = int(results[0] or 0)
            current_tokens = int(results[1] or 0)
            burst_used = int(results[2] or 0)
            
            # Calculate effective limits (including burst allowance)
            effective_request_limit = quota_config.requests_per_period + quota_config.burst_allowance
            effective_token_limit = (quota_config.tokens_per_period or 0) + (quota_config.burst_allowance * 100)  # Assume 100 tokens per burst request
            
            # Check request quota
            if current_requests >= effective_request_limit:
                logger.info(f"Request quota exceeded for user {user_id}, service {service}")
                return False, self._get_usage_stats(quota_config, now, current_requests, current_tokens)
            
            # Check token quota if specified
            if quota_config.tokens_per_period and estimated_tokens:
                if current_tokens + estimated_tokens > effective_token_limit:
                    logger.info(f"Token quota would be exceeded for user {user_id}, service {service}")
                    return False, self._get_usage_stats(quota_config, now, current_requests, current_tokens)
            
            return True, self._get_usage_stats(quota_config, now, current_requests, current_tokens)
            
        except Exception as e:
            logger.error(f"Error checking AI quota: {e}")
            # Fail open for availability, but log the error
            return True, None
    
    async def record_usage(
        self,
        user_id: int,
        user_role: UserRole,
        service: str,
        actual_tokens: Optional[int] = None,
        request_duration: Optional[float] = None
    ) -> bool:
        """
        Record actual usage after a successful AI request.
        
        Args:
            user_id: User ID
            user_role: User's role
            service: AI service name
            actual_tokens: Actual tokens used
            request_duration: Request duration in seconds
            
        Returns:
            True if usage recorded successfully
        """
        try:
            if user_role not in self.quota_configs:
                return False
            
            if service not in self.quota_configs[user_role]:
                return False
            
            quota_config = self.quota_configs[user_role][service]
            now = datetime.utcnow()
            period_key = self._get_period_key(quota_config.period, now)
            
            # Redis keys
            requests_key = f"ai_quota:requests:{user_id}:{service}:{period_key}"
            tokens_key = f"ai_quota:tokens:{user_id}:{service}:{period_key}"
            stats_key = f"ai_quota:stats:{user_id}:{service}:{period_key}"
            
            # Calculate TTL for the period
            _, period_end = self._get_period_bounds(quota_config.period, now)
            ttl = int((period_end - now).total_seconds())
            
            # Update usage counters
            pipe = self.redis.pipeline()
            pipe.incr(requests_key)
            pipe.expire(requests_key, ttl)
            
            if actual_tokens:
                pipe.incrby(tokens_key, actual_tokens)
                pipe.expire(tokens_key, ttl)
            
            # Store detailed stats
            stats = {
                "timestamp": now.isoformat(),
                "tokens": actual_tokens or 0,
                "duration": request_duration or 0,
                "service": service
            }
            pipe.lpush(stats_key, json.dumps(stats))
            pipe.ltrim(stats_key, 0, 99)  # Keep last 100 requests
            pipe.expire(stats_key, ttl)
            
            await pipe.execute()
            
            # Update burst usage if over normal quota
            normal_requests_key = f"ai_quota:requests:{user_id}:{service}:{period_key}"
            current_requests = int(await self.redis.get(normal_requests_key) or 0)
            
            if current_requests > quota_config.requests_per_period:
                burst_key = f"ai_quota:burst:{user_id}:{service}"
                burst_used = current_requests - quota_config.requests_per_period
                await self.redis.setex(burst_key, ttl, burst_used)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording AI usage: {e}")
            return False
    
    def _get_usage_stats(
        self,
        quota_config: QuotaConfig,
        current_time: datetime,
        current_requests: int,
        current_tokens: int
    ) -> UsageStats:
        """Generate usage statistics."""
        period_start, period_end = self._get_period_bounds(quota_config.period, current_time)
        
        return UsageStats(
            requests_used=current_requests,
            tokens_used=current_tokens,
            period_start=period_start,
            period_end=period_end,
            remaining_requests=max(0, quota_config.requests_per_period - current_requests),
            remaining_tokens=max(0, (quota_config.tokens_per_period or 0) - current_tokens) if quota_config.tokens_per_period else None
        )
    
    async def get_user_usage_stats(
        self,
        user_id: int,
        user_role: UserRole,
        services: Optional[List[str]] = None
    ) -> Dict[str, UsageStats]:
        """Get usage statistics for a user across all or specified services."""
        try:
            if user_role not in self.quota_configs:
                return {}
            
            if services is None:
                services = list(self.quota_configs[user_role].keys())
            
            stats = {}
            now = datetime.utcnow()
            
            for service in services:
                if service not in self.quota_configs[user_role]:
                    continue
                
                quota_config = self.quota_configs[user_role][service]
                period_key = self._get_period_key(quota_config.period, now)
                
                # Get current usage
                requests_key = f"ai_quota:requests:{user_id}:{service}:{period_key}"
                tokens_key = f"ai_quota:tokens:{user_id}:{service}:{period_key}"
                
                pipe = self.redis.pipeline()
                pipe.get(requests_key)
                pipe.get(tokens_key)
                results = await pipe.execute()
                
                current_requests = int(results[0] or 0)
                current_tokens = int(results[1] or 0)
                
                stats[service] = self._get_usage_stats(
                    quota_config, now, current_requests, current_tokens
                )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user usage stats: {e}")
            return {}
    
    async def reset_user_quota(
        self,
        user_id: int,
        user_role: UserRole,
        service: Optional[str] = None
    ) -> bool:
        """Reset quota for a user (admin function)."""
        try:
            if user_role not in self.quota_configs:
                return False
            
            services = [service] if service else list(self.quota_configs[user_role].keys())
            now = datetime.utcnow()
            
            keys_to_delete = []
            
            for svc in services:
                if svc not in self.quota_configs[user_role]:
                    continue
                
                quota_config = self.quota_configs[user_role][svc]
                period_key = self._get_period_key(quota_config.period, now)
                
                keys_to_delete.extend([
                    f"ai_quota:requests:{user_id}:{svc}:{period_key}",
                    f"ai_quota:tokens:{user_id}:{svc}:{period_key}",
                    f"ai_quota:stats:{user_id}:{svc}:{period_key}",
                    f"ai_quota:burst:{user_id}:{svc}"
                ])
            
            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
            
            logger.info(f"Reset quota for user {user_id}, services: {services}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting user quota: {e}")
            return False
    
    async def get_quota_config(self, user_role: UserRole) -> Dict[str, Dict[str, Any]]:
        """Get quota configuration for a user role."""
        if user_role not in self.quota_configs:
            return {}
        
        config = {}
        for service, quota_config in self.quota_configs[user_role].items():
            config[service] = {
                "requests_per_period": quota_config.requests_per_period,
                "tokens_per_period": quota_config.tokens_per_period,
                "period": quota_config.period.value,
                "burst_allowance": quota_config.burst_allowance
            }
        
        return config
    
    async def get_system_usage_stats(self) -> Dict[str, Any]:
        """Get system-wide usage statistics."""
        try:
            # This would typically aggregate usage across all users
            # For now, return basic system info
            stats = {
                "total_users_with_usage": 0,
                "total_requests_today": 0,
                "total_tokens_today": 0,
                "top_services": [],
                "quota_violations_today": 0
            }
            
            # Get all quota keys for today
            now = datetime.utcnow()
            today_key = now.strftime("%Y-%m-%d")
            
            # Scan for quota keys
            pattern = f"ai_quota:requests:*:*:{today_key}"
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            # Aggregate stats
            if keys:
                values = await self.redis.mget(keys)
                stats["total_requests_today"] = sum(int(v or 0) for v in values)
                stats["total_users_with_usage"] = len([v for v in values if int(v or 0) > 0])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system usage stats: {e}")
            return {}


# Global quota manager instance
ai_quota_manager = AIQuotaManager()
