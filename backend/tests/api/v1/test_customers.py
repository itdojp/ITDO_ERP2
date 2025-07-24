"""
TDD Tests for Customer Management API - CC02 v49.0 Phase 3
48-Hour Backend Blitz - Customer Management Implementation
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import uuid
from datetime import datetime


class TestCustomerAPI:
    """Test suite for Customer Management API - TDD Implementation Phase 3"""

    def test_create_customer(self, api_client: TestClient):
        """Test customer creation endpoint"""
        customer_data = {
            "name": "Test Customer Inc.",
            "email": "test@customer.com",
            "phone": "+1-555-0123",
            "address": "123 Business St, City, State 12345",
            "customer_type": "business",
            "status": "active"
        }
        response = api_client.post("/api/v1/customers", json=customer_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Customer Inc."
        assert data["email"] == "test@customer.com"
        assert data["customer_type"] == "business"
        assert "id" in data
        assert "created_at" in data

    def test_create_customer_validation_error(self, api_client: TestClient):
        """Test customer creation with validation errors"""
        # Missing required fields
        invalid_data = {"name": "Test"}  # Missing email
        response = api_client.post("/api/v1/customers", json=invalid_data)
        assert response.status_code == 422

    def test_create_customer_duplicate_email(self, api_client: TestClient):
        """Test customer creation with duplicate email"""
        customer_data = {
            "name": "First Customer",
            "email": "duplicate@test.com",
            "phone": "+1-555-0001"
        }
        
        # Create first customer
        response1 = api_client.post("/api/v1/customers", json=customer_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        duplicate_data = {
            "name": "Second Customer", 
            "email": "duplicate@test.com",
            "phone": "+1-555-0002"
        }
        response2 = api_client.post("/api/v1/customers", json=duplicate_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_get_customer_by_id(self, api_client: TestClient):
        """Test retrieving customer by ID"""
        # Create customer first
        customer_data = {
            "name": "Get Test Customer",
            "email": "get@test.com",
            "phone": "+1-555-0100"
        }
        create_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = create_response.json()["id"]
        
        # Get customer
        response = api_client.get(f"/api/v1/customers/{customer_id}")
        assert response.status_code == 200
        assert response.json()["id"] == customer_id
        assert response.json()["name"] == "Get Test Customer"

    def test_get_customer_not_found(self, api_client: TestClient):
        """Test retrieving non-existent customer"""
        fake_id = str(uuid.uuid4())
        response = api_client.get(f"/api/v1/customers/{fake_id}")
        assert response.status_code == 404

    def test_list_customers(self, api_client: TestClient):
        """Test listing customers with pagination"""
        # Create test customers
        customers = [
            {"name": "List Customer 1", "email": "list1@test.com", "phone": "+1-555-0201"},
            {"name": "List Customer 2", "email": "list2@test.com", "phone": "+1-555-0202"},
            {"name": "List Customer 3", "email": "list3@test.com", "phone": "+1-555-0203"},
        ]
        
        for customer in customers:
            api_client.post("/api/v1/customers", json=customer)
        
        # List customers
        response = api_client.get("/api/v1/customers")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3
        assert "total" in data
        assert "page" in data
        assert "size" in data

    def test_list_customers_with_search(self, api_client: TestClient):
        """Test customer search functionality"""
        # Create searchable customers
        customers = [
            {"name": "Microsoft Corporation", "email": "contact@microsoft.com", "phone": "+1-800-642-7676"},
            {"name": "Apple Inc.", "email": "support@apple.com", "phone": "+1-800-275-2273"},
            {"name": "Google LLC", "email": "support@google.com", "phone": "+1-650-253-0000"},
        ]
        
        for customer in customers:
            api_client.post("/api/v1/customers", json=customer)
        
        # Search by name
        response = api_client.get("/api/v1/customers?search=Microsoft")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert "Microsoft" in data["items"][0]["name"]

    def test_update_customer(self, api_client: TestClient):
        """Test updating customer information"""
        # Create customer
        customer_data = {
            "name": "Update Test Customer",
            "email": "update@test.com",
            "phone": "+1-555-0300"
        }
        create_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = create_response.json()["id"]
        
        # Update customer
        update_data = {
            "name": "Updated Customer Name",
            "phone": "+1-555-0301",
            "status": "inactive"
        }
        response = api_client.put(f"/api/v1/customers/{customer_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Customer Name"
        assert response.json()["phone"] == "+1-555-0301"
        assert response.json()["email"] == "update@test.com"  # Should remain unchanged

    def test_update_customer_not_found(self, api_client: TestClient):
        """Test updating non-existent customer"""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "Updated Name"}
        response = api_client.put(f"/api/v1/customers/{fake_id}", json=update_data)
        assert response.status_code == 404

    def test_delete_customer(self, api_client: TestClient):
        """Test deleting customer (soft delete)"""
        # Create customer
        customer_data = {
            "name": "Delete Test Customer",
            "email": "delete@test.com",
            "phone": "+1-555-0400"
        }
        create_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = create_response.json()["id"]
        
        # Delete customer
        response = api_client.delete(f"/api/v1/customers/{customer_id}")
        assert response.status_code == 200
        
        # Verify customer is soft deleted
        get_response = api_client.get(f"/api/v1/customers/{customer_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] == False

    def test_customer_contacts_management(self, api_client: TestClient):
        """Test customer contacts management"""
        # Create customer
        customer_data = {
            "name": "Contact Test Customer",
            "email": "contact@test.com",
            "phone": "+1-555-0500"
        }
        create_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = create_response.json()["id"]
        
        # Add contact
        contact_data = {
            "customer_id": customer_id,
            "name": "John Doe",
            "email": "john.doe@test.com",
            "phone": "+1-555-0501",
            "title": "Sales Manager",
            "is_primary": True
        }
        response = api_client.post(f"/api/v1/customers/{customer_id}/contacts", json=contact_data)
        assert response.status_code == 201
        assert response.json()["name"] == "John Doe"
        assert response.json()["is_primary"] == True

    def test_customer_orders_relationship(self, api_client: TestClient):
        """Test customer orders relationship"""
        # Create customer
        customer_data = {
            "name": "Orders Test Customer",
            "email": "orders@test.com",
            "phone": "+1-555-0600"
        }
        create_response = api_client.post("/api/v1/customers", json=customer_data)
        customer_id = create_response.json()["id"]
        
        # Get customer orders (should be empty initially)
        response = api_client.get(f"/api/v1/customers/{customer_id}/orders")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    def test_customer_statistics(self, api_client: TestClient):
        """Test customer statistics endpoint"""
        # Create diverse customers
        customers = [
            {"name": "Stats Customer 1", "email": "stats1@test.com", "customer_type": "business", "status": "active"},
            {"name": "Stats Customer 2", "email": "stats2@test.com", "customer_type": "individual", "status": "active"},
            {"name": "Stats Customer 3", "email": "stats3@test.com", "customer_type": "business", "status": "inactive"},
        ]
        
        for customer in customers:
            api_client.post("/api/v1/customers", json=customer)
        
        response = api_client.get("/api/v1/customers/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_customers" in data
        assert "active_customers" in data
        assert "customer_types" in data

    def test_customer_performance_metrics(self, api_client: TestClient):
        """Test customer API performance requirements (<50ms)"""
        import time
        
        # Create test customer
        customer_data = {
            "name": "Performance Test Customer",
            "email": "performance@test.com",
            "phone": "+1-555-0700"
        }
        
        # Measure creation time
        start_time = time.time()
        response = api_client.post("/api/v1/customers", json=customer_data)
        end_time = time.time()
        
        creation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 201
        assert creation_time < 50, f"Customer creation took {creation_time}ms, exceeds 50ms limit"
        
        customer_id = response.json()["id"]
        
        # Measure retrieval time
        start_time = time.time()
        response = api_client.get(f"/api/v1/customers/{customer_id}")
        end_time = time.time()
        
        retrieval_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert retrieval_time < 50, f"Customer retrieval took {retrieval_time}ms, exceeds 50ms limit"