"""
Tests for CC02 v64.0 Advanced Analytics & Business Intelligence
Comprehensive test suite covering dashboards, data warehouses, OLAP cubes, query builder, and ML
"""

import asyncio
import json
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.api.v1.analytics_bi_v64 import (
    DashboardRequest,
    DashboardResponse,
    DashboardType,
    DataWarehouseManager,
    DataWarehouseRequest,
    DataWarehouseResponse,
    OLAPCubeManager,
    OLAPCubeRequest,
    OLAPCubeResponse,
    PredictiveAnalyticsEngine,
    PredictiveModelRequest,
    PredictiveModelResponse,
    QueryBuilderEngine,
    QueryBuilderRequest,
    QueryExecutionResponse,
    QueryType,
    RealtimeDashboardManager,
    WidgetDataResponse,
)
from app.core.exceptions import BusinessLogicError, NotFoundError


# Test Fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = MagicMock()
    redis_mock.ping.return_value = True
    redis_mock.hset.return_value = True
    redis_mock.hget.return_value = None
    redis_mock.hgetall.return_value = {}
    redis_mock.set.return_value = True
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.exists.return_value = False
    redis_mock.expire.return_value = True
    redis_mock.hincrby.return_value = 1
    return redis_mock


@pytest.fixture
def dashboard_manager_instance(mock_redis):
    """Create dashboard manager instance with mocked Redis"""
    return RealtimeDashboardManager(mock_redis)


@pytest.fixture
def warehouse_manager_instance(mock_redis):
    """Create warehouse manager instance with mocked Redis"""
    return DataWarehouseManager(mock_redis)


@pytest.fixture
def olap_manager_instance(mock_redis):
    """Create OLAP manager instance with mocked Redis"""
    return OLAPCubeManager(mock_redis)


@pytest.fixture
def query_builder_instance(mock_redis):
    """Create query builder instance with mocked Redis"""
    return QueryBuilderEngine(mock_redis)


@pytest.fixture
def ml_engine_instance(mock_redis):
    """Create ML engine instance with mocked Redis"""
    return PredictiveAnalyticsEngine(mock_redis)


@pytest.fixture
def sample_dashboard_request():
    """Sample dashboard request"""
    return DashboardRequest(
        dashboard_type=DashboardType.SALES,
        name="Sales Dashboard",
        description="Comprehensive sales analytics dashboard",
        layout_config={"columns": 12, "rows": 8, "responsive": True},
        widgets=[
            {
                "widget_id": str(uuid4()),
                "widget_type": "chart",
                "title": "Monthly Sales",
                "data_source": "sales_db",
                "query_config": {"table": "orders", "period": "month"},
                "visualization_config": {"chart_type": "line"},
                "position": {"x": 0, "y": 0, "width": 6, "height": 3},
            },
            {
                "widget_id": str(uuid4()),
                "widget_type": "metric",
                "title": "Total Revenue",
                "data_source": "sales_db",
                "query_config": {"metric": "sum", "field": "amount"},
                "visualization_config": {"format": "currency"},
                "position": {"x": 6, "y": 0, "width": 3, "height": 2},
            },
        ],
        refresh_interval_seconds=60,
        filters={"date_range": "last_30_days"},
        permissions=["sales_team", "managers"],
        is_public=False,
        auto_refresh=True,
    )


@pytest.fixture
def sample_warehouse_request():
    """Sample data warehouse request"""
    return DataWarehouseRequest(
        name="Sales Data Warehouse",
        description="Central repository for sales and customer data",
        source_connections=[
            {
                "name": "sales_system",
                "type": "database",
                "connection_string": "postgresql://localhost/sales",
                "tables": ["orders", "customers", "products"],
            },
            {
                "name": "crm_system",
                "type": "api",
                "base_url": "https://api.crm.com",
                "endpoints": ["/customers", "/interactions"],
            },
        ],
        dimension_tables=[
            {
                "name": "customer",
                "source_mapping": {
                    "customer_id": "id",
                    "customer_name": "name",
                    "customer_email": "email",
                },
            },
            {
                "name": "product",
                "source_mapping": {
                    "product_id": "id",
                    "product_name": "name",
                    "category": "category",
                },
            },
        ],
        fact_tables=[
            {
                "name": "sales",
                "measures": ["amount", "quantity", "discount"],
                "dimensions": ["customer", "product", "time"],
            }
        ],
        etl_schedule="0 2 * * *",
        retention_days=730,
        compression_enabled=True,
        partitioning_strategy="date",
    )


@pytest.fixture
def sample_olap_cube_request():
    """Sample OLAP cube request"""
    return OLAPCubeRequest(
        cube_name="Sales Analysis Cube",
        description="Multi-dimensional sales analysis",
        fact_table="fact_sales",
        dimensions=[
            {
                "name": "customer",
                "type": "standard",
                "cardinality": 1000,
                "hierarchy": ["customer_id", "customer_name", "customer_segment"],
            },
            {
                "name": "product",
                "type": "standard",
                "cardinality": 500,
                "hierarchy": ["product_id", "product_name", "category", "subcategory"],
            },
            {
                "name": "time",
                "type": "time",
                "cardinality": 1095,  # 3 years
                "hierarchy": ["year", "quarter", "month", "day"],
            },
        ],
        measures=[
            {"name": "sales_amount", "type": "sum", "format": "currency"},
            {"name": "quantity", "type": "sum", "format": "number"},
            {"name": "avg_price", "type": "average", "format": "currency"},
        ],
        hierarchies=[
            {
                "name": "product_hierarchy",
                "dimension": "product",
                "levels": ["category", "subcategory", "product_name"],
            }
        ],
        aggregation_rules={
            "sales_amount": "sum",
            "quantity": "sum",
            "avg_price": "average",
        },
        build_schedule="0 3 * * *",
        incremental_refresh=True,
    )


@pytest.fixture
def sample_query_request():
    """Sample query builder request"""
    return QueryBuilderRequest(
        query_name="Top Customer Analysis",
        description="Analysis of top customers by revenue",
        query_type=QueryType.AGGREGATE,
        data_sources=["customers", "orders"],
        select_fields=[
            {"field": "customers.name", "alias": "customer_name"},
            {"field": "orders.amount", "aggregation": "sum", "alias": "total_revenue"},
            {
                "field": "orders.order_id",
                "aggregation": "count",
                "alias": "order_count",
            },
        ],
        filters=[
            {"field": "orders.created_at", "operator": ">=", "value": "2024-01-01"},
            {
                "field": "orders.status",
                "operator": "in",
                "value": ["completed", "shipped"],
            },
        ],
        joins=[
            {
                "type": "inner",
                "table": "orders",
                "condition": "customers.id = orders.customer_id",
            }
        ],
        group_by=["customers.id", "customers.name"],
        order_by=[{"field": "total_revenue", "direction": "desc"}],
        limit=50,
    )


