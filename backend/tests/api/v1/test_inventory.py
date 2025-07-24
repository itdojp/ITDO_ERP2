"""
TDD Tests for Inventory API Endpoints - CC02 v49.0 Implementation Overdrive
48-Hour Backend Blitz - Phase 2: Inventory Management
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import uuid
from datetime import datetime


class TestInventoryAPI:
    """Test suite for Inventory API endpoints - TDD Implementation Phase 2"""

    def test_create_inventory_item(self, api_client: TestClient):
        """Test inventory item creation endpoint"""
        # First create a product
        product_data = {"name": "Inventory Test Product", "price": 100, "sku": "INV001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        inventory_data = {
            "product_id": product_id,
            "location": "Warehouse A",
            "quantity": 100,
            "minimum_stock": 10,
            "maximum_stock": 500
        }
        response = api_client.post("/api/v1/inventory", json=inventory_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == product_id
        assert data["location"] == "Warehouse A"
        assert data["quantity"] == 100
        assert "id" in data
        assert "created_at" in data

    def test_get_inventory_by_product(self, api_client: TestClient):
        """Test retrieving inventory by product ID"""
        # Create product and inventory
        product_data = {"name": "Inventory Get Test", "price": 150, "sku": "GETINV001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        inventory_data = {
            "product_id": product_id,
            "location": "Store B",
            "quantity": 75,
            "minimum_stock": 5
        }
        api_client.post("/api/v1/inventory", json=inventory_data)
        
        response = api_client.get(f"/api/v1/inventory/product/{product_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["items"][0]["product_id"] == product_id

    def test_update_inventory_quantity(self, api_client: TestClient):
        """Test updating inventory quantity"""
        # Create product and inventory
        product_data = {"name": "Update Inventory Test", "price": 200, "sku": "UPDINV001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        inventory_data = {
            "product_id": product_id,
            "location": "Warehouse C",
            "quantity": 50
        }
        inv_response = api_client.post("/api/v1/inventory", json=inventory_data)
        inventory_id = inv_response.json()["id"]
        
        update_data = {"quantity": 75}
        response = api_client.put(f"/api/v1/inventory/{inventory_id}", json=update_data)
        
        assert response.status_code == 200
        assert response.json()["quantity"] == 75

    def test_stock_movement_creation(self, api_client: TestClient):
        """Test creating stock movements"""
        # Create product and inventory
        product_data = {"name": "Movement Test", "price": 100, "sku": "MOVTEST001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        movement_data = {
            "product_id": product_id,
            "location": "Warehouse D",
            "movement_type": "in",
            "quantity": 25,
            "reason": "Stock replenishment",
            "reference": "PO-2024-001"
        }
        response = api_client.post("/api/v1/inventory/movements", json=movement_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == product_id
        assert data["movement_type"] == "in"
        assert data["quantity"] == 25

    def test_low_stock_alerts(self, api_client: TestClient):
        """Test low stock alert functionality"""
        # Create product with low stock
        product_data = {"name": "Low Stock Test", "price": 50, "sku": "LOWSTOCK001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        inventory_data = {
            "product_id": product_id,
            "location": "Store E",
            "quantity": 3,
            "minimum_stock": 10
        }
        api_client.post("/api/v1/inventory", json=inventory_data)
        
        response = api_client.get("/api/v1/inventory/alerts/low-stock")
        assert response.status_code == 200
        data = response.json()
        assert len(data["alerts"]) >= 1

    def test_inventory_valuation(self, api_client: TestClient):
        """Test inventory valuation calculation"""
        # Create multiple inventory items
        products_and_inventory = [
            ({"name": "Val Test 1", "price": 100, "sku": "VAL001"}, {"quantity": 10, "location": "WH-A"}),
            ({"name": "Val Test 2", "price": 200, "sku": "VAL002"}, {"quantity": 5, "location": "WH-A"}),
        ]
        
        for product_data, inv_data in products_and_inventory:
            product_response = api_client.post("/api/v1/products", json=product_data)
            product_id = product_response.json()["id"]
            
            inventory_data = {
                "product_id": product_id,
                "location": inv_data["location"],
                "quantity": inv_data["quantity"]
            }
            api_client.post("/api/v1/inventory", json=inventory_data)
        
        response = api_client.get("/api/v1/inventory/valuation")
        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data
        assert "items_count" in data
        assert data["total_value"] >= 1500  # 10*100 + 5*200

    def test_inventory_transfer(self, api_client: TestClient):
        """Test inventory transfer between locations"""
        # Create product and inventory
        product_data = {"name": "Transfer Test", "price": 80, "sku": "TRANSFER001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        # Create initial inventory
        inventory_data = {
            "product_id": product_id,
            "location": "Warehouse F",
            "quantity": 50
        }
        api_client.post("/api/v1/inventory", json=inventory_data)
        
        transfer_data = {
            "product_id": product_id,
            "from_location": "Warehouse F",
            "to_location": "Store G",
            "quantity": 15,
            "reason": "Store replenishment"
        }
        response = api_client.post("/api/v1/inventory/transfer", json=transfer_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == product_id
        assert data["quantity"] == 15

    def test_inventory_locations_list(self, api_client: TestClient):
        """Test listing all inventory locations"""
        # Create some inventory items in different locations
        product_data = {"name": "Location Test", "price": 60, "sku": "LOC001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        locations = ["Warehouse H", "Store I", "Store J"]
        for location in locations:
            inventory_data = {
                "product_id": product_id,
                "location": location,
                "quantity": 20
            }
            api_client.post("/api/v1/inventory", json=inventory_data)
        
        response = api_client.get("/api/v1/inventory/locations")
        
        # Debug output
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        else:
            print(f"Response data: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["locations"]) >= 3

    def test_inventory_performance_metrics(self, api_client: TestClient):
        """Test inventory API performance requirements (<50ms)"""
        import time
        
        # Create test inventory
        product_data = {"name": "Performance Test Inv", "price": 100, "sku": "PERFINV001"}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        inventory_data = {
            "product_id": product_id,
            "location": "Performance Test Location",
            "quantity": 100
        }
        
        # Measure creation time
        start_time = time.time()
        response = api_client.post("/api/v1/inventory", json=inventory_data)
        end_time = time.time()
        
        creation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 201
        assert creation_time < 50, f"Inventory creation took {creation_time}ms, exceeds 50ms limit"
        
        inventory_id = response.json()["id"]
        
        # Measure retrieval time
        start_time = time.time()
        response = api_client.get(f"/api/v1/inventory/product/{product_id}")
        end_time = time.time()
        
        retrieval_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert retrieval_time < 50, f"Inventory retrieval took {retrieval_time}ms, exceeds 50ms limit"