from typing import Optional, AsyncGenerator
import json
import httpx
import asyncio
import google.generativeai as genai
from app.core.config import settings


class AIService:
    def __init__(self) -> None:
        self.provider = (settings.AI_PROVIDER or "gemini").lower()
        self.model = settings.AI_MODEL or settings.GEMINI_MODEL

        # configure SDKs if needed
        if self.provider == "gemini":
            api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY
            if api_key:
                genai.configure(api_key=api_key)

    def generate_reply(self, user_message: str, user_context: str = "", role: Optional[str] = None, language: str = "ru") -> str:
        prompt = self._build_prompt(user_message=user_message, user_context=user_context, role=role, language=language)
        try:
            if self.provider == "gemini":
                model = genai.GenerativeModel(self.model)
                try:
                    resp = model.generate_content(prompt)
                except Exception as e:
                    # Friendly retry once
                    resp = model.generate_content(prompt)
                return getattr(resp, "text", "").strip() or "Пустой ответ от AI"
            elif self.provider == "openrouter":
                api_key = settings.OPENROUTER_API_KEY or settings.AI_API_KEY
                if not api_key:
                    return "AI не настроен: отсутствует OPENROUTER_API_KEY"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://eduanalytics.local",
                    "X-Title": "EduAnalytics",
                    "Content-Type": "application/json",
                }
                body = {
                    "model": self.model or "openrouter/auto",
                    "messages": [
                        {"role": "system", "content": self._system_message(role=role, language=language)},
                        {"role": "user", "content": prompt},
                    ],
                }
                r = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body, timeout=60.0)
                data = r.json()
                return (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip() or "Пустой ответ от AI"
            elif self.provider == "ollama":
                base = settings.OLLAMA_API_BASE.rstrip("/")
                model = "tinyllama"  # Force using tinyllama model
                try:
                    body = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": self._system_message(role=role, language=language)},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                    }
                    r = httpx.post(f"{base}/api/chat", json=body, timeout=60.0)
                    if r.status_code == 200:
                        data = r.json()
                        return (data.get("message", {}).get("content") or "").strip() or "Пустой ответ от AI"
                    else:
                        return f"Ошибка API: {r.status_code} - {r.text}"
                except Exception as e:
                    return f"Ошибка при запросе к Ollama: {e}"
            else:
                return "AI провайдер не настроен"
        except Exception as exc:  # noqa: BLE001
            return "Произошла ошибка при обработке запроса AI. Попробуйте еще раз позже."

    def _system_message(self, role: Optional[str] = None, language: str = "ru") -> str:
        # Language packs (short, focused)
        lang = (language or "ru").lower()
        if lang.startswith("kk") or lang.startswith("kz"):
            lang = "kz"
        elif lang.startswith("en"):
            lang = "en"
        else:
            lang = "ru"

        # Common base by language
        base = {
            "ru": {
                "system": "Ты — AI‑помощник EduAnalytics для образовательной аналитики. Отвечай по теме: оценки, активность, дедлайны, прогнозы, рекомендации.",
                "data": "Данные: всегда опирайся на контекст; не выдумывай цифры; при нехватке данных — попроси уточнение; сравнивай с историей, выделяй тренды.",
                "format": "Формат: кратко, по пунктам; выделяй ключевые метрики; давай 2–3 практических шага.",
                "clarify": "Если не хватает контекста (курс/период/студент) — задай 1–2 уточняющих вопроса.",
                "teacher": "Роль: преподаватель. Фокус: аналитика курсов, риск‑группы, дедлайны, улучшения курса. Разрешено: чтение аналитики, рекомендации, планирование.",
                "student": "Роль: студент. Фокус: собственный прогресс, ближайшие дедлайны и шаги улучшения. Разрешено: только свои данные и советы.",
                "admin": "Роль: админ. Фокус: сводные метрики системы, тренды использования, проблемные зоны."
            },
            "kz": {
                "system": "Сен — EduAnalytics білім беру аналитикасының AI‑көмекшісісің. Тақырыптан ауытқыма: бағалар, белсенділік, дедлайндар, болжам, ұсынымдар.",
                "data": "Деректер: әрдайым контекстке сүйен; цифрды ойдан шығарма; дерек жетпесе — нақтылауды сұра; трендтерді көрсет.",
                "format": "Пішім: қысқа әрі нақты; негізгі метрикаларды бөлектеп көрсет; 2–3 практикалық қадам бер.",
                "clarify": "Контекст жетіспесе (курс/период/студент) — 1–2 нақтылау сұрағын қой.",
                "teacher": "Рөл: оқытушы. Негізгі назар: курс аналитикасы, тәуекел топтары, дедлайндар, курсты жетілдіру.",
                "student": "Рөл: студент. Негізгі назар: жеке прогресс, жақын дедлайндар, жақсарту қадамдары.",
                "admin": "Рөл: админ. Негізгі назар: жүйелік метрикалар, трендтер, мәселелі аймақтар."
            },
            "en": {
                "system": "You are EduAnalytics AI assistant for educational analytics. Stay on topic: grades, engagement, deadlines, forecasting, recommendations.",
                "data": "Data: rely on provided context; never fabricate numbers; if insufficient data — ask to clarify; compare with history and highlight trends.",
                "format": "Format: concise bullet points; highlight key metrics; give 2–3 practical steps.",
                "clarify": "If context is missing (course/period/student) — ask 1–2 clarifying questions.",
                "teacher": "Role: teacher. Focus: course analytics, risk groups, deadlines, course improvement.",
                "student": "Role: student. Focus: own progress, upcoming deadlines, improvement steps.",
                "admin": "Role: admin. Focus: system‑level metrics, usage trends, problem areas."
            }
        }[lang]

        role_key = (role or "").lower()
        role_block = base.get("teacher" if role_key == "teacher" else "student" if role_key == "student" else "admin" if role_key == "admin" else "system")

        # Compose final message
        message = f"{base['system']}\n{base['data']}\n{base['format']}\n{base['clarify']}\n{role_block}"

        if self.provider == "ollama":
            return message
        # For other providers, keep concise
        return message

    def _build_prompt(self, user_message: str, user_context: str, role: Optional[str] = None, language: str = "ru") -> str:
        # Localize heading labels minimally based on language
        labels = {
            "ru": ("Контекст пользователя", "Вопрос", "Ответ"),
            "kz": ("Пайдаланушы контексті", "Сұрақ", "Жауап"),
            "en": ("User Context", "Question", "Answer"),
        }
        lang = (language or "ru").lower()
        if lang.startswith("kk") or lang.startswith("kz"):
            lang = "kz"
        elif lang.startswith("en"):
            lang = "en"
        else:
            lang = "ru"
        ctx_label, q_label, a_label = labels[lang]
        context_block = f"{ctx_label}:\n{user_context}\n" if user_context else ""
        return f"{self._system_message(role=role, language=language)}\n\n{context_block}{q_label}:\n{user_message}\n{a_label}:"
    
    async def generate_stream(self, user_message: str, user_context: str = "", role: Optional[str] = None, language: str = "ru") -> AsyncGenerator[str, None]:
        """Генерирует ответ в режиме потока (для SSE)"""
        prompt = self._build_prompt(user_message=user_message, user_context=user_context, role=role, language=language)
        try:
            if self.provider == "ollama":
                base = settings.OLLAMA_API_BASE.rstrip("/")
                model = "tinyllama"  # Force using tinyllama model
                body = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": self._system_message(role=role, language=language)},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": True,
                }
                
                try:
                    async with httpx.AsyncClient() as client:
                        async with client.stream("POST", f"{base}/api/chat", json=body, timeout=60.0) as response:
                            if response.status_code != 200:
                                yield f"Ошибка API: {response.status_code}"
                                return
                                
                            buffer = ""
                            async for chunk in response.aiter_text():
                                if not chunk.strip():
                                    continue
                                try:
                                    data = json.loads(chunk)
                                    if content := data.get("message", {}).get("content", ""):
                                        buffer += content
                                        yield content
                                except json.JSONDecodeError:
                                    # Некорректный JSON, пропускаем
                                    continue
                except Exception as e:
                    yield f"Ошибка при стриминге от Ollama: {e}"
            else:
                # Для других провайдеров используем обычный генератор и эмулируем стриминг
                full_response = self.generate_reply(user_message, user_context, role=role, language=language)
                chunk_size = 10  # символов в чанке
                for i in range(0, len(full_response), chunk_size):
                    yield full_response[i:i+chunk_size]
                    await asyncio.sleep(0.05)  # небольшая задержка для эмуляции стриминга
        except Exception as exc:
            yield f"Ошибка AI: {exc}"