@pytest.fixture
def sample_ml_model_request():
    """Sample ML model request"""
    return PredictiveModelRequest(
        model_name="Sales Forecasting Model",
        model_type="time_series",
        description="Predict monthly sales based on historical data",
        training_data_query="SELECT * FROM monthly_sales_data WHERE date >= '2022-01-01'",
        target_variable="sales_amount",
        feature_variables=[
            "month",
            "season",
            "marketing_spend",
            "product_launches",
            "competitor_activity",
            "economic_indicator",
        ],
        hyperparameters={
            "forecast_periods": 12,
            "seasonality": "monthly",
            "trend": "additive",
            "confidence_interval": 0.95,
        },
        validation_split=0.2,
        auto_retrain=True,
        retrain_schedule="0 4 1 * *",
    )


# Unit Tests for RealtimeDashboardManager
class TestRealtimeDashboardManager:
    @pytest.mark.asyncio
    async def test_create_dashboard_success(
        self, dashboard_manager_instance, sample_dashboard_request, mock_redis
    ):
        """Test successful dashboard creation"""

        result = await dashboard_manager_instance.create_dashboard(
            sample_dashboard_request
        )

        assert isinstance(result, DashboardResponse)
        assert result.dashboard_id == sample_dashboard_request.dashboard_id
        assert result.dashboard_type == DashboardType.SALES
        assert result.name == "Sales Dashboard"
        assert result.status == "active"
        assert result.widget_count == 2

        # Verify Redis calls
        mock_redis.hset.assert_called()

        # Verify dashboard is stored in memory
        assert (
            sample_dashboard_request.dashboard_id
            in dashboard_manager_instance.dashboards
        )

    @pytest.mark.asyncio
    async def test_create_dashboard_with_auto_refresh_disabled(
        self, dashboard_manager_instance, mock_redis
    ):
        """Test dashboard creation with auto-refresh disabled"""

        request = DashboardRequest(
            dashboard_type=DashboardType.EXECUTIVE,
            name="Executive Dashboard",
            layout_config={"columns": 12},
            widgets=[],
            auto_refresh=False,
        )

        with patch.object(
            dashboard_manager_instance, "_setup_realtime_streams"
        ) as mock_setup:
            result = await dashboard_manager_instance.create_dashboard(request)

            assert result.status == "active"
            # Verify realtime streams not set up when auto_refresh is False
            mock_setup.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_widget_data_from_cache(
        self, dashboard_manager_instance, mock_redis
    ):
        """Test getting widget data from cache"""

        widget_id = uuid4()

        # Mock widget configuration
        mock_redis.hgetall.return_value = {
            "widget_type": "chart",
            "title": "Test Chart",
            "refresh_interval_seconds": "60",
        }

        # Mock cached data
        cached_data = {"chart_type": "line", "data": [1, 2, 3, 4, 5]}
        mock_redis.get.return_value = json.dumps(cached_data)

        result = await dashboard_manager_instance.get_widget_data(widget_id)

        assert isinstance(result, WidgetDataResponse)
        assert result.widget_id == widget_id
        assert result.widget_type == "chart"
        assert result.title == "Test Chart"
        assert result.data == cached_data
        assert result.metadata["source"] == "cache"

    @pytest.mark.asyncio
    async def test_get_widget_data_fresh(self, dashboard_manager_instance, mock_redis):
        """Test getting fresh widget data"""

        widget_id = uuid4()

        # Mock widget configuration
        mock_redis.hgetall.return_value = {
            "widget_type": "metric",
            "title": "Test Metric",
            "refresh_interval_seconds": "30",
        }

        # Mock no cached data
        mock_redis.get.return_value = None

        with patch.object(
            dashboard_manager_instance, "_generate_widget_data"
        ) as mock_generate:
            mock_generate.return_value = {"metric_type": "kpi", "current_value": 12345}

            result = await dashboard_manager_instance.get_widget_data(widget_id)

            assert result.metadata["source"] == "fresh"
            assert result.data["metric_type"] == "kpi"

            # Verify data was cached
            mock_redis.setex.assert_called()

    @pytest.mark.asyncio
    async def test_get_widget_data_not_found(
        self, dashboard_manager_instance, mock_redis
    ):
        """Test getting widget data for non-existent widget"""

        widget_id = uuid4()
        mock_redis.hgetall.return_value = {}

        with pytest.raises(NotFoundError, match=f"Widget {widget_id} not found"):
            await dashboard_manager_instance.get_widget_data(widget_id)

    @pytest.mark.asyncio
    async def test_generate_chart_data_line(self, dashboard_manager_instance):
        """Test generating line chart data"""

        config = {
            "widget_type": "chart",
            "visualization_config": {"chart_type": "line"},
        }

        result = await dashboard_manager_instance._generate_chart_data(config)

        assert result["chart_type"] == "line"
        assert "data" in result
        assert "labels" in result["data"]
        assert "datasets" in result["data"]
        assert len(result["data"]["datasets"]) == 1

    @pytest.mark.asyncio
    async def test_generate_chart_data_bar(self, dashboard_manager_instance):
        """Test generating bar chart data"""

        config = {"widget_type": "chart", "visualization_config": {"chart_type": "bar"}}

        result = await dashboard_manager_instance._generate_chart_data(config)

        assert result["chart_type"] == "bar"
        assert len(result["data"]["labels"]) == 4  # Q1, Q2, Q3, Q4

    @pytest.mark.asyncio
    async def test_generate_table_data(self, dashboard_manager_instance):
        """Test generating table data"""

        config = {"widget_type": "table"}

        result = await dashboard_manager_instance._generate_table_data(config)

        assert result["table_type"] == "data"
        assert "columns" in result
        assert "rows" in result
        assert len(result["rows"]) == 10
        assert "pagination" in result

    @pytest.mark.asyncio
    async def test_generate_metric_data(self, dashboard_manager_instance):
        """Test generating metric data"""

        config = {"title": "Revenue"}

        result = await dashboard_manager_instance._generate_metric_data(config)

        assert result["metric_type"] == "kpi"
        assert "current_value" in result
        assert "previous_value" in result
        assert "change_percent" in result
        assert result["trend"] in ["up", "down"]

    @pytest.mark.asyncio
    async def test_generate_gauge_data(self, dashboard_manager_instance):
        """Test generating gauge data"""

        config = {"widget_type": "gauge"}

        result = await dashboard_manager_instance._generate_gauge_data(config)

        assert result["gauge_type"] == "progress"
        assert result["max_value"] == 100
        assert "current_value" in result
        assert "percentage" in result
        assert result["color"] in ["red", "yellow", "green"]

    @pytest.mark.asyncio
    async def test_generate_map_data(self, dashboard_manager_instance):
        """Test generating map data"""

        config = {"widget_type": "map"}

        result = await dashboard_manager_instance._generate_map_data(config)

        assert result["map_type"] == "markers"
        assert "center" in result
        assert "locations" in result
        assert "heatmap_data" in result
        assert len(result["locations"]) == 5


# Unit Tests for DataWarehouseManager
class TestDataWarehouseManager:
    @pytest.mark.asyncio
    async def test_create_warehouse_success(
        self, warehouse_manager_instance, sample_warehouse_request, mock_redis
    ):
        """Test successful warehouse creation"""

        with patch.object(
            warehouse_manager_instance, "_schedule_etl_process"
        ) as mock_schedule:
            result = await warehouse_manager_instance.create_warehouse(
                sample_warehouse_request
            )

            assert isinstance(result, DataWarehouseResponse)
            assert result.warehouse_id == sample_warehouse_request.warehouse_id
            assert result.name == "Sales Data Warehouse"
            assert result.status == "initializing"
            assert result.total_tables == 3  # 2 dimension + 1 fact table

            # Verify ETL scheduling
            mock_schedule.assert_called_once()

            # Verify warehouse is stored
            assert (
                sample_warehouse_request.warehouse_id
                in warehouse_manager_instance.warehouses
            )

    @pytest.mark.asyncio
    async def test_run_etl_process_success(
        self, warehouse_manager_instance, sample_warehouse_request, mock_redis
    ):
        """Test successful ETL process execution"""

        warehouse_manager_instance.warehouses[sample_warehouse_request.warehouse_id] = (
            sample_warehouse_request
        )

        with (
            patch.object(warehouse_manager_instance, "_extract_data") as mock_extract,
            patch.object(
                warehouse_manager_instance, "_transform_data"
            ) as mock_transform,
            patch.object(warehouse_manager_instance, "_load_data") as mock_load,
            patch.object(
                warehouse_manager_instance, "_update_etl_metrics"
            ) as mock_metrics,
        ):
            mock_extract.return_value = {"source1": {"records": 1000}}
            mock_transform.return_value = {"dim_customer": {"records": 500}}
            mock_load.return_value = {"records_loaded": 1500, "tables_updated": 3}

            result = await warehouse_manager_instance.run_etl_process(
                sample_warehouse_request.warehouse_id
            )

            assert result["status"] == "completed"
            assert result["records_processed"] == 1500
            assert result["tables_updated"] == 3
            assert "duration_minutes" in result

            # Verify all ETL phases were called
            mock_extract.assert_called_once()
            mock_transform.assert_called_once()
            mock_load.assert_called_once()
            mock_metrics.assert_called_with(
                sample_warehouse_request.warehouse_id, mock.ANY, success=True
            )

    @pytest.mark.asyncio
    async def test_run_etl_process_failure(
        self, warehouse_manager_instance, sample_warehouse_request, mock_redis
    ):
        """Test ETL process failure handling"""

        warehouse_manager_instance.warehouses[sample_warehouse_request.warehouse_id] = (
            sample_warehouse_request
        )

        with (
            patch.object(warehouse_manager_instance, "_extract_data") as mock_extract,
            patch.object(
                warehouse_manager_instance, "_update_etl_metrics"
            ) as mock_metrics,
        ):
            mock_extract.side_effect = Exception("Database connection failed")

            with pytest.raises(BusinessLogicError, match="ETL process failed"):
                await warehouse_manager_instance.run_etl_process(
                    sample_warehouse_request.warehouse_id
                )

            # Verify error metrics update
            mock_metrics.assert_called_with(
                sample_warehouse_request.warehouse_id,
                0,
                success=False,
                error="Database connection failed",
            )

    @pytest.mark.asyncio
    async def test_extract_data(self, warehouse_manager_instance):
        """Test data extraction phase"""

        connections = [
            {"type": "database", "name": "sales_db"},
            {"type": "api", "name": "crm_api"},
        ]

        result = await warehouse_manager_instance._extract_data(connections)

        assert "sales_db" in result
        assert "crm_api" in result
        assert "orders" in result["sales_db"]
        assert "customers" in result["sales_db"]
        assert "api_data" in result["crm_api"]

    @pytest.mark.asyncio
    async def test_transform_data(
        self, warehouse_manager_instance, sample_warehouse_request
    ):
        """Test data transformation phase"""

        extracted_data = {
            "sales_db": {
                "orders": [{"id": 1, "amount": 100}],
                "customers": [{"id": 1, "name": "Test"}],
            }
        }

        result = await warehouse_manager_instance._transform_data(
            extracted_data, sample_warehouse_request
        )

        assert "dim_customer" in result
        assert "dim_product" in result
        assert "fact_sales" in result

        # Verify transformation structure
        assert result["dim_customer"]["records"] == 100
        assert "transformations_applied" in result["dim_customer"]

    @pytest.mark.asyncio
    async def test_load_data(
        self, warehouse_manager_instance, sample_warehouse_request
    ):
        """Test data loading phase"""

        transformed_data = {
            "dim_customer": {"records": 500},
            "dim_product": {"records": 200},
            "fact_sales": {"records": 10000},
        }

        result = await warehouse_manager_instance._load_data(
            transformed_data, sample_warehouse_request
        )

        assert result["records_loaded"] == 10700
        assert result["tables_updated"] == 3
        assert "load_strategy" in result

    def test_generate_sample_data(self, warehouse_manager_instance):
        """Test sample data generation"""

        orders = warehouse_manager_instance._generate_sample_orders(100)
        customers = warehouse_manager_instance._generate_sample_customers(50)
        products = warehouse_manager_instance._generate_sample_products(25)

        assert len(orders) == 100
        assert len(customers) == 50
        assert len(products) == 25

        # Verify data structure
        assert "order_id" in orders[0]
        assert "customer_id" in orders[0]
        assert "amount" in orders[0]

        assert "customer_id" in customers[0]
        assert "name" in customers[0]

        assert "product_id" in products[0]
        assert "category" in products[0]


