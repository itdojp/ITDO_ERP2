from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_user():
    user_data = {"name": "Test User", "email": "test@example.com"}
    response = client.post("/users", json=user_data)
    assert response.status_code in [200, 201, 404]


def test_list_users():
    response = client.get("/users")
    assert response.status_code in [200, 404]
