"""
CC02 v54.0 Simple Products API Tests - Issue #579
Basic Unit Testing for Product Management API
"""

import pytest
from fastapi.testclient import TestClient
from app.main_super_minimal import app

class TestProductsV54Simple:
    """Simple Products API Test Suite"""
    
    @pytest.fixture(autouse=True)
    def setup_clean_state(self):
        """Clear in-memory stores before each test"""
        from app.api.v1.products_v54_simple import products_db, categories_db
        products_db.clear()
        categories_db.clear()
    
    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client"""
        return TestClient(app)
    
    def test_create_category(self, client: TestClient):
        """Test category creation"""
        category_data = {
            "name": "Electronics",
            "description": "Electronic products"
        }
        
        response = client.post("/api/v1/products-v54/categories/", json=category_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Electronics"
        assert data["description"] == "Electronic products"
        assert data["product_count"] == 0
        assert "id" in data
        assert "created_at" in data
    
    def test_list_categories_empty(self, client: TestClient):
        """Test listing categories when empty"""
        response = client.get("/api/v1/products-v54/categories/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_product_basic(self, client: TestClient):
        """Test basic product creation"""
        product_data = {
            "name": "Laptop",
            "description": "Gaming laptop",
            "price": 999.99,
            "stock_quantity": 10,
            "sku": "LAP001"
        }
        
        response = client.post("/api/v1/products-v54/products/", json=product_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Laptop"
        assert data["description"] == "Gaming laptop"
        assert data["price"] == 999.99
        assert data["stock_quantity"] == 10
        assert data["sku"] == "LAP001"
        assert data["category_id"] is None
        assert data["category_name"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_product_with_category(self, client: TestClient):
        """Test product creation with category"""
        # Create category first
        category_response = client.post("/api/v1/products-v54/categories/", json={
            "name": "Electronics"
        })
        category_id = category_response.json()["id"]
        
        # Create product with category
        product_data = {
            "name": "Smartphone",
            "price": 599.99,
            "category_id": category_id
        }
        
        response = client.post("/api/v1/products-v54/products/", json=product_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["category_id"] == category_id
        assert data["category_name"] == "Electronics"
    
    def test_create_product_invalid_category(self, client: TestClient):
        """Test product creation with invalid category"""
        product_data = {
            "name": "Invalid Product",
            "price": 100.0,
            "category_id": "invalid-category-id"
        }
        
        response = client.post("/api/v1/products-v54/products/", json=product_data)
        assert response.status_code == 400
        assert "Category not found" in response.json()["detail"]
    
    def test_create_product_duplicate_sku(self, client: TestClient):
        """Test product creation with duplicate SKU"""
        product_data = {
            "name": "Product 1",
            "price": 100.0,
            "sku": "DUPLICATE"
        }
        
        # Create first product
        response1 = client.post("/api/v1/products-v54/products/", json=product_data)
        assert response1.status_code == 201
        
        # Try to create second product with same SKU
        product_data["name"] = "Product 2"
        response2 = client.post("/api/v1/products-v54/products/", json=product_data)
        assert response2.status_code == 400
        assert "SKU already exists" in response2.json()["detail"]
    
    def test_list_products_empty(self, client: TestClient):
        """Test listing products when empty"""
        response = client.get("/api/v1/products-v54/products/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_products_with_filtering(self, client: TestClient):
        """Test listing products with filters"""
        # Create category
        category_response = client.post("/api/v1/products-v54/categories/", json={
            "name": "Electronics"
        })
        category_id = category_response.json()["id"]
        
        # Create products
        products = [
            {"name": "Laptop", "price": 999.99, "category_id": category_id},
            {"name": "Mouse", "price": 29.99, "category_id": category_id},
            {"name": "Book", "price": 19.99}
        ]
        
        for product in products:
            client.post("/api/v1/products-v54/products/", json=product)
        
        # Test basic listing
        response = client.get("/api/v1/products-v54/products/")
        assert response.status_code == 200
        assert len(response.json()) == 3
        
        # Test category filtering
        response = client.get(f"/api/v1/products-v54/products/?category_id={category_id}")
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Test search filtering
        response = client.get("/api/v1/products-v54/products/?search=Laptop")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Laptop"
        
        # Test limit
        response = client.get("/api/v1/products-v54/products/?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_get_product(self, client: TestClient):
        """Test getting specific product"""
        # Create product
        product_data = {"name": "Test Product", "price": 100.0}
        create_response = client.post("/api/v1/products-v54/products/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get product
        response = client.get(f"/api/v1/products-v54/products/{product_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == "Test Product"
        assert data["price"] == 100.0
    
    def test_get_product_not_found(self, client: TestClient):
        """Test getting non-existent product"""
        response = client.get("/api/v1/products-v54/products/invalid-id")
        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]
    
    def test_update_product(self, client: TestClient):
        """Test updating product"""
        # Create product
        product_data = {"name": "Original Name", "price": 100.0}
        create_response = client.post("/api/v1/products-v54/products/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update product
        update_data = {"name": "Updated Name", "price": 150.0, "stock_quantity": 5}
        response = client.put(f"/api/v1/products-v54/products/{product_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["price"] == 150.0
        assert data["stock_quantity"] == 5
    
    def test_update_product_not_found(self, client: TestClient):
        """Test updating non-existent product"""
        update_data = {"name": "Updated Name", "price": 150.0}
        response = client.put("/api/v1/products-v54/products/invalid-id", json=update_data)
        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]
    
    def test_delete_product(self, client: TestClient):
        """Test deleting product"""
        # Create product
        product_data = {"name": "To Delete", "price": 100.0}
        create_response = client.post("/api/v1/products-v54/products/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Delete product
        response = client.delete(f"/api/v1/products-v54/products/{product_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion
        get_response = client.get(f"/api/v1/products-v54/products/{product_id}")
        assert get_response.status_code == 404
    
    def test_get_product_stats(self, client: TestClient):
        """Test getting product statistics"""
        # Create category
        category_response = client.post("/api/v1/products-v54/categories/", json={
            "name": "Test Category"
        })
        
        # Create products
        products = [
            {"name": "Product 1", "price": 100.0, "stock_quantity": 5},
            {"name": "Product 2", "price": 200.0, "stock_quantity": 15},
            {"name": "Product 3", "price": 300.0, "stock_quantity": 8}
        ]
        
        for product in products:
            client.post("/api/v1/products-v54/products/", json=product)
        
        # Get statistics
        response = client.get("/api/v1/products-v54/products/stats/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_products"] == 3
        assert data["total_categories"] == 1
        assert data["total_stock_quantity"] == 28
        assert data["average_price"] == 200.0
        assert data["low_stock_products"] == 2  # Products with stock <= 10
    
    def test_performance_requirement(self, client: TestClient):
        """Test that responses are under 500ms"""
        import time
        
        # Test product creation
        start_time = time.time()
        response = client.post("/api/v1/products-v54/products/", json={
            "name": "Performance Test",
            "price": 100.0
        })
        end_time = time.time()
        
        assert response.status_code == 201
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 500, f"Product creation took {execution_time_ms:.2f}ms"
        
        # Test product listing
        start_time = time.time()
        response = client.get("/api/v1/products-v54/products/")
        end_time = time.time()
        
        assert response.status_code == 200
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 500, f"Product listing took {execution_time_ms:.2f}ms"