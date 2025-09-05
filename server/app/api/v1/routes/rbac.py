"""API routes for RBAC management and audit logging."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.core.rbac import (
    rbac_service, 
    ResourceType, 
    Action, 
    ContextType,
    AccessContext,
    require_permission
)

router = APIRouter(prefix="/rbac", tags=["RBAC & Audit"])


class PermissionCheckRequest(BaseModel):
    """Request model for permission checking."""
    resource_type: str
    action: str
    resource_id: Optional[str] = None
    course_id: Optional[int] = None
    context_type: str = "global"


class PermissionCheckResponse(BaseModel):
    """Response model for permission checking."""
    has_permission: bool
    reason: str
    user_role: str
    resource_type: str
    action: str


class AuditLogResponse(BaseModel):
    """Response model for audit log entries."""
    entry_id: str
    user_id: int
    user_role: str
    resource_type: str
    resource_id: Optional[str]
    action: str
    access_granted: bool
    reason: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: str
    additional_context: Optional[Dict[str, Any]]


class PermissionMatrixResponse(BaseModel):
    """Response model for permission matrix."""
    generated_at: str
    roles: Dict[str, Any]
    resources: List[str]
    actions: List[str]
    contexts: List[str]


class AuditStatsResponse(BaseModel):
    """Response model for audit statistics."""
    total_attempts: int
    granted_attempts: int
    denied_attempts: int
    success_rate: float
    top_users: List[Dict[str, Any]]
    top_resources: List[Dict[str, Any]]
    top_actions: List[Dict[str, Any]]
    denied_attempts_by_reason: Dict[str, int]


@router.get("/permissions/matrix", response_model=PermissionMatrixResponse, summary="Get RBAC permission matrix")
@require_permission(ResourceType.SYSTEM, Action.AUDIT)
async def get_permission_matrix(
    current_user: User = Depends(require_role(UserRole.admin))
) -> PermissionMatrixResponse:
    """Get the complete RBAC permission matrix."""
    try:
        matrix_report = rbac_service.rbac_matrix.get_permission_matrix_report()
        
        return PermissionMatrixResponse(
            generated_at=matrix_report["generated_at"],
            roles=matrix_report["roles"],
            resources=matrix_report["resources"],
            actions=matrix_report["actions"],
            contexts=matrix_report["contexts"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get permission matrix: {str(e)}"
        )


@router.post("/permissions/check", response_model=PermissionCheckResponse, summary="Check user permissions")
async def check_user_permission(
    request: PermissionCheckRequest,
    current_user: User = Depends(get_current_user)
) -> PermissionCheckResponse:
    """Check if current user has specific permissions."""
    try:
        # Validate resource type and action
        try:
            resource_type = ResourceType(request.resource_type)
            action = Action(request.action)
            context_type = ContextType(request.context_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid parameter: {str(e)}"
            )
        
        # Create access context
        context = AccessContext(
            user=current_user,
            resource_type=resource_type,
            action=action,
            resource_id=request.resource_id,
            course_id=request.course_id,
            additional_context={"check_type": "api_request"}
        )
        
        # Check permission
        has_permission, reason = await rbac_service.check_permission(context)
        
        return PermissionCheckResponse(
            has_permission=has_permission,
            reason=reason,
            user_role=current_user.role.value,
            resource_type=request.resource_type,
            action=request.action
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )


@router.get("/audit/logs", response_model=List[AuditLogResponse], summary="Get audit logs")
@require_permission(ResourceType.SYSTEM, Action.AUDIT)
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    access_granted: Optional[bool] = Query(None, description="Filter by access result"),
    hours: int = Query(24, description="Time period in hours"),
    limit: int = Query(1000, description="Maximum number of entries"),
    current_user: User = Depends(require_role(UserRole.admin))
) -> List[AuditLogResponse]:
    """Get audit logs with optional filtering."""
    try:
        logs = await rbac_service.get_audit_logs(
            user_id=user_id,
            resource_type=resource_type,
            access_granted=access_granted,
            hours=hours,
            limit=limit
        )
        
        return [
            AuditLogResponse(
                entry_id=log["entry_id"],
                user_id=log["user_id"],
                user_role=log["user_role"],
                resource_type=log["resource_type"],
                resource_id=log["resource_id"],
                action=log["action"],
                access_granted=log["access_granted"],
                reason=log["reason"],
                ip_address=log["ip_address"],
                user_agent=log["user_agent"],
                timestamp=log["timestamp"],
                additional_context=log["additional_context"]
            )
            for log in logs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}"
        )


@router.get("/audit/stats", response_model=AuditStatsResponse, summary="Get audit statistics")
@require_permission(ResourceType.SYSTEM, Action.AUDIT)
async def get_audit_stats(
    hours: int = Query(24, description="Time period in hours"),
    current_user: User = Depends(require_role(UserRole.admin))
) -> AuditStatsResponse:
    """Get audit statistics and analytics."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Basic stats
            basic_stats_query = """
            SELECT 
                COUNT(*) as total_attempts,
                COUNT(CASE WHEN access_granted = true THEN 1 END) as granted_attempts,
                COUNT(CASE WHEN access_granted = false THEN 1 END) as denied_attempts
            FROM rbac_audit_log
            WHERE timestamp >= :since_time
            """
            
            result = await db.execute(text(basic_stats_query), {"since_time": since_time})
            stats = dict(result.fetchone()._mapping)
            
            success_rate = 0.0
            if stats["total_attempts"] > 0:
                success_rate = (stats["granted_attempts"] / stats["total_attempts"]) * 100
            
            # Top users by activity
            top_users_query = """
            SELECT 
                user_id,
                user_role,
                COUNT(*) as attempt_count,
                COUNT(CASE WHEN access_granted = false THEN 1 END) as denied_count
            FROM rbac_audit_log
            WHERE timestamp >= :since_time
            GROUP BY user_id, user_role
            ORDER BY attempt_count DESC
            LIMIT 10
            """
            
            result = await db.execute(text(top_users_query), {"since_time": since_time})
            top_users = [
                {
                    "user_id": row.user_id,
                    "user_role": row.user_role,
                    "attempt_count": row.attempt_count,
                    "denied_count": row.denied_count,
                    "success_rate": ((row.attempt_count - row.denied_count) / row.attempt_count * 100) if row.attempt_count > 0 else 0
                }
                for row in result.fetchall()
            ]
            
            # Top resources accessed
            top_resources_query = """
            SELECT 
                resource_type,
                COUNT(*) as access_count,
                COUNT(CASE WHEN access_granted = false THEN 1 END) as denied_count
            FROM rbac_audit_log
            WHERE timestamp >= :since_time
            GROUP BY resource_type
            ORDER BY access_count DESC
            LIMIT 10
            """
            
            result = await db.execute(text(top_resources_query), {"since_time": since_time})
            top_resources = [
                {
                    "resource_type": row.resource_type,
                    "access_count": row.access_count,
                    "denied_count": row.denied_count,
                    "success_rate": ((row.access_count - row.denied_count) / row.access_count * 100) if row.access_count > 0 else 0
                }
                for row in result.fetchall()
            ]
            
            # Top actions
            top_actions_query = """
            SELECT 
                action,
                COUNT(*) as action_count,
                COUNT(CASE WHEN access_granted = false THEN 1 END) as denied_count
            FROM rbac_audit_log
            WHERE timestamp >= :since_time
            GROUP BY action
            ORDER BY action_count DESC
            LIMIT 10
            """
            
            result = await db.execute(text(top_actions_query), {"since_time": since_time})
            top_actions = [
                {
                    "action": row.action,
                    "action_count": row.action_count,
                    "denied_count": row.denied_count,
                    "success_rate": ((row.action_count - row.denied_count) / row.action_count * 100) if row.action_count > 0 else 0
                }
                for row in result.fetchall()
            ]
            
            # Denied attempts by reason
            denied_reasons_query = """
            SELECT 
                reason,
                COUNT(*) as count
            FROM rbac_audit_log
            WHERE timestamp >= :since_time
            AND access_granted = false
            GROUP BY reason
            ORDER BY count DESC
            """
            
            result = await db.execute(text(denied_reasons_query), {"since_time": since_time})
            denied_by_reason = {row.reason: row.count for row in result.fetchall()}
        
        return AuditStatsResponse(
            total_attempts=stats["total_attempts"],
            granted_attempts=stats["granted_attempts"],
            denied_attempts=stats["denied_attempts"],
            success_rate=round(success_rate, 2),
            top_users=top_users,
            top_resources=top_resources,
            top_actions=top_actions,
            denied_attempts_by_reason=denied_by_reason
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit statistics: {str(e)}"
        )


@router.get("/roles/{role}/permissions", summary="Get role permissions")
async def get_role_permissions(
    role: str,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Get all permissions for a specific role."""
    try:
        # Validate role
        try:
            user_role = UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
        
        permissions = rbac_service.rbac_matrix.get_role_permissions(user_role)
        
        # Group permissions by resource type
        permissions_by_resource = {}
        
        for permission in permissions:
            resource = permission.resource_type.value
            if resource not in permissions_by_resource:
                permissions_by_resource[resource] = []
            
            permissions_by_resource[resource].append({
                "action": permission.action.value,
                "context": permission.context_type.value,
                "conditions": permission.conditions,
                "description": permission.description
            })
        
        return {
            "role": role,
            "total_permissions": len(permissions),
            "permissions_by_resource": permissions_by_resource,
            "resource_count": len(permissions_by_resource)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get role permissions: {str(e)}"
        )


@router.get("/users/{user_id}/permissions", summary="Get user effective permissions")
@require_permission(ResourceType.USER, Action.AUDIT)
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Get effective permissions for a specific user."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Get user information
            user_query = "SELECT id, role FROM users WHERE id = :user_id"
            result = await db.execute(text(user_query), {"user_id": user_id})
            user_row = result.fetchone()
            
            if not user_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user_role = UserRole(user_row.role)
            permissions = rbac_service.rbac_matrix.get_role_permissions(user_role)
            
            # Get user's course enrollments for context-specific permissions
            enrollments_query = """
            SELECT c.id as course_id, c.name as course_name, e.role as enrollment_role
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.user_id = :user_id AND e.status = 'active'
            """
            
            result = await db.execute(text(enrollments_query), {"user_id": user_id})
            enrollments = [dict(row._mapping) for row in result.fetchall()]
            
            # Recent access attempts
            recent_access_query = """
            SELECT resource_type, action, access_granted, timestamp
            FROM rbac_audit_log
            WHERE user_id = :user_id
            ORDER BY timestamp DESC
            LIMIT 20
            """
            
            result = await db.execute(text(recent_access_query), {"user_id": user_id})
            recent_access = [dict(row._mapping) for row in result.fetchall()]
        
        return {
            "user_id": user_id,
            "role": user_role.value,
            "total_permissions": len(permissions),
            "permissions": [
                {
                    "resource": p.resource_type.value,
                    "action": p.action.value,
                    "context": p.context_type.value,
                    "conditions": p.conditions,
                    "description": p.description
                }
                for p in permissions
            ],
            "course_enrollments": enrollments,
            "recent_access_attempts": [
                {
                    "resource_type": access["resource_type"],
                    "action": access["action"],
                    "access_granted": access["access_granted"],
                    "timestamp": access["timestamp"].isoformat()
                }
                for access in recent_access
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user permissions: {str(e)}"
        )


@router.post("/audit/test-access", summary="Test access control (for testing)")
async def test_access_control(
    resource_type: str,
    action: str,
    resource_id: Optional[str] = None,
    course_id: Optional[int] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test access control for debugging purposes."""
    try:
        # Validate parameters
        try:
            resource_type_enum = ResourceType(resource_type)
            action_enum = Action(action)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid parameter: {str(e)}"
            )
        
        # Create access context
        context = AccessContext(
            user=current_user,
            resource_type=resource_type_enum,
            action=action_enum,
            resource_id=resource_id,
            course_id=course_id,
            additional_context={"test_access": True}
        )
        
        # Check permission
        has_permission, reason = await rbac_service.check_permission(context)
        
        # Log the test access
        entry_id = await rbac_service.log_access_attempt(context, has_permission, reason, request)
        
        return {
            "has_permission": has_permission,
            "reason": reason,
            "user_id": current_user.id,
            "user_role": current_user.role.value,
            "resource_type": resource_type,
            "action": action,
            "resource_id": resource_id,
            "course_id": course_id,
            "audit_entry_id": entry_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test access control: {str(e)}"
        )


