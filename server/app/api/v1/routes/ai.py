from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.ai_service import AIService
from app.services.ai_memory import ChatMemoryRepository, build_history_stub
from app.services.rate_limit import RateLimiter
from app.services.ai_tools import AiToolRegistry
from app.services.ai_intent import extract_intent
from app.services.ai_function_calling import process_function_calls
from app.services.ai_quota_manager import ai_quota_manager, UsageStats
from app.services.permission_aware_search import permission_search_service
from app.db.session import get_async_session
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


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    content_types: Optional[List[str]] = None


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    query_time_ms: float


class QuotaResponse(BaseModel):
    service: str
    usage_stats: Dict[str, Any]


class AllQuotasResponse(BaseModel):
    quotas: Dict[str, Dict[str, Any]]
    system_stats: Dict[str, Any]



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


@router.post("/search", response_model=SearchResponse, summary="Permission-aware content search")
async def ai_search(
    request_data: SearchRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> SearchResponse:
    """Search content using RAG with permission filtering."""
    import time
    start_time = time.time()
    
    try:
        results = await permission_search_service.search_with_permissions(
            query=request_data.query,
            user_id=current_user.id,
            db=db,
            top_k=request_data.top_k,
            content_types=request_data.content_types
        )
        
        query_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=results,
            total_found=len(results),
            query_time_ms=round(query_time_ms, 2)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/quota/{service}", response_model=QuotaResponse, summary="Get AI quota usage for service")
async def get_service_quota(
    service: str,
    current_user: User = Depends(get_current_user)
) -> QuotaResponse:
    """Get quota usage statistics for a specific AI service."""
    try:
        usage_stats = await ai_quota_manager.get_user_usage_stats(
            user_id=current_user.id,
            user_role=current_user.role,
            services=[service]
        )
        
        if service not in usage_stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service}' not found or not accessible"
            )
        
        stats = usage_stats[service]
        return QuotaResponse(
            service=service,
            usage_stats={
                "requests_used": stats.requests_used,
                "tokens_used": stats.tokens_used,
                "remaining_requests": stats.remaining_requests,
                "remaining_tokens": stats.remaining_tokens,
                "period_start": stats.period_start.isoformat(),
                "period_end": stats.period_end.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quota info: {str(e)}"
        )


@router.get("/quotas", response_model=AllQuotasResponse, summary="Get all AI quotas")
async def get_all_quotas(
    current_user: User = Depends(get_current_user)
) -> AllQuotasResponse:
    """Get quota usage statistics for all AI services."""
    try:
        # Get user's usage stats
        usage_stats = await ai_quota_manager.get_user_usage_stats(
            user_id=current_user.id,
            user_role=current_user.role
        )
        
        # Get quota configs
        quota_configs = await ai_quota_manager.get_quota_config(current_user.role)
        
        # Format response
        quotas = {}
        for service, stats in usage_stats.items():
            quotas[service] = {
                "usage": {
                    "requests_used": stats.requests_used,
                    "tokens_used": stats.tokens_used,
                    "remaining_requests": stats.remaining_requests,
                    "remaining_tokens": stats.remaining_tokens,
                    "period_start": stats.period_start.isoformat(),
                    "period_end": stats.period_end.isoformat()
                },
                "limits": quota_configs.get(service, {})
            }
        
        # Get system stats (admin only)
        system_stats = {}
        if current_user.role == UserRole.admin:
            system_stats = await ai_quota_manager.get_system_usage_stats()
        
        return AllQuotasResponse(
            quotas=quotas,
            system_stats=system_stats
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quota info: {str(e)}"
        )


@router.post("/quota/{service}/reset", summary="Reset AI quota for service (admin only)")
async def reset_service_quota(
    service: str,
    target_user_id: Optional[int] = None,
    current_user: User = Depends(require_role(UserRole.admin))
):
    """Reset quota for a specific service and user (admin only)."""
    try:
        # Use target_user_id if provided, otherwise reset for current user
        user_id = target_user_id or current_user.id
        
        # Get target user's role
        # For simplicity, we'll use current_user.role if no target specified
        # In production, you'd fetch the target user's role from database
        user_role = current_user.role
        
        success = await ai_quota_manager.reset_user_quota(
            user_id=user_id,
            user_role=user_role,
            service=service
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to reset quota for service '{service}'"
            )
        
        return {"message": f"Quota reset successful for service '{service}'", "user_id": user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset quota: {str(e)}"
        )


@router.get("/content/stats", summary="Get accessible content statistics")
async def get_content_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about content accessible to the current user."""
    try:
        stats = await permission_search_service.get_user_accessible_content_stats(
            user_id=current_user.id,
            db=db
        )
        
        return {
            "user_id": current_user.id,
            "user_role": current_user.role.value,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content stats: {str(e)}"
        )


@router.post("/recommendations", summary="Get AI-powered recommendations")
async def get_ai_recommendations(
    course_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered recommendations for learning or teaching."""
    try:
        # This is a placeholder for the actual recommendation logic
        # In a real implementation, this would use the permission-aware search
        # to find relevant content and generate personalized recommendations
        
        recommendations = []
        
        if current_user.role == UserRole.student:
            # Student recommendations
            search_query = "study materials assignments practice exercises"
            results = await permission_search_service.search_with_permissions(
                query=search_query,
                user_id=current_user.id,
                db=db,
                top_k=5,
                content_types=["assignment", "page", "quiz"]
            )
            
            for result in results:
                recommendations.append({
                    "type": "study_material",
                    "title": result.get("title", "Recommended Content"),
                    "content_type": result["metadata"].get("type"),
                    "relevance_score": result["score"],
                    "course_id": result["metadata"].get("course_id"),
                    "description": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                })
        
        elif current_user.role in [UserRole.teacher, UserRole.admin]:
            # Teacher recommendations
            search_query = "teaching resources lesson plans assessment rubrics"
            results = await permission_search_service.search_with_permissions(
                query=search_query,
                user_id=current_user.id,
                db=db,
                top_k=5
            )
            
            for result in results:
                recommendations.append({
                    "type": "teaching_resource",
                    "title": result.get("title", "Recommended Resource"),
                    "content_type": result["metadata"].get("type"),
                    "relevance_score": result["score"],
                    "course_id": result["metadata"].get("course_id"),
                    "description": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                })
        
        return {
            "user_id": current_user.id,
            "recommendations": recommendations,
            "generated_at": "now",
            "total_count": len(recommendations)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


