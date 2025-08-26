from __future__ import annotations

import json
from typing import Dict, Any

from app.services.ai_service import AIService


INTENT_SYSTEM = (
    "Ты — парсер намерений EduAnalytics. Твоя задача - извлекать из русскоязычных запросов намерение (action) "
    "и параметры (params) строго в формате JSON. Ты должен отвечать ТОЛЬКО JSON без каких-либо пояснений или дополнительного текста. "
    "Структура ответа: {\"action\": str, \"params\": object, \"confidence\": float}. "
    "КРИТИЧЕСКИ ВАЖНО: твой ответ должен содержать только валидный JSON объект, без любого дополнительного текста до или после JSON. "
    "Не добавляй обратные кавычки, маркеры кода или другие символы форматирования."
)

ALLOWED_ACTIONS = {
    "create_schedule": {
        "required": ["course_id", "instructor_id", "schedule_date", "start_time", "end_time"],
        "optional": ["location", "lesson_type", "description"],
    }
}


def build_intent_prompt(user_message: str) -> str:
    guidance = (
        "ЗАДАЧА: Проанализировать текст пользователя и определить, содержит ли он намерение создать расписание занятия.\n\n"
        
        "ДОПУСТИМЫЕ ДЕЙСТВИЯ:\n"
        "- create_schedule: Создание занятия в расписании\n"
        "- none: Запрос не связан с созданием расписания\n\n"
        
        "ПРАВИЛА НОРМАЛИЗАЦИИ ДАННЫХ:\n"
        "1. Даты (всегда в формате YYYY-MM-DD): \n"
        "   - 'сегодня' → текущая дата (например, 2023-08-15)\n"
        "   - 'завтра' → следующий день (например, 2023-08-16)\n"
        "   - 'послезавтра' → через 2 дня (например, 2023-08-17)\n"
        "   - '10 июня', '10.06' → 2023-06-10\n"
        "   - 'в следующий понедельник' → дата ближайшего понедельника\n\n"
        
        "2. Время (всегда в формате HH:MM, 24-часовой формат):\n"
        "   - '17:00' → '17:00'\n"
        "   - 'с 17 до 18:30' → start_time='17:00', end_time='18:30'\n"
        "   - 'с 9 до 10' → start_time='09:00', end_time='10:00'\n"
        "   - 'в 15 часов' → start_time='15:00', end_time='16:30' (по умолчанию +90 минут)\n"
        "   - 'в 3 часа дня' → start_time='15:00', end_time='16:30'\n\n"
        
        "3. Место проведения (строка):\n"
        "   - '101', 'Аудитория 101', 'кабинет 101' → location='101'\n"
        "   - 'в главном корпусе' → location='Главный корпус'\n\n"
        
        "ПАРАМЕТРЫ ДЛЯ create_schedule:\n"
        "Обязательные параметры:\n"
        "- course_id (int): ID курса (например, 1, 2, 3)\n"
        "- instructor_id (int): ID преподавателя (например, 1, 2, 3)\n"
        "- schedule_date (str): дата в формате YYYY-MM-DD\n"
        "- start_time (str): время начала в формате HH:MM\n"
        "- end_time (str): время окончания в формате HH:MM\n\n"
        
        "Дополнительные параметры:\n"
        "- location (str): место проведения\n"
        "- lesson_type (str): тип занятия (лекция, семинар, практика)\n"
        "- description (str): описание\n\n"
        
        "УРОВНИ УВЕРЕННОСТИ (confidence):\n"
        "- 0.9-1.0: все обязательные параметры указаны явно и корректно\n"
        "- 0.7-0.8: некоторые параметры выведены из контекста или неполные\n"
        "- 0.5-0.6: не хватает некоторых обязательных параметров\n"
        "- 0.0-0.4: запрос не связан с созданием расписания\n\n"
        
        "ПРИМЕРЫ:\n"
        "1. Запрос: \"Создай занятие по математике с преподавателем 2 завтра с 9:00 до 10:30 в аудитории 101\"\n"
        "   Ответ: {\"action\": \"create_schedule\", \"params\": {\"course_id\": 1, \"instructor_id\": 2, \"schedule_date\": \"2023-08-16\", \"start_time\": \"09:00\", \"end_time\": \"10:30\", \"location\": \"101\"}, \"confidence\": 0.95}\n\n"
        
        "2. Запрос: \"Какие у меня оценки по математике?\"\n"
        "   Ответ: {\"action\": \"none\", \"params\": {}, \"confidence\": 0.0}\n\n"
        
        "ВАЖНО: Твой ответ должен содержать ТОЛЬКО JSON объект без дополнительного текста, комментариев или маркеров кода."
    )
    return f"{INTENT_SYSTEM}\n\n{guidance}\n\nТекст запроса:\n{user_message}\n\nОтвет (только JSON):" 


def extract_intent(user_message: str) -> Dict[str, Any]:
    service = AIService()
    prompt = build_intent_prompt(user_message)
    reply = service.generate_reply(user_message=prompt, user_context="")
    
    # Очистка ответа от лишнего текста для поиска JSON
    # Ollama иногда добавляет текст до или после JSON
    try:
        # Удаляем все маркеры кода и лишние пробелы
        cleaned_reply = reply.replace("```json", "").replace("```", "").strip()
        
        # Ищем начало и конец JSON объекта
        start_idx = cleaned_reply.find('{')
        end_idx = cleaned_reply.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = cleaned_reply[start_idx:end_idx]
            
            # Дополнительная проверка на корректность JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # Если не удалось распарсить, попробуем исправить распространенные ошибки
                json_str = json_str.replace("'", "\"")  # Замена одинарных кавычек на двойные
                
                # Проверка и исправление неэкранированных кавычек в значениях
                import re
                json_str = re.sub(r':\s*"([^"]*)"([^,}]*)[,}]', r': "\1\2"', json_str)
                
                # Еще одна попытка парсинга
                data = json.loads(json_str)
            
            # Санитация
            if not isinstance(data, dict):
                return {"action": "none", "params": {}, "confidence": 0.0}
                
            action = data.get("action") or "none"
            params = data.get("params") or {}
            
            # Проверка типов данных
            if not isinstance(params, dict):
                params = {}
                
            # Нормализация confidence
            try:
                confidence = float(data.get("confidence") or 0.0)
                # Ограничиваем значение от 0 до 1
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                confidence = 0.0
                
            # Фильтрация по whitelist
            if action not in ALLOWED_ACTIONS and action != "none":
                return {"action": "none", "params": {}, "confidence": 0.0}
                
            # Проверка обязательных параметров
            if action in ALLOWED_ACTIONS:
                required_params = ALLOWED_ACTIONS[action].get("required", [])
                missing_params = [p for p in required_params if p not in params]
                if missing_params:
                    # Снижаем confidence, если не хватает параметров
                    confidence = min(confidence, 0.6)
                    
            return {"action": action, "params": params, "confidence": confidence}
    except Exception as e:
        print(f"Error parsing intent: {e}")
        print(f"Raw reply: {reply}")
        
    return {"action": "none", "params": {}, "confidence": 0.0}


