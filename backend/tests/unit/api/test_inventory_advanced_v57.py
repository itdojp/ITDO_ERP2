"""
Tests for CC02 v57.0 Advanced Inventory Management API
Comprehensive test suite for inventory transactions, reservations, and alerts
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.inventory_advanced_v57 import (
    TransactionType, TransactionStatus, AlertType, AlertSeverity,
    InventoryTransactionRequest, BulkTransactionRequest, ReservationRequest,
    InventoryAdjustmentRequest, InventoryTransactionManager, ReservationManager,
    InventoryTransactionResponse, InventoryLevelResponse, ReservationResponse
)
from app.models.inventory import InventoryItem, InventoryTransaction, InventoryAlert
from app.models.product import Product
from app.models.user import User
from app.core.exceptions import BusinessLogicError, NotFoundError

# Test Fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.begin.return_value.__aenter__ = AsyncMock()
    session.begin.return_value.__aexit__ = AsyncMock()
    return session

@pytest.fixture
def sample_product():
    """Sample product for testing"""
    return Product(
        id=uuid4(),
        name="Test Widget",
        sku="TW-001",
        description="Test product for inventory management",
        price=Decimal('29.99'),
        cost=Decimal('15.00'),
        created_at=datetime.utcnow()
    )

@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow()
    )

@pytest.fixture
def sample_inventory_item(sample_product):
    """Sample inventory item"""
    return InventoryItem(
        id=uuid4(),
        product_id=sample_product.id,
        location="MAIN_WAREHOUSE",
        current_quantity=100,
        available_quantity=80,
        reserved_quantity=20,
        in_transit_quantity=0,
        reorder_point=25,
        max_stock_level=500,
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

@pytest.fixture
def transaction_manager(mock_db_session):
    """Create transaction manager with mocked database"""
    return InventoryTransactionManager(mock_db_session)

@pytest.fixture
def reservation_manager(mock_db_session):
    """Create reservation manager with mocked database"""
    return ReservationManager(mock_db_session)

# Unit Tests for InventoryTransactionManager
class TestInventoryTransactionManager:
    
    @pytest.mark.asyncio
    async def test_execute_transaction_inbound_success(self, transaction_manager, mock_db_session, sample_product, sample_user):
        """Test successful inbound transaction execution"""
        
        # Mock product lookup
        product_result = MagicMock()
        product_result.scalar_one_or_none.return_value = sample_product
        mock_db_session.execute.return_value = product_result
        
        # Mock inventory item lookup
        inventory_result = MagicMock()
        inventory_result.scalar_one_or_none.return_value = None  # Will create new item
        
        # Set up multiple execute calls for different queries
        mock_db_session.execute.side_effect = [
            product_result,    # Product lookup
            inventory_result,  # Inventory item lookup
            MagicMock(),      # Any other queries
        ]
        
        # Mock flush and commit
        mock_db_session.flush = AsyncMock()
        mock_db_session.add = MagicMock()
        
        # Create transaction request
        request = InventoryTransactionRequest(
            product_id=sample_product.id,
            transaction_type=TransactionType.INBOUND,
            quantity=50,
            reason="Stock replenishment",
            to_location="MAIN_WAREHOUSE"
        )
        
        # Execute transaction
        result = await transaction_manager.execute_transaction(request, sample_user.id)
        
        # Assertions
        assert isinstance(result, InventoryTransactionResponse)
        assert result.transaction_type == TransactionType.INBOUND
        assert result.quantity == 50
        assert result.product_name == sample_product.name
        assert result.created_by == str(sample_user.id)
        
        # Verify database interactions
        assert mock_db_session.execute.call_count >= 2
        mock_db_session.add.assert_called()
        mock_db_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_execute_transaction_outbound_insufficient_stock(self, transaction_manager, mock_db_session, sample_product, sample_user):
        """Test outbound transaction with insufficient stock"""
        
        # Mock product lookup
        product_result = MagicMock()
        product_result.scalar_one_or_none.return_value = sample_product
        
        # Mock stock availability check - insufficient stock
        stock_result = MagicMock()
        stock_result.scalar.return_value = 10  # Only 10 available, but requesting 50
        
        mock_db_session.execute.side_effect = [
            product_result,    # Product lookup
            stock_result,      # Stock availability check
        ]
        
        # Create outbound transaction request
        request = InventoryTransactionRequest(
            product_id=sample_product.id,
            transaction_type=TransactionType.OUTBOUND,
            quantity=50,
            reason="Customer order",
            from_location="MAIN_WAREHOUSE"
        )
        
        # Execute transaction - should raise BusinessLogicError
        with pytest.raises(BusinessLogicError, match="Insufficient stock"):
            await transaction_manager.execute_transaction(request, sample_user.id)

    @pytest.mark.asyncio
    async def test_execute_transaction_product_not_found(self, transaction_manager, mock_db_session, sample_user):
        """Test transaction with non-existent product"""
        
        # Mock product lookup - product not found
        product_result = MagicMock()
        product_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = product_result
        
        request = InventoryTransactionRequest(
            product_id=uuid4(),
            transaction_type=TransactionType.INBOUND,
            quantity=25,
            reason="Test transaction"
        )
        
        # Execute transaction - should raise NotFoundError
        with pytest.raises(NotFoundError, match="Product .* not found"):
            await transaction_manager.execute_transaction(request, sample_user.id)

    @pytest.mark.asyncio
    async def test_execute_bulk_transactions_success(self, transaction_manager, mock_db_session, sample_product, sample_user):
        """Test successful bulk transaction execution"""
        
        # Mock product lookup
        product_result = MagicMock()
        product_result.scalar_one_or_none.return_value = sample_product
        
        # Mock stock availability (high enough for all transactions)
        stock_result = MagicMock()
        stock_result.scalar.return_value = 1000
        
        # Mock inventory item lookup
        inventory_result = MagicMock()
        inventory_result.scalar_one_or_none.return_value = None
        
        mock_db_session.execute.side_effect = [
            product_result, stock_result, inventory_result,  # First transaction
            product_result, stock_result, inventory_result,  # Second transaction
        ] * 3  # Repeat for validation and execution phases
        
        mock_db_session.flush = AsyncMock()
        mock_db_session.add = MagicMock()
        
        # Create bulk transaction request
        requests = [
            InventoryTransactionRequest(
                product_id=sample_product.id,
                transaction_type=TransactionType.INBOUND,
                quantity=25,
                reason="Bulk replenishment 1"
            ),
            InventoryTransactionRequest(
                product_id=sample_product.id,
                transaction_type=TransactionType.INBOUND,
                quantity=30,
                reason="Bulk replenishment 2"
            )
        ]
        
        # Execute bulk transactions
        results = await transaction_manager.execute_bulk_transactions(requests, sample_user.id, "BULK-001")
        
        # Assertions
        assert len(results) == 2
        assert all(isinstance(r, InventoryTransactionResponse) for r in results)
        assert results[0].quantity == 25
        assert results[1].quantity == 30
        
        # Verify database interactions
        assert mock_db_session.add.call_count >= 2
        assert mock_db_session.flush.call_count >= 2

    @pytest.mark.asyncio
    async def test_create_alert_low_stock(self, transaction_manager, mock_db_session):
        """Test creation of low stock alert"""
        
        product_id = uuid4()
        
        # Mock existing alert check
        existing_alert_result = MagicMock()
        existing_alert_result.scalar_one_or_none.return_value = None  # No existing alert
        mock_db_session.execute.return_value = existing_alert_result
        
        mock_db_session.add = MagicMock()
        mock_db_session.flush = AsyncMock()
        
        # Create alert data
        alert_data = {
            'type': AlertType.LOW_STOCK,
            'severity': AlertSeverity.HIGH,
            'message': "Stock level is 5, below reorder point 25",
            'current_value': Decimal('5'),
            'threshold_value': Decimal('25')
        }
        
        # Execute alert creation
        await transaction_manager._create_alert(product_id, alert_data)
        
        # Verify alert was created
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
        
        # Verify alert properties
        created_alert = mock_db_session.add.call_args[0][0]
        assert isinstance(created_alert, InventoryAlert)
        assert created_alert.product_id == product_id
        assert created_alert.alert_type == AlertType.LOW_STOCK.value
        assert created_alert.severity == AlertSeverity.HIGH.value

    @pytest.mark.asyncio
    async def test_process_location_transfer(self, transaction_manager, mock_db_session, sample_product):
        """Test location transfer processing"""
        
        # Mock inventory items for both locations
        from_item = MagicMock()
        from_item.current_quantity = 100
        from_item.available_quantity = 80
        
        to_item = MagicMock()
        to_item.current_quantity = 50
        to_item.available_quantity = 50
        
        # Mock get_or_create_inventory_item calls
        with patch.object(transaction_manager, '_get_or_create_inventory_item', side_effect=[from_item, to_item]):
            mock_db_session.flush = AsyncMock()
            
            # Create transfer request
            request = InventoryTransactionRequest(
                product_id=sample_product.id,
                transaction_type=TransactionType.TRANSFER,
                quantity=20,
                from_location="WAREHOUSE_A",
                to_location="WAREHOUSE_B",
                reason="Location transfer"
            )
            
            # Execute location transfer
            await transaction_manager._process_location_transfer(request)
            
            # Verify quantity changes
            assert from_item.current_quantity == 80  # 100 - 20
            assert from_item.available_quantity == 60  # 80 - 20
            assert to_item.current_quantity == 70     # 50 + 20
            assert to_item.available_quantity == 70   # 50 + 20
            
            mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_transfer_missing_locations(self, transaction_manager, sample_product):
        """Test transfer without required locations"""
        
        request = InventoryTransactionRequest(
            product_id=sample_product.id,
            transaction_type=TransactionType.TRANSFER,
            quantity=20,
            from_location=None,  # Missing from_location
            to_location="WAREHOUSE_B",
            reason="Transfer test"
        )
        
        with pytest.raises(ValueError, match="Both from_location and to_location required for transfers"):
            await transaction_manager._process_location_transfer(request)

# Unit Tests for ReservationManager
class TestReservationManager:
    
    @pytest.mark.asyncio
    async def test_create_reservation_success(self, reservation_manager, mock_db_session, sample_product, sample_user):
        """Test successful reservation creation"""
        
        # Mock stock availability check
        stock_result = MagicMock()
        stock_result.scalar.return_value = 100  # Sufficient stock
        mock_db_session.execute.return_value = stock_result
        
        # Mock transaction manager execution
        with patch('app.api.v1.inventory_advanced_v57.InventoryTransactionManager') as mock_tm:
            mock_tm_instance = mock_tm.return_value
            mock_tm_instance.execute_transaction = AsyncMock()
            
            request = ReservationRequest(
                product_id=sample_product.id,
                quantity=25,
                reserved_for="ORDER-12345",
                priority=5,
                notes="Rush order reservation"
            )
            
            # Execute reservation
            result = await reservation_manager.create_reservation(request, sample_user.id)
            
            # Assertions
            assert isinstance(result, ReservationResponse)
            assert result.product_id == sample_product.id
            assert result.quantity == 25
            assert result.reserved_for == "ORDER-12345"
            assert result.priority == 5
            assert result.status == "active"
            
            # Verify transaction manager was called
            mock_tm_instance.execute_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_reservation_insufficient_stock(self, reservation_manager, mock_db_session, sample_product, sample_user):
        """Test reservation creation with insufficient stock"""
        
        # Mock stock availability check - insufficient stock
        stock_result = MagicMock()
        stock_result.scalar.return_value = 10  # Only 10 available, but requesting 25
        mock_db_session.execute.return_value = stock_result
        
        request = ReservationRequest(
            product_id=sample_product.id,
            quantity=25,
            reserved_for="ORDER-12345"
        )
        
        # Execute reservation - should raise BusinessLogicError
        with pytest.raises(BusinessLogicError, match="Insufficient stock for reservation"):
            await reservation_manager.create_reservation(request, sample_user.id)

# API Endpoint Tests
class TestInventoryAdvancedAPI:
    
    def test_transaction_request_validation(self):
        """Test transaction request validation"""
        
        product_id = uuid4()
        
        # Valid request
        valid_request = InventoryTransactionRequest(
            product_id=product_id,
            transaction_type=TransactionType.INBOUND,
            quantity=50,
            reason="Valid transaction"
        )
        
        assert valid_request.product_id == product_id
        assert valid_request.transaction_type == TransactionType.INBOUND
        assert valid_request.quantity == 50
        
        # Test negative quantity validation
        with pytest.raises(ValueError):
            InventoryTransactionRequest(
                product_id=product_id,
                transaction_type=TransactionType.INBOUND,
                quantity=-10,  # Invalid: negative quantity
                reason="Invalid quantity"
            )

    def test_bulk_transaction_request_validation(self):
        """Test bulk transaction request validation"""
        
        product_id = uuid4()
        
        # Valid bulk request
        transactions = [
            InventoryTransactionRequest(
                product_id=product_id,
                transaction_type=TransactionType.INBOUND,
                quantity=25,
                reason="Bulk transaction 1"
            ),
            InventoryTransactionRequest(
                product_id=product_id,
                transaction_type=TransactionType.INBOUND,
                quantity=30,
                reason="Bulk transaction 2"
            )
        ]
        
        bulk_request = BulkTransactionRequest(
            transactions=transactions,
            batch_reference="BULK-001",
            auto_commit=True
        )
        
        assert len(bulk_request.transactions) == 2
        assert bulk_request.batch_reference == "BULK-001"
        assert bulk_request.auto_commit == True
        
        # Test empty transactions list
        with pytest.raises(ValueError):
            BulkTransactionRequest(transactions=[])  # Invalid: empty list

    def test_reservation_request_validation(self):
        """Test reservation request validation"""
        
        product_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Valid reservation request
        request = ReservationRequest(
            product_id=product_id,
            quantity=15,
            reserved_for="ORDER-56789",
            reservation_expires_at=expires_at,
            priority=3,
            notes="Customer priority order"
        )
        
        assert request.product_id == product_id
        assert request.quantity == 15
        assert request.reserved_for == "ORDER-56789"
        assert request.priority == 3
        
        # Test invalid quantity
        with pytest.raises(ValueError):
            ReservationRequest(
                product_id=product_id,
                quantity=0,  # Invalid: zero quantity
                reserved_for="ORDER-00000"
            )

    def test_inventory_adjustment_request_validation(self):
        """Test inventory adjustment request validation"""
        
        product_id = uuid4()
        
        # Valid adjustment request
        request = InventoryAdjustmentRequest(
            product_id=product_id,
            adjustment_type="relative",
            quantity=10,
            reason="Found additional stock during audit",
            cost_impact=Decimal('150.00'),
            requires_approval=True
        )
        
        assert request.product_id == product_id
        assert request.adjustment_type == "relative"
        assert request.quantity == 10
        assert request.cost_impact == Decimal('150.00')
        
        # Test invalid adjustment type
        with pytest.raises(ValueError):
            InventoryAdjustmentRequest(
                product_id=product_id,
                adjustment_type="invalid_type",  # Invalid: not absolute or relative
                quantity=5,
                reason="Invalid adjustment"
            )
        
        # Test zero quantity
        with pytest.raises(ValueError):
            InventoryAdjustmentRequest(
                product_id=product_id,
                adjustment_type="absolute",
                quantity=0,  # Invalid: zero quantity
                reason="Zero adjustment"
            )

    def test_stock_alert_config_request_validation(self):
        """Test stock alert configuration request validation"""
        
        product_id = uuid4()
        
        # Valid alert config
        request = StockAlertConfigRequest(
            product_id=product_id,
            alert_type=AlertType.LOW_STOCK,
            threshold_value=Decimal('25'),
            is_percentage=False,
            notification_emails=["manager@company.com", "warehouse@company.com"],
            is_active=True
        )
        
        assert request.product_id == product_id
        assert request.alert_type == AlertType.LOW_STOCK
        assert request.threshold_value == Decimal('25')
        assert len(request.notification_emails) == 2
        
        # Test negative threshold
        with pytest.raises(ValueError):
            StockAlertConfigRequest(
                product_id=product_id,
                alert_type=AlertType.LOW_STOCK,
                threshold_value=Decimal('-5'),  # Invalid: negative threshold
                is_percentage=False
            )

    def test_inventory_search_request_validation(self):
        """Test inventory search request validation"""
        
        product_ids = [uuid4(), uuid4()]
        
        # Valid search request
        request = InventorySearchRequest(
            product_ids=product_ids,
            locations=["WAREHOUSE_A", "WAREHOUSE_B"],
            stock_level_min=10,
            stock_level_max=1000,
            last_activity_days=30,
            batch_numbers=["BATCH-001", "BATCH-002"],
            expiry_date_from=date(2024, 1, 1),
            expiry_date_to=date(2024, 12, 31),
            include_zero_stock=False
        )
        
        assert len(request.product_ids) == 2
        assert len(request.locations) == 2
        assert request.stock_level_min == 10
        assert request.stock_level_max == 1000
        assert request.last_activity_days == 30
        assert request.include_zero_stock == False
        
        # Test invalid stock levels
        with pytest.raises(ValueError):
            InventorySearchRequest(
                stock_level_min=-5  # Invalid: negative minimum
            )
        
        # Test invalid activity days
        with pytest.raises(ValueError):
            InventorySearchRequest(
                last_activity_days=400  # Invalid: exceeds 365 days
            )

# Integration Tests for Response Models
class TestResponseModels:
    
    def test_inventory_transaction_response_creation(self):
        """Test InventoryTransactionResponse model creation"""
        
        transaction_id = uuid4()
        product_id = uuid4()
        created_at = datetime.utcnow()
        
        response = InventoryTransactionResponse(
            transaction_id=transaction_id,
            product_id=product_id,
            product_name="Test Product",
            product_sku="TP-001",
            transaction_type=TransactionType.INBOUND,
            status=TransactionStatus.COMPLETED,
            quantity=75,
            from_location=None,
            to_location="MAIN_WAREHOUSE",
            reference_id=None,
            reason="Stock replenishment",
            notes="Delivered by Supplier A",
            batch_number="BATCH-2024-001",
            expiry_date=date(2025, 12, 31),
            cost_per_unit=Decimal('12.50'),
            total_cost=Decimal('937.50'),
            created_at=created_at,
            processed_at=created_at,
            created_by="user-123",
            approved_by=None
        )
        
        assert response.transaction_id == transaction_id
        assert response.product_id == product_id
        assert response.transaction_type == TransactionType.INBOUND
        assert response.status == TransactionStatus.COMPLETED
        assert response.quantity == 75
        assert response.total_cost == Decimal('937.50')

    def test_inventory_level_response_creation(self):
        """Test InventoryLevelResponse model creation"""
        
        product_id = uuid4()
        last_updated = datetime.utcnow()
        
        response = InventoryLevelResponse(
            product_id=product_id,
            product_name="Widget Premium",
            product_sku="WP-001",
            location="MAIN_WAREHOUSE",
            current_stock=150,
            reserved_stock=25,
            available_stock=125,
            in_transit_stock=50,
            total_value=Decimal('4500.00'),
            average_cost=Decimal('30.00'),
            last_updated=last_updated,
            velocity=5.2,
            days_of_supply=24,
            reorder_point=30,
            max_stock_level=500
        )
        
        assert response.product_id == product_id
        assert response.current_stock == 150
        assert response.available_stock == 125
        assert response.velocity == 5.2
        assert response.days_of_supply == 24

    def test_inventory_alert_response_creation(self):
        """Test InventoryAlertResponse model creation"""
        
        alert_id = uuid4()
        product_id = uuid4()
        created_at = datetime.utcnow()
        
        response = InventoryAlertResponse(
            alert_id=alert_id,
            product_id=product_id,
            product_name="Critical Widget",
            alert_type=AlertType.OUT_OF_STOCK,
            severity=AlertSeverity.CRITICAL,
            message="Product is out of stock",
            current_value=Decimal('0'),
            threshold_value=Decimal('10'),
            created_at=created_at,
            acknowledged_at=None,
            resolved_at=None,
            is_active=True
        )
        
        assert response.alert_id == alert_id
        assert response.alert_type == AlertType.OUT_OF_STOCK
        assert response.severity == AlertSeverity.CRITICAL
        assert response.is_active == True

# Performance and Edge Case Tests
class TestPerformanceAndEdgeCases:
    
    @pytest.mark.asyncio
    async def test_large_bulk_transaction_performance(self, transaction_manager, mock_db_session, sample_product, sample_user):
        """Test performance with large bulk transactions"""
        
        # Mock successful validations and executions
        product_result = MagicMock()
        product_result.scalar_one_or_none.return_value = sample_product
        
        stock_result = MagicMock()
        stock_result.scalar.return_value = 10000  # High stock availability
        
        inventory_result = MagicMock()
        inventory_result.scalar_one_or_none.return_value = None
        
        mock_db_session.execute.side_effect = [
            product_result, stock_result, inventory_result
        ] * 200  # Repeat for 100 transactions * 2 phases
        
        mock_db_session.flush = AsyncMock()
        mock_db_session.add = MagicMock()
        
        # Create 100 transactions
        requests = [
            InventoryTransactionRequest(
                product_id=sample_product.id,
                transaction_type=TransactionType.INBOUND,
                quantity=i + 1,
                reason=f"Bulk transaction {i + 1}"
            )
            for i in range(100)
        ]
        
        # Measure execution time
        import time
        start_time = time.time()
        
        results = await transaction_manager.execute_bulk_transactions(requests, sample_user.id)
        
        execution_time = time.time() - start_time
        
        # Assertions
        assert len(results) == 100
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert mock_db_session.add.call_count == 100
        assert mock_db_session.flush.call_count == 100

    @pytest.mark.asyncio
    async def test_concurrent_reservations_same_product(self, reservation_manager, mock_db_session, sample_product, sample_user):
        """Test concurrent reservations for the same product"""
        
        # Mock sufficient stock initially
        stock_result = MagicMock()
        stock_result.scalar.return_value = 100
        mock_db_session.execute.return_value = stock_result
        
        with patch('app.api.v1.inventory_advanced_v57.InventoryTransactionManager') as mock_tm:
            mock_tm_instance = mock_tm.return_value
            mock_tm_instance.execute_transaction = AsyncMock()
            
            # Create multiple concurrent reservation requests
            requests = [
                ReservationRequest(
                    product_id=sample_product.id,
                    quantity=30,
                    reserved_for=f"ORDER-{i:05d}"
                )
                for i in range(5)
            ]
            
            # Execute concurrent reservations
            import asyncio
            tasks = [
                reservation_manager.create_reservation(req, sample_user.id)
                for req in requests
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that all reservations were processed
            successful_reservations = [r for r in results if isinstance(r, ReservationResponse)]
            failed_reservations = [r for r in results if isinstance(r, Exception)]
            
            # At least some should succeed (depending on race conditions)
            assert len(successful_reservations) > 0
            
            # Verify transaction manager was called for successful reservations
            assert mock_tm_instance.execute_transaction.call_count == len(successful_reservations)

    def test_enum_edge_cases(self):
        """Test enum edge cases and invalid values"""
        
        # Test valid enum values
        assert TransactionType.INBOUND == "inbound"
        assert TransactionType.OUTBOUND == "outbound"
        assert AlertType.LOW_STOCK == "low_stock"
        assert AlertSeverity.CRITICAL == "critical"
        
        # Test invalid enum values
        with pytest.raises(ValueError):
            TransactionType("invalid_type")
        
        with pytest.raises(ValueError):
            AlertType("invalid_alert")
        
        with pytest.raises(ValueError):
            TransactionStatus("invalid_status")

if __name__ == "__main__":
    pytest.main([__file__])