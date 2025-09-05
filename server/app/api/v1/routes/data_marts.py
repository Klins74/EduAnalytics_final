"""API routes for data mart management and ETL operations."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.data_mart_etl import data_mart_etl, DataMartType, ETLStatus

router = APIRouter(prefix="/data-marts", tags=["Data Marts"])


class DataMartTypeEnum(str, Enum):
    """Data mart type enumeration for API."""
    STUDENT_PERFORMANCE = "student_performance"
    COURSE_ANALYTICS = "course_analytics"
    ASSIGNMENT_METRICS = "assignment_metrics"
    ENGAGEMENT_TRENDS = "engagement_trends"
    LEARNING_OUTCOMES = "learning_outcomes"


class ETLJobRequest(BaseModel):
    """Request model for ETL job."""
    mart_type: Optional[DataMartTypeEnum] = None
    force_full_refresh: bool = False


class ETLJobResponse(BaseModel):
    """Response model for ETL job."""
    job_id: str
    status: str
    message: str


class ETLStatusResponse(BaseModel):
    """Response model for ETL status."""
    recent_jobs: List[Dict[str, Any]]
    mart_sizes: Dict[str, int]
    status: str
    last_update: str


class DataLineageResponse(BaseModel):
    """Response model for data lineage."""
    lineage_id: int
    source_system: str
    source_table: str
    source_columns: List[str]
    target_table: str
    target_columns: List[str]
    transformation_logic: str
    created_at: str
    created_by: str


@router.post("/etl/initialize", summary="Initialize data mart structures")
async def initialize_data_marts(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Initialize all data mart structures including dimension and fact tables."""
    try:
        await data_mart_etl.initialize_data_marts()
        
        return {
            "success": True,
            "message": "Data mart structures initialized successfully",
            "initialized_components": [
                "dimension_tables",
                "fact_tables", 
                "lineage_tracking",
                "etl_job_tracking"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize data marts: {str(e)}"
        )


@router.post("/etl/run", response_model=ETLJobResponse, summary="Run ETL pipeline")
async def run_etl_pipeline(
    etl_request: ETLJobRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.admin))
) -> ETLJobResponse:
    """Run the ETL pipeline for specified data marts."""
    try:
        # Convert string enum to DataMartType enum
        mart_type = None
        if etl_request.mart_type:
            mart_type = DataMartType(etl_request.mart_type.value)
        
        # Run ETL in background
        background_tasks.add_task(
            data_mart_etl.run_etl_pipeline,
            mart_type
        )
        
        # Generate job ID for tracking
        from datetime import datetime
        job_id = f"etl_{mart_type.value if mart_type else 'full'}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return ETLJobResponse(
            job_id=job_id,
            status="started",
            message=f"ETL pipeline started for {mart_type.value if mart_type else 'all marts'}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start ETL pipeline: {str(e)}"
        )


