"""API management routes for versioning, metrics, and idempotency."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.core.api_pagination import APIVersioning, APIParams, paginated_query, PaginatedResponse
from app.core.idempotency import idempotency_manager, require_idempotency_key_dependency
from app.middleware.api_versioning import get_api_metrics

router = APIRouter(prefix="/api-management", tags=["API Management"])


class APIVersionInfo(BaseModel):
    """API version information response."""
    current_version: str
    supported_versions: List[str]
    version_format: str
    deprecation_policy: str


class IdempotencyKeyInfo(BaseModel):
    """Idempotency key information."""
    key: str
    endpoint: str
    created_at: str
    expires_at: str
    response_status: int


class IdempotencyKeyRequest(BaseModel):
    """Request to generate idempotency key."""
    description: Optional[str] = None


class IdempotencyKeyResponse(BaseModel):
    """Response with generated idempotency key."""
    idempotency_key: str
    description: Optional[str]
    generated_at: str


class APIMetricsResponse(BaseModel):
    """API metrics response."""
    endpoints: Dict[str, Any]
    total_requests: int
    total_errors: int
    generated_at: str


class APIHealthResponse(BaseModel):
    """API health response."""
    status: str
    version: str
    timestamp: str
    components: Dict[str, Any]


@router.get("/version", response_model=APIVersionInfo, summary="Get API version information")
async def get_api_version_info() -> APIVersionInfo:
    """Get current API version information."""
    version_info = APIVersioning.get_version_info()
    
    return APIVersionInfo(
        current_version=version_info["current_version"],
        supported_versions=version_info["supported_versions"],
        version_format=version_info["version_format"],
        deprecation_policy=version_info["deprecation_policy"]
    )


@router.get("/metrics", response_model=APIMetricsResponse, summary="Get API metrics")
async def get_api_metrics_endpoint(
    current_user: User = Depends(require_role(UserRole.admin))
) -> APIMetricsResponse:
    """Get API usage metrics."""
    try:
        metrics = get_api_metrics()
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API metrics not available"
            )
        
        return APIMetricsResponse(
            endpoints=metrics.get("endpoints", {}),
            total_requests=metrics.get("total_requests", 0),
            total_errors=metrics.get("total_errors", 0),
            generated_at=metrics.get("generated_at", datetime.utcnow().isoformat())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API metrics: {str(e)}"
        )


@router.post("/idempotency/generate", response_model=IdempotencyKeyResponse, summary="Generate idempotency key")
async def generate_idempotency_key(
    request: IdempotencyKeyRequest,
    current_user: User = Depends(get_current_user)
) -> IdempotencyKeyResponse:
    """Generate a new idempotency key."""
    try:
        key = idempotency_manager.generate_idempotency_key()
        
        return IdempotencyKeyResponse(
            idempotency_key=key,
            description=request.description,
            generated_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate idempotency key: {str(e)}"
        )


@router.get("/idempotency/keys", response_model=List[IdempotencyKeyInfo], summary="Get user's idempotency keys")
async def get_user_idempotency_keys(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> List[IdempotencyKeyInfo]:
    """Get current user's idempotency keys."""
    try:
        keys = await idempotency_manager.get_user_keys(current_user.id, limit)
        
        return [
            IdempotencyKeyInfo(
                key=key_info["key"],
                endpoint=key_info["endpoint"],
                created_at=key_info["created_at"],
                expires_at=key_info["expires_at"],
                response_status=key_info["response_status"]
            )
            for key_info in keys
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get idempotency keys: {str(e)}"
        )


