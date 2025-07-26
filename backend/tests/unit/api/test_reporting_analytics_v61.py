"""
Tests for CC02 v61.0 Advanced Reporting & Analytics Management API
Comprehensive test suite for dashboards, business intelligence, custom reports, and KPI management
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.reporting_analytics_v61 import (
    AggregationType,
    AnalyticsQueryRequest,
    BusinessIntelligenceEngine,
    ChartType,
    CustomReportRequest,
    DashboardEngine,
    DashboardWidgetRequest,
    DeliveryMethod,
    KPIDefinitionRequest,
    KPIManager,
    ReportBuilder,
    ReportFormat,
    ReportingAnalyticsManager,
    ReportScheduleRequest,
    ReportType,
    ScheduledReportManager,
    TimeGranularity,
)
from app.core.exceptions import BusinessLogicError, NotFoundError
from app.models.customer import Customer
from app.models.order import Order
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
def sample_customer():
    """Sample customer for testing"""
    return Customer(
        id=uuid4(),
        email="test.customer@example.com",
        full_name="Test Customer",
        phone="+1234567890",
        status="active",
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_order():
    """Sample order for testing"""
    return Order(
        id=uuid4(),
        customer_id=uuid4(),
        order_number="ORD-2024-001",
        total_amount=Decimal("250.00"),
        status="completed",
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def dashboard_engine(mock_db_session):
    """Create dashboard engine with mocked database"""
    return DashboardEngine(mock_db_session)


@pytest.fixture
def report_builder(mock_db_session):
    """Create report builder with mocked database"""
    return ReportBuilder(mock_db_session)


@pytest.fixture
def bi_engine(mock_db_session):
    """Create business intelligence engine with mocked database"""
    return BusinessIntelligenceEngine(mock_db_session)


@pytest.fixture
def kpi_manager(mock_db_session):
    """Create KPI manager with mocked database"""
    return KPIManager(mock_db_session)


@pytest.fixture
def schedule_manager(mock_db_session):
    """Create scheduled report manager with mocked database"""
    return ScheduledReportManager(mock_db_session)


@pytest.fixture
def analytics_manager(mock_db_session):
    """Create main analytics manager with mocked database"""
    return ReportingAnalyticsManager(mock_db_session)


# Unit Tests for DashboardEngine
class TestDashboardEngine:
    @pytest.mark.asyncio
    async def test_create_dashboard_widget_success(
        self, dashboard_engine, mock_db_session, sample_user
    ):
        """Test successful dashboard widget creation"""

        # Mock database operations
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()

        # Mock widget data generation
        with patch.object(dashboard_engine, "_generate_widget_data") as mock_generate:
            mock_generate.return_value = {
                "labels": ["2024-01-01", "2024-01-02"],
                "datasets": [{"label": "Sales", "data": [100, 150]}],
            }

            request = DashboardWidgetRequest(
                title="Sales Overview",
                chart_type=ChartType.LINE,
                data_source="sales",
                metrics=["revenue", "order_count"],
                dimensions=["date"],
                filters={"status": "completed"},
                refresh_interval=300,
                position={"x": 0, "y": 0, "width": 4, "height": 3},
            )

            # Execute widget creation
            result = await dashboard_engine.create_dashboard_widget(
                request, sample_user.id
            )

            # Assertions
            assert "widget_id" in result
            assert result["title"] == "Sales Overview"
            assert result["chart_type"] == ChartType.LINE
            assert "data" in result
            assert "created_at" in result

            # Verify database operations
            mock_db_session.execute.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dashboard_widget_failure(
        self, dashboard_engine, mock_db_session, sample_user
    ):
        """Test dashboard widget creation failure"""

        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")
        mock_db_session.rollback = AsyncMock()

        request = DashboardWidgetRequest(
            title="Test Widget",
            chart_type=ChartType.BAR,
            data_source="sales",
            metrics=["revenue"],
        )

        # Execute widget creation - should raise BusinessLogicError
        with pytest.raises(BusinessLogicError, match="Failed to create widget"):
            await dashboard_engine.create_dashboard_widget(request, sample_user.id)

        # Verify rollback was called
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dashboard_data_success(self, dashboard_engine, mock_db_session):
        """Test successful dashboard data retrieval"""

        dashboard_id = uuid4()

        # Mock widget query result
        mock_result = MagicMock()
        mock_widget = MagicMock()
        mock_widget.id = str(uuid4())
        mock_widget.title = "Test Widget"
        mock_widget.chart_type = "line"
        mock_widget.data_source = "sales"
        mock_widget.metrics = '["revenue"]'
        mock_widget.dimensions = '["date"]'
        mock_widget.filters = '{"status": "completed"}'
        mock_widget.time_range = "30d"
        mock_widget.refresh_interval = 300
        mock_widget.position = '{"x": 0, "y": 0}'
        mock_widget.updated_at = datetime.utcnow()

        mock_result.fetchall.return_value = [mock_widget]
        mock_db_session.execute.return_value = mock_result

        # Mock widget data generation
        with patch.object(dashboard_engine, "_generate_widget_data") as mock_generate:
            mock_generate.return_value = {"data": "test_data"}

            # Execute dashboard data retrieval
            result = await dashboard_engine.get_dashboard_data(dashboard_id)

            # Assertions
            assert result["dashboard_id"] == dashboard_id
            assert "widgets" in result
            assert len(result["widgets"]) == 1
            assert result["widgets"][0]["title"] == "Test Widget"
            assert result["widgets"][0]["data"] == {"data": "test_data"}
            assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_generate_sales_data(self, dashboard_engine, mock_db_session):
        """Test sales data generation for widgets"""

        # Mock sales query result
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(
                date=date(2024, 1, 1),
                order_count=10,
                total_revenue=Decimal("1000.00"),
                avg_order_value=Decimal("100.00"),
            ),
            MagicMock(
                date=date(2024, 1, 2),
                order_count=15,
                total_revenue=Decimal("1800.00"),
                avg_order_value=Decimal("120.00"),
            ),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db_session.execute.return_value = mock_result

        request = DashboardWidgetRequest(
            title="Sales Widget",
            chart_type=ChartType.LINE,
            data_source="sales",
            metrics=["order_count", "total_revenue"],
        )

        # Execute sales data generation
        result = await dashboard_engine._generate_sales_data(request)

        # Assertions
        assert "labels" in result
        assert len(result["labels"]) == 2
        assert result["labels"][0] == "2024-01-01"
        assert "datasets" in result
        assert len(result["datasets"]) == 2

        # Check order count dataset
        order_dataset = next(ds for ds in result["datasets"] if ds["label"] == "Orders")
        assert order_dataset["data"] == [10, 15]

        # Check revenue dataset
        revenue_dataset = next(
            ds for ds in result["datasets"] if ds["label"] == "Revenue"
        )
        assert revenue_dataset["data"] == [1000.0, 1800.0]

    @pytest.mark.asyncio
    async def test_generate_inventory_data(self, dashboard_engine, mock_db_session):
        """Test inventory data generation for widgets"""

        # Mock inventory query result
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(
                product_name="Product A",
                stock_level=50,
                reorder_point=10,
                stock_value=Decimal("500.00"),
            ),
            MagicMock(
                product_name="Product B",
                stock_level=25,
                reorder_point=15,
                stock_value=Decimal("750.00"),
            ),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db_session.execute.return_value = mock_result

        request = DashboardWidgetRequest(
            title="Inventory Widget",
            chart_type=ChartType.BAR,
            data_source="inventory",
            metrics=["stock_level", "stock_value"],
        )

        # Execute inventory data generation
        result = await dashboard_engine._generate_inventory_data(request)

        # Assertions
        assert "labels" in result
        assert result["labels"] == ["Product A", "Product B"]
        assert "datasets" in result
        assert len(result["datasets"]) == 2

    @pytest.mark.asyncio
    async def test_generate_customer_data(self, dashboard_engine, mock_db_session):
        """Test customer data generation for widgets"""

        # Mock customer query result
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(
                registration_date=date(2024, 1, 1), new_customers=5, active_customers=4
            ),
            MagicMock(
                registration_date=date(2024, 1, 2), new_customers=8, active_customers=7
            ),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db_session.execute.return_value = mock_result

        request = DashboardWidgetRequest(
            title="Customer Widget",
            chart_type=ChartType.AREA,
            data_source="customers",
            metrics=["new_customers"],
        )

        # Execute customer data generation
        result = await dashboard_engine._generate_customer_data(request)

        # Assertions
        assert "labels" in result
        assert len(result["labels"]) == 2
        assert "datasets" in result
        assert len(result["datasets"]) == 1
        assert result["datasets"][0]["label"] == "New Customers"
        assert result["datasets"][0]["data"] == [5, 8]

    def test_generate_financial_data(self, dashboard_engine):
        """Test financial data generation for widgets"""

        request = DashboardWidgetRequest(
            title="Financial Widget",
            chart_type=ChartType.GAUGE,
            data_source="financial",
            metrics=["profit_margin"],
        )

        # Execute financial data generation
        result = dashboard_engine._generate_financial_data(request)

        # Assertions (simplified financial data)
        assert "summary" in result
        assert "trends" in result
        assert result["summary"]["total_revenue"] == 125000.00
        assert result["summary"]["profit_margin"] == 30.0


# Unit Tests for ReportBuilder
class TestReportBuilder:
    @pytest.mark.asyncio
    async def test_create_custom_report_success(
        self, report_builder, mock_db_session, sample_user
    ):
        """Test successful custom report creation"""

        # Mock database operations
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()

        # Mock report data generation
        with patch.object(report_builder, "_execute_report_query") as mock_execute:
            mock_execute.return_value = [
                {
                    "order_id": "123",
                    "customer_name": "John Doe",
                    "total_amount": 250.00,
                },
                {
                    "order_id": "124",
                    "customer_name": "Jane Smith",
                    "total_amount": 180.00,
                },
            ]

            request = CustomReportRequest(
                report_name="Sales Report",
                description="Monthly sales analysis",
                report_type=ReportType.SALES,
                data_sources=["orders"],
                columns=["order_id", "customer_name", "total_amount"],
                filters={"status": "completed"},
                date_range={"start": datetime.utcnow() - timedelta(days=30)},
            )

            # Execute report creation
            result = await report_builder.create_custom_report(request, sample_user.id)

            # Assertions
            assert "report_id" in result
            assert result["report_name"] == "Sales Report"
            assert result["report_type"] == ReportType.SALES
            assert result["row_count"] == 2
            assert len(result["data"]) == 2
            assert "generation_time_ms" in result
            assert "generated_at" in result

            # Verify database operations
            mock_db_session.execute.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_custom_report_failure(
        self, report_builder, mock_db_session, sample_user
    ):
        """Test custom report creation failure"""

        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")
        mock_db_session.rollback = AsyncMock()

        request = CustomReportRequest(
            report_name="Test Report",
            report_type=ReportType.SALES,
            data_sources=["orders"],
            columns=["order_id"],
        )

        # Execute report creation - should raise BusinessLogicError
        with pytest.raises(BusinessLogicError, match="Failed to create report"):
            await report_builder.create_custom_report(request, sample_user.id)

        # Verify rollback was called
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_orders_data(self, report_builder, mock_db_session):
        """Test orders data query execution"""

        # Mock orders query result
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(
                _mapping={
                    "order_id": str(uuid4()),
                    "order_number": "ORD-001",
                    "total_amount": Decimal("250.00"),
                    "status": "completed",
                    "customer_name": "John Doe",
                    "customer_email": "john@example.com",
                }
            ),
            MagicMock(
                _mapping={
                    "order_id": str(uuid4()),
                    "order_number": "ORD-002",
                    "total_amount": Decimal("180.00"),
                    "status": "completed",
                    "customer_name": "Jane Smith",
                    "customer_email": "jane@example.com",
                }
            ),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db_session.execute.return_value = mock_result

        request = CustomReportRequest(
            report_name="Orders Report",
            report_type=ReportType.SALES,
            data_sources=["orders"],
            columns=["order_id", "total_amount", "customer_name"],
            filters={"status": "completed"},
            limit=100,
        )

        # Execute orders query
        result = await report_builder._query_orders_data(request)

        # Assertions
        assert len(result) == 2
        assert result[0]["order_number"] == "ORD-001"
        assert result[0]["customer_name"] == "John Doe"
        assert result[1]["order_number"] == "ORD-002"

    @pytest.mark.asyncio
    async def test_query_customers_data(self, report_builder, mock_db_session):
        """Test customers data query execution"""

        # Mock customers query result
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(
                _mapping={
                    "customer_id": str(uuid4()),
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "status": "active",
                    "total_orders": 5,
                    "total_spent": Decimal("1200.00"),
                }
            ),
            MagicMock(
                _mapping={
                    "customer_id": str(uuid4()),
                    "full_name": "Jane Smith",
                    "email": "jane@example.com",
                    "status": "active",
                    "total_orders": 3,
                    "total_spent": Decimal("850.00"),
                }
            ),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db_session.execute.return_value = mock_result

        request = CustomReportRequest(
            report_name="Customer Report",
            report_type=ReportType.CUSTOMER,
            data_sources=["customers"],
            columns=["customer_id", "full_name", "total_orders", "total_spent"],
            filters={"status": "active"},
        )

        # Execute customers query
        result = await report_builder._query_customers_data(request)

        # Assertions
        assert len(result) == 2
        assert result[0]["full_name"] == "John Doe"
        assert result[0]["total_orders"] == 5
        assert result[1]["full_name"] == "Jane Smith"

    @pytest.mark.asyncio
    async def test_query_products_data(self, report_builder, mock_db_session):
        """Test products data query execution"""

        # Mock products query result
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(
                _mapping={
                    "product_id": str(uuid4()),
                    "name": "Product A",
                    "sku": "SKU-001",
                    "unit_cost": Decimal("25.00"),
                    "status": "active",
                    "stock_level": 50,
                }
            ),
            MagicMock(
                _mapping={
                    "product_id": str(uuid4()),
                    "name": "Product B",
                    "sku": "SKU-002",
                    "unit_cost": Decimal("35.00"),
                    "status": "active",
                    "stock_level": 30,
                }
            ),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db_session.execute.return_value = mock_result

        request = CustomReportRequest(
            report_name="Product Report",
            report_type=ReportType.INVENTORY,
            data_sources=["products"],
            columns=["product_id", "name", "sku", "stock_level"],
            filters={"status": "active"},
        )

        # Execute products query
        result = await report_builder._query_products_data(request)

        # Assertions
        assert len(result) == 2
        assert result[0]["name"] == "Product A"
        assert result[0]["stock_level"] == 50
        assert result[1]["name"] == "Product B"

    @pytest.mark.asyncio
    async def test_query_inventory_data(self, report_builder, mock_db_session):
        """Test inventory data query execution"""

        # Mock inventory query result
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(
                _mapping={
                    "product_name": "Product A",
                    "sku": "SKU-001",
                    "stock_level": 50,
                    "reorder_point": 10,
                    "max_stock": 100,
                    "unit_cost": Decimal("25.00"),
                    "stock_value": Decimal("1250.00"),
                }
            ),
            MagicMock(
                _mapping={
                    "product_name": "Product B",
                    "sku": "SKU-002",
                    "stock_level": 30,
                    "reorder_point": 15,
                    "max_stock": 80,
                    "unit_cost": Decimal("35.00"),
                    "stock_value": Decimal("1050.00"),
                }
            ),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db_session.execute.return_value = mock_result

        request = CustomReportRequest(
            report_name="Inventory Report",
            report_type=ReportType.INVENTORY,
            data_sources=["inventory"],
            columns=["product_name", "stock_level", "stock_value"],
            limit=50,
        )

        # Execute inventory query
        result = await report_builder._query_inventory_data(request)

        # Assertions
        assert len(result) == 2
        assert result[0]["product_name"] == "Product A"
        assert result[0]["stock_value"] == Decimal("1250.00")
        assert result[1]["product_name"] == "Product B"


# Unit Tests for BusinessIntelligenceEngine
class TestBusinessIntelligenceEngine:
    @pytest.mark.asyncio
    async def test_generate_insights_success(self, bi_engine, mock_db_session):
        """Test successful insights generation"""

        # Mock component methods
        with (
            patch.object(bi_engine, "_analyze_sales_performance") as mock_sales,
            patch.object(bi_engine, "_analyze_customer_behavior") as mock_customers,
            patch.object(bi_engine, "_analyze_inventory_status") as mock_inventory,
            patch.object(bi_engine, "_analyze_financial_trends") as mock_financial,
        ):
            # Setup mock returns
            mock_sales.return_value = [
                {
                    "insight_id": uuid4(),
                    "title": "Sales Growth",
                    "insight_type": "sales_performance",
                    "severity": "high",
                }
            ]

            mock_customers.return_value = [
                {
                    "insight_id": uuid4(),
                    "title": "Customer Activation",
                    "insight_type": "customer_behavior",
                    "severity": "medium",
                }
            ]

            mock_inventory.return_value = [
                {
                    "insight_id": uuid4(),
                    "title": "Low Stock Alert",
                    "insight_type": "inventory_management",
                    "severity": "high",
                }
            ]

            mock_financial.return_value = [
                {
                    "insight_id": uuid4(),
                    "title": "Financial Health",
                    "insight_type": "financial_analysis",
                    "severity": "low",
                }
            ]

            # Execute insights generation
            insights = await bi_engine.generate_insights("30d")

            # Assertions
            assert len(insights) == 4
            assert insights[0]["insight_type"] == "sales_performance"
            assert insights[1]["insight_type"] == "customer_behavior"
            assert insights[2]["insight_type"] == "inventory_management"
            assert insights[3]["insight_type"] == "financial_analysis"

            # Verify all analysis methods were called
            mock_sales.assert_called_once_with("30d")
            mock_customers.assert_called_once_with("30d")
            mock_inventory.assert_called_once()
            mock_financial.assert_called_once_with("30d")

    @pytest.mark.asyncio
    async def test_analyze_sales_performance(self, bi_engine, mock_db_session):
        """Test sales performance analysis"""

        # Mock current period sales
        current_result = MagicMock()
        current_row = MagicMock()
        current_row.order_count = 50
        current_row.total_revenue = Decimal("10000.00")
        current_row.avg_order_value = Decimal("200.00")
        current_result.fetchone.return_value = current_row

        # Mock previous period sales
        previous_result = MagicMock()
        previous_row = MagicMock()
        previous_row.order_count = 40
        previous_row.total_revenue = Decimal("8000.00")
        previous_row.avg_order_value = Decimal("200.00")
        previous_result.fetchone.return_value = previous_row

        mock_db_session.execute.side_effect = [current_result, previous_result]

        # Execute sales analysis
        insights = await bi_engine._analyze_sales_performance("30d")

        # Assertions
        assert len(insights) == 1
        insight = insights[0]
        assert insight["title"] == "Sales Revenue Surge"
        assert insight["insight_type"] == "sales_performance"
        assert insight["severity"] == "medium"  # 25% increase
        assert insight["supporting_data"]["change_percentage"] == 25.0

    @pytest.mark.asyncio
    async def test_analyze_customer_behavior(self, bi_engine, mock_db_session):
        """Test customer behavior analysis"""

        # Mock customer behavior query result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.new_customers = 100
        mock_row.active_customers = 60  # 60% activation rate
        mock_row.avg_orders_per_customer = 2.5
        mock_result.fetchone.return_value = mock_row

        mock_db_session.execute.return_value = mock_result

        # Execute customer behavior analysis
        insights = await bi_engine._analyze_customer_behavior("30d")

        # Assertions
        assert len(insights) == 1
        insight = insights[0]
        assert insight["title"] == "Low Customer Activation Rate"
        assert insight["insight_type"] == "customer_behavior"
        assert insight["severity"] == "medium"
        assert insight["supporting_data"]["activation_rate"] == 60.0

    @pytest.mark.asyncio
    async def test_analyze_inventory_status(self, bi_engine, mock_db_session):
        """Test inventory status analysis"""

        # Mock inventory query result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.low_stock_items = 20
        mock_row.overstock_items = 5
        mock_row.total_items = 100
        mock_row.total_inventory_value = Decimal("50000.00")
        mock_result.fetchone.return_value = mock_row

        mock_db_session.execute.return_value = mock_result

        # Execute inventory analysis
        insights = await bi_engine._analyze_inventory_status()

        # Assertions
        assert len(insights) == 1
        insight = insights[0]
        assert insight["title"] == "High Number of Low Stock Items"
        assert insight["insight_type"] == "inventory_management"
        assert insight["severity"] == "high"
        assert insight["supporting_data"]["low_stock_ratio"] == 20.0

    @pytest.mark.asyncio
    async def test_analyze_financial_trends(self, bi_engine):
        """Test financial trends analysis"""

        # Execute financial analysis
        insights = await bi_engine._analyze_financial_trends("30d")

        # Assertions (simplified financial analysis)
        assert len(insights) == 1
        insight = insights[0]
        assert insight["title"] == "Financial Health Analysis"
        assert insight["insight_type"] == "financial_analysis"
        assert insight["severity"] == "low"
        assert "revenue_trend" in insight["supporting_data"]


# Unit Tests for KPIManager
class TestKPIManager:
    @pytest.mark.asyncio
    async def test_calculate_kpi_success(self, kpi_manager, mock_db_session):
        """Test successful KPI calculation"""

        kpi_id = uuid4()

        # Mock KPI definition query
        kpi_result = MagicMock()
        kpi_row = MagicMock()
        kpi_row.kpi_name = "Monthly Revenue"
        kpi_row.calculation_formula = "SUM(revenue)"
        kpi_row.data_sources = '["orders"]'
        kpi_row.target_value = Decimal("50000.00")
        kpi_row.warning_threshold = Decimal("40000.00")
        kpi_row.critical_threshold = Decimal("30000.00")
        kpi_row.unit = "USD"
        kpi_row.frequency = "monthly"
        kpi_result.fetchone.return_value = kpi_row

        mock_db_session.execute.return_value = kpi_result

        # Mock KPI calculation methods
        with (
            patch.object(kpi_manager, "_execute_kpi_calculation") as mock_calc,
            patch.object(kpi_manager, "_get_previous_kpi_value") as mock_prev,
        ):
            mock_calc.return_value = Decimal("45000.00")
            mock_prev.return_value = Decimal("42000.00")

            # Execute KPI calculation
            result = await kpi_manager.calculate_kpi(kpi_id)

            # Assertions
            assert result["kpi_id"] == kpi_id
            assert result["kpi_name"] == "Monthly Revenue"
            assert result["current_value"] == Decimal("45000.00")
            assert result["target_value"] == Decimal("50000.00")
            assert result["previous_period_value"] == Decimal("42000.00")
            assert result["change_percentage"] is not None
            assert result["status"] == "warning"  # Below target, above warning
            assert result["trend"] == "up"  # 7.14% increase

    @pytest.mark.asyncio
    async def test_calculate_kpi_not_found(self, kpi_manager, mock_db_session):
        """Test KPI calculation for non-existent KPI"""

        kpi_id = uuid4()

        # Mock KPI not found
        kpi_result = MagicMock()
        kpi_result.fetchone.return_value = None
        mock_db_session.execute.return_value = kpi_result

        # Execute KPI calculation - should raise NotFoundError
        with pytest.raises(NotFoundError, match=f"KPI {kpi_id} not found"):
            await kpi_manager.calculate_kpi(kpi_id)

    @pytest.mark.asyncio
    async def test_execute_kpi_calculation_revenue(self, kpi_manager, mock_db_session):
        """Test KPI calculation execution for revenue formula"""

        # Mock revenue query result
        mock_result = MagicMock()
        mock_result.scalar.return_value = Decimal("25000.00")
        mock_db_session.execute.return_value = mock_result

        # Execute revenue KPI calculation
        result = await kpi_manager._execute_kpi_calculation("SUM(revenue)", ["orders"])

        # Assertions
        assert result == Decimal("25000.00")
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_kpi_calculation_customers(
        self, kpi_manager, mock_db_session
    ):
        """Test KPI calculation execution for customers formula"""

        # Mock customer count query result
        mock_result = MagicMock()
        mock_result.scalar.return_value = 150
        mock_db_session.execute.return_value = mock_result

        # Execute customer KPI calculation
        result = await kpi_manager._execute_kpi_calculation(
            "COUNT(customers)", ["customers"]
        )

        # Assertions
        assert result == Decimal("150")
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_previous_kpi_value(self, kpi_manager, mock_db_session):
        """Test previous KPI value retrieval"""

        kpi_id = uuid4()

        # Mock previous value query result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.value = Decimal("42000.00")
        mock_result.fetchone.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        # Execute previous value retrieval
        result = await kpi_manager._get_previous_kpi_value(kpi_id)

        # Assertions
        assert result == Decimal("42000.00")

    @pytest.mark.asyncio
    async def test_get_previous_kpi_value_not_found(self, kpi_manager, mock_db_session):
        """Test previous KPI value retrieval when no history exists"""

        kpi_id = uuid4()

        # Mock no previous value
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute previous value retrieval
        result = await kpi_manager._get_previous_kpi_value(kpi_id)

        # Assertions
        assert result is None

    def test_determine_kpi_status(self, kpi_manager):
        """Test KPI status determination logic"""

        # Test critical status
        status = kpi_manager._determine_kpi_status(
            Decimal("25000"), Decimal("50000"), Decimal("40000"), Decimal("30000")
        )
        assert status == "critical"

        # Test warning status
        status = kpi_manager._determine_kpi_status(
            Decimal("35000"), Decimal("50000"), Decimal("40000"), Decimal("30000")
        )
        assert status == "warning"

        # Test good status
        status = kpi_manager._determine_kpi_status(
            Decimal("55000"), Decimal("50000"), Decimal("40000"), Decimal("30000")
        )
        assert status == "good"

        # Test neutral status
        status = kpi_manager._determine_kpi_status(
            Decimal("45000"), Decimal("50000"), Decimal("40000"), Decimal("30000")
        )
        assert status == "neutral"


# Unit Tests for ScheduledReportManager
class TestScheduledReportManager:
    @pytest.mark.asyncio
    async def test_create_report_schedule_success(
        self, schedule_manager, mock_db_session, sample_user
    ):
        """Test successful report schedule creation"""

        # Mock database operations
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()

        request = ReportScheduleRequest(
            report_id=uuid4(),
            schedule_name="Daily Sales Report",
            cron_expression="0 9 * * *",  # Daily at 9 AM
            format=ReportFormat.PDF,
            delivery_method=DeliveryMethod.EMAIL,
            recipients=["manager@company.com", "sales@company.com"],
            enabled=True,
            parameters={"include_charts": True},
        )

        # Execute schedule creation
        result = await schedule_manager.create_report_schedule(request, sample_user.id)

        # Assertions
        assert "schedule_id" in result
        assert result["schedule_name"] == "Daily Sales Report"
        assert result["enabled"]
        assert "next_run" in result
        assert "created_at" in result

        # Verify database operations
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_report_schedule_failure(
        self, schedule_manager, mock_db_session, sample_user
    ):
        """Test report schedule creation failure"""

        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")
        mock_db_session.rollback = AsyncMock()

        request = ReportScheduleRequest(
            report_id=uuid4(),
            schedule_name="Test Schedule",
            cron_expression="0 12 * * *",
            format=ReportFormat.JSON,
            delivery_method=DeliveryMethod.EMAIL,
            recipients=["test@example.com"],
        )

        # Execute schedule creation - should raise BusinessLogicError
        with pytest.raises(BusinessLogicError, match="Failed to create schedule"):
            await schedule_manager.create_report_schedule(request, sample_user.id)

        # Verify rollback was called
        mock_db_session.rollback.assert_called_once()

    def test_calculate_next_run_valid_cron(self, schedule_manager):
        """Test next run calculation with valid cron expression"""

        # Test daily at 14:00 (2 PM)
        cron_expression = "0 14 * * *"
        next_run = schedule_manager._calculate_next_run(cron_expression)

        # Assertions
        assert isinstance(next_run, datetime)
        assert next_run.hour == 14
        assert next_run.minute == 0
        assert next_run > datetime.utcnow()

    def test_calculate_next_run_invalid_cron(self, schedule_manager):
        """Test next run calculation with invalid cron expression"""

        # Test invalid cron expression
        cron_expression = "invalid cron"
        next_run = schedule_manager._calculate_next_run(cron_expression)

        # Assertions (should default to next hour)
        assert isinstance(next_run, datetime)
        assert next_run > datetime.utcnow()


# Unit Tests for ReportingAnalyticsManager
class TestReportingAnalyticsManager:
    @pytest.mark.asyncio
    async def test_get_executive_summary_success(
        self, analytics_manager, mock_db_session
    ):
        """Test successful executive summary generation"""

        # Mock component methods
        with (
            patch.object(analytics_manager, "_get_key_metrics") as mock_metrics,
            patch.object(
                analytics_manager.bi_engine, "generate_insights"
            ) as mock_insights,
            patch.object(analytics_manager, "_get_kpi_summary") as mock_kpi,
        ):
            # Setup mock returns
            mock_metrics.return_value = {
                "revenue": {"total_revenue": 100000.0, "total_orders": 500},
                "customers": {"total_customers": 1200, "active_customers": 1000},
            }

            mock_insights.return_value = [
                {"insight_id": uuid4(), "title": "Sales Growth", "severity": "high"},
                {
                    "insight_id": uuid4(),
                    "title": "Customer Retention",
                    "severity": "medium",
                },
            ]

            mock_kpi.return_value = {
                "revenue_growth": {"value": 15.0, "trend": "up", "status": "good"}
            }

            # Execute executive summary generation
            result = await analytics_manager.get_executive_summary()

            # Assertions
            assert "summary_date" in result
            assert "key_metrics" in result
            assert "insights" in result
            assert "kpi_summary" in result
            assert "generated_at" in result

            assert result["key_metrics"]["revenue"]["total_revenue"] == 100000.0
            assert len(result["insights"]) == 2
            assert result["kpi_summary"]["revenue_growth"]["value"] == 15.0

            # Verify all methods were called
            mock_metrics.assert_called_once()
            mock_insights.assert_called_once_with("7d")
            mock_kpi.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_key_metrics_success(self, analytics_manager, mock_db_session):
        """Test key metrics retrieval"""

        # Mock revenue query result
        revenue_result = MagicMock()
        revenue_row = MagicMock()
        revenue_row.total_orders = 150
        revenue_row.total_revenue = Decimal("45000.00")
        revenue_row.avg_order_value = Decimal("300.00")
        revenue_result.fetchone.return_value = revenue_row

        # Mock customer query result
        customer_result = MagicMock()
        customer_row = MagicMock()
        customer_row.total_customers = 800
        customer_row.active_customers = 650
        customer_result.fetchone.return_value = customer_row

        mock_db_session.execute.side_effect = [revenue_result, customer_result]

        # Execute key metrics retrieval
        result = await analytics_manager._get_key_metrics()

        # Assertions
        assert "revenue" in result
        assert "customers" in result
        assert result["revenue"]["total_orders"] == 150
        assert result["revenue"]["total_revenue"] == 45000.0
        assert result["customers"]["total_customers"] == 800
        assert result["customers"]["active_customers"] == 650

    def test_get_kpi_summary(self, analytics_manager):
        """Test KPI summary generation"""

        # Execute KPI summary generation
        result = analytics_manager._get_kpi_summary()

        # Assertions (simplified KPI summary)
        assert "revenue_growth" in result
        assert "customer_acquisition" in result
        assert "inventory_turnover" in result
        assert "customer_satisfaction" in result

        assert result["revenue_growth"]["value"] == 12.5
        assert result["revenue_growth"]["trend"] == "up"
        assert result["revenue_growth"]["status"] == "good"


# Request Model Tests
class TestRequestModels:
    def test_dashboard_widget_request_validation(self):
        """Test dashboard widget request validation"""

        # Valid request
        valid_request = DashboardWidgetRequest(
            title="Sales Dashboard",
            chart_type=ChartType.LINE,
            data_source="sales",
            metrics=["revenue", "orders"],
            dimensions=["date", "region"],
            filters={"status": "completed"},
            time_range="30d",
            refresh_interval=600,
            position={"x": 0, "y": 0, "width": 6, "height": 4},
        )

        assert valid_request.title == "Sales Dashboard"
        assert valid_request.chart_type == ChartType.LINE
        assert len(valid_request.metrics) == 2
        assert valid_request.refresh_interval == 600

        # Test title validation
        with pytest.raises(ValueError):
            DashboardWidgetRequest(
                title="",  # Invalid: empty title
                chart_type=ChartType.BAR,
                data_source="sales",
                metrics=["revenue"],
            )

        # Test refresh interval validation
        with pytest.raises(ValueError):
            DashboardWidgetRequest(
                title="Test Widget",
                chart_type=ChartType.PIE,
                data_source="sales",
                metrics=["revenue"],
                refresh_interval=30,  # Invalid: too low
            )

    def test_custom_report_request_validation(self):
        """Test custom report request validation"""

        # Valid request
        valid_request = CustomReportRequest(
            report_name="Monthly Sales Analysis",
            description="Comprehensive monthly sales report",
            report_type=ReportType.SALES,
            data_sources=["orders", "customers"],
            columns=["order_date", "customer_name", "total_amount"],
            filters={"status": "completed"},
            grouping=["customer_type"],
            aggregations={"total_amount": AggregationType.SUM},
            time_granularity=TimeGranularity.MONTHLY,
            limit=1000,
        )

        assert valid_request.report_name == "Monthly Sales Analysis"
        assert valid_request.report_type == ReportType.SALES
        assert len(valid_request.data_sources) == 2
        assert len(valid_request.columns) == 3
        assert valid_request.time_granularity == TimeGranularity.MONTHLY

        # Test data sources validation
        with pytest.raises(ValueError):
            CustomReportRequest(
                report_name="Test Report",
                report_type=ReportType.SALES,
                data_sources=[],  # Invalid: empty list
                columns=["order_id"],
            )

        # Test limit validation
        with pytest.raises(ValueError):
            CustomReportRequest(
                report_name="Test Report",
                report_type=ReportType.SALES,
                data_sources=["orders"],
                columns=["order_id"],
                limit=15000,  # Invalid: too high
            )

    def test_report_schedule_request_validation(self):
        """Test report schedule request validation"""

        report_id = uuid4()

        # Valid request
        valid_request = ReportScheduleRequest(
            report_id=report_id,
            schedule_name="Daily Revenue Report",
            cron_expression="0 8 * * *",
            format=ReportFormat.EXCEL,
            delivery_method=DeliveryMethod.EMAIL,
            recipients=["manager@company.com", "sales@company.com"],
            enabled=True,
            parameters={"include_charts": True, "currency": "USD"},
        )

        assert valid_request.report_id == report_id
        assert valid_request.schedule_name == "Daily Revenue Report"
        assert valid_request.cron_expression == "0 8 * * *"
        assert valid_request.format == ReportFormat.EXCEL
        assert len(valid_request.recipients) == 2

        # Test cron expression validation
        with pytest.raises(ValueError):
            ReportScheduleRequest(
                report_id=report_id,
                schedule_name="Test Schedule",
                cron_expression="0 8 *",  # Invalid: only 3 parts
                format=ReportFormat.JSON,
                delivery_method=DeliveryMethod.EMAIL,
                recipients=["test@example.com"],
            )

        # Test recipients validation
        with pytest.raises(ValueError):
            ReportScheduleRequest(
                report_id=report_id,
                schedule_name="Test Schedule",
                cron_expression="0 8 * * *",
                format=ReportFormat.JSON,
                delivery_method=DeliveryMethod.EMAIL,
                recipients=[],  # Invalid: empty list
            )

    def test_analytics_query_request_validation(self):
        """Test analytics query request validation"""

        # Valid request
        valid_request = AnalyticsQueryRequest(
            query_name="Customer Segmentation Analysis",
            sql_query="SELECT customer_type, COUNT(*) FROM customers GROUP BY customer_type",
            data_source="customers",
            parameters={"date_from": "2024-01-01"},
            cache_duration=1800,
            visualization_config={
                "chart_type": "pie",
                "colors": ["#FF6384", "#36A2EB"],
            },
        )

        assert valid_request.query_name == "Customer Segmentation Analysis"
        assert valid_request.data_source == "customers"
        assert valid_request.cache_duration == 1800
        assert valid_request.visualization_config is not None

        # Test cache duration validation
        with pytest.raises(ValueError):
            AnalyticsQueryRequest(
                query_name="Test Query",
                data_source="orders",
                cache_duration=90000,  # Invalid: too high
            )

    def test_kpi_definition_request_validation(self):
        """Test KPI definition request validation"""

        # Valid request
        valid_request = KPIDefinitionRequest(
            kpi_name="Monthly Revenue Growth",
            description="Month-over-month revenue growth percentage",
            calculation_formula="(current_month_revenue - last_month_revenue) / last_month_revenue * 100",
            data_sources=["orders", "financial_transactions"],
            target_value=Decimal("15.0"),
            warning_threshold=Decimal("10.0"),
            critical_threshold=Decimal("5.0"),
            unit="%",
            frequency=TimeGranularity.MONTHLY,
        )

        assert valid_request.kpi_name == "Monthly Revenue Growth"
        assert len(valid_request.data_sources) == 2
        assert valid_request.target_value == Decimal("15.0")
        assert valid_request.unit == "%"
        assert valid_request.frequency == TimeGranularity.MONTHLY

        # Test data sources validation
        with pytest.raises(ValueError):
            KPIDefinitionRequest(
                kpi_name="Test KPI",
                calculation_formula="SUM(revenue)",
                data_sources=[],  # Invalid: empty list
            )


# Enum Tests
class TestEnums:
    def test_report_type_enum_values(self):
        """Test report type enum values"""

        assert ReportType.FINANCIAL == "financial"
        assert ReportType.SALES == "sales"
        assert ReportType.INVENTORY == "inventory"
        assert ReportType.CUSTOMER == "customer"
        assert ReportType.OPERATIONAL == "operational"
        assert ReportType.EXECUTIVE == "executive"
        assert ReportType.CUSTOM == "custom"

    def test_chart_type_enum_values(self):
        """Test chart type enum values"""

        assert ChartType.LINE == "line"
        assert ChartType.BAR == "bar"
        assert ChartType.PIE == "pie"
        assert ChartType.AREA == "area"
        assert ChartType.SCATTER == "scatter"
        assert ChartType.HEATMAP == "heatmap"
        assert ChartType.GAUGE == "gauge"
        assert ChartType.TABLE == "table"

    def test_aggregation_type_enum_values(self):
        """Test aggregation type enum values"""

        assert AggregationType.SUM == "sum"
        assert AggregationType.COUNT == "count"
        assert AggregationType.AVERAGE == "average"
        assert AggregationType.MIN == "min"
        assert AggregationType.MAX == "max"
        assert AggregationType.MEDIAN == "median"
        assert AggregationType.DISTINCT_COUNT == "distinct_count"

    def test_time_granularity_enum_values(self):
        """Test time granularity enum values"""

        assert TimeGranularity.HOURLY == "hourly"
        assert TimeGranularity.DAILY == "daily"
        assert TimeGranularity.WEEKLY == "weekly"
        assert TimeGranularity.MONTHLY == "monthly"
        assert TimeGranularity.QUARTERLY == "quarterly"
        assert TimeGranularity.YEARLY == "yearly"

    def test_delivery_method_enum_values(self):
        """Test delivery method enum values"""

        assert DeliveryMethod.EMAIL == "email"
        assert DeliveryMethod.SLACK == "slack"
        assert DeliveryMethod.WEBHOOK == "webhook"
        assert DeliveryMethod.FTP == "ftp"
        assert DeliveryMethod.API == "api"

    def test_report_format_enum_values(self):
        """Test report format enum values"""

        assert ReportFormat.JSON == "json"
        assert ReportFormat.CSV == "csv"
        assert ReportFormat.EXCEL == "excel"
        assert ReportFormat.PDF == "pdf"
        assert ReportFormat.HTML == "html"


# Integration Tests
class TestReportingAnalyticsIntegration:
    @pytest.mark.asyncio
    async def test_complete_dashboard_workflow(
        self, analytics_manager, mock_db_session, sample_user
    ):
        """Test complete dashboard creation and data retrieval workflow"""

        dashboard_id = uuid4()

        # Mock database operations for widget creation
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()

        # Step 1: Create dashboard widget
        widget_request = DashboardWidgetRequest(
            title="Revenue Trends",
            chart_type=ChartType.LINE,
            data_source="sales",
            metrics=["revenue", "orders"],
            time_range="30d",
            refresh_interval=300,
        )

        with patch.object(
            analytics_manager.dashboard_engine, "_generate_widget_data"
        ) as mock_data:
            mock_data.return_value = {"test": "data"}

            widget_result = (
                await analytics_manager.dashboard_engine.create_dashboard_widget(
                    widget_request, sample_user.id
                )
            )

            assert "widget_id" in widget_result
            assert widget_result["title"] == "Revenue Trends"

        # Step 2: Retrieve dashboard data
        mock_widgets_result = MagicMock()
        mock_widget = MagicMock()
        mock_widget.id = str(widget_result["widget_id"])
        mock_widget.title = "Revenue Trends"
        mock_widget.chart_type = "line"
        mock_widget.data_source = "sales"
        mock_widget.metrics = '["revenue", "orders"]'
        mock_widget.dimensions = "[]"
        mock_widget.filters = "{}"
        mock_widget.time_range = "30d"
        mock_widget.refresh_interval = 300
        mock_widget.position = "{}"
        mock_widget.updated_at = datetime.utcnow()

        mock_widgets_result.fetchall.return_value = [mock_widget]
        mock_db_session.execute.return_value = mock_widgets_result

        with patch.object(
            analytics_manager.dashboard_engine, "_generate_widget_data"
        ) as mock_data:
            mock_data.return_value = {"test": "dashboard_data"}

            dashboard_data = (
                await analytics_manager.dashboard_engine.get_dashboard_data(
                    dashboard_id
                )
            )

            assert dashboard_data["dashboard_id"] == dashboard_id
            assert len(dashboard_data["widgets"]) == 1
            assert dashboard_data["widgets"][0]["title"] == "Revenue Trends"

    @pytest.mark.asyncio
    async def test_complete_report_workflow(
        self, analytics_manager, mock_db_session, sample_user
    ):
        """Test complete custom report creation and scheduling workflow"""

        # Mock database operations
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()

        # Step 1: Create custom report
        report_request = CustomReportRequest(
            report_name="Monthly Sales Report",
            description="Comprehensive monthly sales analysis",
            report_type=ReportType.SALES,
            data_sources=["orders"],
            columns=["order_date", "customer_name", "total_amount"],
            filters={"status": "completed"},
        )

        with patch.object(
            analytics_manager.report_builder, "_execute_report_query"
        ) as mock_query:
            mock_query.return_value = [
                {
                    "order_date": "2024-01-01",
                    "customer_name": "John Doe",
                    "total_amount": 250.00,
                }
            ]

            report_result = await analytics_manager.report_builder.create_custom_report(
                report_request, sample_user.id
            )

            assert "report_id" in report_result
            assert report_result["report_name"] == "Monthly Sales Report"
            assert report_result["row_count"] == 1

        # Step 2: Schedule the report
        schedule_request = ReportScheduleRequest(
            report_id=report_result["report_id"],
            schedule_name="Monthly Sales Schedule",
            cron_expression="0 9 1 * *",  # First day of month at 9 AM
            format=ReportFormat.EXCEL,
            delivery_method=DeliveryMethod.EMAIL,
            recipients=["manager@company.com"],
        )

        schedule_result = await analytics_manager.scheduler.create_report_schedule(
            schedule_request, sample_user.id
        )

        assert "schedule_id" in schedule_result
        assert schedule_result["schedule_name"] == "Monthly Sales Schedule"
        assert schedule_result["enabled"]

    @pytest.mark.asyncio
    async def test_complete_analytics_workflow(
        self, analytics_manager, mock_db_session
    ):
        """Test complete analytics workflow with insights and KPIs"""

        # Step 1: Generate business insights
        with patch.object(
            analytics_manager.bi_engine, "_analyze_sales_performance"
        ) as mock_analysis:
            mock_analysis.return_value = [
                {
                    "insight_id": uuid4(),
                    "title": "Revenue Growth",
                    "insight_type": "sales_performance",
                    "severity": "high",
                    "confidence_score": 0.92,
                }
            ]

            insights = await analytics_manager.bi_engine.generate_insights("30d")

            assert len(insights) >= 1
            assert insights[0]["title"] == "Revenue Growth"

        # Step 2: Calculate KPI
        kpi_id = uuid4()

        # Mock KPI definition
        kpi_result = MagicMock()
        kpi_row = MagicMock()
        kpi_row.kpi_name = "Monthly Revenue"
        kpi_row.calculation_formula = "SUM(revenue)"
        kpi_row.data_sources = '["orders"]'
        kpi_row.target_value = Decimal("50000.00")
        kpi_row.warning_threshold = None
        kpi_row.critical_threshold = None
        kpi_row.unit = "USD"
        kpi_row.frequency = "monthly"
        kpi_result.fetchone.return_value = kpi_row

        mock_db_session.execute.return_value = kpi_result

        with patch.object(
            analytics_manager.kpi_manager, "_execute_kpi_calculation"
        ) as mock_calc:
            mock_calc.return_value = Decimal("45000.00")

            kpi_result = await analytics_manager.kpi_manager.calculate_kpi(kpi_id)

            assert kpi_result["kpi_id"] == kpi_id
            assert kpi_result["current_value"] == Decimal("45000.00")

        # Step 3: Generate executive summary
        with (
            patch.object(analytics_manager, "_get_key_metrics") as mock_metrics,
            patch.object(analytics_manager, "_get_kpi_summary") as mock_kpi_summary,
        ):
            mock_metrics.return_value = {"revenue": {"total_revenue": 100000.0}}
            mock_kpi_summary.return_value = {"revenue_growth": {"value": 12.5}}

            summary = await analytics_manager.get_executive_summary()

            assert "key_metrics" in summary
            assert "insights" in summary
            assert "kpi_summary" in summary


# Performance Tests
class TestPerformanceAndScalability:
    @pytest.mark.asyncio
    async def test_dashboard_performance(self, dashboard_engine, mock_db_session):
        """Test dashboard performance with multiple widgets"""

        dashboard_id = uuid4()

        # Mock multiple widgets
        mock_widgets = []
        for i in range(10):
            mock_widget = MagicMock()
            mock_widget.id = str(uuid4())
            mock_widget.title = f"Widget {i}"
            mock_widget.chart_type = "line"
            mock_widget.data_source = "sales"
            mock_widget.metrics = '["revenue"]'
            mock_widget.dimensions = "[]"
            mock_widget.filters = "{}"
            mock_widget.time_range = "30d"
            mock_widget.refresh_interval = 300
            mock_widget.position = "{}"
            mock_widget.updated_at = datetime.utcnow()
            mock_widgets.append(mock_widget)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_widgets
        mock_db_session.execute.return_value = mock_result

        # Mock data generation
        with patch.object(dashboard_engine, "_generate_widget_data") as mock_generate:
            mock_generate.return_value = {"test": "data"}

            # Measure execution time
            import time

            start_time = time.time()

            result = await dashboard_engine.get_dashboard_data(dashboard_id)

            execution_time = time.time() - start_time

            # Assertions
            assert len(result["widgets"]) == 10
            assert execution_time < 5.0  # Should complete within 5 seconds
            assert mock_generate.call_count == 10

    @pytest.mark.asyncio
    async def test_report_generation_performance(
        self, report_builder, mock_db_session, sample_user
    ):
        """Test report generation performance with large dataset"""

        # Mock large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append(
                {
                    "order_id": str(uuid4()),
                    "customer_name": f"Customer {i}",
                    "total_amount": 100.0 + i,
                    "order_date": datetime.utcnow() - timedelta(days=i % 365),
                }
            )

        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()

        with patch.object(report_builder, "_execute_report_query") as mock_query:
            mock_query.return_value = large_dataset

            request = CustomReportRequest(
                report_name="Large Sales Report",
                report_type=ReportType.SALES,
                data_sources=["orders"],
                columns=["order_id", "customer_name", "total_amount"],
                limit=1000,
            )

            # Measure execution time
            import time

            start_time = time.time()

            result = await report_builder.create_custom_report(request, sample_user.id)

            execution_time = time.time() - start_time

            # Assertions
            assert result["row_count"] == 1000
            assert len(result["data"]) == 1000
            assert execution_time < 10.0  # Should complete within 10 seconds

    @pytest.mark.asyncio
    async def test_concurrent_analytics_operations(
        self, analytics_manager, mock_db_session
    ):
        """Test concurrent analytics operations"""

        # Mock database operations
        mock_db_session.execute = AsyncMock()

        # Create multiple concurrent operations
        operations = []

        # Dashboard data retrieval
        operations.append(
            analytics_manager.dashboard_engine.get_dashboard_data(uuid4())
        )

        # Insights generation
        operations.append(analytics_manager.bi_engine.generate_insights("7d"))

        # Executive summary
        operations.append(analytics_manager.get_executive_summary())

        # Mock the operations to avoid actual database calls
        with (
            patch.object(
                analytics_manager.dashboard_engine, "get_dashboard_data"
            ) as mock_dash,
            patch.object(
                analytics_manager.bi_engine, "generate_insights"
            ) as mock_insights,
            patch.object(analytics_manager, "get_executive_summary") as mock_summary,
        ):
            mock_dash.return_value = {"dashboard_id": uuid4(), "widgets": []}
            mock_insights.return_value = [
                {"insight_id": uuid4(), "title": "Test Insight"}
            ]
            mock_summary.return_value = {"key_metrics": {}, "insights": []}

            # Execute operations concurrently
            import asyncio

            start_time = time.time()

            results = await asyncio.gather(*operations, return_exceptions=True)

            execution_time = time.time() - start_time

            # Assertions
            assert len(results) == 3
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == 3
            assert execution_time < 3.0  # Should complete concurrently within 3 seconds


if __name__ == "__main__":
    pytest.main([__file__])
