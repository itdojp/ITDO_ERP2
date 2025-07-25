"""
Tests for CC02 v58.0 Advanced Customer Management API
Comprehensive test suite for CRM, RFM analysis, LTV calculation, and customer segmentation
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.customer_advanced_v58 import (
    CommunicationChannel,
    CRMManager,
    CustomerInteractionRequest,
    CustomerInteractionResponse,
    CustomerLifecycleUpdateRequest,
    CustomerLTVResponse,
    CustomerMetrics,
    CustomerRFMResponse,
    CustomerStatus,
    InteractionStatus,
    InteractionType,
    LifecycleStage,
    LTVCalculationEngine,
    LTVCalculationRequest,
    RFMAnalysisEngine,
    RFMAnalysisRequest,
    RFMSegment,
)
from app.core.exceptions import NotFoundError
from app.models.customer import Customer
from app.models.user import User


# Test Fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.begin.return_value.__aenter__ = AsyncMock()
    session.begin.return_value.__aexit__ = AsyncMock()
    return session


@pytest.fixture
def sample_customer():
    """Sample customer for testing"""
    return Customer(
        id=uuid4(),
        email="test.customer@example.com",
        full_name="Test Customer",
        phone="+1234567890",
        lifecycle_stage=LifecycleStage.ACTIVE.value,
        status=CustomerStatus.ACTIVE.value,
        created_at=datetime.utcnow(),
        last_contact_date=datetime.utcnow() - timedelta(days=5),
    )


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id=uuid4(),
        email="test.user@example.com",
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_customer_metrics():
    """Sample customer metrics for testing"""
    return CustomerMetrics(
        customer_id=uuid4(),
        total_revenue=Decimal("1500.00"),
        order_count=5,
        avg_order_value=Decimal("300.00"),
        first_order_date=date(2024, 1, 1),
        last_order_date=date(2024, 3, 15),
        days_since_last_order=30,
        customer_lifespan_days=74,
        purchase_frequency_days=18.5,
    )


@pytest.fixture
def crm_manager(mock_db_session):
    """Create CRM manager with mocked database"""
    return CRMManager(mock_db_session)


@pytest.fixture
def rfm_engine(mock_db_session):
    """Create RFM analysis engine with mocked database"""
    return RFMAnalysisEngine(mock_db_session)


@pytest.fixture
def ltv_engine(mock_db_session):
    """Create LTV calculation engine with mocked database"""
    return LTVCalculationEngine(mock_db_session)


# Unit Tests for CRMManager
class TestCRMManager:
    @pytest.mark.asyncio
    async def test_create_customer_interaction_success(
        self, crm_manager, mock_db_session, sample_customer, sample_user
    ):
        """Test successful customer interaction creation"""

        # Mock customer lookup
        customer_result = MagicMock()
        customer_result.scalar_one_or_none.return_value = sample_customer
        mock_db_session.execute.return_value = customer_result

        # Mock database operations
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Mock update customer last contact
        with patch.object(
            crm_manager, "_update_customer_last_contact", new_callable=AsyncMock
        ):
            request = CustomerInteractionRequest(
                customer_id=sample_customer.id,
                interaction_type=InteractionType.EMAIL,
                channel=CommunicationChannel.EMAIL,
                subject="Welcome email",
                description="Welcome new customer with onboarding information",
                follow_up_required=True,
                follow_up_date=datetime.utcnow() + timedelta(days=7),
                tags=["welcome", "onboarding"],
            )

            # Execute interaction creation
            result = await crm_manager.create_customer_interaction(
                request, sample_user.id
            )

            # Assertions
            assert isinstance(result, CustomerInteractionResponse)
            assert result.customer_id == sample_customer.id
            assert result.interaction_type == InteractionType.EMAIL
            assert result.channel == CommunicationChannel.EMAIL
            assert result.subject == "Welcome email"
            assert result.follow_up_required
            assert len(result.tags) == 2

            # Verify database interactions
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_interaction_customer_not_found(
        self, crm_manager, mock_db_session, sample_user
    ):
        """Test interaction creation with non-existent customer"""

        # Mock customer lookup - customer not found
        customer_result = MagicMock()
        customer_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = customer_result

        request = CustomerInteractionRequest(
            customer_id=uuid4(),
            interaction_type=InteractionType.PHONE,
            channel=CommunicationChannel.PHONE,
            subject="Support call",
            description="Customer support inquiry",
        )

        # Execute interaction creation - should raise NotFoundError
        with pytest.raises(NotFoundError, match="Customer .* not found"):
            await crm_manager.create_customer_interaction(request, sample_user.id)

    @pytest.mark.asyncio
    async def test_update_customer_lifecycle_stage_success(
        self, crm_manager, mock_db_session, sample_customer, sample_user
    ):
        """Test successful customer lifecycle stage update"""

        # Mock customer lookup
        customer_result = MagicMock()
        customer_result.scalar_one_or_none.return_value = sample_customer

        # Mock update result
        update_result = MagicMock()
        update_result.rowcount = 1

        mock_db_session.execute.side_effect = [customer_result, update_result]
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()

        request = CustomerLifecycleUpdateRequest(
            customer_id=sample_customer.id,
            new_stage=LifecycleStage.RETENTION,
            reason="Customer completed first year anniversary",
            notes="Excellent customer satisfaction scores",
            automated=False,
        )

        # Execute lifecycle update
        result = await crm_manager.update_customer_lifecycle_stage(
            request, sample_user.id
        )

        # Assertions
        assert result["customer_id"] == str(sample_customer.id)
        assert result["old_stage"] == sample_customer.lifecycle_stage
        assert result["new_stage"] == LifecycleStage.RETENTION.value
        assert result["reason"] == request.reason
        assert not result["automated"]

        # Verify database interactions
        assert mock_db_session.execute.call_count == 2
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_customer_timeline_success(
        self, crm_manager, mock_db_session, sample_customer
    ):
        """Test successful customer timeline retrieval"""

        # Mock interactions
        mock_interaction = MagicMock()
        mock_interaction.id = uuid4()
        mock_interaction.subject = "Support call"
        mock_interaction.description = "Technical support inquiry"
        mock_interaction.interaction_type = "support"
        mock_interaction.channel = "phone"
        mock_interaction.status = "completed"
        mock_interaction.created_at = datetime.utcnow() - timedelta(days=2)

        interactions_result = MagicMock()
        interactions_result.scalars.return_value.all.return_value = [mock_interaction]

        # Mock orders
        mock_order = MagicMock()
        mock_order.id = uuid4()
        mock_order.order_number = "ORD-12345"
        mock_order.total_amount = Decimal("299.99")
        mock_order.status = "completed"
        mock_order.order_date = datetime.utcnow() - timedelta(days=1)

        orders_result = MagicMock()
        orders_result.scalars.return_value.all.return_value = [mock_order]

        mock_db_session.execute.side_effect = [interactions_result, orders_result]

        # Execute timeline retrieval
        timeline = await crm_manager.get_customer_timeline(sample_customer.id, 50)

        # Assertions
        assert len(timeline) == 2

        # Check interaction event
        interaction_event = next(
            (e for e in timeline if e["type"] == "interaction"), None
        )
        assert interaction_event is not None
        assert interaction_event["title"] == "Support call"
        assert interaction_event["interaction_type"] == "support"

        # Check order event
        order_event = next((e for e in timeline if e["type"] == "order"), None)
        assert order_event is not None
        assert order_event["title"] == "Order ORD-12345"
        assert order_event["amount"] == 299.99

        # Verify timeline is sorted by date (newest first)
        assert timeline[0]["date"] > timeline[1]["date"]


# Unit Tests for RFMAnalysisEngine
class TestRFMAnalysisEngine:
    @pytest.mark.asyncio
    async def test_calculate_rfm_analysis_success(
        self, rfm_engine, mock_db_session, sample_customer_metrics
    ):
        """Test successful RFM analysis calculation"""

        # Mock customer metrics query
        metrics_result = MagicMock()
        metrics_row = MagicMock()
        metrics_row.customer_id = sample_customer_metrics.customer_id
        metrics_row.total_revenue = sample_customer_metrics.total_revenue
        metrics_row.order_count = sample_customer_metrics.order_count
        metrics_row.avg_order_value = sample_customer_metrics.avg_order_value
        metrics_row.first_order_date = sample_customer_metrics.first_order_date
        metrics_row.last_order_date = sample_customer_metrics.last_order_date

        metrics_result.all.return_value = [metrics_row]

        # Mock customer lookup
        mock_customer = MagicMock()
        mock_customer.full_name = "Test Customer"
        mock_customer.email = "test@example.com"

        customer_result = MagicMock()
        customer_result.scalar_one_or_none.return_value = mock_customer

        mock_db_session.execute.side_effect = [metrics_result, customer_result]

        request = RFMAnalysisRequest(
            date_range_days=365, recency_bins=5, frequency_bins=5, monetary_bins=5
        )

        # Execute RFM analysis
        results = await rfm_engine.calculate_rfm_analysis(request)

        # Assertions
        assert len(results) == 1
        result = results[0]

        assert isinstance(result, CustomerRFMResponse)
        assert result.customer_id == sample_customer_metrics.customer_id
        assert result.customer_name == "Test Customer"
        assert result.recency_days == sample_customer_metrics.days_since_last_order
        assert result.frequency_orders == sample_customer_metrics.order_count
        assert result.monetary_value == sample_customer_metrics.total_revenue
        assert isinstance(result.rfm_scores.rfm_segment, RFMSegment)
        assert (
            result.rfm_scores.recency_score >= 1
            and result.rfm_scores.recency_score <= 5
        )
        assert (
            result.rfm_scores.frequency_score >= 1
            and result.rfm_scores.frequency_score <= 5
        )
        assert (
            result.rfm_scores.monetary_score >= 1
            and result.rfm_scores.monetary_score <= 5
        )

    def test_determine_rfm_segment_champions(self, rfm_engine):
        """Test RFM segment determination for champions"""

        # High scores across all dimensions should be champions
        segment = rfm_engine._determine_rfm_segment(5, 5, 5)
        assert segment == RFMSegment.CHAMPIONS

        segment = rfm_engine._determine_rfm_segment(4, 4, 4)
        assert segment == RFMSegment.CHAMPIONS

    def test_determine_rfm_segment_loyal_customers(self, rfm_engine):
        """Test RFM segment determination for loyal customers"""

        # High frequency should be loyal customers
        segment = rfm_engine._determine_rfm_segment(3, 5, 3)
        assert segment == RFMSegment.LOYAL_CUSTOMERS

        segment = rfm_engine._determine_rfm_segment(2, 4, 2)
        assert segment == RFMSegment.LOYAL_CUSTOMERS

    def test_determine_rfm_segment_lost(self, rfm_engine):
        """Test RFM segment determination for lost customers"""

        # Low scores across all dimensions should be lost
        segment = rfm_engine._determine_rfm_segment(1, 1, 1)
        assert segment == RFMSegment.LOST

    def test_calculate_percentile_thresholds(self, rfm_engine):
        """Test percentile threshold calculation"""

        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        thresholds = rfm_engine._calculate_percentile_thresholds(values, 5)

        # Should have 4 thresholds for 5 bins
        assert len(thresholds) == 4

        # Thresholds should be in ascending order
        assert all(
            thresholds[i] <= thresholds[i + 1] for i in range(len(thresholds) - 1)
        )

    def test_calculate_score(self, rfm_engine):
        """Test score calculation"""

        thresholds = [20, 40, 60, 80]

        # Test various values
        assert rfm_engine._calculate_score(10, thresholds) == 1  # Below all thresholds
        assert rfm_engine._calculate_score(30, thresholds) == 2  # Above first threshold
        assert (
            rfm_engine._calculate_score(50, thresholds) == 3
        )  # Above second threshold
        assert rfm_engine._calculate_score(70, thresholds) == 4  # Above third threshold
        assert rfm_engine._calculate_score(90, thresholds) == 5  # Above all thresholds

    def test_get_segment_description(self, rfm_engine):
        """Test segment description retrieval"""

        description = rfm_engine._get_segment_description(RFMSegment.CHAMPIONS)
        assert "Best customers" in description

        description = rfm_engine._get_segment_description(RFMSegment.LOST)
        assert "churned" in description.lower()


# Unit Tests for LTVCalculationEngine
class TestLTVCalculationEngine:
    @pytest.mark.asyncio
    async def test_calculate_customer_ltv_success(
        self, ltv_engine, mock_db_session, sample_customer_metrics
    ):
        """Test successful LTV calculation"""

        # Mock customer metrics query
        metrics_result = MagicMock()
        metrics_row = MagicMock()
        metrics_row.customer_id = sample_customer_metrics.customer_id
        metrics_row.total_revenue = sample_customer_metrics.total_revenue
        metrics_row.order_count = sample_customer_metrics.order_count
        metrics_row.avg_order_value = sample_customer_metrics.avg_order_value
        metrics_row.first_order_date = sample_customer_metrics.first_order_date
        metrics_row.last_order_date = sample_customer_metrics.last_order_date

        metrics_result.all.return_value = [metrics_row]

        # Mock customer lookup
        mock_customer = MagicMock()
        mock_customer.full_name = "Test Customer"
        mock_customer.email = "test@example.com"

        customer_result = MagicMock()
        customer_result.scalar_one_or_none.return_value = mock_customer

        mock_db_session.execute.side_effect = [metrics_result, customer_result]

        request = LTVCalculationRequest(
            prediction_months=12,
            discount_rate=0.1,
            include_acquisition_cost=True,
            method="historic",
        )

        # Execute LTV calculation
        results = await ltv_engine.calculate_customer_ltv(request)

        # Assertions
        assert len(results) == 1
        result = results[0]

        assert isinstance(result, CustomerLTVResponse)
        assert result.customer_id == sample_customer_metrics.customer_id
        assert result.customer_name == "Test Customer"
        assert result.historical_ltv == sample_customer_metrics.total_revenue
        assert result.predicted_ltv > 0
        assert result.ltv_12_months > 0
        assert result.ltv_24_months > 0
        assert result.acquisition_cost == Decimal("50.00")  # Default value
        assert result.net_ltv == result.predicted_ltv - result.acquisition_cost
        assert 0 <= result.churn_probability <= 1

    @pytest.mark.asyncio
    async def test_calculate_historic_ltv(self, ltv_engine, sample_customer_metrics):
        """Test historic LTV calculation method"""

        request = LTVCalculationRequest(
            prediction_months=12, discount_rate=0.1, method="historic"
        )

        # Execute historic LTV calculation
        ltv = await ltv_engine._calculate_historic_ltv(sample_customer_metrics, request)

        # Assertions
        assert isinstance(ltv, Decimal)
        assert ltv >= 0

        # LTV should be reasonable based on customer metrics
        # AOV * frequency * months should be in the ballpark
        expected_monthly_frequency = (
            30.0 / sample_customer_metrics.purchase_frequency_days
        )
        expected_base = (
            sample_customer_metrics.avg_order_value
            * Decimal(str(expected_monthly_frequency))
            * 12
        )

        # Allow for discount factor variance
        assert ltv <= expected_base * Decimal("1.1")  # Within 10% of base calculation

    @pytest.mark.asyncio
    async def test_calculate_predictive_ltv(self, ltv_engine, sample_customer_metrics):
        """Test predictive LTV calculation method"""

        request = LTVCalculationRequest(
            prediction_months=12, discount_rate=0.1, method="predictive"
        )

        # Execute predictive LTV calculation
        ltv = await ltv_engine._calculate_predictive_ltv(
            sample_customer_metrics, request
        )

        # Assertions
        assert isinstance(ltv, Decimal)
        assert ltv >= 0

        # Predictive LTV should consider customer behavior factors
        # Should be adjusted based on recency and frequency

    def test_calculate_churn_probability(self, ltv_engine, sample_customer_metrics):
        """Test churn probability calculation"""

        churn_prob = ltv_engine._calculate_churn_probability(sample_customer_metrics)

        # Assertions
        assert isinstance(churn_prob, float)
        assert 0 <= churn_prob <= 1
        assert churn_prob == round(
            churn_prob, 3
        )  # Should be rounded to 3 decimal places

    def test_determine_ltv_segment(self, ltv_engine):
        """Test LTV segment determination"""

        # Test different LTV values
        assert ltv_engine._determine_ltv_segment(Decimal("2500.00")) == "High Value"
        assert (
            ltv_engine._determine_ltv_segment(Decimal("1500.00")) == "Medium-High Value"
        )
        assert ltv_engine._determine_ltv_segment(Decimal("750.00")) == "Medium Value"
        assert (
            ltv_engine._determine_ltv_segment(Decimal("300.00")) == "Low-Medium Value"
        )
        assert ltv_engine._determine_ltv_segment(Decimal("50.00")) == "Low Value"


# API Endpoint Tests
class TestCustomerAdvancedAPI:
    def test_customer_interaction_request_validation(self):
        """Test customer interaction request validation"""

        customer_id = uuid4()

        # Valid request
        valid_request = CustomerInteractionRequest(
            customer_id=customer_id,
            interaction_type=InteractionType.EMAIL,
            channel=CommunicationChannel.EMAIL,
            subject="Customer inquiry",
            description="Customer has questions about product features and pricing",
            follow_up_required=True,
            follow_up_date=datetime.utcnow() + timedelta(days=3),
            tags=["inquiry", "product"],
        )

        assert valid_request.customer_id == customer_id
        assert valid_request.interaction_type == InteractionType.EMAIL
        assert valid_request.follow_up_required
        assert len(valid_request.tags) == 2

        # Test subject length validation
        with pytest.raises(ValueError):
            CustomerInteractionRequest(
                customer_id=customer_id,
                interaction_type=InteractionType.EMAIL,
                channel=CommunicationChannel.EMAIL,
                subject="",  # Invalid: empty subject
                description="Valid description",
            )

        # Test description length validation
        with pytest.raises(ValueError):
            CustomerInteractionRequest(
                customer_id=customer_id,
                interaction_type=InteractionType.EMAIL,
                channel=CommunicationChannel.EMAIL,
                subject="Valid subject",
                description="",  # Invalid: empty description
            )

    def test_rfm_analysis_request_validation(self):
        """Test RFM analysis request validation"""

        # Valid request
        valid_request = RFMAnalysisRequest(
            date_range_days=365,
            recency_bins=5,
            frequency_bins=5,
            monetary_bins=5,
            exclude_inactive=True,
        )

        assert valid_request.date_range_days == 365
        assert valid_request.recency_bins == 5
        assert valid_request.exclude_inactive

        # Test date range validation
        with pytest.raises(ValueError):
            RFMAnalysisRequest(date_range_days=25)  # Invalid: too short

        with pytest.raises(ValueError):
            RFMAnalysisRequest(date_range_days=1200)  # Invalid: too long

        # Test bins validation
        with pytest.raises(ValueError):
            RFMAnalysisRequest(recency_bins=2)  # Invalid: too few bins

        with pytest.raises(ValueError):
            RFMAnalysisRequest(frequency_bins=15)  # Invalid: too many bins

    def test_ltv_calculation_request_validation(self):
        """Test LTV calculation request validation"""

        customer_ids = [uuid4(), uuid4()]

        # Valid request
        valid_request = LTVCalculationRequest(
            customer_ids=customer_ids,
            prediction_months=12,
            discount_rate=0.1,
            include_acquisition_cost=True,
            method="historic",
        )

        assert len(valid_request.customer_ids) == 2
        assert valid_request.prediction_months == 12
        assert valid_request.discount_rate == 0.1
        assert valid_request.method == "historic"

        # Test prediction months validation
        with pytest.raises(ValueError):
            LTVCalculationRequest(prediction_months=0)  # Invalid: zero months

        with pytest.raises(ValueError):
            LTVCalculationRequest(prediction_months=70)  # Invalid: too many months

        # Test discount rate validation
        with pytest.raises(ValueError):
            LTVCalculationRequest(discount_rate=-0.1)  # Invalid: negative rate

        with pytest.raises(ValueError):
            LTVCalculationRequest(discount_rate=0.6)  # Invalid: too high rate

        # Test method validation
        with pytest.raises(ValueError):
            LTVCalculationRequest(method="invalid_method")  # Invalid: unknown method

    def test_customer_lifecycle_update_request_validation(self):
        """Test customer lifecycle update request validation"""

        customer_id = uuid4()

        # Valid request
        valid_request = CustomerLifecycleUpdateRequest(
            customer_id=customer_id,
            new_stage=LifecycleStage.RETENTION,
            reason="Customer reached 1-year milestone",
            notes="Excellent customer satisfaction scores",
            automated=False,
        )

        assert valid_request.customer_id == customer_id
        assert valid_request.new_stage == LifecycleStage.RETENTION
        assert not valid_request.automated

        # Test reason validation
        with pytest.raises(ValueError):
            CustomerLifecycleUpdateRequest(
                customer_id=customer_id,
                new_stage=LifecycleStage.RETENTION,
                reason="",  # Invalid: empty reason
            )


# Integration Tests for Response Models
class TestResponseModels:
    def test_customer_interaction_response_creation(self):
        """Test CustomerInteractionResponse model creation"""

        interaction_id = uuid4()
        customer_id = uuid4()
        created_at = datetime.utcnow()

        response = CustomerInteractionResponse(
            interaction_id=interaction_id,
            customer_id=customer_id,
            customer_name="John Doe",
            customer_email="john.doe@example.com",
            interaction_type=InteractionType.PHONE,
            channel=CommunicationChannel.PHONE,
            subject="Product support inquiry",
            description="Customer needs help with product setup",
            outcome="Issue resolved, customer satisfied",
            status=InteractionStatus.COMPLETED,
            scheduled_at=None,
            completed_at=created_at,
            duration_minutes=25,
            follow_up_required=False,
            follow_up_date=None,
            created_by="user-123",
            created_at=created_at,
            tags=["support", "product", "resolved"],
        )

        assert response.interaction_id == interaction_id
        assert response.customer_id == customer_id
        assert response.interaction_type == InteractionType.PHONE
        assert response.status == InteractionStatus.COMPLETED
        assert response.duration_minutes == 25
        assert len(response.tags) == 3

    def test_customer_rfm_response_creation(self):
        """Test CustomerRFMResponse model creation"""

        from app.api.v1.customer_advanced_v58 import RFMScores

        customer_id = uuid4()
        calculated_at = datetime.utcnow()

        rfm_scores = RFMScores(
            recency_score=4,
            frequency_score=5,
            monetary_score=4,
            rfm_segment=RFMSegment.CHAMPIONS,
            segment_description="Best customers - high value, frequent buyers",
        )

        response = CustomerRFMResponse(
            customer_id=customer_id,
            customer_name="Jane Smith",
            customer_email="jane.smith@example.com",
            recency_days=15,
            frequency_orders=12,
            monetary_value=Decimal("2400.00"),
            rfm_scores=rfm_scores,
            last_order_date=date(2024, 3, 15),
            total_orders=12,
            avg_order_value=Decimal("200.00"),
            calculated_at=calculated_at,
        )

        assert response.customer_id == customer_id
        assert response.recency_days == 15
        assert response.frequency_orders == 12
        assert response.rfm_scores.rfm_segment == RFMSegment.CHAMPIONS
        assert response.rfm_scores.recency_score == 4

    def test_customer_ltv_response_creation(self):
        """Test CustomerLTVResponse model creation"""

        customer_id = uuid4()
        calculated_at = datetime.utcnow()

        response = CustomerLTVResponse(
            customer_id=customer_id,
            customer_name="Bob Johnson",
            customer_email="bob.johnson@example.com",
            historical_ltv=Decimal("1800.00"),
            predicted_ltv=Decimal("2500.00"),
            ltv_12_months=Decimal("2500.00"),
            ltv_24_months=Decimal("5000.00"),
            acquisition_cost=Decimal("75.00"),
            net_ltv=Decimal("2425.00"),
            average_order_value=Decimal("150.00"),
            purchase_frequency=2.5,
            customer_lifespan_months=18.0,
            churn_probability=0.15,
            ltv_segment="High Value",
            calculated_at=calculated_at,
        )

        assert response.customer_id == customer_id
        assert response.historical_ltv == Decimal("1800.00")
        assert response.predicted_ltv == Decimal("2500.00")
        assert response.net_ltv == Decimal("2425.00")
        assert response.churn_probability == 0.15
        assert response.ltv_segment == "High Value"


# Performance and Edge Case Tests
class TestPerformanceAndEdgeCases:
    @pytest.mark.asyncio
    async def test_rfm_analysis_large_dataset(self, rfm_engine, mock_db_session):
        """Test RFM analysis performance with large dataset"""

        # Mock large dataset
        large_dataset = []
        for i in range(1000):
            row = MagicMock()
            row.customer_id = uuid4()
            row.total_revenue = Decimal(str(100 + i * 10))
            row.order_count = i % 20 + 1
            row.avg_order_value = Decimal(str(50 + i % 100))
            row.first_order_date = date(2023, 1, 1)
            row.last_order_date = date(2024, 1, 1) + timedelta(days=i % 365)
            large_dataset.append(row)

        metrics_result = MagicMock()
        metrics_result.all.return_value = large_dataset

        # Mock customer lookup for all customers
        mock_customer = MagicMock()
        mock_customer.full_name = "Test Customer"
        mock_customer.email = "test@example.com"

        customer_result = MagicMock()
        customer_result.scalar_one_or_none.return_value = mock_customer

        mock_db_session.execute.side_effect = [metrics_result] + [
            customer_result
        ] * 1000

        request = RFMAnalysisRequest(date_range_days=365)

        # Measure execution time
        import time

        start_time = time.time()

        results = await rfm_engine.calculate_rfm_analysis(request)

        execution_time = time.time() - start_time

        # Assertions
        assert len(results) == 1000
        assert execution_time < 10.0  # Should complete within 10 seconds

        # Verify all customers have valid RFM scores
        for result in results:
            assert 1 <= result.rfm_scores.recency_score <= 5
            assert 1 <= result.rfm_scores.frequency_score <= 5
            assert 1 <= result.rfm_scores.monetary_score <= 5

    @pytest.mark.asyncio
    async def test_ltv_calculation_edge_cases(self, ltv_engine):
        """Test LTV calculation edge cases"""

        # Customer with zero orders
        zero_metrics = CustomerMetrics(
            customer_id=uuid4(),
            total_revenue=Decimal("0"),
            order_count=0,
            avg_order_value=Decimal("0"),
            first_order_date=date.today(),
            last_order_date=date.today(),
            days_since_last_order=0,
            customer_lifespan_days=0,
            purchase_frequency_days=0,
        )

        request = LTVCalculationRequest(method="historic")
        ltv = await ltv_engine._calculate_historic_ltv(zero_metrics, request)
        assert ltv >= 0  # Should handle gracefully

        # Customer with single order
        single_order_metrics = CustomerMetrics(
            customer_id=uuid4(),
            total_revenue=Decimal("100"),
            order_count=1,
            avg_order_value=Decimal("100"),
            first_order_date=date.today(),
            last_order_date=date.today(),
            days_since_last_order=0,
            customer_lifespan_days=0,
            purchase_frequency_days=0,  # Will cause division by zero scenario
        )

        ltv = await ltv_engine._calculate_historic_ltv(single_order_metrics, request)
        assert ltv >= 0  # Should handle gracefully

    def test_rfm_segment_edge_cases(self, rfm_engine):
        """Test RFM segment determination edge cases"""

        # Test all possible score combinations for edge cases
        test_cases = [
            (1, 1, 1),  # Minimum scores
            (5, 5, 5),  # Maximum scores
            (3, 3, 3),  # Middle scores
            (1, 5, 1),  # High frequency, low recency/monetary
            (5, 1, 5),  # High recency/monetary, low frequency
        ]

        for r, f, m in test_cases:
            segment = rfm_engine._determine_rfm_segment(r, f, m)
            assert isinstance(segment, RFMSegment)

            description = rfm_engine._get_segment_description(segment)
            assert isinstance(description, str)
            assert len(description) > 0

    def test_enum_validations(self):
        """Test enum validations and edge cases"""

        # Test valid enum values
        assert InteractionType.EMAIL == "email"
        assert LifecycleStage.RETENTION == "retention"
        assert RFMSegment.CHAMPIONS == "champions"
        assert CommunicationChannel.PHONE == "phone"

        # Test invalid enum values
        with pytest.raises(ValueError):
            InteractionType("invalid_type")

        with pytest.raises(ValueError):
            LifecycleStage("invalid_stage")

        with pytest.raises(ValueError):
            RFMSegment("invalid_segment")


if __name__ == "__main__":
    pytest.main([__file__])
