"""
Database Migration Manager with safety guardrails.

Provides dry-run, rollback, and validation capabilities for Alembic migrations.
"""

import logging
import asyncio
import subprocess
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import re
import tempfile
import shutil

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from alembic.runtime.environment import EnvironmentContext

from app.core.config import settings
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Migration status enumeration."""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationRisk(Enum):
    """Migration risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MigrationInfo:
    """Information about a migration."""
    revision_id: str
    description: str
    down_revision: Optional[str]
    branch_labels: Optional[str]
    depends_on: Optional[str]
    status: MigrationStatus
    risk_level: MigrationRisk
    estimated_duration: Optional[int]  # seconds
    backup_required: bool
    rollback_available: bool


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    revision_id: str
    operation: str
    duration: float
    message: str
    backup_path: Optional[str] = None
    error: Optional[str] = None
    dry_run: bool = False


class DatabaseBackupManager:
    """Manages database backups for migration safety."""
    
    def __init__(self):
        self.backup_dir = Path(settings.UPLOAD_DIRECTORY) / "db_backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_backup(self, revision_id: str) -> str:
        """Create a database backup before migration."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{revision_id}_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Extract connection details from DATABASE_URL
            db_url = str(settings.DATABASE_URL)
            
            # For PostgreSQL
            if "postgresql" in db_url:
                # Parse connection string
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(db_url.replace("postgresql+asyncpg://", "postgresql://"))
                
                pg_dump_cmd = [
                    "pg_dump",
                    "-h", parsed.hostname or "localhost",
                    "-p", str(parsed.port or 5432),
                    "-U", parsed.username or "postgres",
                    "-d", parsed.path[1:] if parsed.path else "postgres",
                    "-f", str(backup_path),
                    "--verbose",
                    "--no-password"
                ]
                
                # Set password via environment if available
                env = {"PGPASSWORD": parsed.password} if parsed.password else {}
                
                process = await asyncio.create_subprocess_exec(
                    *pg_dump_cmd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"Database backup created: {backup_path}")
                    return str(backup_path)
                else:
                    raise Exception(f"pg_dump failed: {stderr.decode()}")
            
            # For SQLite (development)
            elif "sqlite" in db_url:
                db_file = db_url.replace("sqlite+aiosqlite:///", "")
                if Path(db_file).exists():
                    shutil.copy2(db_file, backup_path)
                    logger.info(f"SQLite backup created: {backup_path}")
                    return str(backup_path)
                else:
                    raise Exception(f"SQLite file not found: {db_file}")
            
            else:
                raise Exception(f"Unsupported database type for backup: {db_url}")
                
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            raise
    
    async def restore_backup(self, backup_path: str) -> bool:
        """Restore database from backup."""
        try:
            if not Path(backup_path).exists():
                raise Exception(f"Backup file not found: {backup_path}")
            
            db_url = str(settings.DATABASE_URL)
            
            # For PostgreSQL
            if "postgresql" in db_url:
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(db_url.replace("postgresql+asyncpg://", "postgresql://"))
                
                # Drop and recreate database
                psql_cmd = [
                    "psql",
                    "-h", parsed.hostname or "localhost",
                    "-p", str(parsed.port or 5432),
                    "-U", parsed.username or "postgres",
                    "-d", "postgres",  # Connect to postgres db to drop target
                    "-c", f"DROP DATABASE IF EXISTS {parsed.path[1:]}; CREATE DATABASE {parsed.path[1:]};"
                ]
                
                env = {"PGPASSWORD": parsed.password} if parsed.password else {}
                
                # Drop and recreate
                process = await asyncio.create_subprocess_exec(
                    *psql_cmd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                # Restore from backup
                psql_restore_cmd = [
                    "psql",
                    "-h", parsed.hostname or "localhost",
                    "-p", str(parsed.port or 5432),
                    "-U", parsed.username or "postgres",
                    "-d", parsed.path[1:],
                    "-f", backup_path
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *psql_restore_cmd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"Database restored from backup: {backup_path}")
                    return True
                else:
                    raise Exception(f"psql restore failed: {stderr.decode()}")
            
            # For SQLite
            elif "sqlite" in db_url:
                db_file = db_url.replace("sqlite+aiosqlite:///", "")
                shutil.copy2(backup_path, db_file)
                logger.info(f"SQLite restored from backup: {backup_path}")
                return True
            
            else:
                raise Exception(f"Unsupported database type for restore: {db_url}")
                
        except Exception as e:
            logger.error(f"Failed to restore database backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.sql"):
            try:
                # Parse filename: backup_{revision}_{timestamp}.sql
                parts = backup_file.stem.split("_")
                if len(parts) >= 3:
                    revision = parts[1]
                    timestamp = parts[2]
                    
                    backups.append({
                        "path": str(backup_file),
                        "revision": revision,
                        "timestamp": timestamp,
                        "size": backup_file.stat().st_size,
                        "created_at": datetime.fromtimestamp(backup_file.stat().st_mtime)
                    })
            except Exception as e:
                logger.warning(f"Error parsing backup file {backup_file}: {e}")
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)


class MigrationAnalyzer:
    """Analyzes migrations for risk assessment."""
    
    def __init__(self):
        self.high_risk_operations = [
            "DROP TABLE",
            "DROP COLUMN",
            "DROP INDEX",
            "ALTER COLUMN.*DROP",
            "TRUNCATE",
            "DELETE FROM"
        ]
        
        self.medium_risk_operations = [
            "ALTER TABLE.*ADD COLUMN.*NOT NULL",
            "CREATE INDEX.*CONCURRENTLY",
            "ALTER COLUMN.*TYPE",
            "RENAME TABLE",
            "RENAME COLUMN"
        ]
    
    def analyze_migration(self, revision_id: str) -> MigrationInfo:
        """Analyze a migration for risk and requirements."""
        try:
            # Get Alembic config
            alembic_cfg = Config("server/alembic.ini")
            script_dir = ScriptDirectory.from_config(alembic_cfg)
            
            # Get revision
            revision = script_dir.get_revision(revision_id)
            if not revision:
                raise Exception(f"Revision {revision_id} not found")
            
            # Read migration file
            migration_file = Path(revision.path)
            migration_content = migration_file.read_text()
            
            # Analyze risk
            risk_level = self._assess_risk(migration_content)
            
            # Check if rollback is available
            rollback_available = "def downgrade()" in migration_content and "pass" not in migration_content.split("def downgrade()")[1].split("def")[0]
            
            # Estimate duration (basic heuristic)
            estimated_duration = self._estimate_duration(migration_content)
            
            # Check if backup is required
            backup_required = risk_level in [MigrationRisk.HIGH, MigrationRisk.CRITICAL]
            
            return MigrationInfo(
                revision_id=revision_id,
                description=revision.doc or "",
                down_revision=revision.down_revision,
                branch_labels=revision.branch_labels,
                depends_on=revision.depends_on,
                status=MigrationStatus.PENDING,
                risk_level=risk_level,
                estimated_duration=estimated_duration,
                backup_required=backup_required,
                rollback_available=rollback_available
            )
            
        except Exception as e:
            logger.error(f"Error analyzing migration {revision_id}: {e}")
            # Return safe defaults
            return MigrationInfo(
                revision_id=revision_id,
                description="Unknown migration",
                down_revision=None,
                branch_labels=None,
                depends_on=None,
                status=MigrationStatus.PENDING,
                risk_level=MigrationRisk.HIGH,  # Assume high risk if can't analyze
                estimated_duration=60,
                backup_required=True,
                rollback_available=False
            )
    
    def _assess_risk(self, migration_content: str) -> MigrationRisk:
        """Assess risk level of migration based on content."""
        content_upper = migration_content.upper()
        
        # Check for high-risk operations
        for operation in self.high_risk_operations:
            if re.search(operation, content_upper):
                return MigrationRisk.CRITICAL
        
        # Check for medium-risk operations
        for operation in self.medium_risk_operations:
            if re.search(operation, content_upper):
                return MigrationRisk.MEDIUM
        
        # Check for bulk data operations
        if any(keyword in content_upper for keyword in ["INSERT INTO", "UPDATE.*SET", "BULK", "BATCH"]):
            return MigrationRisk.MEDIUM
        
        # Default to low risk for simple operations
        return MigrationRisk.LOW
    
    def _estimate_duration(self, migration_content: str) -> int:
        """Estimate migration duration in seconds."""
        content_upper = migration_content.upper()
        
        # Base duration
        duration = 10
        
        # Add time for different operations
        if "CREATE INDEX" in content_upper:
            duration += 30
        if "ALTER TABLE" in content_upper:
            duration += 20
        if "INSERT INTO" in content_upper or "UPDATE" in content_upper:
            duration += 60
        if "DROP" in content_upper:
            duration += 15
        
        # Add time for each operation
        operation_count = len(re.findall(r'op\.[a-z_]+\(', migration_content))
        duration += operation_count * 5
        
        return min(duration, 300)  # Cap at 5 minutes


class MigrationManager:
    """Main migration manager with safety features."""
    
    def __init__(self):
        self.backup_manager = DatabaseBackupManager()
        self.analyzer = MigrationAnalyzer()
        self.alembic_cfg = Config("server/alembic.ini")
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        try:
            # Get current revision
            engine = create_async_engine(str(settings.DATABASE_URL))
            
            async with engine.connect() as connection:
                def get_current_revision(conn):
                    context = MigrationContext.configure(conn)
                    return context.get_current_revision()
                
                current_revision = await connection.run_sync(get_current_revision)
            
            await engine.dispose()
            
            # Get pending migrations
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            
            if current_revision:
                pending_revisions = list(script_dir.walk_revisions(current_revision, "head"))
                # Remove current revision from pending
                pending_revisions = [rev for rev in pending_revisions if rev.revision != current_revision]
            else:
                # No migrations applied yet
                pending_revisions = list(script_dir.walk_revisions("base", "head"))
            
            # Analyze pending migrations
            pending_migrations = []
            for revision in pending_revisions:
                migration_info = self.analyzer.analyze_migration(revision.revision)
                pending_migrations.append({
                    "revision_id": migration_info.revision_id,
                    "description": migration_info.description,
                    "risk_level": migration_info.risk_level.value,
                    "estimated_duration": migration_info.estimated_duration,
                    "backup_required": migration_info.backup_required,
                    "rollback_available": migration_info.rollback_available
                })
            
            return {
                "current_revision": current_revision,
                "pending_migrations": pending_migrations,
                "total_pending": len(pending_migrations),
                "high_risk_count": len([m for m in pending_migrations if m["risk_level"] in ["high", "critical"]]),
                "backup_available": len(self.backup_manager.list_backups()) > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting migration status: {e}")
            return {
                "error": str(e),
                "current_revision": None,
                "pending_migrations": [],
                "total_pending": 0,
                "high_risk_count": 0,
                "backup_available": False
            }
    
    async def dry_run_migration(self, target_revision: str = "head") -> Dict[str, Any]:
        """Perform a dry run of migrations."""
        try:
            # Create temporary database for dry run
            temp_db_url = await self._create_temp_database()
            
            # Copy current database schema to temp database
            await self._copy_schema_to_temp(temp_db_url)
            
            # Run migrations on temp database
            temp_alembic_cfg = self._create_temp_alembic_config(temp_db_url)
            
            # Capture Alembic output
            import io
            import contextlib
            
            output_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(output_buffer):
                command.upgrade(temp_alembic_cfg, target_revision)
            
            migration_output = output_buffer.getvalue()
            
            # Clean up temp database
            await self._cleanup_temp_database(temp_db_url)
            
            return {
                "success": True,
                "target_revision": target_revision,
                "migration_output": migration_output,
                "message": "Dry run completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Dry run failed: {e}")
            return {
                "success": False,
                "target_revision": target_revision,
                "error": str(e),
                "message": "Dry run failed"
            }
    
    async def upgrade_with_safety(
        self, 
        target_revision: str = "head",
        create_backup: bool = True,
        force: bool = False
    ) -> MigrationResult:
        """Upgrade database with safety checks."""
        start_time = datetime.utcnow()
        backup_path = None
        
        try:
            # Get migration info
            status = await self.get_migration_status()
            pending_migrations = status.get("pending_migrations", [])
            
            if not pending_migrations:
                return MigrationResult(
                    success=True,
                    revision_id=target_revision,
                    operation="upgrade",
                    duration=0,
                    message="No pending migrations"
                )
            
            # Check for high-risk migrations
            high_risk_migrations = [m for m in pending_migrations if m["risk_level"] in ["high", "critical"]]
            
            if high_risk_migrations and not force:
                return MigrationResult(
                    success=False,
                    revision_id=target_revision,
                    operation="upgrade",
                    duration=0,
                    message=f"High-risk migrations detected. Use force=True to proceed. Risky migrations: {[m['revision_id'] for m in high_risk_migrations]}",
                    error="High-risk migrations require confirmation"
                )
            
            # Create backup if required
            if create_backup or any(m["backup_required"] for m in pending_migrations):
                backup_path = await self.backup_manager.create_backup(target_revision)
            
            # Perform dry run first
            dry_run_result = await self.dry_run_migration(target_revision)
            if not dry_run_result["success"]:
                return MigrationResult(
                    success=False,
                    revision_id=target_revision,
                    operation="upgrade",
                    duration=0,
                    message="Dry run failed, aborting migration",
                    error=dry_run_result.get("error"),
                    backup_path=backup_path
                )
            
            # Run actual migration
            command.upgrade(self.alembic_cfg, target_revision)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return MigrationResult(
                success=True,
                revision_id=target_revision,
                operation="upgrade",
                duration=duration,
                message=f"Migration to {target_revision} completed successfully",
                backup_path=backup_path
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Migration failed: {e}")
            
            return MigrationResult(
                success=False,
                revision_id=target_revision,
                operation="upgrade",
                duration=duration,
                message="Migration failed",
                error=str(e),
                backup_path=backup_path
            )
    
    async def rollback_migration(
        self, 
        target_revision: str,
        create_backup: bool = True
    ) -> MigrationResult:
        """Rollback to a specific revision."""
        start_time = datetime.utcnow()
        backup_path = None
        
        try:
            # Create backup before rollback
            if create_backup:
                backup_path = await self.backup_manager.create_backup(f"rollback_{target_revision}")
            
            # Perform rollback
            command.downgrade(self.alembic_cfg, target_revision)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return MigrationResult(
                success=True,
                revision_id=target_revision,
                operation="rollback",
                duration=duration,
                message=f"Rollback to {target_revision} completed successfully",
                backup_path=backup_path
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Rollback failed: {e}")
            
            return MigrationResult(
                success=False,
                revision_id=target_revision,
                operation="rollback",
                duration=duration,
                message="Rollback failed",
                error=str(e),
                backup_path=backup_path
            )
    
    async def _create_temp_database(self) -> str:
        """Create a temporary database for dry runs."""
        import uuid
        temp_db_name = f"temp_migration_{uuid.uuid4().hex[:8]}"
        
        # For PostgreSQL
        if "postgresql" in str(settings.DATABASE_URL):
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(str(settings.DATABASE_URL).replace("postgresql+asyncpg://", "postgresql://"))
            
            # Create temp database
            temp_db_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{temp_db_name}"
            
            # Connect to postgres database to create temp database
            postgres_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
            
            engine = create_engine(postgres_url)
            with engine.connect() as connection:
                connection.execute(text("COMMIT"))  # End any existing transaction
                connection.execute(text(f"CREATE DATABASE {temp_db_name}"))
            engine.dispose()
            
            return temp_db_url.replace("postgresql://", "postgresql+asyncpg://")
        
        # For SQLite
        else:
            temp_file = Path(tempfile.gettempdir()) / f"{temp_db_name}.db"
            return f"sqlite+aiosqlite:///{temp_file}"
    
    async def _copy_schema_to_temp(self, temp_db_url: str):
        """Copy current database schema to temporary database."""
        # This is a simplified version - in production you might want to use pg_dump/restore
        source_engine = create_async_engine(str(settings.DATABASE_URL))
        temp_engine = create_async_engine(temp_db_url)
        
        # For now, just run the initial migration to create base schema
        temp_alembic_cfg = self._create_temp_alembic_config(temp_db_url)
        
        # Get current revision and apply all migrations up to that point
        async with source_engine.connect() as connection:
            def get_current_revision(conn):
                context = MigrationContext.configure(conn)
                return context.get_current_revision()
            
            current_revision = await connection.run_sync(get_current_revision)
        
        if current_revision:
            command.upgrade(temp_alembic_cfg, current_revision)
        
        await source_engine.dispose()
        await temp_engine.dispose()
    
    def _create_temp_alembic_config(self, temp_db_url: str) -> Config:
        """Create Alembic config for temporary database."""
        temp_config = Config("server/alembic.ini")
        temp_config.set_main_option("sqlalchemy.url", temp_db_url)
        return temp_config
    
    async def _cleanup_temp_database(self, temp_db_url: str):
        """Clean up temporary database."""
        if "postgresql" in temp_db_url:
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(temp_db_url.replace("postgresql+asyncpg://", "postgresql://"))
            temp_db_name = parsed.path[1:]  # Remove leading slash
            
            # Connect to postgres database to drop temp database
            postgres_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
            
            engine = create_engine(postgres_url)
            with engine.connect() as connection:
                connection.execute(text("COMMIT"))  # End any existing transaction
                # Terminate any connections to the temp database
                connection.execute(text(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{temp_db_name}' AND pid <> pg_backend_pid()
                """))
                connection.execute(text(f"DROP DATABASE IF EXISTS {temp_db_name}"))
            engine.dispose()
        
        elif "sqlite" in temp_db_url:
            db_file = temp_db_url.replace("sqlite+aiosqlite:///", "")
            Path(db_file).unlink(missing_ok=True)


# Global migration manager instance
migration_manager = MigrationManager()
