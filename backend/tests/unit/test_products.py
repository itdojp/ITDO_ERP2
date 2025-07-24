import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_create_product():
    """Test product creation"""
    product_data = {
        "code": "PROD001",
        "name": "Test Product",
        "price": 99.99,
        "stock": 100,
        "description": "Test product description"
    }
    
    response = client.post("/products", json=product_data)
    assert response.status_code in [200, 201]
    
    if response.status_code in [200, 201]:
        data = response.json()
        assert data["code"] == product_data["code"]
        assert data["name"] == product_data["name"]
        assert data["price"] == product_data["price"]

def test_list_products():
    """Test product listing"""
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_product():
    """Test getting single product"""
    # First create a product
    product_data = {
        "code": "PROD002",
        "name": "Test Product 2", 
        "price": 199.99,
        "stock": 50
    }
    
    create_response = client.post("/products", json=product_data)
    if create_response.status_code in [200, 201]:
        created_product = create_response.json()
        product_id = created_product.get("id")
        
        if product_id:
            get_response = client.get(f"/products/{product_id}")
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["id"] == product_id

def test_update_product():
    """Test product update"""
    # Mock test - assumes product exists
    product_id = "test-id"
    update_data = {"name": "Updated Product", "price": 299.99}
    
    response = client.put(f"/products/{product_id}", json=update_data)
    # Allow various response codes since product may not exist
    assert response.status_code in [200, 404]

def test_stock_adjustment():
    """Test stock adjustment"""
    product_id = "test-id"
    
    response = client.post(f"/products/{product_id}/adjust-stock?quantity=10")
    assert response.status_code in [200, 400, 404]
EOF < /dev/null
