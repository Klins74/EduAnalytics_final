"""
AI Quota Enforcement Middleware.

Automatically enforces AI usage quotas on relevant endpoints.
"""

import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import time

from app.services.ai_quota_manager import ai_quota_manager
from app.models.user import User

logger = logging.getLogger(__name__)


class AIQuotaMiddleware:
    """Middleware to enforce AI quotas on API endpoints."""
    
    def __init__(self, app):
        self.app = app
        # Define which endpoints require quota checking
        self.ai_endpoints = {
            "/api/v1/ai/chat": "chat",
            "/api/v1/ai/analytics": "analytics", 
            "/api/v1/ai/recommendations": "recommendations",
            "/api/v1/ai/batch-analysis": "batch_analysis",
            "/api/v1/analytics/predict": "analytics"
        }
    
    async def __call__(self, request: Request, call_next: Callable):
        """Process request with quota enforcement."""
        start_time = time.time()
        
        # Check if this is an AI endpoint
        ai_service = self._get_ai_service(request.url.path)
        if not ai_service:
            return await call_next(request)
        
        # Get user from request state (set by auth middleware)
        user = getattr(request.state, 'user', None)
        if not user:
            # No user context, let auth middleware handle it
            return await call_next(request)
        
        # Estimate tokens for the request
        estimated_tokens = await self._estimate_tokens(request, ai_service)
        
        # Check quota
        allowed, usage_stats = await ai_quota_manager.check_quota(
            user_id=user.id,
            user_role=user.role,
            service=ai_service,
            estimated_tokens=estimated_tokens
        )
        
        if not allowed:
            return await self._create_quota_exceeded_response(usage_stats)
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Record usage after successful request
            duration = time.time() - start_time
            actual_tokens = await self._extract_token_usage(response, ai_service)
            
            await ai_quota_manager.record_usage(
                user_id=user.id,
                user_role=user.role,
                service=ai_service,
                actual_tokens=actual_tokens or estimated_tokens,
                request_duration=duration
            )
            
            # Add quota info to response headers
            if usage_stats:
                response.headers["X-AI-Quota-Remaining"] = str(usage_stats.remaining_requests)
                response.headers["X-AI-Quota-Reset"] = usage_stats.period_end.isoformat()
                if usage_stats.remaining_tokens is not None:
                    response.headers["X-AI-Token-Quota-Remaining"] = str(usage_stats.remaining_tokens)
            
            return response
            
        except Exception as e:
            # Don't record usage for failed requests
            logger.error(f"Error in AI endpoint {request.url.path}: {e}")
            raise
    
    def _get_ai_service(self, path: str) -> Optional[str]:
        """Determine if path is an AI endpoint and return service name."""
        for endpoint_pattern, service in self.ai_endpoints.items():
            if path.startswith(endpoint_pattern):
                return service
        return None
    
    async def _estimate_tokens(self, request: Request, service: str) -> Optional[int]:
        """Estimate token usage for the request."""
        try:
            # Read request body to estimate tokens
            body = await self._get_request_body(request)
            if not body:
                return None
            
            # Simple token estimation based on character count
            # This is a rough approximation; real implementations might use tiktoken
            content_length = len(str(body))
            
            # Different services have different token usage patterns
            if service == "chat":
                # Chat typically has input + output tokens
                estimated_tokens = max(100, content_length // 3)  # ~3 chars per token
                estimated_tokens += 150  # Estimated response tokens
            elif service == "analytics":
                # Analytics requests are usually more complex
                estimated_tokens = max(200, content_length // 2)
                estimated_tokens += 300  # Estimated response tokens
            elif service == "recommendations":
                # Recommendations are typically shorter
                estimated_tokens = max(50, content_length // 4)
                estimated_tokens += 100
            elif service == "batch_analysis":
                # Batch analysis can be very large
                estimated_tokens = max(500, content_length // 2)
                estimated_tokens += 1000
            else:
                # Default estimation
                estimated_tokens = max(100, content_length // 3)
                estimated_tokens += 200
            
            return min(estimated_tokens, 10000)  # Cap at 10k tokens
            
        except Exception as e:
            logger.error(f"Error estimating tokens: {e}")
            return 500  # Default fallback
    
    async def _get_request_body(self, request: Request) -> Optional[str]:
        """Safely get request body."""
        try:
            # Check if body has already been read
            if hasattr(request.state, 'body'):
                return request.state.body
            
            # Read and cache body
            body = await request.body()
            request.state.body = body.decode('utf-8') if body else ""
            return request.state.body
            
        except Exception as e:
            logger.error(f"Error reading request body: {e}")
            return None
    
    async def _extract_token_usage(self, response: Response, service: str) -> Optional[int]:
        """Extract actual token usage from response."""
        try:
            # Check if response has token usage info in headers
            token_header = response.headers.get("X-AI-Tokens-Used")
            if token_header:
                return int(token_header)
            
            # If no header, estimate from response body
            if hasattr(response, 'body'):
                body_length = len(response.body) if response.body else 0
                return max(50, body_length // 4)  # Rough estimation
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting token usage: {e}")
            return None
    
    async def _create_quota_exceeded_response(self, usage_stats) -> JSONResponse:
        """Create response for quota exceeded."""
        error_detail = {
            "error": "quota_exceeded",
            "message": "AI service quota exceeded for your user role",
            "quota_info": {}
        }
        
        if usage_stats:
            error_detail["quota_info"] = {
                "requests_used": usage_stats.requests_used,
                "tokens_used": usage_stats.tokens_used,
                "period_end": usage_stats.period_end.isoformat(),
                "remaining_requests": usage_stats.remaining_requests
            }
            
            if usage_stats.remaining_tokens is not None:
                error_detail["quota_info"]["remaining_tokens"] = usage_stats.remaining_tokens
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_detail,
            headers={
                "Retry-After": "3600",  # Suggest retry after 1 hour
                "X-AI-Quota-Exceeded": "true"
            }
        )


def create_ai_quota_middleware():
    """Factory function to create AI quota middleware."""
    return AIQuotaMiddleware