@router.post("/idempotency/cleanup", summary="Cleanup expired idempotency keys")
async def cleanup_expired_idempotency_keys(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Clean up expired idempotency keys."""
    try:
        deleted_count = await idempotency_manager.cleanup_expired()
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} expired idempotency keys",
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup idempotency keys: {str(e)}"
        )


@router.post("/test/idempotency", summary="Test idempotency functionality")
async def test_idempotency(
    test_data: Dict[str, Any],
    request: Request,
    idempotency_key: str = Depends(require_idempotency_key_dependency),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test endpoint for idempotency functionality."""
    try:
        # Simulate some processing
        import time
        time.sleep(0.1)
        
        response_data = {
            "success": True,
            "message": "Test operation completed",
            "data": test_data,
            "user_id": current_user.id,
            "idempotency_key": idempotency_key,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(request.state, 'request_id', None)
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test operation failed: {str(e)}"
        )


@router.get("/health", response_model=APIHealthResponse, summary="API health check")
async def api_health_check() -> APIHealthResponse:
    """Comprehensive API health check."""
    try:
        components = {}
        overall_status = "healthy"
        
        # Check API versioning
        try:
            version_info = APIVersioning.get_version_info()
            components["versioning"] = {
                "status": "ok",
                "current_version": version_info["current_version"],
                "supported_versions": len(version_info["supported_versions"])
            }
        except Exception as e:
            components["versioning"] = {
                "status": "error",
                "error": str(e)
            }
            overall_status = "degraded"
        
        # Check idempotency system
        try:
            # Test idempotency manager
            test_key = idempotency_manager.generate_idempotency_key()
            components["idempotency"] = {
                "status": "ok",
                "test_key_generated": bool(test_key)
            }
        except Exception as e:
            components["idempotency"] = {
                "status": "error",
                "error": str(e)
            }
            overall_status = "degraded"
        
        # Check metrics
        try:
            metrics = get_api_metrics()
            components["metrics"] = {
                "status": "ok" if metrics else "unavailable",
                "endpoints_tracked": len(metrics.get("endpoints", {})) if metrics else 0
            }
        except Exception as e:
            components["metrics"] = {
                "status": "error",
                "error": str(e)
            }
            overall_status = "degraded"
        
        # Check database connectivity
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as db:
                await db.execute(text("SELECT 1"))
                components["database"] = {
                    "status": "ok",
                    "connection": "active"
                }
        except Exception as e:
            components["database"] = {
                "status": "error",
                "error": str(e)
            }
            overall_status = "unhealthy"
        
        # Check Redis connectivity
        try:
            from app.services.redis_service import redis_service
            redis_client = redis_service.get_client()
            await redis_client.ping()
            components["redis"] = {
                "status": "ok",
                "connection": "active"
            }
        except Exception as e:
            components["redis"] = {
                "status": "error",
                "error": str(e)
            }
            if overall_status != "unhealthy":
                overall_status = "degraded"
        
        return APIHealthResponse(
            status=overall_status,
            version=APIVersioning.DEFAULT_VERSION,
            timestamp=datetime.utcnow().isoformat(),
            components=components
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/endpoints", summary="List all API endpoints")
async def list_api_endpoints(
    include_deprecated: bool = False,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """List all available API endpoints."""
    try:
        from fastapi.routing import APIRoute
        from app.main import app  # Import the FastAPI app
        
        endpoints = []
        
        for route in app.routes:
            if isinstance(route, APIRoute):
                endpoint_info = {
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": route.name,
                    "summary": getattr(route, 'summary', None),
                    "tags": getattr(route, 'tags', [])
                }
                
                # Check if endpoint is deprecated
                is_deprecated = any(
                    tag.lower() == 'deprecated' for tag in endpoint_info.get("tags", [])
                )
                
                if include_deprecated or not is_deprecated:
                    endpoints.append(endpoint_info)
        
        # Group by tags
        endpoints_by_tag = {}
        for endpoint in endpoints:
            for tag in endpoint.get("tags", ["Untagged"]):
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append(endpoint)
        
        return {
            "total_endpoints": len(endpoints),
            "endpoints_by_tag": endpoints_by_tag,
            "api_version": APIVersioning.DEFAULT_VERSION,
            "include_deprecated": include_deprecated,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list endpoints: {str(e)}"
        )


@router.get("/rate-limits", summary="Get API rate limit information")
async def get_rate_limit_info(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get rate limit information for current user."""
    try:
        # This would integrate with your rate limiting system
        # For now, return basic information
        
        rate_limits = {
            "user_id": current_user.id,
            "role": current_user.role.value,
            "limits": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000
            },
            "current_usage": {
                "requests_this_minute": 0,  # Would come from rate limiter
                "requests_this_hour": 0,
                "requests_this_day": 0
            },
            "reset_times": {
                "minute_reset": datetime.utcnow().replace(second=0, microsecond=0).isoformat(),
                "hour_reset": datetime.utcnow().replace(minute=0, second=0, microsecond=0).isoformat(),
                "day_reset": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            }
        }
        
        return rate_limits
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit info: {str(e)}"
        )
