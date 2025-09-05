"""
Notification delivery metrics and SLA tracking service.

Monitors notification performance, tracks SLA compliance, and provides
detailed analytics for notification delivery across all channels.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, time
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, or_, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.services.redis_service import redis_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class SLAStatus(Enum):
    """SLA compliance status."""
    MET = "met"
    BREACHED = "breached"
    AT_RISK = "at_risk"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Types of notification metrics."""
    DELIVERY_RATE = "delivery_rate"
    DELIVERY_TIME = "delivery_time"
    ERROR_RATE = "error_rate"
    RETRY_RATE = "retry_rate"
    THROUGHPUT = "throughput"
    CHANNEL_PERFORMANCE = "channel_performance"
    PRIORITY_PERFORMANCE = "priority_performance"


@dataclass
class SLATarget:
    """SLA target definition."""
    metric_type: MetricType
    channel: str
    priority: Optional[int]
    target_value: float
    target_unit: str  # percentage, milliseconds, count_per_minute
    measurement_window: str  # 5m, 1h, 24h, 7d
    description: str


@dataclass
class MetricSnapshot:
    """Point-in-time metric snapshot."""
    metric_id: str
    metric_type: MetricType
    channel: str
    timestamp: datetime
    value: float
    unit: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SLAReport:
    """SLA compliance report."""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    overall_compliance: float
    sla_breaches: List[Dict[str, Any]]
    channel_compliance: Dict[str, float]
    priority_compliance: Dict[str, float]
    recommendations: List[str]
    metadata: Optional[Dict[str, Any]] = None


