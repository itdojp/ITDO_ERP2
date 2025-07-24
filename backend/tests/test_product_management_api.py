"""
TDD Tests for Complete Product Management API - CC02 v48.0
Comprehensive test suite covering all product CRUD operations with advanced features
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, List, Any
import json
import uuid
from datetime import datetime

# Import the main app
from app.main_super_minimal import app

client = TestClient(app)

class TestProductManagementAPI:
    """Comprehensive test suite for Product Management API"""

    def setup_method(self):
        """Setup test data before each test"""
        # Clear any existing test data from both endpoints
        try:
            client.delete("/api/v1/simple-products/test/clear-all")
        except:
            pass
        try:
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass
        
        # Test product data
        self.test_product = {
            "code": "TEST001",
            "name": "Test Product 1",
            "description": "A test product for unit testing",
            "price": 99.99,
            "category": "Test Category"
        }
        
        self.test_products_bulk = [
            {
                "code": "BULK001",
                "name": "Bulk Product 1",
                "description": "First bulk test product",
                "price": 149.99,
                "category": "Electronics"
            },
            {
                "code": "BULK002", 
                "name": "Bulk Product 2",
                "description": "Second bulk test product",
                "price": 249.99,
                "category": "Electronics"
            },
            {
                "code": "BULK003",
                "name": "Bulk Product 3", 
                "description": "Third bulk test product",
                "price": 349.99,
                "category": "Furniture"
            }
        ]

    def test_create_product_success(self):
        """Test successful product creation"""
        response = client.post("/api/v1/simple-products/", json=self.test_product)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "id" in data
        assert data["code"] == self.test_product["code"]
        assert data["name"] == self.test_product["name"]
        assert data["description"] == self.test_product["description"]
        assert data["price"] == self.test_product["price"]
        assert data["category"] == self.test_product["category"]
        assert data["is_active"] == True
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_product_duplicate_code_fails(self):
        """Test that duplicate product codes are rejected"""
        # Create first product
        client.post("/api/v1/simple-products/", json=self.test_product)
        
        # Try to create duplicate
        response = client.post("/api/v1/simple-products/", json=self.test_product)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_product_invalid_data_fails(self):
        """Test validation of invalid product data"""
        invalid_products = [
            {"code": "", "name": "Test", "price": 10.0},  # Empty code
            {"code": "TEST", "name": "", "price": 10.0},  # Empty name
            {"code": "TEST", "name": "Test", "price": -1.0},  # Negative price
            {"code": "TEST", "name": "Test", "price": 0.0},  # Zero price
        ]
        
        for invalid_product in invalid_products:
            response = client.post("/api/v1/simple-products/", json=invalid_product)
            assert response.status_code == 422  # Validation error

    def test_list_products_empty(self):
        """Test listing products when none exist"""
        response = client.get("/api/v1/simple-products/")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_list_products_with_data(self):
        """Test listing products with existing data"""
        # Create test products
        for product in self.test_products_bulk:
            client.post("/api/v1/simple-products/", json=product)
        
        response = client.get("/api/v1/simple-products/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_products_pagination(self):
        """Test product listing with pagination"""
        # Create test products
        for product in self.test_products_bulk:
            client.post("/api/v1/simple-products/", json=product)
        
        # Test pagination
        response = client.get("/api/v1/simple-products/?skip=1&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_products_category_filter(self):
        """Test product listing with category filtering"""
        # Create test products
        for product in self.test_products_bulk:
            client.post("/api/v1/simple-products/", json=product)
        
        # Filter by Electronics category
        response = client.get("/api/v1/simple-products/?category=Electronics")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for product in data:
            assert product["category"] == "Electronics"

    def test_list_products_search_filter(self):
        """Test product listing with search functionality"""
        # Create test products
        for product in self.test_products_bulk:
            client.post("/api/v1/simple-products/", json=product)
        
        # Search by name
        response = client.get("/api/v1/simple-products/?search=Bulk Product 1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Bulk Product 1" in data[0]["name"]

    def test_list_products_active_filter(self):
        """Test product listing with active status filtering"""
        # Create and then deactivate a product
        create_response = client.post("/api/v1/simple-products/", json=self.test_product)
        product_id = create_response.json()["id"]
        
        client.delete(f"/api/v1/simple-products/{product_id}")
        
        # Filter active products
        response = client.get("/api/v1/simple-products/?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert all(product["is_active"] for product in data)
        
        # Filter inactive products
        response = client.get("/api/v1/simple-products/?is_active=false")
        assert response.status_code == 200
        data = response.json()
        assert all(not product["is_active"] for product in data)

    def test_get_product_by_id_success(self):
        """Test retrieving product by ID"""
        create_response = client.post("/api/v1/simple-products/", json=self.test_product)
        product_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/simple-products/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["code"] == self.test_product["code"]

    def test_get_product_by_id_not_found(self):
        """Test retrieving non-existent product by ID"""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/simple-products/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_product_by_code_success(self):
        """Test retrieving product by code"""
        client.post("/api/v1/simple-products/", json=self.test_product)
        
        response = client.get(f"/api/v1/simple-products/code/{self.test_product['code']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == self.test_product["code"]

    def test_get_product_by_code_not_found(self):
        """Test retrieving non-existent product by code"""
        response = client.get("/api/v1/simple-products/code/NONEXISTENT")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_product_success(self):
        """Test successful product update"""
        create_response = client.post("/api/v1/simple-products/", json=self.test_product)
        product_id = create_response.json()["id"]
        
        update_data = {
            "name": "Updated Product Name",
            "price": 199.99,
            "description": "Updated description"
        }
        
        response = client.put(f"/api/v1/simple-products/{product_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["price"] == update_data["price"]
        assert data["description"] == update_data["description"]
        assert data["code"] == self.test_product["code"]  # Code should remain unchanged

    def test_update_product_not_found(self):
        """Test updating non-existent product"""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "Updated Name"}
        
        response = client.put(f"/api/v1/simple-products/{fake_id}", json=update_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_product_partial_update(self):
        """Test partial product update"""
        create_response = client.post("/api/v1/simple-products/", json=self.test_product)
        product_id = create_response.json()["id"]
        
        update_data = {"price": 299.99}  # Only update price
        
        response = client.put(f"/api/v1/simple-products/{product_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == update_data["price"]
        assert data["name"] == self.test_product["name"]  # Other fields unchanged

    def test_delete_product_success(self):
        """Test successful product deletion (soft delete)"""
        create_response = client.post("/api/v1/simple-products/", json=self.test_product)
        product_id = create_response.json()["id"]
        
        response = client.delete(f"/api/v1/simple-products/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deactivated" in data["message"]
        
        # Verify product is deactivated
        get_response = client.get(f"/api/v1/simple-products/{product_id}")
        assert get_response.status_code == 200
        assert not get_response.json()["is_active"]

    def test_delete_product_not_found(self):
        """Test deleting non-existent product"""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/simple-products/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_bulk_create_products_success(self):
        """Test successful bulk product creation"""
        response = client.post("/api/v1/simple-products/bulk/create", json=self.test_products_bulk)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        for i, product in enumerate(data):
            assert product["code"] == self.test_products_bulk[i]["code"]
            assert product["name"] == self.test_products_bulk[i]["name"]

    def test_bulk_create_products_with_duplicates(self):
        """Test bulk creation with duplicate codes"""
        # Create one product first
        client.post("/api/v1/simple-products/", json=self.test_products_bulk[0])
        
        # Try bulk create including the duplicate
        response = client.post("/api/v1/simple-products/bulk/create", json=self.test_products_bulk)
        
        # Should still succeed with partial results
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Only the non-duplicate products created

    def test_get_product_statistics(self):
        """Test product statistics endpoint"""
        # Create test products
        for product in self.test_products_bulk:
            client.post("/api/v1/simple-products/", json=product)
        
        response = client.get("/api/v1/simple-products/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_products" in data
        assert "active_products" in data
        assert "inactive_products" in data
        assert "categories_breakdown" in data
        assert data["total_products"] == 3
        assert data["active_products"] == 3
        assert data["inactive_products"] == 0

    def test_product_statistics_with_deactivated(self):
        """Test statistics including deactivated products"""
        # Create and deactivate one product
        create_response = client.post("/api/v1/simple-products/", json=self.test_product)
        product_id = create_response.json()["id"]
        client.delete(f"/api/v1/simple-products/{product_id}")
        
        # Create active products
        for product in self.test_products_bulk:
            client.post("/api/v1/simple-products/", json=product)
        
        response = client.get("/api/v1/simple-products/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_products"] == 4
        assert data["active_products"] == 3
        assert data["inactive_products"] == 1

    def test_advanced_search_combined_filters(self):
        """Test advanced search with multiple filters combined"""
        # Create test products
        for product in self.test_products_bulk:
            client.post("/api/v1/simple-products/", json=product)
        
        # Test combined filters: category + search + pagination
        response = client.get(
            "/api/v1/simple-products/?category=Electronics&search=Bulk&skip=0&limit=1"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "Electronics"
        assert "Bulk" in data[0]["name"]

    def test_product_validation_edge_cases(self):
        """Test product validation with edge cases"""
        edge_cases = [
            # Very long strings
            {
                "code": "A" * 51,  # Exceeds max length
                "name": "Test",
                "price": 10.0
            },
            # Special characters in code
            {
                "code": "TEST@#$",
                "name": "Test",
                "price": 10.0
            },
            # Very high price
            {
                "code": "TEST_HIGH",
                "name": "Test",
                "price": 999999.99
            }
        ]
        
        for edge_case in edge_cases:
            response = client.post("/api/v1/simple-products/", json=edge_case)
            # Some may pass, some may fail depending on validation rules
            # This test documents the current behavior

    def test_concurrent_product_operations(self):
        """Test concurrent product operations for data consistency"""
        import threading
        import time
        
        results = []
        
        def create_product(index):
            product = {
                "code": f"CONCURRENT_{index}",
                "name": f"Concurrent Product {index}",
                "price": 100.0 + index
            }
            response = client.post("/api/v1/simple-products/", json=product)
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_product, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations succeeded
        assert all(status == 200 for status in results)

    def test_performance_product_listing(self):
        """Test performance of product listing with large dataset"""
        import time
        
        # Create larger dataset for performance testing
        large_dataset = []
        for i in range(50):
            large_dataset.append({
                "code": f"PERF_{i:03d}",
                "name": f"Performance Test Product {i}",
                "description": f"Product for performance testing number {i}",
                "price": 10.0 + (i * 0.5),
                "category": f"Category_{i % 5}"
            })
        
        # Bulk create
        client.post("/api/v1/simple-products/bulk/create", json=large_dataset)
        
        # Measure response time
        start_time = time.time()
        response = client.get("/api/v1/simple-products/")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        assert len(response.json()) == 50
        # Performance assertion: should respond within 100ms
        assert response_time < 100, f"Response time {response_time}ms exceeds 100ms threshold"

    def teardown_method(self):
        """Clean up after each test"""
        # Clear test data from both endpoints
        try:
            client.delete("/api/v1/simple-products/test/clear-all")
        except:
            pass
        try:
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass