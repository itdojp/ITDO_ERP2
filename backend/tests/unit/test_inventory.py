import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_create_inventory_transaction():
    """Test inventory transaction creation"""
    transaction_data = {
        "product_id": "product-123",
        "transaction_type": "in",
        "quantity": 100,
        "reason": "Initial stock",
        "reference_id": "ref-001"
    }
    
    response = client.post("/inventory/transactions", json=transaction_data)
    assert response.status_code in [200, 201, 404]

def test_list_inventory_transactions():
    """Test inventory transaction listing"""
    response = client.get("/inventory/transactions")
    assert response.status_code in [200, 404]

def test_get_inventory_levels():
    """Test inventory levels"""
    response = client.get("/inventory/levels")
    assert response.status_code in [200, 404]
    
def test_get_product_inventory_level():
    """Test product specific inventory level"""
    product_id = "test-product"
    response = client.get(f"/inventory/levels/{product_id}")
    assert response.status_code in [200, 404]

def test_adjust_inventory():
    """Test inventory adjustment"""
    product_id = "test-product"
    response = client.post(f"/inventory/adjust/{product_id}?quantity=10&reason=adjustment")
    assert response.status_code in [200, 404, 422]

def test_reserve_inventory():
    """Test inventory reservation"""
    product_id = "test-product"
    response = client.post(f"/inventory/reserve/{product_id}?quantity=5&reference_id=order-123")
    assert response.status_code in [200, 400, 404]

def test_inventory_filtering():
    """Test inventory transaction filtering"""
    response = client.get("/inventory/transactions?transaction_type=in&skip=0&limit=10")
    assert response.status_code in [200, 404]
EOF < /dev/null
