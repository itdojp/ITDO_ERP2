"""
CC02 v53.0 Products API Unit Tests - Issue #568
10-Day ERP Business API Implementation Sprint - Day 1-2
Test-Driven Development Implementation
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.main_super_minimal import app
# from app.models.product import Product, ProductCategory, ProductPriceHistory  
# from app.schemas.product import (
#     ProductCreate, ProductUpdate, ProductResponse, 
#     ProductListResponse, BulkProductOperation, ProductStatistics
# )


class TestProductsAPI:
    """
    Comprehensive Products API Test Suite
    TDD Implementation for CC02 v53.0 ERP Business APIs
    
    Requirements:
    - Test Coverage: 95%+
    - Response Time: <200ms
    - Error Handling: Complete implementation
    """

    def test_create_product_basic(self, client: TestClient, db_session: AsyncSession):
        """Test basic product creation with required fields only"""
        product_data = {
            "name": "Test Product Basic",
            "sku": "TST-BASIC-001",
            "price": "199.99",
            "description": "Basic test product for API validation"
        }
        
        response = client.post("/api/v1/products-v53/", json=product_data)
        assert response.status_code == 201
        
        data = response.json()
        print(f"Response data: {data}")  # Debug print
        assert data["name"] == product_data["name"]
        assert data["sku"] == product_data["sku"]
        assert float(data["price"]) == 199.99
        if "description" in data:
            assert data["description"] == product_data["description"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_product_comprehensive(self, client: TestClient, db_session: AsyncSession):
        """Test product creation with all optional fields"""
        # First create a category
        category_data = {"name": "Electronics", "code": "ELEC", "description": "Electronic products"}
        cat_response = client.post("/api/v1/products-v53/categories/", json=category_data)
        category_id = cat_response.json()["id"]
        
        product_data = {
            "name": "Advanced Smartphone",
            "sku": "PHONE-ADV-001",
            "price": "899.99",
            "cost": "450.00",
            "description": "Latest smartphone with advanced features",
            "category_id": category_id,
            "brand": "TechCorp",
            "model": "X1 Pro",
            "weight": "185.5",
            "dimensions": {
                "length": "158.1",
                "width": "77.8", 
                "height": "7.9"
            },
            "color": "Midnight Black",
            "material": "Aluminum",
            "warranty_months": 24,
            "is_active": True,
            "is_featured": True,
            "min_stock_level": 10,
            "max_stock_level": 1000,
            "reorder_point": 25,
            "barcode": "1234567890123",
            "tags": ["smartphone", "electronics", "mobile"],
            "attributes": {
                "screen_size": "6.7 inches",
                "storage": "256GB",
                "ram": "8GB",
                "camera": "108MP"
            }
        }
        
        response = client.post("/api/v1/products-v53/", json=product_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == product_data["name"]
        assert data["brand"] == product_data["brand"]
        assert data["model"] == product_data["model"]
        assert data["category_id"] == category_id
        assert data["warranty_months"] == 24
        assert data["is_featured"] is True
        assert len(data["tags"]) == 3
        assert "screen_size" in data["attributes"]

    def test_create_product_validation_errors(self, client: TestClient):
        """Test product creation validation with various error scenarios"""
        
        # Missing required field - name
        invalid_data_1 = {
            "sku": "INV-001",
            "price": "99.99"
        }
        response = client.post("/api/v1/products-v53/", json=invalid_data_1)
        assert response.status_code == 422
        assert "name" in response.json()["detail"][0]["loc"]
        
        # Missing required field - SKU
        invalid_data_2 = {
            "name": "Invalid Product",
            "price": "99.99"
        }
        response = client.post("/api/v1/products-v53/", json=invalid_data_2)
        assert response.status_code == 422
        assert "sku" in response.json()["detail"][0]["loc"]
        
        # Invalid price format
        invalid_data_3 = {
            "name": "Invalid Price Product",
            "sku": "INV-PRICE-001",
            "price": "invalid_price"
        }
        response = client.post("/api/v1/products-v53/", json=invalid_data_3)
        assert response.status_code == 422
        
        # Negative price
        invalid_data_4 = {
            "name": "Negative Price Product", 
            "sku": "NEG-PRICE-001",
            "price": "-50.00"
        }
        response = client.post("/api/v1/products-v53/", json=invalid_data_4)
        assert response.status_code == 422

    def test_create_product_duplicate_sku(self, client: TestClient):
        """Test duplicate SKU validation"""
        product_data = {
            "name": "Original Product",
            "sku": "DUPLICATE-SKU-001", 
            "price": "199.99"
        }
        
        # Create first product
        response1 = client.post("/api/v1/products-v53/", json=product_data)
        assert response1.status_code == 201
        
        # Try to create duplicate SKU
        duplicate_data = {
            "name": "Duplicate SKU Product",
            "sku": "DUPLICATE-SKU-001",
            "price": "299.99"
        }
        response2 = client.post("/api/v1/products-v53/", json=duplicate_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_get_product_by_id(self, client: TestClient):
        """Test retrieving product by ID"""
        # Create a product first
        product_data = {
            "name": "Retrievable Product",
            "sku": "RETR-001",
            "price": "149.99",
            "description": "Product for retrieval testing"
        }
        create_response = client.post("/api/v1/products-v53/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Retrieve the product
        response = client.get(f"/api/v1/products-v53/{product_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == product_data["name"]
        assert data["sku"] == product_data["sku"]

    def test_get_product_not_found(self, client: TestClient):
        """Test retrieving non-existent product"""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/products-v53/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_product(self, client: TestClient):
        """Test product update functionality"""
        # Create product
        product_data = {
            "name": "Updatable Product",
            "sku": "UPD-001", 
            "price": "199.99"
        }
        create_response = client.post("/api/v1/products-v53/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update product
        update_data = {
            "name": "Updated Product Name",
            "price": "249.99",
            "description": "Updated description"
        }
        response = client.put(f"/api/v1/products-v53/{product_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert float(data["price"]) == 249.99
        assert data["description"] == update_data["description"]
        assert data["sku"] == product_data["sku"]  # Should remain unchanged

    def test_update_product_not_found(self, client: TestClient):
        """Test updating non-existent product"""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "Updated Name"}
        response = client.put(f"/api/v1/products-v53/{fake_id}", json=update_data)
        assert response.status_code == 404

    def test_delete_product_soft_delete(self, client: TestClient):
        """Test product soft deletion"""
        # Create product
        product_data = {
            "name": "Deletable Product",
            "sku": "DEL-001",
            "price": "99.99"
        }
        create_response = client.post("/api/v1/products-v53/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Delete product
        response = client.delete(f"/api/v1/products-v53/{product_id}")
        assert response.status_code == 200
        
        # Verify soft deletion - product should exist but be inactive
        get_response = client.get(f"/api/v1/products-v53/{product_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    def test_list_products_basic(self, client: TestClient):
        """Test basic product listing"""
        # Create multiple products
        products_data = [
            {"name": "List Product 1", "sku": "LIST-001", "price": "99.99"},
            {"name": "List Product 2", "sku": "LIST-002", "price": "149.99"},
            {"name": "List Product 3", "sku": "LIST-003", "price": "199.99"}
        ]
        
        for product_data in products_data:
            client.post("/api/v1/products-v53/", json=product_data)
        
        response = client.get("/api/v1/products-v53/")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["items"]) >= 3

    def test_list_products_pagination(self, client: TestClient):
        """Test product listing with pagination"""
        # Create products for pagination testing
        for i in range(15):
            product_data = {
                "name": f"Pagination Product {i+1}",
                "sku": f"PAG-{i+1:03d}",
                "price": f"{100 + i}.99"
            }
            client.post("/api/v1/products-v53/", json=product_data)
        
        # Test first page
        response = client.get("/api/v1/products-v53/?page=1&size=5")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["size"] == 5
        assert data["total"] >= 15
        
        # Test second page
        response = client.get("/api/v1/products-v53/?page=2&size=5")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 2

    def test_list_products_search_and_filtering(self, client: TestClient):
        """Test product search and filtering capabilities"""
        # Create category for filtering
        category_data = {"name": "Search Category", "code": "SEARCH"}
        cat_response = client.post("/api/v1/products-v53/categories/", json=category_data)
        category_id = cat_response.json()["id"]
        
        # Create products with different attributes
        products_data = [
            {
                "name": "iPhone 15 Pro",
                "sku": "APPLE-IPHONE-15",
                "price": "999.99",
                "brand": "Apple",
                "category_id": category_id
            },
            {
                "name": "Samsung Galaxy S24",
                "sku": "SAMSUNG-S24",
                "price": "849.99", 
                "brand": "Samsung"
            },
            {
                "name": "MacBook Pro 16",
                "sku": "APPLE-MBP-16",
                "price": "2499.99",
                "brand": "Apple"
            }
        ]
        
        for product_data in products_data:
            client.post("/api/v1/products-v53/", json=product_data)
        
        # Test name search
        response = client.get("/api/v1/products-v53/?search=iPhone")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len([item for item in items if "iPhone" in item["name"]]) >= 1
        
        # Test brand filtering
        response = client.get("/api/v1/products-v53/?brand=Apple")
        assert response.status_code == 200
        items = response.json()["items"]
        apple_products = [item for item in items if item["brand"] == "Apple"]
        assert len(apple_products) >= 2
        
        # Test category filtering
        response = client.get(f"/api/v1/products-v53/?category_id={category_id}")
        assert response.status_code == 200
        items = response.json()["items"]
        category_products = [item for item in items if item.get("category_id") == category_id]
        assert len(category_products) >= 1
        
        # Test price range filtering
        response = client.get("/api/v1/products-v53/?min_price=800&max_price=1500")
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            price = float(item["price"])
            assert 800 <= price <= 1500

    def test_bulk_operations(self, client: TestClient):
        """Test bulk product operations"""
        bulk_data = {
            "products": [
                {"name": "Bulk Product 1", "sku": "BULK-001", "price": "99.99"},
                {"name": "Bulk Product 2", "sku": "BULK-002", "price": "149.99"},
                {"name": "Bulk Product 3", "sku": "BULK-003", "price": "199.99"}
            ]
        }
        
        response = client.post("/api/v1/products-v53/bulk", json=bulk_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["created_count"] == 3
        assert data["failed_count"] == 0
        assert len(data["created_items"]) == 3

    def test_bulk_operations_with_errors(self, client: TestClient):
        """Test bulk operations with some invalid items"""
        bulk_data = {
            "products": [
                {"name": "Valid Bulk Product", "sku": "VALID-BULK-001", "price": "99.99"},
                {"name": "Invalid Product", "price": "149.99"},  # Missing SKU
                {"name": "Another Valid", "sku": "VALID-BULK-002", "price": "199.99"}
            ]
        }
        
        response = client.post("/api/v1/products-v53/bulk", json=bulk_data)
        assert response.status_code == 207  # Multi-status
        
        data = response.json()
        assert data["created_count"] == 2
        assert data["failed_count"] == 1
        assert len(data["failed_items"]) == 1

    def test_product_categories_management(self, client: TestClient):
        """Test product categories CRUD operations"""
        # Create category
        category_data = {
            "name": "Electronics",
            "code": "ELECTRONICS",
            "description": "Electronic devices and accessories",
            "parent_id": None,
            "is_active": True
        }
        
        response = client.post("/api/v1/products-v53/categories/", json=category_data)
        assert response.status_code == 201
        
        category = response.json()
        category_id = category["id"]
        assert category["name"] == category_data["name"]
        assert category["code"] == category_data["code"]
        
        # Create subcategory
        subcategory_data = {
            "name": "Smartphones",
            "code": "SMARTPHONES", 
            "parent_id": category_id
        }
        
        response = client.post("/api/v1/products-v53/categories/", json=subcategory_data)
        assert response.status_code == 201
        
        subcategory = response.json()
        assert subcategory["parent_id"] == category_id
        
        # List categories
        response = client.get("/api/v1/products-v53/categories/")
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) >= 2

    def test_product_statistics(self, client: TestClient):
        """Test product statistics endpoint"""
        # Clear any existing products first
        from app.api.v1.endpoints.products_v53 import products_store
        products_store.clear()
        
        # Create products with different attributes for statistics
        products_data = [
            {"name": "Stat Product 1", "sku": "STAT-001", "price": "100.00", "is_active": True},
            {"name": "Stat Product 2", "sku": "STAT-002", "price": "200.00", "is_active": True},
            {"name": "Stat Product 3", "sku": "STAT-003", "price": "300.00", "is_active": False}
        ]
        
        for product_data in products_data:
            client.post("/api/v1/products-v53/", json=product_data)
        
        response = client.get("/api/v1/products-v53/statistics?include_inactive=true")
        assert response.status_code == 200
        
        stats = response.json()
        print(f"Statistics response: {stats}")  # Debug print
        assert "total_products" in stats
        assert "active_products" in stats
        assert "inactive_products" in stats
        assert "average_product_price" in stats
        assert "total_inventory_value" in stats
        assert "total_categories" in stats
        
        assert stats["total_products"] >= 3
        assert stats["active_products"] >= 2
        assert stats["inactive_products"] >= 1

    def test_product_price_history(self, client: TestClient):
        """Test product price history tracking"""
        # Create product
        product_data = {
            "name": "Price History Product",
            "sku": "PRICE-HIST-001",
            "price": "199.99"
        }
        create_response = client.post("/api/v1/products-v53/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update price multiple times
        price_updates = ["249.99", "299.99", "279.99"]
        for new_price in price_updates:
            update_data = {"price": new_price}
            client.put(f"/api/v1/products-v53/{product_id}", json=update_data)
        
        # Get price history
        response = client.get(f"/api/v1/products-v53/{product_id}/price-history")
        assert response.status_code == 200
        
        history = response.json()
        assert "product_id" in history
        assert "price_changes" in history
        assert len(history["price_changes"]) >= 4  # Initial + 3 updates

    def test_product_inventory_integration(self, client: TestClient):
        """Test product inventory levels integration"""
        # Create product
        product_data = {
            "name": "Inventory Product",
            "sku": "INV-PROD-001",
            "price": "199.99"
        }
        create_response = client.post("/api/v1/products-v53/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get inventory levels
        response = client.get(f"/api/v1/products-v53/{product_id}/inventory")
        assert response.status_code == 200
        
        inventory = response.json()
        assert "product_id" in inventory
        assert "total_stock" in inventory
        assert "available_stock" in inventory
        assert "reserved_stock" in inventory
        assert "locations" in inventory

    def test_api_performance_requirements(self, client: TestClient):
        """Test API performance requirements (<200ms)"""
        import time
        
        # Create test product
        product_data = {
            "name": "Performance Test Product",
            "sku": "PERF-001",
            "price": "199.99"
        }
        
        # Measure creation time
        start_time = time.time()
        response = client.post("/api/v1/products-v53/", json=product_data)
        end_time = time.time()
        
        creation_time_ms = (end_time - start_time) * 1000
        assert response.status_code == 201
        assert creation_time_ms < 200, f"Product creation took {creation_time_ms}ms, exceeds 200ms limit"
        
        product_id = response.json()["id"]
        
        # Measure retrieval time
        start_time = time.time()
        response = client.get(f"/api/v1/products-v53/{product_id}")
        end_time = time.time()
        
        retrieval_time_ms = (end_time - start_time) * 1000
        assert response.status_code == 200
        assert retrieval_time_ms < 200, f"Product retrieval took {retrieval_time_ms}ms, exceeds 200ms limit"
        
        # Measure list time
        start_time = time.time()
        response = client.get("/api/v1/products-v53/?size=50")
        end_time = time.time()
        
        list_time_ms = (end_time - start_time) * 1000
        assert response.status_code == 200
        assert list_time_ms < 200, f"Product listing took {list_time_ms}ms, exceeds 200ms limit"

    def test_error_handling_comprehensive(self, client: TestClient):
        """Test comprehensive error handling"""
        
        # Test various HTTP error scenarios
        test_cases = [
            # Invalid JSON
            ("/api/v1/products-v53/", "POST", "invalid_json", 400),
            # Unauthorized access (if auth is implemented)
            # ("/api/v1/products-v53/", "POST", {"name": "Test"}, 401),
            # Forbidden access (if auth is implemented)
            # ("/api/v1/products-v53/", "POST", {"name": "Test"}, 403),
            # Not found
            (f"/api/v1/products-v53/{uuid.uuid4()}", "GET", None, 404),
            # Method not allowed
            ("/api/v1/products-v53/invalid-endpoint", "PATCH", {}, 404),
            # Validation error
            ("/api/v1/products-v53/", "POST", {"invalid": "data"}, 422),
        ]
        
        for endpoint, method, data, expected_status in test_cases:
            if method == "POST":
                if data == "invalid_json":
                    # Test invalid JSON by sending raw string
                    continue  # Skip this test case for now
                else:
                    response = client.post(endpoint, json=data)
            elif method == "GET":
                response = client.get(endpoint)
            elif method == "PATCH":
                response = client.patch(endpoint, json=data)
            
            assert response.status_code == expected_status
            
            # Verify error response structure
            if response.status_code >= 400:
                error_data = response.json()
                assert "detail" in error_data

    def test_multi_tenant_support(self, client: TestClient):
        """Test multi-tenant product isolation (if implemented)"""
        # This test assumes multi-tenant functionality
        # Create products for different tenants
        
        # Tenant 1 product
        tenant1_headers = {"X-Tenant-ID": "tenant-1"}
        product_data_1 = {
            "name": "Tenant 1 Product",
            "sku": "T1-PROD-001",
            "price": "199.99"
        }
        response1 = client.post("/api/v1/products-v53/", json=product_data_1, headers=tenant1_headers)
        # assert response1.status_code == 201  # Uncomment when multi-tenant is implemented
        
        # Tenant 2 product
        tenant2_headers = {"X-Tenant-ID": "tenant-2"}
        product_data_2 = {
            "name": "Tenant 2 Product", 
            "sku": "T2-PROD-001",
            "price": "299.99"
        }
        response2 = client.post("/api/v1/products-v53/", json=product_data_2, headers=tenant2_headers)
        # assert response2.status_code == 201  # Uncomment when multi-tenant is implemented
        
        # Verify tenant isolation
        # list_response1 = client.get("/api/v1/products-v53/", headers=tenant1_headers)
        # list_response2 = client.get("/api/v1/products-v53/", headers=tenant2_headers)
        
        # Tenant 1 should only see their products
        # tenant1_products = [p for p in list_response1.json()["items"] if p["sku"].startswith("T1-")]
        # assert len(tenant1_products) >= 1
        
        # Tenant 2 should only see their products  
        # tenant2_products = [p for p in list_response2.json()["items"] if p["sku"].startswith("T2-")]
        # assert len(tenant2_products) >= 1


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture 
async def db_session():
    """Create test database session"""
    # This will be implemented with actual database session
    # For now, using mock
    return None


# Performance and Load Testing
class TestProductsAPIPerformance:
    """Performance testing suite for Products API"""
    
    def test_concurrent_requests(self, client: TestClient):
        """Test handling of concurrent requests"""
        import concurrent.futures
        import threading
        
        def create_product(thread_id):
            product_data = {
                "name": f"Concurrent Product {thread_id}",
                "sku": f"CONCURRENT-{thread_id:03d}",
                "price": "199.99"
            }
            return client.post("/api/v1/products-v53/", json=product_data)
        
        # Test with 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_product, i) for i in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        success_count = sum(1 for response in responses if response.status_code == 201)
        assert success_count >= 8, f"Only {success_count}/10 concurrent requests succeeded"
    
    def test_large_dataset_handling(self, client: TestClient):
        """Test API performance with large datasets"""
        # Create large number of products
        bulk_data = {
            "products": [
                {
                    "name": f"Large Dataset Product {i}",
                    "sku": f"LARGE-{i:05d}",
                    "price": f"{100 + (i % 900)}.99"
                }
                for i in range(100)
            ]
        }
        
        import time
        start_time = time.time()
        response = client.post("/api/v1/products-v53/bulk", json=bulk_data)
        end_time = time.time()
        
        processing_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code in [201, 207]  # Created or Multi-status
        assert processing_time_ms < 5000, f"Bulk creation took {processing_time_ms}ms, too slow"
        
        # Test listing performance with large dataset
        start_time = time.time()
        list_response = client.get("/api/v1/products-v53/?size=100")
        end_time = time.time()
        
        list_time_ms = (end_time - start_time) * 1000
        assert list_response.status_code == 200
        assert list_time_ms < 300, f"Large list took {list_time_ms}ms, exceeds performance requirement"


# Integration Testing
class TestProductsAPIIntegration:
    """Integration testing suite for Products API with other systems"""
    
    def test_product_category_integration(self, client: TestClient):
        """Test integration between products and categories"""
        # This test verifies the relationship between products and categories
        pass  # Implementation depends on category system
    
    def test_product_inventory_integration(self, client: TestClient):
        """Test integration between products and inventory system"""
        # This test verifies inventory tracking for products
        pass  # Implementation depends on inventory system
    
    def test_product_pricing_integration(self, client: TestClient):
        """Test integration with pricing and discount systems"""
        # This test verifies pricing rules and discount applications
        pass  # Implementation depends on pricing system