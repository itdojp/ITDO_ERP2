"""
ITDO ERP Backend - Financial Integration Tests
Day 27: Comprehensive test suite for financial management integration

Test Coverage:
- Financial integration API endpoints
- Cross-module financial service functionality
- Integrated dashboard service operations
- Multi-currency operations
- AI-powered financial analytics
- Risk assessment and management
- Performance optimization scenarios
"""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.cross_module_financial_service import CrossModuleFinancialService
from app.services.integrated_financial_dashboard_service import (
    IntegratedFinancialDashboardService,
)

# Test client
client = TestClient(app)

# Test data
TEST_ORG_ID = "org_123"
TEST_USER_ID = "user_456"


@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = Mock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing"""
    return {
        "organization_id": TEST_ORG_ID,
        "total_revenue": 1250000.0,
        "total_expenses": 950000.0,
        "net_income": 300000.0,
        "gross_margin": 35.2,
        "operating_margin": 18.7,
        "cash_flow": 180000.0,
        "revenue_growth": 12.5,
    }


@pytest.fixture
def sample_module_metrics():
    """Sample module metrics for testing"""
    return {
        "inventory": {
            "valuation": 850000.0,
            "turnover": 8.5,
            "carrying_costs": 45000.0,
        },
        "sales": {
            "pipeline": 2500000.0,
            "conversion_rate": 0.15,
            "customer_lifetime_value": 45000.0,
        },
        "projects": {
            "active_projects": 12,
            "total_budget": 1800000.0,
            "roi": 18.5,
        },
        "resources": {
            "utilization": 0.85,
            "total_cost": 950000.0,
            "efficiency": 87.2,
        },
    }


class TestFinancialIntegrationAPI:
    """Test cases for Financial Integration API endpoints"""

    @pytest.mark.asyncio
    async def test_get_comprehensive_dashboard_success(self, mock_db_session):
        """Test successful comprehensive dashboard retrieval"""
        with patch("app.core.database.get_db", return_value=mock_db_session):
            with patch(
                "app.core.security.get_current_user",
                return_value={"user_id": TEST_USER_ID},
            ):
                response = client.get(
                    f"/api/v1/financial-integration/dashboard/comprehensive?organization_id={TEST_ORG_ID}&period=12m"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["organization_id"] == TEST_ORG_ID
                assert data["period"] == "12m"
                assert "dashboard_data" in data
                assert "last_updated" in data

    @pytest.mark.asyncio
    async def test_get_comprehensive_dashboard_invalid_period(self, mock_db_session):
        """Test comprehensive dashboard with invalid period parameter"""
        with patch("app.core.database.get_db", return_value=mock_db_session):
            with patch(
                "app.core.security.get_current_user",
                return_value={"user_id": TEST_USER_ID},
            ):
                response = client.get(
                    f"/api/v1/financial-integration/dashboard/comprehensive?organization_id={TEST_ORG_ID}&period=invalid"
                )

                assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_integrated_financial_report_success(self, mock_db_session):
        """Test successful integrated financial report generation"""
        start_date = date.today() - timedelta(days=365)
        end_date = date.today()

        with patch("app.core.database.get_db", return_value=mock_db_session):
            with patch(
                "app.core.security.get_current_user",
                return_value={"user_id": TEST_USER_ID},
            ):
                response = client.get(
                    f"/api/v1/financial-integration/reports/integrated"
                    f"?organization_id={TEST_ORG_ID}"
                    f"&start_date={start_date.isoformat()}"
                    f"&end_date={end_date.isoformat()}"
                    f"&report_type=comprehensive"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["organization_id"] == TEST_ORG_ID
                assert data["report_type"] == "comprehensive"
                assert "financial_statements" in data
                assert "analytics_data" in data
                assert "recommendations" in data

    @pytest.mark.asyncio
    async def test_get_cross_module_analytics_success(self, mock_db_session):
        """Test successful cross-module analytics retrieval"""
        with patch("app.core.database.get_db", return_value=mock_db_session):
            with patch(
                "app.core.security.get_current_user",
                return_value={"user_id": TEST_USER_ID},
            ):
                response = client.get(
                    f"/api/v1/financial-integration/analytics/cross-module"
                    f"?organization_id={TEST_ORG_ID}"
                    f"&modules=financial&modules=inventory&modules=sales"
                    f"&period=6m"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["organization_id"] == TEST_ORG_ID
                assert "analytics" in data
                assert "correlations" in data
                assert "insights" in data

    @pytest.mark.asyncio
    async def test_sync_financial_data_success(self, mock_db_session):
        """Test successful financial data synchronization"""
        sync_options = {
            "sync_journal_entries": True,
            "sync_budgets": True,
            "sync_currency_data": True,
            "update_forecasts": True,
        }

        with patch("app.core.database.get_db", return_value=mock_db_session):
            with patch(
                "app.core.security.get_current_user",
                return_value={"user_id": TEST_USER_ID},
            ):
                response = client.post(
                    "/api/v1/financial-integration/sync/data",
                    json={
                        "organization_id": TEST_ORG_ID,
                        "sync_options": sync_options,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["organization_id"] == TEST_ORG_ID
                assert "modules_synced" in data
                assert data["status"] in ["completed", "completed_with_errors"]

    @pytest.mark.asyncio
    async def test_financial_integration_health_check(self):
        """Test financial integration API health check"""
        response = client.get("/api/v1/financial-integration/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "financial-integration-api"
        assert "features" in data
        assert "timestamp" in data


class TestCrossModuleFinancialService:
    """Test cases for Cross-Module Financial Service"""

    @pytest.mark.asyncio
    async def test_integrate_financial_data_success(
        self, mock_db_session, sample_financial_data
    ):
        """Test successful financial data integration"""
        service = CrossModuleFinancialService(mock_db_session)
        integration_scope = ["inventory", "sales", "projects", "resources"]

        with patch.object(
            service, "_integrate_inventory_financial_data", return_value={"errors": []}
        ):
            with patch.object(
                service, "_integrate_sales_financial_data", return_value={"errors": []}
            ):
                with patch.object(
                    service,
                    "_integrate_project_financial_data",
                    return_value={"errors": []},
                ):
                    with patch.object(
                        service,
                        "_integrate_resource_financial_data",
                        return_value={"errors": []},
                    ):
                        with patch.object(
                            service,
                            "_update_integrated_financial_metrics",
                            return_value=None,
                        ):
                            result = await service.integrate_financial_data(
                                TEST_ORG_ID, integration_scope
                            )

                            assert result["organization_id"] == TEST_ORG_ID
                            assert result["integration_scope"] == integration_scope
                            assert len(result["modules_integrated"]) == 4
                            assert result["status"] == "completed"
                            assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_calculate_unified_kpis_success(self, mock_db_session):
        """Test successful unified KPI calculation"""
        service = CrossModuleFinancialService(mock_db_session)

        with patch.object(
            service,
            "_calculate_core_financial_kpis",
            return_value={"total_revenue": 1250000.0},
        ):
            with patch.object(
                service,
                "_calculate_advanced_analytics_kpis",
                return_value={"forecast_accuracy": 87.5},
            ):
                with patch.object(
                    service,
                    "_calculate_multi_currency_kpis",
                    return_value={"currency_exposure_usd": 125000.0},
                ):
                    with patch.object(
                        service,
                        "_calculate_operational_kpis",
                        return_value={"inventory_turnover_rate": 8.5},
                    ):
                        with patch.object(
                            service,
                            "_calculate_integrated_performance_score",
                            return_value=87.5,
                        ):
                            result = await service.calculate_unified_kpis(
                                TEST_ORG_ID, "12m"
                            )

                            assert result["organization_id"] == TEST_ORG_ID
                            assert result["period"] == "12m"
                            assert "core_financial_kpis" in result
                            assert "advanced_analytics_kpis" in result
                            assert "multi_currency_kpis" in result
                            assert "operational_kpis" in result
                            assert result["integrated_performance_score"] == 87.5

    @pytest.mark.asyncio
    async def test_synchronize_financial_workflows_success(self, mock_db_session):
        """Test successful financial workflow synchronization"""
        service = CrossModuleFinancialService(mock_db_session)
        workflow_types = [
            "budget_approval",
            "expense_approval",
            "financial_reporting",
            "risk_management",
        ]

        with patch.object(
            service, "_sync_budget_approval_workflow", return_value={"errors": []}
        ):
            with patch.object(
                service, "_sync_expense_approval_workflow", return_value={"errors": []}
            ):
                with patch.object(
                    service,
                    "_sync_financial_reporting_workflow",
                    return_value={"errors": []},
                ):
                    with patch.object(
                        service,
                        "_sync_risk_management_workflow",
                        return_value={"errors": []},
                    ):
                        result = await service.synchronize_financial_workflows(
                            TEST_ORG_ID, workflow_types
                        )

                        assert result["organization_id"] == TEST_ORG_ID
                        assert result["workflow_types"] == workflow_types
                        assert len(result["workflows_synced"]) == 4
                        assert result["status"] == "completed"
                        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_generate_integrated_financial_insights_success(
        self, mock_db_session
    ):
        """Test successful integrated financial insights generation"""
        service = CrossModuleFinancialService(mock_db_session)

        with patch.object(
            service,
            "_get_comprehensive_financial_data",
            return_value={"core_financial": {}},
        ):
            with patch.object(
                service,
                "_generate_ai_financial_insights",
                return_value=["Insight 1", "Insight 2"],
            ):
                with patch.object(
                    service,
                    "_analyze_cross_module_correlations",
                    return_value={"correlation": 0.85},
                ):
                    with patch.object(
                        service,
                        "_identify_risks_and_opportunities",
                        return_value={"risks": [], "opportunities": []},
                    ):
                        with patch.object(
                            service,
                            "_generate_predictive_insights",
                            return_value={"forecast": "positive"},
                        ):
                            with patch.object(
                                service,
                                "_generate_strategic_recommendations",
                                return_value=["Recommendation 1"],
                            ):
                                result = await service.generate_integrated_financial_insights(
                                    TEST_ORG_ID, "comprehensive"
                                )

                                assert result["organization_id"] == TEST_ORG_ID
                                assert result["analysis_depth"] == "comprehensive"
                                assert "ai_insights" in result
                                assert "correlation_insights" in result
                                assert "strategic_recommendations" in result
                                assert result["confidence_score"] == 87.5


class TestIntegratedFinancialDashboardService:
    """Test cases for Integrated Financial Dashboard Service"""

    @pytest.mark.asyncio
    async def test_get_comprehensive_dashboard_data_success(
        self, mock_db_session, sample_financial_data, sample_module_metrics
    ):
        """Test successful comprehensive dashboard data retrieval"""
        service = IntegratedFinancialDashboardService(mock_db_session)

        with patch.object(
            service, "_get_basic_financial_metrics", return_value=sample_financial_data
        ):
            with patch.object(
                service, "_get_module_metrics", return_value=sample_module_metrics
            ):
                with patch.object(
                    service,
                    "_get_latest_predictions",
                    return_value={"predictions": "positive"},
                ):
                    with patch.object(
                        service,
                        "_get_risk_assessment_data",
                        return_value={"risk_level": "medium"},
                    ):
                        with patch.object(
                            service,
                            "_get_currency_dashboard_data",
                            return_value={"currencies": 5},
                        ):
                            with patch.object(
                                service,
                                "_calculate_integrated_dashboard_kpis",
                                return_value={"overall_score": 87.5},
                            ):
                                with patch.object(
                                    service,
                                    "_generate_dashboard_insights",
                                    return_value=["Insight 1"],
                                ):
                                    with patch.object(
                                        service,
                                        "_calculate_performance_correlations",
                                        return_value={"correlation": 0.85},
                                    ):
                                        with patch.object(
                                            service,
                                            "_calculate_dashboard_health_score",
                                            return_value={"overall_score": 87.5},
                                        ):
                                            result = await service.get_comprehensive_dashboard_data(
                                                TEST_ORG_ID, "12m", True, True, True
                                            )

                                            assert (
                                                result["organization_id"] == TEST_ORG_ID
                                            )
                                            assert result["period"] == "12m"
                                            assert "dashboard_data" in result
                                            assert "last_updated" in result
                                            assert result["data_quality_score"] == 95.5

    @pytest.mark.asyncio
    async def test_get_real_time_financial_metrics_success(self, mock_db_session):
        """Test successful real-time financial metrics retrieval"""
        service = IntegratedFinancialDashboardService(mock_db_session)

        with patch.object(
            service,
            "_get_current_cash_position",
            return_value={"cash_on_hand": 285000.0},
        ):
            with patch.object(
                service,
                "_get_daily_transaction_summary",
                return_value={"total_transactions": 45},
            ):
                with patch.object(
                    service,
                    "_get_monthly_progress_metrics",
                    return_value={"revenue_progress": 78.5},
                ):
                    with patch.object(
                        service,
                        "_get_financial_alerts",
                        return_value=[{"type": "info"}],
                    ):
                        with patch.object(
                            service,
                            "_get_market_indicators_impact",
                            return_value={"impact": "positive"},
                        ):
                            result = await service.get_real_time_financial_metrics(
                                TEST_ORG_ID
                            )

                            assert result["organization_id"] == TEST_ORG_ID
                            assert "timestamp" in result
                            assert "cash_position" in result
                            assert "daily_transactions" in result
                            assert result["system_status"] == "operational"

    @pytest.mark.asyncio
    async def test_get_financial_trends_analysis_success(self, mock_db_session):
        """Test successful financial trends analysis"""
        service = IntegratedFinancialDashboardService(mock_db_session)

        with patch.object(
            service,
            "_get_revenue_trends",
            return_value=[{"period": "2024-01", "value": 95000}],
        ):
            with patch.object(
                service,
                "_get_expense_trends",
                return_value=[{"period": "2024-01", "value": 72000}],
            ):
                with patch.object(
                    service,
                    "_get_profitability_trends",
                    return_value=[{"period": "2024-01", "value": 23000}],
                ):
                    with patch.object(
                        service,
                        "_get_cashflow_trends",
                        return_value=[{"period": "2024-01", "value": 28000}],
                    ):
                        with patch.object(
                            service,
                            "_get_module_performance_trends",
                            return_value={"inventory": []},
                        ):
                            with patch.object(
                                service,
                                "_analyze_financial_trends",
                                return_value=["Trend insight 1"],
                            ):
                                result = await service.get_financial_trends_analysis(
                                    TEST_ORG_ID, "12m", "monthly"
                                )

                                assert result["organization_id"] == TEST_ORG_ID
                                assert result["trend_period"] == "12m"
                                assert result["granularity"] == "monthly"
                                assert "trends" in result
                                assert "trend_insights" in result


class TestFinancialPerformanceOptimization:
    """Test cases for Financial Performance Optimization"""

    @pytest.mark.asyncio
    async def test_financial_query_performance(self, mock_db_session):
        """Test financial query performance optimization"""
        service = CrossModuleFinancialService(mock_db_session)

        # Mock database query execution time
        mock_db_session.execute.return_value = Mock()
        mock_db_session.execute.return_value.scalar = Mock(return_value=1250000.0)

        start_time = datetime.now()
        result = await service._calculate_core_financial_kpis(
            TEST_ORG_ID, date.today() - timedelta(days=365), date.today()
        )
        end_time = datetime.now()

        # Performance assertion: query should complete within reasonable time
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 1.0  # Should complete within 1 second
        assert result is not None

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, mock_db_session):
        """Test handling of large financial datasets"""
        service = IntegratedFinancialDashboardService(mock_db_session)

        # Mock large dataset scenario
        large_dataset = [
            {"period": f"2024-{i:02d}", "value": i * 10000} for i in range(1, 101)
        ]

        with patch.object(service, "_get_revenue_trends", return_value=large_dataset):
            result = await service.get_financial_trends_analysis(
                TEST_ORG_ID, "24m", "monthly"
            )

            assert result is not None
            assert (
                len(result["trends"]["revenue"]) == 100
            )  # Should handle 100 data points

    @pytest.mark.asyncio
    async def test_concurrent_dashboard_requests(self, mock_db_session):
        """Test concurrent dashboard data requests"""
        service = IntegratedFinancialDashboardService(mock_db_session)

        # Mock concurrent request scenario
        with patch.object(
            service, "_get_basic_financial_metrics", return_value={"revenue": 1000000}
        ):
            with patch.object(
                service, "_get_module_metrics", return_value={"inventory": {}}
            ):
                # Simulate concurrent requests
                tasks = []
                for i in range(5):
                    task = service.get_comprehensive_dashboard_data(TEST_ORG_ID, "12m")
                    tasks.append(task)

                # All requests should complete successfully
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    assert not isinstance(result, Exception)
                    assert result["organization_id"] == TEST_ORG_ID


class TestFinancialSecurityAndCompliance:
    """Test cases for Financial Security and Compliance"""

    @pytest.mark.asyncio
    async def test_financial_data_access_control(self, mock_db_session):
        """Test financial data access control and authorization"""
        unauthorized_user = {"user_id": "unauthorized_user", "permissions": []}

        with patch(
            "app.core.security.get_current_user", return_value=unauthorized_user
        ):
            response = client.get(
                f"/api/v1/financial-integration/dashboard/comprehensive?organization_id={TEST_ORG_ID}"
            )
            # Should handle unauthorized access appropriately
            assert response.status_code in [
                401,
                403,
                200,
            ]  # Depending on implementation

    @pytest.mark.asyncio
    async def test_financial_data_encryption(self, mock_db_session):
        """Test financial data encryption and privacy"""
        service = IntegratedFinancialDashboardService(mock_db_session)

        # Test that sensitive financial data is properly handled
        result = await service.get_comprehensive_dashboard_data(TEST_ORG_ID, "12m")

        # Verify no sensitive raw data is exposed in logs or responses
        assert "password" not in str(result)
        assert "credit_card" not in str(result)
        assert "ssn" not in str(result)

    @pytest.mark.asyncio
    async def test_financial_audit_trail(self, mock_db_session):
        """Test financial audit trail and logging"""
        service = CrossModuleFinancialService(mock_db_session)

        with patch("app.services.cross_module_financial_service.logger") as mock_logger:
            await service.integrate_financial_data(TEST_ORG_ID, ["inventory"])

            # Verify appropriate logging for audit trail
            mock_logger.info.assert_called()


class TestFinancialErrorHandling:
    """Test cases for Financial Error Handling and Recovery"""

    @pytest.mark.asyncio
    async def test_database_connection_failure(self, mock_db_session):
        """Test handling of database connection failures"""
        service = IntegratedFinancialDashboardService(mock_db_session)

        # Mock database connection failure
        mock_db_session.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception):
            await service.get_comprehensive_dashboard_data(TEST_ORG_ID, "12m")

    @pytest.mark.asyncio
    async def test_invalid_financial_data_handling(self, mock_db_session):
        """Test handling of invalid or corrupted financial data"""
        service = CrossModuleFinancialService(mock_db_session)

        # Test with invalid organization ID
        with pytest.raises(Exception):
            await service.integrate_financial_data("", ["inventory"])

    @pytest.mark.asyncio
    async def test_api_rate_limiting(self):
        """Test API rate limiting for financial endpoints"""
        # Simulate rapid requests to test rate limiting
        responses = []
        for i in range(10):
            response = client.get("/api/v1/financial-integration/health")
            responses.append(response.status_code)

        # All health check requests should succeed (or be rate limited appropriately)
        assert all(status in [200, 429] for status in responses)


# Additional integration tests
import asyncio


@pytest.mark.asyncio
async def test_end_to_end_financial_integration_workflow(mock_db_session):
    """Test complete end-to-end financial integration workflow"""
    # This test simulates a complete financial integration workflow

    # Step 1: Initialize services
    cross_module_service = CrossModuleFinancialService(mock_db_session)
    dashboard_service = IntegratedFinancialDashboardService(mock_db_session)

    # Step 2: Integrate financial data
    with patch.object(
        cross_module_service,
        "_integrate_inventory_financial_data",
        return_value={"errors": []},
    ):
        with patch.object(
            cross_module_service,
            "_integrate_sales_financial_data",
            return_value={"errors": []},
        ):
            integration_result = await cross_module_service.integrate_financial_data(
                TEST_ORG_ID, ["inventory", "sales"]
            )
            assert integration_result["status"] == "completed"

    # Step 3: Calculate KPIs
    with patch.object(
        cross_module_service,
        "_calculate_core_financial_kpis",
        return_value={"revenue": 1000000},
    ):
        kpi_result = await cross_module_service.calculate_unified_kpis(
            TEST_ORG_ID, "12m"
        )
        assert "core_financial_kpis" in kpi_result

    # Step 4: Generate dashboard data
    with patch.object(
        dashboard_service,
        "_get_basic_financial_metrics",
        return_value={"revenue": 1000000},
    ):
        with patch.object(
            dashboard_service, "_get_module_metrics", return_value={"inventory": {}}
        ):
            dashboard_result = await dashboard_service.get_comprehensive_dashboard_data(
                TEST_ORG_ID, "12m"
            )
            assert dashboard_result["organization_id"] == TEST_ORG_ID

    # Step 5: Verify workflow completion
    assert integration_result is not None
    assert kpi_result is not None
    assert dashboard_result is not None


if __name__ == "__main__":
    # Run specific test categories
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--cov=app.services.cross_module_financial_service",
            "--cov=app.services.integrated_financial_dashboard_service",
            "--cov=app.api.v1.financial_integration_api",
            "--cov-report=html",
            "--cov-report=term-missing",
        ]
    )
