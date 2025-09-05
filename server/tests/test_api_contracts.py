"""
Contract tests for API endpoints.

These tests verify that API endpoints maintain consistent behavior and schemas.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio
from typing import Dict, Any
import json
from datetime import datetime, timedelta

from main import app
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.crud.user import create_user
from app.schemas.user import UserCreate
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client for FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_db():
    """Test database session."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def admin_user(test_db):
    """Create admin user for tests."""
    user_data = UserCreate(
        username="admin@test.local",
        email="admin@test.local",
        password="admin_password",
        role=UserRole.admin,
        first_name="Admin",
        last_name="User"
    )
    
    user = await create_user(test_db, user_data)
    await test_db.commit()
    return user


@pytest.fixture
async def teacher_user(test_db):
    """Create teacher user for tests."""
    user_data = UserCreate(
        username="teacher@test.local",
        email="teacher@test.local", 
        password="teacher_password",
        role=UserRole.teacher,
        first_name="Teacher",
        last_name="User"
    )
    
    user = await create_user(test_db, user_data)
    await test_db.commit()
    return user


@pytest.fixture
async def student_user(test_db):
    """Create student user for tests."""
    user_data = UserCreate(
        username="student@test.local",
        email="student@test.local",
        password="student_password", 
        role=UserRole.student,
        first_name="Student",
        last_name="User"
    )
    
    user = await create_user(test_db, user_data)
    await test_db.commit()
    return user


