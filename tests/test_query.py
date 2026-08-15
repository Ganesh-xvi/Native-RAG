from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "index_loaded" in payload


def test_query_requires_api_key():
    response = client.post("/query", json={"question": "test"})
    assert response.status_code == 422