class NotificationSLAManager:
    """Manages SLA targets and compliance tracking."""
    
    def __init__(self):
        self.redis_client = redis_service.get_client()
        
        # Default SLA targets
        self.default_sla_targets = [
            # Delivery rate targets
            SLATarget(
                metric_type=MetricType.DELIVERY_RATE,
                channel="email",
                priority=None,
                target_value=99.5,
                target_unit="percentage",
                measurement_window="24h",
                description="Email delivery rate over 24 hours"
            ),
            SLATarget(
                metric_type=MetricType.DELIVERY_RATE,
                channel="sms",
                priority=None,
                target_value=99.0,
                target_unit="percentage",
                measurement_window="24h",
                description="SMS delivery rate over 24 hours"
            ),
            SLATarget(
                metric_type=MetricType.DELIVERY_RATE,
                channel="telegram",
                priority=None,
                target_value=98.0,
                target_unit="percentage",
                measurement_window="24h",
                description="Telegram delivery rate over 24 hours"
            ),
            SLATarget(
                metric_type=MetricType.DELIVERY_RATE,
                channel="in_app",
                priority=None,
                target_value=99.9,
                target_unit="percentage",
                measurement_window="24h",
                description="In-app notification delivery rate"
            ),
            
            # Delivery time targets
            SLATarget(
                metric_type=MetricType.DELIVERY_TIME,
                channel="email",
                priority=1,  # Critical priority
                target_value=30000,  # 30 seconds
                target_unit="milliseconds",
                measurement_window="1h",
                description="Critical email delivery time"
            ),
            SLATarget(
                metric_type=MetricType.DELIVERY_TIME,
                channel="email",
                priority=3,  # Normal priority
                target_value=300000,  # 5 minutes
                target_unit="milliseconds",
                measurement_window="1h",
                description="Normal email delivery time"
            ),
            SLATarget(
                metric_type=MetricType.DELIVERY_TIME,
                channel="sms",
                priority=1,  # Critical priority
                target_value=10000,  # 10 seconds
                target_unit="milliseconds",
                measurement_window="1h",
                description="Critical SMS delivery time"
            ),
            SLATarget(
                metric_type=MetricType.DELIVERY_TIME,
                channel="in_app",
                priority=None,
                target_value=1000,  # 1 second
                target_unit="milliseconds",
                measurement_window="1h",
                description="In-app notification delivery time"
            ),
            
            # Error rate targets
            SLATarget(
                metric_type=MetricType.ERROR_RATE,
                channel="email",
                priority=None,
                target_value=1.0,  # Max 1% error rate
                target_unit="percentage",
                measurement_window="1h",
                description="Email error rate"
            ),
            SLATarget(
                metric_type=MetricType.ERROR_RATE,
                channel="sms",
                priority=None,
                target_value=2.0,  # Max 2% error rate
                target_unit="percentage",
                measurement_window="1h",
                description="SMS error rate"
            ),
            
            # Throughput targets
            SLATarget(
                metric_type=MetricType.THROUGHPUT,
                channel="email",
                priority=None,
                target_value=1000,  # 1000 emails per minute
                target_unit="count_per_minute",
                measurement_window="5m",
                description="Email throughput capacity"
            ),
            SLATarget(
                metric_type=MetricType.THROUGHPUT,
                channel="sms",
                priority=None,
                target_value=500,  # 500 SMS per minute
                target_unit="count_per_minute",
                measurement_window="5m",
                description="SMS throughput capacity"
            )
        ]
    
    async def initialize_sla_targets(self):
        """Initialize SLA targets in database."""
        try:
            async with AsyncSessionLocal() as db:
                await self._create_metrics_tables(db)
                
                for target in self.default_sla_targets:
                    await self._store_sla_target(db, target)
                
                await db.commit()
                logger.info(f"Initialized {len(self.default_sla_targets)} SLA targets")
                
        except Exception as e:
            logger.error(f"Error initializing SLA targets: {e}")
            raise
    
    async def add_sla_target(self, target: SLATarget) -> bool:
        """Add custom SLA target."""
        try:
            async with AsyncSessionLocal() as db:
                await self._store_sla_target(db, target)
                await db.commit()
                logger.info(f"Added SLA target: {target.description}")
                return True
        except Exception as e:
            logger.error(f"Error adding SLA target: {e}")
            return False
    
    async def get_sla_targets(self, channel: Optional[str] = None) -> List[SLATarget]:
        """Get SLA targets, optionally filtered by channel."""
        try:
            async with AsyncSessionLocal() as db:
                if channel:
                    query = "SELECT * FROM notification_sla_targets WHERE channel = :channel"
                    result = await db.execute(text(query), {"channel": channel})
                else:
                    query = "SELECT * FROM notification_sla_targets"
                    result = await db.execute(text(query))
                
                targets = []
                for row in result.fetchall():
                    targets.append(SLATarget(
                        metric_type=MetricType(row.metric_type),
                        channel=row.channel,
                        priority=row.priority,
                        target_value=row.target_value,
                        target_unit=row.target_unit,
                        measurement_window=row.measurement_window,
                        description=row.description
                    ))
                
                return targets
                
        except Exception as e:
            logger.error(f"Error getting SLA targets: {e}")
            return []
    
    async def check_sla_compliance(self, target: SLATarget) -> Dict[str, Any]:
        """Check SLA compliance for a specific target."""
        try:
            # Calculate time window
            window_start = self._calculate_window_start(target.measurement_window)
            
            # Get metric data for the window
            metric_data = await self._get_metric_data(
                target.metric_type,
                target.channel,
                target.priority,
                window_start,
                datetime.utcnow()
            )
            
            if not metric_data:
                return {
                    "status": SLAStatus.UNKNOWN.value,
                    "current_value": None,
                    "target_value": target.target_value,
                    "compliance_percentage": None,
                    "samples_count": 0
                }
            
            # Calculate current metric value
            current_value = self._calculate_metric_value(target.metric_type, metric_data)
            
            # Determine compliance status
            status, compliance_percentage = self._determine_compliance_status(
                current_value, target.target_value, target.metric_type
            )
            
            return {
                "status": status.value,
                "current_value": current_value,
                "target_value": target.target_value,
                "compliance_percentage": compliance_percentage,
                "samples_count": len(metric_data),
                "window_start": window_start.isoformat(),
                "window_end": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking SLA compliance: {e}")
            return {
                "status": SLAStatus.UNKNOWN.value,
                "error": str(e)
            }
    
    async def generate_sla_report(
        self, 
        period_hours: int = 24,
        channels: Optional[List[str]] = None
    ) -> SLAReport:
        """Generate comprehensive SLA compliance report."""
        try:
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(hours=period_hours)
            
            # Get all relevant SLA targets
            all_targets = await self.get_sla_targets()
            if channels:
                all_targets = [t for t in all_targets if t.channel in channels]
            
            # Check compliance for each target
            compliance_results = []
            sla_breaches = []
            channel_compliance = defaultdict(list)
            priority_compliance = defaultdict(list)
            
            for target in all_targets:
                compliance = await self.check_sla_compliance(target)
                compliance_results.append({
                    "target": target,
                    "compliance": compliance
                })
                
                # Track breaches
                if compliance.get("status") == SLAStatus.BREACHED.value:
                    sla_breaches.append({
                        "metric_type": target.metric_type.value,
                        "channel": target.channel,
                        "priority": target.priority,
                        "target_value": target.target_value,
                        "current_value": compliance.get("current_value"),
                        "description": target.description
                    })
                
                # Group by channel
                if compliance.get("compliance_percentage") is not None:
                    channel_compliance[target.channel].append(compliance["compliance_percentage"])
                
                # Group by priority
                if target.priority and compliance.get("compliance_percentage") is not None:
                    priority_compliance[target.priority].append(compliance["compliance_percentage"])
            
            # Calculate overall compliance
            all_compliance_values = [
                r["compliance"]["compliance_percentage"] 
                for r in compliance_results 
                if r["compliance"].get("compliance_percentage") is not None
            ]
            overall_compliance = sum(all_compliance_values) / len(all_compliance_values) if all_compliance_values else 0
            
            # Calculate channel averages
            channel_averages = {
                channel: sum(values) / len(values) 
                for channel, values in channel_compliance.items()
            }
            
            # Calculate priority averages
            priority_averages = {
                priority: sum(values) / len(values) 
                for priority, values in priority_compliance.items()
            }
            
            # Generate recommendations
            recommendations = self._generate_recommendations(compliance_results, sla_breaches)
            
            report = SLAReport(
                report_id=str(uuid.uuid4()),
                generated_at=datetime.utcnow(),
                period_start=period_start,
                period_end=period_end,
                overall_compliance=overall_compliance,
                sla_breaches=sla_breaches,
                channel_compliance=channel_averages,
                priority_compliance=priority_averages,
                recommendations=recommendations,
                metadata={
                    "targets_evaluated": len(all_targets),
                    "compliance_results": len(compliance_results)
                }
            )
            
            # Store report
            await self._store_sla_report(report)
            
            logger.info(f"Generated SLA report: {overall_compliance:.2f}% compliance, {len(sla_breaches)} breaches")
            return report
            
        except Exception as e:
            logger.error(f"Error generating SLA report: {e}")
            raise
    
    def _calculate_window_start(self, measurement_window: str) -> datetime:
        """Calculate window start time from measurement window string."""
        now = datetime.utcnow()
        
        if measurement_window == "5m":
            return now - timedelta(minutes=5)
        elif measurement_window == "1h":
            return now - timedelta(hours=1)
        elif measurement_window == "24h":
            return now - timedelta(hours=24)
        elif measurement_window == "7d":
            return now - timedelta(days=7)
        else:
            # Default to 1 hour
            return now - timedelta(hours=1)
    
    async def _get_metric_data(
        self,
        metric_type: MetricType,
        channel: str,
        priority: Optional[int],
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get metric data from database for specified period."""
        try:
            async with AsyncSessionLocal() as db:
                # Build query based on metric type
                if metric_type == MetricType.DELIVERY_RATE:
                    query = """
                    SELECT 
                        channel,
                        priority,
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'sent' THEN 1 END) as successful,
                        DATE_TRUNC('minute', created_at) as time_bucket
                    FROM notification_log
                    WHERE channel = :channel
                    AND created_at BETWEEN :start_time AND :end_time
                    """
                    if priority is not None:
                        query += " AND priority = :priority"
                    query += " GROUP BY channel, priority, time_bucket ORDER BY time_bucket"
                    
                elif metric_type == MetricType.DELIVERY_TIME:
                    query = """
                    SELECT 
                        AVG(nda.latency_ms) as avg_latency,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nda.latency_ms) as median_latency,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY nda.latency_ms) as p95_latency,
                        DATE_TRUNC('minute', nda.attempted_at) as time_bucket
                    FROM notification_delivery_attempts nda
                    JOIN notification_log nl ON nda.message_id = nl.id
                    WHERE nl.channel = :channel
                    AND nda.status = 'sent'
                    AND nda.attempted_at BETWEEN :start_time AND :end_time
                    AND nda.latency_ms IS NOT NULL
                    """
                    if priority is not None:
                        query += " AND nl.priority = :priority"
                    query += " GROUP BY time_bucket ORDER BY time_bucket"
                    
                elif metric_type == MetricType.ERROR_RATE:
                    query = """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                        DATE_TRUNC('minute', created_at) as time_bucket
                    FROM notification_log
                    WHERE channel = :channel
                    AND created_at BETWEEN :start_time AND :end_time
                    """
                    if priority is not None:
                        query += " AND priority = :priority"
                    query += " GROUP BY time_bucket ORDER BY time_bucket"
                    
                elif metric_type == MetricType.THROUGHPUT:
                    query = """
                    SELECT 
                        COUNT(*) as count,
                        DATE_TRUNC('minute', created_at) as time_bucket
                    FROM notification_log
                    WHERE channel = :channel
                    AND created_at BETWEEN :start_time AND :end_time
                    """
                    if priority is not None:
                        query += " AND priority = :priority"
                    query += " GROUP BY time_bucket ORDER BY time_bucket"
                
                else:
                    return []
                
                params = {
                    "channel": channel,
                    "start_time": start_time,
                    "end_time": end_time
                }
                if priority is not None:
                    params["priority"] = priority
                
                result = await db.execute(text(query), params)
                return [dict(row._mapping) for row in result.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting metric data: {e}")
            return []
    
    def _calculate_metric_value(self, metric_type: MetricType, metric_data: List[Dict[str, Any]]) -> float:
        """Calculate the current metric value from raw data."""
        if not metric_data:
            return 0.0
        
        if metric_type == MetricType.DELIVERY_RATE:
            total_notifications = sum(row.get("total", 0) for row in metric_data)
            successful_notifications = sum(row.get("successful", 0) for row in metric_data)
            return (successful_notifications / total_notifications * 100) if total_notifications > 0 else 0.0
            
        elif metric_type == MetricType.DELIVERY_TIME:
            # Use P95 latency as the metric value
            p95_values = [row.get("p95_latency", 0) for row in metric_data if row.get("p95_latency")]
            return sum(p95_values) / len(p95_values) if p95_values else 0.0
            
        elif metric_type == MetricType.ERROR_RATE:
            total_notifications = sum(row.get("total", 0) for row in metric_data)
            failed_notifications = sum(row.get("failed", 0) for row in metric_data)
            return (failed_notifications / total_notifications * 100) if total_notifications > 0 else 0.0
            
        elif metric_type == MetricType.THROUGHPUT:
            # Average throughput per minute
            counts = [row.get("count", 0) for row in metric_data]
            return sum(counts) / len(counts) if counts else 0.0
        
        return 0.0
    
    def _determine_compliance_status(
        self, 
        current_value: float, 
        target_value: float, 
        metric_type: MetricType
    ) -> Tuple[SLAStatus, float]:
        """Determine SLA compliance status and percentage."""
        if metric_type in [MetricType.DELIVERY_RATE]:
            # Higher is better
            compliance_percentage = min(100.0, (current_value / target_value) * 100)
            if current_value >= target_value:
                status = SLAStatus.MET
            elif current_value >= target_value * 0.95:  # Within 95% of target
                status = SLAStatus.AT_RISK
            else:
                status = SLAStatus.BREACHED
                
        elif metric_type in [MetricType.DELIVERY_TIME, MetricType.ERROR_RATE]:
            # Lower is better
            compliance_percentage = min(100.0, (target_value / current_value) * 100) if current_value > 0 else 100.0
            if current_value <= target_value:
                status = SLAStatus.MET
            elif current_value <= target_value * 1.05:  # Within 105% of target
                status = SLAStatus.AT_RISK
            else:
                status = SLAStatus.BREACHED
                
        elif metric_type == MetricType.THROUGHPUT:
            # Higher is better (capacity)
            compliance_percentage = min(100.0, (current_value / target_value) * 100)
            if current_value >= target_value:
                status = SLAStatus.MET
            elif current_value >= target_value * 0.8:  # Within 80% of capacity
                status = SLAStatus.AT_RISK
            else:
                status = SLAStatus.BREACHED
        
        else:
            status = SLAStatus.UNKNOWN
            compliance_percentage = 0.0
        
        return status, compliance_percentage
    
    def _generate_recommendations(
        self, 
        compliance_results: List[Dict[str, Any]], 
        sla_breaches: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on SLA compliance results."""
        recommendations = []
        
        # Check for consistent breaches by channel
        breach_channels = defaultdict(int)
        for breach in sla_breaches:
            breach_channels[breach["channel"]] += 1
        
        for channel, breach_count in breach_channels.items():
            if breach_count >= 2:
                recommendations.append(
                    f"Channel {channel} has {breach_count} SLA breaches. "
                    f"Consider scaling infrastructure or reviewing configuration."
                )
        
        # Check for delivery time issues
        delivery_time_breaches = [
            b for b in sla_breaches 
            if b["metric_type"] == MetricType.DELIVERY_TIME.value
        ]
        
        if delivery_time_breaches:
            recommendations.append(
                "Delivery time SLA breaches detected. "
                "Consider optimizing notification processing pipeline or increasing worker capacity."
            )
        
        # Check for error rate issues
        error_rate_breaches = [
            b for b in sla_breaches 
            if b["metric_type"] == MetricType.ERROR_RATE.value
        ]
        
        if error_rate_breaches:
            recommendations.append(
                "High error rates detected. "
                "Review notification provider configurations and error handling logic."
            )
        
        # Check for throughput issues
        throughput_breaches = [
            b for b in sla_breaches 
            if b["metric_type"] == MetricType.THROUGHPUT.value
        ]
        
        if throughput_breaches:
            recommendations.append(
                "Throughput capacity issues detected. "
                "Consider scaling notification workers or increasing rate limits."
            )
        
        if not recommendations:
            recommendations.append("All SLA targets are being met. Continue monitoring.")
        
        return recommendations
    
    async def _create_metrics_tables(self, db: AsyncSession):
        """Create metrics and SLA tables."""
        create_sla_targets_table = """
        CREATE TABLE IF NOT EXISTS notification_sla_targets (
            target_id SERIAL PRIMARY KEY,
            metric_type VARCHAR(50) NOT NULL,
            channel VARCHAR(20) NOT NULL,
            priority INTEGER,
            target_value DECIMAL(10,3) NOT NULL,
            target_unit VARCHAR(20) NOT NULL,
            measurement_window VARCHAR(10) NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_sla_targets_channel ON notification_sla_targets(channel);
        CREATE INDEX IF NOT EXISTS idx_sla_targets_metric_type ON notification_sla_targets(metric_type);
        """
        
        create_sla_reports_table = """
        CREATE TABLE IF NOT EXISTS notification_sla_reports (
            report_id VARCHAR(36) PRIMARY KEY,
            generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            period_start TIMESTAMP WITH TIME ZONE NOT NULL,
            period_end TIMESTAMP WITH TIME ZONE NOT NULL,
            overall_compliance DECIMAL(5,2) NOT NULL,
            sla_breaches JSONB,
            channel_compliance JSONB,
            priority_compliance JSONB,
            recommendations JSONB,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_sla_reports_generated ON notification_sla_reports(generated_at);
        CREATE INDEX IF NOT EXISTS idx_sla_reports_compliance ON notification_sla_reports(overall_compliance);
        """
        
        create_metrics_snapshots_table = """
        CREATE TABLE IF NOT EXISTS notification_metric_snapshots (
            snapshot_id SERIAL PRIMARY KEY,
            metric_id VARCHAR(100) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            channel VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            value DECIMAL(12,4) NOT NULL,
            unit VARCHAR(20) NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_metric_snapshots_timestamp ON notification_metric_snapshots(timestamp);
        CREATE INDEX IF NOT EXISTS idx_metric_snapshots_channel_type ON notification_metric_snapshots(channel, metric_type);
        """
        
        await db.execute(text(create_sla_targets_table))
        await db.execute(text(create_sla_reports_table))
        await db.execute(text(create_metrics_snapshots_table))
    
    async def _store_sla_target(self, db: AsyncSession, target: SLATarget):
        """Store SLA target in database."""
        upsert_sql = """
        INSERT INTO notification_sla_targets (
            metric_type, channel, priority, target_value, target_unit,
            measurement_window, description
        ) VALUES (
            :metric_type, :channel, :priority, :target_value, :target_unit,
            :measurement_window, :description
        ) ON CONFLICT (metric_type, channel, COALESCE(priority, -1)) DO UPDATE SET
            target_value = EXCLUDED.target_value,
            target_unit = EXCLUDED.target_unit,
            measurement_window = EXCLUDED.measurement_window,
            description = EXCLUDED.description,
            updated_at = NOW()
        """
        
        await db.execute(text(upsert_sql), {
            "metric_type": target.metric_type.value,
            "channel": target.channel,
            "priority": target.priority,
            "target_value": target.target_value,
            "target_unit": target.target_unit,
            "measurement_window": target.measurement_window,
            "description": target.description
        })
    
    async def _store_sla_report(self, report: SLAReport):
        """Store SLA report in database."""
        try:
            async with AsyncSessionLocal() as db:
                insert_sql = """
                INSERT INTO notification_sla_reports (
                    report_id, generated_at, period_start, period_end,
                    overall_compliance, sla_breaches, channel_compliance,
                    priority_compliance, recommendations, metadata
                ) VALUES (
                    :report_id, :generated_at, :period_start, :period_end,
                    :overall_compliance, :sla_breaches, :channel_compliance,
                    :priority_compliance, :recommendations, :metadata
                )
                """
                
                await db.execute(text(insert_sql), {
                    "report_id": report.report_id,
                    "generated_at": report.generated_at,
                    "period_start": report.period_start,
                    "period_end": report.period_end,
                    "overall_compliance": report.overall_compliance,
                    "sla_breaches": json.dumps(report.sla_breaches),
                    "channel_compliance": json.dumps(report.channel_compliance),
                    "priority_compliance": json.dumps(report.priority_compliance),
                    "recommendations": json.dumps(report.recommendations),
                    "metadata": json.dumps(report.metadata) if report.metadata else None
                })
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error storing SLA report: {e}")


