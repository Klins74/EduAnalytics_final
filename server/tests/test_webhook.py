import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_webhook_notify_success():
    payload = {
        "event_type": "test_notification",
        "data": {"message": "Test webhook"},
        "notification_channels": ["email"]
    }
    response = client.post("/api/v1/n8n/notify", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "event_id" in response.json()

def test_webhook_notify_invalid_event():
    payload = {
        "event_type": "invalid_event",
        "data": {},
        "notification_channels": ["email"]
    }
    response = client.post("/api/v1/n8n/notify", json=payload)
    assert response.status_code == 400 or response.status_code == 422

def test_webhook_health():
    response = client.get("/api/v1/n8n/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"