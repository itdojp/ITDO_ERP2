"""
Tests for Inventory Integration System - CC02 v62.0
Comprehensive test suite for real-time tracking, auto-ordering, analytics, shipping integration, and warehouse management
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, StockMovement, Warehouse, MovementType, InventoryStatus
from app.models.inventory_integration import (
    AutoOrder,
    AutoOrderRule,
    AutoOrderStatus,
    InventoryAnalytics,
    RealtimeInventoryAlert,
    ShippingInventorySync,
    AlertType,
    ShipmentStatus,
)
from app.schemas.inventory_integration import (
    AutoOrderRuleCreate,
    RealtimeInventoryUpdate,
    ShippingInventorySyncCreate,
)
from app.services.inventory_integration_service import (
    RealtimeInventoryTrackingService,
    AutoOrderingService,
    InventoryAnalyticsService,
    ShippingInventoryIntegrationService,
)
from app.services.warehouse_management_service import WarehouseOptimizationService


class TestRealtimeInventoryTrackingService:
    """Test suite for real-time inventory tracking service."""
    
    @pytest.fixture
    async def tracking_service(self, db_session: AsyncSession):
        """Create tracking service instance."""
        return RealtimeInventoryTrackingService(db_session)
    
    @pytest.fixture
    async def sample_warehouse(self, db_session: AsyncSession, test_organization):
        """Create sample warehouse for testing."""
        warehouse = Warehouse(
            code="WH001",
            name="Test Warehouse",
            organization_id=test_organization.id,
            storage_capacity=Decimal("10000"),
            is_default=True,
            created_by=1
        )
        db_session.add(warehouse)
        await db_session.commit()
        await db_session.refresh(warehouse)
        return warehouse
    
    @pytest.fixture
    async def sample_inventory_item(self, db_session: AsyncSession, sample_warehouse, test_organization):
        """Create sample inventory item for testing."""
        from app.models.product import Product
        
        # Create a test product first
        product = Product(
            code="PROD001",
            name="Test Product",
            organization_id=test_organization.id,
            created_by=1
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        inventory_item = InventoryItem(
            product_id=product.id,
            warehouse_id=sample_warehouse.id,
            organization_id=test_organization.id,
            quantity_on_hand=Decimal("100"),
            quantity_reserved=Decimal("10"),
            quantity_available=Decimal("90"),
            minimum_level=Decimal("20"),
            reorder_point=Decimal("25"),
            created_by=1
        )
        db_session.add(inventory_item)
        await db_session.commit()
        await db_session.refresh(inventory_item)
        return inventory_item
    
    async def test_get_realtime_snapshot(
        self, 
        tracking_service: RealtimeInventoryTrackingService,
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Test getting real-time inventory snapshot."""
        snapshot = await tracking_service.get_realtime_snapshot(
            sample_inventory_item.product_id,
            sample_inventory_item.warehouse_id,
            test_organization.id
        )
        
        assert snapshot.product_id == sample_inventory_item.product_id
        assert snapshot.warehouse_id == sample_inventory_item.warehouse_id
        assert snapshot.current_stock == sample_inventory_item.quantity_on_hand
        assert snapshot.reserved_stock == sample_inventory_item.quantity_reserved
        assert snapshot.available_stock == sample_inventory_item.quantity_available
    
    async def test_process_realtime_update_inbound(
        self,
        tracking_service: RealtimeInventoryTrackingService,
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Test processing inbound inventory update."""
        update = RealtimeInventoryUpdate(
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            quantity_change=Decimal("50"),
            movement_type=MovementType.IN.value,
            timestamp=datetime.utcnow(),
            user_id=1,
            reason="Purchase order receipt"
        )
        
        snapshot = await tracking_service.process_realtime_update(update, test_organization.id)
        
        assert snapshot.current_stock == Decimal("150")  # 100 + 50
        assert snapshot.available_stock == Decimal("140")  # 150 - 10 reserved
    
    async def test_process_realtime_update_outbound(
        self,
        tracking_service: RealtimeInventoryTrackingService,
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Test processing outbound inventory update."""
        update = RealtimeInventoryUpdate(
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            quantity_change=Decimal("30"),
            movement_type=MovementType.OUT.value,
            timestamp=datetime.utcnow(),
            user_id=1,
            reason="Sales order fulfillment"
        )
        
        snapshot = await tracking_service.process_realtime_update(update, test_organization.id)
        
        assert snapshot.current_stock == Decimal("70")  # 100 - 30
        assert snapshot.available_stock == Decimal("60")  # 70 - 10 reserved
    
    async def test_low_stock_alert_creation(
        self,
        tracking_service: RealtimeInventoryTrackingService,
        sample_inventory_item: InventoryItem,
        test_organization,
        db_session: AsyncSession
    ):
        """Test that low stock alerts are created when needed."""
        # Create update that brings stock below minimum level
        update = RealtimeInventoryUpdate(
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            quantity_change=Decimal("85"),  # This will bring available stock to 5, below minimum of 20
            movement_type=MovementType.OUT.value,
            timestamp=datetime.utcnow(),
            user_id=1,
            reason="Large sales order"
        )
        
        await tracking_service.process_realtime_update(update, test_organization.id)
        
        # Check that alert was created
        from sqlalchemy import select
        alert_query = select(RealtimeInventoryAlert).where(
            RealtimeInventoryAlert.inventory_item_id == sample_inventory_item.id
        )
        result = await db_session.execute(alert_query)
        alerts = result.scalars().all()
        
        assert len(alerts) > 0
        low_stock_alert = next((a for a in alerts if a.alert_type == AlertType.LOW_STOCK.value), None)
        assert low_stock_alert is not None
        assert low_stock_alert.severity == "high"


class TestAutoOrderingService:
    """Test suite for auto-ordering service."""
    
    @pytest.fixture
    async def ordering_service(self, db_session: AsyncSession):
        """Create auto-ordering service instance."""
        return AutoOrderingService(db_session)
    
    @pytest.fixture
    async def sample_auto_order_rule(
        self, 
        db_session: AsyncSession, 
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Create sample auto order rule for testing."""
        rule_data = AutoOrderRuleCreate(
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            rule_name="Test Auto Order Rule",
            trigger_level=Decimal("25"),
            order_quantity=Decimal("100"),
            supplier_unit_cost=Decimal("10.50"),
            lead_time_days=7
        )
        
        rule = AutoOrderRule(
            organization_id=test_organization.id,
            created_by=1,
            **rule_data.model_dump()
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)
        return rule
    
    async def test_create_auto_order_rule(
        self,
        ordering_service: AutoOrderingService,
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Test creating auto order rule."""
        rule_data = AutoOrderRuleCreate(
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            rule_name="New Auto Order Rule",
            trigger_level=Decimal("30"),
            order_quantity=Decimal("200"),
            supplier_unit_cost=Decimal("12.00"),
            lead_time_days=5
        )
        
        rule = await ordering_service.create_auto_order_rule(
            rule_data, test_organization.id, 1
        )
        
        assert rule.rule_name == "New Auto Order Rule"
        assert rule.trigger_level == Decimal("30")
        assert rule.order_quantity == Decimal("200")
        assert rule.is_active is True
    
    async def test_check_and_process_auto_orders(
        self,
        ordering_service: AutoOrderingService,
        sample_auto_order_rule: AutoOrderRule,
        sample_inventory_item: InventoryItem,
        test_organization,
        db_session: AsyncSession
    ):
        """Test checking and processing auto orders."""
        # Reduce inventory below trigger level
        sample_inventory_item.quantity_available = Decimal("20")  # Below trigger of 25
        await db_session.commit()
        
        orders = await ordering_service.check_and_process_auto_orders(test_organization.id)
        
        assert len(orders) == 1
        order = orders[0]
        assert order.order_rule_id == sample_auto_order_rule.id
        assert order.quantity_ordered == sample_auto_order_rule.order_quantity
        assert order.status == AutoOrderStatus.PENDING.value
    
    async def test_approve_auto_order(
        self,
        ordering_service: AutoOrderingService,
        sample_auto_order_rule: AutoOrderRule,
        test_organization,
        db_session: AsyncSession
    ):
        """Test approving auto order."""
        # Create a pending auto order
        order = AutoOrder(
            order_number="AO-TEST-001",
            order_rule_id=sample_auto_order_rule.id,
            product_id=sample_auto_order_rule.product_id,
            warehouse_id=sample_auto_order_rule.warehouse_id,
            organization_id=test_organization.id,
            quantity_ordered=Decimal("100"),
            status=AutoOrderStatus.PENDING.value,
            requires_approval=True,
            created_by=1
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        
        approved_order = await ordering_service.approve_auto_order(
            order.id, 2, "Approved for processing"
        )
        
        assert approved_order.status == AutoOrderStatus.APPROVED.value
        assert approved_order.approved_by == 2
        assert approved_order.approval_notes == "Approved for processing"
        assert approved_order.approval_date is not None


class TestInventoryAnalyticsService:
    """Test suite for inventory analytics service."""
    
    @pytest.fixture
    async def analytics_service(self, db_session: AsyncSession):
        """Create analytics service instance."""
        return InventoryAnalyticsService(db_session)
    
    @pytest.fixture
    async def sample_stock_movements(
        self,
        db_session: AsyncSession,
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Create sample stock movements for analytics testing."""
        movements = []
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(10):
            movement = StockMovement(
                transaction_number=f"TXN-{i:03d}",
                inventory_item_id=sample_inventory_item.id,
                product_id=sample_inventory_item.product_id,
                warehouse_id=sample_inventory_item.warehouse_id,
                organization_id=test_organization.id,
                movement_type=MovementType.OUT.value,
                movement_date=base_date + timedelta(days=i * 3),
                quantity=Decimal("-10"),
                unit_cost=Decimal("5.00"),
                total_cost=Decimal("-50.00"),
                created_by=1
            )
            movements.append(movement)
            db_session.add(movement)
        
        await db_session.commit()
        return movements
    
    async def test_generate_analytics(
        self,
        analytics_service: InventoryAnalyticsService,
        sample_inventory_item: InventoryItem,
        sample_stock_movements,
        test_organization
    ):
        """Test generating inventory analytics."""
        analytics = await analytics_service.generate_analytics(
            sample_inventory_item.product_id,
            sample_inventory_item.warehouse_id,
            test_organization.id,
            30
        )
        
        assert analytics.product_id == sample_inventory_item.product_id
        assert analytics.warehouse_id == sample_inventory_item.warehouse_id
        assert analytics.total_outbound == Decimal("100")  # 10 movements * 10 quantity
        assert analytics.average_daily_usage > Decimal("0")
        assert analytics.abc_classification is not None


class TestShippingInventoryIntegrationService:
    """Test suite for shipping inventory integration service."""
    
    @pytest.fixture
    async def shipping_service(self, db_session: AsyncSession):
        """Create shipping integration service instance."""
        return ShippingInventoryIntegrationService(db_session)
    
    async def test_create_shipping_sync(
        self,
        shipping_service: ShippingInventoryIntegrationService,
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Test creating shipping sync record."""
        sync_data = ShippingInventorySyncCreate(
            sync_id="SYNC-001",
            shipment_id="SHIP-001",
            tracking_number="TRK123456",
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            inventory_item_id=sample_inventory_item.id,
            quantity_shipped=Decimal("25"),
            carrier_name="Test Carrier"
        )
        
        sync_record = await shipping_service.create_shipping_sync(sync_data, test_organization.id)
        
        assert sync_record.sync_id == "SYNC-001"
        assert sync_record.shipment_id == "SHIP-001"
        assert sync_record.quantity_shipped == Decimal("25")
        assert sync_record.inventory_reserved_at_ship is True
    
    async def test_update_shipment_status_to_shipped(
        self,
        shipping_service: ShippingInventoryIntegrationService,
        sample_inventory_item: InventoryItem,
        test_organization,
        db_session: AsyncSession
    ):
        """Test updating shipment status to shipped."""
        # Create shipping sync record
        sync_record = ShippingInventorySync(
            sync_id="SYNC-002",
            shipment_id="SHIP-002",
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            inventory_item_id=sample_inventory_item.id,
            organization_id=test_organization.id,
            quantity_shipped=Decimal("30"),
            status=ShipmentStatus.PENDING.value,
            inventory_reserved_at_ship=True,
            created_by=1
        )
        db_session.add(sync_record)
        await db_session.commit()
        await db_session.refresh(sync_record)
        
        # Store original inventory quantity
        original_quantity = sample_inventory_item.quantity_on_hand
        
        # Update status to shipped
        updated_sync = await shipping_service.update_shipment_status(
            "SYNC-002", ShipmentStatus.SHIPPED.value, None, test_organization.id
        )
        
        assert updated_sync.status == ShipmentStatus.SHIPPED.value
        assert updated_sync.inventory_reduced_at_ship is True
        
        # Verify inventory was reduced
        await db_session.refresh(sample_inventory_item)
        assert sample_inventory_item.quantity_on_hand == original_quantity - Decimal("30")


class TestWarehouseOptimizationService:
    """Test suite for warehouse optimization service."""
    
    @pytest.fixture
    async def optimization_service(self, db_session: AsyncSession):
        """Create warehouse optimization service instance."""
        return WarehouseOptimizationService(db_session)
    
    async def test_get_warehouse_performance_metrics(
        self,
        optimization_service: WarehouseOptimizationService,
        sample_warehouse: Warehouse,
        test_organization
    ):
        """Test getting warehouse performance metrics."""
        metrics = await optimization_service.get_warehouse_performance_metrics(
            sample_warehouse.id, test_organization.id, 30
        )
        
        assert metrics.warehouse_id == sample_warehouse.id
        assert metrics.warehouse_name == sample_warehouse.name
        assert metrics.total_items >= 0
        assert metrics.total_stock_value >= Decimal("0")
    
    async def test_optimize_warehouse_layout(
        self,
        optimization_service: WarehouseOptimizationService,
        sample_warehouse: Warehouse,
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Test warehouse layout optimization."""
        optimization = await optimization_service.optimize_warehouse_layout(
            sample_warehouse.id, test_organization.id
        )
        
        assert optimization["warehouse_id"] == sample_warehouse.id
        assert "layout_recommendations" in optimization
        assert "efficiency_gains" in optimization
        assert "high_velocity_zone" in optimization["layout_recommendations"]
        assert "medium_velocity_zone" in optimization["layout_recommendations"]
        assert "low_velocity_zone" in optimization["layout_recommendations"]
    
    async def test_calculate_optimal_stock_levels(
        self,
        optimization_service: WarehouseOptimizationService,
        sample_warehouse: Warehouse,
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Test calculating optimal stock levels."""
        optimization = await optimization_service.calculate_optimal_stock_levels(
            sample_warehouse.id, test_organization.id
        )
        
        assert optimization["warehouse_id"] == sample_warehouse.id
        assert "optimizations" in optimization
        assert "summary" in optimization
        assert optimization["total_products_analyzed"] >= 0
    
    async def test_generate_warehouse_capacity_report(
        self,
        optimization_service: WarehouseOptimizationService,
        sample_warehouse: Warehouse,
        test_organization
    ):
        """Test generating warehouse capacity report."""
        report = await optimization_service.generate_warehouse_capacity_report(
            sample_warehouse.id, test_organization.id
        )
        
        assert report["warehouse_id"] == sample_warehouse.id
        assert report["warehouse_name"] == sample_warehouse.name
        assert "capacity_metrics" in report
        assert "zone_breakdown" in report
        assert "recommendations" in report
        assert report["capacity_metrics"]["total_capacity"] > 0


class TestInventoryIntegrationAPI:
    """Test suite for inventory integration API endpoints."""
    
    async def test_get_realtime_snapshot_endpoint(
        self,
        async_client,
        sample_inventory_item: InventoryItem,
        auth_headers
    ):
        """Test real-time snapshot API endpoint."""
        response = await async_client.get(
            f"/api/v1/inventory-integration/realtime/snapshot/{sample_inventory_item.product_id}/{sample_inventory_item.warehouse_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == sample_inventory_item.product_id
        assert data["warehouse_id"] == sample_inventory_item.warehouse_id
    
    async def test_process_realtime_update_endpoint(
        self,
        async_client,
        sample_inventory_item: InventoryItem,
        auth_headers
    ):
        """Test real-time update API endpoint."""
        update_data = {
            "product_id": sample_inventory_item.product_id,
            "warehouse_id": sample_inventory_item.warehouse_id,
            "quantity_change": 25,
            "movement_type": "in",
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "Test receipt"
        }
        
        response = await async_client.post(
            "/api/v1/inventory-integration/realtime/update",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == sample_inventory_item.product_id
        assert data["current_stock"] == 125  # 100 + 25
    
    async def test_get_dashboard_stats_endpoint(
        self,
        async_client,
        auth_headers
    ):
        """Test dashboard stats API endpoint."""
        response = await async_client.get(
            "/api/v1/inventory-integration/dashboard/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data
        assert "total_warehouses" in data
        assert "total_stock_value" in data
        assert "active_alerts" in data
    
    async def test_health_check_endpoint(self, async_client):
        """Test health check endpoint."""
        response = await async_client.get("/api/v1/inventory-integration/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "CC02 v62.0"
        assert data["system"] == "Inventory Integration API"


# Fixtures for pytest
@pytest.fixture
async def test_organization(db_session: AsyncSession):
    """Create test organization."""
    from app.models.organization import Organization
    
    org = Organization(
        name="Test Organization",
        code="TESTORG",
        created_by=1
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def auth_headers(test_user):
    """Create authentication headers for testing."""
    # This would typically create a JWT token for the test user
    return {"Authorization": "Bearer test-token"}


# Performance and load testing
class TestPerformance:
    """Performance tests for inventory integration system."""
    
    @pytest.mark.asyncio
    async def test_bulk_update_performance(
        self,
        async_client,
        auth_headers,
        sample_inventory_item: InventoryItem
    ):
        """Test performance of bulk inventory updates."""
        import time
        
        # Create 100 update records
        updates = []
        for i in range(100):
            updates.append({
                "product_id": sample_inventory_item.product_id,
                "warehouse_id": sample_inventory_item.warehouse_id,
                "quantity_change": 1,
                "movement_type": "in",
                "timestamp": datetime.utcnow().isoformat(),
                "reason": f"Bulk test update {i}"
            })
        
        bulk_data = {
            "updates": updates,
            "batch_id": "PERF-TEST-001",
            "validate_before_processing": True
        }
        
        start_time = time.time()
        response = await async_client.post(
            "/api/v1/inventory-integration/realtime/bulk-update",
            json=bulk_data,
            headers=auth_headers
        )
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 100
        assert data["successful_items"] >= 95  # Allow for some failures
        
        # Performance assertion - should complete within 10 seconds
        processing_time = end_time - start_time
        assert processing_time < 10.0, f"Bulk update took {processing_time} seconds, should be < 10"
    
    @pytest.mark.asyncio
    async def test_analytics_generation_performance(
        self,
        async_client,
        auth_headers,
        sample_inventory_item: InventoryItem
    ):
        """Test performance of analytics generation."""
        import time
        
        start_time = time.time()
        response = await async_client.post(
            f"/api/v1/inventory-integration/analytics/generate/{sample_inventory_item.product_id}/{sample_inventory_item.warehouse_id}",
            headers=auth_headers
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Performance assertion - analytics should generate within 5 seconds
        processing_time = end_time - start_time
        assert processing_time < 5.0, f"Analytics generation took {processing_time} seconds, should be < 5"


# Integration tests
class TestIntegration:
    """Integration tests for the complete inventory management workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_inventory_workflow(
        self,
        db_session: AsyncSession,
        sample_inventory_item: InventoryItem,
        test_organization
    ):
        """Test complete inventory management workflow."""
        # 1. Real-time tracking
        tracking_service = RealtimeInventoryTrackingService(db_session)
        
        update = RealtimeInventoryUpdate(
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            quantity_change=Decimal("50"),
            movement_type=MovementType.OUT.value,
            timestamp=datetime.utcnow(),
            user_id=1,
            reason="Sales order"
        )
        
        snapshot = await tracking_service.process_realtime_update(update, test_organization.id)
        assert snapshot.current_stock == Decimal("50")  # 100 - 50
        
        # 2. Auto-ordering
        ordering_service = AutoOrderingService(db_session)
        
        rule_data = AutoOrderRuleCreate(
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            rule_name="Integration Test Rule",
            trigger_level=Decimal("60"),  # Above current stock of 50
            order_quantity=Decimal("100")
        )
        
        rule = await ordering_service.create_auto_order_rule(
            rule_data, test_organization.id, 1
        )
        
        orders = await ordering_service.check_and_process_auto_orders(test_organization.id)
        assert len(orders) == 1
        
        # 3. Analytics
        analytics_service = InventoryAnalyticsService(db_session)
        analytics = await analytics_service.generate_analytics(
            sample_inventory_item.product_id,
            sample_inventory_item.warehouse_id,
            test_organization.id
        )
        
        assert analytics.total_outbound == Decimal("50")
        
        # 4. Shipping integration
        shipping_service = ShippingInventoryIntegrationService(db_session)
        
        sync_data = ShippingInventorySyncCreate(
            sync_id="INT-TEST-001",
            shipment_id="SHIP-INT-001",
            product_id=sample_inventory_item.product_id,
            warehouse_id=sample_inventory_item.warehouse_id,
            inventory_item_id=sample_inventory_item.id,
            quantity_shipped=Decimal("20")
        )
        
        sync_record = await shipping_service.create_shipping_sync(sync_data, test_organization.id)
        assert sync_record.inventory_reserved_at_ship is True
        
        # 5. Warehouse optimization
        optimization_service = WarehouseOptimizationService(db_session)
        
        metrics = await optimization_service.get_warehouse_performance_metrics(
            sample_inventory_item.warehouse_id, test_organization.id
        )
        
        assert metrics.warehouse_id == sample_inventory_item.warehouse_id