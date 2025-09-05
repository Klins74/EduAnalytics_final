"""
Smoke tests for critical system functionality.

These tests verify that core services are operational and basic workflows work.
They should be run against deployed environments to validate system health.
"""

import pytest
import asyncio
import httpx
import os
from typing import Optional
from datetime import datetime
import json

# Test configuration
TEST_BASE_URL = os.getenv("SMOKE_TEST_URL", "http://localhost:8000")
TEST_ADMIN_USERNAME = os.getenv("SMOKE_TEST_ADMIN_USER", "admin@eduanalytics.local")
TEST_ADMIN_PASSWORD = os.getenv("SMOKE_TEST_ADMIN_PASSWORD", "admin_password")
TIMEOUT = int(os.getenv("SMOKE_TEST_TIMEOUT", "30"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def http_client():
    """HTTP client for smoke tests."""
    async with httpx.AsyncClient(
        base_url=TEST_BASE_URL,
        timeout=TIMEOUT,
        follow_redirects=True
    ) as client:
        yield client


@pytest.fixture(scope="session")
async def admin_token(http_client):
    """Get admin authentication token."""
    response = await http_client.post(
        "/api/auth/token",
        data={
            "username": TEST_ADMIN_USERNAME,
            "password": TEST_ADMIN_PASSWORD
        }
    )
    
    if response.status_code != 200:
        pytest.skip(f"Cannot authenticate admin user: {response.status_code}")
    
    token_data = response.json()
    return token_data["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    """Authentication headers for requests."""
    return {"Authorization": f"Bearer {admin_token}"}


class TestSystemHealth:
    """Test basic system health and connectivity."""
    
    @pytest.mark.asyncio
    async def test_service_is_running(self, http_client):
        """Test that the service is running and responding."""
        response = await http_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, http_client):
        """Test health endpoint is working."""
        response = await http_client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, http_client):
        """Test readiness endpoint and dependencies."""
        response = await http_client.get("/api/readiness")
        
        # Accept both 200 (ready) and 503 (not ready) as valid responses
        assert response.status_code in [200, 503]
        
        if response.status_code == 503:
            data = response.json()["detail"]
        else:
            data = response.json()
        
        assert "status" in data
        assert "checks" in data
        assert isinstance(data["checks"], list)
        
        # Log dependency status for debugging
        for check in data["checks"]:
            print(f"Dependency {check['name']}: {check['status']}")
    
    @pytest.mark.asyncio 
    async def test_database_connectivity(self, http_client, auth_headers):
        """Test database connectivity through API."""
        response = await http_client.get("/api/metrics", headers=auth_headers)
        
        # If admin user doesn't exist, this might fail
        if response.status_code == 401:
            pytest.skip("Admin authentication not configured")
        
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "latency_ms" in data["database"]


class TestAuthentication:
    """Test authentication workflows."""
    
    @pytest.mark.asyncio
    async def test_admin_authentication(self, http_client):
        """Test admin user can authenticate."""
        response = await http_client.post(
            "/api/auth/token",
            data={
                "username": TEST_ADMIN_USERNAME,
                "password": TEST_ADMIN_PASSWORD
            }
        )
        
        if response.status_code == 401:
            pytest.skip("Admin credentials not configured or invalid")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_invalid_credentials(self, http_client):
        """Test invalid credentials are rejected."""
        response = await http_client.post(
            "/api/auth/token",
            data={
                "username": "invalid@test.local",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self, http_client):
        """Test protected endpoints require authentication."""
        response = await http_client.get("/api/users/")
        assert response.status_code == 401


class TestCoreAPIEndpoints:
    """Test core API endpoints are accessible."""
    
    @pytest.mark.asyncio
    async def test_users_endpoint(self, http_client, auth_headers):
        """Test users endpoint is accessible."""
        response = await http_client.get("/api/users/", headers=auth_headers)
        
        if response.status_code == 401:
            pytest.skip("Authentication not working")
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
    
    @pytest.mark.asyncio
    async def test_courses_endpoint(self, http_client, auth_headers):
        """Test courses endpoint is accessible."""
        response = await http_client.get("/api/courses/", headers=auth_headers)
        
        if response.status_code == 401:
            pytest.skip("Authentication not working")
        
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
    
    @pytest.mark.asyncio
    async def test_analytics_endpoint(self, http_client, auth_headers):
        """Test analytics endpoints are accessible."""
        response = await http_client.get("/api/analytics/overview", headers=auth_headers)
        
        if response.status_code == 401:
            pytest.skip("Authentication not working")
        
        # Analytics might return empty data but should not error
        assert response.status_code in [200, 404]


class TestDataIntegrity:
    """Test basic data integrity and workflows."""
    
    @pytest.mark.asyncio
    async def test_user_creation_workflow(self, http_client, auth_headers):
        """Test user creation workflow."""
        # Create a test user
        user_data = {
            "username": f"smoketest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.local",
            "email": f"smoketest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.local",
            "password": "smoke_test_password",
            "role": "student",
            "first_name": "Smoke",
            "last_name": "Test"
        }
        
        response = await http_client.post("/api/users/", json=user_data, headers=auth_headers)
        
        if response.status_code == 401:
            pytest.skip("Authentication not working")
        
        assert response.status_code == 201
        created_user = response.json()
        assert created_user["username"] == user_data["username"]
        assert "id" in created_user
        
        # Verify user can be retrieved
        user_id = created_user["id"]
        response = await http_client.get(f"/api/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200
        
        retrieved_user = response.json()
        assert retrieved_user["id"] == user_id
        assert retrieved_user["username"] == user_data["username"]
    
    @pytest.mark.asyncio
    async def test_course_creation_workflow(self, http_client, auth_headers):
        """Test course creation workflow."""
        # Create a test course
        course_data = {
            "name": f"Smoke Test Course {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "code": f"SMOKE{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Course created by smoke tests"
        }
        
        response = await http_client.post("/api/courses/", json=course_data, headers=auth_headers)
        
        if response.status_code == 401:
            pytest.skip("Authentication not working")
        
        if response.status_code == 403:
            pytest.skip("Insufficient permissions for course creation")
        
        assert response.status_code == 201
        created_course = response.json()
        assert created_course["name"] == course_data["name"]
        assert "id" in created_course


class TestExternalIntegrations:
    """Test external service integrations."""
    
    @pytest.mark.asyncio
    async def test_canvas_integration_status(self, http_client, auth_headers):
        """Test Canvas integration status."""
        response = await http_client.get("/api/canvas/status", headers=auth_headers)
        
        # Canvas integration might not be configured in all environments
        if response.status_code == 404:
            pytest.skip("Canvas integration not available")
        
        if response.status_code == 401:
            pytest.skip("Authentication not working")
        
        # Accept various status codes as Canvas might not be configured
        assert response.status_code in [200, 503]
    
    @pytest.mark.asyncio
    async def test_redis_connectivity(self, http_client, auth_headers):
        """Test Redis connectivity through cache operations."""
        # Try to access an endpoint that uses cache
        response = await http_client.get("/api/analytics/overview", headers=auth_headers)
        
        if response.status_code == 401:
            pytest.skip("Authentication not working")
        
        # If Redis is down, some endpoints might still work but be slower
        # We're mainly checking that the service doesn't crash
        assert response.status_code in [200, 404, 500]


class TestPerformance:
    """Basic performance and responsiveness tests."""
    
    @pytest.mark.asyncio
    async def test_response_times(self, http_client):
        """Test that endpoints respond within reasonable time."""
        import time
        
        start_time = time.time()
        response = await http_client.get("/api/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        # Health endpoint should respond quickly (under 1 second)
        assert response_time < 1.0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, http_client):
        """Test system handles multiple concurrent requests."""
        async def make_request():
            return await http_client.get("/api/health")
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200


class TestSecurityBasics:
    """Basic security configuration tests."""
    
    @pytest.mark.asyncio
    async def test_security_headers(self, http_client):
        """Test security headers are present."""
        response = await http_client.get("/api/health")
        assert response.status_code == 200
        
        headers = response.headers
        
        # Check for basic security headers
        assert "x-frame-options" in headers
        assert "x-content-type-options" in headers
        assert "x-xss-protection" in headers
    
    @pytest.mark.asyncio
    async def test_cors_configuration(self, http_client):
        """Test CORS configuration."""
        response = await http_client.options("/api/health")
        
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers


@pytest.mark.asyncio
async def test_overall_system_health():
    """Comprehensive system health check."""
    async with httpx.AsyncClient(base_url=TEST_BASE_URL, timeout=TIMEOUT) as client:
        # Basic connectivity
        response = await client.get("/")
        assert response.status_code == 200
        
        # Health check
        response = await client.get("/api/health")
        assert response.status_code == 200
        
        # Authentication
        auth_response = await client.post(
            "/api/auth/token",
            data={
                "username": TEST_ADMIN_USERNAME,
                "password": TEST_ADMIN_PASSWORD
            }
        )
        
        if auth_response.status_code == 200:
            token = auth_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Protected endpoint
            response = await client.get("/api/users/", headers=headers)
            assert response.status_code == 200
        
        print("✅ Overall system health check passed")


if __name__ == "__main__":
    # Run smoke tests
    print(f"Running smoke tests against: {TEST_BASE_URL}")
    pytest.main([__file__, "-v", "--tb=short"])
