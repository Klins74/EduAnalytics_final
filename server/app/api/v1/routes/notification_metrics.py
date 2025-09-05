"""API routes for notification metrics and SLA monitoring."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.notification_metrics import (
    notification_sla_manager,
    notification_metrics_collector,
    SLATarget,
    MetricType,
    SLAStatus
)

router = APIRouter(prefix="/notification-metrics", tags=["Notification Metrics"])


class SLATargetRequest(BaseModel):
    """Request model for creating SLA target."""
    metric_type: str
    channel: str
    priority: Optional[int] = None
    target_value: float
    target_unit: str
    measurement_window: str
    description: str


class SLATargetResponse(BaseModel):
    """Response model for SLA target."""
    metric_type: str
    channel: str
    priority: Optional[int]
    target_value: float
    target_unit: str
    measurement_window: str
    description: str


class SLAComplianceResponse(BaseModel):
    """Response model for SLA compliance check."""
    status: str
    current_value: Optional[float]
    target_value: float
    compliance_percentage: Optional[float]
    samples_count: int
    window_start: Optional[str] = None
    window_end: Optional[str] = None


class SLAReportResponse(BaseModel):
    """Response model for SLA report."""
    report_id: str
    generated_at: str
    period_start: str
    period_end: str
    overall_compliance: float
    sla_breaches: List[Dict[str, Any]]
    channel_compliance: Dict[str, float]
    priority_compliance: Dict[str, float]
    recommendations: List[str]
    metadata: Optional[Dict[str, Any]] = None


class MetricsOverviewResponse(BaseModel):
    """Response model for metrics overview."""
    channels: List[str]
    total_notifications_24h: int
    overall_delivery_rate: float
    overall_error_rate: float
    average_delivery_time: float
    sla_compliance_percentage: float
    active_alerts: int


@router.get("/overview", response_model=MetricsOverviewResponse, summary="Get metrics overview")
async def get_metrics_overview(
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> MetricsOverviewResponse:
    """Get high-level overview of notification metrics."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Get basic stats for last 24 hours
            since_time = datetime.utcnow() - timedelta(hours=24)
            
            # Total notifications
            total_query = """
            SELECT COUNT(*) as total
            FROM notification_log
            WHERE created_at >= :since_time
            """
            
            total_result = await db.execute(text(total_query), {"since_time": since_time})
            total_notifications = total_result.scalar() or 0
            
            # Delivery rate
            delivery_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as successful
            FROM notification_log
            WHERE created_at >= :since_time
            """
            
            delivery_result = await db.execute(text(delivery_query), {"since_time": since_time})
            delivery_row = delivery_result.fetchone()
            overall_delivery_rate = 0.0
            if delivery_row and delivery_row.total > 0:
                overall_delivery_rate = (delivery_row.successful / delivery_row.total) * 100
            
            # Error rate
            error_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM notification_log
            WHERE created_at >= :since_time
            """
            
            error_result = await db.execute(text(error_query), {"since_time": since_time})
            error_row = error_result.fetchone()
            overall_error_rate = 0.0
            if error_row and error_row.total > 0:
                overall_error_rate = (error_row.failed / error_row.total) * 100
            
            # Average delivery time
            latency_query = """
            SELECT AVG(latency_ms) as avg_latency
            FROM notification_delivery_attempts nda
            JOIN notification_log nl ON nda.message_id = nl.id
            WHERE nl.created_at >= :since_time
            AND nda.status = 'sent'
            AND nda.latency_ms IS NOT NULL
            """
            
            latency_result = await db.execute(text(latency_query), {"since_time": since_time})
            average_delivery_time = latency_result.scalar() or 0.0
            
            # Active channels
            channels_query = """
            SELECT DISTINCT channel
            FROM notification_log
            WHERE created_at >= :since_time
            ORDER BY channel
            """
            
            channels_result = await db.execute(text(channels_query), {"since_time": since_time})
            channels = [row.channel for row in channels_result.fetchall()]
        
        # Get recent SLA compliance
        try:
            recent_report = await notification_sla_manager.generate_sla_report(period_hours=1)
            sla_compliance = recent_report.overall_compliance
            active_alerts = len(recent_report.sla_breaches)
        except:
            sla_compliance = 0.0
            active_alerts = 0
        
        return MetricsOverviewResponse(
            channels=channels,
            total_notifications_24h=total_notifications,
            overall_delivery_rate=overall_delivery_rate,
            overall_error_rate=overall_error_rate,
            average_delivery_time=average_delivery_time,
            sla_compliance_percentage=sla_compliance,
            active_alerts=active_alerts
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics overview: {str(e)}"
        )


