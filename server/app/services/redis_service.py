"""
Simple Redis client wrapper providing an async interface used by services.

Falls back to creating a client from settings.REDIS_URL. Kept minimal for tests.
"""

from __future__ import annotations

import os
import redis.asyncio as redis
from app.core.config import settings


def _create_client() -> redis.Redis:
    url = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL", "redis://cache:6379/0")
    return redis.from_url(url)


# Export a shared async Redis client
redis_client: redis.Redis = _create_client()


