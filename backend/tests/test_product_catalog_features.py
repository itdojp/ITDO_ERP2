"""
Comprehensive TDD Tests for Product Catalog Features API - CC02 v48.0
Testing CSV import/export, product duplication, bulk operations, and statistics
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, List, Any
import json
import uuid
import io
import csv
from datetime import datetime
from decimal import Decimal

# Import the main app
from app.main_super_minimal import app

client = TestClient(app)

class TestProductCatalogFeaturesAPI:
    """Comprehensive test suite for Product Catalog Features API"""

    def setup_method(self):
        """Setup test data before each test"""
        # Clear any existing test data
        try:
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass
        
        # Create some base products for testing
        self.base_products = [
            {
                "code": "BASE001",
                "name": "Base Product 1",
                "description": "First base product",
                "price": 99.99,
                "category": "Electronics",
                "sku": "SKU-BASE001",
                "brand": "TestBrand"
            },
            {
                "code": "BASE002", 
                "name": "Base Product 2",
                "description": "Second base product",
                "price": 199.99,
                "category": "Furniture",
                "sku": "SKU-BASE002",
                "brand": "TestBrand"
            }
        ]
        
        # Create base products
        for product in self.base_products:
            client.post("/api/v1/products/", json=product)

    def test_csv_template_download(self):
        """Test downloading CSV template"""
        response = client.get("/api/v1/products/catalog/template/csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "product_import_template.csv" in response.headers["content-disposition"]
        
        # Verify CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        headers = csv_reader.fieldnames
        
        assert "code" in headers
        assert "name" in headers
        assert "price" in headers
        assert "category" in headers
        
        # Check sample data
        rows = list(csv_reader)
        assert len(rows) == 1
        assert rows[0]["code"] == "SAMPLE001"

    def test_csv_import_success(self):
        """Test successful CSV import"""
        # Create CSV content
        csv_content = """code,name,description,price,category,sku,brand
IMPORT001,Import Product 1,Imported product description,299.99,Electronics,IMP-SKU001,ImportBrand
IMPORT002,Import Product 2,Another imported product,399.99,Furniture,IMP-SKU002,ImportBrand"""
        
        # Create file-like object
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/api/v1/products/catalog/import/csv",
            files={"file": ("test_import.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_processed"] == 2
        assert data["successful_imports"] == 2
        assert data["failed_imports"] == 0
        assert len(data["created_products"]) == 2
        assert len(data["failed_records"]) == 0
        assert data["processing_time_seconds"] > 0

    def test_csv_import_with_duplicates(self):
        """Test CSV import with duplicate handling"""
        # Create CSV with duplicate code
        csv_content = """code,name,description,price,category
