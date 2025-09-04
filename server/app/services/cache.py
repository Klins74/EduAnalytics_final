import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings


logger = logging.getLogger(__name__)


class AnalyticsCache:
    def __init__(self) -> None:
        self._client: redis.Redis = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        # Default TTLs (seconds)
        self.ttl_short = 60  # very dynamic endpoints
        self.ttl_medium = 300  # common analytics
        self.ttl_long = 900  # heavy analytics

    async def get_json(self, key: str) -> Optional[Any]:
        try:
            raw = await self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning(f"Cache get failed for {key}: {exc}")
            return None

    async def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        try:
            await self._client.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ex or self.ttl_medium)
        except Exception as exc:
            logger.warning(f"Cache set failed for {key}: {exc}")

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys by pattern using SCAN to avoid blocking Redis."""
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await self._client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    deleted += await self._client.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except Exception as exc:
            logger.warning(f"Cache delete_pattern failed for {pattern}: {exc}")
            return 0

    # Invalidation helpers
    async def invalidate_course(self, course_id: int) -> None:
        prefix = f"analytics:course:{course_id}:*"
        await self.delete_pattern(prefix)

    async def invalidate_student(self, student_id: int) -> None:
        prefix = f"analytics:student:{student_id}:*"
        await self.delete_pattern(prefix)


analytics_cache = AnalyticsCache()


