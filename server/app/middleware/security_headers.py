from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, csp: Optional[str] = None) -> None:
        super().__init__(app)
        self.csp = csp or (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 http://localhost:5173 http://127.0.0.1:5173; "
            "frame-ancestors 'none'"
        )

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Basic security headers
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'no-referrer')
        response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        response.headers.setdefault('Cross-Origin-Resource-Policy', 'same-site')
        response.headers.setdefault('Cross-Origin-Embedder-Policy', 'require-corp')
        if self.csp:
            response.headers.setdefault('Content-Security-Policy', self.csp)
        return response