class NotificationMetricsCollector:
    """Collects and aggregates notification metrics."""
    
    def __init__(self):
        self.redis_client = redis_service.get_client()
        self.sla_manager = NotificationSLAManager()
        
    async def start_metrics_collection(self):
        """Start metrics collection background tasks."""
        logger.info("Starting notification metrics collection...")
        
        tasks = [
            asyncio.create_task(self._collect_realtime_metrics()),
            asyncio.create_task(self._generate_periodic_reports()),
            asyncio.create_task(self._cleanup_old_snapshots())
        ]
        
        await asyncio.gather(*tasks)
    
    async def record_metric_snapshot(self, snapshot: MetricSnapshot):
        """Record a metric snapshot."""
        try:
            async with AsyncSessionLocal() as db:
                insert_sql = """
                INSERT INTO notification_metric_snapshots (
                    metric_id, metric_type, channel, timestamp, value, unit, metadata
                ) VALUES (
                    :metric_id, :metric_type, :channel, :timestamp, :value, :unit, :metadata
                )
                """
                
                await db.execute(text(insert_sql), {
                    "metric_id": snapshot.metric_id,
                    "metric_type": snapshot.metric_type.value,
                    "channel": snapshot.channel,
                    "timestamp": snapshot.timestamp,
                    "value": snapshot.value,
                    "unit": snapshot.unit,
                    "metadata": json.dumps(snapshot.metadata) if snapshot.metadata else None
                })
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error recording metric snapshot: {e}")
    
    async def _collect_realtime_metrics(self):
        """Collect real-time metrics."""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                
                # Collect metrics for each channel
                channels = ["email", "sms", "telegram", "in_app", "push"]
                
                for channel in channels:
                    await self._collect_channel_metrics(channel)
                
            except Exception as e:
                logger.error(f"Error in realtime metrics collection: {e}")
    
    async def _collect_channel_metrics(self, channel: str):
        """Collect metrics for a specific channel."""
        try:
            timestamp = datetime.utcnow()
            
            # Collect delivery rate
            delivery_rate = await self._calculate_delivery_rate(channel, 5)  # Last 5 minutes
            if delivery_rate is not None:
                await self.record_metric_snapshot(MetricSnapshot(
                    metric_id=f"{channel}_delivery_rate_{timestamp.strftime('%Y%m%d_%H%M')}",
                    metric_type=MetricType.DELIVERY_RATE,
                    channel=channel,
                    timestamp=timestamp,
                    value=delivery_rate,
                    unit="percentage"
                ))
            
            # Collect error rate
            error_rate = await self._calculate_error_rate(channel, 5)  # Last 5 minutes
            if error_rate is not None:
                await self.record_metric_snapshot(MetricSnapshot(
                    metric_id=f"{channel}_error_rate_{timestamp.strftime('%Y%m%d_%H%M')}",
                    metric_type=MetricType.ERROR_RATE,
                    channel=channel,
                    timestamp=timestamp,
                    value=error_rate,
                    unit="percentage"
                ))
            
            # Collect throughput
            throughput = await self._calculate_throughput(channel, 1)  # Last 1 minute
            if throughput is not None:
                await self.record_metric_snapshot(MetricSnapshot(
                    metric_id=f"{channel}_throughput_{timestamp.strftime('%Y%m%d_%H%M')}",
                    metric_type=MetricType.THROUGHPUT,
                    channel=channel,
                    timestamp=timestamp,
                    value=throughput,
                    unit="count_per_minute"
                ))
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {channel}: {e}")
    
    async def _calculate_delivery_rate(self, channel: str, minutes: int) -> Optional[float]:
        """Calculate delivery rate for the last N minutes."""
        try:
            async with AsyncSessionLocal() as db:
                since_time = datetime.utcnow() - timedelta(minutes=minutes)
                
                query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'sent' THEN 1 END) as successful
                FROM notification_log
                WHERE channel = :channel
                AND created_at >= :since_time
                """
                
                result = await db.execute(text(query), {
                    "channel": channel,
                    "since_time": since_time
                })
                
                row = result.fetchone()
                if row and row.total > 0:
                    return (row.successful / row.total) * 100
                
                return None
                
        except Exception as e:
            logger.error(f"Error calculating delivery rate: {e}")
            return None
    
    async def _calculate_error_rate(self, channel: str, minutes: int) -> Optional[float]:
        """Calculate error rate for the last N minutes."""
        try:
            async with AsyncSessionLocal() as db:
                since_time = datetime.utcnow() - timedelta(minutes=minutes)
                
                query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
                FROM notification_log
                WHERE channel = :channel
                AND created_at >= :since_time
                """
                
                result = await db.execute(text(query), {
                    "channel": channel,
                    "since_time": since_time
                })
                
                row = result.fetchone()
                if row and row.total > 0:
                    return (row.failed / row.total) * 100
                
                return None
                
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return None
    
    async def _calculate_throughput(self, channel: str, minutes: int) -> Optional[float]:
        """Calculate throughput for the last N minutes."""
        try:
            async with AsyncSessionLocal() as db:
                since_time = datetime.utcnow() - timedelta(minutes=minutes)
                
                query = """
                SELECT COUNT(*) as count
                FROM notification_log
                WHERE channel = :channel
                AND created_at >= :since_time
                """
                
                result = await db.execute(text(query), {
                    "channel": channel,
                    "since_time": since_time
                })
                
                row = result.fetchone()
                if row:
                    return row.count / minutes  # notifications per minute
                
                return None
                
        except Exception as e:
            logger.error(f"Error calculating throughput: {e}")
            return None
    
    async def _generate_periodic_reports(self):
        """Generate periodic SLA reports."""
        while True:
            try:
                await asyncio.sleep(3600)  # Generate every hour
                
                # Generate hourly report
                await self.sla_manager.generate_sla_report(period_hours=1)
                
                # Generate daily report at midnight
                now = datetime.utcnow()
                if now.hour == 0 and now.minute < 1:
                    await self.sla_manager.generate_sla_report(period_hours=24)
                
            except Exception as e:
                logger.error(f"Error generating periodic reports: {e}")
    
    async def _cleanup_old_snapshots(self):
        """Clean up old metric snapshots."""
        while True:
            try:
                await asyncio.sleep(3600 * 6)  # Clean up every 6 hours
                
                async with AsyncSessionLocal() as db:
                    # Keep snapshots for 7 days
                    cleanup_date = datetime.utcnow() - timedelta(days=7)
                    
                    cleanup_sql = """
                    DELETE FROM notification_metric_snapshots 
                    WHERE timestamp < :cleanup_date
                    """
                    
                    result = await db.execute(text(cleanup_sql), {"cleanup_date": cleanup_date})
                    await db.commit()
                    
                    if result.rowcount > 0:
                        logger.info(f"Cleaned up {result.rowcount} old metric snapshots")
                        
            except Exception as e:
                logger.error(f"Error cleaning up old snapshots: {e}")


# Global instances
notification_sla_manager = NotificationSLAManager()
notification_metrics_collector = NotificationMetricsCollector()
