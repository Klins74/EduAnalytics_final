"""
API versioning and standardization middleware.

Handles API versioning, response standardization, and request/response logging.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import uuid

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.api_pagination import APIVersioning, APIResponseBuilder

logger = logging.getLogger(__name__)


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Middleware for API versioning and standardization."""
    
    def __init__(self, app: ASGIApp, default_version: str = "v1"):
        super().__init__(app)
        self.default_version = default_version
        self.api_versioning = APIVersioning()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with versioning and standardization."""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Extract API version from path
        api_version = self._extract_version(request)
        request.state.api_version = api_version
        
        # Validate API version
        if not self.api_versioning.is_supported_version(api_version):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIResponseBuilder.error(
                    message=f"Unsupported API version: {api_version}",
                    code="UNSUPPORTED_API_VERSION",
                    details={
                        "requested_version": api_version,
                        "supported_versions": self.api_versioning.SUPPORTED_VERSIONS
                    }
                )
            )
        
        # Log request
        await self._log_request(request, request_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Process response
            response = await self._process_response(request, response, start_time, request_id)
            
            return response
            
        except HTTPException as e:
            # Handle HTTP exceptions
            return await self._handle_http_exception(e, request_id)
            
        except Exception as e:
            # Handle unexpected exceptions
            return await self._handle_unexpected_exception(e, request_id)
    
    def _extract_version(self, request: Request) -> str:
        """Extract API version from request."""
        # Try to get version from path
        path_version = self.api_versioning.get_version_from_path(request.url.path)
        if path_version != self.api_versioning.DEFAULT_VERSION:
            return path_version
        
        # Try to get version from header
        header_version = request.headers.get("API-Version")
        if header_version and self.api_versioning.is_supported_version(header_version):
            return header_version
        
        # Try to get version from query parameter
        query_version = request.query_params.get("version")
        if query_version and self.api_versioning.is_supported_version(query_version):
            return query_version
        
        return self.default_version
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request."""
        try:
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "api_version": request.state.api_version,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log request body for POST/PUT/PATCH (be careful with sensitive data)
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        body = await request.body()
                        if body:
                            # Don't log sensitive endpoints
                            sensitive_paths = ["/auth/login", "/auth/register", "/users/password"]
                            is_sensitive = any(path in request.url.path for path in sensitive_paths)
                            
                            if not is_sensitive:
                                log_data["body"] = json.loads(body.decode())
                            else:
                                log_data["body"] = "[REDACTED - SENSITIVE]"
                    except:
                        log_data["body"] = "[INVALID JSON]"
            
            logger.info(f"API Request: {json.dumps(log_data)}")
            
        except Exception as e:
            logger.error(f"Error logging request: {e}")
    
    async def _process_response(self, request: Request, response: Response, 
                              start_time: float, request_id: str) -> Response:
        """Process and standardize response."""
        try:
            processing_time = time.time() - start_time
            
            # Add standard headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-API-Version"] = request.state.api_version
            response.headers["X-Processing-Time"] = f"{processing_time:.4f}s"
            response.headers["X-Timestamp"] = datetime.utcnow().isoformat()
            
            # Log response
            await self._log_response(request, response, processing_time, request_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return response
    
    async def _log_response(self, request: Request, response: Response, 
                          processing_time: float, request_id: str):
        """Log outgoing response."""
        try:
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "processing_time": processing_time,
                "api_version": request.state.api_version,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log response body for errors or if explicitly requested
            if response.status_code >= 400 or request.query_params.get("log_response") == "true":
                try:
                    if hasattr(response, 'body') and response.body:
                        body_text = response.body.decode() if isinstance(response.body, bytes) else str(response.body)
                        log_data["response_body"] = body_text[:1000]  # Limit size
                except:
                    log_data["response_body"] = "[UNABLE TO READ]"
            
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(log_level, f"API Response: {json.dumps(log_data)}")
            
        except Exception as e:
            logger.error(f"Error logging response: {e}")
    
    async def _handle_http_exception(self, exc: HTTPException, request_id: str) -> JSONResponse:
        """Handle HTTP exceptions with standardized response."""
        try:
            error_response = APIResponseBuilder.error(
                message=exc.detail if exc.detail else "HTTP Error",
                code=f"HTTP_{exc.status_code}",
                details={
                    "status_code": exc.status_code,
                    "request_id": request_id
                }
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response,
                headers={
                    "X-Request-ID": request_id,
                    "X-Error-Type": "HTTP_EXCEPTION"
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling HTTP exception: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )
    
    async def _handle_unexpected_exception(self, exc: Exception, request_id: str) -> JSONResponse:
        """Handle unexpected exceptions."""
        try:
            logger.error(f"Unexpected exception in request {request_id}: {exc}", exc_info=True)
            
            error_response = APIResponseBuilder.error(
                message="Internal server error",
                code="INTERNAL_SERVER_ERROR",
                details={
                    "request_id": request_id,
                    "error_type": type(exc).__name__
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response,
                headers={
                    "X-Request-ID": request_id,
                    "X-Error-Type": "UNEXPECTED_EXCEPTION"
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling unexpected exception: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Critical server error"}
            )


class ResponseStandardizationMiddleware(BaseHTTPMiddleware):
    """Middleware for standardizing API responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Standardize API responses."""
        response = await call_next(request)
        
        # Only process JSON responses from API endpoints
        if (request.url.path.startswith("/api/") and 
            isinstance(response, JSONResponse) and 
            response.status_code < 400):
            
            try:
                # Get original response content
                original_content = json.loads(response.body.decode())
                
                # Check if already standardized
                if not isinstance(original_content, dict) or "success" not in original_content:
                    # Standardize the response
                    standardized_content = APIResponseBuilder.success(
                        data=original_content,
                        message="Request completed successfully"
                    )
                    
                    # Create new response with standardized content
                    response = JSONResponse(
                        content=standardized_content,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
            
            except Exception as e:
                logger.error(f"Error standardizing response: {e}")
        
        return response


class APIMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = {}
        self.response_times = {}
        self.error_count = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect API metrics."""
        start_time = time.time()
        
        # Extract endpoint info
        endpoint = self._get_endpoint_key(request)
        
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(endpoint, response.status_code, processing_time)
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_metrics(endpoint, 500, processing_time)
            raise
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Generate endpoint key for metrics."""
        # Normalize path by removing IDs
        path_parts = request.url.path.strip("/").split("/")
        normalized_parts = []
        
        for part in path_parts:
            if part.isdigit():
                normalized_parts.append("{id}")
            else:
                normalized_parts.append(part)
        
        normalized_path = "/" + "/".join(normalized_parts)
        return f"{request.method} {normalized_path}"
    
    def _update_metrics(self, endpoint: str, status_code: int, processing_time: float):
        """Update endpoint metrics."""
        try:
            # Request count
            if endpoint not in self.request_count:
                self.request_count[endpoint] = 0
            self.request_count[endpoint] += 1
            
            # Response times
            if endpoint not in self.response_times:
                self.response_times[endpoint] = []
            self.response_times[endpoint].append(processing_time)
            
            # Keep only last 1000 response times
            if len(self.response_times[endpoint]) > 1000:
                self.response_times[endpoint] = self.response_times[endpoint][-1000:]
            
            # Error count
            if status_code >= 400:
                if endpoint not in self.error_count:
                    self.error_count[endpoint] = 0
                self.error_count[endpoint] += 1
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        try:
            summary = {
                "endpoints": {},
                "total_requests": sum(self.request_count.values()),
                "total_errors": sum(self.error_count.values()),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            for endpoint in self.request_count.keys():
                response_times = self.response_times.get(endpoint, [])
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                summary["endpoints"][endpoint] = {
                    "request_count": self.request_count.get(endpoint, 0),
                    "error_count": self.error_count.get(endpoint, 0),
                    "avg_response_time": round(avg_response_time, 4),
                    "error_rate": (self.error_count.get(endpoint, 0) / self.request_count.get(endpoint, 1)) * 100
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {"error": str(e)}


# Global middleware instances for metrics access
api_metrics_middleware = None

def get_api_metrics() -> Optional[Dict[str, Any]]:
    """Get current API metrics."""
    global api_metrics_middleware
    if api_metrics_middleware:
        return api_metrics_middleware.get_metrics_summary()
    return None
