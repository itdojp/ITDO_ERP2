from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sales_summary():
    response = client.get("/reports/sales-summary")
    assert response.status_code in [200, 404]


def test_inventory_status():
    response = client.get("/reports/inventory-status")
    assert response.status_code in [200, 404]
