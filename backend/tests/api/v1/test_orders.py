"""
TDD Tests for Order Management API - CC02 v49.0 Phase 4
48-Hour Backend Blitz - Order Management Implementation
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import uuid
from datetime import datetime


class TestOrderAPI:
    """Test suite for Order Management API - TDD Implementation Phase 4"""

    def setup_method(self):
        """Setup test data for each test method"""
        # We'll need customer and product data for orders
        pass

    def test_create_order(self, api_client: TestClient):
        """Test order creation endpoint"""
        # First create customer and product
        customer_data = {
            "name": "Order Test Customer",
            "email": "order@test.com",
            "phone": "+1-555-0800"
        }
        customer_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = customer_response.json()["id"]
        
        product_data = {"name": "Order Test Product", "price": 100, "sku": "ORDER001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        order_data = {
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "unit_price": 100.0
                }
            ],
            "order_date": datetime.now().isoformat(),
            "status": "pending",
            "notes": "Test order"
        }
        response = api_client.post("/api/v1/orders", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == customer_id
        assert len(data["items"]) == 1
        assert data["total_amount"] == 200.0  # 2 * 100
        assert "id" in data
        assert "created_at" in data

    def test_create_order_validation_error(self, api_client: TestClient):
        """Test order creation with validation errors"""
        # Missing required fields
        invalid_data = {"customer_id": "fake-id"}  # Missing items
        response = api_client.post("/api/v1/orders", json=invalid_data)
        assert response.status_code == 422

    def test_create_order_invalid_customer(self, api_client: TestClient):
        """Test order creation with invalid customer"""
        fake_customer_id = str(uuid.uuid4())
        order_data = {
            "customer_id": fake_customer_id,
            "items": [
                {
                    "product_id": "fake-product-id",
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ]
        }
        response = api_client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 404
        assert "Customer not found" in response.json()["detail"]

    def test_get_order_by_id(self, api_client: TestClient):
        """Test retrieving order by ID"""
        # Create customer, product, and order
        customer_data = {"name": "Get Order Customer", "email": "getorder@test.com"}
        customer_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = customer_response.json()["id"]
        
        product_data = {"name": "Get Order Product", "price": 150, "sku": "GETORDER001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        order_data = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 150.0}]
        }
        create_response = api_client.post("/api/v1/orders", json=order_data)
        order_id = create_response.json()["id"]
        
        # Get order
        response = api_client.get(f"/api/v1/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["id"] == order_id
        assert response.json()["customer_id"] == customer_id

    def test_get_order_not_found(self, api_client: TestClient):
        """Test retrieving non-existent order"""
        fake_id = str(uuid.uuid4())
        response = api_client.get(f"/api/v1/orders/{fake_id}")
        assert response.status_code == 404

    def test_list_orders(self, api_client: TestClient):
        """Test listing orders with pagination"""
        # Create customer and product
        customer_data = {"name": "List Orders Customer", "email": "listorders@test.com"}
        customer_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = customer_response.json()["id"]
        
        product_data = {"name": "List Orders Product", "price": 75, "sku": "LISTORDER001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        # Create test orders
        for i in range(3):
            order_data = {
                "customer_id": customer_id,
                "items": [{"product_id": product_id, "quantity": i+1, "unit_price": 75.0}],
                "notes": f"List test order {i+1}"
            }
            api_client.post("/api/v1/orders", json=order_data)
        
        # List orders
        response = api_client.get("/api/v1/orders")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3
        assert "total" in data
        assert "page" in data

    def test_update_order_status(self, api_client: TestClient):
        """Test updating order status"""
        # Create customer, product, and order
        customer_data = {"name": "Update Status Customer", "email": "updatestatus@test.com"}
        customer_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = customer_response.json()["id"]
        
        product_data = {"name": "Update Status Product", "price": 200, "sku": "UPDATESTATUS001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        order_data = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 200.0}]
        }
        create_response = api_client.post("/api/v1/orders", json=order_data)
        order_id = create_response.json()["id"]
        
        # Update order status
        update_data = {"status": "confirmed", "notes": "Order confirmed"}
        response = api_client.put(f"/api/v1/orders/{order_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"
        assert response.json()["notes"] == "Order confirmed"

    def test_cancel_order(self, api_client: TestClient):
        """Test cancelling an order"""
        # Create customer, product, and order
        customer_data = {"name": "Cancel Order Customer", "email": "cancelorder@test.com"}
        customer_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = customer_response.json()["id"]
        
        product_data = {"name": "Cancel Order Product", "price": 300, "sku": "CANCELORDER001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        order_data = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 300.0}]
        }
        create_response = api_client.post("/api/v1/orders", json=order_data)
        order_id = create_response.json()["id"]
        
        # Cancel order
        response = api_client.delete(f"/api/v1/orders/{order_id}")
        assert response.status_code == 200
        
        # Verify order is cancelled
        get_response = api_client.get(f"/api/v1/orders/{order_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "cancelled"

    def test_order_items_management(self, api_client: TestClient):
        """Test order items management"""
        # Create customer and products
        customer_data = {"name": "Items Test Customer", "email": "items@test.com"}
        customer_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = customer_response.json()["id"]
        
        product1_data = {"name": "Item Product 1", "price": 50, "sku": "ITEM001"}
        product1_response = api_client.post("/api/v1/products", json=product1_data)
        product1_id = product1_response.json()["id"]
        
        product2_data = {"name": "Item Product 2", "price": 75, "sku": "ITEM002"}
        product2_response = api_client.post("/api/v1/products", json=product2_data)
        product2_id = product2_response.json()["id"]
        
        # Create order with multiple items
        order_data = {
            "customer_id": customer_id,
            "items": [
                {"product_id": product1_id, "quantity": 2, "unit_price": 50.0},
                {"product_id": product2_id, "quantity": 1, "unit_price": 75.0}
            ]
        }
        response = api_client.post("/api/v1/orders", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total_amount"] == 175.0  # (2*50) + (1*75)

    def test_order_customer_relationship(self, api_client: TestClient):
        """Test order-customer relationship"""
        # Create customer
        customer_data = {"name": "Relationship Test Customer", "email": "relationship@test.com"}
        customer_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = customer_response.json()["id"]
        
        # Create product
        product_data = {"name": "Relationship Product", "price": 100, "sku": "RELATION001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        # Create order
        order_data = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 100.0}]
        }
        api_client.post("/api/v1/orders", json=order_data)
        
        # Check customer orders
        response = api_client.get(f"/api/v1/customers/{customer_id}/orders")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

    def test_order_statistics(self, api_client: TestClient):
        """Test order statistics endpoint"""
        # Create customer and product for statistics
        customer_data = {"name": "Stats Order Customer", "email": "statsorder@test.com"}
        customer_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = customer_response.json()["id"]
        
        product_data = {"name": "Stats Order Product", "price": 100, "sku": "STATSORDER001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        # Create diverse orders
        statuses = ["pending", "confirmed", "cancelled"]
        for i, status in enumerate(statuses):
            order_data = {
                "customer_id": customer_id,
                "items": [{"product_id": product_id, "quantity": i+1, "unit_price": 100.0}],
                "status": status
            }
            api_client.post("/api/v1/orders", json=order_data)
        
        response = api_client.get("/api/v1/orders/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "order_statuses" in data
        assert "total_revenue" in data

    def test_order_performance_metrics(self, api_client: TestClient):
        """Test order API performance requirements (<50ms)"""
        import time
        
        # Create customer and product
        customer_data = {"name": "Performance Order Customer", "email": "perforder@test.com"}
        customer_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = customer_response.json()["id"]
        
        product_data = {"name": "Performance Order Product", "price": 100, "sku": "PERFORDER001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        order_data = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 100.0}]
        }
        
        # Measure creation time
        start_time = time.time()
        response = api_client.post("/api/v1/orders", json=order_data)
        end_time = time.time()
        
        creation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 201
        assert creation_time < 50, f"Order creation took {creation_time}ms, exceeds 50ms limit"
        
        order_id = response.json()["id"]
        
        # Measure retrieval time
        start_time = time.time()
        response = api_client.get(f"/api/v1/orders/{order_id}")
        end_time = time.time()
        
        retrieval_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert retrieval_time < 50, f"Order retrieval took {retrieval_time}ms, exceeds 50ms limit"