"""
TDD Tests for Core Products API - CC02 v50.0
12-Hour Core Business API Sprint - Products Management
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import uuid
import json


class TestCoreProductsAPI:
    """Test suite for Core Products API - TDD Implementation"""

    def test_create_product_basic(self, api_client: TestClient):
        """Test basic product creation endpoint"""
        product_data = {
            "name": "Core Test Product",
            "sku": "CORE-TEST-001",
            "price": 99.99,
            "description": "Test product for core business API",
            "category": "Electronics"
        }
        response = api_client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Core Test Product"
        assert data["sku"] == "CORE-TEST-001"
        assert data["price"] == 99.99
        assert "id" in data
        assert "created_at" in data

    def test_create_product_with_advanced_attributes(self, api_client: TestClient):
        """Test product creation with advanced business attributes"""
        product_data = {
            "name": "Advanced Business Product",
            "sku": "ADV-BIZ-001",
            "price": 299.99,
            "cost": 150.00,
            "description": "Advanced product with business attributes",
            "category": "Business Software",
            "brand": "ITDO Corp",
            "weight": 1.5,
            "dimensions": {"length": 10, "width": 5, "height": 2},
            "is_active": True,
            "track_inventory": True,
            "tax_exempt": False,
            "min_order_quantity": 1,
            "max_order_quantity": 100
        }
        response = api_client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        data = response.json()
        assert data["cost"] == 150.00
        assert data["brand"] == "ITDO Corp"
        assert data["weight"] == 1.5
        assert data["track_inventory"] is True

    def test_create_product_validation_errors(self, api_client: TestClient):
        """Test product creation validation"""
        # Missing required fields
        invalid_data = {"name": "Incomplete Product"}
        response = api_client.post("/api/v1/products", json=invalid_data)
        assert response.status_code == 422

        # Invalid price
        invalid_price_data = {
            "name": "Invalid Price Product",
            "sku": "INVALID-001",
            "price": -10.00
        }
        response = api_client.post("/api/v1/products", json=invalid_price_data)
        assert response.status_code == 422

    def test_create_product_duplicate_sku(self, api_client: TestClient):
        """Test duplicate SKU handling"""
        product_data = {
            "name": "Original Product",
            "sku": "DUPLICATE-SKU-001",
            "price": 99.99
        }
        
        # First creation should succeed
        response1 = api_client.post("/api/v1/products", json=product_data)
        assert response1.status_code == 201
        
        # Second creation with same SKU should fail
        duplicate_data = {
            "name": "Duplicate Product",
            "sku": "DUPLICATE-SKU-001",
            "price": 149.99
        }
        response2 = api_client.post("/api/v1/products", json=duplicate_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    def test_get_product_by_id(self, api_client: TestClient):
        """Test retrieving product by ID"""
        # Create product first
        product_data = {
            "name": "Get Test Product",
            "sku": "GET-TEST-001",
            "price": 199.99
        }
        create_response = api_client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get product
        response = api_client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        assert response.json()["id"] == product_id
        assert response.json()["name"] == "Get Test Product"

    def test_get_product_not_found(self, api_client: TestClient):
        """Test retrieving non-existent product"""
        fake_id = str(uuid.uuid4())
        response = api_client.get(f"/api/v1/products/{fake_id}")
        assert response.status_code == 404

    def test_list_products_basic(self, api_client: TestClient):
        """Test basic product listing"""
        # Create test products
        for i in range(3):
            product_data = {
                "name": f"List Test Product {i+1}",
                "sku": f"LIST-TEST-{i+1:03d}",
                "price": (i+1) * 50.0
            }
            api_client.post("/api/v1/products", json=product_data)
        
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
        # Create multiple products
        for i in range(10):
            product_data = {
                "name": f"Pagination Product {i+1}",
                "sku": f"PAGE-{i+1:03d}",
                "price": 100.0
            }
            api_client.post("/api/v1/products", json=product_data)
        
        # Test pagination
        response = api_client.get("/api/v1/products?page=1&size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        assert data["page"] == 1
        assert data["size"] == 5

    def test_list_products_with_search(self, api_client: TestClient):
        """Test product search functionality"""
        # Create searchable products
        search_products = [
            {"name": "Search Electronics Laptop", "sku": "SEARCH-ELEC-001", "price": 999.99},
            {"name": "Search Electronics Phone", "sku": "SEARCH-ELEC-002", "price": 599.99},
            {"name": "Search Furniture Chair", "sku": "SEARCH-FURN-001", "price": 199.99}
        ]
        
        for product in search_products:
            api_client.post("/api/v1/products", json=product)
        
        # Search by name
        response = api_client.get("/api/v1/products?search=Electronics")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 2
        
        # Search by SKU
        response = api_client.get("/api/v1/products?search=FURN")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

    def test_list_products_with_filters(self, api_client: TestClient):
        """Test product filtering"""
        # Create products with different categories
        filter_products = [
            {"name": "Filter Electronics 1", "sku": "FILT-ELEC-001", "price": 299.99, "category": "Electronics"},
            {"name": "Filter Electronics 2", "sku": "FILT-ELEC-002", "price": 399.99, "category": "Electronics"},
            {"name": "Filter Books 1", "sku": "FILT-BOOK-001", "price": 29.99, "category": "Books"}
        ]
        
        for product in filter_products:
            api_client.post("/api/v1/products", json=product)
        
        # Filter by category
        response = api_client.get("/api/v1/products?category=Electronics")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 2
        
        # Filter by price range
        response = api_client.get("/api/v1/products?min_price=100&max_price=500")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 2

    def test_update_product_basic(self, api_client: TestClient):
        """Test basic product update"""
        # Create product
        product_data = {
            "name": "Update Test Product",
            "sku": "UPDATE-TEST-001",
            "price": 199.99
        }
        create_response = api_client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update product
        update_data = {
            "name": "Updated Product Name",
            "price": 249.99,
            "description": "Updated description"
        }
        response = api_client.put(f"/api/v1/products/{product_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product Name"
        assert data["price"] == 249.99
        assert data["description"] == "Updated description"

    def test_update_product_not_found(self, api_client: TestClient):
        """Test updating non-existent product"""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "Non-existent Product"}
        response = api_client.put(f"/api/v1/products/{fake_id}", json=update_data)
        assert response.status_code == 404

    def test_delete_product_soft_delete(self, api_client: TestClient):
        """Test soft delete of product"""
        # Create product
        product_data = {
            "name": "Delete Test Product",
            "sku": "DELETE-TEST-001",
            "price": 99.99
        }
        create_response = api_client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Delete product (soft delete)
        response = api_client.delete(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        
        # Verify product is soft deleted (should return but marked as inactive)
        get_response = api_client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    def test_bulk_create_products(self, api_client: TestClient):
        """Test bulk product creation"""
        bulk_products = [
            {"name": "Bulk Product 1", "sku": "BULK-001", "price": 99.99},
            {"name": "Bulk Product 2", "sku": "BULK-002", "price": 149.99},
            {"name": "Bulk Product 3", "sku": "BULK-003", "price": 199.99}
        ]
        
        response = api_client.post("/api/v1/products/bulk", json={"products": bulk_products})
        assert response.status_code == 201
        data = response.json()
        assert len(data["created"]) == 3
        assert data["success_count"] == 3
        assert data["error_count"] == 0

    def test_bulk_create_products_with_errors(self, api_client: TestClient):
        """Test bulk product creation with validation errors"""
        bulk_products = [
            {"name": "Valid Bulk Product", "sku": "BULK-VALID-001", "price": 99.99},
            {"name": "Invalid Product"},  # Missing SKU and price
            {"name": "Another Valid Product", "sku": "BULK-VALID-002", "price": 149.99}
        ]
        
        response = api_client.post("/api/v1/products/bulk", json={"products": bulk_products})
        assert response.status_code == 207  # Multi-status
        data = response.json()
        assert data["success_count"] == 2
        assert data["error_count"] == 1
        assert len(data["errors"]) == 1

    def test_product_categories_management(self, api_client: TestClient):
        """Test product categories endpoint"""
        # Create products with different categories
        categories_data = [
            {"name": "Cat Product 1", "sku": "CAT-001", "price": 99.99, "category": "Electronics"},
            {"name": "Cat Product 2", "sku": "CAT-002", "price": 149.99, "category": "Books"},
            {"name": "Cat Product 3", "sku": "CAT-003", "price": 199.99, "category": "Electronics"}
        ]
        
        for product in categories_data:
            api_client.post("/api/v1/products", json=product)
        
        # Get categories
        response = api_client.get("/api/v1/products/categories")
        assert response.status_code == 200
        data = response.json()
        assert "Electronics" in data["categories"]
        assert "Books" in data["categories"]

    def test_product_statistics(self, api_client: TestClient):
        """Test product statistics endpoint"""
        # Create diverse products for statistics
        stats_products = [
            {"name": "Stats Product 1", "sku": "STATS-001", "price": 99.99, "category": "Electronics", "is_active": True},
            {"name": "Stats Product 2", "sku": "STATS-002", "price": 149.99, "category": "Books", "is_active": True},
            {"name": "Stats Product 3", "sku": "STATS-003", "price": 199.99, "category": "Electronics", "is_active": False}
        ]
        
        for product in stats_products:
            api_client.post("/api/v1/products", json=product)
        
        response = api_client.get("/api/v1/products/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data
        assert "active_products" in data
        assert "categories" in data
        assert "average_price" in data

    def test_product_api_performance(self, api_client: TestClient):
        """Test Core Products API performance requirements"""
        import time
        
        product_data = {
            "name": "Performance Test Product",
            "sku": "PERF-TEST-001",
            "price": 99.99
        }
        
        # Measure creation time
        start_time = time.time()
        response = api_client.post("/api/v1/products", json=product_data)
        end_time = time.time()
        
        creation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 201
        assert creation_time < 100, f"Product creation took {creation_time}ms, exceeds 100ms limit"
        
        product_id = response.json()["id"]
        
        # Measure retrieval time
        start_time = time.time()
        response = api_client.get(f"/api/v1/products/{product_id}")
        end_time = time.time()
        
        retrieval_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert retrieval_time < 50, f"Product retrieval took {retrieval_time}ms, exceeds 50ms limit"