"""
Role-Based Access Control (RBAC) system aligned with Canvas LMS roles.

Provides comprehensive permission management, audit logging, and access control
for all API endpoints and system resources.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import functools

from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, or_

from app.models.user import User, UserRole
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of system resources."""
    USER = "user"
    COURSE = "course"
    ASSIGNMENT = "assignment"
    SUBMISSION = "submission"
    GRADE = "grade"
    ENROLLMENT = "enrollment"
    DISCUSSION = "discussion"
    QUIZ = "quiz"
    MODULE = "module"
    PAGE = "page"
    FILE = "file"
    RUBRIC = "rubric"
    NOTIFICATION = "notification"
    ANALYTICS = "analytics"
    SYSTEM = "system"
    AI_SERVICE = "ai_service"
    ML_MODEL = "ml_model"
    DATA_MART = "data_mart"
    MIGRATION = "migration"


class Action(Enum):
    """Available actions on resources."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    EXECUTE = "execute"
    MANAGE = "manage"
    AUDIT = "audit"
    EXPORT = "export"
    IMPORT = "import"


class ContextType(Enum):
    """Context types for permission evaluation."""
    GLOBAL = "global"
    COURSE = "course"
    ENROLLMENT = "enrollment"
    ASSIGNMENT = "assignment"
    SUBMISSION = "submission"
    SELF = "self"  # Own resources


@dataclass
class Permission:
    """Permission definition."""
    resource_type: ResourceType
    action: Action
    context_type: ContextType = ContextType.GLOBAL
    conditions: Optional[Dict[str, Any]] = None
    description: str = ""


@dataclass
class AccessContext:
    """Context for access control evaluation."""
    user: User
    resource_type: ResourceType
    action: Action
    resource_id: Optional[str] = None
    course_id: Optional[int] = None
    additional_context: Optional[Dict[str, Any]] = None


@dataclass
class AuditLogEntry:
    """Audit log entry for access control events."""
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
    timestamp: datetime
    additional_context: Optional[Dict[str, Any]] = None


class RBACMatrix:
    """RBAC permission matrix aligned with Canvas roles."""
    
    def __init__(self):
        self.permissions_matrix = self._build_permissions_matrix()
    
    def _build_permissions_matrix(self) -> Dict[UserRole, List[Permission]]:
        """Build comprehensive permissions matrix for all roles."""
        
        # Student permissions
        student_permissions = [
            # Own profile and data
            Permission(ResourceType.USER, Action.READ, ContextType.SELF, description="Read own profile"),
            Permission(ResourceType.USER, Action.UPDATE, ContextType.SELF, description="Update own profile"),
            
            # Course access
            Permission(ResourceType.COURSE, Action.READ, ContextType.ENROLLMENT, description="Read enrolled courses"),
            Permission(ResourceType.COURSE, Action.LIST, ContextType.ENROLLMENT, description="List enrolled courses"),
            
            # Assignments
            Permission(ResourceType.ASSIGNMENT, Action.READ, ContextType.ENROLLMENT, description="Read course assignments"),
            Permission(ResourceType.ASSIGNMENT, Action.LIST, ContextType.ENROLLMENT, description="List course assignments"),
            
            # Submissions
            Permission(ResourceType.SUBMISSION, Action.CREATE, ContextType.ENROLLMENT, description="Submit assignments"),
            Permission(ResourceType.SUBMISSION, Action.READ, ContextType.SELF, description="Read own submissions"),
            Permission(ResourceType.SUBMISSION, Action.UPDATE, ContextType.SELF, 
                      conditions={"before_due_date": True}, description="Update own submissions before due date"),
            
            # Grades
            Permission(ResourceType.GRADE, Action.READ, ContextType.SELF, description="Read own grades"),
            
            # Discussions
            Permission(ResourceType.DISCUSSION, Action.READ, ContextType.ENROLLMENT, description="Read course discussions"),
            Permission(ResourceType.DISCUSSION, Action.CREATE, ContextType.ENROLLMENT, description="Create discussion posts"),
            Permission(ResourceType.DISCUSSION, Action.UPDATE, ContextType.SELF, description="Update own posts"),
            
            # Quizzes
            Permission(ResourceType.QUIZ, Action.READ, ContextType.ENROLLMENT, description="Read course quizzes"),
            Permission(ResourceType.QUIZ, Action.EXECUTE, ContextType.ENROLLMENT, description="Take quizzes"),
            
            # Modules and Pages
            Permission(ResourceType.MODULE, Action.READ, ContextType.ENROLLMENT, description="Read course modules"),
            Permission(ResourceType.PAGE, Action.READ, ContextType.ENROLLMENT, description="Read course pages"),
            
            # Files
            Permission(ResourceType.FILE, Action.READ, ContextType.ENROLLMENT, description="Read course files"),
            Permission(ResourceType.FILE, Action.CREATE, ContextType.ENROLLMENT, description="Upload assignment files"),
            
            # Notifications
            Permission(ResourceType.NOTIFICATION, Action.READ, ContextType.SELF, description="Read own notifications"),
            Permission(ResourceType.NOTIFICATION, Action.UPDATE, ContextType.SELF, description="Mark notifications as read"),
            
            # Basic analytics
            Permission(ResourceType.ANALYTICS, Action.READ, ContextType.SELF, description="Read own performance analytics"),
        ]
        
        # Teacher permissions (includes all student permissions plus teaching capabilities)
        teacher_permissions = student_permissions + [
            # User management in courses
            Permission(ResourceType.USER, Action.READ, ContextType.COURSE, description="Read course participants"),
            Permission(ResourceType.USER, Action.LIST, ContextType.COURSE, description="List course participants"),
            
            # Course management
            Permission(ResourceType.COURSE, Action.UPDATE, ContextType.COURSE, description="Update own courses"),
            Permission(ResourceType.COURSE, Action.MANAGE, ContextType.COURSE, description="Manage course settings"),
            
            # Assignment management
            Permission(ResourceType.ASSIGNMENT, Action.CREATE, ContextType.COURSE, description="Create assignments"),
            Permission(ResourceType.ASSIGNMENT, Action.UPDATE, ContextType.COURSE, description="Update assignments"),
            Permission(ResourceType.ASSIGNMENT, Action.DELETE, ContextType.COURSE, description="Delete assignments"),
            
            # Submission management
            Permission(ResourceType.SUBMISSION, Action.READ, ContextType.COURSE, description="Read all course submissions"),
            Permission(ResourceType.SUBMISSION, Action.LIST, ContextType.COURSE, description="List all course submissions"),
            Permission(ResourceType.SUBMISSION, Action.UPDATE, ContextType.COURSE, description="Grade submissions"),
            
            # Grade management
            Permission(ResourceType.GRADE, Action.CREATE, ContextType.COURSE, description="Create grades"),
            Permission(ResourceType.GRADE, Action.UPDATE, ContextType.COURSE, description="Update grades"),
            Permission(ResourceType.GRADE, Action.READ, ContextType.COURSE, description="Read all course grades"),
            Permission(ResourceType.GRADE, Action.EXPORT, ContextType.COURSE, description="Export gradebook"),
            
            # Enrollment management
            Permission(ResourceType.ENROLLMENT, Action.READ, ContextType.COURSE, description="Read course enrollments"),
            Permission(ResourceType.ENROLLMENT, Action.CREATE, ContextType.COURSE, description="Enroll students"),
            Permission(ResourceType.ENROLLMENT, Action.UPDATE, ContextType.COURSE, description="Update enrollment status"),
            
            # Discussion management
            Permission(ResourceType.DISCUSSION, Action.MANAGE, ContextType.COURSE, description="Manage course discussions"),
            Permission(ResourceType.DISCUSSION, Action.DELETE, ContextType.COURSE, description="Delete inappropriate posts"),
            
            # Quiz management
            Permission(ResourceType.QUIZ, Action.CREATE, ContextType.COURSE, description="Create quizzes"),
            Permission(ResourceType.QUIZ, Action.UPDATE, ContextType.COURSE, description="Update quizzes"),
            Permission(ResourceType.QUIZ, Action.DELETE, ContextType.COURSE, description="Delete quizzes"),
            Permission(ResourceType.QUIZ, Action.MANAGE, ContextType.COURSE, description="Manage quiz settings"),
            
            # Module and page management
            Permission(ResourceType.MODULE, Action.CREATE, ContextType.COURSE, description="Create course modules"),
            Permission(ResourceType.MODULE, Action.UPDATE, ContextType.COURSE, description="Update course modules"),
            Permission(ResourceType.MODULE, Action.DELETE, ContextType.COURSE, description="Delete course modules"),
            Permission(ResourceType.PAGE, Action.CREATE, ContextType.COURSE, description="Create course pages"),
            Permission(ResourceType.PAGE, Action.UPDATE, ContextType.COURSE, description="Update course pages"),
            Permission(ResourceType.PAGE, Action.DELETE, ContextType.COURSE, description="Delete course pages"),
            
            # Rubric management
            Permission(ResourceType.RUBRIC, Action.CREATE, ContextType.COURSE, description="Create rubrics"),
            Permission(ResourceType.RUBRIC, Action.UPDATE, ContextType.COURSE, description="Update rubrics"),
            Permission(ResourceType.RUBRIC, Action.DELETE, ContextType.COURSE, description="Delete rubrics"),
            
            # File management
            Permission(ResourceType.FILE, Action.MANAGE, ContextType.COURSE, description="Manage course files"),
            Permission(ResourceType.FILE, Action.DELETE, ContextType.COURSE, description="Delete course files"),
            
            # Notifications
            Permission(ResourceType.NOTIFICATION, Action.CREATE, ContextType.COURSE, description="Send course notifications"),
            
            # Analytics
            Permission(ResourceType.ANALYTICS, Action.READ, ContextType.COURSE, description="Read course analytics"),
            Permission(ResourceType.ANALYTICS, Action.EXPORT, ContextType.COURSE, description="Export course analytics"),
            
            # AI services
            Permission(ResourceType.AI_SERVICE, Action.EXECUTE, ContextType.COURSE, description="Use AI for course analysis"),
        ]
        
        # Admin permissions (includes all teacher permissions plus system administration)
        admin_permissions = teacher_permissions + [
            # Global user management
            Permission(ResourceType.USER, Action.CREATE, ContextType.GLOBAL, description="Create users"),
            Permission(ResourceType.USER, Action.UPDATE, ContextType.GLOBAL, description="Update any user"),
            Permission(ResourceType.USER, Action.DELETE, ContextType.GLOBAL, description="Delete users"),
            Permission(ResourceType.USER, Action.LIST, ContextType.GLOBAL, description="List all users"),
            Permission(ResourceType.USER, Action.AUDIT, ContextType.GLOBAL, description="Audit user activities"),
            
            # Global course management
            Permission(ResourceType.COURSE, Action.CREATE, ContextType.GLOBAL, description="Create courses"),
            Permission(ResourceType.COURSE, Action.UPDATE, ContextType.GLOBAL, description="Update any course"),
            Permission(ResourceType.COURSE, Action.DELETE, ContextType.GLOBAL, description="Delete courses"),
            Permission(ResourceType.COURSE, Action.LIST, ContextType.GLOBAL, description="List all courses"),
            Permission(ResourceType.COURSE, Action.AUDIT, ContextType.GLOBAL, description="Audit course activities"),
            
            # System management
            Permission(ResourceType.SYSTEM, Action.MANAGE, ContextType.GLOBAL, description="Manage system settings"),
            Permission(ResourceType.SYSTEM, Action.AUDIT, ContextType.GLOBAL, description="Access system audit logs"),
            
            # Migration management
            Permission(ResourceType.MIGRATION, Action.EXECUTE, ContextType.GLOBAL, description="Execute database migrations"),
            Permission(ResourceType.MIGRATION, Action.AUDIT, ContextType.GLOBAL, description="Audit migration history"),
            
            # Data mart management
            Permission(ResourceType.DATA_MART, Action.MANAGE, ContextType.GLOBAL, description="Manage data marts"),
            Permission(ResourceType.DATA_MART, Action.EXECUTE, ContextType.GLOBAL, description="Execute ETL jobs"),
            
            # ML model management
            Permission(ResourceType.ML_MODEL, Action.CREATE, ContextType.GLOBAL, description="Create ML models"),
            Permission(ResourceType.ML_MODEL, Action.UPDATE, ContextType.GLOBAL, description="Update ML models"),
            Permission(ResourceType.ML_MODEL, Action.DELETE, ContextType.GLOBAL, description="Delete ML models"),
            Permission(ResourceType.ML_MODEL, Action.EXECUTE, ContextType.GLOBAL, description="Execute ML training"),
            
            # Global analytics
            Permission(ResourceType.ANALYTICS, Action.READ, ContextType.GLOBAL, description="Read global analytics"),
            Permission(ResourceType.ANALYTICS, Action.EXPORT, ContextType.GLOBAL, description="Export all analytics"),
            
            # Global notifications
            Permission(ResourceType.NOTIFICATION, Action.CREATE, ContextType.GLOBAL, description="Send system notifications"),
            Permission(ResourceType.NOTIFICATION, Action.MANAGE, ContextType.GLOBAL, description="Manage notification system"),
            
            # AI service management
            Permission(ResourceType.AI_SERVICE, Action.MANAGE, ContextType.GLOBAL, description="Manage AI services"),
            Permission(ResourceType.AI_SERVICE, Action.AUDIT, ContextType.GLOBAL, description="Audit AI usage"),
        ]
        
        return {
            UserRole.student: student_permissions,
            UserRole.teacher: teacher_permissions,
            UserRole.admin: admin_permissions
        }
    
    def get_role_permissions(self, role: UserRole) -> List[Permission]:
        """Get all permissions for a specific role."""
        return self.permissions_matrix.get(role, [])
    
    def has_permission(self, role: UserRole, resource_type: ResourceType, action: Action, 
                      context_type: ContextType = ContextType.GLOBAL) -> bool:
        """Check if a role has a specific permission."""
        permissions = self.get_role_permissions(role)
        
        for permission in permissions:
            if (permission.resource_type == resource_type and 
                permission.action == action and 
                permission.context_type == context_type):
                return True
        
        return False
    
    def get_permission_matrix_report(self) -> Dict[str, Any]:
        """Generate a comprehensive permission matrix report."""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "roles": {},
            "resources": list(ResourceType.__members__.keys()),
            "actions": list(Action.__members__.keys()),
            "contexts": list(ContextType.__members__.keys())
        }
        
        for role, permissions in self.permissions_matrix.items():
            role_report = {
                "role_name": role.value,
                "permission_count": len(permissions),
                "permissions": []
            }
            
            for permission in permissions:
                role_report["permissions"].append({
                    "resource": permission.resource_type.value,
                    "action": permission.action.value,
                    "context": permission.context_type.value,
                    "conditions": permission.conditions,
                    "description": permission.description
                })
            
            report["roles"][role.value] = role_report
        
        return report


class RBACService:
    """Service for RBAC enforcement and audit logging."""
    
    def __init__(self):
        self.rbac_matrix = RBACMatrix()
    
    async def check_permission(self, context: AccessContext) -> Tuple[bool, str]:
        """Check if user has permission for the requested action."""
        try:
            # Basic role-based check
            has_basic_permission = self.rbac_matrix.has_permission(
                context.user.role,
                context.resource_type,
                context.action,
                ContextType.GLOBAL
            )
            
            if not has_basic_permission:
                # Check context-specific permissions
                if context.course_id:
                    has_course_permission = await self._check_course_permission(context)
                    if has_course_permission:
                        return True, "Course-level permission granted"
                
                if context.action == Action.READ and context.resource_type == ResourceType.USER:
                    # Check if accessing own profile
                    if context.resource_id == str(context.user.id):
                        return True, "Self-access permission granted"
                
                return False, f"Permission denied: {context.user.role.value} cannot {context.action.value} {context.resource_type.value}"
            
            # Check additional conditions
            permission = self._find_matching_permission(context)
            if permission and permission.conditions:
                condition_met, condition_reason = await self._check_conditions(context, permission.conditions)
                if not condition_met:
                    return False, f"Permission condition not met: {condition_reason}"
            
            return True, "Permission granted"
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False, f"Permission check error: {str(e)}"
    
    async def _check_course_permission(self, context: AccessContext) -> bool:
        """Check course-specific permissions."""
        if not context.course_id:
            return False
        
        try:
            async with AsyncSessionLocal() as db:
                # Check if user is enrolled in the course
                enrollment_query = """
                SELECT 1 FROM enrollments 
                WHERE user_id = :user_id AND course_id = :course_id 
                AND status = 'active'
                """
                
                result = await db.execute(text(enrollment_query), {
                    "user_id": context.user.id,
                    "course_id": context.course_id
                })
                
                is_enrolled = result.fetchone() is not None
                
                if is_enrolled:
                    # Check if user has course-level permissions
                    return self.rbac_matrix.has_permission(
                        context.user.role,
                        context.resource_type,
                        context.action,
                        ContextType.COURSE
                    ) or self.rbac_matrix.has_permission(
                        context.user.role,
                        context.resource_type,
                        context.action,
                        ContextType.ENROLLMENT
                    )
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking course permission: {e}")
            return False
    
    def _find_matching_permission(self, context: AccessContext) -> Optional[Permission]:
        """Find the matching permission for the context."""
        permissions = self.rbac_matrix.get_role_permissions(context.user.role)
        
        for permission in permissions:
            if (permission.resource_type == context.resource_type and 
                permission.action == context.action):
                return permission
        
        return None
    
    async def _check_conditions(self, context: AccessContext, conditions: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if permission conditions are met."""
        try:
            for condition_key, condition_value in conditions.items():
                if condition_key == "before_due_date":
                    # Check if current time is before assignment due date
                    if context.resource_type == ResourceType.SUBMISSION:
                        is_before_due = await self._check_before_due_date(context)
                        if not is_before_due:
                            return False, "Submission deadline has passed"
                
                elif condition_key == "own_resource":
                    # Check if user owns the resource
                    if not await self._check_resource_ownership(context):
                        return False, "User does not own this resource"
                
                # Add more condition checks as needed
            
            return True, "All conditions met"
            
        except Exception as e:
            logger.error(f"Error checking conditions: {e}")
            return False, f"Condition check error: {str(e)}"
    
    async def _check_before_due_date(self, context: AccessContext) -> bool:
        """Check if current time is before assignment due date."""
        try:
            async with AsyncSessionLocal() as db:
                query = """
                SELECT a.due_date 
                FROM assignments a
                JOIN submissions s ON a.id = s.assignment_id
                WHERE s.id = :submission_id
                """
                
                result = await db.execute(text(query), {"submission_id": context.resource_id})
                row = result.fetchone()
                
                if row and row.due_date:
                    return datetime.utcnow() < row.due_date
                
                return True  # No due date means always allowed
                
        except Exception as e:
            logger.error(f"Error checking due date: {e}")
            return False
    
    async def _check_resource_ownership(self, context: AccessContext) -> bool:
        """Check if user owns the specified resource."""
        try:
            async with AsyncSessionLocal() as db:
                # Define ownership queries for different resource types
                ownership_queries = {
                    ResourceType.SUBMISSION: "SELECT 1 FROM submissions WHERE id = :resource_id AND student_id = :user_id",
                    ResourceType.USER: "SELECT 1 FROM users WHERE id = :resource_id AND id = :user_id",
                    # Add more resource types as needed
                }
                
                query = ownership_queries.get(context.resource_type)
                if not query:
                    return False
                
                result = await db.execute(text(query), {
                    "resource_id": context.resource_id,
                    "user_id": context.user.id
                })
                
                return result.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Error checking resource ownership: {e}")
            return False
    
    async def log_access_attempt(self, context: AccessContext, granted: bool, reason: str, 
                               request: Optional[Request] = None) -> str:
        """Log access attempt for audit purposes."""
        try:
            import uuid
            
            entry_id = str(uuid.uuid4())
            
            # Extract request information
            ip_address = None
            user_agent = None
            
            if request:
                # Get real IP address (considering proxies)
                ip_address = request.headers.get("x-forwarded-for", 
                           request.headers.get("x-real-ip", 
                           str(request.client.host) if request.client else None))
                user_agent = request.headers.get("user-agent")
            
            audit_entry = AuditLogEntry(
                entry_id=entry_id,
                user_id=context.user.id,
                user_role=context.user.role.value,
                resource_type=context.resource_type.value,
                resource_id=context.resource_id,
                action=context.action.value,
                access_granted=granted,
                reason=reason,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                additional_context=context.additional_context
            )
            
            # Store in database
            await self._store_audit_log(audit_entry)
            
            # Log to application logger
            log_level = logging.INFO if granted else logging.WARNING
            logger.log(log_level, 
                      f"Access {'granted' if granted else 'denied'}: "
                      f"user={context.user.id}({context.user.role.value}) "
                      f"action={context.action.value} "
                      f"resource={context.resource_type.value}({context.resource_id}) "
                      f"reason={reason}")
            
            return entry_id
            
        except Exception as e:
            logger.error(f"Error logging access attempt: {e}")
            return ""
    
    async def _store_audit_log(self, entry: AuditLogEntry):
        """Store audit log entry in database."""
        try:
            async with AsyncSessionLocal() as db:
                # Create audit table if not exists
                await self._create_audit_table(db)
                
                insert_sql = """
                INSERT INTO rbac_audit_log (
                    entry_id, user_id, user_role, resource_type, resource_id,
                    action, access_granted, reason, ip_address, user_agent,
                    timestamp, additional_context
                ) VALUES (
                    :entry_id, :user_id, :user_role, :resource_type, :resource_id,
                    :action, :access_granted, :reason, :ip_address, :user_agent,
                    :timestamp, :additional_context
                )
                """
                
                await db.execute(text(insert_sql), {
                    "entry_id": entry.entry_id,
                    "user_id": entry.user_id,
                    "user_role": entry.user_role,
                    "resource_type": entry.resource_type,
                    "resource_id": entry.resource_id,
                    "action": entry.action,
                    "access_granted": entry.access_granted,
                    "reason": entry.reason,
                    "ip_address": entry.ip_address,
                    "user_agent": entry.user_agent,
                    "timestamp": entry.timestamp,
                    "additional_context": json.dumps(entry.additional_context) if entry.additional_context else None
                })
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error storing audit log: {e}")
    
    async def _create_audit_table(self, db: AsyncSession):
        """Create RBAC audit log table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS rbac_audit_log (
            entry_id VARCHAR(36) PRIMARY KEY,
            user_id INTEGER NOT NULL,
            user_role VARCHAR(20) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(100),
            action VARCHAR(20) NOT NULL,
            access_granted BOOLEAN NOT NULL,
            reason TEXT NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            additional_context JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_rbac_audit_user_id ON rbac_audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_rbac_audit_timestamp ON rbac_audit_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_rbac_audit_resource ON rbac_audit_log(resource_type, resource_id);
        CREATE INDEX IF NOT EXISTS idx_rbac_audit_access_granted ON rbac_audit_log(access_granted);
        """
        
        await db.execute(text(create_table_sql))
    
    async def get_audit_logs(self, 
                           user_id: Optional[int] = None,
                           resource_type: Optional[str] = None,
                           access_granted: Optional[bool] = None,
                           hours: int = 24,
                           limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering."""
        try:
            async with AsyncSessionLocal() as db:
                conditions = ["timestamp >= NOW() - INTERVAL '%s hours'" % hours]
                params = {}
                
                if user_id:
                    conditions.append("user_id = :user_id")
                    params["user_id"] = user_id
                
                if resource_type:
                    conditions.append("resource_type = :resource_type")
                    params["resource_type"] = resource_type
                
                if access_granted is not None:
                    conditions.append("access_granted = :access_granted")
                    params["access_granted"] = access_granted
                
                where_clause = " AND ".join(conditions)
                
                query = f"""
                SELECT entry_id, user_id, user_role, resource_type, resource_id,
                       action, access_granted, reason, ip_address, user_agent,
                       timestamp, additional_context
                FROM rbac_audit_log
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit
                """
                
                params["limit"] = limit
                
                result = await db.execute(text(query), params)
                
                logs = []
                for row in result.fetchall():
                    logs.append({
                        "entry_id": row.entry_id,
                        "user_id": row.user_id,
                        "user_role": row.user_role,
                        "resource_type": row.resource_type,
                        "resource_id": row.resource_id,
                        "action": row.action,
                        "access_granted": row.access_granted,
                        "reason": row.reason,
                        "ip_address": row.ip_address,
                        "user_agent": row.user_agent,
                        "timestamp": row.timestamp.isoformat(),
                        "additional_context": json.loads(row.additional_context) if row.additional_context else None
                    })
                
                return logs
                
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []


# Decorator for automatic permission checking
def require_permission(resource_type: ResourceType, action: Action, 
                      context_type: ContextType = ContextType.GLOBAL):
    """Decorator to require specific permissions for endpoint access."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the current user in function arguments
            current_user = None
            request = None
            
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                elif isinstance(arg, Request):
                    request = arg
            
            if not current_user:
                # Try to find in kwargs
                current_user = kwargs.get('current_user')
                request = kwargs.get('request')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Create access context
            resource_id = kwargs.get('id') or kwargs.get('resource_id')
            course_id = kwargs.get('course_id')
            
            context = AccessContext(
                user=current_user,
                resource_type=resource_type,
                action=action,
                resource_id=str(resource_id) if resource_id else None,
                course_id=course_id,
                additional_context={"endpoint": func.__name__}
            )
            
            # Check permission
            rbac_service = RBACService()
            has_permission, reason = await rbac_service.check_permission(context)
            
            # Log access attempt
            await rbac_service.log_access_attempt(context, has_permission, reason, request)
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=reason
                )
            
            # Execute the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global RBAC service instance
rbac_service = RBACService()
