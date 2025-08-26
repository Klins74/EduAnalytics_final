import asyncio
import pytest
from httpx import AsyncClient

from main import app


@pytest.mark.asyncio
async def test_ai_chat_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/api/ai/chat", json={"message": "hi"})
        assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_ai_chat_ok_with_token(monkeypatch):
    # Получаем токен через реальный эндпоинт
    async with AsyncClient(app=app, base_url="http://test") as ac:
        token_resp = await ac.post("/api/auth/token", data={"username": "admin@example.com", "password": "admin"})
        assert token_resp.status_code == 200
        token = token_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        r = await ac.post("/api/ai/chat", headers=headers, json={"message": "Короткий анализ курса #1", "scope": "analytics", "course_id": 1})
        assert r.status_code == 200
        data = r.json()
        assert "reply" in data


@pytest.mark.asyncio
async def test_ai_stream_ok(monkeypatch):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        token_resp = await ac.post("/api/auth/token", data={"username": "admin@example.com", "password": "admin"})
        assert token_resp.status_code == 200
        token = token_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        r = await ac.post("/api/ai/chat/stream", headers=headers, json={"message": "Длинный запрос " + ("x"*200), "scope": "analytics", "course_id": 1})
        assert r.status_code == 200
        # Проверяем, что это sse-подобный текст
        body = r.text
        assert "data:" in body



