"""
OpenTelemetry tracing configuration for EduAnalytics.

Provides distributed tracing across API endpoints, database operations,
external service calls, and background workers.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextvars import ContextVar

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

logger = logging.getLogger(__name__)

# Context variable for tracking custom trace attributes
trace_context: ContextVar[Dict[str, Any]] = ContextVar('trace_context', default={})


class TracingConfig:
    """OpenTelemetry tracing configuration."""
    
    def __init__(self):
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "eduanalytics-api")
        self.service_version = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        self.environment = os.getenv("OTEL_ENVIRONMENT", "development")
        self.enabled = os.getenv("OTEL_TRACING_ENABLED", "false").lower() == "true"
        
        # Exporter configuration
        self.exporter_type = os.getenv("OTEL_EXPORTER_TYPE", "console")  # console, otlp, jaeger
        self.otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        self.jaeger_endpoint = os.getenv("OTEL_EXPORTER_JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
        
        # Sampling configuration
        self.sample_rate = float(os.getenv("OTEL_TRACE_SAMPLE_RATE", "0.1"))


def setup_tracing(app=None) -> Optional[trace.Tracer]:
    """
    Initialize OpenTelemetry tracing.
    
    Args:
        app: FastAPI application instance for instrumentation
        
    Returns:
        Tracer instance if enabled, None otherwise
    """
    config = TracingConfig()
    
    if not config.enabled:
        logger.info("OpenTelemetry tracing disabled")
        return None
    
    logger.info(f"Initializing OpenTelemetry tracing for {config.service_name}")
    
    # Create resource with service information
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: config.service_name,
        ResourceAttributes.SERVICE_VERSION: config.service_version,
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: config.environment,
    })
    
    # Set up tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Configure exporters
    _configure_exporters(tracer_provider, config)
    
    # Set up auto-instrumentation
    _setup_auto_instrumentation(app)
    
    # Create tracer
    tracer = trace.get_tracer(__name__)
    
    logger.info(f"OpenTelemetry tracing initialized with {config.exporter_type} exporter")
    return tracer


def _configure_exporters(tracer_provider: TracerProvider, config: TracingConfig):
    """Configure trace exporters based on configuration."""
    
    if config.exporter_type == "console":
        # Console exporter for development
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(
            BatchSpanProcessor(console_exporter)
        )
        
    elif config.exporter_type == "otlp":
        # OTLP exporter for standard observability backends
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=config.otlp_endpoint,
                insecure=True  # Use TLS in production
            )
            tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            logger.info(f"OTLP exporter configured: {config.otlp_endpoint}")
        except Exception as e:
            logger.error(f"Failed to configure OTLP exporter: {e}")
            
    elif config.exporter_type == "jaeger":
        # Jaeger exporter
        try:
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )
            tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
            logger.info("Jaeger exporter configured")
        except Exception as e:
            logger.error(f"Failed to configure Jaeger exporter: {e}")
    
    else:
        logger.warning(f"Unknown exporter type: {config.exporter_type}")


def _setup_auto_instrumentation(app):
    """Set up automatic instrumentation for common libraries."""
    
    try:
        # FastAPI instrumentation
        if app:
            FastAPIInstrumentor.instrument_app(app)
            logger.debug("FastAPI instrumentation enabled")
        
        # Database instrumentation
        SQLAlchemyInstrumentor().instrument()
        Psycopg2Instrumentor().instrument()
        logger.debug("Database instrumentation enabled")
        
        # Redis instrumentation
        RedisInstrumentor().instrument()
        logger.debug("Redis instrumentation enabled")
        
        # HTTP client instrumentation
        HTTPXClientInstrumentor().instrument()
        logger.debug("HTTP client instrumentation enabled")
        
    except Exception as e:
        logger.error(f"Failed to set up auto-instrumentation: {e}")


def get_tracer() -> trace.Tracer:
    """Get the configured tracer instance."""
    return trace.get_tracer(__name__)


def trace_function(operation_name: str, **attributes):
    """
    Decorator for tracing function calls.
    
    Args:
        operation_name: Name of the operation being traced
        **attributes: Additional span attributes
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                # Add custom attributes
                for key, value in attributes.items():
                    span.set_attribute(key, value)
                
                # Add function metadata
                span.set_attribute("code.function", func.__name__)
                span.set_attribute("code.namespace", func.__module__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(
                        trace.Status(
                            trace.StatusCode.ERROR, 
                            description=str(e)
                        )
                    )
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


async def trace_async_function(operation_name: str, **attributes):
    """
    Decorator for tracing async function calls.
    
    Args:
        operation_name: Name of the operation being traced
        **attributes: Additional span attributes
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                # Add custom attributes
                for key, value in attributes.items():
                    span.set_attribute(key, value)
                
                # Add function metadata
                span.set_attribute("code.function", func.__name__)
                span.set_attribute("code.namespace", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(
                        trace.Status(
                            trace.StatusCode.ERROR, 
                            description=str(e)
                        )
                    )
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def add_span_attributes(**attributes):
    """Add attributes to the current span."""
    span = trace.get_current_span()
    if span:
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Add an event to the current span."""
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes or {})


def record_exception(exception: Exception, attributes: Optional[Dict[str, Any]] = None):
    """Record an exception in the current span."""
    span = trace.get_current_span()
    if span:
        span.record_exception(exception, attributes)
        span.set_status(
            trace.Status(
                trace.StatusCode.ERROR, 
                description=str(exception)
            )
        )


class TracingContext:
    """Context manager for custom tracing spans."""
    
    def __init__(self, operation_name: str, **attributes):
        self.operation_name = operation_name
        self.attributes = attributes
        self.span = None
    
    def __enter__(self):
        tracer = get_tracer()
        self.span = tracer.start_span(self.operation_name)
        
        # Add custom attributes
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type is not None:
                self.span.set_status(
                    trace.Status(
                        trace.StatusCode.ERROR, 
                        description=str(exc_val)
                    )
                )
                self.span.record_exception(exc_val)
            else:
                self.span.set_status(trace.Status(trace.StatusCode.OK))
            
            self.span.end()


# Convenience function for creating tracing contexts
def trace_operation(operation_name: str, **attributes):
    """Create a tracing context for an operation."""
    return TracingContext(operation_name, **attributes)


# Pre-configured tracers for different components
class ComponentTracers:
    """Pre-configured tracers for different system components."""
    
    @staticmethod
    def get_api_tracer():
        """Get tracer for API operations."""
        return trace.get_tracer("eduanalytics.api")
    
    @staticmethod
    def get_database_tracer():
        """Get tracer for database operations."""
        return trace.get_tracer("eduanalytics.database")
    
    @staticmethod
    def get_canvas_tracer():
        """Get tracer for Canvas integration operations."""
        return trace.get_tracer("eduanalytics.canvas")
    
    @staticmethod
    def get_analytics_tracer():
        """Get tracer for analytics operations.""" 
        return trace.get_tracer("eduanalytics.analytics")
    
    @staticmethod
    def get_worker_tracer():
        """Get tracer for background worker operations."""
        return trace.get_tracer("eduanalytics.worker")
