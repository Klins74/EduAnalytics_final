"""
Page View Tracking Middleware.

Automatically tracks page views for authenticated users to provide
comprehensive engagement analytics.
"""

import logging
import asyncio
import uuid
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.services.attendance_analytics import pageview_service, PageViewType
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


class PageViewTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track page views for analytics."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.excluded_paths = {
            "/docs", "/redoc", "/openapi.json", "/favicon.ico",
            "/health", "/metrics", "/api/health", "/api/attendance/page-views"
        }
        self.excluded_prefixes = {
            "/static/", "/assets/", "/api/auth/", "/_next/", "/api/webhooks/"
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and track page view if applicable."""
        start_time = datetime.utcnow()
        
        # Get response
        response = await call_next(request)
        
        # Only track successful GET requests
        if (request.method == "GET" and 
            response.status_code == 200 and 
            self._should_track_request(request)):
            
            # Track page view asynchronously (don't block response)
            asyncio.create_task(self._track_page_view(request, start_time))
        
        return response
    
    def _should_track_request(self, request: Request) -> bool:
        """Determine if this request should be tracked."""
        path = request.url.path
        
        # Skip excluded paths
        if path in self.excluded_paths:
            return False
        
        # Skip excluded prefixes
        if any(path.startswith(prefix) for prefix in self.excluded_prefixes):
            return False
        
        # Skip API endpoints that aren't user-facing
        if path.startswith("/api/") and not self._is_user_facing_api(path):
            return False
        
        return True
    
    def _is_user_facing_api(self, path: str) -> bool:
        """Check if an API endpoint is user-facing and should be tracked."""
        user_facing_api_prefixes = [
            "/api/courses/", "/api/assignments/", "/api/submissions/",
            "/api/discussions/", "/api/quizzes/", "/api/modules/",
            "/api/pages/", "/api/gradebook/", "/api/analytics/"
        ]
        
        return any(path.startswith(prefix) for prefix in user_facing_api_prefixes)
    
    async def _track_page_view(self, request: Request, start_time: datetime):
        """Track the page view asynchronously."""
        try:
            # Get user ID from token
            user_id = await self._get_user_id_from_request(request)
            if not user_id:
                return
            
            # Extract page information
            page_info = self._extract_page_info(request)
            
            # Calculate time on page (this is just request processing time, 
            # real time on page would need JavaScript tracking)
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            
            # Get or generate session ID
            session_id = self._get_session_id(request)
            
            # Record page view
            await pageview_service.record_page_view(
                user_id=user_id,
                course_id=page_info["course_id"],
                page_type=page_info["page_type"],
                page_url=str(request.url),
                session_id=session_id,
                page_id=page_info["page_id"],
                page_title=page_info["page_title"],
                time_on_page=processing_time if processing_time > 0 else None,
                referrer=request.headers.get("Referer"),
                user_agent=request.headers.get("User-Agent"),
                ip_address=self._get_client_ip(request)
            )
            
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"Error tracking page view: {e}")
    
    async def _get_user_id_from_request(self, request: Request) -> Optional[int]:
        """Extract user ID from JWT token in request."""
        try:
            # Get token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.replace("Bearer ", "")
            payload = decode_access_token(token)
            return payload.get("sub")  # user ID
            
        except Exception:
            return None
    
    def _extract_page_info(self, request: Request) -> dict:
        """Extract page information from the request."""
        path = request.url.path
        query_params = dict(request.query_params)
        
        # Initialize page info
        page_info = {
            "course_id": None,
            "page_type": PageViewType.OTHER,
            "page_id": None,
            "page_title": None
        }
        
        # Extract course ID from path or query params
        course_id = self._extract_course_id(path, query_params)
        page_info["course_id"] = course_id
        
        # Determine page type and details based on path
        if "/courses/" in path:
            page_info["page_type"] = PageViewType.COURSE_HOME
            if "/assignments/" in path:
                page_info["page_type"] = PageViewType.ASSIGNMENT
                page_info["page_id"] = self._extract_id_from_path(path, "assignments")
            elif "/discussions/" in path:
                page_info["page_type"] = PageViewType.DISCUSSION
                page_info["page_id"] = self._extract_id_from_path(path, "discussions")
            elif "/quizzes/" in path:
                page_info["page_type"] = PageViewType.QUIZ
                page_info["page_id"] = self._extract_id_from_path(path, "quizzes")
            elif "/modules/" in path:
                page_info["page_type"] = PageViewType.MODULE
                page_info["page_id"] = self._extract_id_from_path(path, "modules")
            elif "/pages/" in path:
                page_info["page_type"] = PageViewType.PAGE
                page_info["page_id"] = self._extract_id_from_path(path, "pages")
            elif "/gradebook" in path:
                page_info["page_type"] = PageViewType.GRADEBOOK
            elif "/syllabus" in path:
                page_info["page_type"] = PageViewType.SYLLABUS
            elif "/announcements" in path:
                page_info["page_type"] = PageViewType.ANNOUNCEMENTS
            elif "/files/" in path:
                page_info["page_type"] = PageViewType.FILE
                page_info["page_id"] = self._extract_id_from_path(path, "files")
        
        elif path.startswith("/api/"):
            # For API endpoints, determine type from the endpoint
            if "/assignments/" in path:
                page_info["page_type"] = PageViewType.ASSIGNMENT
                page_info["page_id"] = self._extract_id_from_path(path, "assignments")
            elif "/discussions/" in path:
                page_info["page_type"] = PageViewType.DISCUSSION
                page_info["page_id"] = self._extract_id_from_path(path, "discussions")
            elif "/quizzes/" in path:
                page_info["page_type"] = PageViewType.QUIZ
                page_info["page_id"] = self._extract_id_from_path(path, "quizzes")
            elif "/gradebook" in path:
                page_info["page_type"] = PageViewType.GRADEBOOK
            elif "/analytics" in path:
                page_info["page_type"] = PageViewType.OTHER
                page_info["page_title"] = "Analytics Dashboard"
        
        # Try to extract page title from query params or headers
        page_info["page_title"] = (
            query_params.get("title") or 
            query_params.get("name") or 
            self._generate_page_title(page_info["page_type"], page_info["page_id"])
        )
        
        return page_info
    
    def _extract_course_id(self, path: str, query_params: dict) -> Optional[int]:
        """Extract course ID from path or query parameters."""
        try:
            # Try query parameter first
            if "course_id" in query_params:
                return int(query_params["course_id"])
            
            # Try to extract from path
            if "/courses/" in path:
                parts = path.split("/courses/")
                if len(parts) > 1:
                    course_part = parts[1].split("/")[0]
                    if course_part.isdigit():
                        return int(course_part)
            
            # Try API path pattern
            if path.startswith("/api/") and "/courses/" in path:
                parts = path.split("/courses/")
                if len(parts) > 1:
                    course_part = parts[1].split("/")[0]
                    if course_part.isdigit():
                        return int(course_part)
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def _extract_id_from_path(self, path: str, resource_type: str) -> Optional[str]:
        """Extract resource ID from path."""
        try:
            if f"/{resource_type}/" in path:
                parts = path.split(f"/{resource_type}/")
                if len(parts) > 1:
                    id_part = parts[1].split("/")[0]
                    return id_part if id_part else None
            return None
        except (ValueError, IndexError):
            return None
    
    def _generate_page_title(self, page_type: PageViewType, page_id: Optional[str]) -> Optional[str]:
        """Generate a page title based on page type and ID."""
        type_titles = {
            PageViewType.COURSE_HOME: "Course Home",
            PageViewType.ASSIGNMENT: f"Assignment {page_id}" if page_id else "Assignment",
            PageViewType.DISCUSSION: f"Discussion {page_id}" if page_id else "Discussion",
            PageViewType.QUIZ: f"Quiz {page_id}" if page_id else "Quiz",
            PageViewType.MODULE: f"Module {page_id}" if page_id else "Module",
            PageViewType.PAGE: f"Page {page_id}" if page_id else "Course Page",
            PageViewType.FILE: f"File {page_id}" if page_id else "File",
            PageViewType.GRADEBOOK: "Gradebook",
            PageViewType.SYLLABUS: "Syllabus",
            PageViewType.ANNOUNCEMENTS: "Announcements",
            PageViewType.OTHER: "Course Content"
        }
        
        return type_titles.get(page_type, "Unknown Page")
    
    def _get_session_id(self, request: Request) -> str:
        """Get or generate session ID for the request."""
        # Try to get session ID from header
        session_id = request.headers.get("X-Session-ID")
        
        if not session_id:
            # Try to get from cookie
            session_id = request.cookies.get("session_id")
        
        if not session_id:
            # Generate new session ID
            session_id = str(uuid.uuid4())
        
        return session_id
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Get client IP address from request."""
        # Check for forwarded headers first (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return None


def create_page_tracking_middleware() -> PageViewTrackingMiddleware:
    """Create page view tracking middleware instance."""
    return PageViewTrackingMiddleware
