from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_diagnose_basic_smoke() -> None:
    response = client.post("/agent/diagnose", json={"symptoms": {"fever": True}})
    assert response.status_code == 200
    assert "X-Correlation-Id" in response.headers
