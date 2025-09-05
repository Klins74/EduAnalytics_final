from typing import Dict, Any
import time
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
import httpx

from app.db.session import get_async_session
from app.core.config import settings
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.canvas_client import CanvasClient
from app.services.canvas_auth import CanvasAuthService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/health",
    summary="Basic health check",
    description="Basic health endpoint that returns 200 OK if the service is running",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    },
    tags=["Health"]
)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns simple OK status for load balancers and monitoring systems.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "eduanalytics-api"
    }


@router.get(
    "/readiness",
    summary="Readiness check with dependencies",
    description="Comprehensive readiness check that validates all critical dependencies",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready - dependencies unavailable"}
    },
    tags=["Health"]
)
async def readiness_check(db: AsyncSession = Depends(get_async_session)):
    """
    Readiness check that validates all critical dependencies.
    
    Checks:
    - Database connectivity
    - Redis connectivity  
    - Canvas API connectivity (if configured)
    - Critical environment variables
    """
    start_time = time.time()
    checks = []
    overall_status = "ready"
    
    # 1. Database check
    try:
        result = await db.execute(text("SELECT 1"))
        db_status = "healthy"
        db_latency = round((time.time() - start_time) * 1000, 2)
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
        db_latency = None
        overall_status = "not_ready"
    
    checks.append({
        "name": "database",
        "status": db_status,
        "latency_ms": db_latency,
        "details": "PostgreSQL connection"
    })
    
    # 2. Redis check
    try:
        redis_start = time.time()
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        redis_status = "healthy"
        redis_latency = round((time.time() - redis_start) * 1000, 2)
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_status = "unhealthy"
        redis_latency = None
        overall_status = "not_ready"
    
    checks.append({
        "name": "redis",
        "status": redis_status,
        "latency_ms": redis_latency,
        "details": "Redis cache and sessions"
    })
    
    # 3. Canvas API check (if configured)
    canvas_status = "not_configured"
    canvas_latency = None
    
    if hasattr(settings, 'CANVAS_BASE_URL') and settings.CANVAS_BASE_URL:
        try:
            canvas_start = time.time()
            async with httpx.AsyncClient() as client:
                # Check Canvas API base endpoint
                response = await client.get(
                    f"{settings.CANVAS_BASE_URL}/api/v1/accounts/self",
                    timeout=5.0
                )
                # We expect a 401 since we're not authenticated, but service is reachable
                if response.status_code in [200, 401, 403]:
                    canvas_status = "healthy"
                else:
                    canvas_status = "unhealthy"
                    
            canvas_latency = round((time.time() - canvas_start) * 1000, 2)
            
        except Exception as e:
            logger.error(f"Canvas API health check failed: {str(e)}")
            canvas_status = "unhealthy"
            canvas_latency = None
            # Canvas is optional, don't fail overall readiness
    
    checks.append({
        "name": "canvas_api",
        "status": canvas_status,
        "latency_ms": canvas_latency,
        "details": "Canvas LMS API connectivity"
    })
    
    # 4. Environment configuration check
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "REDIS_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not hasattr(settings, var.lower()) or not getattr(settings, var.lower()):
            missing_vars.append(var)
    
    config_status = "healthy" if not missing_vars else "unhealthy"
    if missing_vars:
        overall_status = "not_ready"
    
    checks.append({
        "name": "configuration",
        "status": config_status,
        "details": f"Missing vars: {missing_vars}" if missing_vars else "All required variables present"
    })
    
    total_latency = round((time.time() - start_time) * 1000, 2)
    
    response_data = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "total_latency_ms": total_latency,
        "checks": checks,
        "service": "eduanalytics-api",
        "version": getattr(settings, 'VERSION', 'unknown')
    }
    
    if overall_status == "not_ready":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response_data
        )
    
    return response_data


@router.get(
    "/live",
    summary="Liveness check",
    description="Liveness probe for Kubernetes/container orchestration",
    responses={
        200: {"description": "Service is live"},
    },
    tags=["Health"]
)
async def liveness_check():
    """
    Liveness check for container orchestration.
    
    Should only fail if the service is completely broken and needs restart.
    Does not check external dependencies.
    """
    return {
        "status": "live",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.process_time()
    }


@router.get(
    "/metrics",
    summary="Service metrics",
    description="Basic service metrics for monitoring (admin only)",
    responses={
        200: {"description": "Service metrics"},
        401: {"description": "Unauthorized"},
        403: {"description": "Insufficient permissions"}
    },
    tags=["Health"]
)
async def service_metrics(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.admin))
):
    """
    Service metrics endpoint for monitoring.
    
    Returns basic metrics about the service state and performance.
    Only accessible to administrators.
    """
    try:
        # Database metrics
        db_start = time.time()
        
        # Count total records in main tables
        tables_query = """
        SELECT 
            'users' as table_name, COUNT(*) as count FROM users
        UNION ALL
        SELECT 
            'courses' as table_name, COUNT(*) as count FROM courses
        UNION ALL
        SELECT 
            'assignments' as table_name, COUNT(*) as count FROM assignments
        UNION ALL
        SELECT 
            'submissions' as table_name, COUNT(*) as count FROM submissions
        UNION ALL
        SELECT 
            'grades' as table_name, COUNT(*) as count FROM grades;
        """
        
        result = await db.execute(text(tables_query))
        table_counts = {row[0]: row[1] for row in result.fetchall()}
        
        db_latency = round((time.time() - db_start) * 1000, 2)
        
        # Recent activity (last 24 hours)
        activity_query = """
        SELECT 
            COUNT(DISTINCT s.id) as recent_submissions,
            COUNT(DISTINCT g.id) as recent_grades,
            COUNT(DISTINCT u.id) as recent_logins
        FROM submissions s
        FULL OUTER JOIN grades g ON s.id = g.submission_id AND g.created_at >= NOW() - INTERVAL '24 hours'
        FULL OUTER JOIN users u ON u.last_login >= NOW() - INTERVAL '24 hours'
        WHERE s.created_at >= NOW() - INTERVAL '24 hours';
        """
        
        activity_result = await db.execute(text(activity_query))
        activity_row = activity_result.fetchone()
        
        activity_metrics = {
            "recent_submissions_24h": activity_row[0] or 0,
            "recent_grades_24h": activity_row[1] or 0,
            "recent_logins_24h": activity_row[2] or 0
        } if activity_row else {}
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "latency_ms": db_latency,
                "table_counts": table_counts
            },
            "activity": activity_metrics,
            "system": {
                "uptime_seconds": time.process_time(),
                "version": getattr(settings, 'VERSION', 'unknown')
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect metrics"
        )
