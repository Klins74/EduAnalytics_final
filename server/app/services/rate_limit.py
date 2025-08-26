from __future__ import annotations

import time
import redis.asyncio as redis
from fastapi import HTTPException, status

from app.core.config import settings


_redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


class RateLimiter:
    """Простой скользящий лимитер запросов на пользователя."""

    def __init__(self, window_seconds: int = 30, max_requests: int = 10) -> None:
        self.window_seconds = window_seconds
        self.max_requests = max_requests

    @staticmethod
    def _key(user_id: int) -> str:
        return f"ai:rate:{user_id}"

    async def check(self, user_id: int) -> None:
        now = int(time.time())
        key = self._key(user_id)
        # Удаляем старые отметки времени
        await _redis_client.zremrangebyscore(key, 0, now - self.window_seconds)
        # Количество оставшихся за окно
        count = await _redis_client.zcard(key)
        if count >= self.max_requests:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Слишком много запросов. Повторите позже.")
        # Добавляем текущий
        await _redis_client.zadd(key, {str(now): now})
        await _redis_client.expire(key, self.window_seconds)


