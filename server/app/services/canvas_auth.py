import os
import time
from typing import Optional

import httpx
import redis.asyncio as redis

from app.core.config import settings


class CanvasAuthService:
    """OAuth2 for Canvas with token storage in Redis per user.

    Stores: access_token, refresh_token, expires_at (epoch seconds)
    Keys: canvas:oauth:user:{user_id}
    """

    def __init__(self) -> None:
        self.base_url: str = getattr(settings, 'CANVAS_BASE_URL', '').rstrip('/')
        self.client_id: str = getattr(settings, 'CANVAS_CLIENT_ID', '')
        self.client_secret: str = getattr(settings, 'CANVAS_CLIENT_SECRET', '')
        self.redirect_uri: str = getattr(settings, 'CANVAS_REDIRECT_URI', '')
        self.redis: redis.Redis = redis.from_url(getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)

    def authorize_url(self, state: str) -> str:
        return (
            f"{self.base_url}/login/oauth2/auth?client_id={self.client_id}"
            f"&response_type=code&redirect_uri={httpx.QueryParams({'redirect_uri': self.redirect_uri})['redirect_uri']}"
            f"&state={state}"
        )

    async def exchange_code(self, code: str) -> dict:
        token_url = f"{self.base_url}/login/oauth2/token"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                token_url,
                data={
                    'grant_type': 'authorization_code',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': self.redirect_uri,
                    'code': code,
                },
                headers={'Accept': 'application/json'},
            )
            resp.raise_for_status()
            return resp.json()

    async def refresh_token(self, refresh_token: str) -> dict:
        token_url = f"{self.base_url}/login/oauth2/token"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                token_url,
                data={
                    'grant_type': 'refresh_token',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'refresh_token': refresh_token,
                },
                headers={'Accept': 'application/json'},
            )
            resp.raise_for_status()
            return resp.json()

    async def save_tokens(self, user_id: int, tokens: dict) -> None:
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in') or tokens.get('expires') or 3600
        expires_at = int(time.time()) + int(expires_in)
        key = f"canvas:oauth:user:{user_id}"
        payload = {
            'access_token': access_token or '',
            'refresh_token': refresh_token or '',
            'expires_at': str(expires_at),
        }
        await self.redis.hset(key, mapping=payload)
        await self.redis.expire(key, max(24 * 3600, int(expires_in)))

    async def get_valid_access_token(self, user_id: int) -> Optional[str]:
        key = f"canvas:oauth:user:{user_id}"
        data = await self.redis.hgetall(key)
        if not data:
            return None
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        expires_at = int(data.get('expires_at') or 0)
        now = int(time.time())
        if access_token and now < expires_at - 60:
            return access_token
        if refresh_token:
            tokens = await self.refresh_token(refresh_token)
            await self.save_tokens(user_id, tokens)
            return tokens.get('access_token')
        return None


canvas_auth_service = CanvasAuthService()


