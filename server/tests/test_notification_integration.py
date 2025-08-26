import os
import pytest
import requests
from datetime import datetime, timezone

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/eduanalytics-webhook")

def test_real_n8n_webhook():
    """
    Интеграционный тест: отправка реального webhook в n8n instance
    """
    payload = {
        "event_type": "integration_test",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "data": {
            "message": "Integration test from pytest",
            "test": True
        }
    }
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        assert response.status_code == 200
    except requests.exceptions.RequestException as e:
        pytest.skip(f"n8n instance not available: {e}")