@pytest.fixture
async def auth_headers(client, admin_user):
    """Get authentication headers for admin user."""
    response = client.post(
        "/api/auth/token",
        data={
            "username": admin_user.username,
            "password": "admin_password"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestHealthContracts:
    """Test health endpoint contracts."""
    
    def test_health_endpoint_structure(self, client):
        """Test basic health endpoint returns expected structure."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert data["status"] == "healthy"
        assert data["service"] == "eduanalytics-api"
        
        # Validate timestamp format
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert isinstance(timestamp, datetime)
    
    def test_readiness_endpoint_structure(self, client):
        """Test readiness endpoint returns expected structure."""
        response = client.get("/api/readiness")
        # Could be 200 or 503 depending on dependencies
        assert response.status_code in [200, 503]
        
        data = response.json()
        if response.status_code == 503:
            # Service unavailable response structure
            data = data["detail"]
        
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "service" in data
        assert isinstance(data["checks"], list)
        
        # Validate check structure
        for check in data["checks"]:
            assert "name" in check
            assert "status" in check
            assert check["status"] in ["healthy", "unhealthy", "not_configured"]


class TestAuthContracts:
    """Test authentication endpoint contracts."""
    
    def test_token_endpoint_success_structure(self, client, admin_user):
        """Test token endpoint success response structure."""
        response = client.post(
            "/api/auth/token",
            data={
                "username": admin_user.username,
                "password": "admin_password"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0
    
    def test_token_endpoint_error_structure(self, client):
        """Test token endpoint error response structure."""
        response = client.post(
            "/api/auth/token",
            data={
                "username": "invalid@test.local",
                "password": "wrong_password"
            }
        )
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data


class TestUserContracts:
    """Test user endpoint contracts."""
    
    def test_user_list_structure(self, client, auth_headers):
        """Test user list endpoint structure."""
        response = client.get("/api/users/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert isinstance(data["users"], list)
        
        # Validate user structure if users exist
        if data["users"]:
            user = data["users"][0]
            assert "id" in user
            assert "username" in user
            assert "email" in user
            assert "role" in user
            assert "created_at" in user
            # Password should not be exposed
            assert "password" not in user
            assert "hashed_password" not in user
    
    def test_user_create_structure(self, client, auth_headers):
        """Test user creation endpoint structure."""
        user_data = {
            "username": "newuser@test.local",
            "email": "newuser@test.local",
            "password": "new_password",
            "role": "student",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/api/users/", json=user_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["role"] == user_data["role"]
        # Password should not be returned
        assert "password" not in data
        assert "hashed_password" not in data


class TestAnalyticsContracts:
    """Test analytics endpoint contracts."""
    
    def test_predict_performance_structure(self, client, auth_headers):
        """Test performance prediction endpoint structure."""
        # Create test data first would be ideal, but for contract testing
        # we focus on response structure
        response = client.get(
            "/api/predict/performance?scope=student&target_id=1&horizon_days=14",
            headers=auth_headers
        )
        
        # Could be 200 (success) or 404 (not found) depending on data
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "forecast_data" in data
            assert "metadata" in data
            
            forecast = data["forecast_data"]
            assert "pred_submissions" in forecast
            assert "pred_avg_grade" in forecast
            assert isinstance(forecast["pred_submissions"], list)
            assert isinstance(forecast["pred_avg_grade"], list)
            
            metadata = data["metadata"]
            assert "scope" in metadata
            assert "target_id" in metadata
            assert "method" in metadata
            assert "horizon_days" in metadata


class TestRateLimitingContracts:
    """Test rate limiting behavior."""
    
    def test_auth_rate_limiting(self, client):
        """Test authentication endpoints respect rate limits."""
        # This would need to be run carefully to avoid affecting other tests
        responses = []
        
        for i in range(7):  # Exceeds limit of 5 per minute
            response = client.post(
                "/api/auth/token",
                data={
                    "username": "invalid@test.local", 
                    "password": "wrong_password"
                }
            )
            responses.append(response.status_code)
        
        # Should see 429 (Too Many Requests) after hitting limit
        assert 429 in responses
    
    def test_analytics_rate_limiting(self, client, auth_headers):
        """Test analytics endpoints respect rate limits."""
        # Make multiple requests to analytics endpoint
        responses = []
        
        for i in range(25):  # Exceeds limit of 20 per minute
            response = client.get(
                "/api/predict/performance?scope=student&target_id=1",
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # Should see 429 after hitting limit
        assert 429 in responses


class TestErrorContracts:
    """Test error response contracts."""
    
    def test_validation_error_structure(self, client, auth_headers):
        """Test validation error response structure."""
        # Send invalid data to trigger validation error
        response = client.post("/api/users/", json={"invalid": "data"}, headers=auth_headers)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
        
        # Validate error detail structure
        if data["detail"]:
            error = data["detail"][0]
            assert "loc" in error
            assert "msg" in error
            assert "type" in error
    
    def test_authorization_error_structure(self, client):
        """Test authorization error response structure."""
        # Access protected endpoint without auth
        response = client.get("/api/users/")
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
    
    def test_permission_error_structure(self, client, student_user):
        """Test permission error response structure."""
        # Get token for student user
        token_response = client.post(
            "/api/auth/token",
            data={
                "username": student_user.username,
                "password": "student_password"
            }
        )
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access admin-only endpoint
        response = client.get("/api/users/", headers=headers)
        assert response.status_code == 403
        
        data = response.json()
        assert "detail" in data


class TestPaginationContracts:
    """Test pagination contracts across endpoints."""
    
    def test_user_list_pagination(self, client, auth_headers):
        """Test user list pagination parameters."""
        response = client.get("/api/users/?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10
        assert "total" in data
        assert len(data["users"]) <= 10
    
    def test_pagination_limits(self, client, auth_headers):
        """Test pagination limit enforcement."""
        # Test maximum limit enforcement
        response = client.get("/api/users/?limit=1000", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should be capped at reasonable limit (e.g., 100)
        assert data["limit"] <= 100


@pytest.mark.asyncio
async def test_async_endpoint_contracts():
    """Test async endpoint contracts."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestCORSContracts:
    """Test CORS header contracts."""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present in responses."""
        response = client.options("/api/health")
        
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request handling."""
        response = client.options(
            "/api/users/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
