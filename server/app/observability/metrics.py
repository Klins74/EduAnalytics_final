"""
OpenTelemetry metrics configuration for EduAnalytics.

Provides custom metrics for business logic, performance monitoring,
and operational insights.
"""

import os
import time
import logging
from typing import Optional, Dict, Any, Union
from contextvars import ContextVar
from functools import wraps

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from prometheus_client import start_http_server, CollectorRegistry

logger = logging.getLogger(__name__)


class MetricsConfig:
    """OpenTelemetry metrics configuration."""
    
    def __init__(self):
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "eduanalytics-api")
        self.service_version = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        self.environment = os.getenv("OTEL_ENVIRONMENT", "development")
        self.enabled = os.getenv("OTEL_METRICS_ENABLED", "false").lower() == "true"
        
        # Exporter configuration
        self.exporter_type = os.getenv("OTEL_METRICS_EXPORTER_TYPE", "prometheus")  # prometheus, otlp
        self.prometheus_port = int(os.getenv("OTEL_METRICS_PROMETHEUS_PORT", "9090"))
        self.otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "http://localhost:4317")
        
        # Collection interval
        self.collection_interval = int(os.getenv("OTEL_METRICS_INTERVAL", "30"))


class EduAnalyticsMetrics:
    """Custom metrics for EduAnalytics application."""
    
    def __init__(self, meter: metrics.Meter):
        self.meter = meter
        self._setup_counters()
        self._setup_histograms()
        self._setup_gauges()
    
    def _setup_counters(self):
        """Set up counter metrics."""
        # API request counters
        self.api_requests_total = self.meter.create_counter(
            name="eduanalytics_api_requests_total",
            description="Total number of API requests",
            unit="1"
        )
        
        self.api_errors_total = self.meter.create_counter(
            name="eduanalytics_api_errors_total", 
            description="Total number of API errors",
            unit="1"
        )
        
        # Authentication metrics
        self.auth_attempts_total = self.meter.create_counter(
            name="eduanalytics_auth_attempts_total",
            description="Total number of authentication attempts",
            unit="1"
        )
        
        self.auth_failures_total = self.meter.create_counter(
            name="eduanalytics_auth_failures_total",
            description="Total number of authentication failures", 
            unit="1"
        )
        
        # Database operation counters
        self.db_operations_total = self.meter.create_counter(
            name="eduanalytics_db_operations_total",
            description="Total number of database operations",
            unit="1"
        )
        
        self.db_errors_total = self.meter.create_counter(
            name="eduanalytics_db_errors_total",
            description="Total number of database errors",
            unit="1"
        )
        
        # Canvas integration metrics
        self.canvas_api_calls_total = self.meter.create_counter(
            name="eduanalytics_canvas_api_calls_total",
            description="Total number of Canvas API calls",
            unit="1"
        )
        
        self.canvas_sync_operations_total = self.meter.create_counter(
            name="eduanalytics_canvas_sync_operations_total",
            description="Total number of Canvas sync operations",
            unit="1"
        )
        
        # Business logic metrics
        self.submissions_processed_total = self.meter.create_counter(
            name="eduanalytics_submissions_processed_total",
            description="Total number of submissions processed",
            unit="1"
        )
        
        self.grades_assigned_total = self.meter.create_counter(
            name="eduanalytics_grades_assigned_total",
            description="Total number of grades assigned",
            unit="1"
        )
        
        # Notification metrics
        self.notifications_sent_total = self.meter.create_counter(
            name="eduanalytics_notifications_sent_total",
            description="Total number of notifications sent",
            unit="1"
        )
        
        self.notification_failures_total = self.meter.create_counter(
            name="eduanalytics_notification_failures_total",
            description="Total number of notification failures",
            unit="1"
        )
    
    def _setup_histograms(self):
        """Set up histogram metrics for latency and duration tracking."""
        # API response time
        self.api_request_duration = self.meter.create_histogram(
            name="eduanalytics_api_request_duration_seconds",
            description="API request duration in seconds",
            unit="s"
        )
        
        # Database query duration
        self.db_query_duration = self.meter.create_histogram(
            name="eduanalytics_db_query_duration_seconds", 
            description="Database query duration in seconds",
            unit="s"
        )
        
        # Canvas API call duration
        self.canvas_api_duration = self.meter.create_histogram(
            name="eduanalytics_canvas_api_duration_seconds",
            description="Canvas API call duration in seconds",
            unit="s"
        )
        
        # Analytics computation duration
        self.analytics_computation_duration = self.meter.create_histogram(
            name="eduanalytics_analytics_computation_duration_seconds",
            description="Analytics computation duration in seconds",
            unit="s"
        )
        
        # File upload size
        self.file_upload_size = self.meter.create_histogram(
            name="eduanalytics_file_upload_size_bytes",
            description="File upload size in bytes",
            unit="By"
        )
    
    def _setup_gauges(self):
        """Set up gauge metrics for current state tracking."""
        # Active users
        self.active_users = self.meter.create_up_down_counter(
            name="eduanalytics_active_users",
            description="Number of currently active users",
            unit="1"
        )
        
        # Active sessions
        self.active_sessions = self.meter.create_up_down_counter(
            name="eduanalytics_active_sessions",
            description="Number of active user sessions",
            unit="1"
        )
        
        # Queue sizes
        self.notification_queue_size = self.meter.create_up_down_counter(
            name="eduanalytics_notification_queue_size",
            description="Number of notifications in queue",
            unit="1"
        )
        
        # Cache hit rate
        self.cache_operations_total = self.meter.create_counter(
            name="eduanalytics_cache_operations_total",
            description="Total cache operations",
            unit="1"
        )
    
    # Counter methods
    def increment_api_requests(self, endpoint: str, method: str, status_code: int):
        """Increment API request counter."""
        self.api_requests_total.add(1, {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code)
        })
    
    def increment_api_errors(self, endpoint: str, error_type: str):
        """Increment API error counter."""
        self.api_errors_total.add(1, {
            "endpoint": endpoint,
            "error_type": error_type
        })
    
    def increment_auth_attempts(self, result: str, user_role: Optional[str] = None):
        """Increment authentication attempt counter."""
        attributes = {"result": result}
        if user_role:
            attributes["user_role"] = user_role
        self.auth_attempts_total.add(1, attributes)
    
    def increment_db_operations(self, operation: str, table: str, status: str):
        """Increment database operation counter."""
        self.db_operations_total.add(1, {
            "operation": operation,
            "table": table,
            "status": status
        })
    
    def increment_canvas_api_calls(self, endpoint: str, status: str):
        """Increment Canvas API call counter."""
        self.canvas_api_calls_total.add(1, {
            "endpoint": endpoint,
            "status": status
        })
    
    def increment_notifications_sent(self, channel: str, status: str):
        """Increment notification counter."""
        self.notifications_sent_total.add(1, {
            "channel": channel,
            "status": status
        })
    
    # Histogram methods
    def record_api_request_duration(self, duration: float, endpoint: str, method: str):
        """Record API request duration."""
        self.api_request_duration.record(duration, {
            "endpoint": endpoint,
            "method": method
        })
    
    def record_db_query_duration(self, duration: float, operation: str):
        """Record database query duration."""
        self.db_query_duration.record(duration, {
            "operation": operation
        })
    
    def record_canvas_api_duration(self, duration: float, endpoint: str):
        """Record Canvas API call duration."""
        self.canvas_api_duration.record(duration, {
            "endpoint": endpoint
        })
    
    def record_analytics_computation_duration(self, duration: float, computation_type: str):
        """Record analytics computation duration."""
        self.analytics_computation_duration.record(duration, {
            "computation_type": computation_type
        })
    
    def record_file_upload_size(self, size: int, file_type: str):
        """Record file upload size."""
        self.file_upload_size.record(size, {
            "file_type": file_type
        })
    
    # Gauge methods
    def set_active_users(self, count: int):
        """Set active users count."""
        self.active_users.add(count)
    
    def increment_active_sessions(self):
        """Increment active sessions."""
        self.active_sessions.add(1)
    
    def decrement_active_sessions(self):
        """Decrement active sessions."""
        self.active_sessions.add(-1)


