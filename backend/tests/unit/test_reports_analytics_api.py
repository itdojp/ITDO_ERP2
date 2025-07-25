"""
CC02 v53.0 Reporting and Analytics API Tests - Issue #568
10-Day ERP Business API Implementation Sprint - Day 9-10 Phase 3
Comprehensive Test-Driven Development Test Suite
"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import date, datetime, timedelta
import uuid
from typing import List, Dict, Any

from app.main_super_minimal import app

class TestReportsAnalyticsAPIv53:
    """CC02 v53.0 Reporting and Analytics API Test Suite"""
    
    @pytest.fixture(autouse=True)
    def setup_clean_state(self):
        """Clear in-memory stores before each test"""
        from app.api.v1.endpoints.reports_analytics_v53 import (
            reports_store, dashboards_store, kpis_store, 
            executions_store, analytics_cache
        )
        reports_store.clear()
        dashboards_store.clear()
        kpis_store.clear()
        executions_store.clear()
        analytics_cache.clear()
    
    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for CC02 v53.0 Reporting and Analytics API testing."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_report_data(self) -> Dict[str, Any]:
        """Sample report data for testing."""
        return {
            "name": "Monthly Sales Report",
            "description": "Comprehensive monthly sales analysis",
            "report_type": "sales",
            "format": "json",
            "time_range": "this_month",
            "data_source": "sales",
            "filters": [
                {
                    "field": "category",
                    "operator": "eq",
                    "value": "Electronics"
                }
            ],
            "sorting": [
                {
                    "field": "date",
                    "direction": "desc"
                }
            ],
            "include_summary": True,
            "include_charts": True,
            "chart_config": {
                "chart_type": "bar",
                "title": "Sales by Category",
                "x_axis": "category",
                "y_axis": "revenue",
                "show_legend": True,
                "show_labels": True
            },
            "tags": ["sales", "monthly", "executive"],
            "category": "Sales Reports",
            "is_public": False
        }
    
    @pytest.fixture
    def sample_dashboard_data(self) -> Dict[str, Any]:
        """Sample dashboard data for testing."""
        return {
            "name": "Executive Dashboard",
            "description": "High-level business metrics dashboard",
            "category": "Executive",
            "layout_config": {
                "columns": 12,
                "rows": 8,
                "gap": 10
            },
            "theme": "dark",
            "widgets": [
                {
                    "id": "widget_001",
                    "type": "metric",
                    "title": "Total Revenue",
                    "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                    "data_source": "sales",
                    "filters": [],
                    "refresh_interval": 300,
                    "clickable": False,
                    "drill_down_enabled": False,
                    "export_enabled": True,
                    "custom_config": {}
                }
            ],
            "is_public": False,
            "shared_with": [],
            "auto_refresh": True,
            "refresh_interval": 300,
            "tags": ["executive", "overview"]
        }
    
    @pytest.fixture
    def sample_analytics_query(self) -> Dict[str, Any]:
        """Sample analytics query for testing."""
        return {
            "metric_name": "revenue",
            "aggregation": "sum",
            "time_range": "this_month",
            "group_by": "date",
            "filters": [
                {
                    "field": "status",
                    "operator": "eq",
                    "value": "completed"
                }
            ],
            "limit": 100
        }
    
    # Report Management Tests
    
    def test_create_report_basic(self, client: TestClient, sample_report_data):
        """Test basic report creation with required fields"""
        response = client.post("/api/v1/reports-v53/reports/", json=sample_report_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_report_data["name"]
        assert data["description"] == sample_report_data["description"]
        assert data["report_type"] == sample_report_data["report_type"]
        assert data["format"] == sample_report_data["format"]
        assert data["status"] == "pending"
        assert data["time_range"] == sample_report_data["time_range"]
        assert data["data_source"] == sample_report_data["data_source"]
        assert len(data["filters"]) == 1
        assert len(data["sorting"]) == 1
        assert data["include_summary"] == sample_report_data["include_summary"]
        assert data["include_charts"] == sample_report_data["include_charts"]
        assert data["chart_config"] is not None
        assert data["tags"] == sample_report_data["tags"]
        assert data["category"] == sample_report_data["category"]
        assert data["is_public"] == sample_report_data["is_public"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_report_minimal(self, client: TestClient):
        """Test minimal report creation with only required fields"""
        minimal_report = {
            "name": "Simple Report",
            "report_type": "inventory",
            "data_source": "inventory"
        }
        
        response = client.post("/api/v1/reports-v53/reports/", json=minimal_report)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Simple Report"
        assert data["report_type"] == "inventory"
        assert data["format"] == "json"  # Default value
        assert data["time_range"] == "this_month"  # Default value
        assert data["include_summary"] is True  # Default value
        assert data["include_charts"] is False  # Default value
    
    def test_create_report_invalid_data_source(self, client: TestClient):
        """Test report creation with invalid data source"""
        invalid_report = {
            "name": "Invalid Report",
            "report_type": "sales",
            "data_source": "invalid_source"
        }
        
        response = client.post("/api/v1/reports-v53/reports/", json=invalid_report)
        assert response.status_code == 400
        assert "Invalid data source" in response.json()["detail"]
    
    def test_list_reports_empty(self, client: TestClient):
        """Test listing reports when none exist"""
        response = client.get("/api/v1/reports-v53/reports/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 50
        assert data["pages"] == 0
    
    def test_list_reports_with_filtering(self, client: TestClient, sample_report_data):
        """Test listing reports with comprehensive filtering"""
        # Create test reports
        report_types = ["sales", "inventory", "crm"]
        statuses = ["pending", "completed", "failed"]
        
        created_reports = []
        for i in range(3):
            report_data = sample_report_data.copy()
            report_data["name"] = f"Report {i+1}"
            report_data["report_type"] = report_types[i]
            response = client.post("/api/v1/reports-v53/reports/", json=report_data)
            assert response.status_code == 201
            created_reports.append(response.json())
        
        # Test basic listing
        response = client.get("/api/v1/reports-v53/reports/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        
        # Test filtering by report type
        response = client.get("/api/v1/reports-v53/reports/?report_type=sales")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["report_type"] == "sales"
        
        # Test filtering by status
        response = client.get("/api/v1/reports-v53/reports/?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3  # All reports start as pending
        
        # Test search functionality
        response = client.get("/api/v1/reports-v53/reports/?search=Report 1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "Report 1" in data["items"][0]["name"]
    
    def test_get_report_not_found(self, client: TestClient):
        """Test getting non-existent report"""
        response = client.get("/api/v1/reports-v53/reports/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_report_with_view_count(self, client: TestClient, sample_report_data):
        """Test getting report increments view count"""
        # Create report
        response = client.post("/api/v1/reports-v53/reports/", json=sample_report_data)
        assert response.status_code == 201
        report = response.json()
        report_id = report["id"]
        
        # Get report multiple times
        for i in range(3):
            response = client.get(f"/api/v1/reports-v53/reports/{report_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["view_count"] == i + 1
    
    def test_update_report(self, client: TestClient, sample_report_data):
        """Test updating report configuration"""
        # Create report
        response = client.post("/api/v1/reports-v53/reports/", json=sample_report_data)
        assert response.status_code == 201
        report = response.json()
        
        # Update report
        update_data = {
            "name": "Updated Report Name",
            "description": "Updated description",
            "time_range": "last_month",
            "include_charts": False
        }
        
        response = client.put(f"/api/v1/reports-v53/reports/{report['id']}", json=update_data)
        assert response.status_code == 200
        
        updated_report = response.json()
        assert updated_report["name"] == "Updated Report Name"
        assert updated_report["description"] == "Updated description"
        assert updated_report["time_range"] == "last_month"
        assert updated_report["include_charts"] is False
        assert updated_report["updated_at"] != report["updated_at"]
    
    def test_delete_report(self, client: TestClient, sample_report_data):
        """Test deleting report"""
        # Create report
        response = client.post("/api/v1/reports-v53/reports/", json=sample_report_data)
        assert response.status_code == 201
        report = response.json()
        
        # Delete report
        response = client.delete(f"/api/v1/reports-v53/reports/{report['id']}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion
        response = client.get(f"/api/v1/reports-v53/reports/{report['id']}")
        assert response.status_code == 404
    
    def test_generate_report_manual(self, client: TestClient, sample_report_data):
        """Test manual report generation trigger"""
        # Create report
        response = client.post("/api/v1/reports-v53/reports/", json=sample_report_data)
        assert response.status_code == 201
        report = response.json()
        
        # Trigger generation
        response = client.post(f"/api/v1/reports-v53/reports/{report['id']}/generate")
        assert response.status_code == 202
        assert "generation started" in response.json()["message"]
    
    def test_download_report_not_ready(self, client: TestClient, sample_report_data):
        """Test downloading report that's not ready"""
        # Create report
        response = client.post("/api/v1/reports-v53/reports/", json=sample_report_data)
        assert response.status_code == 201
        report = response.json()
        
        # Try to download before generation
        response = client.get(f"/api/v1/reports-v53/reports/{report['id']}/download")
        assert response.status_code == 400
        assert "not ready for download" in response.json()["detail"]
    
    # Dashboard Management Tests
    
    def test_create_dashboard_basic(self, client: TestClient, sample_dashboard_data):
        """Test basic dashboard creation"""
        response = client.post("/api/v1/reports-v53/dashboards/", json=sample_dashboard_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_dashboard_data["name"]
        assert data["description"] == sample_dashboard_data["description"]
        assert data["category"] == sample_dashboard_data["category"]
        assert data["theme"] == sample_dashboard_data["theme"]
        assert len(data["widgets"]) == 1
        assert data["widget_count"] == 1
        assert data["is_public"] == sample_dashboard_data["is_public"]
        assert data["auto_refresh"] == sample_dashboard_data["auto_refresh"]
        assert data["refresh_interval"] == sample_dashboard_data["refresh_interval"]
        assert data["is_active"] is True
        assert data["health_status"] == "healthy"
        assert data["view_count"] == 0
        assert "id" in data
        assert "created_at" in data
    
    def test_create_dashboard_minimal(self, client: TestClient):
        """Test minimal dashboard creation"""
        minimal_dashboard = {
            "name": "Simple Dashboard"
        }
        
        response = client.post("/api/v1/reports-v53/dashboards/", json=minimal_dashboard)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Simple Dashboard"
        assert data["theme"] == "default"  # Default value
        assert data["widget_count"] == 0
        assert data["auto_refresh"] is True  # Default value
    
    def test_list_dashboards_with_filtering(self, client: TestClient, sample_dashboard_data):
        """Test listing dashboards with filtering"""
        # Create test dashboards
        categories = ["Executive", "Sales", "Operations"]
        
        for i in range(3):
            dashboard_data = sample_dashboard_data.copy()
            dashboard_data["name"] = f"Dashboard {i+1}"
            dashboard_data["category"] = categories[i]
            dashboard_data["is_public"] = i % 2 == 0
            response = client.post("/api/v1/reports-v53/dashboards/", json=dashboard_data)
            assert response.status_code == 201
        
        # Test basic listing
        response = client.get("/api/v1/reports-v53/dashboards/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Test filtering by category
        response = client.get("/api/v1/reports-v53/dashboards/?category=Executive")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["category"] == "Executive"
        
        # Test filtering by public status
        response = client.get("/api/v1/reports-v53/dashboards/?is_public=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # Dashboards 1 and 3
    
    def test_get_dashboard_with_view_tracking(self, client: TestClient, sample_dashboard_data):
        """Test getting dashboard tracks views"""
        # Create dashboard
        response = client.post("/api/v1/reports-v53/dashboards/", json=sample_dashboard_data)
        assert response.status_code == 201
        dashboard = response.json()
        
        # Get dashboard and check view tracking
        response = client.get(f"/api/v1/reports-v53/dashboards/{dashboard['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["view_count"] == 1
        assert data["last_viewed"] is not None
    
    # Analytics and KPI Tests
    
    def test_query_analytics_basic(self, client: TestClient, sample_analytics_query):
        """Test basic analytics query execution"""
        response = client.post("/api/v1/reports-v53/analytics/query", json=sample_analytics_query)
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "metrics" in data
        assert "data_points" in data
        assert "summary" in data
        assert data["total_records"] > 0
        assert data["query_time_ms"] > 0
        assert data["cache_hit"] is False  # First query not cached
        assert "generated_at" in data
    
    def test_query_analytics_with_custom_dates(self, client: TestClient):
        """Test analytics query with custom date range"""
        query_data = {
            "metric_name": "sales",
            "aggregation": "average",
            "time_range": "custom",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "group_by": "category"
        }
        
        response = client.post("/api/v1/reports-v53/analytics/query", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["data_points"]) > 0
        assert len(data["metrics"]) > 0
        assert data["summary"]["date_range"] == "2024-01-01 to 2024-01-31"
    
    def test_list_kpis_empty_generates_samples(self, client: TestClient):
        """Test KPI listing generates sample data when empty"""
        response = client.get("/api/v1/reports-v53/kpis/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) > 0  # Sample KPIs generated
        assert data["total"] > 0
        
        # Check sample KPI structure
        kpi = data["items"][0]
        assert "name" in kpi
        assert "category" in kpi
        assert "formula" in kpi
        assert "target_value" in kpi
        assert "is_active" in kpi
    
    def test_list_kpis_with_filtering(self, client: TestClient):
        """Test KPI listing with filtering"""
        # First call to generate samples
        response = client.get("/api/v1/reports-v53/kpis/")
        assert response.status_code == 200
        
        # Test filtering by category
        response = client.get("/api/v1/reports-v53/kpis/?category=Sales")
        assert response.status_code == 200
        data = response.json()
        for kpi in data["items"]:
            assert kpi["category"] == "Sales"
        
        # Test filtering by active status
        response = client.get("/api/v1/reports-v53/kpis/?is_active=true")
        assert response.status_code == 200
        data = response.json()
        for kpi in data["items"]:
            assert kpi["is_active"] is True
    
    def test_get_kpi_values(self, client: TestClient):
        """Test getting KPI values"""
        response = client.get("/api/v1/reports-v53/kpis/values")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check KPI value structure
        kpi_value = data[0]
        assert "kpi_id" in kpi_value
        assert "kpi_name" in kpi_value
        assert "value" in kpi_value
        assert "formatted_value" in kpi_value
        assert "status" in kpi_value
        assert "period_start" in kpi_value
        assert "period_end" in kpi_value
    
    def test_get_kpi_values_with_filtering(self, client: TestClient):
        """Test getting KPI values with filtering"""
        # Test filtering by specific KPI IDs
        response = client.get("/api/v1/reports-v53/kpis/values?kpi_ids=kpi_001&kpi_ids=kpi_002")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 2
        for kpi_value in data:
            assert kpi_value["kpi_id"] in ["kpi_001", "kpi_002"]
    
    # Business Intelligence Dashboard Tests
    
    def test_get_bi_dashboard(self, client: TestClient):
        """Test comprehensive BI dashboard retrieval"""
        response = client.get("/api/v1/reports-v53/bi-dashboard")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check main sections
        assert "overview_metrics" in data
        assert "kpi_summary" in data
        assert "sales_performance" in data
        assert "revenue_trends" in data
        assert "top_products" in data
        assert "customer_insights" in data
        assert "inventory_health" in data
        assert "lead_pipeline" in data
        assert "financial_summary" in data
        assert "operational_efficiency" in data
        assert "alerts" in data
        assert "recommendations" in data
        
        # Check metrics structure
        assert len(data["overview_metrics"]) > 0
        overview_metric = data["overview_metrics"][0]
        assert "name" in overview_metric
        assert "value" in overview_metric
        assert "format_type" in overview_metric
        
        # Check KPI summary
        assert len(data["kpi_summary"]) > 0
        kpi = data["kpi_summary"][0]
        assert "kpi_name" in kpi
        assert "value" in kpi
        assert "status" in kpi
        
        # Check revenue trends
        assert len(data["revenue_trends"]) > 0
        trend = data["revenue_trends"][0]
        assert "timestamp" in trend
        assert "value" in trend
        
        # Check metadata
        assert data["dashboard_health"] == "healthy"
        assert "last_updated" in data
        assert "generation_time_ms" in data
    
    def test_get_bi_dashboard_with_time_range(self, client: TestClient):
        """Test BI dashboard with custom time range"""
        response = client.get("/api/v1/reports-v53/bi-dashboard?time_range=last_month")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["overview_metrics"]) > 0
        assert len(data["revenue_trends"]) > 0
    
    # Bulk Operations Tests
    
    def test_bulk_report_generation(self, client: TestClient, sample_report_data):
        """Test bulk report generation operation"""
        # Create multiple reports
        report_ids = []
        for i in range(3):
            report_data = sample_report_data.copy()
            report_data["name"] = f"Bulk Report {i+1}"
            response = client.post("/api/v1/reports-v53/reports/", json=report_data)
            assert response.status_code == 201
            report_ids.append(response.json()["id"])
        
        # Execute bulk generation
        bulk_operation = {
            "operation_type": "generate",
            "report_ids": report_ids,
            "notify_on_completion": False
        }
        
        response = client.post("/api/v1/reports-v53/reports/bulk", json=bulk_operation)
        assert response.status_code == 200
        
        data = response.json()
        assert data["operation_type"] == "generate"
        assert data["total_reports"] == 3
        assert data["successful_count"] == 3
        assert data["failed_count"] == 0
        assert len(data["successful_reports"]) == 3
        assert data["status"] == "completed"
    
    def test_bulk_report_deletion(self, client: TestClient, sample_report_data):
        """Test bulk report deletion operation"""
        # Create multiple reports
        report_ids = []
        for i in range(2):
            report_data = sample_report_data.copy()
            report_data["name"] = f"Delete Report {i+1}"
            response = client.post("/api/v1/reports-v53/reports/", json=report_data)
            assert response.status_code == 201
            report_ids.append(response.json()["id"])
        
        # Add non-existent report ID
        report_ids.append("non-existent-id")
        
        # Execute bulk deletion
        bulk_operation = {
            "operation_type": "delete",
            "report_ids": report_ids
        }
        
        response = client.post("/api/v1/reports-v53/reports/bulk", json=bulk_operation)
        assert response.status_code == 200
        
        data = response.json()
        assert data["operation_type"] == "delete"
        assert data["total_reports"] == 3
        assert data["successful_count"] == 2
        assert data["failed_count"] == 1
        assert len(data["failed_reports"]) == 1
        assert "not found" in data["failed_reports"][0]["error"]
    
    # System Health and Statistics Tests
    
    def test_get_reporting_health(self, client: TestClient):
        """Test reporting system health check"""
        response = client.get("/api/v1/reports-v53/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "Reporting and Analytics API v53.0" in data["service"]
        assert data["report_engine"] == "operational"
        assert "data_sources" in data
        assert "sales" in data["data_sources"]
        assert "inventory" in data["data_sources"]
        assert "crm" in data["data_sources"]
        assert data["total_reports"] >= 0
        assert data["active_dashboards"] >= 0
        assert "average_generation_time_ms" in data
        assert "cache_hit_rate" in data
        assert "timestamp" in data
    
    def test_get_reporting_statistics(self, client: TestClient, sample_report_data, sample_dashboard_data):
        """Test comprehensive reporting statistics"""
        # Create some test data
        report_response = client.post("/api/v1/reports-v53/reports/", json=sample_report_data)
        assert report_response.status_code == 201
        
        dashboard_response = client.post("/api/v1/reports-v53/dashboards/", json=sample_dashboard_data)
        assert dashboard_response.status_code == 201
        
        # Get statistics
        response = client.get("/api/v1/reports-v53/statistics")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check report statistics
        assert "report_statistics" in data
        report_stats = data["report_statistics"]
        assert report_stats["total_reports"] >= 1
        assert "completion_rate" in report_stats
        assert "report_types" in report_stats
        assert "format_breakdown" in report_stats
        
        # Check dashboard statistics
        assert "dashboard_statistics" in data
        dashboard_stats = data["dashboard_statistics"]
        assert dashboard_stats["total_dashboards"] >= 1
        assert dashboard_stats["active_dashboards"] >= 1
        
        # Check KPI statistics
        assert "kpi_statistics" in data
        kpi_stats = data["kpi_statistics"]
        assert "total_kpis" in kpi_stats
        
        # Check system performance
        assert "system_performance" in data
        perf_stats = data["system_performance"]
        assert "calculation_time_ms" in perf_stats
        assert perf_stats["calculation_time_ms"] < 200  # Performance requirement
    
    # Performance Tests
    
    def test_create_report_performance(self, client: TestClient, sample_report_data):
        """Test report creation performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.post("/api/v1/reports-v53/reports/", json=sample_report_data)
        end_time = time.time()
        
        assert response.status_code == 201
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Report creation took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    def test_create_dashboard_performance(self, client: TestClient, sample_dashboard_data):
        """Test dashboard creation performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.post("/api/v1/reports-v53/dashboards/", json=sample_dashboard_data)
        end_time = time.time()
        
        assert response.status_code == 201
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Dashboard creation took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    def test_analytics_query_performance(self, client: TestClient, sample_analytics_query):
        """Test analytics query performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.post("/api/v1/reports-v53/analytics/query", json=sample_analytics_query)
        end_time = time.time()
        
        assert response.status_code == 200
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Analytics query took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    def test_bi_dashboard_performance(self, client: TestClient):
        """Test BI dashboard generation performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/reports-v53/bi-dashboard")
        end_time = time.time()
        
        assert response.status_code == 200
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"BI dashboard took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    def test_statistics_performance(self, client: TestClient):
        """Test statistics calculation performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/reports-v53/statistics")
        end_time = time.time()
        
        assert response.status_code == 200
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Statistics calculation took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    # Data Validation and Error Handling Tests
    
    def test_report_with_invalid_time_range(self, client: TestClient):
        """Test report creation with invalid time range"""
        invalid_report = {
            "name": "Invalid Time Range Report",
            "report_type": "sales",
            "data_source": "sales",
            "time_range": "invalid_range"
        }
        
        response = client.post("/api/v1/reports-v53/reports/", json=invalid_report)
        assert response.status_code == 422  # Validation error
    
    def test_dashboard_with_invalid_widget_type(self, client: TestClient):
        """Test dashboard creation with invalid widget type"""
        invalid_dashboard = {
            "name": "Invalid Widget Dashboard",
            "widgets": [
                {
                    "id": "invalid_widget",
                    "type": "invalid_type",  # Invalid widget type
                    "title": "Invalid Widget",
                    "position": {"x": 0, "y": 0, "width": 2, "height": 2},
                    "data_source": "sales"
                }
            ]
        }
        
        response = client.post("/api/v1/reports-v53/dashboards/", json=invalid_dashboard)
        assert response.status_code == 422  # Validation error
    
    def test_analytics_query_validation(self, client: TestClient):
        """Test analytics query with missing required fields"""
        invalid_query = {
            "aggregation": "sum",
            "time_range": "this_month"
            # Missing metric_name
        }
        
        response = client.post("/api/v1/reports-v53/analytics/query", json=invalid_query)
        assert response.status_code == 422  # Validation error
    
    # Integration Tests
    
    def test_end_to_end_report_workflow(self, client: TestClient, sample_report_data):
        """Test complete report workflow from creation to download"""
        # 1. Create report
        response = client.post("/api/v1/reports-v53/reports/", json=sample_report_data)
        assert response.status_code == 201
        report = response.json()
        report_id = report["id"]
        
        # 2. List reports (should include our report)
        response = client.get("/api/v1/reports-v53/reports/")
        assert response.status_code == 200
        assert any(r["id"] == report_id for r in response.json()["items"])
        
        # 3. Get specific report
        response = client.get(f"/api/v1/reports-v53/reports/{report_id}")
        assert response.status_code == 200
        assert response.json()["id"] == report_id
        
        # 4. Update report
        update_data = {"name": "Updated Report Name"}
        response = client.put(f"/api/v1/reports-v53/reports/{report_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Report Name"
        
        # 5. Trigger generation
        response = client.post(f"/api/v1/reports-v53/reports/{report_id}/generate")
        assert response.status_code == 202
    
    def test_dashboard_with_analytics_integration(self, client: TestClient, sample_dashboard_data, sample_analytics_query):
        """Test dashboard creation with analytics query integration"""
        # Create dashboard
        response = client.post("/api/v1/reports-v53/dashboards/", json=sample_dashboard_data)
        assert response.status_code == 201
        dashboard = response.json()
        
        # Execute analytics query
        response = client.post("/api/v1/reports-v53/analytics/query", json=sample_analytics_query)
        assert response.status_code == 200
        analytics_result = response.json()
        
        # Verify both work together
        assert dashboard["id"] is not None
        assert len(analytics_result["data_points"]) > 0
        assert dashboard["widget_count"] == 1
        assert analytics_result["total_records"] > 0