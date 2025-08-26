from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
from app.core.security import get_current_user
from app.models.user import User
from app.services.ai_service import AIService
from app.services.ai_memory import ChatMemoryRepository, build_history_stub
from app.services.rate_limit import RateLimiter
from app.services.ai_tools import AiToolRegistry
from app.services.ai_intent import extract_intent
from app.services.ai_function_calling import process_function_calls
import app.services.ai_functions  # Импортируем для регистрации функций
import app.services.ai_analytics_tools  # Импортируем аналитические инструменты


router = APIRouter(prefix="/ai", tags=["AI"])


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    scope: Optional[str] = None  # e.g., 'student' | 'teacher' | 'course' | 'general'
    student_id: Optional[int] = None
    course_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
class IntentResponse(BaseModel):
    action: str
    params: dict
    confidence: float



memory = ChatMemoryRepository()
limiter = RateLimiter()
tools = AiToolRegistry()


@router.post("/chat", response_model=ChatResponse, summary="AI чат (Gemini/OpenRouter/Ollama)")
async def ai_chat(payload: ChatRequest, request: Request, current_user: User = Depends(get_current_user)) -> ChatResponse:
    text = payload.message.strip()
    if not text:
        return ChatResponse(reply="Пожалуйста, задайте вопрос.")
    await limiter.check(current_user.id)
    pieces = [
        f"Пользователь: {getattr(current_user, 'username', 'unknown')}",
        f"Роль: {getattr(current_user, 'role', 'unknown')}",
    ]
    if payload.scope:
        pieces.append(f"Scope: {payload.scope}")
    if payload.student_id:
        pieces.append(f"StudentID: {payload.student_id}")
    if payload.course_id:
        pieces.append(f"CourseID: {payload.course_id}")
    if payload.context:
        pieces.append(f"FrontendContext: {payload.context}")
    user_context = " | ".join(pieces)
    service = AIService()
    # Память: добавляем вопрос / читаем контекст
    await memory.append_message(current_user.id, role="user", content=text)
    recent = await memory.get_recent_messages(current_user.id, limit=8)
    history_stub = build_history_stub(recent, max_chars=1200)
    # Инструменты: краткая выжимка метрик
    auth_header = f"Bearer {getattr(current_user, 'token', '')}"  # нет сохраненного токена → используем заголовок ниже
    # Вытянем из контекста запроса реальный Authorization
    # Прокси реального Authorization из запроса (без записи в память)
    # FastAPI сам пробросит заголовки в зависимости — здесь формируем строку
    auth_header_value = request.headers.get('Authorization')

    # Студент может видеть только свои данные
    requested_student_id = payload.student_id
    if getattr(current_user, 'role', None) == 'student' and requested_student_id and requested_student_id != getattr(current_user, 'id', None):
        requested_student_id = None

    tool_summary = await tools.gather_context(
        auth_header=auth_header_value,
        role=getattr(current_user, 'role', None),
        scope=payload.scope,
        student_id=requested_student_id,
        course_id=payload.course_id,
    )
    extra = (f"\nКраткие данные:\n{tool_summary}" if tool_summary else "")
    user_context = user_context + (f" | History:\n{history_stub}" if history_stub else "") + extra
    # Language detection from headers (Accept-Language)
    accept_lang = (request.headers.get('Accept-Language') or 'ru').lower()
    lang = 'ru'
    if accept_lang.startswith('en'):
        lang = 'en'
    elif accept_lang.startswith('kk') or accept_lang.startswith('kz'):
        lang = 'kz'

    reply = service.generate_reply(user_message=text, user_context=user_context, role=getattr(current_user, 'role', None), language=lang)
    await memory.append_message(current_user.id, role="assistant", content=reply)
    return ChatResponse(reply=reply)