@router.get("/health", summary="RBAC system health check")
async def rbac_health_check(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Check RBAC system health and configuration."""
    try:
        # Basic system checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check RBAC matrix
        try:
            matrix_report = rbac_service.rbac_matrix.get_permission_matrix_report()
            health_status["checks"]["permission_matrix"] = {
                "status": "ok",
                "roles_count": len(matrix_report["roles"]),
                "resources_count": len(matrix_report["resources"]),
                "actions_count": len(matrix_report["actions"])
            }
        except Exception as e:
            health_status["checks"]["permission_matrix"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check audit log table
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as db:
                # Check if audit table exists and is accessible
                result = await db.execute(text("SELECT COUNT(*) FROM rbac_audit_log WHERE timestamp >= NOW() - INTERVAL '1 hour'"))
                recent_logs = result.scalar()
                
                health_status["checks"]["audit_logging"] = {
                    "status": "ok",
                    "recent_logs_count": recent_logs
                }
        except Exception as e:
            health_status["checks"]["audit_logging"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check current user permissions
        try:
            user_permissions = rbac_service.rbac_matrix.get_role_permissions(current_user.role)
            health_status["checks"]["user_permissions"] = {
                "status": "ok",
                "user_role": current_user.role.value,
                "permissions_count": len(user_permissions)
            }
        except Exception as e:
            health_status["checks"]["user_permissions"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RBAC health check failed: {str(e)}"
        )
