import asyncio
import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.services.canvas_auth import canvas_auth_service


class CanvasRateLimiter:
    def __init__(self, max_per_minute: int = 300) -> None:
        self.capacity = max_per_minute
        self.tokens = max_per_minute
        self.last_refill = time.time()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        # refill per second
        self.tokens = min(self.capacity, self.tokens + elapsed * (self.capacity / 60.0))
        self.last_refill = now

    async def acquire(self) -> None:
        while True:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return
            await asyncio.sleep(0.05)


class CanvasClient:
    def __init__(self) -> None:
        self.base_url: str = getattr(settings, 'CANVAS_BASE_URL', '').rstrip('/')
        self.rate_limiter = CanvasRateLimiter(max_per_minute=getattr(settings, 'CANVAS_RATE_LIMIT', 300))

    async def get_json(self, path: str, user_id: int, params: Optional[Dict[str, Any]] = None) -> dict | list[dict]:
        resp = await self._request('GET', path, user_id, params)
        return resp.json()

    async def _request(self, method: str, path: str, user_id: int, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        await self.rate_limiter.acquire()
        token = await canvas_auth_service.get_valid_access_token(user_id)
        if not token:
            raise PermissionError("Canvas access token missing for user")
        url = f"{self.base_url}{path}"
        attempts = 0
        backoff = 0.5
        while attempts < 4:
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.request(
                        method,
                        url,
                        params=params,
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Accept': 'application/json'
                        }
                    )
                    if resp.status_code in (429, 500, 502, 503, 504):
                        attempts += 1
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    resp.raise_for_status()
                    return resp
            except httpx.HTTPError:
                attempts += 1
                await asyncio.sleep(backoff)
                backoff *= 2
        raise RuntimeError(f"Canvas request failed after retries: {method} {path}")

    async def list_paginated(self, path: str, user_id: int, params: Optional[Dict[str, Any]] = None) -> list[dict]:
        params = dict(params or {})
        params.setdefault('per_page', 100)
        page = 1
        results: list[dict] = []
        while True:
            params['page'] = page
            resp = await self._request('GET', path, user_id, params)
            data = resp.json()
            if isinstance(data, list):
                results.extend(data)
            else:
                results.append(data)
            # pagination via Link header
            link = resp.headers.get('Link') or resp.headers.get('link')
            if link and 'rel="next"' in link:
                page += 1
                continue
            break
        return results

    async def list_since(self, path: str, user_id: int, since_iso: Optional[str]) -> list[dict]:
        params: Dict[str, Any] = {}
        if since_iso:
            params['search_term'] = None  # placeholder; some endpoints support 'updated_since'
            params['updated_since'] = since_iso
        return await self.list_paginated(path, user_id, params)


canvas_client = CanvasClient()


