import hashlib
import hmac
from typing import Any, Dict, Optional

import redis.asyncio as redis

from app.core.config import settings


class LiveEventsIngestService:
    def __init__(self) -> None:
        self.redis: redis.Redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.stream_key = getattr(settings, 'CANVAS_EVENTS_STREAM', 'canvas:events')
        self.dlq_key = getattr(settings, 'CANVAS_EVENTS_DLQ', 'canvas:events:dlq')
        self.maxlen = getattr(settings, 'CANVAS_EVENTS_STREAM_MAXLEN', 10000)
        self.secret = getattr(settings, 'CANVAS_LIVE_EVENTS_SECRET', '')

    def _verify_signature(self, body: bytes, signature: Optional[str], bearer: Optional[str], token_header: Optional[str]) -> bool:
        # Prefer HMAC-SHA256 signature if provided
        if signature and self.secret:
            sig = signature
            if sig.startswith('sha256='):
                sig = sig.split('=', 1)[1]
            digest = hmac.new(self.secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
            return hmac.compare_digest(digest, sig)
        # Fallback to Bearer or X-Canvas-Token check
        secret_ok = False
        if bearer and bearer.lower().startswith('bearer '):
            token = bearer.split(' ', 1)[1].strip()
            secret_ok = token and self.secret and token == self.secret
        if token_header:
            secret_ok = secret_ok or (self.secret and token_header == self.secret)
        return bool(secret_ok)

    async def ingest(self, body: bytes, headers: Dict[str, str]) -> bool:
        signature = headers.get('x-canvas-signature') or headers.get('x-signature')
        auth = headers.get('authorization')
        token_header = headers.get('x-canvas-token')
        verified = self._verify_signature(body, signature, auth, token_header)
        payload = {
            'payload': body.decode('utf-8', errors='replace'),
        }
        # Add some header context (trim long values)
        for hk in ('x-request-id', 'x-canvas-signature', 'x-canvas-event', 'x-canvas-shard'):
            if headers.get(hk):
                payload[hk] = headers[hk][:256]

        if verified:
            await self.redis.xadd(self.stream_key, payload, maxlen=self.maxlen, approximate=True)
            return True
        else:
            await self.redis.xadd(self.dlq_key, payload, maxlen=self.maxlen, approximate=True)
            return False


live_events_ingest = LiveEventsIngestService()


