#!/usr/bin/env python3
"""
Minimal FastAPI application for testing basic functionality.
Excludes complex modules that have import issues.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Core imports
from app.core.config import settings
from app.api.v1.routes import (
    users, 
    course, 
    assignment, 
    submission, 
    grades,
    auth,
    health
)

app = FastAPI(
    title="EduAnalytics API (Minimal)",
    description="Educational Analytics Platform - Minimal Version",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include basic routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])  # /api/v1/token
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])  # /api/v1/users
app.include_router(course.router, prefix="/api/v1/courses", tags=["Courses"])  # /api/v1/courses
app.include_router(assignment.router, prefix="/api/v1/assignments", tags=["Assignments"])  # /api/v1/assignments
app.include_router(submission.router, prefix="/api/v1/submissions", tags=["Submissions"])  # /api/v1/submissions
app.include_router(grades.router, prefix="/api/v1/grades", tags=["Grades"])  # /api/v1/grades

@app.get("/")
async def root():
    return {
        "message": "EduAnalytics API is running!",
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "eduanalytics-api",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    print("🚀 Starting EduAnalytics API (minimal mode)...")
    uvicorn.run(
        "main_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