# Unit Tests for OLAPCubeManager
class TestOLAPCubeManager:
    @pytest.mark.asyncio
    async def test_create_cube_success(
        self, olap_manager_instance, sample_olap_cube_request, mock_redis
    ):
        """Test successful OLAP cube creation"""

        with patch.object(
            olap_manager_instance, "_schedule_cube_build"
        ) as mock_schedule:
            result = await olap_manager_instance.create_cube(sample_olap_cube_request)

            assert isinstance(result, OLAPCubeResponse)
            assert result.cube_id == sample_olap_cube_request.cube_id
            assert result.cube_name == "Sales Analysis Cube"
            assert result.status == "pending_build"
            assert result.dimension_count == 3
            assert result.measure_count == 3

            # Verify cube is stored
            assert sample_olap_cube_request.cube_id in olap_manager_instance.cubes

            # Verify build scheduling
            mock_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_cube_success(
        self, olap_manager_instance, sample_olap_cube_request, mock_redis
    ):
        """Test successful cube building"""

        olap_manager_instance.cubes[sample_olap_cube_request.cube_id] = (
            sample_olap_cube_request
        )

        with (
            patch.object(olap_manager_instance, "_build_dimensions") as mock_dimensions,
            patch.object(olap_manager_instance, "_process_fact_data") as mock_facts,
            patch.object(olap_manager_instance, "_create_aggregations") as mock_agg,
            patch.object(olap_manager_instance, "_store_cube_data") as mock_store,
            patch.object(olap_manager_instance, "_update_cube_metrics") as mock_metrics,
        ):
            mock_dimensions.return_value = {"customer": {"cardinality": 1000}}
            mock_facts.return_value = {"sales_amount": {"total": 1000000}}
            mock_agg.return_value = {"customer_sales_amount": {"pre_calculated": True}}

            result = await olap_manager_instance.build_cube(
                sample_olap_cube_request.cube_id
            )

            assert result["status"] == "completed"
            assert result["dimensions_processed"] == 1
            assert result["measures_calculated"] == 1
            assert result["aggregations_created"] == 1
            assert "build_time_minutes" in result

            # Verify all build phases were called
            mock_dimensions.assert_called_once()
            mock_facts.assert_called_once()
            mock_agg.assert_called_once()
            mock_store.assert_called_once()
            mock_metrics.assert_called_with(
                sample_olap_cube_request.cube_id, mock.ANY, success=True
            )

    @pytest.mark.asyncio
    async def test_build_cube_failure(
        self, olap_manager_instance, sample_olap_cube_request, mock_redis
    ):
        """Test cube building failure"""

        olap_manager_instance.cubes[sample_olap_cube_request.cube_id] = (
            sample_olap_cube_request
        )

        with (
            patch.object(olap_manager_instance, "_build_dimensions") as mock_dimensions,
            patch.object(olap_manager_instance, "_update_cube_metrics") as mock_metrics,
        ):
            mock_dimensions.side_effect = Exception("Dimension build failed")

            with pytest.raises(BusinessLogicError, match="Cube build failed"):
                await olap_manager_instance.build_cube(sample_olap_cube_request.cube_id)

            # Verify error metrics update
            mock_metrics.assert_called_with(
                sample_olap_cube_request.cube_id,
                0,
                success=False,
                error="Dimension build failed",
            )

    @pytest.mark.asyncio
    async def test_query_cube_success(
        self, olap_manager_instance, sample_olap_cube_request, mock_redis
    ):
        """Test successful cube querying"""

        cube_id = sample_olap_cube_request.cube_id

        # Mock cube data exists
        mock_redis.exists.return_value = True

        query_config = {
            "dimensions": ["customer", "product"],
            "measures": ["sales_amount", "quantity"],
            "filters": {"time": "2024"},
        }

        with patch.object(olap_manager_instance, "_execute_cube_query") as mock_query:
            mock_query.return_value = {
                "data": [{"customer": "A", "product": "X", "sales_amount": 1000}],
                "total_rows": 1,
            }

            result = await olap_manager_instance.query_cube(cube_id, query_config)

            assert result["cube_id"] == str(cube_id)
            assert result["dimension_count"] == 2
            assert result["measure_count"] == 2
            assert result["result_cells"] == 1
            assert "query_result" in result

    @pytest.mark.asyncio
    async def test_query_cube_not_built(self, olap_manager_instance, mock_redis):
        """Test querying non-existent cube"""

        cube_id = uuid4()
        mock_redis.exists.return_value = False

        with pytest.raises(NotFoundError, match="Cube .* data not found"):
            await olap_manager_instance.query_cube(cube_id, {})

    @pytest.mark.asyncio
    async def test_build_dimensions(self, olap_manager_instance):
        """Test dimension building"""

        dimensions = [
            {"name": "customer", "type": "standard", "hierarchy": ["id", "name"]},
            {"name": "time", "type": "time", "hierarchy": ["year", "month", "day"]},
        ]

        result = await olap_manager_instance._build_dimensions(dimensions)

        assert "customer" in result
        assert "time" in result
        assert result["time"]["type"] == "time"
        assert "hierarchy_levels" in result["time"]
        assert result["customer"]["type"] == "standard"

    def test_build_time_dimension(self, olap_manager_instance):
        """Test time dimension building"""

        result = olap_manager_instance._build_time_dimension()

        assert result["type"] == "time"
        assert "cardinality" in result
        assert result["hierarchy_levels"] == ["Year", "Quarter", "Month", "Day"]
        assert "data" in result
        assert len(result["data"]) <= 100  # Limited for demonstration

    def test_build_standard_dimension(self, olap_manager_instance):
        """Test standard dimension building"""

        result = olap_manager_instance._build_standard_dimension(
            "product", ["category", "name"]
        )

        assert result["type"] == "standard"
        assert result["name"] == "product"
        assert result["hierarchy_levels"] == ["category", "name"]
        assert "cardinality" in result
        assert "data" in result

    @pytest.mark.asyncio
    async def test_process_fact_data(self, olap_manager_instance):
        """Test fact data processing"""

        measures = [
            {"name": "sales_amount", "type": "sum"},
            {"name": "order_count", "type": "count"},
            {"name": "avg_price", "type": "average"},
        ]

        result = await olap_manager_instance._process_fact_data("fact_sales", measures)

        assert "sales_amount" in result
        assert "order_count" in result
        assert "avg_price" in result

        assert result["sales_amount"]["type"] == "sum"
        assert result["order_count"]["type"] == "count"
        assert result["avg_price"]["type"] == "average"

    @pytest.mark.asyncio
    async def test_create_aggregations(
        self, olap_manager_instance, sample_olap_cube_request
    ):
        """Test aggregation creation"""

        dimensions = {"customer": {}, "product": {}}
        facts = {"sales_amount": {"type": "sum"}, "quantity": {"type": "sum"}}

        result = await olap_manager_instance._create_aggregations(
            sample_olap_cube_request, dimensions, facts
        )

        # Should create aggregations for each dimension-measure combination
        assert len(result) == 4  # 2 dimensions * 2 measures
        assert "customer_sales_amount" in result
        assert "product_quantity" in result

        for agg in result.values():
            assert agg["pre_calculated"] == True
            assert "storage_size_mb" in agg


# Unit Tests for QueryBuilderEngine
class TestQueryBuilderEngine:
    @pytest.mark.asyncio
    async def test_create_query_success(
        self, query_builder_instance, sample_query_request, mock_redis
    ):
        """Test successful query creation"""

        result = await query_builder_instance.create_query(sample_query_request)

        assert result["query_id"] == str(sample_query_request.query_id)
        assert result["query_name"] == "Top Customer Analysis"
        assert result["status"] == "created"
        assert "generated_sql" in result
        assert "estimated_complexity" in result

        # Verify query is stored
        assert sample_query_request.query_id in query_builder_instance.queries

        # Verify Redis storage
        mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_execute_query_success(
        self, query_builder_instance, sample_query_request, mock_redis
    ):
        """Test successful query execution"""

        query_builder_instance.queries[sample_query_request.query_id] = (
            sample_query_request
        )

        # Mock no cached data
        mock_redis.get.return_value = None

        with patch.object(query_builder_instance, "_execute_sql_query") as mock_execute:
            mock_execute.return_value = [
                {
                    "customer_name": "Customer A",
                    "total_revenue": 5000,
                    "order_count": 10,
                },
                {
                    "customer_name": "Customer B",
                    "total_revenue": 3000,
                    "order_count": 8,
                },
            ]

            result = await query_builder_instance.execute_query(
                sample_query_request.query_id
            )

            assert isinstance(result, QueryExecutionResponse)
            assert result.query_id == sample_query_request.query_id
            assert result.status == "completed"
            assert result.result_count == 2
            assert len(result.data) == 2
            assert result.execution_time_ms > 0

            # Verify caching
            mock_redis.setex.assert_called()

    @pytest.mark.asyncio
    async def test_execute_query_from_cache(
        self, query_builder_instance, sample_query_request, mock_redis
    ):
        """Test query execution from cache"""

        query_builder_instance.queries[sample_query_request.query_id] = (
            sample_query_request
        )

        # Mock cached data
        cached_data = [{"customer": "Test", "revenue": 1000}]
        mock_redis.get.return_value = json.dumps(cached_data)

        result = await query_builder_instance.execute_query(
            sample_query_request.query_id
        )

        assert result.status == "completed"
        assert result.data == cached_data
        assert result.result_count == 1

    @pytest.mark.asyncio
    async def test_execute_query_failure(
        self, query_builder_instance, sample_query_request, mock_redis
    ):
        """Test query execution failure"""

        query_builder_instance.queries[sample_query_request.query_id] = (
            sample_query_request
        )
        mock_redis.get.return_value = None

        with patch.object(query_builder_instance, "_execute_sql_query") as mock_execute:
            mock_execute.side_effect = Exception("SQL execution failed")

            result = await query_builder_instance.execute_query(
                sample_query_request.query_id
            )

            assert result.status == "failed"
            assert result.error_message == "SQL execution failed"
            assert result.data is None

    def test_generate_sql_basic_select(self, query_builder_instance):
        """Test basic SQL generation"""

        query = QueryBuilderRequest(
            query_name="Simple Select",
            query_type=QueryType.SELECT,
            data_sources=["customers"],
            select_fields=[{"field": "name"}, {"field": "email"}],
        )

        sql = query_builder_instance._generate_sql(query)

        assert "SELECT name, email" in sql
        assert "FROM customers" in sql

    def test_generate_sql_with_aggregation(self, query_builder_instance):
        """Test SQL generation with aggregation"""

        query = QueryBuilderRequest(
            query_name="Aggregated Query",
            query_type=QueryType.AGGREGATE,
            data_sources=["orders"],
            select_fields=[
                {"field": "customer_id"},
                {"field": "amount", "aggregation": "sum", "alias": "total_amount"},
            ],
            group_by=["customer_id"],
        )

        sql = query_builder_instance._generate_sql(query)

        assert "SELECT customer_id, sum(amount) AS total_amount" in sql
        assert "GROUP BY customer_id" in sql

    def test_generate_sql_with_joins(self, query_builder_instance):
        """Test SQL generation with joins"""

        query = QueryBuilderRequest(
            query_name="Join Query",
            query_type=QueryType.JOIN,
            data_sources=["customers"],
            select_fields=[{"field": "customers.name"}, {"field": "orders.amount"}],
            joins=[
                {
                    "type": "inner",
                    "table": "orders",
                    "condition": "customers.id = orders.customer_id",
                }
            ],
        )

        sql = query_builder_instance._generate_sql(query)

        assert "INNER JOIN orders ON customers.id = orders.customer_id" in sql

    def test_generate_sql_with_filters(self, query_builder_instance):
        """Test SQL generation with filters"""

        query = QueryBuilderRequest(
            query_name="Filtered Query",
            query_type=QueryType.SELECT,
            data_sources=["orders"],
            select_fields=[{"field": "*"}],
            filters=[
                {"field": "status", "operator": "=", "value": "completed"},
                {"field": "amount", "operator": ">", "value": "1000"},
                {"field": "category", "operator": "in", "value": ["A", "B", "C"]},
            ],
        )

        sql = query_builder_instance._generate_sql(query)

        assert (
            "WHERE status = 'completed' AND amount > '1000' AND category IN ('A', 'B', 'C')"
            in sql
        )

    def test_generate_sql_with_order_and_limit(self, query_builder_instance):
        """Test SQL generation with ordering and limit"""

        query = QueryBuilderRequest(
            query_name="Ordered Query",
            query_type=QueryType.SELECT,
            data_sources=["orders"],
            select_fields=[{"field": "*"}],
            order_by=[
                {"field": "amount", "direction": "desc"},
                {"field": "created_at", "direction": "asc"},
            ],
            limit=100,
        )

        sql = query_builder_instance._generate_sql(query)

        assert "ORDER BY amount DESC, created_at ASC" in sql
        assert "LIMIT 100" in sql

    def test_estimate_query_complexity(self, query_builder_instance):
        """Test query complexity estimation"""

        # Simple query
        simple_query = QueryBuilderRequest(
            query_name="Simple",
            query_type=QueryType.SELECT,
            data_sources=["table1"],
            select_fields=[{"field": "id"}, {"field": "name"}],
        )
        assert query_builder_instance._estimate_query_complexity(simple_query) == "low"

        # Complex query
        complex_query = QueryBuilderRequest(
            query_name="Complex",
            query_type=QueryType.SUBQUERY,
            data_sources=["table1"],
            select_fields=[
                {"field": "id"},
                {"field": "amount", "aggregation": "sum"},
                {"field": "count", "aggregation": "count"},
            ],
            joins=[
                {
                    "type": "inner",
                    "table": "table2",
                    "condition": "table1.id = table2.ref_id",
                },
                {
                    "type": "left",
                    "table": "table3",
                    "condition": "table1.id = table3.ref_id",
                },
            ],
        )
        assert (
            query_builder_instance._estimate_query_complexity(complex_query) == "high"
        )

    @pytest.mark.asyncio
    async def test_execute_sql_query(
        self, query_builder_instance, sample_query_request
    ):
        """Test SQL query execution simulation"""

        result = await query_builder_instance._execute_sql_query(sample_query_request)

        assert isinstance(result, list)
        assert len(result) <= 100  # Limited for demo

        if result:
            # Verify structure based on select fields
            row = result[0]
            assert "customers.name" in str(row) or "customer_name" in str(row)

            # Check for aggregated fields
            for field_config in sample_query_request.select_fields:
                if field_config.get("aggregation"):
                    assert field_config["field"] in str(row) or field_config.get(
                        "alias"
                    ) in str(row)


