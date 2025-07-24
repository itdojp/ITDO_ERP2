import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch
from datetime import datetime
from decimal import Decimal

from app.main import app
from app.models.inventory_extended import Warehouse, InventoryItem, StockMovement, CycleCount, StockAlert
from app.models.user_extended import User


class TestInventoryCompleteV30:
    """Complete Inventory Management API Tests"""

    @pytest.fixture
    async def mock_user(self):
        """Create a mock user for testing"""
        user = User()
        user.id = "test-user-123"
        user.is_superuser = True
        return user

    @pytest.fixture
    async def mock_warehouse(self):
        """Create a mock warehouse for testing"""
        warehouse = Warehouse()
        warehouse.id = "test-warehouse-123"
        warehouse.code = "WH001"
        warehouse.name = "Main Warehouse"
        warehouse.description = "Primary storage facility"
        warehouse.warehouse_type = "standard"
        warehouse.address_line1 = "123 Storage St"
        warehouse.city = "Tokyo"
        warehouse.country = "Japan"
        warehouse.capacity_sqm = Decimal("1000.00")
        warehouse.is_active = True
        warehouse.is_default = True
        warehouse.created_at = datetime.utcnow()
        warehouse.settings = {}
        warehouse.operating_hours = {}
        return warehouse

    @pytest.fixture
    async def mock_inventory_item(self):
        """Create a mock inventory item for testing"""
        item = InventoryItem()
        item.id = "test-inventory-123"
        item.product_id = "test-product-123"
        item.warehouse_id = "test-warehouse-123"
        item.quantity_available = 100
        item.quantity_reserved = 10
        item.quantity_allocated = 5
        item.quantity_on_order = 0
        item.quantity_in_transit = 0
        item.unit_cost = Decimal("50.00")
        item.average_cost = Decimal("50.00")
        item.quality_status = "good"
        item.reorder_point = 20
        item.safety_stock = 10
        item.is_active = True
        item.is_locked = False
        item.created_at = datetime.utcnow()
        item.attributes = {}
        item.serial_numbers = []
        return item

    @pytest.fixture
    async def mock_stock_movement(self):
        """Create a mock stock movement for testing"""
        movement = StockMovement()
        movement.id = "test-movement-123"
        movement.inventory_item_id = "test-inventory-123"
        movement.product_id = "test-product-123"
        movement.movement_type = "inbound"
        movement.transaction_type = "purchase"
        movement.quantity = 50
        movement.unit_cost = Decimal("48.00")
        movement.total_cost = Decimal("2400.00")
        movement.stock_before = 50
        movement.stock_after = 100
        movement.status = "executed"
        movement.movement_date = datetime.utcnow()
        movement.created_at = datetime.utcnow()
        return movement

    @pytest.fixture
    async def mock_cycle_count(self):
        """Create a mock cycle count for testing"""
        count = CycleCount()
        count.id = "test-count-123"
        count.cycle_count_number = "CC-2025-001"
        count.warehouse_id = "test-warehouse-123"
        count.count_type = "full"
        count.scheduled_date = datetime.utcnow()
        count.status = "planned"
        count.total_items_planned = 100
        count.total_items_counted = 0
        count.total_discrepancies = 0
        count.created_at = datetime.utcnow()
        return count

    @pytest.mark.asyncio
    async def test_create_warehouse_success(self, mock_user):
        """Test successful warehouse creation"""
        with patch('app.api.v1.inventory_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.WarehouseCRUD') as mock_crud:
            
            # Setup mocks
            mock_warehouse = Warehouse()
            mock_warehouse.id = "new-warehouse-123"
            mock_warehouse.code = "WH002"
            mock_warehouse.name = "New Warehouse"
            
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_warehouse
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/warehouses",
                    json={
                        "code": "WH002",
                        "name": "New Warehouse",
                        "description": "Secondary storage facility",
                        "warehouse_type": "standard",
                        "address_line1": "456 Storage Ave",
                        "city": "Osaka",
                        "country": "Japan"
                    }
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["code"] == "WH002"
            assert data["name"] == "New Warehouse"

    @pytest.mark.asyncio
    async def test_list_warehouses_with_filters(self, mock_user, mock_warehouse):
        """Test warehouses list with filters"""
        with patch('app.api.v1.inventory_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.WarehouseCRUD') as mock_crud:
            
            # Setup mocks
            mock_warehouses = [mock_warehouse]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_multi.return_value = (mock_warehouses, 1)
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/warehouses?search=main&is_active=true&warehouse_type=standard")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            
            # Verify filters were passed correctly
            mock_crud_instance.get_multi.assert_called_once()
            call_args = mock_crud_instance.get_multi.call_args
            filters = call_args[1]["filters"]
            assert filters["search"] == "main"
            assert filters["is_active"] == True
            assert filters["warehouse_type"] == "standard"

    @pytest.mark.asyncio
    async def test_get_warehouse_by_id(self, mock_user, mock_warehouse):
        """Test get warehouse by ID"""
        with patch('app.api.v1.inventory_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.WarehouseCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_by_id.return_value = mock_warehouse
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/warehouses/{mock_warehouse.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == mock_warehouse.id
            assert data["code"] == mock_warehouse.code

    @pytest.mark.asyncio
    async def test_create_inventory_item_success(self, mock_user):
        """Test successful inventory item creation"""
        with patch('app.api.v1.inventory_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.InventoryItemCRUD') as mock_crud:
            
            # Setup mocks
            mock_item = InventoryItem()
            mock_item.id = "new-inventory-123"
            mock_item.product_id = "product-123"
            mock_item.warehouse_id = "warehouse-123"
            mock_item.quantity_available = 50
            
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_item
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/inventory",
                    json={
                        "product_id": "product-123",
                        "warehouse_id": "warehouse-123",
                        "quantity_available": 50,
                        "unit_cost": "25.00",
                        "quality_status": "good"
                    }
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["product_id"] == "product-123"

    @pytest.mark.asyncio
    async def test_list_inventory_items_with_filters(self, mock_user, mock_inventory_item):
        """Test inventory items list with advanced filters"""
        with patch('app.api.v1.inventory_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.InventoryItemCRUD') as mock_crud:
            
            # Setup mocks
            mock_items = [mock_inventory_item]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_multi.return_value = (mock_items, 1)
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    "/api/v1/inventory?warehouse_id=wh1&low_stock=true&quality_status=good"
                )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            
            # Verify filters were passed correctly
            mock_crud_instance.get_multi.assert_called_once()
            call_args = mock_crud_instance.get_multi.call_args
            filters = call_args[1]["filters"]
            assert filters["warehouse_id"] == "wh1"
            assert filters["low_stock"] == True
            assert filters["quality_status"] == "good"

    @pytest.mark.asyncio
    async def test_adjust_inventory_success(self, mock_user, mock_stock_movement):
        """Test successful inventory adjustment"""
        with patch('app.api.v1.inventory_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.InventoryItemCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.adjust_quantity.return_value = mock_stock_movement
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/inventory/test-inventory-123/adjust",
                    json={
                        "movement_type": "inbound",
                        "quantity": 25,
                        "unit_cost": "45.00",
                        "reason": "Purchase receipt"
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["movement_type"] == "inbound"
            assert data["quantity"] == 25

    @pytest.mark.asyncio
    async def test_adjust_inventory_insufficient_stock(self, mock_user):
        """Test inventory adjustment with insufficient stock"""
        with patch('app.api.v1.inventory_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.InventoryItemCRUD') as mock_crud:
            
            # Setup mocks
            from app.crud.inventory_extended_v30 import InsufficientStockError
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.adjust_quantity.side_effect = InsufficientStockError("Not enough inventory available")
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/inventory/test-inventory-123/adjust",
                    json={
                        "movement_type": "outbound",
                        "quantity": 200,
                        "reason": "Sale"
                    }
                )
            
            assert response.status_code == 400
            assert "Not enough inventory available" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_reserve_inventory_success(self, mock_user):
        """Test successful inventory reservation"""
        with patch('app.api.v1.inventory_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.InventoryItemCRUD') as mock_crud:
            
            # Setup mocks
            from app.models.inventory_extended import InventoryReservation
            mock_reservation = InventoryReservation()
            mock_reservation.id = "reservation-123"
            mock_reservation.quantity_reserved = 10
            
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.reserve_inventory.return_value = mock_reservation
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/inventory/reserve",
                    json={
                        "inventory_item_id": "inventory-123",
                        "quantity_reserved": 10,
                        "reservation_type": "sales_order",
                        "reference_type": "sales_order",
                        "reference_id": "SO-001"
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["quantity_reserved"] == 10

    @pytest.mark.asyncio
    async def test_get_inventory_summary(self, mock_user):
        """Test get inventory summary"""
        with patch('app.api.v1.inventory_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.InventoryItemCRUD') as mock_crud:
            
            # Setup mocks
            mock_summary = [
                {
                    "product_id": "product-1",
                    "total_available": 100,
                    "total_reserved": 10,
                    "total_allocated": 5,
                    "locations_count": 2
                }
            ]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_stock_summary.return_value = mock_summary
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/inventory/summary?product_id=product-1")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["product_id"] == "product-1"

    @pytest.mark.asyncio
    async def test_get_inventory_valuation(self, mock_user):
        """Test get inventory valuation"""
        with patch('app.api.v1.inventory_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.InventoryItemCRUD') as mock_crud:
            
            # Setup mocks
            mock_valuation = {
                "total_value": Decimal("50000.00"),
                "by_warehouse": {"Main Warehouse": Decimal("30000.00"), "Secondary": Decimal("20000.00")},
                "valuation_date": datetime.utcnow()
            }
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_inventory_valuation.return_value = mock_valuation
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/inventory/valuation")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_value" in data
            assert "by_warehouse" in data

    @pytest.mark.asyncio
    async def test_create_cycle_count_success(self, mock_user, mock_cycle_count):
        """Test successful cycle count creation"""
        with patch('app.api.v1.inventory_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.CycleCountCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_cycle_count
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/cycle-counts",
                    json={
                        "cycle_count_number": "CC-2025-001",
                        "warehouse_id": "warehouse-123",
                        "count_type": "full",
                        "scheduled_date": "2025-01-25T10:00:00Z"
                    }
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["cycle_count_number"] == "CC-2025-001"

    @pytest.mark.asyncio
    async def test_update_cycle_count_item(self, mock_user):
        """Test cycle count item update"""
        with patch('app.api.v1.inventory_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.CycleCountCRUD') as mock_crud:
            
            # Setup mocks
            from app.models.inventory_extended import CycleCountItem
            mock_count_item = CycleCountItem()
            mock_count_item.id = "count-item-123"
            mock_count_item.counted_quantity = 95
            mock_count_item.variance_quantity = -5
            
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.update_count_item.return_value = mock_count_item
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.put(
                    "/api/v1/cycle-counts/count-123/items/count-item-123",
                    json={
                        "counted_quantity": 95,
                        "notes": "Minor shortage found"
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["counted_quantity"] == 95

    @pytest.mark.asyncio
    async def test_get_stock_alerts(self, mock_user):
        """Test get stock alerts"""
        with patch('app.api.v1.inventory_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.StockAlertCRUD') as mock_crud:
            
            # Setup mocks
            mock_alerts = []
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_active_alerts.return_value = mock_alerts
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/alerts/stock?limit=20")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_acknowledge_stock_alert(self, mock_user):
        """Test acknowledge stock alert"""
        with patch('app.api.v1.inventory_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.StockAlertCRUD') as mock_crud:
            
            # Setup mocks
            mock_alert = StockAlert()
            mock_alert.id = "alert-123"
            mock_alert.status = "acknowledged"
            
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.acknowledge_alert.return_value = mock_alert
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post("/api/v1/alerts/stock/alert-123/acknowledge")
            
            assert response.status_code == 200
            data = response.json()
            assert "acknowledged successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_generate_stock_alerts(self, mock_user):
        """Test generate stock alerts"""
        with patch('app.api.v1.inventory_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db, \
             patch('app.crud.inventory_extended_v30.StockAlertCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create_low_stock_alerts.return_value = 5
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post("/api/v1/alerts/stock/generate")
            
            assert response.status_code == 200
            data = response.json()
            assert "5 alerts created" in data["message"]

    @pytest.mark.asyncio
    async def test_get_inventory_statistics(self, mock_user):
        """Test get inventory statistics"""
        with patch('app.api.v1.inventory_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.inventory_complete_v30.get_db') as mock_db:
            
            # Setup mocks for direct database queries
            mock_db.return_value.query.return_value.scalar.return_value = 5
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/inventory/stats/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_warehouses" in data
            assert "total_inventory_items" in data