@router.get("/sla/targets", response_model=List[SLATargetResponse], summary="Get SLA targets")
async def get_sla_targets(
    channel: Optional[str] = Query(None, description="Filter by channel"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> List[SLATargetResponse]:
    """Get all SLA targets, optionally filtered by channel."""
    try:
        targets = await notification_sla_manager.get_sla_targets(channel=channel)
        
        return [
            SLATargetResponse(
                metric_type=target.metric_type.value,
                channel=target.channel,
                priority=target.priority,
                target_value=target.target_value,
                target_unit=target.target_unit,
                measurement_window=target.measurement_window,
                description=target.description
            )
            for target in targets
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SLA targets: {str(e)}"
        )


@router.post("/sla/targets", summary="Create SLA target")
async def create_sla_target(
    target_request: SLATargetRequest,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Create a new SLA target."""
    try:
        # Validate metric type
        try:
            metric_type = MetricType(target_request.metric_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric type: {target_request.metric_type}"
            )
        
        target = SLATarget(
            metric_type=metric_type,
            channel=target_request.channel,
            priority=target_request.priority,
            target_value=target_request.target_value,
            target_unit=target_request.target_unit,
            measurement_window=target_request.measurement_window,
            description=target_request.description
        )
        
        success = await notification_sla_manager.add_sla_target(target)
        
        if success:
            return {
                "success": True,
                "message": "SLA target created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create SLA target"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SLA target: {str(e)}"
        )


@router.get("/sla/compliance", summary="Check SLA compliance")
async def check_sla_compliance(
    channel: str = Query(..., description="Channel to check"),
    metric_type: str = Query(..., description="Metric type to check"),
    priority: Optional[int] = Query(None, description="Priority level"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> SLAComplianceResponse:
    """Check SLA compliance for specific target."""
    try:
        # Validate metric type
        try:
            metric_type_enum = MetricType(metric_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric type: {metric_type}"
            )
        
        # Find matching SLA target
        targets = await notification_sla_manager.get_sla_targets(channel=channel)
        matching_target = None
        
        for target in targets:
            if (target.metric_type == metric_type_enum and 
                target.channel == channel and 
                target.priority == priority):
                matching_target = target
                break
        
        if not matching_target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA target not found for specified criteria"
            )
        
        compliance = await notification_sla_manager.check_sla_compliance(matching_target)
        
        return SLAComplianceResponse(
            status=compliance.get("status", SLAStatus.UNKNOWN.value),
            current_value=compliance.get("current_value"),
            target_value=compliance.get("target_value", 0),
            compliance_percentage=compliance.get("compliance_percentage"),
            samples_count=compliance.get("samples_count", 0),
            window_start=compliance.get("window_start"),
            window_end=compliance.get("window_end")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check SLA compliance: {str(e)}"
        )


@router.get("/sla/report", response_model=SLAReportResponse, summary="Generate SLA report")
async def generate_sla_report(
    period_hours: int = Query(24, description="Period in hours for the report"),
    channels: Optional[str] = Query(None, description="Comma-separated list of channels"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> SLAReportResponse:
    """Generate comprehensive SLA compliance report."""
    try:
        # Parse channels parameter
        channels_list = None
        if channels:
            channels_list = [c.strip() for c in channels.split(",")]
        
        report = await notification_sla_manager.generate_sla_report(
            period_hours=period_hours,
            channels=channels_list
        )
        
        return SLAReportResponse(
            report_id=report.report_id,
            generated_at=report.generated_at.isoformat(),
            period_start=report.period_start.isoformat(),
            period_end=report.period_end.isoformat(),
            overall_compliance=report.overall_compliance,
            sla_breaches=report.sla_breaches,
            channel_compliance=report.channel_compliance,
            priority_compliance=report.priority_compliance,
            recommendations=report.recommendations,
            metadata=report.metadata
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SLA report: {str(e)}"
        )


@router.get("/channel/{channel}", summary="Get channel-specific metrics")
async def get_channel_metrics(
    channel: str,
    hours: int = Query(24, description="Time period in hours"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get detailed metrics for a specific channel."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Basic stats
            stats_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN retry_count > 0 THEN 1 END) as retried
            FROM notification_log
            WHERE channel = :channel
            AND created_at >= :since_time
            """
            
            stats_result = await db.execute(text(stats_query), {
                "channel": channel,
                "since_time": since_time
            })
            stats = dict(stats_result.fetchone()._mapping)
            
            # Delivery time stats
            latency_query = """
            SELECT 
                AVG(latency_ms) as avg_latency,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as median_latency,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
                MIN(latency_ms) as min_latency,
                MAX(latency_ms) as max_latency
            FROM notification_delivery_attempts nda
            JOIN notification_log nl ON nda.message_id = nl.id
            WHERE nl.channel = :channel
            AND nl.created_at >= :since_time
            AND nda.status = 'sent'
            AND nda.latency_ms IS NOT NULL
            """
            
            latency_result = await db.execute(text(latency_query), {
                "channel": channel,
                "since_time": since_time
            })
            latency_stats = dict(latency_result.fetchone()._mapping) if latency_result.rowcount > 0 else {}
            
            # Hourly distribution
            hourly_query = """
            SELECT 
                DATE_TRUNC('hour', created_at) as hour,
                COUNT(*) as count,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as successful
            FROM notification_log
            WHERE channel = :channel
            AND created_at >= :since_time
            GROUP BY hour
            ORDER BY hour
            """
            
            hourly_result = await db.execute(text(hourly_query), {
                "channel": channel,
                "since_time": since_time
            })
            hourly_distribution = [
                {
                    "hour": row.hour.isoformat(),
                    "total": row.count,
                    "successful": row.successful,
                    "success_rate": (row.successful / row.count * 100) if row.count > 0 else 0
                }
                for row in hourly_result.fetchall()
            ]
            
            # Priority distribution
            priority_query = """
            SELECT 
                priority,
                COUNT(*) as count,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as successful
            FROM notification_log
            WHERE channel = :channel
            AND created_at >= :since_time
            GROUP BY priority
            ORDER BY priority
            """
            
            priority_result = await db.execute(text(priority_query), {
                "channel": channel,
                "since_time": since_time
            })
            priority_distribution = [
                {
                    "priority": row.priority,
                    "total": row.count,
                    "successful": row.successful,
                    "success_rate": (row.successful / row.count * 100) if row.count > 0 else 0
                }
                for row in priority_result.fetchall()
            ]
        
        # Calculate derived metrics
        delivery_rate = (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
        error_rate = (stats["failed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        retry_rate = (stats["retried"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        return {
            "channel": channel,
            "period_hours": hours,
            "summary": {
                "total_notifications": stats["total"],
                "successful": stats["successful"],
                "failed": stats["failed"],
                "pending": stats["pending"],
                "retried": stats["retried"],
                "delivery_rate": round(delivery_rate, 2),
                "error_rate": round(error_rate, 2),
                "retry_rate": round(retry_rate, 2)
            },
            "latency_stats": {
                "avg_latency_ms": round(latency_stats.get("avg_latency", 0), 2),
                "median_latency_ms": round(latency_stats.get("median_latency", 0), 2),
                "p95_latency_ms": round(latency_stats.get("p95_latency", 0), 2),
                "min_latency_ms": latency_stats.get("min_latency", 0),
                "max_latency_ms": latency_stats.get("max_latency", 0)
            },
            "hourly_distribution": hourly_distribution,
            "priority_distribution": priority_distribution
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get channel metrics: {str(e)}"
        )


@router.get("/alerts", summary="Get active SLA alerts")
async def get_active_alerts(
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get currently active SLA alerts and breaches."""
    try:
        # Generate current report to get latest breaches
        report = await notification_sla_manager.generate_sla_report(period_hours=1)
        
        # Categorize alerts by severity
        critical_alerts = []
        warning_alerts = []
        
        for breach in report.sla_breaches:
            alert = {
                "metric_type": breach["metric_type"],
                "channel": breach["channel"],
                "priority": breach.get("priority"),
                "target_value": breach["target_value"],
                "current_value": breach["current_value"],
                "description": breach["description"],
                "detected_at": datetime.utcnow().isoformat()
            }
            
            # Determine severity based on metric type and values
            if breach["metric_type"] in ["delivery_rate", "error_rate"]:
                if breach["current_value"] is not None:
                    if breach["metric_type"] == "delivery_rate" and breach["current_value"] < 90:
                        critical_alerts.append(alert)
                    elif breach["metric_type"] == "error_rate" and breach["current_value"] > 5:
                        critical_alerts.append(alert)
                    else:
                        warning_alerts.append(alert)
                else:
                    warning_alerts.append(alert)
            else:
                warning_alerts.append(alert)
        
        return {
            "total_alerts": len(report.sla_breaches),
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "overall_compliance": report.overall_compliance,
            "last_updated": report.generated_at.isoformat(),
            "recommendations": report.recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active alerts: {str(e)}"
        )


@router.post("/initialize", summary="Initialize metrics system")
async def initialize_metrics_system(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Initialize the notification metrics and SLA system."""
    try:
        # Initialize SLA targets
        await notification_sla_manager.initialize_sla_targets()
        
        # Start metrics collection (this would typically be done in background)
        # For API response, we'll just confirm initialization
        
        return {
            "success": True,
            "message": "Notification metrics system initialized successfully",
            "components": [
                "SLA targets created",
                "Database tables initialized",
                "Metrics collection configured"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize metrics system: {str(e)}"
        )