# Unit Tests for PredictiveAnalyticsEngine
class TestPredictiveAnalyticsEngine:
    @pytest.mark.asyncio
    async def test_create_model_success(
        self, ml_engine_instance, sample_ml_model_request, mock_redis
    ):
        """Test successful ML model creation"""

        result = await ml_engine_instance.create_model(sample_ml_model_request)

        assert isinstance(result, PredictiveModelResponse)
        assert result.model_id == sample_ml_model_request.model_id
        assert result.model_name == "Sales Forecasting Model"
        assert result.model_type == "time_series"
        assert result.status == "created"
        assert result.feature_count == 6
        assert result.predictions_made == 0

        # Verify model is stored
        assert sample_ml_model_request.model_id in ml_engine_instance.models

        # Verify Redis storage
        mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_train_model_success(
        self, ml_engine_instance, sample_ml_model_request, mock_redis
    ):
        """Test successful model training"""

        ml_engine_instance.models[sample_ml_model_request.model_id] = (
            sample_ml_model_request
        )

        with (
            patch.object(ml_engine_instance, "_load_training_data") as mock_load,
            patch.object(ml_engine_instance, "_train_ml_model") as mock_train,
            patch.object(ml_engine_instance, "_store_trained_model") as mock_store,
            patch.object(ml_engine_instance, "_update_model_metrics") as mock_metrics,
        ):
            mock_load.return_value = {"records": 5000, "features": [], "target": []}
            mock_train.return_value = {
                "model_type": "time_series",
                "accuracy": 0.85,
                "training_records": 5000,
                "validation_score": 0.82,
            }

            result = await ml_engine_instance.train_model(
                sample_ml_model_request.model_id
            )

            assert result["status"] == "trained"
            assert result["accuracy_score"] == 0.85
            assert result["training_records"] == 5000
            assert result["validation_score"] == 0.82
            assert "training_time_minutes" in result

            # Verify all training phases
            mock_load.assert_called_once()
            mock_train.assert_called_once()
            mock_store.assert_called_once()
            mock_metrics.assert_called()

    @pytest.mark.asyncio
    async def test_train_model_failure(
        self, ml_engine_instance, sample_ml_model_request, mock_redis
    ):
        """Test model training failure"""

        ml_engine_instance.models[sample_ml_model_request.model_id] = (
            sample_ml_model_request
        )

        with (
            patch.object(ml_engine_instance, "_load_training_data") as mock_load,
            patch.object(ml_engine_instance, "_update_model_metrics") as mock_metrics,
        ):
            mock_load.side_effect = Exception("Data loading failed")

            with pytest.raises(BusinessLogicError, match="Model training failed"):
                await ml_engine_instance.train_model(sample_ml_model_request.model_id)

            # Verify error metrics update
            mock_metrics.assert_called_with(
                sample_ml_model_request.model_id, {"error": "Data loading failed"}, 0
            )

    @pytest.mark.asyncio
    async def test_make_prediction_success(
        self, ml_engine_instance, sample_ml_model_request, mock_redis
    ):
        """Test successful prediction"""

        model_id = sample_ml_model_request.model_id
        ml_engine_instance.models[model_id] = sample_ml_model_request

        # Mock trained model exists
        mock_redis.exists.return_value = True

        input_data = {
            "month": 12,
            "season": "winter",
            "marketing_spend": 50000,
            "product_launches": 2,
            "competitor_activity": 3,
            "economic_indicator": 1.05,
        }

        with patch.object(ml_engine_instance, "_execute_prediction") as mock_predict:
            mock_predict.return_value = {
                "prediction": 125000.0,
                "confidence": 0.87,
                "feature_importance": {"marketing_spend": 0.4, "season": 0.3},
                "execution_time_ms": 50,
            }

            result = await ml_engine_instance.make_prediction(model_id, input_data)

            assert result["model_id"] == str(model_id)
            assert result["prediction"] == 125000.0
            assert result["confidence"] == 0.87
            assert "feature_importance" in result
            assert "predicted_at" in result

            # Verify prediction count increment
            mock_redis.hincrby.assert_called_with(
                f"model:metrics:{model_id}", "predictions_made", 1
            )

    @pytest.mark.asyncio
    async def test_make_prediction_model_not_trained(
        self, ml_engine_instance, sample_ml_model_request, mock_redis
    ):
        """Test prediction with untrained model"""

        model_id = sample_ml_model_request.model_id
        mock_redis.exists.return_value = False

        with pytest.raises(NotFoundError, match="Trained model .* not found"):
            await ml_engine_instance.make_prediction(model_id, {})

    @pytest.mark.asyncio
    async def test_make_prediction_missing_features(
        self, ml_engine_instance, sample_ml_model_request, mock_redis
    ):
        """Test prediction with missing features"""

        model_id = sample_ml_model_request.model_id
        ml_engine_instance.models[model_id] = sample_ml_model_request
        mock_redis.exists.return_value = True

        # Missing required features
        input_data = {"month": 12}  # Missing other required features

        with pytest.raises(BusinessLogicError, match="Missing required features"):
            await ml_engine_instance.make_prediction(model_id, input_data)

    @pytest.mark.asyncio
    async def test_load_training_data(self, ml_engine_instance):
        """Test training data loading"""

        query = "SELECT * FROM sales_data WHERE date >= '2022-01-01'"

        result = await ml_engine_instance._load_training_data(query)

        assert "records" in result
        assert "features" in result
        assert "target" in result
        assert "loaded_at" in result
        assert result["records"] >= 1000

    @pytest.mark.asyncio
    async def test_train_ml_model_linear_regression(
        self, ml_engine_instance, sample_ml_model_request
    ):
        """Test linear regression model training"""

        sample_ml_model_request.model_type = "linear_regression"
        training_data = {"records": 5000, "features": [], "target": []}

        result = await ml_engine_instance._train_ml_model(
            sample_ml_model_request, training_data
        )

        assert result["model_type"] == "linear_regression"
        assert "accuracy" in result
        assert "coefficients" in result
        assert "intercept" in result
        assert result["training_records"] == 5000

    @pytest.mark.asyncio
    async def test_train_ml_model_random_forest(
        self, ml_engine_instance, sample_ml_model_request
    ):
        """Test random forest model training"""

        sample_ml_model_request.model_type = "random_forest"
        training_data = {"records": 8000, "features": [], "target": []}

        result = await ml_engine_instance._train_ml_model(
            sample_ml_model_request, training_data
        )

        assert result["model_type"] == "random_forest"
        assert "accuracy" in result
        assert "feature_importance" in result
        assert "n_estimators" in result
        assert result["training_records"] == 8000

    @pytest.mark.asyncio
    async def test_train_ml_model_neural_network(
        self, ml_engine_instance, sample_ml_model_request
    ):
        """Test neural network model training"""

        sample_ml_model_request.model_type = "neural_network"
        sample_ml_model_request.hyperparameters = {
            "epochs": 150,
            "layers": [128, 64, 32],
        }
        training_data = {"records": 10000, "features": [], "target": []}

        result = await ml_engine_instance._train_ml_model(
            sample_ml_model_request, training_data
        )

        assert result["model_type"] == "neural_network"
        assert result["epochs"] == 150
        assert result["layers"] == [128, 64, 32]
        assert "loss" in result

    @pytest.mark.asyncio
    async def test_train_ml_model_time_series(
        self, ml_engine_instance, sample_ml_model_request
    ):
        """Test time series model training"""

        # sample_ml_model_request is already time_series
        training_data = {"records": 3000, "features": [], "target": []}

        result = await ml_engine_instance._train_ml_model(
            sample_ml_model_request, training_data
        )

        assert result["model_type"] == "time_series"
        assert "seasonality" in result
        assert "trend" in result
        assert "forecast_horizon" in result

    @pytest.mark.asyncio
    async def test_execute_prediction_regression(
        self, ml_engine_instance, sample_ml_model_request
    ):
        """Test regression prediction execution"""

        input_data = {"feature1": 100, "feature2": 200}

        result = await ml_engine_instance._execute_prediction(
            sample_ml_model_request, input_data
        )

        assert "prediction" in result
        assert "confidence" in result
        assert "feature_importance" in result
        assert "execution_time_ms" in result
        assert isinstance(result["prediction"], (int, float))

    @pytest.mark.asyncio
    async def test_execute_prediction_classification(
        self, ml_engine_instance, sample_ml_model_request
    ):
        """Test classification prediction execution"""

        sample_ml_model_request.model_type = "classification"
        input_data = {"feature1": 100, "feature2": 200}

        result = await ml_engine_instance._execute_prediction(
            sample_ml_model_request, input_data
        )

        assert "prediction" in result
        assert isinstance(result["prediction"], str)  # Class name
        assert result["confidence"] <= 1.0

    def test_validate_prediction_input_success(
        self, ml_engine_instance, sample_ml_model_request
    ):
        """Test successful prediction input validation"""

        # All required features provided
        input_data = {
            "month": 12,
            "season": "winter",
            "marketing_spend": 50000,
            "product_launches": 2,
            "competitor_activity": 3,
            "economic_indicator": 1.05,
        }

        # Should not raise exception
        ml_engine_instance._validate_prediction_input(
            sample_ml_model_request, input_data
        )

    def test_validate_prediction_input_missing_features(
        self, ml_engine_instance, sample_ml_model_request
    ):
        """Test prediction input validation with missing features"""

        # Missing some required features
        input_data = {
            "month": 12,
            "season": "winter",
            # Missing marketing_spend, product_launches, competitor_activity, economic_indicator
        }

        with pytest.raises(BusinessLogicError, match="Missing required features"):
            ml_engine_instance._validate_prediction_input(
                sample_ml_model_request, input_data
            )


