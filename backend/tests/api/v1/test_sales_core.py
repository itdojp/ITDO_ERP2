"""
TDD Tests for Core Sales API - CC02 v50.0 Phase 3
12-Hour Core Business API Sprint - Sales Process Management
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import uuid
import json
from datetime import datetime, timedelta


class TestCoreSalesAPI:
    """Test suite for Core Sales API - TDD Implementation Phase 3"""

    def test_create_customer_quote(self, api_client: TestClient):
        """Test sales quote creation"""
        # Create customer and product first
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Quote Customer", "email": "quote@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Quote Product", "sku": "QUOTE-001", "price": 299.99
        })
        product_id = product_response.json()["id"]
        
        quote_data = {
            "customer_id": customer_id,
            "quote_number": "Q-2025-001",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 5,
                    "unit_price": 299.99,
                    "discount_percentage": 10.0
                }
            ],
            "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
            "notes": "Special pricing for bulk order"
        }
        response = api_client.post("/api/v1/sales/quotes", json=quote_data)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == customer_id
        assert data["quote_number"] == "Q-2025-001"
        assert len(data["items"]) == 1
        assert abs(data["total_amount"] - 1349.95) < 0.01  # 5 * 299.99 * 0.9 (10% discount)
        assert "id" in data
        assert "created_at" in data

    def test_convert_quote_to_order(self, api_client: TestClient):
        """Test converting quote to sales order"""
        # Create customer, product, and quote
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Convert Customer", "email": "convert@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Convert Product", "sku": "CONVERT-001", "price": 199.99
        })
        product_id = product_response.json()["id"]
        
        quote_response = api_client.post("/api/v1/sales/quotes", json={
            "customer_id": customer_id,
            "quote_number": "Q-CONVERT-001",
            "items": [{"product_id": product_id, "quantity": 3, "unit_price": 199.99}]
        })
        quote_id = quote_response.json()["id"]
        
        # Convert to order
        convert_data = {
            "order_number": "SO-2025-001",
            "notes": "Converted from quote"
        }
        response = api_client.post(f"/api/v1/sales/quotes/{quote_id}/convert", json=convert_data)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == customer_id
        assert data["order_number"] == "SO-2025-001"
        assert data["quote_id"] == quote_id  # Reference to original quote
        assert data["status"] == "confirmed"

    def test_create_sales_order_direct(self, api_client: TestClient):
        """Test direct sales order creation"""
        # Create customer and product
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Direct Order Customer", "email": "direct@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Direct Product", "sku": "DIRECT-001", "price": 149.99
        })
        product_id = product_response.json()["id"]
        
        order_data = {
            "customer_id": customer_id,
            "order_number": "SO-DIRECT-001",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "unit_price": 149.99,
                    "discount_percentage": 5.0
                }
            ],
            "shipping_address": "123 Direct St, Order City",
            "payment_terms": "net_30",
            "notes": "Rush order"
        }
        response = api_client.post("/api/v1/sales/orders", json=order_data)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == customer_id
        assert data["order_number"] == "SO-DIRECT-001"
        assert abs(data["total_amount"] - 284.98) < 0.01  # 2 * 149.99 * 0.95
        assert data["status"] == "confirmed"

    def test_update_order_status(self, api_client: TestClient):
        """Test updating sales order status"""
        # Create customer, product, and order
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Status Customer", "email": "status@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Status Product", "sku": "STATUS-001", "price": 99.99
        })
        product_id = product_response.json()["id"]
        
        order_response = api_client.post("/api/v1/sales/orders", json={
            "customer_id": customer_id,
            "order_number": "SO-STATUS-001",
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 99.99}]
        })
        order_id = order_response.json()["id"]
        
        # Update status to shipped
        status_data = {
            "status": "shipped",
            "tracking_number": "TRACK123456",
            "notes": "Shipped via express delivery"
        }
        response = api_client.put(f"/api/v1/sales/orders/{order_id}/status", json=status_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "shipped"
        assert data["tracking_number"] == "TRACK123456"

    def test_generate_invoice(self, api_client: TestClient):
        """Test invoice generation from sales order"""
        # Create customer, product, and order
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Invoice Customer", "email": "invoice@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Invoice Product", "sku": "INVOICE-001", "price": 499.99
        })
        product_id = product_response.json()["id"]
        
        order_response = api_client.post("/api/v1/sales/orders", json={
            "customer_id": customer_id,
            "order_number": "SO-INVOICE-001",
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 499.99}]
        })
        order_id = order_response.json()["id"]
        
        # Generate invoice
        invoice_data = {
            "invoice_number": "INV-2025-001",
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "tax_rate": 8.5,
            "notes": "Payment terms: Net 30 days"
        }
        response = api_client.post(f"/api/v1/sales/orders/{order_id}/invoice", json=invoice_data)
        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] == order_id
        assert data["invoice_number"] == "INV-2025-001"
        assert data["subtotal"] == 499.99
        assert data["tax_amount"] == 42.50  # 8.5% of 499.99
        assert data["total_amount"] == 542.49

    def test_record_payment(self, api_client: TestClient):
        """Test recording payment against invoice"""
        # Create full sales flow: customer -> product -> order -> invoice
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Payment Customer", "email": "payment@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Payment Product", "sku": "PAYMENT-001", "price": 299.99
        })
        product_id = product_response.json()["id"]
        
        order_response = api_client.post("/api/v1/sales/orders", json={
            "customer_id": customer_id,
            "order_number": "SO-PAYMENT-001",
            "items": [{"product_id": product_id, "quantity": 2, "unit_price": 299.99}]
        })
        order_id = order_response.json()["id"]
        
        invoice_response = api_client.post(f"/api/v1/sales/orders/{order_id}/invoice", json={
            "invoice_number": "INV-PAYMENT-001",
            "tax_rate": 10.0
        })
        invoice_id = invoice_response.json()["id"]
        
        # Record payment
        payment_data = {
            "amount": 659.98,  # Full amount
            "payment_method": "credit_card",
            "payment_reference": "CC123456789",
            "payment_date": datetime.now().isoformat(),
            "notes": "Paid in full via credit card"
        }
        response = api_client.post(f"/api/v1/sales/invoices/{invoice_id}/payments", json=payment_data)
        assert response.status_code == 201
        data = response.json()
        assert data["invoice_id"] == invoice_id
        assert data["amount"] == 659.98
        assert data["payment_method"] == "credit_card"
        assert data["status"] == "completed"

    def test_partial_payment_tracking(self, api_client: TestClient):
        """Test partial payment tracking"""
        # Create invoice setup
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Partial Customer", "email": "partial@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Partial Product", "sku": "PARTIAL-001", "price": 1000.00
        })
        product_id = product_response.json()["id"]
        
        order_response = api_client.post("/api/v1/sales/orders", json={
            "customer_id": customer_id,
            "order_number": "SO-PARTIAL-001",
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 1000.00}]
        })
        order_id = order_response.json()["id"]
        
        invoice_response = api_client.post(f"/api/v1/sales/orders/{order_id}/invoice", json={
            "invoice_number": "INV-PARTIAL-001",
            "tax_rate": 0.0
        })
        invoice_id = invoice_response.json()["id"]
        
        # Record first partial payment
        api_client.post(f"/api/v1/sales/invoices/{invoice_id}/payments", json={
            "amount": 400.00,
            "payment_method": "bank_transfer",
            "payment_reference": "BT001"
        })
        
        # Record second partial payment
        api_client.post(f"/api/v1/sales/invoices/{invoice_id}/payments", json={
            "amount": 600.00,
            "payment_method": "check",
            "payment_reference": "CHK002"
        })
        
        # Check invoice payment status
        response = api_client.get(f"/api/v1/sales/invoices/{invoice_id}/payments")
        assert response.status_code == 200
        data = response.json()
        assert len(data["payments"]) == 2
        assert data["total_paid"] == 1000.00
        assert data["remaining_balance"] == 0.00
        assert data["payment_status"] == "paid"

    def test_sales_pipeline_tracking(self, api_client: TestClient):
        """Test sales pipeline and opportunity tracking"""
        # Create customer
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Pipeline Customer", "email": "pipeline@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        # Create sales opportunity
        opportunity_data = {
            "customer_id": customer_id,
            "title": "Enterprise Software Deal",
            "description": "Large enterprise software implementation",
            "estimated_value": 50000.00,
            "probability": 75,
            "stage": "proposal",
            "expected_close_date": (datetime.now() + timedelta(days=45)).isoformat(),
            "assigned_to": "sales_rep_001"
        }
        response = api_client.post("/api/v1/sales/opportunities", json=opportunity_data)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == customer_id
        assert data["estimated_value"] == 50000.00
        assert data["probability"] == 75
        assert data["stage"] == "proposal"

    def test_update_opportunity_stage(self, api_client: TestClient):
        """Test updating opportunity stage in sales pipeline"""
        # Create opportunity
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Stage Customer", "email": "stage@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        opportunity_response = api_client.post("/api/v1/sales/opportunities", json={
            "customer_id": customer_id,
            "title": "Stage Test Deal",
            "estimated_value": 25000.00,
            "probability": 50,
            "stage": "qualification"
        })
        opportunity_id = opportunity_response.json()["id"]
        
        # Update to next stage
        stage_data = {
            "stage": "negotiation",
            "probability": 80,
            "notes": "Customer interested, negotiating terms"
        }
        response = api_client.put(f"/api/v1/sales/opportunities/{opportunity_id}/stage", json=stage_data)
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "negotiation"
        assert data["probability"] == 80

    def test_sales_reporting_metrics(self, api_client: TestClient):
        """Test sales reporting and metrics"""
        # Create sample sales data
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Metrics Customer", "email": "metrics@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Metrics Product", "sku": "METRICS-001", "price": 199.99
        })
        product_id = product_response.json()["id"]
        
        # Create multiple orders for metrics
        for i in range(3):
            api_client.post("/api/v1/sales/orders", json={
                "customer_id": customer_id,
                "order_number": f"SO-METRICS-{i+1:03d}",
                "items": [{"product_id": product_id, "quantity": i+1, "unit_price": 199.99}]
            })
        
        # Create opportunities for pipeline metrics
        for i in range(2):
            api_client.post("/api/v1/sales/opportunities", json={
                "customer_id": customer_id,
                "title": f"Metrics Opportunity {i+1}",
                "estimated_value": (i+1) * 10000.00,
                "probability": 60,
                "stage": "proposal"
            })
        
        # Get sales metrics
        response = api_client.get("/api/v1/sales/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "total_revenue" in data
        assert "total_opportunities" in data
        assert "pipeline_value" in data
        assert "average_order_value" in data
        assert data["total_orders"] >= 3
        assert data["total_opportunities"] >= 2

    def test_list_quotes_with_filtering(self, api_client: TestClient):
        """Test listing quotes with filtering and search"""
        # Create customer and product
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Filter Customer", "email": "filter@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Filter Product", "sku": "FILTER-001", "price": 299.99
        })
        product_id = product_response.json()["id"]
        
        # Create quotes with different statuses
        quote_statuses = ["draft", "sent", "accepted", "expired"]
        for i, status in enumerate(quote_statuses):
            api_client.post("/api/v1/sales/quotes", json={
                "customer_id": customer_id,
                "quote_number": f"Q-FILTER-{i+1:03d}",
                "items": [{"product_id": product_id, "quantity": 1, "unit_price": 299.99}],
                "status": status
            })
        
        # List all quotes
        response = api_client.get("/api/v1/sales/quotes")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 4
        
        # Filter by status
        response = api_client.get("/api/v1/sales/quotes?status=sent")
        assert response.status_code == 200
        data = response.json()
        sent_quotes = [q for q in data["items"] if q["status"] == "sent"]
        assert len(sent_quotes) >= 1

    def test_sales_api_performance(self, api_client: TestClient):
        """Test sales API performance requirements"""
        import time
        
        # Create test data
        customer_response = api_client.post("/api/v1/customers", json={
            "name": "Performance Sales Customer", "email": "perfsales@test.com"
        })
        customer_id = customer_response.json()["id"]
        
        product_response = api_client.post("/api/v1/products", json={
            "name": "Performance Sales Product", "sku": "PERF-SALES-001", "price": 199.99
        })
        product_id = product_response.json()["id"]
        
        quote_data = {
            "customer_id": customer_id,
            "quote_number": "Q-PERF-001",
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 199.99}]
        }
        
        # Measure quote creation time
        start_time = time.time()
        response = api_client.post("/api/v1/sales/quotes", json=quote_data)
        end_time = time.time()
        
        creation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 201
        assert creation_time < 100, f"Quote creation took {creation_time}ms, exceeds 100ms limit"
        
        quote_id = response.json()["id"]
        
        # Measure quote retrieval time
        start_time = time.time()
        response = api_client.get(f"/api/v1/sales/quotes/{quote_id}")
        end_time = time.time()
        
        retrieval_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert retrieval_time < 50, f"Quote retrieval took {retrieval_time}ms, exceeds 50ms limit"