@router.get("/etl/status", response_model=ETLStatusResponse, summary="Get ETL status")
async def get_etl_status(
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> ETLStatusResponse:
    """Get the current status of ETL operations and data marts."""
    try:
        status_info = await data_mart_etl.get_etl_status()
        
        return ETLStatusResponse(
            recent_jobs=status_info["recent_jobs"],
            mart_sizes=status_info["mart_sizes"],
            status=status_info["status"],
            last_update=status_info["last_update"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ETL status: {str(e)}"
        )


@router.get("/lineage", summary="Get data lineage information")
async def get_data_lineage(
    source_table: Optional[str] = Query(None, description="Filter by source table"),
    target_table: Optional[str] = Query(None, description="Filter by target table"),
    limit: int = Query(50, description="Maximum number of records to return"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get data lineage information for data marts."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Build query with filters
            where_conditions = []
            params = {"limit": limit}
            
            if source_table:
                where_conditions.append("source_table = :source_table")
                params["source_table"] = source_table
            
            if target_table:
                where_conditions.append("target_table = :target_table")
                params["target_table"] = target_table
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            query = f"""
            SELECT lineage_id, source_system, source_table, source_columns,
                   target_table, target_columns, transformation_logic,
                   created_at, created_by
            FROM data_lineage
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
            """
            
            result = await db.execute(text(query), params)
            lineage_records = []
            
            for row in result.fetchall():
                lineage_records.append({
                    "lineage_id": row.lineage_id,
                    "source_system": row.source_system,
                    "source_table": row.source_table,
                    "source_columns": row.source_columns or [],
                    "target_table": row.target_table,
                    "target_columns": row.target_columns or [],
                    "transformation_logic": row.transformation_logic,
                    "created_at": row.created_at.isoformat(),
                    "created_by": row.created_by
                })
            
            return {
                "lineage_records": lineage_records,
                "total_count": len(lineage_records),
                "filters": {
                    "source_table": source_table,
                    "target_table": target_table,
                    "limit": limit
                }
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data lineage: {str(e)}"
        )


@router.get("/schema", summary="Get data mart schema information")
async def get_data_mart_schema(
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get schema information for data mart tables."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Get table information
            tables_query = """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (table_name LIKE 'dim_%' OR table_name LIKE 'fact_%')
            ORDER BY table_name
            """
            
            result = await db.execute(text(tables_query))
            tables = [{"name": row.table_name, "type": row.table_type} for row in result.fetchall()]
            
            # Get column information for each table
            schema_info = {}
            
            for table in tables:
                table_name = table["name"]
                columns_query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table_name
                ORDER BY ordinal_position
                """
                
                col_result = await db.execute(text(columns_query), {"table_name": table_name})
                columns = []
                
                for col_row in col_result.fetchall():
                    columns.append({
                        "name": col_row.column_name,
                        "type": col_row.data_type,
                        "nullable": col_row.is_nullable == "YES",
                        "default": col_row.column_default
                    })
                
                schema_info[table_name] = {
                    "type": table["type"],
                    "columns": columns
                }
            
            return {
                "tables": schema_info,
                "table_count": len(tables),
                "dimension_tables": [name for name in schema_info.keys() if name.startswith("dim_")],
                "fact_tables": [name for name in schema_info.keys() if name.startswith("fact_")]
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schema information: {str(e)}"
        )


@router.get("/quality", summary="Get data quality metrics")
async def get_data_quality_metrics(
    table_name: Optional[str] = Query(None, description="Specific table to check"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get data quality metrics for data mart tables."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            quality_metrics = {}
            
            # Define tables to check
            tables_to_check = []
            if table_name:
                tables_to_check = [table_name]
            else:
                # Get all fact and dimension tables
                tables_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND (table_name LIKE 'dim_%' OR table_name LIKE 'fact_%')
                """
                
                result = await db.execute(text(tables_query))
                tables_to_check = [row.table_name for row in result.fetchall()]
            
            # Check each table
            for table in tables_to_check:
                try:
                    # Basic metrics
                    count_query = f"SELECT COUNT(*) as total_rows FROM {table}"
                    count_result = await db.execute(text(count_query))
                    total_rows = count_result.scalar()
                    
                    # Check for recent updates (if table has updated_at column)
                    recent_updates = 0
                    try:
                        recent_query = f"""
                        SELECT COUNT(*) 
                        FROM {table} 
                        WHERE updated_at >= NOW() - INTERVAL '24 hours'
                        """
                        recent_result = await db.execute(text(recent_query))
                        recent_updates = recent_result.scalar()
                    except:
                        # Table might not have updated_at column
                        pass
                    
                    # Check for NULL values in key columns
                    null_checks = {}
                    if table.startswith("fact_"):
                        # Check key foreign key columns
                        key_columns = ["student_key", "course_key", "date_key"]
                        for col in key_columns:
                            try:
                                null_query = f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL"
                                null_result = await db.execute(text(null_query))
                                null_count = null_result.scalar()
                                null_checks[col] = null_count
                            except:
                                # Column might not exist
                                pass
                    
                    quality_metrics[table] = {
                        "total_rows": total_rows,
                        "recent_updates_24h": recent_updates,
                        "null_key_columns": null_checks,
                        "last_checked": datetime.utcnow().isoformat()
                    }
                    
                except Exception as e:
                    quality_metrics[table] = {
                        "error": str(e),
                        "last_checked": datetime.utcnow().isoformat()
                    }
            
            return {
                "quality_metrics": quality_metrics,
                "tables_checked": len(tables_to_check),
                "overall_status": "healthy" if all("error" not in metrics for metrics in quality_metrics.values()) else "issues_detected"
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data quality metrics: {str(e)}"
        )


@router.delete("/etl/cleanup", summary="Clean up old ETL data")
async def cleanup_etl_data(
    retention_days: int = Query(30, description="Number of days to retain data"),
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Clean up old ETL job logs and temporary data."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        from datetime import datetime, timedelta
        
        cleanup_date = datetime.utcnow() - timedelta(days=retention_days)
        cleanup_results = {}
        
        async with AsyncSessionLocal() as db:
            # Clean up old ETL job logs
            cleanup_jobs_query = """
            DELETE FROM etl_jobs 
            WHERE created_at < :cleanup_date
            AND status IN ('completed', 'failed')
            """
            
            result = await db.execute(text(cleanup_jobs_query), {"cleanup_date": cleanup_date})
            cleanup_results["etl_jobs_deleted"] = result.rowcount
            
            # Clean up old lineage records (optional - you might want to keep these)
            cleanup_lineage_query = """
            DELETE FROM data_lineage 
            WHERE created_at < :cleanup_date
            """
            
            result = await db.execute(text(cleanup_lineage_query), {"cleanup_date": cleanup_date})
            cleanup_results["lineage_records_deleted"] = result.rowcount
            
            await db.commit()
            
            return {
                "success": True,
                "cleanup_results": cleanup_results,
                "retention_days": retention_days,
                "cleanup_date": cleanup_date.isoformat()
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup ETL data: {str(e)}"
        )