# Integration Tests
class TestAnalyticsIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_dashboard_workflow(
        self, dashboard_manager_instance, mock_redis
    ):
        """Test complete dashboard creation and data retrieval workflow"""

        # 1. Create dashboard
        dashboard_request = DashboardRequest(
            dashboard_type=DashboardType.EXECUTIVE,
            name="Executive Dashboard",
            layout_config={"columns": 12},
            widgets=[
                {
                    "widget_id": str(uuid4()),
                    "widget_type": "chart",
                    "title": "Revenue Trend",
                    "data_source": "finance_db",
                    "query_config": {"metric": "revenue"},
                    "visualization_config": {"chart_type": "line"},
                    "position": {"x": 0, "y": 0, "width": 6, "height": 3},
                }
            ],
        )

        dashboard_result = await dashboard_manager_instance.create_dashboard(
            dashboard_request
        )
        assert dashboard_result.status == "active"

        # 2. Get widget data
        widget_id = UUID(dashboard_request.widgets[0]["widget_id"])

        # Mock widget configuration for data retrieval
        mock_redis.hgetall.return_value = {
            "widget_type": "chart",
            "title": "Revenue Trend",
            "refresh_interval_seconds": "60",
        }
        mock_redis.get.return_value = None  # No cache

        widget_result = await dashboard_manager_instance.get_widget_data(widget_id)
        assert widget_result.widget_type == "chart"
        assert widget_result.title == "Revenue Trend"

    @pytest.mark.asyncio
    async def test_end_to_end_warehouse_etl_workflow(
        self, warehouse_manager_instance, mock_redis
    ):
        """Test complete warehouse creation and ETL workflow"""

        # 1. Create warehouse
        warehouse_request = DataWarehouseRequest(
            name="Integration Test Warehouse",
            source_connections=[{"name": "test_db", "type": "database"}],
            dimension_tables=[
                {"name": "customer", "source_mapping": {"id": "customer_id"}}
            ],
            fact_tables=[{"name": "sales", "measures": ["amount"]}],
        )

        warehouse_result = await warehouse_manager_instance.create_warehouse(
            warehouse_request
        )
        assert warehouse_result.status == "initializing"

        # 2. Run ETL process
        with (
            patch.object(warehouse_manager_instance, "_extract_data") as mock_extract,
            patch.object(
                warehouse_manager_instance, "_transform_data"
            ) as mock_transform,
            patch.object(warehouse_manager_instance, "_load_data") as mock_load,
        ):
            mock_extract.return_value = {"test_db": {"records": 1000}}
            mock_transform.return_value = {"dim_customer": {"records": 500}}
            mock_load.return_value = {"records_loaded": 1500, "tables_updated": 2}

            etl_result = await warehouse_manager_instance.run_etl_process(
                warehouse_request.warehouse_id
            )
            assert etl_result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_end_to_end_olap_cube_workflow(
        self, olap_manager_instance, mock_redis
    ):
        """Test complete OLAP cube creation, build, and query workflow"""

        # 1. Create cube
        cube_request = OLAPCubeRequest(
            cube_name="Integration Test Cube",
            fact_table="fact_sales",
            dimensions=[{"name": "customer", "type": "standard", "cardinality": 100}],
            measures=[{"name": "sales_amount", "type": "sum"}],
        )

        cube_result = await olap_manager_instance.create_cube(cube_request)
        assert cube_result.status == "pending_build"

        # 2. Build cube
        with (
            patch.object(olap_manager_instance, "_build_dimensions") as mock_dims,
            patch.object(olap_manager_instance, "_process_fact_data") as mock_facts,
            patch.object(olap_manager_instance, "_create_aggregations") as mock_agg,
            patch.object(olap_manager_instance, "_store_cube_data") as mock_store,
        ):
            mock_dims.return_value = {"customer": {"cardinality": 100}}
            mock_facts.return_value = {"sales_amount": {"total": 100000}}
            mock_agg.return_value = {"customer_sales_amount": {"pre_calculated": True}}

            build_result = await olap_manager_instance.build_cube(cube_request.cube_id)
            assert build_result["status"] == "completed"

        # 3. Query cube
        mock_redis.exists.return_value = True

        with patch.object(olap_manager_instance, "_execute_cube_query") as mock_query:
            mock_query.return_value = {
                "data": [{"customer": "A", "sales_amount": 1000}]
            }

            query_result = await olap_manager_instance.query_cube(
                cube_request.cube_id,
                {"dimensions": ["customer"], "measures": ["sales_amount"]},
            )
            assert "query_result" in query_result

    @pytest.mark.asyncio
    async def test_end_to_end_ml_workflow(self, ml_engine_instance, mock_redis):
        """Test complete ML model creation, training, and prediction workflow"""

        # 1. Create model
        model_request = PredictiveModelRequest(
            model_name="Integration Test Model",
            model_type="linear_regression",
            training_data_query="SELECT * FROM test_data",
            target_variable="target",
            feature_variables=["feature1", "feature2"],
        )

        model_result = await ml_engine_instance.create_model(model_request)
        assert model_result.status == "created"

        # 2. Train model
        with (
            patch.object(ml_engine_instance, "_load_training_data") as mock_load,
            patch.object(ml_engine_instance, "_train_ml_model") as mock_train,
            patch.object(ml_engine_instance, "_store_trained_model") as mock_store,
        ):
            mock_load.return_value = {"records": 1000, "features": [], "target": []}
            mock_train.return_value = {
                "model_type": "linear_regression",
                "accuracy": 0.85,
                "training_records": 1000,
            }

            train_result = await ml_engine_instance.train_model(model_request.model_id)
            assert train_result["status"] == "trained"

        # 3. Make prediction
        mock_redis.exists.return_value = True

        with patch.object(ml_engine_instance, "_execute_prediction") as mock_predict:
            mock_predict.return_value = {
                "prediction": 123.45,
                "confidence": 0.87,
                "feature_importance": {"feature1": 0.6, "feature2": 0.4},
            }

            prediction_result = await ml_engine_instance.make_prediction(
                model_request.model_id, {"feature1": 100, "feature2": 200}
            )
            assert prediction_result["prediction"] == 123.45

    @pytest.mark.asyncio
    async def test_end_to_end_query_builder_workflow(
        self, query_builder_instance, mock_redis
    ):
        """Test complete query builder creation and execution workflow"""

        # 1. Create query
        query_request = QueryBuilderRequest(
            query_name="Integration Test Query",
            query_type=QueryType.SELECT,
            data_sources=["test_table"],
            select_fields=[{"field": "id"}, {"field": "name"}],
        )

        query_result = await query_builder_instance.create_query(query_request)
        assert query_result["status"] == "created"

        # 2. Execute query
        mock_redis.get.return_value = None  # No cache

        with patch.object(query_builder_instance, "_execute_sql_query") as mock_execute:
            mock_execute.return_value = [{"id": 1, "name": "Test"}]

            execution_result = await query_builder_instance.execute_query(
                query_request.query_id
            )
            assert execution_result.status == "completed"
            assert execution_result.result_count == 1


