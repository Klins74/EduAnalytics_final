import asyncio
import time
from typing import Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.core.config import settings


class RateLimiter:
    def __init__(self, redis_url: str, prefix: str = "ratelimit:") -> None:
        self.client: redis.Redis = redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix

    def _key(self, bucket: str, identifier: str) -> str:
        return f"{self.prefix}{bucket}:{identifier}"

    async def check(self, bucket: str, identifier: str, limit: int, window_seconds: int) -> None:
        """Fixed window counter using Redis INCR + EXPIRE.
        Raises HTTP 429 if limit exceeded.
        """
        key = self._key(bucket, identifier)
        try:
            # increment
            current = await self.client.incr(key)
            if current == 1:
                await self.client.expire(key, window_seconds)
            if current > limit:
                ttl = await self.client.ttl(key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": "Too many requests",
                        "retry_after": max(ttl, 1) if ttl and ttl > 0 else window_seconds,
                    },
                )
        except HTTPException:
            raise
        except Exception:
            # Fail-open on Redis errors
            return


rate_limiter = RateLimiter(settings.REDIS_URL)


def limit(bucket: str, limit: int, window_seconds: int):
    async def dependency(request: Request):
        # Identify by IP for unauth endpoints; honor X-Forwarded-For if present
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        identifier = client_ip
        await rate_limiter.check(bucket=bucket, identifier=identifier, limit=limit, window_seconds=window_seconds)
    return dependency


