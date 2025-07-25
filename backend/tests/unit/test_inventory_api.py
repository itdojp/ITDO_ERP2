"""
CC02 v53.0 Inventory API Unit Tests - Issue #568
10-Day ERP Business API Implementation Sprint - Day 3-4
Test-Driven Development Implementation for Inventory Management
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.main_super_minimal import app
# from app.models.inventory import Location, InventoryItem, InventoryMovement
# from app.schemas.inventory_v53 import (
#     LocationCreate, LocationUpdate, LocationResponse,
#     InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
#     InventoryMovementCreate, InventoryMovementResponse,
#     StockAdjustmentCreate, StockTransferCreate,
#     InventoryStatistics
# )


class TestInventoryAPI:
    """
    Comprehensive Inventory API Test Suite
    TDD Implementation for CC02 v53.0 ERP Business APIs
    
    Requirements:
    - Test Coverage: 95%+
    - Response Time: <200ms
    - Error Handling: Complete implementation
    """

    def test_create_location_basic(self, client: TestClient, db_session: AsyncSession):
        """Test basic location creation with required fields only"""
        location_data = {
            "name": "Main Warehouse",
            "code": "WH-001",
            "location_type": "warehouse",
            "address": "123 Industrial Ave",
            "is_active": True
        }
        
        response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == location_data["name"]
        assert data["code"] == location_data["code"]
        assert data["location_type"] == location_data["location_type"]
        assert data["address"] == location_data["address"]
        assert data["is_active"] == location_data["is_active"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_location_comprehensive(self, client: TestClient, db_session: AsyncSession):
        """Test location creation with all optional fields"""
        # First create a parent location
        parent_data = {"name": "Distribution Center", "code": "DC-001", "location_type": "warehouse"}
        parent_response = client.post("/api/v1/inventory-v53/locations/", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        location_data = {
            "name": "Store #1",
            "code": "ST-001",
            "location_type": "store",
            "address": "456 Main Street, Downtown",
            "contact_person": "John Manager",
            "contact_phone": "+1-555-0123",
            "contact_email": "john@store.com",
            "is_active": True,
            "capacity_limit": 10000,
            "parent_location_id": parent_id,
            "attributes": {
                "store_type": "retail",
                "opening_hours": "9:00-21:00",
                "square_feet": 2500
            }
        }
        
        response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == location_data["name"]
        assert data["contact_person"] == location_data["contact_person"]
        assert data["contact_phone"] == location_data["contact_phone"]
        assert data["contact_email"] == location_data["contact_email"]
        assert data["capacity_limit"] == location_data["capacity_limit"]
        assert data["parent_location_id"] == parent_id
        assert data["attributes"]["store_type"] == "retail"

    def test_create_location_duplicate_code(self, client: TestClient):
        """Test duplicate location code validation"""
        location_data = {
            "name": "First Location",
            "code": "DUPLICATE-001",
            "location_type": "warehouse"
        }
        
        # Create first location
        response1 = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        assert response1.status_code == 201
        
        # Try to create duplicate code
        duplicate_data = {
            "name": "Second Location",
            "code": "DUPLICATE-001",
            "location_type": "store"
        }
        response2 = client.post("/api/v1/inventory-v53/locations/", json=duplicate_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_list_locations_with_filtering(self, client: TestClient):
        """Test location listing with filtering capabilities"""
        # Clear any existing locations first
        from app.api.v1.endpoints.inventory_v53 import locations_store
        locations_store.clear()
        
        # Create multiple locations for filtering
        locations_data = [
            {"name": "Warehouse A", "code": "WH-A", "location_type": "warehouse", "is_active": True},
            {"name": "Store B", "code": "ST-B", "location_type": "store", "is_active": True},
            {"name": "Warehouse C", "code": "WH-C", "location_type": "warehouse", "is_active": False}
        ]
        
        for location_data in locations_data:
            client.post("/api/v1/inventory-v53/locations/", json=location_data)
        
        # Test basic listing
        response = client.get("/api/v1/inventory-v53/locations/")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 3
        
        # Test filtering by location type
        response = client.get("/api/v1/inventory-v53/locations/?location_type=warehouse")
        assert response.status_code == 200
        
        data = response.json()
        warehouse_items = [item for item in data["items"] if item["location_type"] == "warehouse"]
        assert len(warehouse_items) >= 2
        
        # Test filtering by active status
        response = client.get("/api/v1/inventory-v53/locations/?is_active=true")
        assert response.status_code == 200
        
        data = response.json()
        active_items = [item for item in data["items"] if item["is_active"]]
        assert len(active_items) >= 2

    def test_create_inventory_item_basic(self, client: TestClient):
        """Test basic inventory item creation"""
        # First create a location
        location_data = {"name": "Test Warehouse", "code": "TEST-WH", "location_type": "warehouse"}
        location_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        # Create inventory item
        item_data = {
            "product_id": "prod-001",
            "location_id": location_id,
            "quantity": "100.00",
            "minimum_level": "10.00",
            "reorder_point": "20.00",
            "cost_per_unit": "15.50"
        }
        
        response = client.post("/api/v1/inventory-v53/items/", json=item_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["product_id"] == item_data["product_id"]
        assert data["location_id"] == location_id
        assert float(data["quantity"]) == 100.00
        assert float(data["available_quantity"]) == 100.00
        assert float(data["minimum_level"]) == 10.00
        assert float(data["reorder_point"]) == 20.00
        assert float(data["cost_per_unit"]) == 15.50
        assert float(data["total_value"]) == 1550.00  # 100 * 15.50

    def test_create_inventory_item_comprehensive(self, client: TestClient):
        """Test inventory item creation with all fields"""
        # Create location
        location_data = {"name": "Comprehensive Warehouse", "code": "COMP-WH", "location_type": "warehouse"}
        location_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        # Create comprehensive inventory item
        item_data = {
            "product_id": "prod-comp-001",
            "location_id": location_id,
            "quantity": "250.50",
            "reserved_quantity": "25.00",
            "allocated_quantity": "15.00",
            "minimum_level": "50.00",
            "maximum_level": "500.00",
            "reorder_point": "75.00",
            "reorder_quantity": "200.00",
            "status": "available",
            "cost_per_unit": "12.75",
            "lot_number": "LOT-2024-001",
            "serial_number": "SN-ABC123",
            "expiry_date": "2025-12-31",
            "manufacture_date": "2024-01-15",
            "supplier_id": "supplier-001",
            "notes": "High-quality inventory item for testing",
            "attributes": {
                "batch_number": "B-001",
                "quality_grade": "A",
                "storage_temperature": "-18C"
            }
        }
        
        response = client.post("/api/v1/inventory-v53/items/", json=item_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["product_id"] == item_data["product_id"]
        assert float(data["quantity"]) == 250.50
        assert float(data["reserved_quantity"]) == 25.00
        assert float(data["allocated_quantity"]) == 15.00
        assert float(data["available_quantity"]) == 210.50  # 250.50 - 25.00 - 15.00
        assert data["lot_number"] == item_data["lot_number"]
        assert data["serial_number"] == item_data["serial_number"]
        assert data["supplier_id"] == item_data["supplier_id"]
        assert data["attributes"]["quality_grade"] == "A"

    def test_inventory_item_duplicate_prevention(self, client: TestClient):
        """Test prevention of duplicate inventory items for same product/location"""
        # Create location
        location_data = {"name": "Duplicate Test Warehouse", "code": "DUP-WH", "location_type": "warehouse"}
        location_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        # Create first inventory item
        item_data = {
            "product_id": "prod-duplicate",
            "location_id": location_id,
            "quantity": "100.00"
        }
        
        response1 = client.post("/api/v1/inventory-v53/items/", json=item_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post("/api/v1/inventory-v53/items/", json=item_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_stock_adjustment_positive(self, client: TestClient):
        """Test positive stock adjustment (increase)"""
        # Create location and inventory item
        location_data = {"name": "Adjustment Warehouse", "code": "ADJ-WH", "location_type": "warehouse"}
        location_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        item_data = {
            "product_id": "prod-adjust",
            "location_id": location_id,
            "quantity": "100.00",
            "cost_per_unit": "10.00"
        }
        
        item_response = client.post("/api/v1/inventory-v53/items/", json=item_data)
        assert item_response.status_code == 201
        
        # Create positive adjustment
        adjustment_data = {
            "product_id": "prod-adjust",
            "location_id": location_id,
            "adjustment_quantity": "50.00",
            "reason": "Stock received from supplier",
            "notes": "Additional inventory from emergency order"
        }
        
        response = client.post("/api/v1/inventory-v53/adjustments/", json=adjustment_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["product_id"] == "prod-adjust"
        assert float(data["old_quantity"]) == 100.00
        assert float(data["adjustment_quantity"]) == 50.00
        assert float(data["new_quantity"]) == 150.00
        assert data["reason"] == adjustment_data["reason"]

    def test_stock_adjustment_negative(self, client: TestClient):
        """Test negative stock adjustment (decrease)"""
        # Create location and inventory item
        location_data = {"name": "Negative Adj Warehouse", "code": "NEG-WH", "location_type": "warehouse"}
        location_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        item_data = {
            "product_id": "prod-neg-adjust",
            "location_id": location_id,
            "quantity": "100.00"
        }
        
        client.post("/api/v1/inventory-v53/items/", json=item_data)
        
        # Create negative adjustment
        adjustment_data = {
            "product_id": "prod-neg-adjust",
            "location_id": location_id,
            "adjustment_quantity": "-25.00",
            "reason": "Damaged goods write-off",
            "notes": "Items damaged during transportation"
        }
        
        response = client.post("/api/v1/inventory-v53/adjustments/", json=adjustment_data)
        assert response.status_code == 201
        
        data = response.json()
        assert float(data["old_quantity"]) == 100.00
        assert float(data["adjustment_quantity"]) == -25.00
        assert float(data["new_quantity"]) == 75.00

    def test_stock_adjustment_insufficient_stock(self, client: TestClient):
        """Test stock adjustment that would result in negative stock"""
        # Create location and inventory item
        location_data = {"name": "Insufficient Stock Warehouse", "code": "INS-WH", "location_type": "warehouse"}
        location_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        item_data = {
            "product_id": "prod-insufficient",
            "location_id": location_id,
            "quantity": "50.00"
        }
        
        client.post("/api/v1/inventory-v53/items/", json=item_data)
        
        # Try to adjust more than available
        adjustment_data = {
            "product_id": "prod-insufficient",
            "location_id": location_id,
            "adjustment_quantity": "-75.00",  # More than the 50 available
            "reason": "Over-adjustment test"
        }
        
        response = client.post("/api/v1/inventory-v53/adjustments/", json=adjustment_data)
        assert response.status_code == 400
        assert "negative stock" in response.json()["detail"]

    def test_stock_transfer_basic(self, client: TestClient):
        """Test basic stock transfer between locations"""
        # Create two locations
        from_location_data = {"name": "Source Warehouse", "code": "SRC-WH", "location_type": "warehouse"}
        from_response = client.post("/api/v1/inventory-v53/locations/", json=from_location_data)
        from_location_id = from_response.json()["id"]
        
        to_location_data = {"name": "Destination Store", "code": "DEST-ST", "location_type": "store"}
        to_response = client.post("/api/v1/inventory-v53/locations/", json=to_location_data)
        to_location_id = to_response.json()["id"]
        
        # Create inventory item in source location
        item_data = {
            "product_id": "prod-transfer",
            "location_id": from_location_id,
            "quantity": "200.00"
        }
        
        client.post("/api/v1/inventory-v53/items/", json=item_data)
        
        # Create transfer
        transfer_data = {
            "product_id": "prod-transfer",
            "from_location_id": from_location_id,
            "to_location_id": to_location_id,
            "quantity": "75.00",
            "reason": "Store replenishment",
            "notes": "Regular weekly transfer"
        }
        
        response = client.post("/api/v1/inventory-v53/transfers/", json=transfer_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["product_id"] == "prod-transfer"
        assert data["from_location_id"] == from_location_id
        assert data["to_location_id"] == to_location_id
        assert float(data["quantity"]) == 75.00
        assert data["reason"] == "Store replenishment"

    def test_stock_transfer_insufficient_stock(self, client: TestClient):
        """Test stock transfer with insufficient stock"""
        # Create two locations
        from_location_data = {"name": "Low Stock Warehouse", "code": "LOW-WH", "location_type": "warehouse"}
        from_response = client.post("/api/v1/inventory-v53/locations/", json=from_location_data)
        from_location_id = from_response.json()["id"]
        
        to_location_data = {"name": "Dest Store", "code": "DEST-ST2", "location_type": "store"}
        to_response = client.post("/api/v1/inventory-v53/locations/", json=to_location_data)
        to_location_id = to_response.json()["id"]
        
        # Create inventory item with limited stock
        item_data = {
            "product_id": "prod-limited",
            "location_id": from_location_id,
            "quantity": "30.00",
            "reserved_quantity": "10.00"  # Only 20 available
        }
        
        client.post("/api/v1/inventory-v53/items/", json=item_data)
        
        # Try to transfer more than available
        transfer_data = {
            "product_id": "prod-limited",
            "from_location_id": from_location_id,
            "to_location_id": to_location_id,
            "quantity": "25.00",  # More than the 20 available
            "reason": "Over-transfer test"
        }
        
        response = client.post("/api/v1/inventory-v53/transfers/", json=transfer_data)
        assert response.status_code == 400
        assert "Insufficient stock" in response.json()["detail"]

    def test_inventory_item_listing_with_filters(self, client: TestClient):
        """Test inventory item listing with various filters"""
        # Clear existing items
        from app.api.v1.endpoints.inventory_v53 import inventory_items_store, locations_store
        inventory_items_store.clear()
        locations_store.clear()
        
        # Create locations
        wh_response = client.post("/api/v1/inventory-v53/locations/", 
                                 json={"name": "Filter Warehouse", "code": "FILT-WH", "location_type": "warehouse"})
        wh_id = wh_response.json()["id"]
        
        st_response = client.post("/api/v1/inventory-v53/locations/", 
                                 json={"name": "Filter Store", "code": "FILT-ST", "location_type": "store"})
        st_id = st_response.json()["id"]
        
        # Create inventory items for filtering
        items_data = [
            {"product_id": "prod-filter-1", "location_id": wh_id, "quantity": "100.00", "reorder_point": "20.00"},
            {"product_id": "prod-filter-2", "location_id": wh_id, "quantity": "15.00", "reorder_point": "20.00"},  # Low stock
            {"product_id": "prod-filter-3", "location_id": st_id, "quantity": "0.00"},  # Out of stock
            {"product_id": "prod-filter-4", "location_id": st_id, "quantity": "50.00", "status": "reserved"}
        ]
        
        for item_data in items_data:
            client.post("/api/v1/inventory-v53/items/", json=item_data)
        
        # Test basic listing
        response = client.get("/api/v1/inventory-v53/items/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 4
        
        # Test filtering by location
        response = client.get(f"/api/v1/inventory-v53/items/?location_id={wh_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 2
        assert all(item["location_id"] == wh_id for item in data["items"])
        
        # Test low stock filter
        response = client.get("/api/v1/inventory-v53/items/?low_stock_only=true")
        assert response.status_code == 200
        
        data = response.json()
        low_stock_items = [item for item in data["items"] if float(item["quantity"]) <= float(item.get("reorder_point", 0))]
        assert len(low_stock_items) >= 1
        
        # Test out of stock filter
        response = client.get("/api/v1/inventory-v53/items/?out_of_stock_only=true")
        assert response.status_code == 200
        
        data = response.json()
        out_of_stock_items = [item for item in data["items"] if float(item["quantity"]) == 0]
        assert len(out_of_stock_items) >= 1

    def test_inventory_statistics_comprehensive(self, client: TestClient):
        """Test comprehensive inventory statistics"""
        # Clear existing data
        from app.api.v1.endpoints.inventory_v53 import (
            inventory_items_store, locations_store, movements_store
        )
        inventory_items_store.clear()
        locations_store.clear()
        movements_store.clear()
        
        # Create locations
        wh_response = client.post("/api/v1/inventory-v53/locations/", 
                                 json={"name": "Stats Warehouse", "code": "STATS-WH", "location_type": "warehouse", "is_active": True})
        wh_id = wh_response.json()["id"]
        
        st_response = client.post("/api/v1/inventory-v53/locations/", 
                                 json={"name": "Stats Store", "code": "STATS-ST", "location_type": "store", "is_active": True})
        st_id = st_response.json()["id"]
        
        # Create inventory items with different statuses
        items_data = [
            {"product_id": "stats-prod-1", "location_id": wh_id, "quantity": "100.00", "cost_per_unit": "10.00", "status": "available"},
            {"product_id": "stats-prod-2", "location_id": wh_id, "quantity": "50.00", "cost_per_unit": "20.00", "status": "reserved"},
            {"product_id": "stats-prod-3", "location_id": st_id, "quantity": "25.00", "cost_per_unit": "15.00", "status": "available"},
            {"product_id": "stats-prod-4", "location_id": st_id, "quantity": "0.00", "cost_per_unit": "5.00", "status": "available"}
        ]
        
        for item_data in items_data:
            client.post("/api/v1/inventory-v53/items/", json=item_data)
        
        # Get statistics
        response = client.get("/api/v1/inventory-v53/statistics")
        assert response.status_code == 200
        
        stats = response.json()
        
        # Verify required statistics fields
        required_fields = [
            "total_locations", "active_locations", "total_products_tracked",
            "total_inventory_items", "total_stock_quantity", "total_inventory_value",
            "available_items", "reserved_items", "out_of_stock_alerts",
            "locations_by_type", "last_updated"
        ]
        
        for field in required_fields:
            assert field in stats, f"Missing required field: {field}"
        
        # Verify statistics accuracy
        assert stats["total_locations"] == 2
        assert stats["active_locations"] == 2
        assert stats["total_products_tracked"] == 4
        assert stats["total_inventory_items"] == 4
        assert float(stats["total_stock_quantity"]) == 175.00  # 100 + 50 + 25 + 0
        assert float(stats["total_inventory_value"]) == 2375.00  # (100*10) + (50*20) + (25*15) + (0*5)
        assert stats["available_items"] >= 3
        assert stats["reserved_items"] >= 1
        assert stats["out_of_stock_alerts"] >= 1

    def test_inventory_movements_listing(self, client: TestClient):
        """Test inventory movements listing and filtering"""
        # Create some test data first
        location_data = {"name": "Movement Test Warehouse", "code": "MOV-WH", "location_type": "warehouse"}
        location_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        item_data = {
            "product_id": "prod-movement",
            "location_id": location_id,
            "quantity": "100.00"
        }
        client.post("/api/v1/inventory-v53/items/", json=item_data)
        
        # Create an adjustment to generate movement
        adjustment_data = {
            "product_id": "prod-movement",
            "location_id": location_id,
            "adjustment_quantity": "25.00",
            "reason": "Test movement generation"
        }
        client.post("/api/v1/inventory-v53/adjustments/", json=adjustment_data)
        
        # Test movements listing
        response = client.get("/api/v1/inventory-v53/movements/")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
        
        # Verify movement structure
        if data["items"]:
            movement = data["items"][0]
            assert "id" in movement
            assert "product_id" in movement
            assert "movement_type" in movement
            assert "quantity" in movement
            assert "reason" in movement
            assert "created_at" in movement

    def test_api_performance_requirements(self, client: TestClient):
        """Test API performance requirements (<200ms)"""
        import time
        
        # Create test location for performance testing
        location_data = {
            "name": "Performance Test Warehouse",
            "code": "PERF-WH",
            "location_type": "warehouse"
        }
        
        # Measure location creation time
        start_time = time.time()
        response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        end_time = time.time()
        
        creation_time_ms = (end_time - start_time) * 1000
        assert response.status_code == 201
        assert creation_time_ms < 200, f"Location creation took {creation_time_ms}ms, exceeds 200ms limit"
        
        location_id = response.json()["id"]
        
        # Measure inventory item creation time
        item_data = {
            "product_id": "perf-prod-001",
            "location_id": location_id,
            "quantity": "100.00"
        }
        
        start_time = time.time()
        response = client.post("/api/v1/inventory-v53/items/", json=item_data)
        end_time = time.time()
        
        item_creation_time_ms = (end_time - start_time) * 1000
        assert response.status_code == 201
        assert item_creation_time_ms < 200, f"Item creation took {item_creation_time_ms}ms, exceeds 200ms limit"
        
        # Measure statistics retrieval time
        start_time = time.time()
        response = client.get("/api/v1/inventory-v53/statistics")
        end_time = time.time()
        
        stats_time_ms = (end_time - start_time) * 1000
        assert response.status_code == 200
        assert stats_time_ms < 200, f"Statistics retrieval took {stats_time_ms}ms, exceeds 200ms limit"

    def test_error_handling_comprehensive(self, client: TestClient):
        """Test comprehensive error handling scenarios"""
        
        # Test creating item with non-existent location
        invalid_item_data = {
            "product_id": "error-prod",
            "location_id": "non-existent-location",
            "quantity": "100.00"
        }
        
        response = client.post("/api/v1/inventory-v53/items/", json=invalid_item_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        
        # Test accessing non-existent location
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/inventory-v53/locations/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        
        # Test accessing non-existent inventory item
        response = client.get(f"/api/v1/inventory-v53/items/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        
        # Test invalid adjustment for non-existent product/location combination
        adjustment_data = {
            "product_id": "non-existent-product",
            "location_id": "non-existent-location",
            "adjustment_quantity": "10.00",
            "reason": "Test error"
        }
        
        response = client.post("/api/v1/inventory-v53/adjustments/", json=adjustment_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_location_update_and_delete(self, client: TestClient):
        """Test location update and delete operations"""
        # Create location
        location_data = {
            "name": "Updatable Location",
            "code": "UPD-LOC",
            "location_type": "warehouse",
            "address": "Original Address"
        }
        
        create_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = create_response.json()["id"]
        
        # Update location
        update_data = {
            "name": "Updated Location Name",
            "address": "New Address 123",
            "contact_person": "Updated Manager",
            "capacity_limit": 5000
        }
        
        response = client.put(f"/api/v1/inventory-v53/locations/{location_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["address"] == update_data["address"]
        assert data["contact_person"] == update_data["contact_person"]
        assert data["capacity_limit"] == update_data["capacity_limit"]
        assert data["code"] == location_data["code"]  # Should remain unchanged
        
        # Test soft delete
        response = client.delete(f"/api/v1/inventory-v53/locations/{location_id}")
        assert response.status_code == 200
        
        # Verify location is deactivated
        get_response = client.get(f"/api/v1/inventory-v53/locations/{location_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    def test_inventory_item_update(self, client: TestClient):
        """Test inventory item update functionality"""
        # Create location and item
        location_data = {"name": "Update Test Warehouse", "code": "UPD-WH", "location_type": "warehouse"}
        location_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        item_data = {
            "product_id": "prod-update",
            "location_id": location_id,
            "quantity": "100.00",
            "cost_per_unit": "10.00",
            "minimum_level": "20.00"
        }
        
        create_response = client.post("/api/v1/inventory-v53/items/", json=item_data)
        item_id = create_response.json()["id"]
        
        # Update item
        update_data = {
            "quantity": "150.00",
            "cost_per_unit": "12.00",
            "reorder_point": "30.00",
            "notes": "Updated inventory item"
        }
        
        response = client.put(f"/api/v1/inventory-v53/items/{item_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert float(data["quantity"]) == 150.00
        assert float(data["cost_per_unit"]) == 12.00
        assert float(data["reorder_point"]) == 30.00
        assert data["notes"] == update_data["notes"]
        assert data["total_value"] == 1800.00  # 150 * 12

    def test_health_performance_endpoint(self, client: TestClient):
        """Test health and performance endpoint"""
        response = client.get("/api/v1/inventory-v53/health/performance")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "response_time_ms" in data
        assert "location_count" in data
        assert "inventory_item_count" in data
        assert "movement_count" in data
        assert "timestamp" in data
        assert data["version"] == "v53.0"
        
        # Verify performance
        assert float(data["response_time_ms"]) < 50  # Health check should be very fast


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
class TestInventoryAPIPerformance:
    """Performance testing suite for Inventory API"""
    
    def test_concurrent_location_creation(self, client: TestClient):
        """Test handling of concurrent location creation requests"""
        import concurrent.futures
        import threading
        
        def create_location(thread_id):
            location_data = {
                "name": f"Concurrent Location {thread_id}",
                "code": f"CONC-{thread_id:03d}",
                "location_type": "warehouse"
            }
            return client.post("/api/v1/inventory-v53/locations/", json=location_data)
        
        # Test with 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_location, i) for i in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        success_count = sum(1 for response in responses if response.status_code == 201)
        assert success_count >= 8, f"Only {success_count}/10 concurrent location creations succeeded"
    
    def test_large_inventory_listing_performance(self, client: TestClient):
        """Test performance with large inventory datasets"""
        # Clear existing data
        from app.api.v1.endpoints.inventory_v53 import inventory_items_store, locations_store
        inventory_items_store.clear()
        locations_store.clear()
        
        # Create a location
        location_data = {"name": "Large Dataset Warehouse", "code": "LARGE-WH", "location_type": "warehouse"}
        location_response = client.post("/api/v1/inventory-v53/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        # Create many inventory items
        for i in range(50):
            item_data = {
                "product_id": f"large-prod-{i:03d}",
                "location_id": location_id,
                "quantity": f"{100 + i}.00",
                "cost_per_unit": f"{10 + (i % 10)}.00"
            }
            client.post("/api/v1/inventory-v53/items/", json=item_data)
        
        # Test listing performance
        import time
        start_time = time.time()
        response = client.get("/api/v1/inventory-v53/items/?size=50")
        end_time = time.time()
        
        list_time_ms = (end_time - start_time) * 1000
        assert response.status_code == 200
        assert list_time_ms < 300, f"Large inventory listing took {list_time_ms}ms, exceeds performance requirement"
        
        # Verify we got the expected data
        data = response.json()
        assert len(data["items"]) == 50
        assert data["total"] == 50


# Integration Testing
class TestInventoryAPIIntegration:
    """Integration testing suite for Inventory API with other systems"""
    
    def test_inventory_product_integration(self, client: TestClient):
        """Test integration between inventory and product systems"""
        # This test verifies the relationship between inventory items and products
        pass  # Implementation depends on product system integration
    
    def test_inventory_order_integration(self, client: TestClient):
        """Test integration between inventory and order systems"""
        # This test verifies inventory reservations and allocations for orders
        pass  # Implementation depends on order system integration
    
    def test_inventory_reporting_integration(self, client: TestClient):
        """Test integration with reporting systems"""
        # This test verifies inventory data feeds into reporting
        pass  # Implementation depends on reporting system integration