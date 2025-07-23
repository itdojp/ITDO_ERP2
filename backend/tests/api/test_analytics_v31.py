"""
Analytics System API Tests - CC02 v31.0 Phase 2

Comprehensive test suite for analytics API including:
- Multi-Dimensional Analytics & KPI Tracking
- Real-Time Data Processing & Aggregation
- Advanced Business Intelligence & Reporting
- Performance Metrics & Benchmarking
- Predictive Analytics & Forecasting
- Custom Dashboard & Visualization
- Data Mining & Machine Learning Integration
- Executive Analytics & Strategic Insights
- Operational Analytics & Process Optimization
- Compliance Analytics & Risk Management
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.analytics_extended import (
    AnalyticsAlert,
    AnalyticsDashboard,
    AnalyticsDataPoint,
    AnalyticsDataSource,
    AnalyticsInsight,
    AnalyticsMetric,
    AnalyticsPrediction,
    AnalyticsReport,
    AnalyticsReportExecution,
    ReportStatus,
)

client = TestClient(app)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_db_session():
    """Mock database session fixture."""
    session = MagicMock(spec=Session)
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def sample_data_source_data():
    """Sample data source data for testing."""
    return {
        "organization_id": "test-org-123",
        "name": "Sales Database",
        "code": "SALES_DB",
        "description": "Primary sales data source",
        "source_type": "database",
        "connection_string": "postgresql://localhost/sales",
        "connection_config": {"host": "localhost", "port": 5432},
        "authentication_config": {"username": "sales_user"},
        "schema_definition": {"tables": ["sales", "customers"]},
        "sync_frequency": "daily",
        "sync_schedule": "0 2 * * *",
        "validation_rules": {"required_fields": ["id", "date"]},
        "is_active": True,
        "is_realtime": False,
        "created_by": "user-123",
    }


@pytest.fixture
def sample_metric_data():
    """Sample metric data for testing."""
    return {
        "organization_id": "test-org-123",
        "data_source_id": "ds-123",
        "name": "Monthly Revenue",
        "code": "MONTHLY_REVENUE",
        "display_name": "Monthly Revenue ($)",
        "description": "Total monthly revenue calculation",
        "category": "financial",
        "metric_type": "currency",
        "analytics_type": "financial",
        "aggregation_type": "sum",
        "calculation_formula": "SUM(amount) WHERE status = 'completed'",
        "calculation_fields": ["amount", "status"],
        "unit": "USD",
        "format_pattern": "${0:,.2f}",
        "decimal_places": 2,
        "target_value": Decimal("100000.00"),
        "calculation_frequency": "daily",
        "is_active": True,
        "created_by": "user-123",
    }


@pytest.fixture
def sample_dashboard_data():
    """Sample dashboard data for testing."""
    return {
        "organization_id": "test-org-123",
        "name": "Executive Dashboard",
        "slug": "executive-dashboard",
        "description": "Executive overview dashboard",
        "dashboard_type": "executive",
        "layout_config": {"columns": 3, "rows": 4},
        "widgets": [
            {"id": "revenue", "type": "metric", "position": {"x": 0, "y": 0}},
            {"id": "customers", "type": "chart", "position": {"x": 1, "y": 0}},
        ],
        "global_filters": {"date_range": "last_30_days"},
        "is_public": False,
        "is_shared": True,
        "theme": "default",
        "created_by": "user-123",
    }


@pytest.fixture
def sample_report_data():
    """Sample report data for testing."""
    return {
        "organization_id": "test-org-123",
        "name": "Monthly Financial Report",
        "title": "Monthly Financial Analysis Report",
        "description": "Comprehensive monthly financial analysis",
        "report_type": "financial",
        "metrics": ["metric-123", "metric-456"],
        "dashboards": ["dashboard-123"],
        "parameters": {"period": "monthly", "currency": "USD"},
        "filters": {"department": ["sales", "marketing"]},
        "is_scheduled": True,
        "schedule_config": {"frequency": "monthly", "day": 1},
        "schedule_cron": "0 9 1 * *",
        "format": "pdf",
        "recipients": ["admin@company.com", "finance@company.com"],
        "delivery_method": "email",
        "created_by": "user-123",
    }


@pytest.fixture
def sample_alert_data():
    """Sample alert data for testing."""
    return {
        "organization_id": "test-org-123",
        "metric_id": "metric-123",
        "name": "Revenue Alert",
        "description": "Alert when revenue drops below threshold",
        "alert_type": "threshold",
        "conditions": {"operator": "less_than", "value": 50000, "period": "daily"},
        "evaluation_frequency": "hourly",
        "priority": "high",
        "notification_channels": ["email", "slack"],
        "notification_recipients": ["admin@company.com"],
        "is_active": True,
        "created_by": "user-123",
    }


@pytest.fixture
def sample_prediction_data():
    """Sample prediction data for testing."""
    return {
        "organization_id": "test-org-123",
        "metric_id": "metric-123",
        "name": "Revenue Forecast",
        "description": "Monthly revenue forecasting model",
        "prediction_type": "forecast",
        "model_type": "linear_regression",
        "model_parameters": {"lookback_days": 90, "features": ["seasonality"]},
        "feature_columns": ["month", "year", "previous_revenue"],
        "target_column": "revenue",
        "prediction_horizon": 90,
        "update_frequency": "weekly",
        "is_active": True,
        "created_by": "user-123",
    }


# =============================================================================
# Data Source API Tests
# =============================================================================


class TestDataSourceAPI:
    """Test cases for analytics data source API endpoints."""

    @patch("app.crud.analytics_v31.analytics_service.create_data_source")
    def test_create_data_source_success(self, mock_create, sample_data_source_data):
        """Test successful data source creation."""
        # Mock service response
        mock_data_source = AnalyticsDataSource(**sample_data_source_data)
        mock_data_source.id = "ds-123"
        mock_data_source.created_at = datetime.now()
        mock_create.return_value = mock_data_source

        response = client.post(
            "/api/v1/analytics_v31/data-sources", json=sample_data_source_data
        )

        assert response.status_code == 201
        assert response.json()["id"] == "ds-123"
        assert response.json()["name"] == "Sales Database"
        mock_create.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.create_data_source")
    def test_create_data_source_validation_error(
        self, mock_create, sample_data_source_data
    ):
        """Test data source creation with validation error."""
        mock_create.side_effect = ValueError("Invalid connection string")

        response = client.post(
            "/api/v1/analytics_v31/data-sources", json=sample_data_source_data
        )

        assert response.status_code == 400
        assert "Invalid connection string" in response.json()["detail"]

    @patch("app.crud.analytics_v31.analytics_service.list_data_sources")
    def test_list_data_sources_success(self, mock_list):
        """Test successful data source listing."""
        mock_list.return_value = {
            "data_sources": [],
            "total_count": 0,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        response = client.get(
            "/api/v1/analytics_v31/data-sources?organization_id=test-org-123"
        )

        assert response.status_code == 200
        assert response.json()["total_count"] == 0
        mock_list.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.get_data_source")
    def test_get_data_source_success(self, mock_get, sample_data_source_data):
        """Test successful data source retrieval."""
        mock_data_source = AnalyticsDataSource(**sample_data_source_data)
        mock_data_source.id = "ds-123"
        mock_get.return_value = mock_data_source

        response = client.get("/api/v1/analytics_v31/data-sources/ds-123")

        assert response.status_code == 200
        assert response.json()["id"] == "ds-123"
        mock_get.assert_called_once_with(mock_get.call_args[0][0], "ds-123")

    @patch("app.crud.analytics_v31.analytics_service.get_data_source")
    def test_get_data_source_not_found(self, mock_get):
        """Test data source retrieval when not found."""
        mock_get.return_value = None

        response = client.get("/api/v1/analytics_v31/data-sources/nonexistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "Data source not found"

    @patch("app.crud.analytics_v31.analytics_service.test_data_source_connection")
    def test_test_data_source_connection_success(self, mock_test):
        """Test successful data source connection testing."""
        mock_test.return_value = {
            "status": "success",
            "connection_time_ms": 150,
            "schema_info": {"tables": ["sales", "customers"]},
        }

        test_request = {"test_query": "SELECT 1", "timeout_seconds": 30}
        response = client.post(
            "/api/v1/analytics_v31/data-sources/ds-123/test-connection",
            json=test_request,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_test.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.sync_data_source")
    def test_sync_data_source_success(self, mock_sync):
        """Test successful data source synchronization."""
        mock_sync.return_value = {
            "status": "completed",
            "records_processed": 1000,
            "duration_ms": 5000,
            "errors": [],
        }

        sync_request = {"full_sync": False, "batch_size": 1000}
        response = client.post(
            "/api/v1/analytics_v31/data-sources/ds-123/sync", json=sync_request
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["records_processed"] == 1000
        mock_sync.assert_called_once()


# =============================================================================
# Metrics API Tests
# =============================================================================


class TestMetricsAPI:
    """Test cases for analytics metrics API endpoints."""

    @patch("app.crud.analytics_v31.analytics_service.create_metric")
    def test_create_metric_success(self, mock_create, sample_metric_data):
        """Test successful metric creation."""
        mock_metric = AnalyticsMetric(**sample_metric_data)
        mock_metric.id = "metric-123"
        mock_metric.created_at = datetime.now()
        mock_create.return_value = mock_metric

        response = client.post("/api/v1/analytics_v31/metrics", json=sample_metric_data)

        assert response.status_code == 201
        assert response.json()["id"] == "metric-123"
        assert response.json()["name"] == "Monthly Revenue"
        mock_create.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.list_metrics")
    def test_list_metrics_with_filters(self, mock_list):
        """Test metric listing with filters."""
        mock_list.return_value = {
            "metrics": [],
            "total_count": 0,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        response = client.get(
            "/api/v1/analytics_v31/metrics"
            "?organization_id=test-org-123"
            "&analytics_type=financial"
            "&is_active=true"
        )

        assert response.status_code == 200
        mock_list.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.calculate_metric")
    def test_calculate_metric_success(self, mock_calculate):
        """Test successful metric calculation."""
        mock_calculate.return_value = {
            "metric_id": "metric-123",
            "value": 85000.50,
            "calculated_at": datetime.now().isoformat(),
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "data_points": 31,
        }

        calc_request = {
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "force_recalculate": True,
        }
        response = client.post(
            "/api/v1/analytics_v31/metrics/metric-123/calculate", json=calc_request
        )

        assert response.status_code == 200
        assert response.json()["value"] == 85000.50
        mock_calculate.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.compare_metrics")
    def test_compare_metrics_success(self, mock_compare):
        """Test successful metric comparison."""
        mock_compare.return_value = {
            "comparison_id": "comp-123",
            "metrics": ["metric-123", "metric-456"],
            "periods": ["2024-01", "2024-02"],
            "results": [
                {"metric": "metric-123", "period": "2024-01", "value": 75000},
                {"metric": "metric-123", "period": "2024-02", "value": 85000},
            ],
            "trends": {"metric-123": {"direction": "up", "percentage": 13.33}},
        }

        compare_request = {
            "metric_ids": ["metric-123", "metric-456"],
            "periods": [
                {"start": "2024-01-01", "end": "2024-01-31"},
                {"start": "2024-02-01", "end": "2024-02-29"},
            ],
            "comparison_type": "period_over_period",
        }
        response = client.post(
            "/api/v1/analytics_v31/metrics/compare", json=compare_request
        )

        assert response.status_code == 200
        assert "comparison_id" in response.json()
        mock_compare.assert_called_once()


# =============================================================================
# Dashboard API Tests
# =============================================================================


class TestDashboardAPI:
    """Test cases for analytics dashboard API endpoints."""

    @patch("app.crud.analytics_v31.analytics_service.create_dashboard")
    def test_create_dashboard_success(self, mock_create, sample_dashboard_data):
        """Test successful dashboard creation."""
        mock_dashboard = AnalyticsDashboard(**sample_dashboard_data)
        mock_dashboard.id = "dashboard-123"
        mock_dashboard.created_at = datetime.now()
        mock_create.return_value = mock_dashboard

        response = client.post(
            "/api/v1/analytics_v31/dashboards", json=sample_dashboard_data
        )

        assert response.status_code == 201
        assert response.json()["id"] == "dashboard-123"
        assert response.json()["name"] == "Executive Dashboard"
        mock_create.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.export_dashboard")
    def test_export_dashboard_success(self, mock_export):
        """Test successful dashboard export."""
        mock_export.return_value = {
            "export_id": "export-123",
            "format": "pdf",
            "file_path": "/tmp/dashboard_export.pdf",
            "file_size": 2048576,
            "generated_at": datetime.now().isoformat(),
        }

        export_request = {
            "format": "pdf",
            "include_data": True,
            "date_range": {"start": "2024-01-01", "end": "2024-01-31"},
        }
        response = client.post(
            "/api/v1/analytics_v31/dashboards/dashboard-123/export", json=export_request
        )

        assert response.status_code == 200
        assert response.json()["format"] == "pdf"
        mock_export.assert_called_once()


# =============================================================================
# Report API Tests
# =============================================================================


class TestReportAPI:
    """Test cases for analytics report API endpoints."""

    @patch("app.crud.analytics_v31.analytics_service.create_report")
    def test_create_report_success(self, mock_create, sample_report_data):
        """Test successful report creation."""
        mock_report = AnalyticsReport(**sample_report_data)
        mock_report.id = "report-123"
        mock_report.created_at = datetime.now()
        mock_create.return_value = mock_report

        response = client.post("/api/v1/analytics_v31/reports", json=sample_report_data)

        assert response.status_code == 201
        assert response.json()["id"] == "report-123"
        assert response.json()["name"] == "Monthly Financial Report"
        mock_create.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.generate_report")
    def test_generate_report_success(self, mock_generate):
        """Test successful report generation."""
        mock_execution = AnalyticsReportExecution(
            id="exec-123",
            organization_id="test-org-123",
            report_id="report-123",
            execution_type="manual",
            status=ReportStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_ms=5000,
        )
        mock_generate.return_value = mock_execution

        gen_request = {
            "parameters": {"period": "monthly"},
            "output_format": "pdf",
            "priority": "high",
        }
        response = client.post(
            "/api/v1/analytics_v31/reports/report-123/generate", json=gen_request
        )

        assert response.status_code == 200
        assert response.json()["id"] == "exec-123"
        assert response.json()["status"] == "completed"
        mock_generate.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.list_report_executions")
    def test_list_report_executions_success(self, mock_list):
        """Test successful report execution listing."""
        mock_list.return_value = []

        response = client.get("/api/v1/analytics_v31/reports/report-123/executions")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        mock_list.assert_called_once()


# =============================================================================
# Alert API Tests
# =============================================================================


class TestAlertAPI:
    """Test cases for analytics alert API endpoints."""

    @patch("app.crud.analytics_v31.analytics_service.create_alert")
    def test_create_alert_success(self, mock_create, sample_alert_data):
        """Test successful alert creation."""
        mock_alert = AnalyticsAlert(**sample_alert_data)
        mock_alert.id = "alert-123"
        mock_alert.created_at = datetime.now()
        mock_create.return_value = mock_alert

        response = client.post("/api/v1/analytics_v31/alerts", json=sample_alert_data)

        assert response.status_code == 201
        assert response.json()["id"] == "alert-123"
        assert response.json()["name"] == "Revenue Alert"
        mock_create.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.evaluate_alert")
    def test_evaluate_alert_success(self, mock_evaluate):
        """Test successful alert evaluation."""
        mock_evaluate.return_value = {
            "alert_id": "alert-123",
            "evaluation_result": True,
            "current_value": 45000,
            "threshold_value": 50000,
            "triggered": True,
            "evaluated_at": datetime.now().isoformat(),
        }

        eval_request = {"force_evaluation": True, "test_mode": False}
        response = client.post(
            "/api/v1/analytics_v31/alerts/alert-123/evaluate", json=eval_request
        )

        assert response.status_code == 200
        assert response.json()["triggered"] is True
        mock_evaluate.assert_called_once()


# =============================================================================
# Prediction API Tests
# =============================================================================


class TestPredictionAPI:
    """Test cases for analytics prediction API endpoints."""

    @patch("app.crud.analytics_v31.analytics_service.create_prediction")
    def test_create_prediction_success(self, mock_create, sample_prediction_data):
        """Test successful prediction creation."""
        mock_prediction = AnalyticsPrediction(**sample_prediction_data)
        mock_prediction.id = "pred-123"
        mock_prediction.created_at = datetime.now()
        mock_create.return_value = mock_prediction

        response = client.post(
            "/api/v1/analytics_v31/predictions", json=sample_prediction_data
        )

        assert response.status_code == 201
        assert response.json()["id"] == "pred-123"
        assert response.json()["name"] == "Revenue Forecast"
        mock_create.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.train_prediction_model")
    def test_train_prediction_model_success(self, mock_train):
        """Test successful prediction model training."""
        mock_train.return_value = {
            "training_id": "train-123",
            "model_id": "pred-123",
            "status": "completed",
            "accuracy_score": 0.92,
            "mae_score": 5420.30,
            "rmse_score": 7850.45,
            "training_duration_seconds": 180,
            "data_points_used": 1000,
        }

        train_request = {
            "training_period_start": "2023-01-01",
            "training_period_end": "2024-01-31",
            "validation_split": 0.2,
            "hyperparameters": {"learning_rate": 0.01},
        }
        response = client.post(
            "/api/v1/analytics_v31/predictions/pred-123/train", json=train_request
        )

        assert response.status_code == 200
        assert response.json()["accuracy_score"] == 0.92
        mock_train.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.get_prediction_forecast")
    def test_get_prediction_forecast_success(self, mock_forecast):
        """Test successful prediction forecast retrieval."""
        mock_forecast.return_value = {
            "prediction_id": "pred-123",
            "forecast_data": [
                {
                    "date": "2024-02-01",
                    "predicted_value": 87500,
                    "confidence_interval": [82000, 93000],
                },
                {
                    "date": "2024-02-02",
                    "predicted_value": 88200,
                    "confidence_interval": [82800, 93600],
                },
            ],
            "model_accuracy": 0.92,
            "generated_at": datetime.now().isoformat(),
        }

        response = client.get(
            "/api/v1/analytics_v31/predictions/pred-123/forecast?days_ahead=30"
        )

        assert response.status_code == 200
        assert len(response.json()["forecast_data"]) == 2
        mock_forecast.assert_called_once()


# =============================================================================
# Insight API Tests
# =============================================================================


class TestInsightAPI:
    """Test cases for analytics insight API endpoints."""

    @patch("app.crud.analytics_v31.analytics_service.list_insights")
    def test_list_insights_success(self, mock_list):
        """Test successful insight listing."""
        mock_list.return_value = {
            "insights": [],
            "total_count": 0,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        response = client.get(
            "/api/v1/analytics_v31/insights?organization_id=test-org-123"
        )

        assert response.status_code == 200
        assert response.json()["total_count"] == 0
        mock_list.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.generate_insights")
    def test_generate_insights_success(self, mock_generate):
        """Test successful insight generation."""
        mock_insights = [
            AnalyticsInsight(
                id="insight-123",
                organization_id="test-org-123",
                title="Revenue Trend Analysis",
                summary="Revenue has increased by 15% this month",
                description="Detailed analysis of revenue trends",
                insight_type="trend_analysis",
                priority_score=Decimal("8.5"),
                is_actionable=True,
                created_at=datetime.now(),
            )
        ]
        mock_generate.return_value = mock_insights

        gen_request = {
            "organization_id": "test-org-123",
            "analysis_period": {"start": "2024-01-01", "end": "2024-01-31"},
            "focus_areas": ["revenue", "customers"],
            "insight_types": ["trend_analysis", "anomaly_detection"],
        }
        response = client.post(
            "/api/v1/analytics_v31/insights/generate", json=gen_request
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Revenue Trend Analysis"
        mock_generate.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.acknowledge_insight")
    def test_acknowledge_insight_success(self, mock_acknowledge):
        """Test successful insight acknowledgment."""
        mock_acknowledge.return_value = {
            "insight_id": "insight-123",
            "acknowledged_by": "user-123",
            "acknowledged_at": datetime.now().isoformat(),
            "status": "acknowledged",
        }

        response = client.put(
            "/api/v1/analytics_v31/insights/insight-123/acknowledge?user_id=user-123"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "acknowledged"
        mock_acknowledge.assert_called_once()


# =============================================================================
# Advanced Analytics Tests
# =============================================================================


class TestAdvancedAnalytics:
    """Test cases for advanced analytics features."""

    @patch("app.crud.analytics_v31.analytics_service.execute_analytics_query")
    def test_execute_analytics_query_success(self, mock_execute):
        """Test successful advanced analytics query execution."""
        mock_execute.return_value = {
            "query_id": "query-123",
            "results": [
                {"month": "2024-01", "revenue": 85000, "customers": 450},
                {"month": "2024-02", "revenue": 92000, "customers": 480},
            ],
            "execution_time_ms": 250,
            "rows_returned": 2,
            "executed_at": datetime.now().isoformat(),
        }

        query_request = {
            "organization_id": "test-org-123",
            "query_type": "aggregation",
            "data_sources": ["ds-123"],
            "metrics": ["revenue", "customer_count"],
            "dimensions": ["month"],
            "filters": {"date_range": {"start": "2024-01-01", "end": "2024-02-29"}},
            "aggregations": {"revenue": "sum", "customer_count": "distinct"},
        }
        response = client.post("/api/v1/analytics_v31/query", json=query_request)

        assert response.status_code == 200
        assert len(response.json()["results"]) == 2
        mock_execute.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.get_analytics_health")
    def test_get_analytics_health_success(self, mock_health):
        """Test successful analytics health check."""
        mock_health.return_value = {
            "status": "healthy",
            "database_status": "connected",
            "data_sources_status": {"active": 5, "inactive": 1, "error": 0},
            "metrics_status": {"total": 25, "calculating": 2, "error": 0},
            "system_load": {"cpu_percent": 45.2, "memory_percent": 62.1},
            "performance_metrics": {
                "avg_query_time_ms": 150,
                "queries_per_minute": 45,
                "data_freshness_minutes": 5,
            },
            "version": "v31.0",
            "checked_at": datetime.now().isoformat(),
        }

        response = client.get("/api/v1/analytics_v31/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["version"] == "v31.0"
        mock_health.assert_called_once()


# =============================================================================
# Data Point API Tests
# =============================================================================


class TestDataPointAPI:
    """Test cases for analytics data point API endpoints."""

    @patch("app.crud.analytics_v31.analytics_service.create_data_point")
    def test_create_data_point_success(self, mock_create):
        """Test successful data point creation."""
        sample_data = {
            "organization_id": "test-org-123",
            "metric_id": "metric-123",
            "timestamp": datetime.now().isoformat(),
            "period_type": "day",
            "value": Decimal("85000.50"),
            "raw_value": Decimal("85000.50"),
            "count": 1,
            "dimensions": {"department": "sales", "region": "north"},
        }

        mock_data_point = AnalyticsDataPoint(**sample_data)
        mock_data_point.id = "dp-123"
        mock_create.return_value = mock_data_point

        response = client.post("/api/v1/analytics_v31/data-points", json=sample_data)

        assert response.status_code == 201
        assert response.json()["id"] == "dp-123"
        mock_create.assert_called_once()

    @patch("app.crud.analytics_v31.analytics_service.query_data_points")
    def test_query_data_points_success(self, mock_query):
        """Test successful data point querying."""
        mock_query.return_value = {
            "data_points": [],
            "total_count": 0,
            "aggregations": {"sum": 0, "avg": 0, "count": 0},
            "query_time_ms": 45,
        }

        query_request = {
            "organization_id": "test-org-123",
            "metric_ids": ["metric-123"],
            "period_start": "2024-01-01T00:00:00",
            "period_end": "2024-01-31T23:59:59",
            "dimensions": {"department": "sales"},
            "aggregations": ["sum", "avg", "count"],
        }
        response = client.post(
            "/api/v1/analytics_v31/data-points/query", json=query_request
        )

        assert response.status_code == 200
        assert "aggregations" in response.json()
        mock_query.assert_called_once()


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    @patch("app.crud.analytics_v31.analytics_service.create_data_source")
    def test_internal_server_error(self, mock_create, sample_data_source_data):
        """Test handling of internal server errors."""
        mock_create.side_effect = Exception("Database connection failed")

        response = client.post(
            "/api/v1/analytics_v31/data-sources", json=sample_data_source_data
        )

        assert response.status_code == 500
        assert "Failed to create data source" in response.json()["detail"]

    def test_invalid_request_data(self):
        """Test handling of invalid request data."""
        invalid_data = {
            "organization_id": "",  # Empty organization_id
            "name": "",  # Empty name
        }

        response = client.post("/api/v1/analytics_v31/data-sources", json=invalid_data)

        assert response.status_code == 422  # Validation error

    @patch("app.crud.analytics_v31.analytics_service.delete_data_source")
    def test_delete_nonexistent_resource(self, mock_delete):
        """Test deletion of non-existent resource."""
        mock_delete.return_value = False

        response = client.delete("/api/v1/analytics_v31/data-sources/nonexistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "Data source not found"


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration test cases for analytics API workflows."""

    @patch("app.crud.analytics_v31.analytics_service")
    def test_complete_analytics_workflow(
        self, mock_service, sample_data_source_data, sample_metric_data
    ):
        """Test complete analytics workflow from data source to insights."""
        # Mock data source creation
        mock_data_source = AnalyticsDataSource(**sample_data_source_data)
        mock_data_source.id = "ds-123"
        mock_service.create_data_source.return_value = mock_data_source

        # Mock metric creation
        sample_metric_data["data_source_id"] = "ds-123"
        mock_metric = AnalyticsMetric(**sample_metric_data)
        mock_metric.id = "metric-123"
        mock_service.create_metric.return_value = mock_metric

        # Mock calculation
        mock_service.calculate_metric.return_value = {
            "metric_id": "metric-123",
            "value": 85000.50,
            "calculated_at": datetime.now().isoformat(),
        }

        # Step 1: Create data source
        ds_response = client.post(
            "/api/v1/analytics_v31/data-sources", json=sample_data_source_data
        )
        assert ds_response.status_code == 201

        # Step 2: Create metric
        metric_response = client.post(
            "/api/v1/analytics_v31/metrics", json=sample_metric_data
        )
        assert metric_response.status_code == 201

        # Step 3: Calculate metric
        calc_request = {
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "force_recalculate": True,
        }
        calc_response = client.post(
            "/api/v1/analytics_v31/metrics/metric-123/calculate", json=calc_request
        )
        assert calc_response.status_code == 200
        assert calc_response.json()["value"] == 85000.50


if __name__ == "__main__":
    pytest.main([__file__])
