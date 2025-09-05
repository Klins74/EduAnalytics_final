import asyncio
import json
from typing import Any, Dict

import redis.asyncio as redis

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.crud.canvas_sync import canvas_sync_crud


class LiveEventsWorker:
    def __init__(self) -> None:
        self.redis: redis.Redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.stream_key = getattr(settings, 'CANVAS_EVENTS_STREAM', 'canvas:events')
        self.group = f"{self.stream_key}:group"
        self.consumer = getattr(settings, 'HOSTNAME', 'worker')

    async def ensure_group(self) -> None:
        try:
            await self.redis.xgroup_create(name=self.stream_key, groupname=self.group, id='0', mkstream=True)
        except Exception:
            # group may already exist
            pass

    async def handle_event(self, fields: Dict[str, str]) -> None:
        payload = fields.get('payload')
        try:
            data = json.loads(payload) if payload else {}
        except Exception:
            data = {"raw": payload}
        # placeholder: persist processing stats
        async with AsyncSessionLocal() as db:
            state = await canvas_sync_crud.get_or_create(db, scope='live_events')
            extra = dict(state.extra or {})
            extra['processed'] = int(extra.get('processed', 0)) + 1
            await canvas_sync_crud.update(db, scope='live_events', extra=extra)

    async def run(self) -> None:
        await self.ensure_group()
        while True:
            try:
                msgs = await self.redis.xreadgroup(self.group, self.consumer, streams={self.stream_key: '>'}, count=10, latest_ids=None, block=5000)
                if not msgs:
                    continue
                for _, entries in msgs:
                    for message_id, fields in entries:
                        try:
                            await self.handle_event(fields)
                            await self.redis.xack(self.stream_key, self.group, message_id)
                        except Exception:
                            # leave in pending or move to DLQ in future
                            await self.redis.xack(self.stream_key, self.group, message_id)
            except Exception:
                await asyncio.sleep(1.0)


live_events_worker = LiveEventsWorker()


