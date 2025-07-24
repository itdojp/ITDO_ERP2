"""
TDD Tests for Products API Endpoints - CC02 v49.0 Implementation Overdrive
48-Hour Backend Blitz - Test-First Mandatory Approach
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import uuid
from datetime import datetime

class TestProductsAPI:
    """Test suite for Products API endpoints - TDD Implementation"""

    def test_create_product(self, api_client: TestClient):
        """Test product creation endpoint"""
        product_data = {"name": "Test", "price": 100, "sku": "TEST001"}
        response = api_client.post("/api/v1/products", json=product_data)
        
        # Debug response if not 201
        if response.status_code != 201:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        
        assert response.status_code == 201
        assert response.json()["name"] == "Test"
        assert response.json()["price"] == 100
        assert response.json()["sku"] == "TEST001"
        assert "id" in response.json()
        assert "created_at" in response.json()

    def test_create_product_validation_error(self, api_client: TestClient):
        """Test product creation with validation errors"""
        # Missing required fields
        invalid_data = {"name": "Test"}  # Missing price and sku
        response = api_client.post("/api/v1/products", json=invalid_data)
        assert response.status_code == 422

    def test_create_product_duplicate_sku(self, api_client: TestClient):
        """Test product creation with duplicate SKU"""
        product_data = {"name": "Test1", "price": 100, "sku": "DUPLICATE001"}
        
        # Create first product
        response1 = api_client.post("/api/v1/products", json=product_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        duplicate_data = {"name": "Test2", "price": 200, "sku": "DUPLICATE001"}
        response2 = api_client.post("/api/v1/products", json=duplicate_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_get_product_by_id(self, api_client: TestClient):
        """Test retrieving product by ID"""
        # Create product first
        product_data = {"name": "Get Test", "price": 150, "sku": "GET001"}
        create_response = api_client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get product
        response = api_client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        assert response.json()["id"] == product_id
        assert response.json()["name"] == "Get Test"

    def test_get_product_not_found(self, api_client: TestClient):
        """Test retrieving non-existent product"""
        fake_id = str(uuid.uuid4())
        response = api_client.get(f"/api/v1/products/{fake_id}")
        assert response.status_code == 404

    def test_list_products(self, api_client: TestClient):
        """Test listing all products"""
        # Create test products
        products = [
            {"name": "List Test 1", "price": 100, "sku": "LIST001"},
            {"name": "List Test 2", "price": 200, "sku": "LIST002"},
            {"name": "List Test 3", "price": 300, "sku": "LIST003"},
        ]
        
        for product in products:
            api_client.post("/api/v1/products", json=product)
        
        # List products
        response = api_client.get("/api/v1/products")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3
        assert "total" in data
        assert "page" in data
        assert "size" in data

    def test_list_products_with_pagination(self, api_client: TestClient):
        """Test product listing with pagination"""
        # Create test products
        for i in range(10):
            product = {"name": f"Page Test {i}", "price": 100 + i, "sku": f"PAGE{i:03d}"}
            api_client.post("/api/v1/products", json=product)
        
        # Test pagination
        response = api_client.get("/api/v1/products?page=1&size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        assert data["page"] == 1
        assert data["size"] == 5

    def test_list_products_with_search(self, api_client: TestClient):
        """Test product listing with search functionality"""
        # Create searchable products
        products = [
            {"name": "iPhone 15 Pro", "price": 999, "sku": "IPHONE001"},
            {"name": "Samsung Galaxy", "price": 899, "sku": "SAMSUNG001"},
            {"name": "MacBook Pro", "price": 1999, "sku": "MACBOOK001"},
        ]
        
        for product in products:
            api_client.post("/api/v1/products", json=product)
        
        # Search by name
        response = api_client.get("/api/v1/products?search=iPhone")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert "iPhone" in data["items"][0]["name"]

    def test_update_product(self, api_client: TestClient):
        """Test updating product"""
        # Create product
        product_data = {"name": "Update Test", "price": 100, "sku": "UPDATE001"}
        create_response = api_client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update product
        update_data = {"name": "Updated Test", "price": 150}
        response = api_client.put(f"/api/v1/products/{product_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Test"
        assert response.json()["price"] == 150
        assert response.json()["sku"] == "UPDATE001"  # Should remain unchanged

    def test_update_product_not_found(self, api_client: TestClient):
        """Test updating non-existent product"""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "Updated Test"}
        response = api_client.put(f"/api/v1/products/{fake_id}", json=update_data)
        assert response.status_code == 404

    def test_delete_product(self, api_client: TestClient):
        """Test deleting product (soft delete)"""
        # Create product
        product_data = {"name": "Delete Test", "price": 100, "sku": "DELETE001"}
        create_response = api_client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Delete product
        response = api_client.delete(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        
        # Verify product is soft deleted
        get_response = api_client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] == False

    def test_bulk_create_products(self, api_client: TestClient):
        """Test bulk product creation"""
        bulk_data = {
            "products": [
                {"name": "Bulk 1", "price": 100, "sku": "BULK001"},
                {"name": "Bulk 2", "price": 200, "sku": "BULK002"},
                {"name": "Bulk 3", "price": 300, "sku": "BULK003"},
            ]
        }
        
        response = api_client.post("/api/v1/products/bulk", json=bulk_data)
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 3
        assert data["failed"] == 0

    def test_get_product_statistics(self, api_client: TestClient):
        """Test product statistics endpoint"""
        # Create diverse products
        products = [
            {"name": "Stats 1", "price": 100, "sku": "STATS001", "category": "Electronics"},
            {"name": "Stats 2", "price": 200, "sku": "STATS002", "category": "Electronics"},
            {"name": "Stats 3", "price": 300, "sku": "STATS003", "category": "Furniture"},
        ]
        
        for product in products:
            api_client.post("/api/v1/products", json=product)
        
        response = api_client.get("/api/v1/products/statistics")
        
        # Debug if not 200
        if response.status_code != 200:
            print(f"Statistics endpoint status: {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data
        assert "active_products" in data
        assert "categories" in data
        assert "average_price" in data

    def test_product_performance_metrics(self, api_client: TestClient):
        """Test API performance requirements (<50ms)"""
        import time
        
        # Create test product
        product_data = {"name": "Performance Test", "price": 100, "sku": "PERF001"}
        
        # Measure creation time
        start_time = time.time()
        response = api_client.post("/api/v1/products", json=product_data)
        end_time = time.time()
        
        creation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 201
        assert creation_time < 50, f"Product creation took {creation_time}ms, exceeds 50ms limit"
        
        product_id = response.json()["id"]
        
        # Measure retrieval time
        start_time = time.time()
        response = api_client.get(f"/api/v1/products/{product_id}")
        end_time = time.time()
        
        retrieval_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert retrieval_time < 50, f"Product retrieval took {retrieval_time}ms, exceeds 50ms limit"