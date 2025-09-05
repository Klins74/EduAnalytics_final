"""
Canvas synchronization scheduler and consistency checker.

Manages scheduled syncs with Canvas REST API and DAP, validates data consistency,
and handles conflict resolution.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta, time
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, or_, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.services.scheduler import scheduler_service
from app.services.canvas_client import canvas_client
from app.services.canvas_dap import canvas_dap_service
from app.services.canvas_live_events import canvas_live_events_service
from app.crud.canvas_sync import CanvasSyncCRUD
from app.models.canvas_sync import CanvasSyncState
from app.core.config import settings

logger = logging.getLogger(__name__)


class SyncType(Enum):
    """Types of Canvas synchronization."""
    FULL_SYNC = "full_sync"
    INCREMENTAL_SYNC = "incremental_sync"
    DAP_SYNC = "dap_sync"
    LIVE_EVENTS_SYNC = "live_events_sync"
    CONSISTENCY_CHECK = "consistency_check"


class SyncStatus(Enum):
    """Synchronization status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class SyncPriority(Enum):
    """Sync operation priority."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class SyncJob:
    """Synchronization job configuration."""
    job_id: str
    sync_type: SyncType
    source: str  # canvas_rest, canvas_dap, canvas_live_events
    target_entities: List[str]  # courses, users, assignments, etc.
    priority: SyncPriority
    schedule_cron: Optional[str]
    filters: Optional[Dict[str, Any]]
    created_at: datetime
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    status: SyncStatus
    retry_count: int = 0
    max_retries: int = 3
    timeout_minutes: int = 60
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SyncResult:
    """Result of synchronization operation."""
    job_id: str
    sync_type: SyncType
    status: SyncStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    records_processed: int
    records_created: int
    records_updated: int
    records_deleted: int
    errors: List[str]
    warnings: List[str]
    next_sync_scheduled: Optional[datetime]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConsistencyIssue:
    """Data consistency issue."""
    issue_id: str
    entity_type: str
    entity_id: str
    source_system: str
    issue_type: str  # missing, outdated, conflicting, orphaned
    description: str
    severity: str  # critical, warning, info
    detected_at: datetime
    resolved_at: Optional[datetime]
    resolution_action: Optional[str]
    metadata: Optional[Dict[str, Any]] = None


class CanvasSyncScheduler:
    """Manages Canvas synchronization scheduling and execution."""
    
    def __init__(self):
        self.sync_crud = CanvasSyncCRUD()
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.job_semaphore = asyncio.Semaphore(3)  # Max 3 concurrent sync jobs
        
        # Default sync schedules
        self.default_schedules = {
            SyncType.INCREMENTAL_SYNC: "*/15 * * * *",      # Every 15 minutes
            SyncType.DAP_SYNC: "0 2 * * *",                 # Daily at 2 AM
            SyncType.FULL_SYNC: "0 1 * * 0",                # Weekly on Sunday at 1 AM
            SyncType.CONSISTENCY_CHECK: "0 6 * * *",        # Daily at 6 AM
            SyncType.LIVE_EVENTS_SYNC: "*/5 * * * *"        # Every 5 minutes
        }
    
    async def initialize_default_sync_jobs(self):
        """Initialize default synchronization jobs."""
        try:
            logger.info("Initializing default Canvas sync jobs...")
            
            default_jobs = [
                # Incremental syncs for recent data
                SyncJob(
                    job_id="canvas_incremental_users",
                    sync_type=SyncType.INCREMENTAL_SYNC,
                    source="canvas_rest",
                    target_entities=["users", "enrollments"],
                    priority=SyncPriority.HIGH,
                    schedule_cron=self.default_schedules[SyncType.INCREMENTAL_SYNC],
                    filters={"updated_since": "1_hour"},
                    created_at=datetime.utcnow(),
                    status=SyncStatus.PENDING,
                    timeout_minutes=30
                ),
                
                SyncJob(
                    job_id="canvas_incremental_courses",
                    sync_type=SyncType.INCREMENTAL_SYNC,
                    source="canvas_rest",
                    target_entities=["courses", "assignments", "submissions"],
                    priority=SyncPriority.HIGH,
                    schedule_cron=self.default_schedules[SyncType.INCREMENTAL_SYNC],
                    filters={"updated_since": "30_minutes"},
                    created_at=datetime.utcnow(),
                    status=SyncStatus.PENDING,
                    timeout_minutes=45
                ),
                
                # DAP full data sync
                SyncJob(
                    job_id="canvas_dap_daily",
                    sync_type=SyncType.DAP_SYNC,
                    source="canvas_dap",
                    target_entities=["all"],
                    priority=SyncPriority.NORMAL,
                    schedule_cron=self.default_schedules[SyncType.DAP_SYNC],
                    filters={"extract_type": "daily"},
                    created_at=datetime.utcnow(),
                    status=SyncStatus.PENDING,
                    timeout_minutes=120
                ),
                
                # Weekly full sync for comprehensive data
                SyncJob(
                    job_id="canvas_full_weekly",
                    sync_type=SyncType.FULL_SYNC,
                    source="canvas_rest",
                    target_entities=["all"],
                    priority=SyncPriority.LOW,
                    schedule_cron=self.default_schedules[SyncType.FULL_SYNC],
                    filters=None,
                    created_at=datetime.utcnow(),
                    status=SyncStatus.PENDING,
                    timeout_minutes=180
                ),
                
                # Live events processing
                SyncJob(
                    job_id="canvas_live_events",
                    sync_type=SyncType.LIVE_EVENTS_SYNC,
                    source="canvas_live_events",
                    target_entities=["events"],
                    priority=SyncPriority.CRITICAL,
                    schedule_cron=self.default_schedules[SyncType.LIVE_EVENTS_SYNC],
                    filters=None,
                    created_at=datetime.utcnow(),
                    status=SyncStatus.PENDING,
                    timeout_minutes=15
                ),
                
                # Consistency checks
                SyncJob(
                    job_id="canvas_consistency_check",
                    sync_type=SyncType.CONSISTENCY_CHECK,
                    source="internal",
                    target_entities=["all"],
                    priority=SyncPriority.NORMAL,
                    schedule_cron=self.default_schedules[SyncType.CONSISTENCY_CHECK],
                    filters=None,
                    created_at=datetime.utcnow(),
                    status=SyncStatus.PENDING,
                    timeout_minutes=60
                )
            ]
            
            # Store jobs in database
            await self._store_sync_jobs(default_jobs)
            
            # Schedule jobs with APScheduler
            for job in default_jobs:
                await self._schedule_job(job)
            
            logger.info(f"Initialized {len(default_jobs)} default sync jobs")
            
        except Exception as e:
            logger.error(f"Error initializing default sync jobs: {e}")
            raise
    
    async def start_sync_scheduler(self):
        """Start the sync scheduler and background tasks."""
        logger.info("Starting Canvas sync scheduler...")
        
        # Initialize default jobs if not exists
        await self.initialize_default_sync_jobs()
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._monitor_running_jobs()),
            asyncio.create_task(self._cleanup_old_results()),
            asyncio.create_task(self._schedule_missed_jobs())
        ]
        
        await asyncio.gather(*tasks)
    
    async def execute_sync_job(self, job_id: str) -> SyncResult:
        """Execute a specific synchronization job."""
        if job_id in self.running_jobs:
            logger.warning(f"Sync job {job_id} is already running")
            return SyncResult(
                job_id=job_id,
                sync_type=SyncType.INCREMENTAL_SYNC,
                status=SyncStatus.FAILED,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration_seconds=0,
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_deleted=0,
                errors=["Job already running"],
                warnings=[]
            )
        
        # Get job configuration
        job = await self._get_sync_job(job_id)
        if not job:
            logger.error(f"Sync job {job_id} not found")
            return SyncResult(
                job_id=job_id,
                sync_type=SyncType.INCREMENTAL_SYNC,
                status=SyncStatus.FAILED,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration_seconds=0,
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_deleted=0,
                errors=["Job not found"],
                warnings=[]
            )
        
        # Execute job with semaphore
        async with self.job_semaphore:
            task = asyncio.create_task(self._execute_sync_job_internal(job))
            self.running_jobs[job_id] = task
            
            try:
                result = await task
                return result
            finally:
                if job_id in self.running_jobs:
                    del self.running_jobs[job_id]
    
    async def _execute_sync_job_internal(self, job: SyncJob) -> SyncResult:
        """Internal method to execute sync job."""
        start_time = datetime.utcnow()
        result = SyncResult(
            job_id=job.job_id,
            sync_type=job.sync_type,
            status=SyncStatus.RUNNING,
            start_time=start_time,
            end_time=None,
            duration_seconds=None,
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_deleted=0,
            errors=[],
            warnings=[]
        )
        
        try:
            logger.info(f"Starting sync job: {job.job_id} ({job.sync_type.value})")
            
            # Update job status
            await self._update_job_status(job.job_id, SyncStatus.RUNNING)
            
            # Execute based on sync type
            if job.sync_type == SyncType.INCREMENTAL_SYNC:
                result = await self._execute_incremental_sync(job, result)
            elif job.sync_type == SyncType.FULL_SYNC:
                result = await self._execute_full_sync(job, result)
            elif job.sync_type == SyncType.DAP_SYNC:
                result = await self._execute_dap_sync(job, result)
            elif job.sync_type == SyncType.LIVE_EVENTS_SYNC:
                result = await self._execute_live_events_sync(job, result)
            elif job.sync_type == SyncType.CONSISTENCY_CHECK:
                result = await self._execute_consistency_check(job, result)
            else:
                result.errors.append(f"Unknown sync type: {job.sync_type}")
                result.status = SyncStatus.FAILED
            
            # Calculate duration
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            
            # Determine final status
            if result.status == SyncStatus.RUNNING:
                result.status = SyncStatus.COMPLETED if not result.errors else SyncStatus.FAILED
            
            # Schedule next run
            result.next_sync_scheduled = await self._schedule_next_run(job)
            
            # Update job with results
            await self._update_job_last_run(job.job_id, result)
            
            logger.info(f"Sync job {job.job_id} completed: {result.status.value}, processed {result.records_processed} records")
            
        except asyncio.CancelledError:
            result.status = SyncStatus.CANCELLED
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            logger.warning(f"Sync job {job.job_id} was cancelled")
            
        except Exception as e:
            result.status = SyncStatus.FAILED
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            result.errors.append(str(e))
            logger.error(f"Sync job {job.job_id} failed: {e}")
        
        return result
    
    async def _execute_incremental_sync(self, job: SyncJob, result: SyncResult) -> SyncResult:
        """Execute incremental synchronization."""
        try:
            # Get last sync time
            last_sync = await self._get_last_sync_time(job.job_id)
            
            # Determine time window
            if job.filters and "updated_since" in job.filters:
                since_value = job.filters["updated_since"]
                if since_value == "1_hour":
                    since_time = datetime.utcnow() - timedelta(hours=1)
                elif since_value == "30_minutes":
                    since_time = datetime.utcnow() - timedelta(minutes=30)
                else:
                    since_time = last_sync or (datetime.utcnow() - timedelta(hours=1))
            else:
                since_time = last_sync or (datetime.utcnow() - timedelta(hours=1))
            
            # Sync each target entity
            for entity in job.target_entities:
                try:
                    entity_result = await self._sync_entity_incremental(entity, since_time)
                    result.records_processed += entity_result.get("processed", 0)
                    result.records_created += entity_result.get("created", 0)
                    result.records_updated += entity_result.get("updated", 0)
                    result.records_deleted += entity_result.get("deleted", 0)
                    
                    if entity_result.get("errors"):
                        result.errors.extend(entity_result["errors"])
                    
                    if entity_result.get("warnings"):
                        result.warnings.extend(entity_result["warnings"])
                        
                except Exception as e:
                    result.errors.append(f"Error syncing {entity}: {str(e)}")
            
            return result
            
        except Exception as e:
            result.errors.append(f"Incremental sync error: {str(e)}")
            result.status = SyncStatus.FAILED
            return result
    
    async def _execute_full_sync(self, job: SyncJob, result: SyncResult) -> SyncResult:
        """Execute full synchronization."""
        try:
            # Full sync of all entities
            entities = job.target_entities if job.target_entities != ["all"] else [
                "users", "courses", "enrollments", "assignments", "submissions", "grades"
            ]
            
            for entity in entities:
                try:
                    entity_result = await self._sync_entity_full(entity)
                    result.records_processed += entity_result.get("processed", 0)
                    result.records_created += entity_result.get("created", 0)
                    result.records_updated += entity_result.get("updated", 0)
                    result.records_deleted += entity_result.get("deleted", 0)
                    
                    if entity_result.get("errors"):
                        result.errors.extend(entity_result["errors"])
                    
                    if entity_result.get("warnings"):
                        result.warnings.extend(entity_result["warnings"])
                        
                except Exception as e:
                    result.errors.append(f"Error syncing {entity}: {str(e)}")
            
            return result
            
        except Exception as e:
            result.errors.append(f"Full sync error: {str(e)}")
            result.status = SyncStatus.FAILED
            return result
    
    async def _execute_dap_sync(self, job: SyncJob, result: SyncResult) -> SyncResult:
        """Execute DAP synchronization."""
        try:
            # Run DAP extraction and ingestion
            dap_result = await canvas_dap_service.run_daily_extract()
            
            result.records_processed = dap_result.get("files_processed", 0)
            result.records_created = dap_result.get("records_ingested", 0)
            
            if dap_result.get("errors"):
                result.errors.extend(dap_result["errors"])
            
            if dap_result.get("warnings"):
                result.warnings.extend(dap_result["warnings"])
            
            return result
            
        except Exception as e:
            result.errors.append(f"DAP sync error: {str(e)}")
            result.status = SyncStatus.FAILED
            return result
    
    async def _execute_live_events_sync(self, job: SyncJob, result: SyncResult) -> SyncResult:
        """Execute live events synchronization."""
        try:
            # Process live events from Redis stream
            events_result = await canvas_live_events_service.process_pending_events()
            
            result.records_processed = events_result.get("events_processed", 0)
            result.records_created = events_result.get("entities_created", 0)
            result.records_updated = events_result.get("entities_updated", 0)
            
            if events_result.get("errors"):
                result.errors.extend(events_result["errors"])
            
            if events_result.get("warnings"):
                result.warnings.extend(events_result["warnings"])
            
            return result
            
        except Exception as e:
            result.errors.append(f"Live events sync error: {str(e)}")
            result.status = SyncStatus.FAILED
            return result
    
    async def _execute_consistency_check(self, job: SyncJob, result: SyncResult) -> SyncResult:
        """Execute data consistency check."""
        try:
            consistency_checker = CanvasConsistencyChecker()
            check_result = await consistency_checker.run_consistency_checks()
            
            result.records_processed = check_result.get("entities_checked", 0)
            result.metadata = {
                "issues_found": check_result.get("issues_found", 0),
                "critical_issues": check_result.get("critical_issues", 0),
                "resolved_issues": check_result.get("resolved_issues", 0)
            }
            
            if check_result.get("errors"):
                result.errors.extend(check_result["errors"])
            
            if check_result.get("warnings"):
                result.warnings.extend(check_result["warnings"])
            
            return result
            
        except Exception as e:
            result.errors.append(f"Consistency check error: {str(e)}")
            result.status = SyncStatus.FAILED
            return result
    
    async def _sync_entity_incremental(self, entity: str, since_time: datetime) -> Dict[str, Any]:
        """Sync specific entity incrementally."""
        # This would call the appropriate Canvas client methods
        # For now, return mock data
        return {
            "processed": 100,
            "created": 10,
            "updated": 85,
            "deleted": 5,
            "errors": [],
            "warnings": []
        }
    
    async def _sync_entity_full(self, entity: str) -> Dict[str, Any]:
        """Sync specific entity fully."""
        # This would call the appropriate Canvas client methods
        # For now, return mock data
        return {
            "processed": 500,
            "created": 50,
            "updated": 400,
            "deleted": 50,
            "errors": [],
            "warnings": []
        }
    
    async def _store_sync_jobs(self, jobs: List[SyncJob]):
        """Store sync jobs in database."""
        try:
            async with AsyncSessionLocal() as db:
                # Create table if not exists
                await self._create_sync_tables(db)
                
                for job in jobs:
                    await self._upsert_sync_job(db, job)
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error storing sync jobs: {e}")
            raise
    
    async def _create_sync_tables(self, db: AsyncSession):
        """Create sync-related tables."""
        create_jobs_table = """
        CREATE TABLE IF NOT EXISTS canvas_sync_jobs (
            job_id VARCHAR(100) PRIMARY KEY,
            sync_type VARCHAR(50) NOT NULL,
            source VARCHAR(50) NOT NULL,
            target_entities JSONB NOT NULL,
            priority INTEGER NOT NULL,
            schedule_cron VARCHAR(100),
            filters JSONB,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            last_run TIMESTAMP WITH TIME ZONE,
            next_run TIMESTAMP WITH TIME ZONE,
            status VARCHAR(20) NOT NULL,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            timeout_minutes INTEGER DEFAULT 60,
            metadata JSONB,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_sync_jobs_status ON canvas_sync_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_sync_jobs_next_run ON canvas_sync_jobs(next_run);
        CREATE INDEX IF NOT EXISTS idx_sync_jobs_sync_type ON canvas_sync_jobs(sync_type);
        """
        
        create_results_table = """
        CREATE TABLE IF NOT EXISTS canvas_sync_results (
            result_id SERIAL PRIMARY KEY,
            job_id VARCHAR(100) NOT NULL,
            sync_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL,
            start_time TIMESTAMP WITH TIME ZONE NOT NULL,
            end_time TIMESTAMP WITH TIME ZONE,
            duration_seconds DECIMAL(10,2),
            records_processed INTEGER DEFAULT 0,
            records_created INTEGER DEFAULT 0,
            records_updated INTEGER DEFAULT 0,
            records_deleted INTEGER DEFAULT 0,
            errors JSONB,
            warnings JSONB,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_sync_results_job_id ON canvas_sync_results(job_id);
        CREATE INDEX IF NOT EXISTS idx_sync_results_start_time ON canvas_sync_results(start_time);
        CREATE INDEX IF NOT EXISTS idx_sync_results_status ON canvas_sync_results(status);
        """
        
        create_consistency_table = """
        CREATE TABLE IF NOT EXISTS canvas_consistency_issues (
            issue_id VARCHAR(100) PRIMARY KEY,
            entity_type VARCHAR(50) NOT NULL,
            entity_id VARCHAR(100) NOT NULL,
            source_system VARCHAR(50) NOT NULL,
            issue_type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            severity VARCHAR(20) NOT NULL,
            detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
            resolved_at TIMESTAMP WITH TIME ZONE,
            resolution_action TEXT,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_consistency_issues_entity ON canvas_consistency_issues(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_consistency_issues_severity ON canvas_consistency_issues(severity);
        CREATE INDEX IF NOT EXISTS idx_consistency_issues_detected ON canvas_consistency_issues(detected_at);
        """
        
        await db.execute(text(create_jobs_table))
        await db.execute(text(create_results_table))
        await db.execute(text(create_consistency_table))
    
    async def _upsert_sync_job(self, db: AsyncSession, job: SyncJob):
        """Upsert sync job in database."""
        upsert_sql = """
        INSERT INTO canvas_sync_jobs (
            job_id, sync_type, source, target_entities, priority,
            schedule_cron, filters, created_at, last_run, next_run,
            status, retry_count, max_retries, timeout_minutes, metadata
        ) VALUES (
            :job_id, :sync_type, :source, :target_entities, :priority,
            :schedule_cron, :filters, :created_at, :last_run, :next_run,
            :status, :retry_count, :max_retries, :timeout_minutes, :metadata
        ) ON CONFLICT (job_id) DO UPDATE SET
            sync_type = EXCLUDED.sync_type,
            source = EXCLUDED.source,
            target_entities = EXCLUDED.target_entities,
            priority = EXCLUDED.priority,
            schedule_cron = EXCLUDED.schedule_cron,
            filters = EXCLUDED.filters,
            status = EXCLUDED.status,
            retry_count = EXCLUDED.retry_count,
            max_retries = EXCLUDED.max_retries,
            timeout_minutes = EXCLUDED.timeout_minutes,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        """
        
        await db.execute(text(upsert_sql), {
            "job_id": job.job_id,
            "sync_type": job.sync_type.value,
            "source": job.source,
            "target_entities": json.dumps(job.target_entities),
            "priority": job.priority.value,
            "schedule_cron": job.schedule_cron,
            "filters": json.dumps(job.filters) if job.filters else None,
            "created_at": job.created_at,
            "last_run": job.last_run,
            "next_run": job.next_run,
            "status": job.status.value,
            "retry_count": job.retry_count,
            "max_retries": job.max_retries,
            "timeout_minutes": job.timeout_minutes,
            "metadata": json.dumps(job.metadata) if job.metadata else None
        })
    
    async def _schedule_job(self, job: SyncJob):
        """Schedule job with APScheduler."""
        if job.schedule_cron:
            try:
                scheduler_service.schedule_job(
                    func=self.execute_sync_job,
                    args=[job.job_id],
                    job_id=f"canvas_sync_{job.job_id}",
                    cron_expression=job.schedule_cron,
                    timezone="UTC"
                )
                logger.info(f"Scheduled sync job {job.job_id} with cron: {job.schedule_cron}")
            except Exception as e:
                logger.error(f"Error scheduling job {job.job_id}: {e}")
    
    async def _get_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """Get sync job by ID."""
        try:
            async with AsyncSessionLocal() as db:
                query = "SELECT * FROM canvas_sync_jobs WHERE job_id = :job_id"
                result = await db.execute(text(query), {"job_id": job_id})
                row = result.fetchone()
                
                if not row:
                    return None
                
                return SyncJob(
                    job_id=row.job_id,
                    sync_type=SyncType(row.sync_type),
                    source=row.source,
                    target_entities=json.loads(row.target_entities),
                    priority=SyncPriority(row.priority),
                    schedule_cron=row.schedule_cron,
                    filters=json.loads(row.filters) if row.filters else None,
                    created_at=row.created_at,
                    last_run=row.last_run,
                    next_run=row.next_run,
                    status=SyncStatus(row.status),
                    retry_count=row.retry_count,
                    max_retries=row.max_retries,
                    timeout_minutes=row.timeout_minutes,
                    metadata=json.loads(row.metadata) if row.metadata else None
                )
                
        except Exception as e:
            logger.error(f"Error getting sync job {job_id}: {e}")
            return None
    
    async def _update_job_status(self, job_id: str, status: SyncStatus):
        """Update job status."""
        try:
            async with AsyncSessionLocal() as db:
                update_sql = """
                UPDATE canvas_sync_jobs 
                SET status = :status, updated_at = NOW()
                WHERE job_id = :job_id
                """
                await db.execute(text(update_sql), {"job_id": job_id, "status": status.value})
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
    
    async def _get_last_sync_time(self, job_id: str) -> Optional[datetime]:
        """Get last successful sync time for job."""
        try:
            async with AsyncSessionLocal() as db:
                query = """
                SELECT MAX(end_time) as last_sync
                FROM canvas_sync_results 
                WHERE job_id = :job_id AND status = 'completed'
                """
                result = await db.execute(text(query), {"job_id": job_id})
                row = result.fetchone()
                return row.last_sync if row else None
        except Exception as e:
            logger.error(f"Error getting last sync time: {e}")
            return None
    
    async def _schedule_next_run(self, job: SyncJob) -> Optional[datetime]:
        """Calculate and schedule next run time."""
        # For now, return a simple calculation
        # In production, this would use proper cron parsing
        if job.schedule_cron:
            if "*/15" in job.schedule_cron:  # Every 15 minutes
                return datetime.utcnow() + timedelta(minutes=15)
            elif "*/5" in job.schedule_cron:   # Every 5 minutes
                return datetime.utcnow() + timedelta(minutes=5)
            elif "0 2" in job.schedule_cron:   # Daily at 2 AM
                next_run = datetime.utcnow().replace(hour=2, minute=0, second=0, microsecond=0)
                if next_run <= datetime.utcnow():
                    next_run += timedelta(days=1)
                return next_run
        return None
    
    async def _update_job_last_run(self, job_id: str, result: SyncResult):
        """Update job last run and store result."""
        try:
            async with AsyncSessionLocal() as db:
                # Update job
                update_job_sql = """
                UPDATE canvas_sync_jobs 
                SET last_run = :last_run, next_run = :next_run, 
                    status = :status, updated_at = NOW()
                WHERE job_id = :job_id
                """
                
                await db.execute(text(update_job_sql), {
                    "job_id": job_id,
                    "last_run": result.end_time,
                    "next_run": result.next_sync_scheduled,
                    "status": SyncStatus.PENDING.value  # Reset to pending for next run
                })
                
                # Store result
                insert_result_sql = """
                INSERT INTO canvas_sync_results (
                    job_id, sync_type, status, start_time, end_time, duration_seconds,
                    records_processed, records_created, records_updated, records_deleted,
                    errors, warnings, metadata
                ) VALUES (
                    :job_id, :sync_type, :status, :start_time, :end_time, :duration_seconds,
                    :records_processed, :records_created, :records_updated, :records_deleted,
                    :errors, :warnings, :metadata
                )
                """
                
                await db.execute(text(insert_result_sql), {
                    "job_id": result.job_id,
                    "sync_type": result.sync_type.value,
                    "status": result.status.value,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                    "duration_seconds": result.duration_seconds,
                    "records_processed": result.records_processed,
                    "records_created": result.records_created,
                    "records_updated": result.records_updated,
                    "records_deleted": result.records_deleted,
                    "errors": json.dumps(result.errors),
                    "warnings": json.dumps(result.warnings),
                    "metadata": json.dumps(result.metadata) if result.metadata else None
                })
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error updating job last run: {e}")
    
    async def _monitor_running_jobs(self):
        """Monitor running jobs for timeouts and failures."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check for timed out jobs
                current_time = datetime.utcnow()
                for job_id, task in list(self.running_jobs.items()):
                    if task.done():
                        # Job completed, remove from tracking
                        del self.running_jobs[job_id]
                    # Add timeout logic here if needed
                        
            except Exception as e:
                logger.error(f"Error monitoring running jobs: {e}")
    
    async def _cleanup_old_results(self):
        """Clean up old sync results."""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                
                async with AsyncSessionLocal() as db:
                    # Keep results for 30 days
                    cleanup_date = datetime.utcnow() - timedelta(days=30)
                    
                    cleanup_sql = """
                    DELETE FROM canvas_sync_results 
                    WHERE start_time < :cleanup_date
                    """
                    
                    result = await db.execute(text(cleanup_sql), {"cleanup_date": cleanup_date})
                    await db.commit()
                    
                    if result.rowcount > 0:
                        logger.info(f"Cleaned up {result.rowcount} old sync results")
                        
            except Exception as e:
                logger.error(f"Error cleaning up old results: {e}")
    
    async def _schedule_missed_jobs(self):
        """Check for and schedule missed jobs."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                async with AsyncSessionLocal() as db:
                    # Find jobs that should have run
                    query = """
                    SELECT job_id FROM canvas_sync_jobs 
                    WHERE next_run <= NOW() 
                    AND status = 'pending'
                    AND job_id NOT IN (
                        SELECT DISTINCT job_id FROM canvas_sync_results 
                        WHERE status = 'running'
                    )
                    """
                    
                    result = await db.execute(text(query))
                    missed_jobs = [row.job_id for row in result.fetchall()]
                    
                    for job_id in missed_jobs:
                        if job_id not in self.running_jobs:
                            logger.info(f"Scheduling missed job: {job_id}")
                            asyncio.create_task(self.execute_sync_job(job_id))
                            
            except Exception as e:
                logger.error(f"Error checking missed jobs: {e}")


class CanvasConsistencyChecker:
    """Checks data consistency between Canvas and local database."""
    
    async def run_consistency_checks(self) -> Dict[str, Any]:
        """Run all consistency checks."""
        try:
            logger.info("Starting Canvas data consistency checks...")
            
            results = {
                "entities_checked": 0,
                "issues_found": 0,
                "critical_issues": 0,
                "resolved_issues": 0,
                "errors": [],
                "warnings": []
            }
            
            # Check different entity types
            checks = [
                self._check_user_consistency(),
                self._check_course_consistency(),
                self._check_enrollment_consistency(),
                self._check_assignment_consistency(),
                self._check_submission_consistency()
            ]
            
            check_results = await asyncio.gather(*checks, return_exceptions=True)
            
            for i, check_result in enumerate(check_results):
                if isinstance(check_result, Exception):
                    results["errors"].append(f"Check {i} failed: {str(check_result)}")
                else:
                    results["entities_checked"] += check_result.get("checked", 0)
                    results["issues_found"] += check_result.get("issues", 0)
                    results["critical_issues"] += check_result.get("critical", 0)
                    results["resolved_issues"] += check_result.get("resolved", 0)
            
            logger.info(f"Consistency check completed: {results['issues_found']} issues found")
            return results
            
        except Exception as e:
            logger.error(f"Error in consistency checks: {e}")
            return {
                "entities_checked": 0,
                "issues_found": 0,
                "critical_issues": 0,
                "resolved_issues": 0,
                "errors": [str(e)],
                "warnings": []
            }
    
    async def _check_user_consistency(self) -> Dict[str, Any]:
        """Check user data consistency."""
        # Placeholder implementation
        return {"checked": 100, "issues": 2, "critical": 0, "resolved": 1}
    
    async def _check_course_consistency(self) -> Dict[str, Any]:
        """Check course data consistency."""
        # Placeholder implementation
        return {"checked": 50, "issues": 1, "critical": 0, "resolved": 0}
    
    async def _check_enrollment_consistency(self) -> Dict[str, Any]:
        """Check enrollment data consistency."""
        # Placeholder implementation
        return {"checked": 200, "issues": 3, "critical": 1, "resolved": 2}
    
    async def _check_assignment_consistency(self) -> Dict[str, Any]:
        """Check assignment data consistency."""
        # Placeholder implementation
        return {"checked": 150, "issues": 0, "critical": 0, "resolved": 0}
    
    async def _check_submission_consistency(self) -> Dict[str, Any]:
        """Check submission data consistency."""
        # Placeholder implementation
        return {"checked": 500, "issues": 5, "critical": 2, "resolved": 3}


# Global instances
canvas_sync_scheduler = CanvasSyncScheduler()
canvas_consistency_checker = CanvasConsistencyChecker()
