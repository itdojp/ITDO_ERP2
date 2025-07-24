"""
Comprehensive TDD Tests for Advanced Product Management API - CC02 v48.0
Testing all advanced features including search, filtering, bulk operations
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, List, Any
import json
import uuid
from datetime import datetime
from decimal import Decimal

# Import the main app
from app.main_super_minimal import app

client = TestClient(app)

class TestAdvancedProductManagementAPI:
    """Comprehensive test suite for Advanced Product Management API"""

    def setup_method(self):
        """Setup test data before each test"""
        # Clear any existing test data
        try:
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass
        
        # Advanced test product data
        self.advanced_product = {
            "code": "ADV001",
            "name": "Advanced Product 1",
            "description": "Advanced product with full features",
            "short_description": "Short description",
            "price": 299.99,
            "cost_price": 150.00,
            "sku": "SKU-ADV001",
            "barcode": "1234567890123",
            "category": "Electronics",
            "subcategory": "Smartphones",
            "brand": "TechBrand",
            "manufacturer": "TechCorp",
            "product_type": "physical",
            "status": "active",
            "weight": 0.5,
            "dimensions": {"length": 15.0, "width": 7.0, "height": 0.8},
            "color": "Black",
            "size": "Medium",
            "material": "Aluminum",
            "tags": ["electronics", "smartphone", "premium"],
            "warranty_period": 24,
            "min_order_quantity": 1,
            "max_order_quantity": 100,
            "reorder_point": 10,
            "is_featured": True,
            "is_digital_download": False,
            "meta_title": "Advanced Product Meta Title",
            "meta_description": "Advanced product meta description",
            "custom_fields": {"color_variant": "midnight", "storage": "128GB"}
        }

    def test_create_advanced_product_success(self):
        """Test successful creation of advanced product"""
        response = client.post("/api/v1/products/", json=self.advanced_product)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate all fields
        assert data["code"] == self.advanced_product["code"]
        assert data["name"] == self.advanced_product["name"]
        assert data["description"] == self.advanced_product["description"]
        assert float(data["price"]) == self.advanced_product["price"]
        assert data["sku"] == self.advanced_product["sku"]
        assert data["barcode"] == self.advanced_product["barcode"]
        assert data["category"] == self.advanced_product["category"]
        assert data["subcategory"] == self.advanced_product["subcategory"]
        assert data["brand"] == self.advanced_product["brand"]
        assert data["manufacturer"] == self.advanced_product["manufacturer"]
        assert data["product_type"] == self.advanced_product["product_type"]
        assert data["status"] == self.advanced_product["status"]
        assert data["is_featured"] == self.advanced_product["is_featured"]
        assert data["tags"] == ["electronics", "smartphone", "premium"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_advanced_product_duplicate_sku_fails(self):
        """Test that duplicate SKU is rejected"""
        # Create first product
        client.post("/api/v1/products/", json=self.advanced_product)
        
        # Try to create another with same SKU
        duplicate_sku_product = self.advanced_product.copy()
        duplicate_sku_product["code"] = "ADV002"
        
        response = client.post("/api/v1/products/", json=duplicate_sku_product)
        assert response.status_code == 400
        assert "SKU" in response.json()["detail"]

    def test_create_advanced_product_duplicate_barcode_fails(self):
        """Test that duplicate barcode is rejected"""
        # Create first product
        client.post("/api/v1/products/", json=self.advanced_product)
        
        # Try to create another with same barcode
        duplicate_barcode_product = self.advanced_product.copy()
        duplicate_barcode_product["code"] = "ADV003"
        duplicate_barcode_product["sku"] = "SKU-ADV003"
        
        response = client.post("/api/v1/products/", json=duplicate_barcode_product)
        assert response.status_code == 400
        assert "barcode" in response.json()["detail"]

    def test_list_advanced_products_with_filters(self):
        """Test listing with advanced filters"""
        # Create test products
        products = [
            {**self.advanced_product, "code": "FILTER1", "sku": "SKU1", "category": "Electronics", "brand": "BrandA", "price": 100.0},
            {**self.advanced_product, "code": "FILTER2", "sku": "SKU2", "category": "Electronics", "brand": "BrandB", "price": 200.0},
            {**self.advanced_product, "code": "FILTER3", "sku": "SKU3", "category": "Furniture", "brand": "BrandA", "price": 300.0},
        ]
        
        for product in products:
            del product["barcode"]  # Remove to avoid duplicates
            client.post("/api/v1/products/", json=product)
        
        # Test category filter
        response = client.get("/api/v1/products/?category=Electronics")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Test brand filter
        response = client.get("/api/v1/products/?brand=BrandA")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Test price range filter
        response = client.get("/api/v1/products/?price_min=150&price_max=250")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert float(data[0]["price"]) == 200.0

    def test_search_advanced_products(self):
        """Test advanced search functionality"""
        # Create searchable products
        products = [
            {**self.advanced_product, "code": "SEARCH1", "sku": "SEARCH-SKU1", "name": "iPhone 15 Pro", "description": "Latest Apple smartphone"},
            {**self.advanced_product, "code": "SEARCH2", "sku": "SEARCH-SKU2", "name": "Samsung Galaxy", "description": "Android smartphone"},
            {**self.advanced_product, "code": "SEARCH3", "sku": "SEARCH-SKU3", "name": "MacBook Pro", "description": "Apple laptop computer"},
        ]
        
        for product in products:
            del product["barcode"]
            client.post("/api/v1/products/", json=product)
        
        # Search by name
        response = client.get("/api/v1/products/?search=iPhone")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "iPhone" in data[0]["name"]
        
        # Search by description
        response = client.get("/api/v1/products/?search=smartphone")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Search by SKU
        response = client.get("/api/v1/products/?search=SEARCH-SKU1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_sort_advanced_products(self):
        """Test sorting functionality"""
        # Create products with different prices and names
        products = [
            {**self.advanced_product, "code": "SORT1", "sku": "SORT-SKU1", "name": "Zebra Product", "price": 300.0},
            {**self.advanced_product, "code": "SORT2", "sku": "SORT-SKU2", "name": "Alpha Product", "price": 100.0},
            {**self.advanced_product, "code": "SORT3", "sku": "SORT-SKU3", "name": "Beta Product", "price": 200.0},
        ]
        
        for product in products:
            del product["barcode"]
            client.post("/api/v1/products/", json=product)
        
        # Sort by name ascending
        response = client.get("/api/v1/products/?sort_by=name&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["name"] == "Alpha Product"
        assert data[1]["name"] == "Beta Product"
        assert data[2]["name"] == "Zebra Product"
        
        # Sort by price descending
        response = client.get("/api/v1/products/?sort_by=price&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        assert float(data[0]["price"]) == 300.0
        assert float(data[1]["price"]) == 200.0
        assert float(data[2]["price"]) == 100.0

    def test_get_product_by_sku(self):
        """Test retrieving product by SKU"""
        # Create product
        response = client.post("/api/v1/products/", json=self.advanced_product)
        assert response.status_code == 200
        
        # Get by SKU
        response = client.get(f"/api/v1/products/sku/{self.advanced_product['sku']}")
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == self.advanced_product["sku"]
        assert data["code"] == self.advanced_product["code"]

    def test_get_product_by_barcode(self):
        """Test retrieving product by barcode"""
        # Create product
        response = client.post("/api/v1/products/", json=self.advanced_product)
        assert response.status_code == 200
        
        # Get by barcode
        response = client.get(f"/api/v1/products/barcode/{self.advanced_product['barcode']}")
        assert response.status_code == 200
        data = response.json()
        assert data["barcode"] == self.advanced_product["barcode"]
        assert data["code"] == self.advanced_product["code"]

    def test_update_advanced_product(self):
        """Test updating advanced product"""
        # Create product
        create_response = client.post("/api/v1/products/", json=self.advanced_product)
        product_id = create_response.json()["id"]
        
        # Update product
        update_data = {
            "name": "Updated Advanced Product",
            "price": 399.99,
            "brand": "UpdatedBrand",
            "is_featured": False,
            "tags": ["updated", "premium"],
            "custom_fields": {"updated": True}
        }
        
        response = client.put(f"/api/v1/products/{product_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert float(data["price"]) == update_data["price"]
        assert data["brand"] == update_data["brand"]
        assert data["is_featured"] == update_data["is_featured"]
        assert data["tags"] == update_data["tags"]
        assert data["custom_fields"]["updated"] == True

    def test_bulk_create_advanced_products(self):
        """Test bulk creation of advanced products"""
        bulk_products = [
            {**self.advanced_product, "code": "BULK1", "sku": "BULK-SKU1", "name": "Bulk Product 1"},
            {**self.advanced_product, "code": "BULK2", "sku": "BULK-SKU2", "name": "Bulk Product 2"},
            {**self.advanced_product, "code": "BULK3", "sku": "BULK-SKU3", "name": "Bulk Product 3"},
        ]
        
        # Remove barcode to avoid duplicates
        for product in bulk_products:
            del product["barcode"]
        
        response = client.post("/api/v1/products/bulk/create", json=bulk_products)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        for i, product in enumerate(data):
            assert product["code"] == bulk_products[i]["code"]
            assert product["sku"] == bulk_products[i]["sku"]
            assert product["name"] == bulk_products[i]["name"]

    def test_bulk_create_with_validation_errors(self):
        """Test bulk creation with validation errors"""
        bulk_products = [
            {**self.advanced_product, "code": "VALID1", "sku": "VALID-SKU1"},
            {**self.advanced_product, "code": "VALID1", "sku": "DUPLICATE-CODE"},  # Duplicate code
            {"code": "", "name": "Invalid", "price": 10.0},  # Invalid product
        ]
        
        for product in bulk_products:
            if "barcode" in product:
                del product["barcode"]
        
        response = client.post("/api/v1/products/bulk/create", json=bulk_products)
        assert response.status_code == 200  # Partial success
        data = response.json()
        assert len(data) == 1  # Only valid product created

    def test_advanced_statistics(self):
        """Test advanced product statistics"""
        # Create diverse products
        products = [
            {**self.advanced_product, "code": "STAT1", "sku": "STAT-SKU1", "category": "Electronics", "status": "active", "is_featured": True, "price": 100.0},
            {**self.advanced_product, "code": "STAT2", "sku": "STAT-SKU2", "category": "Electronics", "status": "inactive", "is_featured": False, "price": 200.0},
            {**self.advanced_product, "code": "STAT3", "sku": "STAT-SKU3", "category": "Furniture", "status": "active", "is_featured": True, "price": 300.0},
        ]
        
        for product in products:
            del product["barcode"]
            client.post("/api/v1/products/", json=product)
        
        response = client.get("/api/v1/products/stats/advanced-summary")
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_products"] == 3
        assert data["active_products"] == 2
        assert data["inactive_products"] == 1
        assert data["featured_products"] == 2
        assert "Electronics" in data["categories_breakdown"]
        assert "Furniture" in data["categories_breakdown"]
        assert data["categories_breakdown"]["Electronics"] == 2
        assert data["categories_breakdown"]["Furniture"] == 1

    def test_featured_products_filter(self):
        """Test filtering by featured products"""
        # Create products with different featured status
        products = [
            {**self.advanced_product, "code": "FEAT1", "sku": "FEAT-SKU1", "is_featured": True},
            {**self.advanced_product, "code": "FEAT2", "sku": "FEAT-SKU2", "is_featured": False},
            {**self.advanced_product, "code": "FEAT3", "sku": "FEAT-SKU3", "is_featured": True},
        ]
        
        for product in products:
            del product["barcode"]
            client.post("/api/v1/products/", json=product)
        
        # Filter featured products
        response = client.get("/api/v1/products/?is_featured=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(product["is_featured"] for product in data)
        
        # Filter non-featured products
        response = client.get("/api/v1/products/?is_featured=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert not data[0]["is_featured"]

    def test_tags_filter(self):
        """Test filtering by tags"""
        # Create products with different tags
        products = [
            {**self.advanced_product, "code": "TAG1", "sku": "TAG-SKU1", "tags": ["electronics", "smartphone"]},
            {**self.advanced_product, "code": "TAG2", "sku": "TAG-SKU2", "tags": ["electronics", "laptop"]},
            {**self.advanced_product, "code": "TAG3", "sku": "TAG-SKU3", "tags": ["furniture", "desk"]},
        ]
        
        for product in products:
            del product["barcode"]
            client.post("/api/v1/products/", json=product)
        
        # Filter by single tag
        response = client.get("/api/v1/products/?tags=electronics")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Filter by specific tag
        response = client.get("/api/v1/products/?tags=smartphone")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_pagination_with_large_dataset(self):
        """Test pagination with larger dataset"""
        # Create 20 products
        products = []
        for i in range(20):
            product = {**self.advanced_product, "code": f"PAGE{i:02d}", "sku": f"PAGE-SKU{i:02d}", "name": f"Product {i:02d}"}
            del product["barcode"]
            products.append(product)
        
        # Bulk create
        client.post("/api/v1/products/bulk/create", json=products)
        
        # Test first page
        response = client.get("/api/v1/products/?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Test second page
        response = client.get("/api/v1/products/?skip=5&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Test last page
        response = client.get("/api/v1/products/?skip=15&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # Only 5 remaining

    def test_dimension_validation(self):
        """Test dimension validation"""
        # Valid dimensions
        valid_product = {**self.advanced_product, "code": "DIM1", "sku": "DIM-SKU1"}
        response = client.post("/api/v1/products/", json=valid_product)
        assert response.status_code == 200
        
        # Invalid dimensions (missing height)
        invalid_dimensions = {"length": 10.0, "width": 5.0}
        invalid_product = {**self.advanced_product, "code": "DIM2", "sku": "DIM-SKU2", "dimensions": invalid_dimensions}
        del invalid_product["barcode"]
        
        response = client.post("/api/v1/products/", json=invalid_product)
        assert response.status_code == 422  # Validation error

    def test_tag_validation_and_normalization(self):
        """Test tag validation and normalization"""
        # Tags should be normalized to lowercase
        product_with_tags = {
            **self.advanced_product, 
            "code": "TAGS1", 
            "sku": "TAGS-SKU1",
            "tags": ["UPPERCASE", "MixedCase", "lowercase", " spaced "]
        }
        del product_with_tags["barcode"]
        
        response = client.post("/api/v1/products/", json=product_with_tags)
        assert response.status_code == 200
        data = response.json()
        
        # Tags should be normalized and spaces trimmed
        expected_tags = ["uppercase", "mixedcase", "lowercase", "spaced"]
        assert data["tags"] == expected_tags

    def test_error_handling_not_found(self):
        """Test error handling for not found scenarios"""
        fake_id = str(uuid.uuid4())
        
        # Get non-existent product by ID
        response = client.get(f"/api/v1/products/{fake_id}")
        assert response.status_code == 404
        
        # Get non-existent product by SKU
        response = client.get("/api/v1/products/sku/NONEXISTENT")
        assert response.status_code == 404
        
        # Get non-existent product by barcode
        response = client.get("/api/v1/products/barcode/000000000000")
        assert response.status_code == 404
        
        # Update non-existent product
        response = client.put(f"/api/v1/products/{fake_id}", json={"name": "Updated"})
        assert response.status_code == 404

    def teardown_method(self):
        """Clean up after each test"""
        try:
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass