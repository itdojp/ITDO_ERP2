"""
TDD Tests for Core Inventory API - CC02 v50.0 Phase 2
12-Hour Core Business API Sprint - Inventory Management
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import uuid
import json


class TestCoreInventoryAPI:
    """Test suite for Core Inventory API - TDD Implementation Phase 2"""

    def test_create_inventory_location(self, api_client: TestClient):
        """Test inventory location creation"""
        location_data = {
            "name": "Main Warehouse",
            "code": "MAIN-WH-001",
            "address": "123 Storage St, Business City",
            "location_type": "warehouse",
            "is_active": True
        }
        response = api_client.post("/api/v1/inventory/locations", json=location_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Main Warehouse"
        assert data["code"] == "MAIN-WH-001"
        assert data["location_type"] == "warehouse"
        assert "id" in data
        assert "created_at" in data

    def test_create_inventory_item(self, api_client: TestClient):
        """Test inventory item creation"""
        # First create a product and location
        product_data = {"name": "Inventory Test Product", "sku": "INV-PROD-001", "price": 99.99}
        product_response = api_client.post("/api/v1/products", json=product_data)
        product_id = product_response.json()["id"]
        
        location_data = {"name": "Test Location", "code": "TEST-LOC-001", "location_type": "warehouse"}
        location_response = api_client.post("/api/v1/inventory/locations", json=location_data)
        location_id = location_response.json()["id"]
        
        inventory_data = {
            "product_id": product_id,
            "location_id": location_id,
            "quantity": 100,
            "unit_cost": 50.00,
            "reorder_point": 10,
            "max_stock": 500
        }
        response = api_client.post("/api/v1/inventory/items", json=inventory_data)
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == product_id
        assert data["location_id"] == location_id
        assert data["quantity"] == 100
        assert data["unit_cost"] == 50.00
        assert data["reorder_point"] == 10

    def test_stock_adjustment(self, api_client: TestClient):
        """Test stock quantity adjustment"""
        # Create product, location, and inventory item
        product_response = api_client.post("/api/v1/products", json={
            "name": "Stock Adjustment Product", "sku": "STOCK-ADJ-001", "price": 149.99
        })
        product_id = product_response.json()["id"]
        
        location_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "Adjustment Location", "code": "ADJ-LOC-001", "location_type": "warehouse"
        })
        location_id = location_response.json()["id"]
        
        inventory_response = api_client.post("/api/v1/inventory/items", json={
            "product_id": product_id,
            "location_id": location_id,
            "quantity": 50,
            "unit_cost": 75.00
        })
        inventory_id = inventory_response.json()["id"]
        
        # Perform stock adjustment
        adjustment_data = {
            "quantity_change": 25,
            "adjustment_type": "manual",
            "reason": "Stock count correction",
            "cost_adjustment": 0.0
        }
        response = api_client.post(f"/api/v1/inventory/items/{inventory_id}/adjust", json=adjustment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 75  # 50 + 25
        assert data["adjustment_type"] == "manual"

    def test_stock_movement_creation(self, api_client: TestClient):
        """Test stock movement logging"""
        # Create basic inventory setup
        product_response = api_client.post("/api/v1/products", json={
            "name": "Movement Product", "sku": "MOVE-001", "price": 199.99
        })
        product_id = product_response.json()["id"]
        
        from_location_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "From Location", "code": "FROM-001", "location_type": "warehouse"
        })
        from_location_id = from_location_response.json()["id"]
        
        to_location_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "To Location", "code": "TO-001", "location_type": "store"
        })
        to_location_id = to_location_response.json()["id"]
        
        # Create inventory in from location
        api_client.post("/api/v1/inventory/items", json={
            "product_id": product_id,
            "location_id": from_location_id,
            "quantity": 100,
            "unit_cost": 99.50
        })
        
        # Create stock movement
        movement_data = {
            "product_id": product_id,
            "from_location_id": from_location_id,
            "to_location_id": to_location_id,
            "quantity": 20,
            "movement_type": "transfer",
            "reference": "Transfer-001",
            "notes": "Inter-location transfer"
        }
        response = api_client.post("/api/v1/inventory/movements", json=movement_data)
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == product_id
        assert data["from_location_id"] == from_location_id
        assert data["to_location_id"] == to_location_id
        assert data["quantity"] == 20
        assert data["movement_type"] == "transfer"

    def test_low_stock_alerts(self, api_client: TestClient):
        """Test low stock alert system"""
        # Create product and inventory with low stock
        product_response = api_client.post("/api/v1/products", json={
            "name": "Low Stock Product", "sku": "LOW-STOCK-001", "price": 99.99
        })
        product_id = product_response.json()["id"]
        
        location_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "Alert Location", "code": "ALERT-001", "location_type": "warehouse"
        })
        location_id = location_response.json()["id"]
        
        # Create inventory with quantity below reorder point
        api_client.post("/api/v1/inventory/items", json={
            "product_id": product_id,
            "location_id": location_id,
            "quantity": 5,  # Below reorder point
            "unit_cost": 50.00,
            "reorder_point": 20,
            "max_stock": 200
        })
        
        # Get low stock alerts
        response = api_client.get("/api/v1/inventory/alerts/low-stock")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        low_stock_item = next((item for item in data["items"] if item["product_id"] == product_id), None)
        assert low_stock_item is not None
        assert low_stock_item["current_quantity"] == 5
        assert low_stock_item["reorder_point"] == 20

    def test_inventory_valuation(self, api_client: TestClient):
        """Test inventory valuation calculation"""
        # Create multiple products and inventory items
        products_data = [
            {"name": "Valuation Product 1", "sku": "VAL-001", "price": 100.00},
            {"name": "Valuation Product 2", "sku": "VAL-002", "price": 200.00}
        ]
        
        location_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "Valuation Location", "code": "VAL-LOC-001", "location_type": "warehouse"
        })
        location_id = location_response.json()["id"]
        
        total_expected_value = 0
        for i, product_data in enumerate(products_data):
            product_response = api_client.post("/api/v1/products", json=product_data)
            product_id = product_response.json()["id"]
            
            quantity = (i + 1) * 10  # 10, 20
            unit_cost = (i + 1) * 50.0  # 50.0, 100.0
            
            api_client.post("/api/v1/inventory/items", json={
                "product_id": product_id,
                "location_id": location_id,
                "quantity": quantity,
                "unit_cost": unit_cost
            })
            
            total_expected_value += quantity * unit_cost
        
        # Get inventory valuation
        response = api_client.get("/api/v1/inventory/valuation")
        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data
        assert data["total_value"] >= total_expected_value

    def test_inventory_transfer_between_locations(self, api_client: TestClient):
        """Test inventory transfer between locations"""
        # Setup products and locations
        product_response = api_client.post("/api/v1/products", json={
            "name": "Transfer Product", "sku": "TRANSFER-001", "price": 150.00
        })
        product_id = product_response.json()["id"]
        
        warehouse_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "Main Warehouse", "code": "WAREHOUSE-001", "location_type": "warehouse"
        })
        warehouse_id = warehouse_response.json()["id"]
        
        store_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "Retail Store", "code": "STORE-001", "location_type": "store"
        })
        store_id = store_response.json()["id"]
        
        # Create initial inventory in warehouse
        api_client.post("/api/v1/inventory/items", json={
            "product_id": product_id,
            "location_id": warehouse_id,
            "quantity": 100,
            "unit_cost": 75.00
        })
        
        # Perform transfer
        transfer_data = {
            "product_id": product_id,
            "from_location_id": warehouse_id,
            "to_location_id": store_id,
            "quantity": 30,
            "notes": "Stock replenishment for store"
        }
        response = api_client.post("/api/v1/inventory/transfers", json=transfer_data)
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == product_id
        assert data["from_location_id"] == warehouse_id
        assert data["to_location_id"] == store_id
        assert data["quantity"] == 30
        assert data["status"] == "completed"

    def test_real_time_inventory_levels(self, api_client: TestClient):
        """Test real-time inventory level tracking"""
        # Create product and location
        product_response = api_client.post("/api/v1/products", json={
            "name": "Real Time Product", "sku": "REALTIME-001", "price": 99.99
        })
        product_id = product_response.json()["id"]
        
        location_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "Real Time Location", "code": "RT-001", "location_type": "warehouse"
        })
        location_id = location_response.json()["id"]
        
        # Create inventory
        inventory_response = api_client.post("/api/v1/inventory/items", json={
            "product_id": product_id,
            "location_id": location_id,
            "quantity": 50,
            "unit_cost": 45.00
        })
        inventory_id = inventory_response.json()["id"]
        
        # Check real-time levels
        response = api_client.get(f"/api/v1/inventory/real-time/{product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == product_id
        assert len(data["locations"]) >= 1
        location_stock = next((loc for loc in data["locations"] if loc["location_id"] == location_id), None)
        assert location_stock is not None
        assert location_stock["quantity"] == 50

    def test_inventory_history_tracking(self, api_client: TestClient):
        """Test inventory change history tracking"""
        # Create basic setup
        product_response = api_client.post("/api/v1/products", json={
            "name": "History Product", "sku": "HISTORY-001", "price": 199.99
        })
        product_id = product_response.json()["id"]
        
        location_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "History Location", "code": "HIST-001", "location_type": "warehouse"
        })
        location_id = location_response.json()["id"]
        
        # Create inventory and perform several adjustments
        inventory_response = api_client.post("/api/v1/inventory/items", json={
            "product_id": product_id,
            "location_id": location_id,
            "quantity": 100,
            "unit_cost": 80.00
        })
        inventory_id = inventory_response.json()["id"]
        
        # Perform multiple adjustments
        for i in range(3):
            api_client.post(f"/api/v1/inventory/items/{inventory_id}/adjust", json={
                "quantity_change": 10 * (i + 1),
                "adjustment_type": "manual",
                "reason": f"Adjustment {i + 1}"
            })
        
        # Get history
        response = api_client.get(f"/api/v1/inventory/items/{inventory_id}/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) >= 3  # At least 3 adjustments
        
    def test_list_inventory_locations(self, api_client: TestClient):
        """Test listing inventory locations with filtering"""
        # Create different types of locations
        locations_data = [
            {"name": "Warehouse A", "code": "WH-A", "location_type": "warehouse", "is_active": True},
            {"name": "Store B", "code": "ST-B", "location_type": "store", "is_active": True},
            {"name": "Warehouse C", "code": "WH-C", "location_type": "warehouse", "is_active": False}
        ]
        
        for location_data in locations_data:
            api_client.post("/api/v1/inventory/locations", json=location_data)
        
        # List all locations
        response = api_client.get("/api/v1/inventory/locations")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3
        
        # Filter by type
        response = api_client.get("/api/v1/inventory/locations?location_type=warehouse")
        assert response.status_code == 200
        data = response.json()
        warehouse_count = len([loc for loc in data["items"] if loc["location_type"] == "warehouse"])
        assert warehouse_count >= 2
        
        # Filter by active status
        response = api_client.get("/api/v1/inventory/locations?is_active=true")
        assert response.status_code == 200
        data = response.json()
        active_count = len([loc for loc in data["items"] if loc["is_active"]])
        assert active_count >= 2

    def test_inventory_statistics(self, api_client: TestClient):
        """Test inventory statistics endpoint"""
        # Create diverse inventory for statistics
        location_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "Stats Location", "code": "STATS-001", "location_type": "warehouse"
        })
        location_id = location_response.json()["id"]
        
        # Create multiple products with different stock levels
        stats_products = [
            {"name": "Stats Product 1", "sku": "STATS-P1", "price": 100, "quantity": 50, "cost": 80},
            {"name": "Stats Product 2", "sku": "STATS-P2", "price": 200, "quantity": 25, "cost": 160},
            {"name": "Stats Product 3", "sku": "STATS-P3", "price": 150, "quantity": 0, "cost": 120}  # Out of stock
        ]
        
        for product_info in stats_products:
            product_response = api_client.post("/api/v1/products", json={
                "name": product_info["name"],
                "sku": product_info["sku"],
                "price": product_info["price"]
            })
            product_id = product_response.json()["id"]
            
            if product_info["quantity"] > 0:
                api_client.post("/api/v1/inventory/items", json={
                    "product_id": product_id,
                    "location_id": location_id,
                    "quantity": product_info["quantity"],
                    "unit_cost": product_info["cost"]
                })
        
        # Get inventory statistics
        response = api_client.get("/api/v1/inventory/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_items" in data
        assert "total_locations" in data
        assert "total_value" in data
        assert "out_of_stock_items" in data
        assert "low_stock_items" in data

    def test_inventory_api_performance(self, api_client: TestClient):
        """Test inventory API performance requirements"""
        import time
        
        # Create test data
        product_response = api_client.post("/api/v1/products", json={
            "name": "Performance Test Product", "sku": "PERF-INV-001", "price": 199.99
        })
        product_id = product_response.json()["id"]
        
        location_response = api_client.post("/api/v1/inventory/locations", json={
            "name": "Performance Location", "code": "PERF-LOC-001", "location_type": "warehouse"
        })
        location_id = location_response.json()["id"]
        
        inventory_data = {
            "product_id": product_id,
            "location_id": location_id,
            "quantity": 100,
            "unit_cost": 99.50
        }
        
        # Measure inventory creation time
        start_time = time.time()
        response = api_client.post("/api/v1/inventory/items", json=inventory_data)
        end_time = time.time()
        
        creation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 201
        assert creation_time < 100, f"Inventory creation took {creation_time}ms, exceeds 100ms limit"
        
        inventory_id = response.json()["id"]
        
        # Measure real-time level retrieval time
        start_time = time.time()
        response = api_client.get(f"/api/v1/inventory/real-time/{product_id}")
        end_time = time.time()
        
        retrieval_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert retrieval_time < 50, f"Real-time retrieval took {retrieval_time}ms, exceeds 50ms limit"