"""
Observability middleware for FastAPI application.

Integrates OpenTelemetry tracing and metrics into the request/response cycle.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.observability.tracing import get_tracer, add_span_attributes
from app.observability.metrics import get_metrics

logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for adding observability to all HTTP requests."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.tracer = get_tracer()
        self.metrics = get_metrics()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with observability instrumentation."""
        
        # Extract request information
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        
        # Start timing
        start_time = time.time()
        
        # Initialize response variables
        status_code = 500
        response = None
        
        try:
            # Add request attributes to current span
            if self.tracer:
                add_span_attributes(
                    http_method=method,
                    http_url=str(request.url),
                    http_scheme=request.url.scheme,
                    http_host=request.url.hostname,
                    http_user_agent=user_agent,
                    http_route=path
                )
            
            # Process request
            response = await call_next(request)
            status_code = response.status_code
            
            # Add response attributes to span
            if self.tracer:
                add_span_attributes(
                    http_status_code=status_code,
                    http_response_size=response.headers.get("content-length", 0)
                )
            
            return response
            
        except Exception as e:
            # Record exception in span
            if self.tracer:
                from app.observability.tracing import record_exception
                record_exception(e, {
                    "http.method": method,
                    "http.url": str(request.url)
                })
            
            # Increment error metrics
            if self.metrics:
                self.metrics.increment_api_errors(
                    endpoint=path,
                    error_type=type(e).__name__
                )
            
            logger.error(f"Request failed: {method} {path} - {str(e)}")
            raise
            
        finally:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Record metrics
            if self.metrics:
                # Increment request counter
                self.metrics.increment_api_requests(
                    endpoint=path,
                    method=method,
                    status_code=status_code
                )
                
                # Record request duration
                self.metrics.record_api_request_duration(
                    duration=duration,
                    endpoint=path,
                    method=method
                )
                
                # Record error metrics for non-2xx responses
                if status_code >= 400:
                    error_type = "client_error" if status_code < 500 else "server_error"
                    self.metrics.increment_api_errors(
                        endpoint=path,
                        error_type=error_type
                    )
            
            # Log request details
            logger.info(
                f"{method} {path} - {status_code} - {duration:.3f}s",
                extra={
                    "http_method": method,
                    "http_path": path,
                    "http_status_code": status_code,
                    "request_duration": duration,
                    "user_agent": user_agent
                }
            )


class AuthenticationMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for tracking authentication metrics."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = get_metrics()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track authentication-related metrics."""
        
        # Check if this is an authentication endpoint
        is_auth_endpoint = (
            request.url.path.startswith("/api/auth/") or
            request.url.path.startswith("/api/login/") or
            request.url.path.startswith("/api/logout/")
        )
        
        if not is_auth_endpoint or not self.metrics:
            return await call_next(request)
        
        # Process authentication request
        response = await call_next(request)
        
        # Track authentication metrics
        if request.url.path.endswith("/token"):
            # Login attempt
            if response.status_code == 200:
                # Successful authentication
                self.metrics.increment_auth_attempts("success")
                
                # Try to extract user role from response if available
                # This would require parsing the JWT or response body
                # For now, we'll track without role information
                
            else:
                # Failed authentication
                self.metrics.increment_auth_attempts("failure")
                self.metrics.auth_failures_total.add(1, {
                    "reason": "invalid_credentials" if response.status_code == 401 else "other"
                })
        
        elif request.url.path.endswith("/refresh"):
            # Token refresh attempt
            if response.status_code == 200:
                self.metrics.increment_auth_attempts("refresh_success")
            else:
                self.metrics.increment_auth_attempts("refresh_failure")
        
        return response


class DatabaseMetricsMiddleware:
    """Middleware for tracking database operation metrics."""
    
    def __init__(self):
        self.metrics = get_metrics()
    
    def track_db_operation(self, operation: str, table: str, duration: float, success: bool):
        """Track a database operation."""
        if not self.metrics:
            return
        
        # Record operation
        status = "success" if success else "error"
        self.metrics.increment_db_operations(operation, table, status)
        
        # Record duration
        self.metrics.record_db_query_duration(duration, operation)
        
        # Increment error counter if failed
        if not success:
            self.metrics.db_errors_total.add(1, {
                "operation": operation,
                "table": table
            })


class BusinessLogicMetricsTracker:
    """Helper class for tracking business logic metrics."""
    
    def __init__(self):
        self.metrics = get_metrics()
    
    def track_submission_processed(self, submission_type: str, status: str):
        """Track submission processing."""
        if self.metrics:
            self.metrics.submissions_processed_total.add(1, {
                "submission_type": submission_type,
                "status": status
            })
    
    def track_grade_assigned(self, assignment_type: str, grade_value: float):
        """Track grade assignment."""
        if self.metrics:
            self.metrics.grades_assigned_total.add(1, {
                "assignment_type": assignment_type,
                "grade_range": self._get_grade_range(grade_value)
            })
    
    def track_notification_sent(self, channel: str, success: bool, notification_type: str = ""):
        """Track notification sending."""
        if not self.metrics:
            return
        
        status = "success" if success else "failure"
        attributes = {
            "channel": channel,
            "status": status
        }
        
        if notification_type:
            attributes["notification_type"] = notification_type
        
        self.metrics.notifications_sent_total.add(1, attributes)
        
        if not success:
            self.metrics.notification_failures_total.add(1, {
                "channel": channel,
                "notification_type": notification_type
            })
    
    def track_canvas_api_call(self, endpoint: str, duration: float, success: bool):
        """Track Canvas API call."""
        if not self.metrics:
            return
        
        status = "success" if success else "error"
        self.metrics.increment_canvas_api_calls(endpoint, status)
        self.metrics.record_canvas_api_duration(duration, endpoint)
    
    def track_analytics_computation(self, computation_type: str, duration: float):
        """Track analytics computation."""
        if self.metrics:
            self.metrics.record_analytics_computation_duration(duration, computation_type)
    
    def track_file_upload(self, file_size: int, file_type: str):
        """Track file upload."""
        if self.metrics:
            self.metrics.record_file_upload_size(file_size, file_type)
    
    def _get_grade_range(self, grade: float) -> str:
        """Convert grade value to range category."""
        if grade >= 90:
            return "A"
        elif grade >= 80:
            return "B"
        elif grade >= 70:
            return "C"
        elif grade >= 60:
            return "D"
        else:
            return "F"


# Global instances
db_metrics = DatabaseMetricsMiddleware()
business_metrics = BusinessLogicMetricsTracker()


def get_db_metrics() -> DatabaseMetricsMiddleware:
    """Get database metrics tracker."""
    return db_metrics


def get_business_metrics() -> BusinessLogicMetricsTracker:
    """Get business logic metrics tracker."""
    return business_metrics
