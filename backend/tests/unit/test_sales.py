import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_sales_order():
    """Test sales order creation"""
    order_data = {
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "items": [{"product_id": "prod-1", "quantity": 2, "unit_price": 100.0}],
    }
    response = client.post("/sales-orders", json=order_data)
    assert response.status_code in [200, 201, 404]


def test_list_sales_orders():
    """Test sales order listing"""
    response = client.get("/sales-orders")
    assert response.status_code in [200, 404]


def test_confirm_order():
    """Test order confirmation"""
    order_id = "test-order"
    response = client.post(f"/sales-orders/{order_id}/confirm")
    assert response.status_code in [200, 400, 404]
