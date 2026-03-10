import os
import requests

BASE_URL = os.getenv("MODEL_SERVICE_URL", "http://localhost:8001")


def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"


def test_metrics_endpoint():
    response = requests.get(f"{BASE_URL}/metrics", timeout=10)
    assert response.status_code == 200
    assert "http_requests_total" in response.text or "http_request_duration_seconds" in response.text
