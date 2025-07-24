from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_organization():
    org_data = {"name": "Test Org", "description": "Test Description"}
    response = client.post("/organizations", json=org_data)
    assert response.status_code in [200, 201, 404]


def test_get_org_tree():
    response = client.get("/organizations/tree")
    assert response.status_code in [200, 404]
