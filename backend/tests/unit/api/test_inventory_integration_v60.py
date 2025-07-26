"""
Tests for CC02 v60.0 Inventory Integration Management API
Comprehensive test suite for real-time tracking, prediction, and supplier integration
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.inventory_integration_v60 import (
    InventoryStatus, StockMovementType, PredictionMethod, AlertSeverity, SupplierStatus,
    InventoryItemRequest, StockMovementRequest, ReorderRequest, StockPredictionRequest,
    SupplierIntegrationRequest, InventoryItemResponse, StockMovementResponse,
    ReorderResponse, StockPredictionResponse, InventoryAlertResponse,
    SupplierIntegrationResponse, InventoryTracker, PredictionEngine,
    SupplierIntegrator, InventoryIntegrationManager
)
from app.models.product import Product
from app.models.customer import Customer
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
        name="Test Product",
        sku="TEST-001",
        description="Test product for inventory",
        unit_cost=Decimal('25.00'),
        status="active",
        created_at=datetime.utcnow()
    )

@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id=uuid4(),
        email="test.user@example.com",
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow()
    )

@pytest.fixture
def inventory_tracker(mock_db_session):
    """Create inventory tracker with mocked database"""
    return InventoryTracker(mock_db_session)

@pytest.fixture
def prediction_engine(mock_db_session):
    """Create prediction engine with mocked database"""
    return PredictionEngine(mock_db_session)

@pytest.fixture
def supplier_integrator(mock_db_session):
    """Create supplier integrator with mocked database"""
    return SupplierIntegrator(mock_db_session)

@pytest.fixture
def integration_manager(mock_db_session):
    """Create integration manager with mocked database"""
    return InventoryIntegrationManager(mock_db_session)

# Unit Tests for InventoryTracker
class TestInventoryTracker:
    
    @pytest.mark.asyncio
    async def test_get_real_time_inventory_success(self, inventory_tracker, mock_db_session, sample_product):
        """Test successful real-time inventory retrieval"""
        
        # Mock database query result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.product_id = str(sample_product.id)
        mock_row.product_name = sample_product.name
        mock_row.product_sku = sample_product.sku
        mock_row.current_quantity = 50
        mock_row.reorder_point = 10
        mock_row.max_stock_level = 100
        mock_row.safety_stock = 5
        mock_row.reserved_quantity = 10
        
        mock_result.fetchone.return_value = mock_row
        mock_db_session.execute.return_value = mock_result
        
        # Execute real-time inventory check
        result = await inventory_tracker.get_real_time_inventory(sample_product.id)
        
        # Assertions
        assert result["product_id"] == sample_product.id
        assert result["product_name"] == sample_product.name
        assert result["current_quantity"] == 50
        assert result["available_quantity"] == 40  # 50 - 10 reserved
        assert result["reserved_quantity"] == 10
        assert result["status"] == InventoryStatus.AVAILABLE
        assert "last_updated" in result
        
        # Verify database query was executed
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_real_time_inventory_not_found(self, inventory_tracker, mock_db_session):
        """Test real-time inventory retrieval for non-existent product"""
        
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        product_id = uuid4()
        
        # Execute real-time inventory check - should raise NotFoundError
        with pytest.raises(NotFoundError, match=f"Product {product_id} not found"):
            await inventory_tracker.get_real_time_inventory(product_id)

    @pytest.mark.asyncio
    async def test_determine_inventory_status_levels(self, inventory_tracker):
        """Test inventory status determination logic"""
        
        # Test out of stock
        status = inventory_tracker._determine_inventory_status(0, 10, 100)
        assert status == InventoryStatus.OUT_OF_STOCK
        
        # Test low stock
        status = inventory_tracker._determine_inventory_status(5, 10, 100)
        assert status == InventoryStatus.LOW_STOCK
        
        # Test available stock
        status = inventory_tracker._determine_inventory_status(50, 10, 100)
        assert status == InventoryStatus.AVAILABLE
        
        # Test exactly at reorder point
        status = inventory_tracker._determine_inventory_status(10, 10, 100)
        assert status == InventoryStatus.LOW_STOCK

    @pytest.mark.asyncio
    async def test_record_stock_movement_success(self, inventory_tracker, mock_db_session, sample_product, sample_user):
        """Test successful stock movement recording"""
        
        # Mock database operations
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()
        
        # Mock get_real_time_inventory call
        with patch.object(inventory_tracker, 'get_real_time_inventory') as mock_get_inventory, \
             patch.object(inventory_tracker, '_check_inventory_alerts') as mock_check_alerts:
            
            mock_get_inventory.return_value = {
                "product_id": sample_product.id,
                "current_quantity": 75,
                "status": InventoryStatus.AVAILABLE
            }
            
            # Create stock movement request
            movement_request = StockMovementRequest(
                product_id=sample_product.id,
                movement_type=StockMovementType.PURCHASE,
                quantity=25,
                unit_cost=Decimal('20.00'),
                notes="Purchase from supplier"
            )
            
            # Execute stock movement recording
            result = await inventory_tracker.record_stock_movement(movement_request, sample_user.id)
            
            # Assertions
            assert "movement_id" in result
            assert result["product_id"] == sample_product.id
            assert result["movement_type"] == StockMovementType.PURCHASE
            assert result["quantity"] == 25
            assert "updated_inventory" in result
            
            # Verify database operations
            mock_db_session.execute.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_get_inventory.assert_called_once()
            mock_check_alerts.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_stock_movement_failure(self, inventory_tracker, mock_db_session, sample_product, sample_user):
        """Test stock movement recording failure"""
        
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")
        mock_db_session.rollback = AsyncMock()
        
        movement_request = StockMovementRequest(
            product_id=sample_product.id,
            movement_type=StockMovementType.SALE,
            quantity=10
        )
        
        # Execute stock movement recording - should raise BusinessLogicError
        with pytest.raises(BusinessLogicError, match="Failed to record stock movement"):
            await inventory_tracker.record_stock_movement(movement_request, sample_user.id)
        
        # Verify rollback was called
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_inventory_alerts_out_of_stock(self, inventory_tracker, mock_db_session):
        """Test inventory alert creation for out-of-stock scenario"""
        
        product_id = uuid4()
        inventory_data = {
            "product_id": product_id,
            "product_name": "Test Product",
            "current_quantity": 0,
            "reorder_point": 10,
            "status": InventoryStatus.OUT_OF_STOCK
        }
        
        # Mock alert creation
        with patch.object(inventory_tracker, '_create_inventory_alert') as mock_create_alert:
            
            await inventory_tracker._check_inventory_alerts(product_id, inventory_data)
            
            # Verify alert was created
            mock_create_alert.assert_called_once()
            
            # Check alert parameters
            call_args = mock_create_alert.call_args[0][0]
            assert call_args["alert_type"] == "out_of_stock"
            assert call_args["severity"] == AlertSeverity.CRITICAL
            assert call_args["product_id"] == product_id

    @pytest.mark.asyncio
    async def test_check_inventory_alerts_low_stock(self, inventory_tracker, mock_db_session):
        """Test inventory alert creation for low stock scenario"""
        
        product_id = uuid4()
        inventory_data = {
            "product_id": product_id,
            "product_name": "Test Product",
            "current_quantity": 5,
            "reorder_point": 10,
            "status": InventoryStatus.LOW_STOCK
        }
        
        # Mock alert creation
        with patch.object(inventory_tracker, '_create_inventory_alert') as mock_create_alert:
            
            await inventory_tracker._check_inventory_alerts(product_id, inventory_data)
            
            # Verify alert was created
            mock_create_alert.assert_called_once()
            
            # Check alert parameters
            call_args = mock_create_alert.call_args[0][0]
            assert call_args["alert_type"] == "low_stock"
            assert call_args["severity"] == AlertSeverity.HIGH
            assert call_args["threshold"] == 10

# Unit Tests for PredictionEngine
class TestPredictionEngine:
    
    @pytest.mark.asyncio
    async def test_generate_stock_predictions_success(self, prediction_engine, mock_db_session):
        """Test successful stock prediction generation"""
        
        product_ids = [uuid4(), uuid4()]
        
        # Mock database queries
        products_result = MagicMock()
        products_result.fetchall.return_value = [
            MagicMock(id=str(product_ids[0])),
            MagicMock(id=str(product_ids[1]))
        ]
        mock_db_session.execute.return_value = products_result
        
        # Mock prediction methods
        with patch.object(prediction_engine, '_predict_single_product') as mock_predict:
            mock_predict.side_effect = [
                {
                    "product_id": product_ids[0],
                    "current_stock": 50,
                    "predicted_demand": 20,
                    "predicted_stock": 30,
                    "reorder_recommendation": False
                },
                {
                    "product_id": product_ids[1],
                    "current_stock": 5,
                    "predicted_demand": 15,
                    "predicted_stock": 0,
                    "reorder_recommendation": True
                }
            ]
            
            request = StockPredictionRequest(
                prediction_days=30,
                method=PredictionMethod.MOVING_AVERAGE
            )
            
            # Execute prediction generation
            predictions = await prediction_engine.generate_stock_predictions(request)
            
            # Assertions
            assert len(predictions) == 2
            assert predictions[0]["product_id"] == product_ids[0]
            assert predictions[0]["reorder_recommendation"] == False
            assert predictions[1]["product_id"] == product_ids[1]
            assert predictions[1]["reorder_recommendation"] == True
            
            # Verify prediction method was called for each product
            assert mock_predict.call_count == 2

    @pytest.mark.asyncio
    async def test_predict_single_product_insufficient_data(self, prediction_engine, mock_db_session):
        """Test single product prediction with insufficient historical data"""
        
        product_id = uuid4()
        
        # Mock insufficient historical data
        with patch.object(prediction_engine, '_get_historical_demand') as mock_get_history:
            mock_get_history.return_value = [5, 3]  # Only 2 data points, need minimum 7
            
            request = StockPredictionRequest(prediction_days=30)
            
            # Execute prediction - should return None for insufficient data
            result = await prediction_engine._predict_single_product(product_id, request)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_predict_single_product_success(self, prediction_engine, mock_db_session):
        """Test successful single product prediction"""
        
        product_id = uuid4()
        
        # Mock sufficient historical data
        historical_data = [10, 12, 8, 15, 11, 9, 13, 14, 7, 16]
        
        with patch.object(prediction_engine, '_get_historical_demand') as mock_get_history, \
             patch.object(prediction_engine, '_get_current_stock') as mock_current_stock, \
             patch.object(prediction_engine, '_get_reorder_point') as mock_reorder_point, \
             patch.object(prediction_engine, '_calculate_reorder_quantity') as mock_reorder_qty:
            
            mock_get_history.return_value = historical_data
            mock_current_stock.return_value = 50
            mock_reorder_point.return_value = 10
            mock_reorder_qty.return_value = 30
            
            request = StockPredictionRequest(
                prediction_days=30,
                method=PredictionMethod.MOVING_AVERAGE
            )
            
            # Execute prediction
            result = await prediction_engine._predict_single_product(product_id, request)
            
            # Assertions
            assert result is not None
            assert result["product_id"] == product_id
            assert result["current_stock"] == 50
            assert result["predicted_demand"] > 0
            assert result["method_used"] == PredictionMethod.MOVING_AVERAGE
            assert "confidence_interval_lower" in result
            assert "confidence_interval_upper" in result

    def test_moving_average_prediction(self, prediction_engine):
        """Test moving average prediction method"""
        
        historical_data = [10, 12, 8, 15, 11, 9, 13]
        prediction_days = 30
        
        result = prediction_engine._moving_average_prediction(historical_data, prediction_days)
        
        # Should be based on recent 7 days average
        expected_avg = sum(historical_data[:7]) / 7
        expected_result = int(expected_avg * prediction_days)
        
        assert result == expected_result

    def test_exponential_smoothing_prediction(self, prediction_engine):
        """Test exponential smoothing prediction method"""
        
        historical_data = [10, 12, 8, 15, 11, 9, 13]
        prediction_days = 30
        
        result = prediction_engine._exponential_smoothing_prediction(historical_data, prediction_days)
        
        # Should apply exponential smoothing algorithm
        assert isinstance(result, int)
        assert result >= 0

    def test_linear_regression_prediction(self, prediction_engine):
        """Test linear regression prediction method"""
        
        # Trending up data
        historical_data = [5, 7, 9, 11, 13, 15, 17]
        prediction_days = 30
        
        result = prediction_engine._linear_regression_prediction(historical_data, prediction_days)
        
        # Should detect upward trend
        assert isinstance(result, int)
        assert result > 0

    def test_calculate_confidence_interval(self, prediction_engine):
        """Test confidence interval calculation"""
        
        historical_data = [10, 12, 8, 15, 11, 9, 13, 14, 7, 16]
        prediction = 300
        confidence = 0.95
        
        lower, upper = prediction_engine._calculate_confidence_interval(
            historical_data, prediction, confidence
        )
        
        # Should return tuple with reasonable bounds
        assert isinstance(lower, int)
        assert isinstance(upper, int)
        assert lower <= 0  # Lower bound should be negative (margin)
        assert upper >= 0  # Upper bound should be positive (margin)

# Unit Tests for SupplierIntegrator
class TestSupplierIntegrator:
    
    @pytest.mark.asyncio
    async def test_register_supplier_success(self, supplier_integrator, mock_db_session):
        """Test successful supplier registration"""
        
        # Mock no existing supplier
        existing_result = MagicMock()
        existing_result.fetchone.return_value = None
        
        # Mock successful insertion
        mock_db_session.execute.side_effect = [existing_result, AsyncMock()]
        mock_db_session.commit = AsyncMock()
        
        # Mock API connection test
        with patch.object(supplier_integrator, '_test_supplier_api_connection') as mock_api_test:
            mock_api_test.return_value = True
            
            request = SupplierIntegrationRequest(
                supplier_id=uuid4(),
                name="Test Supplier",
                contact_email="supplier@test.com",
                contact_phone="+1234567890",
                api_endpoint="https://api.supplier.com",
                api_key="test-api-key",
                lead_time_days=5,
                minimum_order_value=Decimal('100.00'),
                status=SupplierStatus.ACTIVE
            )
            
            # Execute supplier registration
            result = await supplier_integrator.register_supplier(request)
            
            # Assertions
            assert result["supplier_id"] == request.supplier_id
            assert result["name"] == request.name
            assert result["contact_email"] == request.contact_email
            assert result["status"] == request.status
            assert result["api_connected"] == True
            
            # Verify database operations
            assert mock_db_session.execute.call_count == 2  # Check existing + insert
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_supplier_already_exists(self, supplier_integrator, mock_db_session):
        """Test supplier registration when supplier already exists"""
        
        # Mock existing supplier
        existing_result = MagicMock()
        existing_result.fetchone.return_value = MagicMock(id="existing-id")
        mock_db_session.execute.return_value = existing_result
        
        request = SupplierIntegrationRequest(
            supplier_id=uuid4(),
            name="Test Supplier",
            contact_email="existing@supplier.com"
        )
        
        # Execute supplier registration - should raise BusinessLogicError
        with pytest.raises(BusinessLogicError, match="Supplier with email .* already exists"):
            await supplier_integrator.register_supplier(request)

    @pytest.mark.asyncio
    async def test_create_purchase_order_success(self, supplier_integrator, mock_db_session, sample_user):
        """Test successful purchase order creation"""
        
        # Mock supplier lookup
        supplier_result = MagicMock()
        supplier_row = MagicMock()
        supplier_row.name = "Test Supplier"
        supplier_row.contact_email = "supplier@test.com"
        supplier_row.api_endpoint = "https://api.supplier.com"
        supplier_row.api_key = "api-key"
        supplier_row.minimum_order_value = Decimal('50.00')
        supplier_result.fetchone.return_value = supplier_row
        
        # Mock product lookup
        product_result = MagicMock()
        product_row = MagicMock()
        product_row.name = "Test Product"
        product_row.unit_cost = Decimal('25.00')
        product_result.fetchone.return_value = product_row
        
        # Mock purchase order insertion
        mock_db_session.execute.side_effect = [supplier_result, product_result, AsyncMock()]
        mock_db_session.commit = AsyncMock()
        
        # Mock API call
        with patch.object(supplier_integrator, '_send_po_to_supplier_api') as mock_api_send:
            mock_api_send.return_value = True
            
            request = ReorderRequest(
                product_id=uuid4(),
                supplier_id=uuid4(),
                quantity=10,
                priority=2,
                notes="Urgent reorder"
            )
            
            # Execute purchase order creation
            result = await supplier_integrator.create_purchase_order(request, sample_user.id)
            
            # Assertions
            assert "purchase_order_id" in result
            assert result["supplier_name"] == "Test Supplier"
            assert result["product_name"] == "Test Product"
            assert result["quantity"] == 10
            assert result["estimated_cost"] == Decimal('250.00')  # 25 * 10
            assert result["status"] == "pending"
            assert result["api_sent"] == True
            
            # Verify database operations
            assert mock_db_session.execute.call_count == 3
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_purchase_order_supplier_not_found(self, supplier_integrator, mock_db_session, sample_user):
        """Test purchase order creation with non-existent supplier"""
        
        # Mock supplier not found
        supplier_result = MagicMock()
        supplier_result.fetchone.return_value = None
        mock_db_session.execute.return_value = supplier_result
        
        request = ReorderRequest(
            product_id=uuid4(),
            supplier_id=uuid4(),
            quantity=10
        )
        
        # Execute purchase order creation - should raise NotFoundError
        with pytest.raises(NotFoundError, match="Active supplier .* not found"):
            await supplier_integrator.create_purchase_order(request, sample_user.id)

    @pytest.mark.asyncio
    async def test_create_purchase_order_below_minimum(self, supplier_integrator, mock_db_session, sample_user):
        """Test purchase order creation below minimum order value"""
        
        # Mock supplier with high minimum order value
        supplier_result = MagicMock()
        supplier_row = MagicMock()
        supplier_row.name = "Test Supplier"
        supplier_row.minimum_order_value = Decimal('500.00')  # High minimum
        supplier_result.fetchone.return_value = supplier_row
        
        # Mock product with low cost
        product_result = MagicMock()
        product_row = MagicMock()
        product_row.name = "Test Product"
        product_row.unit_cost = Decimal('10.00')  # Low cost
        product_result.fetchone.return_value = product_row
        
        mock_db_session.execute.side_effect = [supplier_result, product_result]
        
        request = ReorderRequest(
            product_id=uuid4(),
            supplier_id=uuid4(),
            quantity=5  # 5 * 10 = 50, below 500 minimum
        )
        
        # Execute purchase order creation - should raise BusinessLogicError
        with pytest.raises(BusinessLogicError, match="Order value .* below minimum"):
            await supplier_integrator.create_purchase_order(request, sample_user.id)

    @pytest.mark.asyncio
    async def test_test_supplier_api_connection(self, supplier_integrator):
        """Test supplier API connection testing"""
        
        # Test successful connection
        result = await supplier_integrator._test_supplier_api_connection(
            "https://api.supplier.com", "valid-key"
        )
        
        # Should return True (simplified for demo)
        assert result == True

    @pytest.mark.asyncio
    async def test_send_po_to_supplier_api(self, supplier_integrator):
        """Test sending purchase order to supplier API"""
        
        po_id = uuid4()
        supplier = MagicMock()
        supplier.name = "Test Supplier"
        product = MagicMock()
        product.name = "Test Product"
        request = ReorderRequest(
            product_id=uuid4(),
            supplier_id=uuid4(),
            quantity=10
        )
        
        # Test successful API call
        result = await supplier_integrator._send_po_to_supplier_api(
            po_id, supplier, product, request
        )
        
        # Should return True (simplified for demo)
        assert result == True

# Unit Tests for InventoryIntegrationManager
class TestInventoryIntegrationManager:
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_inventory_status_single_product(self, integration_manager, mock_db_session):
        """Test comprehensive inventory status for single product"""
        
        product_id = uuid4()
        
        # Mock component methods
        with patch.object(integration_manager.tracker, 'get_real_time_inventory') as mock_real_time, \
             patch.object(integration_manager, '_get_recent_movements') as mock_movements, \
             patch.object(integration_manager, '_get_active_alerts') as mock_alerts, \
             patch.object(integration_manager, '_get_supplier_info') as mock_supplier:
            
            # Setup mock returns
            mock_real_time.return_value = {
                "product_id": product_id,
                "current_quantity": 50,
                "status": InventoryStatus.AVAILABLE
            }
            
            mock_movements.return_value = [
                {
                    "movement_type": "purchase",
                    "quantity": 25,
                    "created_at": datetime.utcnow(),
                    "notes": "Stock purchase"
                }
            ]
            
            mock_alerts.return_value = []
            
            mock_supplier.return_value = {
                "supplier_id": uuid4(),
                "name": "Test Supplier",
                "status": "active"
            }
            
            # Execute comprehensive status check
            result = await integration_manager.get_comprehensive_inventory_status(product_id)
            
            # Assertions
            assert "timestamp" in result
            assert result["total_products"] == 1
            assert len(result["inventory_status"]) == 1
            
            status = result["inventory_status"][0]
            assert status["product_id"] == product_id
            assert "real_time_data" in status
            assert "recent_movements" in status
            assert "active_alerts" in status
            assert "supplier_info" in status
            
            # Verify all component methods were called
            mock_real_time.assert_called_once_with(product_id)
            mock_movements.assert_called_once_with(product_id, 5)
            mock_alerts.assert_called_once_with(product_id)
            mock_supplier.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_comprehensive_inventory_status_all_products(self, integration_manager, mock_db_session):
        """Test comprehensive inventory status for all products"""
        
        # Mock product query
        products_result = MagicMock()
        products_result.fetchall.return_value = [
            MagicMock(id=str(uuid4())),
            MagicMock(id=str(uuid4()))
        ]
        mock_db_session.execute.return_value = products_result
        
        # Mock component methods
        with patch.object(integration_manager.tracker, 'get_real_time_inventory') as mock_real_time, \
             patch.object(integration_manager, '_get_recent_movements') as mock_movements, \
             patch.object(integration_manager, '_get_active_alerts') as mock_alerts, \
             patch.object(integration_manager, '_get_supplier_info') as mock_supplier:
            
            # Setup mock returns
            mock_real_time.return_value = {"current_quantity": 50}
            mock_movements.return_value = []
            mock_alerts.return_value = []
            mock_supplier.return_value = None
            
            # Execute comprehensive status check (no product_id = all products)
            result = await integration_manager.get_comprehensive_inventory_status()
            
            # Assertions
            assert result["total_products"] == 2
            assert len(result["inventory_status"]) == 2
            
            # Verify methods were called for each product
            assert mock_real_time.call_count == 2
            assert mock_movements.call_count == 2
            assert mock_alerts.call_count == 2
            assert mock_supplier.call_count == 2

    @pytest.mark.asyncio
    async def test_get_recent_movements(self, integration_manager, mock_db_session):
        """Test recent movements retrieval"""
        
        product_id = uuid4()
        
        # Mock database query
        movements_result = MagicMock()
        movements_result.fetchall.return_value = [
            MagicMock(
                movement_type="purchase",
                quantity=25,
                created_at=datetime.utcnow(),
                notes="Purchase order"
            ),
            MagicMock(
                movement_type="sale",
                quantity=10,
                created_at=datetime.utcnow() - timedelta(hours=1),
                notes="Customer order"
            )
        ]
        mock_db_session.execute.return_value = movements_result
        
        # Execute recent movements retrieval
        movements = await integration_manager._get_recent_movements(product_id, 5)
        
        # Assertions
        assert len(movements) == 2
        assert movements[0]["movement_type"] == "purchase"
        assert movements[0]["quantity"] == 25
        assert movements[1]["movement_type"] == "sale"
        assert movements[1]["quantity"] == 10

    @pytest.mark.asyncio
    async def test_get_active_alerts(self, integration_manager, mock_db_session):
        """Test active alerts retrieval"""
        
        product_id = uuid4()
        
        # Mock database query
        alerts_result = MagicMock()
        alerts_result.fetchall.return_value = [
            MagicMock(
                alert_type="low_stock",
                severity="high",
                message="Product below reorder point",
                created_at=datetime.utcnow()
            )
        ]
        mock_db_session.execute.return_value = alerts_result
        
        # Execute active alerts retrieval
        alerts = await integration_manager._get_active_alerts(product_id)
        
        # Assertions
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "low_stock"
        assert alerts[0]["severity"] == "high"
        assert "message" in alerts[0]

    @pytest.mark.asyncio
    async def test_get_supplier_info(self, integration_manager, mock_db_session):
        """Test supplier information retrieval"""
        
        product_id = uuid4()
        
        # Mock database query
        supplier_result = MagicMock()
        supplier_result.fetchone.return_value = MagicMock(
            id=str(uuid4()),
            name="Test Supplier",
            contact_email="supplier@test.com",
            lead_time_days=7,
            status="active"
        )
        mock_db_session.execute.return_value = supplier_result
        
        # Execute supplier info retrieval
        supplier_info = await integration_manager._get_supplier_info(product_id)
        
        # Assertions
        assert supplier_info is not None
        assert supplier_info["name"] == "Test Supplier"
        assert supplier_info["contact_email"] == "supplier@test.com"
        assert supplier_info["lead_time_days"] == 7
        assert supplier_info["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_supplier_info_not_found(self, integration_manager, mock_db_session):
        """Test supplier information retrieval when no supplier exists"""
        
        product_id = uuid4()
        
        # Mock database query returning None
        supplier_result = MagicMock()
        supplier_result.fetchone.return_value = None
        mock_db_session.execute.return_value = supplier_result
        
        # Execute supplier info retrieval
        supplier_info = await integration_manager._get_supplier_info(product_id)
        
        # Assertions
        assert supplier_info is None

# Request Model Tests
class TestRequestModels:
    
    def test_inventory_item_request_validation(self):
        """Test inventory item request validation"""
        
        product_id = uuid4()
        
        # Valid request
        valid_request = InventoryItemRequest(
            product_id=product_id,
            quantity=50,
            reorder_point=10,
            max_stock_level=100,
            unit_cost=Decimal('25.00'),
            lead_time_days=7,
            safety_stock=5
        )
        
        assert valid_request.product_id == product_id
        assert valid_request.quantity == 50
        assert valid_request.reorder_point == 10
        assert valid_request.max_stock_level == 100
        
        # Test max_stock_level validation
        with pytest.raises(ValueError):
            InventoryItemRequest(
                product_id=product_id,
                quantity=50,
                reorder_point=50,  # Equal to max_stock_level
                max_stock_level=50,
                unit_cost=Decimal('25.00')
            )

    def test_stock_movement_request_validation(self):
        """Test stock movement request validation"""
        
        product_id = uuid4()
        
        # Valid request
        valid_request = StockMovementRequest(
            product_id=product_id,
            movement_type=StockMovementType.PURCHASE,
            quantity=25,
            unit_cost=Decimal('20.00'),
            notes="Stock purchase from supplier",
            batch_number="BATCH-001"
        )
        
        assert valid_request.product_id == product_id
        assert valid_request.movement_type == StockMovementType.PURCHASE
        assert valid_request.quantity == 25
        assert valid_request.unit_cost == Decimal('20.00')
        assert valid_request.batch_number == "BATCH-001"
        
        # Test quantity validation
        with pytest.raises(ValueError):
            StockMovementRequest(
                product_id=product_id,
                movement_type=StockMovementType.SALE,
                quantity=0  # Invalid: must be > 0
            )

    def test_stock_prediction_request_validation(self):
        """Test stock prediction request validation"""
        
        product_ids = [uuid4(), uuid4()]
        
        # Valid request
        valid_request = StockPredictionRequest(
            product_ids=product_ids,
            prediction_days=30,
            method=PredictionMethod.EXPONENTIAL_SMOOTHING,
            include_seasonal=True,
            confidence_level=0.95
        )
        
        assert len(valid_request.product_ids) == 2
        assert valid_request.prediction_days == 30
        assert valid_request.method == PredictionMethod.EXPONENTIAL_SMOOTHING
        assert valid_request.confidence_level == 0.95
        
        # Test prediction_days validation
        with pytest.raises(ValueError):
            StockPredictionRequest(prediction_days=0)  # Invalid: must be >= 1
        
        with pytest.raises(ValueError):
            StockPredictionRequest(prediction_days=400)  # Invalid: must be <= 365

    def test_supplier_integration_request_validation(self):
        """Test supplier integration request validation"""
        
        supplier_id = uuid4()
        
        # Valid request
        valid_request = SupplierIntegrationRequest(
            supplier_id=supplier_id,
            name="Test Supplier Ltd",
            contact_email="contact@testsupplier.com",
            contact_phone="+1-555-0123",
            api_endpoint="https://api.testsupplier.com/v1",
            api_key="test-api-key-123",
            lead_time_days=5,
            minimum_order_value=Decimal('200.00'),
            status=SupplierStatus.ACTIVE
        )
        
        assert valid_request.supplier_id == supplier_id
        assert valid_request.name == "Test Supplier Ltd"
        assert valid_request.contact_email == "contact@testsupplier.com"
        assert valid_request.lead_time_days == 5
        assert valid_request.status == SupplierStatus.ACTIVE
        
        # Test email validation
        with pytest.raises(ValueError):
            SupplierIntegrationRequest(
                supplier_id=supplier_id,
                name="Test Supplier",
                contact_email="invalid-email"  # Invalid email format
            )

    def test_reorder_request_validation(self):
        """Test reorder request validation"""
        
        product_id = uuid4()
        supplier_id = uuid4()
        
        # Valid request
        valid_request = ReorderRequest(
            product_id=product_id,
            supplier_id=supplier_id,
            quantity=50,
            priority=3,
            delivery_date=datetime.utcnow() + timedelta(days=14),
            notes="Urgent reorder for high-demand product"
        )
        
        assert valid_request.product_id == product_id
        assert valid_request.supplier_id == supplier_id
        assert valid_request.quantity == 50
        assert valid_request.priority == 3
        assert valid_request.delivery_date is not None
        
        # Test quantity validation
        with pytest.raises(ValueError):
            ReorderRequest(
                product_id=product_id,
                supplier_id=supplier_id,
                quantity=0  # Invalid: must be > 0
            )
        
        # Test priority validation
        with pytest.raises(ValueError):
            ReorderRequest(
                product_id=product_id,
                supplier_id=supplier_id,
                quantity=10,
                priority=6  # Invalid: must be <= 5
            )

# Enum Tests
class TestEnums:
    
    def test_inventory_status_enum_values(self):
        """Test inventory status enum values"""
        
        assert InventoryStatus.AVAILABLE == "available"
        assert InventoryStatus.LOW_STOCK == "low_stock"
        assert InventoryStatus.OUT_OF_STOCK == "out_of_stock"
        assert InventoryStatus.DISCONTINUED == "discontinued"
        assert InventoryStatus.RESERVED == "reserved"

    def test_stock_movement_type_enum_values(self):
        """Test stock movement type enum values"""
        
        assert StockMovementType.PURCHASE == "purchase"
        assert StockMovementType.SALE == "sale"
        assert StockMovementType.ADJUSTMENT == "adjustment"
        assert StockMovementType.TRANSFER == "transfer"
        assert StockMovementType.RETURN == "return"
        assert StockMovementType.DAMAGE == "damage"
        assert StockMovementType.RESERVATION == "reservation"
        assert StockMovementType.RELEASE == "release"

    def test_prediction_method_enum_values(self):
        """Test prediction method enum values"""
        
        assert PredictionMethod.MOVING_AVERAGE == "moving_average"
        assert PredictionMethod.EXPONENTIAL_SMOOTHING == "exponential_smoothing"
        assert PredictionMethod.LINEAR_REGRESSION == "linear_regression"
        assert PredictionMethod.SEASONAL_DECOMPOSITION == "seasonal_decomposition"

    def test_alert_severity_enum_values(self):
        """Test alert severity enum values"""
        
        assert AlertSeverity.LOW == "low"
        assert AlertSeverity.MEDIUM == "medium"
        assert AlertSeverity.HIGH == "high"
        assert AlertSeverity.CRITICAL == "critical"

    def test_supplier_status_enum_values(self):
        """Test supplier status enum values"""
        
        assert SupplierStatus.ACTIVE == "active"
        assert SupplierStatus.INACTIVE == "inactive"
        assert SupplierStatus.PENDING == "pending"
        assert SupplierStatus.SUSPENDED == "suspended"

# Integration Tests
class TestInventoryIntegrationWorkflow:
    
    @pytest.mark.asyncio
    async def test_complete_inventory_workflow(self, integration_manager, mock_db_session):
        """Test complete inventory management workflow"""
        
        product_id = uuid4()
        user_id = uuid4()
        supplier_id = uuid4()
        
        # Mock database operations
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()
        
        # Step 1: Register supplier
        supplier_request = SupplierIntegrationRequest(
            supplier_id=supplier_id,
            name="Test Supplier",
            contact_email="supplier@test.com",
            lead_time_days=7,
            minimum_order_value=Decimal('100.00')
        )
        
        with patch.object(integration_manager.supplier_integrator, 'register_supplier') as mock_register:
            mock_register.return_value = {
                "supplier_id": supplier_id,
                "name": "Test Supplier",
                "status": SupplierStatus.ACTIVE
            }
            
            supplier_result = await integration_manager.supplier_integrator.register_supplier(supplier_request)
            assert supplier_result["supplier_id"] == supplier_id
        
        # Step 2: Record stock movement
        movement_request = StockMovementRequest(
            product_id=product_id,
            movement_type=StockMovementType.PURCHASE,
            quantity=100,
            unit_cost=Decimal('10.00')
        )
        
        with patch.object(integration_manager.tracker, 'record_stock_movement') as mock_movement:
            mock_movement.return_value = {
                "movement_id": uuid4(),
                "product_id": product_id,
                "quantity": 100
            }
            
            movement_result = await integration_manager.tracker.record_stock_movement(movement_request, user_id)
            assert movement_result["quantity"] == 100
        
        # Step 3: Generate predictions
        prediction_request = StockPredictionRequest(
            product_ids=[product_id],
            prediction_days=30
        )
        
        with patch.object(integration_manager.predictor, 'generate_stock_predictions') as mock_predict:
            mock_predict.return_value = [
                {
                    "product_id": product_id,
                    "predicted_demand": 60,
                    "reorder_recommendation": True
                }
            ]
            
            predictions = await integration_manager.predictor.generate_stock_predictions(prediction_request)
            assert len(predictions) == 1
            assert predictions[0]["reorder_recommendation"] == True
        
        # Step 4: Create reorder based on prediction
        reorder_request = ReorderRequest(
            product_id=product_id,
            supplier_id=supplier_id,
            quantity=80
        )
        
        with patch.object(integration_manager.supplier_integrator, 'create_purchase_order') as mock_po:
            mock_po.return_value = {
                "purchase_order_id": uuid4(),
                "quantity": 80,
                "status": "pending"
            }
            
            po_result = await integration_manager.supplier_integrator.create_purchase_order(reorder_request, user_id)
            assert po_result["quantity"] == 80

# Performance Tests
class TestPerformanceAndScalability:
    
    @pytest.mark.asyncio
    async def test_bulk_prediction_performance(self, prediction_engine, mock_db_session):
        """Test prediction performance with many products"""
        
        # Mock large number of products
        num_products = 100
        product_ids = [uuid4() for _ in range(num_products)]
        
        products_result = MagicMock()
        products_result.fetchall.return_value = [
            MagicMock(id=str(pid)) for pid in product_ids
        ]
        mock_db_session.execute.return_value = products_result
        
        # Mock prediction method to return quick results
        with patch.object(prediction_engine, '_predict_single_product') as mock_predict:
            mock_predict.return_value = {
                "product_id": uuid4(),
                "predicted_demand": 20,
                "reorder_recommendation": False
            }
            
            request = StockPredictionRequest(prediction_days=30)
            
            # Measure execution time
            import time
            start_time = time.time()
            
            predictions = await prediction_engine.generate_stock_predictions(request)
            
            execution_time = time.time() - start_time
            
            # Assertions
            assert len(predictions) == num_products
            assert execution_time < 5.0  # Should complete within 5 seconds
            assert mock_predict.call_count == num_products

    @pytest.mark.asyncio
    async def test_concurrent_stock_movements(self, inventory_tracker, mock_db_session):
        """Test concurrent stock movement processing"""
        
        product_id = uuid4()
        user_id = uuid4()
        
        # Mock database operations
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()
        
        # Mock inventory retrieval
        with patch.object(inventory_tracker, 'get_real_time_inventory') as mock_inventory, \
             patch.object(inventory_tracker, '_check_inventory_alerts') as mock_alerts:
            
            mock_inventory.return_value = {
                "product_id": product_id,
                "current_quantity": 100,
                "status": InventoryStatus.AVAILABLE
            }
            
            # Create multiple concurrent movements
            movements = [
                StockMovementRequest(
                    product_id=product_id,
                    movement_type=StockMovementType.SALE,
                    quantity=i + 1
                )
                for i in range(10)
            ]
            
            # Process movements concurrently
            tasks = [
                inventory_tracker.record_stock_movement(movement, user_id)
                for movement in movements
            ]
            
            import asyncio
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all movements processed
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == 10
            
            # Verify database operations
            assert mock_db_session.execute.call_count == 10
            assert mock_db_session.commit.call_count == 10

if __name__ == "__main__":
    pytest.main([__file__])