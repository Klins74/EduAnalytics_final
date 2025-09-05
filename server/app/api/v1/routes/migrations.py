"""API routes for database migration management."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.migration_manager import migration_manager

router = APIRouter(prefix="/migrations", tags=["Database Migrations"])


class MigrationStatusResponse(BaseModel):
    current_revision: Optional[str]
    pending_migrations: List[Dict[str, Any]]
    total_pending: int
    high_risk_count: int
    backup_available: bool


class DryRunResponse(BaseModel):
    success: bool
    target_revision: str
    migration_output: Optional[str] = None
    error: Optional[str] = None
    message: str


class MigrationResponse(BaseModel):
    success: bool
    revision_id: str
    operation: str
    duration: float
    message: str
    backup_path: Optional[str] = None
    error: Optional[str] = None


class BackupListResponse(BaseModel):
    backups: List[Dict[str, Any]]
    total_count: int


@router.get("/status", response_model=MigrationStatusResponse, summary="Get migration status")
async def get_migration_status(
    current_user: User = Depends(require_role(UserRole.admin))
) -> MigrationStatusResponse:
    """Get current database migration status."""
    try:
        status = await migration_manager.get_migration_status()
        
        if "error" in status:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get migration status: {status['error']}"
            )
        
        return MigrationStatusResponse(
            current_revision=status["current_revision"],
            pending_migrations=status["pending_migrations"],
            total_pending=status["total_pending"],
            high_risk_count=status["high_risk_count"],
            backup_available=status["backup_available"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get migration status: {str(e)}"
        )


@router.post("/dry-run", response_model=DryRunResponse, summary="Perform migration dry run")
async def dry_run_migration(
    target_revision: str = Query("head", description="Target revision for dry run"),
    current_user: User = Depends(require_role(UserRole.admin))
) -> DryRunResponse:
    """Perform a dry run of database migrations without applying changes."""
    try:
        result = await migration_manager.dry_run_migration(target_revision)
        
        return DryRunResponse(
            success=result["success"],
            target_revision=result["target_revision"],
            migration_output=result.get("migration_output"),
            error=result.get("error"),
            message=result["message"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dry run failed: {str(e)}"
        )


@router.post("/upgrade", response_model=MigrationResponse, summary="Upgrade database")
async def upgrade_database(
    target_revision: str = Query("head", description="Target revision"),
    create_backup: bool = Query(True, description="Create backup before migration"),
    force: bool = Query(False, description="Force migration even if high-risk"),
    current_user: User = Depends(require_role(UserRole.admin))
) -> MigrationResponse:
    """Upgrade database to target revision with safety checks."""
    try:
        result = await migration_manager.upgrade_with_safety(
            target_revision=target_revision,
            create_backup=create_backup,
            force=force
        )
        
        if not result.success and not force:
            # If migration failed due to high risk, return 400 instead of 500
            if "High-risk migrations" in result.message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.message
                )
        
        return MigrationResponse(
            success=result.success,
            revision_id=result.revision_id,
            operation=result.operation,
            duration=result.duration,
            message=result.message,
            backup_path=result.backup_path,
            error=result.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.post("/rollback", response_model=MigrationResponse, summary="Rollback database")
async def rollback_database(
    target_revision: str = Query(..., description="Target revision to rollback to"),
    create_backup: bool = Query(True, description="Create backup before rollback"),
    current_user: User = Depends(require_role(UserRole.admin))
) -> MigrationResponse:
    """Rollback database to a specific revision."""
    try:
        result = await migration_manager.rollback_migration(
            target_revision=target_revision,
            create_backup=create_backup
        )
        
        return MigrationResponse(
            success=result.success,
            revision_id=result.revision_id,
            operation=result.operation,
            duration=result.duration,
            message=result.message,
            backup_path=result.backup_path,
            error=result.error
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}"
        )


@router.get("/backups", response_model=BackupListResponse, summary="List database backups")
async def list_backups(
    current_user: User = Depends(require_role(UserRole.admin))
) -> BackupListResponse:
    """List all available database backups."""
    try:
        backups = migration_manager.backup_manager.list_backups()
        
        # Format backup information for response
        formatted_backups = []
        for backup in backups:
            formatted_backups.append({
                "path": backup["path"],
                "revision": backup["revision"],
                "timestamp": backup["timestamp"],
                "size_mb": round(backup["size"] / 1024 / 1024, 2),
                "created_at": backup["created_at"].isoformat()
            })
        
        return BackupListResponse(
            backups=formatted_backups,
            total_count=len(formatted_backups)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.post("/backup", summary="Create database backup")
async def create_backup(
    revision_id: str = Query("current", description="Revision ID for backup naming"),
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Create a manual database backup."""
    try:
        backup_path = await migration_manager.backup_manager.create_backup(revision_id)
        
        return {
            "success": True,
            "backup_path": backup_path,
            "revision_id": revision_id,
            "message": "Backup created successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )


@router.post("/restore", summary="Restore from backup")
async def restore_backup(
    backup_path: str = Query(..., description="Path to backup file"),
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Restore database from a backup file."""
    try:
        success = await migration_manager.backup_manager.restore_backup(backup_path)
        
        if success:
            return {
                "success": True,
                "backup_path": backup_path,
                "message": "Database restored successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Backup restoration failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore backup: {str(e)}"
        )


@router.get("/history", summary="Get migration history")
async def get_migration_history(
    limit: int = Query(50, description="Maximum number of entries to return"),
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Get migration history and revision information."""
    try:
        from alembic import command
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        import io
        import contextlib
        
        # Get Alembic config
        alembic_cfg = Config("server/alembic.ini")
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        
        # Get revision history
        revisions = []
        for revision in script_dir.walk_revisions():
            revisions.append({
                "revision_id": revision.revision,
                "description": revision.doc or "",
                "down_revision": revision.down_revision,
                "branch_labels": revision.branch_labels,
                "depends_on": revision.depends_on,
                "path": revision.path
            })
            
            if len(revisions) >= limit:
                break
        
        # Get current migration status
        status = await migration_manager.get_migration_status()
        
        return {
            "current_revision": status.get("current_revision"),
            "revisions": revisions,
            "total_revisions": len(revisions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get migration history: {str(e)}"
        )


@router.get("/validate", summary="Validate migration integrity")
async def validate_migrations(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Validate migration integrity and consistency."""
    try:
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Get migration status
        status = await migration_manager.get_migration_status()
        
        # Check for high-risk pending migrations
        high_risk_migrations = [
            m for m in status.get("pending_migrations", [])
            if m.get("risk_level") in ["high", "critical"]
        ]
        
        if high_risk_migrations:
            validation_results["warnings"].append({
                "type": "high_risk_migrations",
                "message": f"Found {len(high_risk_migrations)} high-risk pending migrations",
                "details": high_risk_migrations
            })
        
        # Check for migrations without rollback
        no_rollback_migrations = [
            m for m in status.get("pending_migrations", [])
            if not m.get("rollback_available", False)
        ]
        
        if no_rollback_migrations:
            validation_results["warnings"].append({
                "type": "no_rollback_available",
                "message": f"Found {len(no_rollback_migrations)} migrations without rollback capability",
                "details": [m["revision_id"] for m in no_rollback_migrations]
            })
        
        # Check backup availability
        if not status.get("backup_available", False) and status.get("total_pending", 0) > 0:
            validation_results["warnings"].append({
                "type": "no_backup_available",
                "message": "No backups available and pending migrations exist",
                "recommendation": "Create a backup before running migrations"
            })
        
        return validation_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration validation failed: {str(e)}"
        )
