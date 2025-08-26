from __future__ import annotations

import json
from typing import List, Dict, Any

import redis.asyncio as redis

from app.core.config import settings


_redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


class ChatMemoryRepository:
    """Хранение истории диалога в Redis по пользователю."""

    def __init__(self, max_messages_per_user: int = 50) -> None:
        self.max_messages_per_user = max_messages_per_user

    @staticmethod
    def _history_key(user_id: int) -> str:
        return f"ai:history:{user_id}"

    async def append_message(self, user_id: int, role: str, content: str) -> None:
        message_entry = {"role": role, "content": content}
        key = self._history_key(user_id)
        await _redis_client.rpush(key, json.dumps(message_entry, ensure_ascii=False))
        # Обрезаем историю до лимита
        await _redis_client.ltrim(key, -self.max_messages_per_user, -1)

    async def get_recent_messages(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        key = self._history_key(user_id)
        raw_items = await _redis_client.lrange(key, -limit, -1)
        messages: List[Dict[str, Any]] = []
        for raw in raw_items:
            try:
                messages.append(json.loads(raw))
            except Exception:
                continue
        return messages

    async def clear(self, user_id: int) -> None:
        await _redis_client.delete(self._history_key(user_id))


def build_history_stub(messages: List[Dict[str, Any]], max_chars: int = 1000) -> str:
    """Готовит компактный текст истории для промпта с ограничением длины."""
    parts: List[str] = []
    for m in messages:
        role = m.get("role", "user")
        content = str(m.get("content", "")).replace("\n", " ")
        parts.append(f"{role}: {content}")
    text = "\n".join(parts)
    if len(text) > max_chars:
        return text[-max_chars:]
    return text


