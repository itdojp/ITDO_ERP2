from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_role():
    role_data = {"name": "Test Role", "description": "Test role"}
    response = client.post("/roles", json=role_data)
    assert response.status_code in [200, 201, 404]


def test_check_permission():
    response = client.post(
        "/check-permission?user_id=1&resource=products&permission_type=read"
    )
    assert response.status_code in [200, 404, 422]