def setup_metrics() -> Optional[EduAnalyticsMetrics]:
    """
    Initialize OpenTelemetry metrics.
    
    Returns:
        EduAnalyticsMetrics instance if enabled, None otherwise
    """
    config = MetricsConfig()
    
    if not config.enabled:
        logger.info("OpenTelemetry metrics disabled")
        return None
    
    logger.info(f"Initializing OpenTelemetry metrics for {config.service_name}")
    
    # Create resource
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: config.service_name,
        ResourceAttributes.SERVICE_VERSION: config.service_version,
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: config.environment,
    })
    
    # Configure metric readers
    readers = []
    
    if config.exporter_type == "prometheus":
        # Prometheus exporter
        try:
            prometheus_reader = PrometheusMetricReader()
            readers.append(prometheus_reader)
            
            # Start Prometheus HTTP server
            start_http_server(config.prometheus_port)
            logger.info(f"Prometheus metrics server started on port {config.prometheus_port}")
            
        except Exception as e:
            logger.error(f"Failed to configure Prometheus exporter: {e}")
    
    elif config.exporter_type == "otlp":
        # OTLP exporter
        try:
            otlp_exporter = OTLPMetricExporter(
                endpoint=config.otlp_endpoint,
                insecure=True
            )
            otlp_reader = PeriodicExportingMetricReader(
                exporter=otlp_exporter,
                export_interval_millis=config.collection_interval * 1000
            )
            readers.append(otlp_reader)
            logger.info(f"OTLP metrics exporter configured: {config.otlp_endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to configure OTLP metrics exporter: {e}")
    
    # Set up meter provider
    meter_provider = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(meter_provider)
    
    # Create meter and custom metrics
    meter = metrics.get_meter(__name__)
    custom_metrics = EduAnalyticsMetrics(meter)
    
    logger.info(f"OpenTelemetry metrics initialized with {config.exporter_type} exporter")
    return custom_metrics


def time_function(metric_recorder, operation_name: str):
    """
    Decorator to time function execution and record metrics.
    
    Args:
        metric_recorder: Method to record the timing metric
        operation_name: Name of the operation being timed
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metric_recorder(duration, operation_name)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metric_recorder(duration, operation_name)
                raise
        return wrapper
    return decorator


def time_async_function(metric_recorder, operation_name: str):
    """
    Decorator to time async function execution and record metrics.
    
    Args:
        metric_recorder: Method to record the timing metric
        operation_name: Name of the operation being timed
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metric_recorder(duration, operation_name)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metric_recorder(duration, operation_name)
                raise
        return wrapper
    return decorator


# Global metrics instance
_metrics_instance: Optional[EduAnalyticsMetrics] = None


def get_metrics() -> Optional[EduAnalyticsMetrics]:
    """Get the global metrics instance."""
    return _metrics_instance


def init_global_metrics():
    """Initialize global metrics instance."""
    global _metrics_instance
    _metrics_instance = setup_metrics()


# Context manager for timing operations
class MetricsTimer:
    """Context manager for timing operations."""
    
    def __init__(self, recorder, operation_name: str):
        self.recorder = recorder
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.recorder(duration, self.operation_name)