# Performance Tests
class TestPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_widget_data_requests(
        self, dashboard_manager_instance, mock_redis
    ):
        """Test concurrent widget data requests"""

        # Setup multiple widgets
        widget_ids = [uuid4() for _ in range(10)]

        # Mock widget configurations
        mock_redis.hgetall.return_value = {
            "widget_type": "metric",
            "title": "Test Metric",
            "refresh_interval_seconds": "60",
        }
        mock_redis.get.return_value = None  # No cache

        # Execute concurrent requests
        tasks = [
            dashboard_manager_instance.get_widget_data(widget_id)
            for widget_id in widget_ids
        ]

        results = await asyncio.gather(*tasks)

        # Verify all requests succeeded
        assert len(results) == 10
        for result in results:
            assert isinstance(result, WidgetDataResponse)
            assert result.widget_type == "metric"

    @pytest.mark.asyncio
    async def test_concurrent_model_predictions(self, ml_engine_instance, mock_redis):
        """Test concurrent model predictions"""

        model_id = uuid4()
        model_request = PredictiveModelRequest(
            model_name="Perf Test Model",
            model_type="linear_regression",
            training_data_query="SELECT * FROM data",
            target_variable="target",
            feature_variables=["feature1", "feature2"],
        )

        ml_engine_instance.models[model_id] = model_request
        mock_redis.exists.return_value = True

        # Mock prediction execution
        with patch.object(ml_engine_instance, "_execute_prediction") as mock_predict:
            mock_predict.return_value = {
                "prediction": 100.0,
                "confidence": 0.8,
                "feature_importance": {"feature1": 0.6, "feature2": 0.4},
            }

            # Execute concurrent predictions
            input_data = {"feature1": 100, "feature2": 200}
            tasks = [
                ml_engine_instance.make_prediction(model_id, input_data)
                for _ in range(20)
            ]

            results = await asyncio.gather(*tasks)

            # Verify all predictions succeeded
            assert len(results) == 20
            for result in results:
                assert result["prediction"] == 100.0
                assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_large_query_result_handling(
        self, query_builder_instance, mock_redis
    ):
        """Test handling of large query results"""

        query_request = QueryBuilderRequest(
            query_name="Large Result Query",
            query_type=QueryType.SELECT,
            data_sources=["large_table"],
            select_fields=[{"field": "*"}],
            limit=10000,
        )

        query_builder_instance.queries[query_request.query_id] = query_request
        mock_redis.get.return_value = None

        # Mock large result set
        with patch.object(query_builder_instance, "_execute_sql_query") as mock_execute:
            # Generate large result set (but limited to 100 for performance)
            large_result = [{"id": i, "data": f"row_{i}"} for i in range(100)]
            mock_execute.return_value = large_result

            result = await query_builder_instance.execute_query(query_request.query_id)

            assert result.status == "completed"
            assert result.result_count == 100
            assert len(result.data) == 100


# Error Handling Tests
class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_dashboard_redis_connection_failure(self, mock_redis):
        """Test dashboard manager behavior when Redis fails"""

        mock_redis.hset.side_effect = Exception("Redis connection failed")

        manager = RealtimeDashboardManager(mock_redis)
        request = DashboardRequest(
            dashboard_type=DashboardType.SALES,
            name="Test Dashboard",
            layout_config={},
            widgets=[],
        )

        with pytest.raises(BusinessLogicError, match="Failed to create dashboard"):
            await manager.create_dashboard(request)

    @pytest.mark.asyncio
    async def test_warehouse_etl_extraction_failure(self, warehouse_manager_instance):
        """Test warehouse ETL failure during extraction"""

        request = DataWarehouseRequest(
            name="Test Warehouse",
            source_connections=[{"name": "failing_db", "type": "database"}],
            dimension_tables=[],
            fact_tables=[],
        )

        warehouse_manager_instance.warehouses[request.warehouse_id] = request

        with patch.object(warehouse_manager_instance, "_extract_data") as mock_extract:
            mock_extract.side_effect = Exception("Database connection timeout")

            with pytest.raises(BusinessLogicError, match="ETL process failed"):
                await warehouse_manager_instance.run_etl_process(request.warehouse_id)

    @pytest.mark.asyncio
    async def test_olap_cube_build_dimension_failure(self, olap_manager_instance):
        """Test OLAP cube build failure during dimension processing"""

        request = OLAPCubeRequest(
            cube_name="Test Cube",
            fact_table="fact_test",
            dimensions=[{"name": "failing_dim", "type": "standard"}],
            measures=[{"name": "test_measure", "type": "sum"}],
        )

        olap_manager_instance.cubes[request.cube_id] = request

        with patch.object(olap_manager_instance, "_build_dimensions") as mock_dims:
            mock_dims.side_effect = Exception("Dimension schema error")

            with pytest.raises(BusinessLogicError, match="Cube build failed"):
                await olap_manager_instance.build_cube(request.cube_id)

    @pytest.mark.asyncio
    async def test_query_builder_sql_generation_error(self, query_builder_instance):
        """Test query builder SQL generation error handling"""

        # Create invalid query that would cause SQL generation issues
        request = QueryBuilderRequest(
            query_name="Invalid Query",
            query_type=QueryType.SELECT,
            data_sources=[],  # No data sources
            select_fields=[],  # No fields
        )

        # Should handle gracefully or raise appropriate error
        try:
            await query_builder_instance.create_query(request)
        except BusinessLogicError:
            # Expected for invalid configuration
            pass

    @pytest.mark.asyncio
    async def test_ml_model_training_data_corruption(self, ml_engine_instance):
        """Test ML model handling of corrupted training data"""

        request = PredictiveModelRequest(
            model_name="Test Model",
            model_type="linear_regression",
            training_data_query="SELECT * FROM corrupted_data",
            target_variable="target",
            feature_variables=["feature1"],
        )

        ml_engine_instance.models[request.model_id] = request

        with patch.object(ml_engine_instance, "_load_training_data") as mock_load:
            mock_load.side_effect = Exception("Data corruption detected")

            with pytest.raises(BusinessLogicError, match="Model training failed"):
                await ml_engine_instance.train_model(request.model_id)


if __name__ == "__main__":
    pytest.main([__file__])
