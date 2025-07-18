"""
Integration tests for Sales Analytics API endpoints - Phase 5 CRM.
営業分析APIエンドポイント統合テスト（CRM機能Phase 5）
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.customer import Customer, CustomerStatus, Opportunity, OpportunityStage
from app.models.organization import Organization
from app.models.user import User
from tests.factories.organization import OrganizationFactory
from tests.factories.user import UserFactory


@pytest.fixture
async def test_organization(async_session: AsyncSession):
    """Create test organization."""
    org = OrganizationFactory()
    async_session.add(org)
    await async_session.commit()
    await async_session.refresh(org)
    return org


@pytest.fixture
async def test_user_with_org(async_session: AsyncSession, test_organization: Organization):
    """Create test user with organization."""
    user = UserFactory(organization_id=test_organization.id)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def test_customers_with_opportunities(
    async_session: AsyncSession, test_organization: Organization, test_user_with_org: User
):
    """Create test customers with opportunities."""
    customers = []
    opportunities = []
    
    # Customer 1: Active with high-value opportunity
    customer1 = Customer(
        organization_id=test_organization.id,
        customer_code="CUST001",
        company_name="Test Company 1",
        customer_type="corporate",
        status=CustomerStatus.ACTIVE,
        industry="Technology",
        scale="large",
        annual_revenue=10000000,
        created_by=test_user_with_org.id
    )
    customers.append(customer1)
    async_session.add(customer1)
    await async_session.flush()
    
    opp1 = Opportunity(
        customer_id=customer1.id,
        opportunity_code="OPP001",
        name="Major Software Deal",
        title="Enterprise Software License",
        stage=OpportunityStage.PROPOSAL,
        status="open",
        value=500000,
        probability=75,
        owner_id=test_user_with_org.id
    )
    opportunities.append(opp1)
    async_session.add(opp1)
    
    # Customer 2: Prospect with medium opportunity
    customer2 = Customer(
        organization_id=test_organization.id,
        customer_code="CUST002",
        company_name="Test Company 2",
        customer_type="corporate",
        status=CustomerStatus.PROSPECT,
        industry="Finance",
        scale="medium",
        annual_revenue=5000000,
        created_by=test_user_with_org.id
    )
    customers.append(customer2)
    async_session.add(customer2)
    await async_session.flush()
    
    opp2 = Opportunity(
        customer_id=customer2.id,
        opportunity_code="OPP002",
        name="Financial System",
        title="Banking Software Implementation",
        stage=OpportunityStage.QUALIFIED,
        status="open",
        value=250000,
        probability=50,
        owner_id=test_user_with_org.id
    )
    opportunities.append(opp2)
    async_session.add(opp2)
    
    # Customer 3: Won opportunity
    customer3 = Customer(
        organization_id=test_organization.id,
        customer_code="CUST003",
        company_name="Test Company 3",
        customer_type="corporate",
        status=CustomerStatus.ACTIVE,
        industry="Healthcare",
        scale="small",
        annual_revenue=2000000,
        created_by=test_user_with_org.id
    )
    customers.append(customer3)
    async_session.add(customer3)
    await async_session.flush()
    
    opp3 = Opportunity(
        customer_id=customer3.id,
        opportunity_code="OPP003",
        name="Medical Records System",
        title="Hospital Management Software",
        stage=OpportunityStage.CLOSED_WON,
        status="won",
        value=100000,
        probability=100,
        owner_id=test_user_with_org.id
    )
    opportunities.append(opp3)
    async_session.add(opp3)
    
    await async_session.commit()
    return customers, opportunities


@pytest.mark.asyncio
class TestSalesAnalyticsAPI:
    """Test sales analytics API endpoints."""

    async def test_sales_forecast_endpoint(
        self,
        client: TestClient,
        test_user_with_org: User,
        test_customers_with_opportunities
    ):
        """Test sales forecast generation endpoint."""
        # Mock authentication
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/sales-analytics/forecast/sales?forecast_months=6")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "forecast_type" in data
        assert data["forecast_type"] == "sales_forecast"
        assert "organization_id" in data
        assert data["organization_id"] == test_user_with_org.organization_id
        assert "monthly_forecast" in data
        assert len(data["monthly_forecast"]) == 6
        
        # Verify summary data
        assert "summary" in data
        summary = data["summary"]
        assert "total_pipeline_value" in summary
        assert "weighted_pipeline_value" in summary
        assert "open_opportunities" in summary
        assert summary["open_opportunities"] >= 2  # At least 2 open opportunities

    async def test_win_probability_analysis(
        self,
        client: TestClient,
        test_user_with_org: User,
        test_customers_with_opportunities
    ):
        """Test win probability analysis endpoint."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/sales-analytics/probability/win-analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "organization_analysis" in data
        assert "total_opportunities_analyzed" in data
        
        org_analysis = data["organization_analysis"]
        assert "overall_win_rate" in org_analysis

    async def test_customer_sales_potential(
        self,
        client: TestClient,
        test_user_with_org: User,
        test_customers_with_opportunities
    ):
        """Test customer sales potential analysis endpoint."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/sales-analytics/customers/sales-potential")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "analysis_type" in data
        assert data["analysis_type"] == "customer_sales_potential"
        assert "customer_analyses" in data
        assert "summary" in data
        
        # Verify customer analysis data
        customer_analyses = data["customer_analyses"]
        assert len(customer_analyses) >= 3  # At least 3 customers
        
        for analysis in customer_analyses:
            assert "customer_id" in analysis
            assert "potential_score" in analysis
            assert "company_name" in analysis
            assert 0 <= analysis["potential_score"] <= 100

    async def test_sales_performance_analysis(
        self,
        client: TestClient,
        test_user_with_org: User,
        test_customers_with_opportunities
    ):
        """Test sales performance analysis endpoint."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get(
            "/api/v1/sales-analytics/performance/sales-rep?period_months=3"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "analysis_type" in data
        assert data["analysis_type"] == "sales_performance"
        assert "sales_rep_performance" in data
        assert "team_summary" in data
        
        # Verify sales rep performance data
        sales_rep_perf = data["sales_rep_performance"]
        assert len(sales_rep_perf) >= 1  # At least one sales rep
        
        for perf in sales_rep_perf:
            assert "user_id" in perf
            assert "total_opportunities" in perf
            assert "won_opportunities" in perf
            assert "total_value" in perf

    async def test_sales_analytics_dashboard(
        self,
        client: TestClient,
        test_user_with_org: User,
        test_customers_with_opportunities
    ):
        """Test comprehensive sales analytics dashboard endpoint."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/sales-analytics/dashboard/sales-overview")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify dashboard structure
        assert "dashboard_type" in data
        assert data["dashboard_type"] == "sales_analytics_overview"
        assert "forecast_summary" in data
        assert "probability_insights" in data
        assert "customer_insights" in data
        assert "team_performance" in data
        
        # Verify forecast summary
        forecast_summary = data["forecast_summary"]
        assert "next_6_months" in forecast_summary
        assert "total_pipeline" in forecast_summary
        assert "weighted_pipeline" in forecast_summary

    async def test_pipeline_health_insights(
        self,
        client: TestClient,
        test_user_with_org: User,
        test_customers_with_opportunities
    ):
        """Test pipeline health insights endpoint."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/sales-analytics/insights/pipeline-health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pipeline health structure
        assert "pipeline_health" in data
        assert "pipeline_metrics" in data
        
        pipeline_health = data["pipeline_health"]
        assert "health_score" in pipeline_health
        assert "health_status" in pipeline_health
        assert "insights" in pipeline_health
        assert "recommendations" in pipeline_health
        
        # Verify health score is valid
        assert 0 <= pipeline_health["health_score"] <= 100

    async def test_sales_action_recommendations(
        self,
        client: TestClient,
        test_user_with_org: User,
        test_customers_with_opportunities
    ):
        """Test sales action recommendations endpoint."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        # Test general recommendations
        response = client.get("/api/v1/sales-analytics/recommendations/sales-actions")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify recommendations structure
        assert "recommendations" in data
        assert "total_recommendations" in data
        
        recommendations = data["recommendations"]
        assert len(recommendations) >= 1
        
        for rec in recommendations:
            assert "category" in rec
            assert "priority" in rec
            assert "action" in rec
            assert "description" in rec
            assert "expected_impact" in rec

    async def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        # Test without authentication
        response = client.get("/api/v1/sales-analytics/forecast/sales")
        assert response.status_code == 401
        
        response = client.get("/api/v1/sales-analytics/probability/win-analysis")
        assert response.status_code == 401
        
        response = client.get("/api/v1/sales-analytics/customers/sales-potential")
        assert response.status_code == 401

    async def test_user_without_organization(
        self, client: TestClient, async_session: AsyncSession
    ):
        """Test endpoints with user that has no organization."""
        # Create user without organization
        user = UserFactory(organization_id=None)
        async_session.add(user)
        await async_session.commit()
        
        client.headers = {"Authorization": f"Bearer mock_token_{user.id}"}
        
        response = client.get("/api/v1/sales-analytics/forecast/sales")
        assert response.status_code == 400
        assert "must belong to an organization" in response.json()["detail"]

    async def test_forecast_with_parameters(
        self,
        client: TestClient,
        test_user_with_org: User,
        test_customers_with_opportunities
    ):
        """Test sales forecast with different parameters."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        # Test with custom parameters
        response = client.get(
            "/api/v1/sales-analytics/forecast/sales"
            "?forecast_months=12&include_pipeline=false&include_trends=false"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify parameters were applied
        assert len(data["monthly_forecast"]) == 12
        # Pipeline analysis should be None when include_pipeline=false
        assert data["pipeline_analysis"] is None
        # Trend analysis should be None when include_trends=false
        assert data["trend_analysis"] is None

    async def test_performance_analysis_specific_user(
        self,
        client: TestClient,
        test_user_with_org: User,
        test_customers_with_opportunities
    ):
        """Test sales performance analysis for specific user."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get(
            f"/api/v1/sales-analytics/performance/sales-rep"
            f"?user_id={test_user_with_org.id}&period_months=6"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify user-specific analysis
        assert data["user_id"] == test_user_with_org.id
        assert "sales_rep_performance" in data