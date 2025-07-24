from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_404_endpoints():
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_invalid_json():
    response = client.post("/products", data="invalid json")
    assert response.status_code in [400, 422]


def test_missing_required_fields():
    response = client.post("/products", json={})
    assert response.status_code in [400, 422]