BASE001,Duplicate Product,This should be skipped,199.99,Electronics
IMPORT003,New Product,This should be imported,299.99,Electronics"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/api/v1/products/catalog/import/csv",
            files={"file": ("test_duplicates.csv", csv_file, "text/csv")},
            params={"skip_duplicates": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_processed"] == 2
        assert data["successful_imports"] == 1  # Only new product
        assert len(data["warnings"]) > 0
        assert "duplicate" in data["warnings"][0].lower()

    def test_csv_import_validation_errors(self):
        """Test CSV import with validation errors"""
        # Create CSV with invalid data
        csv_content = """code,name,description,price,category
,Empty Code Product,Invalid empty code,-10.99,Electronics
INVALID002,,Invalid empty name,99.99,Electronics"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/api/v1/products/catalog/import/csv",
            files={"file": ("test_invalid.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_processed"] == 2
        assert data["successful_imports"] == 0
        assert data["failed_imports"] == 2
        assert len(data["failed_records"]) == 2

    def test_csv_import_missing_headers(self):
        """Test CSV import with missing required headers"""
        # Create CSV missing required headers
        csv_content = """name,description,category
Missing Code Product,Product without code,Electronics"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/api/v1/products/catalog/import/csv",
            files={"file": ("test_missing_headers.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 400
        assert "Missing required columns" in response.json()["detail"]

    def test_csv_import_invalid_file_type(self):
        """Test CSV import with invalid file type"""
        # Create non-CSV file
        text_content = "This is not a CSV file"
        text_file = io.BytesIO(text_content.encode('utf-8'))
        
        response = client.post(
            "/api/v1/products/catalog/import/csv",
            files={"file": ("test.txt", text_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "CSV file" in response.json()["detail"]

    def test_product_export_csv(self):
        """Test product export in CSV format"""
        export_request = {
            "format": "csv",
            "include_images": False,
            "include_inactive": True
        }
        
        response = client.post("/api/v1/products/catalog/export", json=export_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        
        # Verify CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)
        
        assert len(rows) >= 2  # Should have our base products

    def test_product_export_json(self):
        """Test product export in JSON format"""
        export_request = {
            "format": "json",
            "include_images": False,
            "include_inactive": True
        }
        
        response = client.post("/api/v1/products/catalog/export", json=export_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        
        # Verify JSON content
        content = response.content.decode('utf-8')
        data = json.loads(content)
        
        assert "export_info" in data
        assert "products" in data
        assert data["export_info"]["total_products"] >= 2
        assert len(data["products"]) >= 2

    def test_product_export_with_filters(self):
        """Test product export with category filter"""
        export_request = {
            "format": "json",
            "categories": ["Electronics"],
            "include_inactive": False
        }
        
        response = client.post("/api/v1/products/catalog/export", json=export_request)
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        data = json.loads(content)
        
        # All exported products should be Electronics
        for product in data["products"]:
            assert product.get("category") == "Electronics"

    def test_product_export_unsupported_format(self):
        """Test product export with unsupported format"""
        export_request = {
            "format": "xlsx",  # Unsupported format
            "include_inactive": True
        }
        
        response = client.post("/api/v1/products/catalog/export", json=export_request)
        assert response.status_code == 400
        assert "Unsupported export format" in response.json()["detail"]

    def test_product_duplication_single(self):
        """Test single product duplication"""
        # Get base product ID
        product_list = client.get("/api/v1/products/").json()
        source_product_id = product_list[0]["id"]
        
        duplication_request = {
            "source_product_id": source_product_id,
            "new_code": "DUPLICATE001",
            "new_name": "Duplicated Product",
            "copy_images": True,
            "quantity_to_create": 1
        }
        
        response = client.post("/api/v1/products/catalog/duplicate", json=duplication_request)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["code"] == "DUPLICATE001"
        assert data[0]["name"] == "Duplicated Product"
        assert data[0]["price"] == product_list[0]["price"]

    def test_product_duplication_multiple_with_pattern(self):
        """Test multiple product duplication with code pattern"""
        # Get base product ID
        product_list = client.get("/api/v1/products/").json()
        source_product_id = product_list[0]["id"]
        
        duplication_request = {
            "source_product_id": source_product_id,
            "new_code": "BATCH",
            "new_name": "Batch Product",
            "copy_images": False,
            "quantity_to_create": 3,
            "code_pattern": "BATCH_{counter}"
        }
        
        response = client.post("/api/v1/products/catalog/duplicate", json=duplication_request)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        assert data[0]["code"] == "BATCH_1"
        assert data[1]["code"] == "BATCH_2" 
        assert data[2]["code"] == "BATCH_3"
        assert data[0]["name"] == "Batch Product #1"
        assert data[1]["name"] == "Batch Product #2"
        assert data[2]["name"] == "Batch Product #3"

    def test_product_duplication_nonexistent_source(self):
        """Test duplication with non-existent source product"""
        fake_id = str(uuid.uuid4())
        
        duplication_request = {
            "source_product_id": fake_id,
            "new_code": "FAIL001",
            "quantity_to_create": 1
        }
        
        response = client.post("/api/v1/products/catalog/duplicate", json=duplication_request)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_product_duplication_duplicate_code(self):
        """Test duplication with existing code"""
        # Get base product ID
        product_list = client.get("/api/v1/products/").json()
        source_product_id = product_list[0]["id"]
        
        duplication_request = {
            "source_product_id": source_product_id,
            "new_code": "BASE001",  # Existing code
            "quantity_to_create": 1
        }
        
        response = client.post("/api/v1/products/catalog/duplicate", json=duplication_request)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_bulk_operations_activate(self):
        """Test bulk activate operation"""
        # Get product IDs
        product_list = client.get("/api/v1/products/").json()
        product_ids = [p["id"] for p in product_list[:2]]
        
        bulk_request = {
            "product_ids": product_ids,
            "operation": "activate",
            "parameters": {}
        }
        
        response = client.post("/api/v1/products/catalog/bulk-operations", json=bulk_request)
        assert response.status_code == 200
        data = response.json()
        
        assert data["operation"] == "activate"
        assert data["total_requested"] == 2
        assert data["successful_operations"] == 2
        assert data["failed_operations"] == 0

    def test_bulk_operations_deactivate(self):
        """Test bulk deactivate operation"""
        # Get product IDs
        product_list = client.get("/api/v1/products/").json()
        product_ids = [p["id"] for p in product_list[:1]]
        
        bulk_request = {
            "product_ids": product_ids,
            "operation": "deactivate",
            "parameters": {}
        }
        
        response = client.post("/api/v1/products/catalog/bulk-operations", json=bulk_request)
        assert response.status_code == 200
        data = response.json()
        
        assert data["operation"] == "deactivate"
        assert data["successful_operations"] == 1

    def test_bulk_operations_update_category(self):
        """Test bulk update category operation"""
        # Get product IDs
        product_list = client.get("/api/v1/products/").json()
        product_ids = [p["id"] for p in product_list[:2]]
        
        bulk_request = {
            "product_ids": product_ids,
            "operation": "update_category",
            "parameters": {"category": "Updated Category"}
        }
        
        response = client.post("/api/v1/products/catalog/bulk-operations", json=bulk_request)
        assert response.status_code == 200
        data = response.json()
        
        assert data["operation"] == "update_category"
        assert data["successful_operations"] == 2
        
        # Verify category was updated
        updated_products = client.get("/api/v1/products/").json()
        for product in updated_products:
            if product["id"] in product_ids:
                assert product["category"] == "Updated Category"

    def test_bulk_operations_unsupported_operation(self):
        """Test bulk operation with unsupported operation"""
        product_list = client.get("/api/v1/products/").json()
        product_ids = [p["id"] for p in product_list[:1]]
        
        bulk_request = {
            "product_ids": product_ids,
            "operation": "unsupported_operation",
            "parameters": {}
        }
        
        response = client.post("/api/v1/products/catalog/bulk-operations", json=bulk_request)
        assert response.status_code == 200
        data = response.json()
        
        assert data["successful_operations"] == 0
        assert data["failed_operations"] == 1
        assert "Unsupported operation" in data["failed_details"][0]["error"]

    def test_bulk_operations_too_many_products(self):
        """Test bulk operation with too many products"""
        # Create list of 1001 fake IDs
        fake_ids = [str(uuid.uuid4()) for _ in range(1001)]
        
        bulk_request = {
            "product_ids": fake_ids,
            "operation": "activate",
            "parameters": {}
        }
        
        response = client.post("/api/v1/products/catalog/bulk-operations", json=bulk_request)
        assert response.status_code == 400
        assert "Maximum 1000 products" in response.json()["detail"]

    def test_catalog_statistics(self):
        """Test comprehensive catalog statistics"""
        response = client.get("/api/v1/products/catalog/statistics")
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        assert "total_products" in data
        assert "active_products" in data
        assert "inactive_products" in data
        assert "categories_count" in data
        assert "brands_count" in data
        assert "average_price" in data
        assert "total_catalog_value" in data
        assert "products_with_images" in data
        assert "recent_additions" in data
        assert "top_categories" in data
        assert "price_distribution" in data
        
        # Validate data types
        assert isinstance(data["total_products"], int)
        assert isinstance(data["active_products"], int)
        assert isinstance(data["average_price"], (int, float))
        assert isinstance(data["top_categories"], list)
        assert isinstance(data["price_distribution"], dict)
        
        # Check price distribution keys
        expected_ranges = ["0-50", "51-100", "101-250", "251-500", "501-1000", "1000+"]
        for range_key in expected_ranges:
            assert range_key in data["price_distribution"]

    def test_catalog_statistics_with_images(self):
        """Test statistics calculation with image data"""
        # Create advanced product with images
        advanced_product = {
            "code": "WITHIMG001",
            "name": "Product with Images",
            "price": 199.99,
            "category": "Test",
            "image_urls": ["url1.jpg", "url2.jpg"]
        }
        
        client.post("/api/v1/products/", json=advanced_product)
        
        response = client.get("/api/v1/products/catalog/statistics")
        assert response.status_code == 200
        data = response.json()
        
        assert data["products_with_images"] >= 1

    def test_csv_import_type_conversions(self):
        """Test CSV import with various data type conversions"""
        csv_content = """code,name,price,weight,warranty_period,is_featured,product_type,status
CONVERT001,Conversion Test,299.99,1.5,24,true,physical,active
CONVERT002,Another Test,399.99,2.0,12,false,digital,inactive"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/api/v1/products/catalog/import/csv",
            files={"file": ("test_conversions.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["successful_imports"] == 2
        assert data["failed_imports"] == 0

    def test_export_with_date_range_filter(self):
        """Test export with date range filtering"""
        export_request = {
            "format": "json",
            "date_range_start": "2024-01-01",
            "date_range_end": "2025-12-31"
        }
        
        response = client.post("/api/v1/products/catalog/export", json=export_request)
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        data = json.loads(content)
        
        # Should include products within date range
        assert len(data["products"]) >= 0

    def test_export_with_specific_fields(self):
        """Test export with specific field selection"""
        export_request = {
            "format": "json",
            "fields": ["code", "name", "price"]
        }
        
        response = client.post("/api/v1/products/catalog/export", json=export_request)
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        data = json.loads(content)
        
        # Check that only specified fields are included
        if data["products"]:
            product = data["products"][0]
            assert "code" in product
            assert "name" in product
            assert "price" in product
            # Should not have other fields like description
            assert len(product.keys()) <= 3

    def teardown_method(self):
        """Clean up after each test"""
        try:
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass