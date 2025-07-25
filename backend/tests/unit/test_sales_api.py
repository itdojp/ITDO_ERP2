"""
CC02 v53.0 Sales API Tests - Issue #568
10-Day ERP Business API Implementation Sprint - Day 5-6 Phase 3
Comprehensive Test-Driven Development Test Suite
"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import date, datetime
import uuid
from typing import List, Dict, Any

from app.main_super_minimal import app

class TestSalesAPIv53:
    """CC02 v53.0 Sales Management API Test Suite"""
    
    @pytest.fixture(autouse=True)
    def setup_clean_state(self):
        """Clear in-memory stores before each test"""
        from app.api.v1.endpoints.sales_v53 import customers_store, sales_orders_store, payments_store, quotes_store
        customers_store.clear()
        sales_orders_store.clear()
        payments_store.clear()
        quotes_store.clear()
    
    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for CC02 v53.0 sales API testing."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_customer_data(self) -> Dict[str, Any]:
        """Sample customer data for testing."""
        return {
            "name": "Test Customer Ltd",
            "email": "test@customer.com",
            "phone": "+1-555-0123",
            "company": "Test Company",
            "tax_id": "TAX-12345",
            "billing_address": "123 Business St, City, State 12345",
            "shipping_address": "456 Shipping Ave, City, State 12345",
            "customer_type": "business",
            "credit_limit": "50000.00",
            "payment_terms": 30,
            "is_active": True,
            "notes": "Premium customer with excellent payment history"
        }
    
    @pytest.fixture
    def sample_order_line_item(self) -> Dict[str, Any]:
        """Sample order line item for testing."""
        return {
            "product_id": "prod-12345",
            "quantity": "5.0",
            "unit_price": "199.99",
            "discount_percent": "10.0",
            "tax_rate": "8.25",
            "notes": "Customer requested expedited processing"
        }
    
    @pytest.fixture
    def sample_order_data(self, sample_order_line_item) -> Dict[str, Any]:
        """Sample sales order data for testing."""
        return {
            "customer_id": "will-be-replaced",
            "order_type": "sales",
            "line_items": [sample_order_line_item],
            "shipping_method": "express",
            "shipping_address": "456 Delivery Ave, City, State 12345",
            "payment_method": "credit_card",
            "payment_terms": 30,
            "priority": "high",
            "notes": "Rush order for important client"
        }
    
    # Customer Management Tests
    
    def test_create_customer_basic(self, client: TestClient, sample_customer_data):
        """Test basic customer creation with required fields only"""
        basic_customer = {
            "name": "Basic Customer",
            "customer_type": "individual",
            "is_active": True
        }
        
        response = client.post("/api/v1/sales-v53/customers/", json=basic_customer)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Basic Customer"
        assert data["customer_type"] == "individual"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert data["current_balance"] == "0"
        assert data["total_orders"] == 0
        assert data["total_spent"] == "0"
    
    def test_create_customer_comprehensive(self, client: TestClient, sample_customer_data):
        """Test comprehensive customer creation with all fields"""
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_customer_data["name"]
        assert data["email"] == sample_customer_data["email"]
        assert data["phone"] == sample_customer_data["phone"]
        assert data["company"] == sample_customer_data["company"]
        assert data["tax_id"] == sample_customer_data["tax_id"]
        assert data["billing_address"] == sample_customer_data["billing_address"]
        assert data["shipping_address"] == sample_customer_data["shipping_address"]
        assert data["customer_type"] == sample_customer_data["customer_type"]
        assert float(data["credit_limit"]) == float(sample_customer_data["credit_limit"])
        assert data["payment_terms"] == sample_customer_data["payment_terms"]
        assert data["is_active"] is True
        assert data["notes"] == sample_customer_data["notes"]
    
    def test_create_customer_duplicate_email(self, client: TestClient):
        """Test customer creation with duplicate email fails"""
        customer_data = {
            "name": "Customer One",
            "email": "duplicate@test.com"
        }
        
        # Create first customer
        response1 = client.post("/api/v1/sales-v53/customers/", json=customer_data)
        assert response1.status_code == 201
        
        # Try to create second customer with same email
        customer_data["name"] = "Customer Two"
        response2 = client.post("/api/v1/sales-v53/customers/", json=customer_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    def test_list_customers_empty(self, client: TestClient):
        """Test listing customers when none exist"""
        response = client.get("/api/v1/sales-v53/customers/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 50
        assert data["pages"] == 0
    
    def test_list_customers_with_data(self, client: TestClient, sample_customer_data):
        """Test listing customers with pagination and filtering"""
        # Create test customers
        customers = []
        for i in range(3):
            customer_data = sample_customer_data.copy()
            customer_data["name"] = f"Customer {i+1}"
            customer_data["email"] = f"customer{i+1}@test.com"
            customer_data["customer_type"] = "business" if i % 2 == 0 else "individual"
            response = client.post("/api/v1/sales-v53/customers/", json=customer_data)
            assert response.status_code == 201
            customers.append(response.json())
        
        # Test basic listing
        response = client.get("/api/v1/sales-v53/customers/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        
        # Test filtering by customer type
        response = client.get("/api/v1/sales-v53/customers/?customer_type=business")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # Customers 1 and 3
        
        # Test pagination
        response = client.get("/api/v1/sales-v53/customers/?page=1&size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["pages"] == 2
    
    def test_get_customer_not_found(self, client: TestClient):
        """Test getting non-existent customer"""
        response = client.get("/api/v1/sales-v53/customers/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_customer_with_relationship_data(self, client: TestClient, sample_customer_data):
        """Test getting customer with calculated relationship metrics"""
        # Create customer
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        assert response.status_code == 201
        customer = response.json()
        customer_id = customer["id"]
        
        # Get customer details
        response = client.get(f"/api/v1/sales-v53/customers/{customer_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == customer_id
        assert data["total_orders"] == 0  # No orders yet
        assert data["total_spent"] == "0"
        assert data["current_balance"] == "0"
    
    # Sales Order Management Tests
    
    def test_create_sales_order_basic(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test basic sales order creation"""
        # First create a customer
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        assert response.status_code == 201
        customer = response.json()
        
        # Create order
        order_data = sample_order_data.copy()
        order_data["customer_id"] = customer["id"]
        
        response = client.post("/api/v1/sales-v53/orders/", json=order_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["customer_id"] == customer["id"]
        assert data["customer_name"] == customer["name"]
        assert data["order_type"] == "sales"
        assert "order_number" in data
        assert data["status"] == "draft"
        assert data["payment_status"] == "pending"
        assert len(data["line_items"]) == 1
        assert data["line_items_count"] == 1
        assert float(data["subtotal"]) > 0
        assert float(data["total_amount"]) > 0
        assert data["paid_amount"] == "0"
        assert float(data["balance_due"]) == float(data["total_amount"])
    
    def test_create_sales_order_customer_not_found(self, client: TestClient, sample_order_data):
        """Test sales order creation with invalid customer"""
        order_data = sample_order_data.copy()
        order_data["customer_id"] = "non-existent-customer"
        
        response = client.post("/api/v1/sales-v53/orders/", json=order_data)
        assert response.status_code == 400
        assert "Customer not found" in response.json()["detail"]
    
    def test_create_sales_order_line_item_calculations(self, client: TestClient, sample_customer_data):
        """Test sales order line item calculations"""
        # Create customer
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        # Create order with specific line items for calculation testing
        order_data = {
            "customer_id": customer["id"],
            "line_items": [
                {
                    "product_id": "prod-1",
                    "quantity": "2.0",
                    "unit_price": "100.00",
                    "discount_percent": "10.0",
                    "tax_rate": "8.0"
                }
            ]
        }
        
        response = client.post("/api/v1/sales-v53/orders/", json=order_data)
        assert response.status_code == 201
        
        data = response.json()
        line_item = data["line_items"][0]
        
        # Verify calculations
        # 2 * 100 = 200 (before discount)
        # 200 * 10% = 20 (discount)
        # 200 - 20 = 180 (line total)
        # 180 * 8% = 14.40 (tax)
        # 180 + 14.40 = 194.40 (net total)
        
        assert float(line_item["line_total"]) == 180.0
        assert float(line_item["line_tax"]) == 14.4
        assert float(line_item["line_net_total"]) == 194.4
        assert float(line_item["discount_amount"]) == 20.0
    
    def test_list_sales_orders_empty(self, client: TestClient):
        """Test listing sales orders when none exist"""
        response = client.get("/api/v1/sales-v53/orders/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
    
    def test_list_sales_orders_with_filtering(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test listing sales orders with comprehensive filtering"""
        # Create customer
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        # Create multiple orders
        orders = []
        for i in range(3):
            order_data = sample_order_data.copy()
            order_data["customer_id"] = customer["id"]
            order_data["order_type"] = "sales" if i % 2 == 0 else "return"
            response = client.post("/api/v1/sales-v53/orders/", json=order_data)
            assert response.status_code == 201
            orders.append(response.json())
        
        # Test basic listing
        response = client.get("/api/v1/sales-v53/orders/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Test filtering by customer
        response = client.get(f"/api/v1/sales-v53/orders/?customer_id={customer['id']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Test filtering by order type
        response = client.get("/api/v1/sales-v53/orders/?order_type=sales")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # Orders 1 and 3
        
        # Test filtering by status
        response = client.get("/api/v1/sales-v53/orders/?status=draft")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3  # All orders are draft
    
    def test_get_sales_order_not_found(self, client: TestClient):
        """Test getting non-existent sales order"""
        response = client.get("/api/v1/sales-v53/orders/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_sales_order(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test updating sales order"""
        # Create customer and order
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        order_data = sample_order_data.copy()
        order_data["customer_id"] = customer["id"]
        response = client.post("/api/v1/sales-v53/orders/", json=order_data)
        order = response.json()
        
        # Update order
        update_data = {
            "status": "confirmed",
            "priority": "urgent",
            "notes": "Updated notes for the order"
        }
        
        response = client.put(f"/api/v1/sales-v53/orders/{order['id']}", json=update_data)
        assert response.status_code == 200
        
        updated_order = response.json()
        assert updated_order["status"] == "confirmed"
        assert updated_order["priority"] == "urgent"
        assert updated_order["notes"] == "Updated notes for the order"
        assert updated_order["updated_at"] != order["updated_at"]
    
    # Payment Management Tests
    
    def test_create_payment_basic(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test basic payment creation"""
        # Create customer and order
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        order_data = sample_order_data.copy()
        order_data["customer_id"] = customer["id"]
        response = client.post("/api/v1/sales-v53/orders/", json=order_data)
        order = response.json()
        
        # Create payment
        payment_data = {
            "order_id": order["id"],
            "amount": "500.00",
            "payment_method": "credit_card",
            "reference": "CC-PAYMENT-12345",
            "notes": "Payment via Visa ending in 1234"
        }
        
        response = client.post("/api/v1/sales-v53/payments/", json=payment_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["order_id"] == order["id"]
        assert data["order_number"] == order["order_number"]
        assert float(data["amount"]) == 500.0
        assert data["payment_method"] == "credit_card"
        assert data["reference"] == "CC-PAYMENT-12345"
        assert data["status"] == "completed"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_payment_order_not_found(self, client: TestClient):
        """Test payment creation with invalid order"""
        payment_data = {
            "order_id": "non-existent-order",
            "amount": "100.00",
            "payment_method": "cash"
        }
        
        response = client.post("/api/v1/sales-v53/payments/", json=payment_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]
    
    def test_create_payment_exceeds_balance(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test payment creation that exceeds order balance"""
        # Create customer and order
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        order_data = sample_order_data.copy()
        order_data["customer_id"] = customer["id"]
        response = client.post("/api/v1/sales-v53/orders/", json=order_data)
        order = response.json()
        
        # Try to pay more than the balance
        excessive_amount = float(order["balance_due"]) + 1000.0
        payment_data = {
            "order_id": order["id"],
            "amount": f"{excessive_amount:.2f}",  # Format to 2 decimal places
            "payment_method": "cash"
        }
        
        response = client.post("/api/v1/sales-v53/payments/", json=payment_data)
        assert response.status_code == 400
        assert "exceeds balance due" in response.json()["detail"]
    
    def test_payment_updates_order_status(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test that payment updates order payment status"""
        # Create customer and order
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        order_data = sample_order_data.copy()
        order_data["customer_id"] = customer["id"]
        response = client.post("/api/v1/sales-v53/orders/", json=order_data)
        order = response.json()
        
        # Make partial payment
        partial_amount = float(order["balance_due"]) / 2
        payment_data = {
            "order_id": order["id"],
            "amount": f"{partial_amount:.2f}",  # Format to 2 decimal places
            "payment_method": "credit_card"
        }
        
        response = client.post("/api/v1/sales-v53/payments/", json=payment_data)
        assert response.status_code == 201
        
        # Check order status
        response = client.get(f"/api/v1/sales-v53/orders/{order['id']}")
        updated_order = response.json()
        assert updated_order["payment_status"] == "partial"
        assert abs(float(updated_order["paid_amount"]) - partial_amount) < 0.01  # Allow for rounding
        assert abs(float(updated_order["balance_due"]) - partial_amount) < 0.01  # Allow for rounding
        
        # Make second payment to complete the balance
        remaining_payment_data = {
            "order_id": order["id"],
            "amount": f"{partial_amount:.2f}",  # Pay the remaining amount
            "payment_method": "credit_card"
        }
        response = client.post("/api/v1/sales-v53/payments/", json=remaining_payment_data)
        assert response.status_code == 201
        
        # Check order is fully paid
        response = client.get(f"/api/v1/sales-v53/orders/{order['id']}")
        updated_order = response.json()
        assert updated_order["payment_status"] == "paid"
        assert abs(float(updated_order["balance_due"])) < 0.01  # Allow for rounding
    
    def test_list_payments(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test listing payments with filtering"""
        # Create customer and order
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        order_data = sample_order_data.copy()
        order_data["customer_id"] = customer["id"]
        response = client.post("/api/v1/sales-v53/orders/", json=order_data)
        order = response.json()
        
        # Create multiple payments
        payment_methods = ["cash", "credit_card", "bank_transfer"]
        for i, method in enumerate(payment_methods):
            payment_data = {
                "order_id": order["id"],
                "amount": "100.00",
                "payment_method": method,
                "reference": f"PAY-{i+1}"
            }
            response = client.post("/api/v1/sales-v53/payments/", json=payment_data)
            assert response.status_code == 201
        
        # Test basic listing
        response = client.get("/api/v1/sales-v53/payments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Test filtering by order
        response = client.get(f"/api/v1/sales-v53/payments/?order_id={order['id']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Test filtering by payment method
        response = client.get("/api/v1/sales-v53/payments/?payment_method=credit_card")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["payment_method"] == "credit_card"
    
    # Quote Management Tests
    
    def test_create_quote_basic(self, client: TestClient, sample_customer_data, sample_order_line_item):
        """Test basic quote creation"""
        # Create customer
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        # Create quote
        quote_data = {
            "customer_id": customer["id"],
            "line_items": [sample_order_line_item],
            "notes": "Initial quote for customer requirements",
            "terms_conditions": "Quote valid for 30 days from issue date"
        }
        
        response = client.post("/api/v1/sales-v53/quotes/", json=quote_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["customer_id"] == customer["id"]
        assert data["customer_name"] == customer["name"]
        assert "quote_number" in data
        assert data["status"] == "active"
        assert data["is_expired"] is False
        assert data["is_converted"] is False
        assert len(data["line_items"]) == 1
        assert data["line_items_count"] == 1
        assert float(data["total_amount"]) > 0
    
    def test_create_quote_customer_not_found(self, client: TestClient, sample_order_line_item):
        """Test quote creation with invalid customer"""
        quote_data = {
            "customer_id": "non-existent-customer",
            "line_items": [sample_order_line_item]
        }
        
        response = client.post("/api/v1/sales-v53/quotes/", json=quote_data)
        assert response.status_code == 400
        assert "Customer not found" in response.json()["detail"]
    
    def test_list_quotes(self, client: TestClient, sample_customer_data, sample_order_line_item):
        """Test listing quotes with filtering"""
        # Create customer
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        # Create multiple quotes
        for i in range(3):
            quote_data = {
                "customer_id": customer["id"],
                "line_items": [sample_order_line_item],
                "notes": f"Quote {i+1}"
            }
            response = client.post("/api/v1/sales-v53/quotes/", json=quote_data)
            assert response.status_code == 201
        
        # Test basic listing
        response = client.get("/api/v1/sales-v53/quotes/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Test filtering by customer
        response = client.get(f"/api/v1/sales-v53/quotes/?customer_id={customer['id']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Test filtering by status
        response = client.get("/api/v1/sales-v53/quotes/?status=active")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
    
    def test_convert_quote_to_order(self, client: TestClient, sample_customer_data, sample_order_line_item):
        """Test converting quote to sales order"""
        # Create customer
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        # Create quote
        quote_data = {
            "customer_id": customer["id"],
            "line_items": [sample_order_line_item],
            "notes": "Quote to be converted"
        }
        response = client.post("/api/v1/sales-v53/quotes/", json=quote_data)
        quote = response.json()
        
        # Convert quote to order
        response = client.post(f"/api/v1/sales-v53/quotes/{quote['id']}/convert")
        assert response.status_code == 200
        
        order = response.json()
        assert order["customer_id"] == customer["id"]
        assert "Converted from quote" in order["notes"]
        assert len(order["line_items"]) == 1
        
        # Check quote is marked as converted
        response = client.get(f"/api/v1/sales-v53/quotes/{quote['id']}")
        updated_quote = response.json()
        assert updated_quote["is_converted"] is True
        assert updated_quote["converted_order_id"] == order["id"]
        assert updated_quote["status"] == "converted"
    
    def test_convert_quote_not_found(self, client: TestClient):
        """Test converting non-existent quote"""
        response = client.post("/api/v1/sales-v53/quotes/non-existent-id/convert")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_convert_quote_already_converted(self, client: TestClient, sample_customer_data, sample_order_line_item):
        """Test converting already converted quote"""
        # Create customer and quote
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        quote_data = {
            "customer_id": customer["id"],
            "line_items": [sample_order_line_item]
        }
        response = client.post("/api/v1/sales-v53/quotes/", json=quote_data)
        quote = response.json()
        
        # Convert quote first time
        response = client.post(f"/api/v1/sales-v53/quotes/{quote['id']}/convert")
        assert response.status_code == 200
        
        # Try to convert again
        response = client.post(f"/api/v1/sales-v53/quotes/{quote['id']}/convert")
        assert response.status_code == 400
        assert "already converted" in response.json()["detail"]
    
    # Statistics and Analytics Tests
    
    def test_get_sales_statistics_empty(self, client: TestClient):
        """Test sales statistics when no data exists"""
        response = client.get("/api/v1/sales-v53/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_orders"] == 0
        assert data["total_customers"] == 0
        assert float(data["total_sales_amount"]) == 0.0
        assert float(data["total_payments_received"]) == 0.0
        assert data["calculation_time_ms"] < 200  # Performance requirement
    
    def test_get_sales_statistics_with_data(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test sales statistics with comprehensive data"""
        # Create customers
        customers = []
        for i in range(3):
            customer_data = sample_customer_data.copy()
            customer_data["name"] = f"Customer {i+1}"
            customer_data["email"] = f"customer{i+1}@test.com"
            response = client.post("/api/v1/sales-v53/customers/", json=customer_data)
            customers.append(response.json())
        
        # Create orders
        orders = []
        for i, customer in enumerate(customers):
            order_data = sample_order_data.copy()
            order_data["customer_id"] = customer["id"]
            order_data["status"] = ["draft", "confirmed", "completed"][i % 3]
            response = client.post("/api/v1/sales-v53/orders/", json=order_data)
            orders.append(response.json())
        
        # Create payments
        for order in orders:
            payment_data = {
                "order_id": order["id"],
                "amount": "100.00",
                "payment_method": "credit_card"
            }
            response = client.post("/api/v1/sales-v53/payments/", json=payment_data)
            assert response.status_code == 201
        
        # Get statistics
        response = client.get("/api/v1/sales-v53/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_orders"] == 3
        assert data["total_customers"] == 3
        assert data["active_customers"] == 3
        assert float(data["total_sales_amount"]) > 0
        assert float(data["total_payments_received"]) == 300.0  # 3 payments of 100 each
        assert data["calculation_time_ms"] < 200  # Performance requirement
        
        # Check order status breakdown
        assert "orders_by_status" in data
        assert "payment_methods_breakdown" in data
    
    # Bulk Operations Tests
    
    def test_bulk_create_orders_validation_only(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test bulk order creation with validation only"""
        # Create customer
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        # Prepare bulk orders
        order_data = sample_order_data.copy()
        order_data["customer_id"] = customer["id"]
        
        bulk_data = {
            "orders": [order_data, order_data],
            "validate_only": True
        }
        
        response = client.post("/api/v1/sales-v53/orders/bulk", json=bulk_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["created_count"] == 2
        assert data["failed_count"] == 0
        assert len(data["created_items"]) == 0  # No actual creation in validation mode
        assert data["execution_time_ms"] is not None
    
    def test_bulk_create_orders_actual(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test actual bulk order creation"""
        # Create customer
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        # Prepare bulk orders
        order_data = sample_order_data.copy()
        order_data["customer_id"] = customer["id"]
        
        bulk_data = {
            "orders": [order_data, order_data],
            "validate_only": False
        }
        
        response = client.post("/api/v1/sales-v53/orders/bulk", json=bulk_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["created_count"] == 2
        assert data["failed_count"] == 0
        assert len(data["created_items"]) == 2
        assert all("id" in item for item in data["created_items"])
    
    def test_bulk_create_orders_with_errors(self, client: TestClient, sample_order_data):
        """Test bulk order creation with mixed success/failure"""
        # Create one valid customer
        customer_data = {"name": "Valid Customer"}
        response = client.post("/api/v1/sales-v53/customers/", json=customer_data)
        valid_customer = response.json()
        
        # Prepare mixed bulk orders (valid and invalid)
        valid_order = sample_order_data.copy()
        valid_order["customer_id"] = valid_customer["id"]
        
        invalid_order = sample_order_data.copy()
        invalid_order["customer_id"] = "non-existent-customer"
        
        bulk_data = {
            "orders": [valid_order, invalid_order],
            "validate_only": False,
            "stop_on_error": False
        }
        
        response = client.post("/api/v1/sales-v53/orders/bulk", json=bulk_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["created_count"] == 1
        assert data["failed_count"] == 1
        assert len(data["created_items"]) == 1
        assert len(data["failed_items"]) == 1
        assert "error" in data["failed_items"][0]
    
    # Performance Tests
    
    def test_create_customer_performance(self, client: TestClient, sample_customer_data):
        """Test customer creation performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        end_time = time.time()
        
        assert response.status_code == 201
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Customer creation took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    def test_create_order_performance(self, client: TestClient, sample_customer_data, sample_order_data):
        """Test order creation performance (<200ms)"""
        import time
        
        # Create customer first
        response = client.post("/api/v1/sales-v53/customers/", json=sample_customer_data)
        customer = response.json()
        
        order_data = sample_order_data.copy()
        order_data["customer_id"] = customer["id"]
        
        start_time = time.time()
        response = client.post("/api/v1/sales-v53/orders/", json=order_data)
        end_time = time.time()
        
        assert response.status_code == 201
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Order creation took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    def test_statistics_performance(self, client: TestClient):
        """Test statistics calculation performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/sales-v53/statistics")
        end_time = time.time()
        
        assert response.status_code == 200
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Statistics calculation took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    # Health Check Test
    
    def test_sales_health_check(self, client: TestClient):
        """Test sales API health check endpoint"""
        response = client.get("/api/v1/sales-v53/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "Sales Management API v53.0" in data["service"]
        assert "customers_count" in data
        assert "orders_count" in data
        assert "payments_count" in data
        assert "quotes_count" in data
        assert "timestamp" in data