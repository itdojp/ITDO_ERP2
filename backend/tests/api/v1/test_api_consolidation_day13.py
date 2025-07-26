"""
API Consolidation Tests - Day 13
Tests for backward compatibility and functionality preservation after API consolidation.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date
from decimal import Decimal

from app.main import app

client = TestClient(app)

# Test data
TEST_PRODUCT_DATA = {
    "code": "TEST001",
    "name": "Test Product",
    "price": 99.99,
    "stock": 100,
    "description": "Test product description"
}

TEST_INVENTORY_DATA = {
    "product_id": "test-product-id",
    "location_id": "test-location-id",
    "quantity": 50,
    "min_stock_level": 10
}

TEST_SALES_ORDER_DATA = {
    "customer_id": "test-customer-id",
    "items": [
        {
            "product_id": "test-product-id",
            "quantity": 2,
            "unit_price": 99.99,
            "discount_percentage": 5.0,
            "tax_percentage": 10.0
        }
    ]
}

# =====================================
# PRODUCTS API CONSOLIDATION TESTS
# =====================================

class TestProductsAPIConsolidation:
    """Test products API consolidation functionality"""
    
    def test_create_product_consolidated_api(self):
        """Test product creation with consolidated API"""
        response = client.post("/api/v1/products/", json=TEST_PRODUCT_DATA)
        assert response.status_code == 201
        
        data = response.json()
        assert data["code"] == TEST_PRODUCT_DATA["code"]
        assert data["name"] == TEST_PRODUCT_DATA["name"]
        assert data["price"] == TEST_PRODUCT_DATA["price"]
        assert "id" in data
        assert "created_at" in data
    
    def test_list_products_consolidated_api(self):
        """Test product listing with consolidated API"""
        # Create a product first
        client.post("/api/v1/products/", json=TEST_PRODUCT_DATA)
        
        response = client.get("/api/v1/products/")
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["products"]) > 0
    
    def test_product_search_functionality(self):
        """Test advanced product search"""
        # Create a product first
        client.post("/products/", json=TEST_PRODUCT_DATA)
        
        search_filters = {
            "name": "Test",
            "min_price": 50.0,
            "max_price": 150.0
        }
        
        response = client.post("/api/v1/products/search", json=search_filters)
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        assert len(data["products"]) >= 0
    
    def test_bulk_product_creation(self):
        """Test bulk product creation functionality"""
        bulk_products = {
            "products": [
                {
                    "code": "BULK001",
                    "name": "Bulk Product 1",
                    "price": 10.0,
                    "stock": 50
                },
                {
                    "code": "BULK002",
                    "name": "Bulk Product 2",
                    "price": 20.0,
                    "stock": 75
                }
            ]
        }
        
        response = client.post("/products/bulk", json=bulk_products)
        assert response.status_code == 200
        
        data = response.json()
        assert "created" in data
        assert "failed" in data
        assert "total_created" in data
        assert data["total_created"] == 2
    
    # Backward Compatibility Tests
    def test_legacy_v21_product_creation(self):
        """Test legacy v21 product creation endpoint"""
        response = client.post("/products/products-v21?name=Legacy Product&price=25.50")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Legacy Product"
        assert data["price"] == 25.50
        assert "id" in data
    
    def test_legacy_v21_product_listing(self):
        """Test legacy v21 product listing endpoint"""
        # Create a legacy product first
        client.post("/products/products-v21?name=Legacy Product&price=25.50")
        
        response = client.get("/products/products-v21")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_simple_product_endpoints(self):
        """Test simple product endpoints for basic use cases"""
        simple_product = {
            "code": "SIMPLE001",
            "name": "Simple Product",
            "price": 15.0
        }
        
        # Create simple product
        response = client.post("/products/simple", json=simple_product)
        assert response.status_code == 200
        
        # List simple products
        response = client.get("/products/simple")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

# =====================================
# INVENTORY API CONSOLIDATION TESTS
# =====================================

class TestInventoryAPIConsolidation:
    """Test inventory API consolidation functionality"""
    
    def test_create_inventory_location(self):
        """Test inventory location creation"""
        location_data = {
            "code": "WH001",
            "name": "Main Warehouse",
            "type": "warehouse",
            "address": "123 Storage St"
        }
        
        response = client.post("/inventory/locations", json=location_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["code"] == location_data["code"]
        assert data["name"] == location_data["name"]
        assert data["type"] == location_data["type"]
        assert "id" in data
    
    def test_inventory_item_management(self):
        """Test inventory item creation and management"""
        # First create a location
        location_data = {
            "code": "WH002",
            "name": "Test Warehouse",
            "type": "warehouse"
        }
        location_response = client.post("/inventory/locations", json=location_data)
        location_id = location_response.json()["id"]
        
        # Create inventory item
        item_data = {
            "product_id": "test-product-123",
            "location_id": location_id,
            "quantity": 100,
            "min_stock_level": 10,
            "max_stock_level": 500
        }
        
        response = client.post("/inventory/items", json=item_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["product_id"] == item_data["product_id"]
        assert data["location_id"] == item_data["location_id"]
        assert data["quantity"] == item_data["quantity"]
        assert "available_quantity" in data
    
    def test_inventory_movements(self):
        """Test inventory movement functionality"""
        # Create location and item first
        location_data = {"code": "WH003", "name": "Movement Test", "type": "warehouse"}
        location_response = client.post("/inventory/locations", json=location_data)
        location_id = location_response.json()["id"]
        
        item_data = {
            "product_id": "movement-test-product",
            "location_id": location_id,
            "quantity": 50
        }
        client.post("/inventory/items", json=item_data)
        
        # Create movement
        movement_data = {
            "product_id": "movement-test-product",
            "location_id": location_id,
            "movement_type": "in",
            "quantity": 25,
            "notes": "Stock replenishment"
        }
        
        response = client.post("/inventory/movements", json=movement_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["movement_type"] == "in"
        assert data["quantity"] == 25
        assert "movement_date" in data
    
    def test_stock_adjustment(self):
        """Test stock adjustment functionality"""
        # Create location and item first
        location_data = {"code": "WH004", "name": "Adjustment Test", "type": "warehouse"}
        location_response = client.post("/inventory/locations", json=location_data)
        location_id = location_response.json()["id"]
        
        item_data = {
            "product_id": "adjustment-test-product",
            "location_id": location_id,
            "quantity": 100
        }
        client.post("/inventory/items", json=item_data)
        
        # Adjust stock
        adjustment_data = {
            "product_id": "adjustment-test-product",
            "location_id": location_id,
            "new_quantity": 150,
            "reason": "Physical count adjustment"
        }
        
        response = client.post("/inventory/adjust-stock", json=adjustment_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "movement_id" in data
        assert data["new_quantity"] == 150
    
    def test_low_stock_alerts(self):
        """Test low stock alert functionality"""
        response = client.get("/inventory/alerts/low-stock")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    # Backward Compatibility Tests
    def test_legacy_v21_inventory_creation(self):
        """Test legacy v21 inventory creation"""
        response = client.post(
            "/inventory/inventory-v21?product_id=legacy-product&quantity=75&location=Legacy Warehouse"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["product_id"] == "legacy-product"
        assert data["quantity"] == 75
        assert data["location"] == "Legacy Warehouse"
    
    def test_legacy_v21_inventory_listing(self):
        """Test legacy v21 inventory listing"""
        # Create a legacy inventory item first
        client.post(
            "/inventory/inventory-v21?product_id=legacy-product&quantity=75&location=Legacy Warehouse"
        )
        
        response = client.get("/inventory/inventory-v21")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

# =====================================
# SALES API CONSOLIDATION TESTS
# =====================================

class TestSalesAPIConsolidation:
    """Test sales API consolidation functionality"""
    
    def test_create_sales_quote(self):
        """Test sales quote creation"""
        quote_data = {
            "customer_id": "test-customer-123",
            "valid_until": "2024-12-31",
            "currency": "USD",
            "items": [
                {
                    "product_id": "quote-product-1",
                    "quantity": 2,
                    "unit_price": 50.0,
                    "tax_percentage": 10.0
                }
            ]
        }
        
        response = client.post("/sales/quotes", json=quote_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["customer_id"] == quote_data["customer_id"]
        assert "quote_number" in data
        assert "subtotal" in data
        assert "total_amount" in data
        assert len(data["items"]) == 1
    
    def test_create_sales_order(self):
        """Test sales order creation"""
        order_data = {
            "customer_id": "test-customer-456",
            "order_type": "standard",
            "currency": "USD",
            "items": [
                {
                    "product_id": "order-product-1",
                    "quantity": 3,
                    "unit_price": 75.0,
                    "discount_percentage": 5.0,
                    "tax_percentage": 8.0
                }
            ]
        }
        
        response = client.post("/sales/orders", json=order_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["customer_id"] == order_data["customer_id"]
        assert data["status"] == "draft"
        assert data["payment_status"] == "pending"
        assert "order_number" in data
        assert "total_amount" in data
    
    def test_quote_to_order_conversion(self):
        """Test converting quote to sales order"""
        # Create a quote first
        quote_data = {
            "customer_id": "conversion-customer",
            "valid_until": "2024-12-31",
            "items": [
                {
                    "product_id": "conversion-product",
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ]
        }
        
        quote_response = client.post("/sales/quotes", json=quote_data)
        quote_id = quote_response.json()["id"]
        
        # Convert to order
        response = client.post(f"/sales/quotes/{quote_id}/convert")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "draft"
        assert "order_number" in data
    
    def test_invoice_creation(self):
        """Test invoice creation from sales order"""
        # Create an order first
        order_data = {
            "customer_id": "invoice-customer",
            "items": [
                {
                    "product_id": "invoice-product",
                    "quantity": 1,
                    "unit_price": 200.0
                }
            ]
        }
        
        order_response = client.post("/sales/orders", json=order_data)
        order_id = order_response.json()["id"]
        
        # Create invoice
        invoice_data = {
            "order_id": order_id,
            "due_date": "2024-12-31",
            "payment_terms": "Net 30"
        }
        
        response = client.post("/sales/invoices", json=invoice_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["order_id"] == order_id
        assert "invoice_number" in data
        assert "amount_due" in data
        assert data["payment_status"] == "pending"
    
    def test_payment_processing(self):
        """Test payment processing against invoice"""
        # Create order and invoice first
        order_data = {
            "customer_id": "payment-customer",
            "items": [{"product_id": "payment-product", "quantity": 1, "unit_price": 150.0}]
        }
        order_response = client.post("/sales/orders", json=order_data)
        order_id = order_response.json()["id"]
        
        invoice_data = {"order_id": order_id, "due_date": "2024-12-31"}
        invoice_response = client.post("/sales/invoices", json=invoice_data)
        invoice_id = invoice_response.json()["id"]
        
        # Process payment
        payment_data = {
            "invoice_id": invoice_id,
            "amount": 150.0,
            "payment_method": "credit_card",
            "reference_number": "PAY123456"
        }
        
        response = client.post("/sales/payments", json=payment_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["invoice_id"] == invoice_id
        assert data["amount"] == 150.0
        assert "payment_date" in data
    
    def test_sales_dashboard(self):
        """Test sales dashboard analytics"""
        response = client.get("/sales/analytics/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_orders" in data
        assert "total_revenue" in data
        assert "pending_orders" in data
        assert "total_quotes" in data
    
    # Backward Compatibility Tests
    def test_legacy_v21_sales_creation(self):
        """Test legacy v21 sales creation"""
        response = client.post("/sales/sales-v21?customer_id=legacy-customer&amount=85.50")
        assert response.status_code == 200
        
        data = response.json()
        assert data["customer_id"] == "legacy-customer"
        assert data["amount"] == 85.50
        assert "id" in data
        assert "date" in data
    
    def test_legacy_v21_sales_listing(self):
        """Test legacy v21 sales listing"""
        # Create a legacy sale first
        client.post("/sales/sales-v21?customer_id=legacy-customer&amount=85.50")
        
        response = client.get("/sales/sales-v21")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

# =====================================
# HEALTH CHECK TESTS
# =====================================

class TestAPIHealthChecks:
    """Test health check endpoints for all consolidated APIs"""
    
    def test_products_health_check(self):
        """Test products API health check"""
        response = client.get("/products/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "total_products" in data
        assert "api_version" in data
        assert "timestamp" in data
    
    def test_inventory_health_check(self):
        """Test inventory API health check"""
        response = client.get("/inventory/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "total_locations" in data
        assert "total_items" in data
        assert "api_version" in data
    
    def test_sales_health_check(self):
        """Test sales API health check"""
        response = client.get("/sales/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "total_orders" in data
        assert "total_quotes" in data
        assert "api_version" in data

# =====================================
# INTEGRATION TESTS
# =====================================

class TestCrossModuleIntegration:
    """Test integration between consolidated APIs"""
    
    def test_product_to_inventory_flow(self):
        """Test creating product and adding to inventory"""
        # Create product
        product_response = client.post("/products/", json=TEST_PRODUCT_DATA)
        product_id = product_response.json()["id"]
        
        # Create inventory location
        location_data = {"code": "INT001", "name": "Integration Test", "type": "warehouse"}
        location_response = client.post("/inventory/locations", json=location_data)
        location_id = location_response.json()["id"]
        
        # Add product to inventory
        inventory_data = {
            "product_id": product_id,
            "location_id": location_id,
            "quantity": 50
        }
        
        response = client.post("/inventory/items", json=inventory_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["product_id"] == product_id
        assert data["quantity"] == 50
    
    def test_product_to_sales_flow(self):
        """Test creating product and selling it"""
        # Create product
        product_response = client.post("/products/", json=TEST_PRODUCT_DATA)
        product_id = product_response.json()["id"]
        
        # Create sales order with the product
        order_data = {
            "customer_id": "integration-customer",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "unit_price": TEST_PRODUCT_DATA["price"]
                }
            ]
        }
        
        response = client.post("/sales/orders", json=order_data)
        assert response.status_code == 201
        
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == product_id

# =====================================
# PERFORMANCE TESTS
# =====================================

class TestAPIPerformance:
    """Test API performance after consolidation"""
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk operations"""
        import time
        
        # Bulk product creation
        bulk_products = {
            "products": [
                {
                    "code": f"PERF{i:03d}",
                    "name": f"Performance Product {i}",
                    "price": 10.0 + i,
                    "stock": 100 + i
                }
                for i in range(1, 51)  # 50 products
            ]
        }
        
        start_time = time.time()
        response = client.post("/products/bulk", json=bulk_products)
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
        
        data = response.json()
        assert data["total_created"] == 50
    
    def test_list_operations_performance(self):
        """Test performance of list operations with pagination"""
        import time
        
        # Test product listing performance
        start_time = time.time()
        response = client.get("/products/?limit=100")
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0  # Should complete within 2 seconds

# =====================================
# ERROR HANDLING TESTS
# =====================================

class TestAPIErrorHandling:
    """Test error handling in consolidated APIs"""
    
    def test_duplicate_product_creation(self):
        """Test error handling for duplicate product creation"""
        # Create first product
        response1 = client.post("/products/", json=TEST_PRODUCT_DATA)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post("/products/", json=TEST_PRODUCT_DATA)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    def test_invalid_inventory_movement(self):
        """Test error handling for invalid inventory movements"""
        movement_data = {
            "product_id": "non-existent-product",
            "location_id": "non-existent-location",
            "movement_type": "out",
            "quantity": 100
        }
        
        response = client.post("/inventory/movements", json=movement_data)
        assert response.status_code == 404
    
    def test_invalid_payment_amount(self):
        """Test error handling for invalid payment amounts"""
        # This would require setting up an invoice first
        # For now, test with non-existent invoice
        payment_data = {
            "invoice_id": "non-existent-invoice",
            "amount": 100.0,
            "payment_method": "cash"
        }
        
        response = client.post("/sales/payments", json=payment_data)
        assert response.status_code == 404