@router.post("/chat/stream", summary="AI чат (SSE)")
async def ai_chat_stream(payload: ChatRequest, request: Request, current_user: User = Depends(get_current_user)):
    text = payload.message.strip()
    if not text:
        def _err():
            yield "data: Пожалуйста, задайте вопрос.\n\n"
        return StreamingResponse(_err(), media_type="text/event-stream")
    await limiter.check(current_user.id)
    pieces = [
        f"Пользователь: {getattr(current_user, 'username', 'unknown')}",
        f"Роль: {getattr(current_user, 'role', 'unknown')}",
    ]
    if payload.scope:
        pieces.append(f"Scope: {payload.scope}")
    if payload.student_id:
        pieces.append(f"StudentID: {payload.student_id}")
    if payload.course_id:
        pieces.append(f"CourseID: {payload.course_id}")
    if payload.context:
        pieces.append(f"FrontendContext: {payload.context}")
    user_context = " | ".join(pieces)
    await memory.append_message(current_user.id, role="user", content=text)
    recent = await memory.get_recent_messages(current_user.id, limit=8)
    history_stub = build_history_stub(recent, max_chars=1200)
    auth_header_value = request.headers.get('Authorization')
    requested_student_id = payload.student_id
    if getattr(current_user, 'role', None) == 'student' and requested_student_id and requested_student_id != getattr(current_user, 'id', None):
        requested_student_id = None
    tool_summary = await tools.gather_context(
        auth_header=auth_header_value,
        role=getattr(current_user, 'role', None),
        scope=payload.scope,
        student_id=requested_student_id,
        course_id=payload.course_id,
    )
    extra = (f"\nКраткие данные:\n{tool_summary}" if tool_summary else "")
    user_context = user_context + (f" | History:\n{history_stub}" if history_stub else "") + extra

    # Настоящий стриминг для Ollama
    service = AIService()
    
    async def _gen():
        full_response = ""
        # Language detection
        accept_lang = (request.headers.get('Accept-Language') or 'ru').lower()
        lang = 'ru'
        if accept_lang.startswith('en'):
            lang = 'en'
        elif accept_lang.startswith('kk') or accept_lang.startswith('kz'):
            lang = 'kz'

        async for chunk in service.generate_stream(user_message=text, user_context=user_context, role=getattr(current_user, 'role', None), language=lang):
            full_response += chunk
            yield f"data: {chunk}\n\n"
        yield "event: end\n"
        yield "data: [END]\n\n"
        # Сохраняем полный ответ в память
        await memory.append_message(current_user.id, role="assistant", content=full_response)

    return StreamingResponse(_gen(), media_type="text/event-stream")


@router.post("/intent", response_model=IntentResponse, summary="Извлечение намерения из текста")
async def ai_intent(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    text = (payload.message or "").strip()
    if not text:
        return IntentResponse(action="none", params={}, confidence=0.0)
    intent = extract_intent(text)
    return IntentResponse(**intent)


@router.post("/function", response_model=ChatResponse, summary="AI чат с вызовом функций")
async def ai_function_chat(payload: ChatRequest, request: Request, current_user: User = Depends(get_current_user)) -> ChatResponse:
    """Endpoint для чата с поддержкой вызова функций"""
    text = payload.message.strip()
    if not text:
        return ChatResponse(reply="Пожалуйста, задайте вопрос.")
    
    await limiter.check(current_user.id)
    
    # Формируем системный контекст
    pieces = [
        f"Пользователь: {getattr(current_user, 'username', 'unknown')}",
        f"Роль: {getattr(current_user, 'role', 'unknown')}",
    ]
    if payload.scope:
        pieces.append(f"Scope: {payload.scope}")
    if payload.student_id:
        pieces.append(f"StudentID: {payload.student_id}")
    if payload.course_id:
        pieces.append(f"CourseID: {payload.course_id}")
    if payload.context:
        pieces.append(f"FrontendContext: {payload.context}")
    
    system_context = " | ".join(pieces)
    
    # Сохраняем сообщение пользователя в историю
    await memory.append_message(current_user.id, role="user", content=text)
    
    # Получаем историю сообщений
    recent = await memory.get_recent_messages(current_user.id, limit=8)
    history_stub = build_history_stub(recent, max_chars=1200)
    if history_stub:
        system_context += f" | История диалога:\n{history_stub}"
    
    # Обрабатываем сообщение с возможным вызовом функций
    reply = await process_function_calls(text, system_context)
    
    # Сохраняем ответ в историю
    await memory.append_message(current_user.id, role="assistant", content=reply)
    
    return ChatResponse(reply=reply)


