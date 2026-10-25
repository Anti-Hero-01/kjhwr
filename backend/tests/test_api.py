from fastapi.testclient import TestClient
from app.config import settings
from app.main import app


def test_required_endpoints_and_csv(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", True)
    client = TestClient(app)
    for path in ("/api/dates", "/api/analysis", "/api/accuracy", "/api/forecast-history"):
        response = client.get(path)
        assert response.status_code == 200
    response = client.get("/api/export.csv")
    assert response.status_code == 200
    assert "timestamp,forecast_mw,actual_mw,method" in response.text
