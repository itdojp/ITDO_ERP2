"""
Comprehensive TDD Tests for Inventory Management Core API - CC02 v48.0 Phase 2
Testing all inventory operations, real-time tracking, alerts, and multi-location management
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, List, Any
import json
import uuid
from datetime import datetime, date
from decimal import Decimal

# Import the main app
from app.main_super_minimal import app

client = TestClient(app)

class TestInventoryManagementCoreAPI:
    """Comprehensive test suite for Inventory Management Core API"""

    def setup_method(self):
        """Setup test data before each test"""
        # Clear any existing test data
        try:
            client.delete("/api/v1/inventory/test/clear-all")
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass
        
        # Create test product first
        self.test_product = {
            "code": "INV001",
            "name": "Inventory Test Product",
            "description": "Product for inventory testing",
            "price": 99.99,
            "category": "Test Category"
        }
        
        product_response = client.post("/api/v1/simple-products/", json=self.test_product)
        self.product_id = product_response.json()["id"]
        
        # Create test locations
        self.warehouse_location = {
            "code": "WH001",
            "name": "Main Warehouse",
            "type": "warehouse",
            "address": "123 Warehouse St",
            "capacity": 10000
        }
        
        self.store_location = {
            "code": "ST001", 
            "name": "Main Store",
            "type": "store",
            "address": "456 Store Ave",
            "capacity": 1000
        }
        
        # Create locations
        warehouse_response = client.post("/api/v1/inventory/locations", json=self.warehouse_location)
        store_response = client.post("/api/v1/inventory/locations", json=self.store_location)
        
        self.warehouse_id = warehouse_response.json()["id"]
        self.store_id = store_response.json()["id"]

    def test_create_location_success(self):
        """Test successful location creation"""
        new_location = {
            "code": "TEST001",
            "name": "Test Location",
            "type": "warehouse",
            "address": "789 Test Blvd"
        }
        
        response = client.post("/api/v1/inventory/locations", json=new_location)
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == new_location["code"]
        assert data["name"] == new_location["name"]
        assert data["type"] == new_location["type"]
        assert data["address"] == new_location["address"]
        assert data["is_active"] == True
        assert "id" in data
        assert "created_at" in data

    def test_create_location_duplicate_code_fails(self):
        """Test that duplicate location codes are rejected"""
        duplicate_location = {
            "code": "WH001",  # Same as warehouse_location
            "name": "Duplicate Warehouse",
            "type": "warehouse"
        }
        
        response = client.post("/api/v1/inventory/locations", json=duplicate_location)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_list_locations(self):
        """Test listing locations"""
        response = client.get("/api/v1/inventory/locations")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 2  # Should have our test locations
        
        # Check that our test locations are present
        codes = [loc["code"] for loc in data]
        assert "WH001" in codes
        assert "ST001" in codes

    def test_list_locations_with_filters(self):
        """Test listing locations with filters"""
        # Filter by type
        response = client.get("/api/v1/inventory/locations?location_type=warehouse")
        assert response.status_code == 200
        data = response.json()
        
        for location in data:
            assert location["type"] == "warehouse"
        
        # Filter by active status
        response = client.get("/api/v1/inventory/locations?is_active=true")
        assert response.status_code == 200
        data = response.json()
        
        for location in data:
            assert location["is_active"] == True

    def test_get_location_by_id(self):
        """Test retrieving specific location"""
        response = client.get(f"/api/v1/inventory/locations/{self.warehouse_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.warehouse_id
        assert data["code"] == "WH001"
        assert data["name"] == "Main Warehouse"

    def test_get_location_not_found(self):
        """Test retrieving non-existent location"""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/inventory/locations/{fake_id}")
        assert response.status_code == 404

    def test_create_inventory_item_success(self):
        """Test successful inventory item creation"""
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100,
            "quantity_reserved": 5,
            "reorder_point": 20,
            "cost_per_unit": 50.00
        }
        
        response = client.post("/api/v1/inventory/items", json=inventory_item)
        assert response.status_code == 200
        data = response.json()
        
        assert data["product_id"] == self.product_id
        assert data["location_id"] == self.warehouse_id
        assert data["quantity_available"] == 100
        assert data["quantity_reserved"] == 5
        assert data["reorder_point"] == 20
        assert float(data["cost_per_unit"]) == 50.00
        assert data["status"] == "available"

    def test_create_inventory_item_invalid_product(self):
        """Test inventory item creation with invalid product"""
        fake_product_id = str(uuid.uuid4())
        inventory_item = {
            "product_id": fake_product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        
        response = client.post("/api/v1/inventory/items", json=inventory_item)
        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]

    def test_create_inventory_item_invalid_location(self):
        """Test inventory item creation with invalid location"""
        fake_location_id = str(uuid.uuid4())
        inventory_item = {
            "product_id": self.product_id,
            "location_id": fake_location_id,
            "quantity_available": 100
        }
        
        response = client.post("/api/v1/inventory/items", json=inventory_item)
        assert response.status_code == 404
        assert "Location not found" in response.json()["detail"]

    def test_create_inventory_item_duplicate_fails(self):
        """Test that duplicate product-location combinations are rejected"""
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        
        # Create first item
        response1 = client.post("/api/v1/inventory/items", json=inventory_item)
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = client.post("/api/v1/inventory/items", json=inventory_item)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_list_inventory_items(self):
        """Test listing inventory items"""
        # Create test inventory item
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        response = client.get("/api/v1/inventory/items")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_inventory_items_with_filters(self):
        """Test listing inventory items with filters"""
        # Create test inventory items
        item1 = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        item2 = {
            "product_id": self.product_id,
            "location_id": self.store_id,
            "quantity_available": 5,  # Below default reorder point of 10
        }
        
        client.post("/api/v1/inventory/items", json=item1)
        client.post("/api/v1/inventory/items", json=item2)
        
        # Filter by product
        response = client.get(f"/api/v1/inventory/items?product_id={self.product_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Filter by location
        response = client.get(f"/api/v1/inventory/items?location_id={self.warehouse_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["location_id"] == self.warehouse_id
        
        # Filter low stock items
        response = client.get("/api/v1/inventory/items?low_stock_only=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # Should include item2 with quantity 5

    def test_get_inventory_item_by_id(self):
        """Test retrieving specific inventory item"""
        # Create inventory item
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        
        create_response = client.post("/api/v1/inventory/items", json=inventory_item)
        item_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/inventory/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == item_id
        assert data["product_id"] == self.product_id

    def test_real_time_inventory_tracking(self):
        """Test real-time inventory data retrieval"""
        # Create inventory item
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100,
            "quantity_reserved": 5,
            "quantity_damaged": 2
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        response = client.get(f"/api/v1/inventory/real-time/{self.product_id}/{self.warehouse_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["product_id"] == self.product_id
        assert data["location_id"] == self.warehouse_id
        assert data["quantity_available"] == 100
        assert data["quantity_reserved"] == 5
        assert data["quantity_damaged"] == 2
        assert data["total_quantity"] == 107
        assert "last_updated" in data

    def test_real_time_inventory_not_found(self):
        """Test real-time inventory for non-existent combination"""
        fake_product_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/inventory/real-time/{fake_product_id}/{self.warehouse_id}")
        assert response.status_code == 404

    def test_stock_adjustment_positive(self):
        """Test positive stock adjustment"""
        # Create inventory item
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 50
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Make positive adjustment
        adjustment = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "adjustment_quantity": 25,
            "reason": "Stock replenishment",
            "reference_number": "ADJ001"
        }
        
        response = client.post("/api/v1/inventory/adjustments", json=adjustment)
        assert response.status_code == 200
        data = response.json()
        
        assert data["product_id"] == self.product_id
        assert data["location_id"] == self.warehouse_id
        assert data["movement_type"] == "adjustment"
        assert data["quantity"] == 25
        assert data["notes"] == "Stock replenishment"
        
        # Verify inventory was updated
        real_time_response = client.get(f"/api/v1/inventory/real-time/{self.product_id}/{self.warehouse_id}")
        assert real_time_response.json()["quantity_available"] == 75

    def test_stock_adjustment_negative(self):
        """Test negative stock adjustment"""
        # Create inventory item
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Make negative adjustment
        adjustment = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "adjustment_quantity": -30,
            "reason": "Damaged goods removed"
        }
        
        response = client.post("/api/v1/inventory/adjustments", json=adjustment)
        assert response.status_code == 200
        
        # Verify inventory was updated
        real_time_response = client.get(f"/api/v1/inventory/real-time/{self.product_id}/{self.warehouse_id}")
        assert real_time_response.json()["quantity_available"] == 70

    def test_stock_adjustment_insufficient_stock(self):
        """Test stock adjustment that would result in negative stock"""
        # Create inventory item with low stock
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 10
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Try to adjust more than available
        adjustment = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "adjustment_quantity": -20,  # More than available
            "reason": "Test negative stock"
        }
        
        response = client.post("/api/v1/inventory/adjustments", json=adjustment)
        assert response.status_code == 400
        assert "negative stock" in response.json()["detail"]

    def test_inventory_transfer_success(self):
        """Test successful inventory transfer between locations"""
        # Create inventory at source location
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Transfer inventory
        transfer = {
            "product_id": self.product_id,
            "from_location_id": self.warehouse_id,
            "to_location_id": self.store_id,
            "quantity": 25,
            "reason": "Store restocking"
        }
        
        response = client.post("/api/v1/inventory/transfers", json=transfer)
        assert response.status_code == 200
        data = response.json()
        
        assert "Transfer completed successfully" in data["message"]
        assert "transfer_id" in data
        assert "out_movement_id" in data
        assert "in_movement_id" in data
        
        # Verify source location stock reduced
        source_response = client.get(f"/api/v1/inventory/real-time/{self.product_id}/{self.warehouse_id}")
        assert source_response.json()["quantity_available"] == 75
        
        # Verify destination location stock increased
        dest_response = client.get(f"/api/v1/inventory/real-time/{self.product_id}/{self.store_id}")
        assert dest_response.json()["quantity_available"] == 25

    def test_inventory_transfer_insufficient_stock(self):
        """Test inventory transfer with insufficient stock"""
        # Create inventory item with low stock
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 10
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Try to transfer more than available
        transfer = {
            "product_id": self.product_id,
            "from_location_id": self.warehouse_id,
            "to_location_id": self.store_id,
            "quantity": 20,  # More than available
            "reason": "Test insufficient stock"
        }
        
        response = client.post("/api/v1/inventory/transfers", json=transfer)
        assert response.status_code == 400
        assert "Insufficient stock" in response.json()["detail"]

    def test_inventory_transfer_same_location(self):
        """Test inventory transfer with same source and destination"""
        transfer = {
            "product_id": self.product_id,
            "from_location_id": self.warehouse_id,
            "to_location_id": self.warehouse_id,  # Same as source
            "quantity": 10,
            "reason": "Invalid transfer"
        }
        
        response = client.post("/api/v1/inventory/transfers", json=transfer)
        assert response.status_code == 400
        assert "cannot be the same" in response.json()["detail"]

    def test_list_inventory_movements(self):
        """Test listing inventory movements"""
        # Create inventory and make some movements
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Make adjustment
        adjustment = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "adjustment_quantity": 10,
            "reason": "Test movement"
        }
        client.post("/api/v1/inventory/adjustments", json=adjustment)
        
        response = client.get("/api/v1/inventory/movements")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["movement_type"] == "adjustment"

    def test_list_inventory_movements_with_filters(self):
        """Test listing inventory movements with filters"""
        # Create inventory and movements
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        adjustment = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "adjustment_quantity": 10,
            "reason": "Test movement"
        }
        client.post("/api/v1/inventory/adjustments", json=adjustment)
        
        # Filter by product
        response = client.get(f"/api/v1/inventory/movements?product_id={self.product_id}")
        assert response.status_code == 200
        data = response.json()
        
        for movement in data:
            assert movement["product_id"] == self.product_id
        
        # Filter by movement type
        response = client.get("/api/v1/inventory/movements?movement_type=adjustment")
        assert response.status_code == 200
        data = response.json()
        
        for movement in data:
            assert movement["movement_type"] == "adjustment"

    def test_inventory_alerts_generation(self):
        """Test automatic inventory alert generation"""
        # Create inventory item with low stock (below reorder point)
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 5,  # Below default reorder point of 10
            "reorder_point": 10
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Check that alert was generated
        response = client.get("/api/v1/inventory/alerts")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        low_stock_alerts = [alert for alert in data if alert["alert_type"] == "low_stock"]
        assert len(low_stock_alerts) >= 1

    def test_inventory_alerts_out_of_stock(self):
        """Test out of stock alert generation"""
        # Create inventory item with zero stock
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 0,
            "reorder_point": 10
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Check that out of stock alert was generated
        response = client.get("/api/v1/inventory/alerts")
        assert response.status_code == 200
        data = response.json()
        
        out_of_stock_alerts = [alert for alert in data if alert["alert_type"] == "out_of_stock"]
        assert len(out_of_stock_alerts) >= 1
        assert out_of_stock_alerts[0]["severity"] == "critical"

    def test_acknowledge_alert(self):
        """Test acknowledging inventory alert"""
        # Create low stock item to generate alert
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 3,
            "reorder_point": 10
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Get alert
        alerts_response = client.get("/api/v1/inventory/alerts")
        alerts = alerts_response.json()
        assert len(alerts) >= 1
        
        alert_id = alerts[0]["id"]
        
        # Acknowledge alert
        response = client.post(f"/api/v1/inventory/alerts/{alert_id}/acknowledge")
        assert response.status_code == 200
        
        # Verify alert is acknowledged
        alert_response = client.get("/api/v1/inventory/alerts")
        updated_alerts = alert_response.json()
        acknowledged_alert = next(alert for alert in updated_alerts if alert["id"] == alert_id)
        assert acknowledged_alert["is_acknowledged"] == True

    def test_reorder_suggestions(self):
        """Test automatic reorder suggestions"""
        # Create inventory item that will trigger reorder suggestion
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 2,  # Very low stock
            "reorder_point": 10
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        response = client.get("/api/v1/inventory/reorder-suggestions")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        suggestion = data[0]
        assert suggestion["product_id"] == self.product_id
        assert suggestion["location_id"] == self.warehouse_id
        assert suggestion["current_stock"] == 2
        assert suggestion["reorder_point"] == 10
        assert suggestion["suggested_quantity"] > 0

    def test_reorder_suggestions_with_priority_filter(self):
        """Test filtering reorder suggestions by priority"""
        # Create out of stock item (high priority)
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 0,
            "reorder_point": 10
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        response = client.get("/api/v1/inventory/reorder-suggestions?priority=high")
        assert response.status_code == 200
        data = response.json()
        
        for suggestion in data:
            assert suggestion["priority"] == "high"

    def test_inventory_statistics(self):
        """Test comprehensive inventory statistics"""
        # Create some test data
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 50,
            "cost_per_unit": 25.00
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Make some movements
        adjustment = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "adjustment_quantity": 10,
            "reason": "Test stats"
        }
        client.post("/api/v1/inventory/adjustments", json=adjustment)
        
        response = client.get("/api/v1/inventory/statistics")
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "locations" in data
        assert "inventory" in data
        assert "movements" in data
        assert "alerts" in data
        assert "cache_status" in data
        
        # Check location data
        assert data["locations"]["total_locations"] >= 2
        assert data["locations"]["active_locations"] >= 2
        
        # Check inventory data
        assert data["inventory"]["total_items"] >= 1
        assert isinstance(data["inventory"]["total_stock_value"], (int, float))
        
        # Check movements data
        assert data["movements"]["total_movements"] >= 1
        assert "adjustment" in data["movements"]["movement_types"]

    def test_performance_real_time_inventory(self):
        """Test performance of real-time inventory retrieval"""
        import time
        
        # Create inventory item
        inventory_item = {
            "product_id": self.product_id,
            "location_id": self.warehouse_id,
            "quantity_available": 100
        }
        client.post("/api/v1/inventory/items", json=inventory_item)
        
        # Measure response time
        start_time = time.time()
        response = client.get(f"/api/v1/inventory/real-time/{self.product_id}/{self.warehouse_id}")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        # Performance assertion: should respond within 10ms for cached data
        assert response_time < 10, f"Response time {response_time}ms exceeds 10ms threshold"

    def test_bulk_inventory_operations(self):
        """Test handling multiple inventory operations"""
        # Create multiple inventory items
        for i in range(5):
            inventory_item = {
                "product_id": self.product_id,
                "location_id": self.warehouse_id if i % 2 == 0 else self.store_id,
                "quantity_available": 50 + i * 10
            }
            try:
                client.post("/api/v1/inventory/items", json=inventory_item)
            except:
                pass  # Skip if duplicate product-location exists
        
        # Make multiple adjustments
        for i in range(3):
            adjustment = {
                "product_id": self.product_id,
                "location_id": self.warehouse_id,
                "adjustment_quantity": 5,
                "reason": f"Bulk adjustment {i}"
            }
            client.post("/api/v1/inventory/adjustments", json=adjustment)
        
        # Verify all movements were recorded
        movements_response = client.get("/api/v1/inventory/movements")
        movements = movements_response.json()
        
        adjustment_movements = [mov for mov in movements if mov["movement_type"] == "adjustment"]
        assert len(adjustment_movements) >= 3

    def test_edge_cases_and_validation(self):
        """Test edge cases and validation scenarios"""
        # Test with non-existent product
        invalid_adjustment = {
            "product_id": str(uuid.uuid4()),
            "location_id": self.warehouse_id,
            "adjustment_quantity": 10,
            "reason": "Invalid product test"
        }
        
        response = client.post("/api/v1/inventory/adjustments", json=invalid_adjustment)
        assert response.status_code == 404
        
        # Test with non-existent location
        invalid_adjustment = {
            "product_id": self.product_id,
            "location_id": str(uuid.uuid4()),
            "adjustment_quantity": 10,
            "reason": "Invalid location test"
        }
        
        response = client.post("/api/v1/inventory/adjustments", json=invalid_adjustment)
        assert response.status_code == 404
        
        # Test transfer with non-existent locations
        invalid_transfer = {
            "product_id": self.product_id,
            "from_location_id": str(uuid.uuid4()),
            "to_location_id": self.store_id,
            "quantity": 10,
            "reason": "Invalid transfer test"
        }
        
        response = client.post("/api/v1/inventory/transfers", json=invalid_transfer)
        assert response.status_code == 404

    def teardown_method(self):
        """Clean up after each test"""
        try:
            client.delete("/api/v1/inventory/test/clear-all")
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass