"""
Test Suite for CRM API v31.0 - Customer Relationship Management API

Comprehensive test coverage for all 10 CRM endpoints:
1. Customer Management
2. Contact Management
3. Lead Management
4. Opportunity Management
5. Activity Tracking
6. Campaign Management
7. Support Tickets
8. CRM Analytics
9. Lead Conversion
10. Sales Pipeline Management
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.crm_extended import (
    ActivityType,
    CampaignExtended,
    CampaignStatus,
    ContactExtended,
    CRMActivity,
    CustomerExtended,
    LeadExtended,
    LeadStatus,
    OpportunityExtended,
    OpportunityStage,
    SupportTicket,
    SupportTicketPriority,
    SupportTicketStatus,
)

client = TestClient(app)

# Test data setup
@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing."""
    return {
        "organization_id": "org-123",
        "company_name": "Test Company Ltd",
        "legal_name": "Test Company Limited",
        "industry": "Technology",
        "company_size": "medium",
        "annual_revenue": "5000000.00",
        "employee_count": 150,
        "website": "https://testcompany.com",
        "main_phone": "+81-3-1234-5678",
        "main_email": "info@testcompany.com",
        "main_address_line1": "1-1-1 Shibuya",
        "main_city": "Tokyo",
        "main_country": "JP",
        "account_manager_id": "user-123",
        "customer_tier": "gold",
        "tags": ["enterprise", "priority"]
    }


@pytest.fixture
def sample_contact_data():
    """Sample contact data for testing."""
    return {
        "customer_id": "customer-123",
        "organization_id": "org-123",
        "first_name": "Taro",
        "last_name": "Yamada",
        "job_title": "IT Manager",
        "department": "Information Technology",
        "work_email": "taro.yamada@testcompany.com",
        "work_phone": "+81-3-1234-5679",
        "contact_type": "primary",
        "is_decision_maker": True,
        "influence_level": 8
    }


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "organization_id": "org-123",
        "first_name": "Hanako",
        "last_name": "Sato",
        "company_name": "Prospect Corp",
        "job_title": "CTO",
        "email": "hanako.sato@prospect.com",
        "phone": "+81-3-9876-5432",
        "lead_source": "website",
        "industry": "Financial Services",
        "budget_range": "1000000-5000000",
        "products_interested": ["ERP System", "Analytics"],
        "assigned_to_id": "user-456"
    }


@pytest.fixture
def sample_opportunity_data():
    """Sample opportunity data for testing."""
    return {
        "customer_id": "customer-123",
        "organization_id": "org-123",
        "name": "ERP Implementation Project",
        "description": "Full ERP system implementation with training",
        "amount": "2500000.00",
        "expected_close_date": (date.today() + timedelta(days=90)).isoformat(),
        "sales_rep_id": "user-456",
        "stage": "qualification",
        "probability": "25.00",
        "products": ["ERP Core", "Analytics Module"],
        "customer_needs": ["Process automation", "Real-time reporting"]
    }


@pytest.fixture
def sample_activity_data():
    """Sample activity data for testing."""
    return {
        "organization_id": "org-123",
        "customer_id": "customer-123",
        "contact_id": "contact-123",
        "activity_type": "call",
        "subject": "Discovery Call",
        "description": "Initial discovery call to understand requirements",
        "activity_date": datetime.now().isoformat(),
        "duration_minutes": 45,
        "owner_id": "user-456",
        "outcome": "Positive response, needs assessment scheduled"
    }


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing."""
    return {
        "organization_id": "org-123",
        "name": "Q4 ERP Campaign",
        "description": "End-of-year ERP promotion campaign",
        "campaign_type": "email",
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=60)).isoformat(),
        "budget": "100000.00",
        "target_leads": 500,
        "target_revenue": "5000000.00",
        "key_message": "Modernize your business with our ERP solution"
    }


@pytest.fixture
def sample_support_ticket_data():
    """Sample support ticket data for testing."""
    return {
        "customer_id": "customer-123",
        "organization_id": "org-123",
        "subject": "Login Issues",
        "description": "User cannot access the system after password reset",
        "category": "technical",
        "priority": "high",
        "reporter_name": "Taro Yamada",
        "reporter_email": "taro.yamada@testcompany.com",
        "source": "email"
    }


class TestCustomerManagement:
    """Test suite for Customer Management endpoints."""

    @patch('app.crud.crm_v31.CRMService.create_customer')
    def test_create_customer_success(self, mock_create, sample_customer_data):
        """Test successful customer creation."""
        # Mock response
        mock_customer = CustomerExtended()
        mock_customer.id = "customer-123"
        mock_customer.customer_code = "CUST-12345678"
        mock_customer.company_name = sample_customer_data["company_name"]
        mock_customer.is_active = True
        mock_customer.created_at = datetime.now()

        mock_create.return_value = mock_customer

        response = client.post("/api/v1/customers", json=sample_customer_data)

        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == sample_customer_data["company_name"]
        assert "customer_code" in data
        mock_create.assert_called_once()

    def test_create_customer_validation_error(self):
        """Test customer creation with validation errors."""
        invalid_data = {
            "organization_id": "org-123",
            # Missing required company_name
            "main_email": "invalid-email"  # Invalid email format
        }

        response = client.post("/api/v1/customers", json=invalid_data)
        assert response.status_code == 422

    @patch('app.crud.crm_v31.CRMService.get_customers')
    def test_list_customers_with_filters(self, mock_get_customers):
        """Test customer listing with various filters."""
        mock_customers = [
            CustomerExtended(id="customer-1", company_name="Company 1"),
            CustomerExtended(id="customer-2", company_name="Company 2")
        ]
        mock_get_customers.return_value = mock_customers

        response = client.get(
            "/api/v1/customers",
            params={
                "organization_id": "org-123",
                "customer_tier": "gold",
                "industry": "Technology",
                "is_active": True,
                "limit": 50
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        mock_get_customers.assert_called_once()

    @patch('app.crud.crm_v31.CRMService.get_customer_by_id')
    def test_get_customer_by_id_success(self, mock_get_customer):
        """Test successful customer retrieval by ID."""
        mock_customer = CustomerExtended()
        mock_customer.id = "customer-123"
        mock_customer.company_name = "Test Company"
        mock_get_customer.return_value = mock_customer

        response = client.get("/api/v1/customers/customer-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "customer-123"
        mock_get_customer.assert_called_once_with(unittest.mock.ANY, "customer-123")

    @patch('app.crud.crm_v31.CRMService.get_customer_by_id')
    def test_get_customer_not_found(self, mock_get_customer):
        """Test customer retrieval when customer doesn't exist."""
        mock_get_customer.return_value = None

        response = client.get("/api/v1/customers/nonexistent")

        assert response.status_code == 404
        assert "Customer not found" in response.json()["detail"]

    @patch('app.crud.crm_v31.CRMService.update_customer')
    def test_update_customer_success(self, mock_update):
        """Test successful customer update."""
        mock_customer = CustomerExtended()
        mock_customer.id = "customer-123"
        mock_customer.company_name = "Updated Company"
        mock_update.return_value = mock_customer

        update_data = {
            "company_name": "Updated Company",
            "customer_tier": "platinum"
        }

        response = client.put("/api/v1/customers/customer-123", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "Updated Company"
        mock_update.assert_called_once()

    @patch('app.crud.crm_v31.CRMService.calculate_customer_health_score')
    def test_get_customer_health_score(self, mock_calculate_health):
        """Test customer health score calculation."""
        mock_health = {
            "customer_id": "customer-123",
            "overall_health_score": 85.5,
            "health_status": "healthy",
            "health_factors": {
                "engagement": {"score": 90.0, "weight": 0.3},
                "revenue": {"score": 80.0, "weight": 0.4},
                "support": {"score": 88.0, "weight": 0.3}
            },
            "recommendations": ["Increase engagement frequency", "Monitor revenue trends"]
        }
        mock_calculate_health.return_value = mock_health

        response = client.get("/api/v1/customers/customer-123/health-score")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_health_score"] == 85.5
        assert data["health_status"] == "healthy"
        assert len(data["recommendations"]) == 2


class TestContactManagement:
    """Test suite for Contact Management endpoints."""

    @patch('app.crud.crm_v31.CRMService.create_contact')
    def test_create_contact_success(self, mock_create, sample_contact_data):
        """Test successful contact creation."""
        mock_contact = ContactExtended()
        mock_contact.id = "contact-123"
        mock_contact.first_name = sample_contact_data["first_name"]
        mock_contact.last_name = sample_contact_data["last_name"]
        mock_contact.is_active = True

        mock_create.return_value = mock_contact

        response = client.post("/api/v1/contacts", json=sample_contact_data)

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == sample_contact_data["first_name"]
        assert data["last_name"] == sample_contact_data["last_name"]

    @patch('app.crud.crm_v31.CRMService.get_contacts')
    def test_list_contacts_filtered(self, mock_get_contacts):
        """Test contact listing with filters."""
        mock_contacts = [
            ContactExtended(id="contact-1", first_name="Taro"),
            ContactExtended(id="contact-2", first_name="Hanako")
        ]
        mock_get_contacts.return_value = mock_contacts

        response = client.get(
            "/api/v1/contacts",
            params={
                "customer_id": "customer-123",
                "is_decision_maker": True,
                "contact_type": "primary"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestLeadManagement:
    """Test suite for Lead Management endpoints."""

    @patch('app.crud.crm_v31.CRMService.create_lead')
    def test_create_lead_success(self, mock_create, sample_lead_data):
        """Test successful lead creation."""
        mock_lead = LeadExtended()
        mock_lead.id = "lead-123"
        mock_lead.lead_number = "LEAD-12345678"
        mock_lead.email = sample_lead_data["email"]
        mock_lead.lead_score = 45
        mock_lead.status = LeadStatus.NEW

        mock_create.return_value = mock_lead

        response = client.post("/api/v1/leads", json=sample_lead_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_lead_data["email"]
        assert "lead_number" in data

    @patch('app.crud.crm_v31.CRMService.get_leads')
    def test_list_leads_with_filters(self, mock_get_leads):
        """Test lead listing with comprehensive filters."""
        mock_leads = [
            LeadExtended(id="lead-1", email="lead1@test.com"),
            LeadExtended(id="lead-2", email="lead2@test.com")
        ]
        mock_get_leads.return_value = mock_leads

        response = client.get(
            "/api/v1/leads",
            params={
                "organization_id": "org-123",
                "status": "new",
                "lead_source": "website",
                "min_lead_score": 40,
                "is_qualified": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch('app.crud.crm_v31.CRMService.convert_lead_to_customer')
    def test_convert_lead_success(self, mock_convert):
        """Test successful lead conversion."""
        mock_conversion = {
            "lead_id": "lead-123",
            "customer_id": "customer-456",
            "contact_id": "contact-789",
            "conversion_date": datetime.now().isoformat()
        }
        mock_convert.return_value = mock_conversion

        conversion_data = {
            "lead_id": "lead-123",
            "customer_data": {"company_tier": "gold"}
        }

        response = client.post("/api/v1/leads/lead-123/convert", json=conversion_data)

        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == "customer-456"

    @patch('app.crud.crm_v31.CRMService.assign_lead')
    def test_assign_lead_success(self, mock_assign):
        """Test successful lead assignment."""
        mock_lead = LeadExtended()
        mock_lead.id = "lead-123"
        mock_lead.assigned_to_id = "user-456"
        mock_assign.return_value = mock_lead

        assignment_data = {
            "lead_id": "lead-123",
            "assigned_to_id": "user-456",
            "notes": "High priority prospect"
        }

        response = client.post("/api/v1/leads/lead-123/assign", json=assignment_data)

        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to_id"] == "user-456"


class TestOpportunityManagement:
    """Test suite for Opportunity Management endpoints."""

    @patch('app.crud.crm_v31.CRMService.create_opportunity')
    def test_create_opportunity_success(self, mock_create, sample_opportunity_data):
        """Test successful opportunity creation."""
        mock_opportunity = OpportunityExtended()
        mock_opportunity.id = "opportunity-123"
        mock_opportunity.opportunity_number = "OPP-12345678"
        mock_opportunity.name = sample_opportunity_data["name"]
        mock_opportunity.amount = Decimal(sample_opportunity_data["amount"])
        mock_opportunity.stage = OpportunityStage.QUALIFICATION

        mock_create.return_value = mock_opportunity

        response = client.post("/api/v1/opportunities", json=sample_opportunity_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_opportunity_data["name"]
        assert "opportunity_number" in data

    @patch('app.crud.crm_v31.CRMService.get_opportunities')
    def test_list_opportunities_filtered(self, mock_get_opportunities):
        """Test opportunity listing with filters."""
        mock_opportunities = [
            OpportunityExtended(id="opp-1", name="Opportunity 1"),
            OpportunityExtended(id="opp-2", name="Opportunity 2")
        ]
        mock_get_opportunities.return_value = mock_opportunities

        response = client.get(
            "/api/v1/opportunities",
            params={
                "customer_id": "customer-123",
                "stage": "qualification",
                "sales_rep_id": "user-456",
                "min_amount": "100000"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch('app.crud.crm_v31.CRMService.update_opportunity_stage')
    def test_update_opportunity_stage(self, mock_update_stage):
        """Test opportunity stage update."""
        mock_opportunity = OpportunityExtended()
        mock_opportunity.id = "opportunity-123"
        mock_opportunity.stage = OpportunityStage.PROPOSAL
        mock_opportunity.probability = Decimal("60.00")
        mock_update_stage.return_value = mock_opportunity

        stage_update = {
            "opportunity_id": "opportunity-123",
            "stage": "proposal",
            "probability": "60.00",
            "notes": "Proposal submitted to customer"
        }

        response = client.post("/api/v1/opportunities/opportunity-123/update-stage", json=stage_update)

        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "proposal"

    @patch('app.crud.crm_v31.CRMService.generate_sales_forecast')
    def test_generate_sales_forecast(self, mock_generate_forecast):
        """Test sales forecast generation."""
        mock_forecast = {
            "organization_id": "org-123",
            "forecast_period": "monthly",
            "total_pipeline_value": 10000000.0,
            "weighted_pipeline_value": 3500000.0,
            "committed_forecast": 2000000.0,
            "best_case_forecast": 5000000.0,
            "opportunities_by_stage": {
                "qualification": 5,
                "proposal": 3,
                "negotiation": 2
            }
        }
        mock_generate_forecast.return_value = mock_forecast

        response = client.get(
            "/api/v1/sales-forecast",
            params={
                "organization_id": "org-123",
                "forecast_period": "monthly"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_pipeline_value"] == 10000000.0
        assert data["committed_forecast"] == 2000000.0


class TestActivityTracking:
    """Test suite for Activity Tracking endpoints."""

    @patch('app.crud.crm_v31.CRMService.create_activity')
    def test_create_activity_success(self, mock_create, sample_activity_data):
        """Test successful activity creation."""
        mock_activity = CRMActivity()
        mock_activity.id = "activity-123"
        mock_activity.subject = sample_activity_data["subject"]
        mock_activity.activity_type = ActivityType.CALL
        mock_activity.is_completed = False

        mock_create.return_value = mock_activity

        response = client.post("/api/v1/activities", json=sample_activity_data)

        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == sample_activity_data["subject"]

    @patch('app.crud.crm_v31.CRMService.get_activities')
    def test_list_activities_filtered(self, mock_get_activities):
        """Test activity listing with filters."""
        mock_activities = [
            CRMActivity(id="activity-1", subject="Call 1"),
            CRMActivity(id="activity-2", subject="Email 1")
        ]
        mock_get_activities.return_value = mock_activities

        response = client.get(
            "/api/v1/activities",
            params={
                "customer_id": "customer-123",
                "activity_type": "call",
                "is_completed": False,
                "date_from": "2024-01-01",
                "date_to": "2024-12-31"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestCampaignManagement:
    """Test suite for Campaign Management endpoints."""

    @patch('app.crud.crm_v31.CRMService.create_campaign')
    def test_create_campaign_success(self, mock_create, sample_campaign_data):
        """Test successful campaign creation."""
        mock_campaign = CampaignExtended()
        mock_campaign.id = "campaign-123"
        mock_campaign.campaign_code = "CAMP-12345678"
        mock_campaign.name = sample_campaign_data["name"]
        mock_campaign.status = CampaignStatus.PLANNING

        mock_create.return_value = mock_campaign

        response = client.post("/api/v1/campaigns", json=sample_campaign_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_campaign_data["name"]
        assert "campaign_code" in data

    @patch('app.crud.crm_v31.CRMService.send_bulk_email_campaign')
    def test_send_bulk_email_campaign(self, mock_send_campaign):
        """Test bulk email campaign execution."""
        mock_result = {
            "campaign_id": "campaign-123",
            "emails_sent": 250,
            "emails_failed": 5,
            "success_rate": 98.0,
            "status": "completed"
        }
        mock_send_campaign.return_value = mock_result

        email_request = {
            "campaign_id": "campaign-123",
            "recipient_list": ["contact-1", "contact-2", "contact-3"],
            "email_template_id": "template-456"
        }

        response = client.post("/api/v1/campaigns/campaign-123/send-email", json=email_request)

        assert response.status_code == 200
        data = response.json()
        assert data["emails_sent"] == 250
        assert data["success_rate"] == 98.0


class TestSupportTicketManagement:
    """Test suite for Support Ticket Management endpoints."""

    @patch('app.crud.crm_v31.CRMService.create_support_ticket')
    def test_create_support_ticket_success(self, mock_create, sample_support_ticket_data):
        """Test successful support ticket creation."""
        mock_ticket = SupportTicket()
        mock_ticket.id = "ticket-123"
        mock_ticket.ticket_number = "TICK-12345678"
        mock_ticket.subject = sample_support_ticket_data["subject"]
        mock_ticket.status = SupportTicketStatus.OPEN
        mock_ticket.priority = SupportTicketPriority.HIGH

        mock_create.return_value = mock_ticket

        response = client.post("/api/v1/support-tickets", json=sample_support_ticket_data)

        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == sample_support_ticket_data["subject"]
        assert "ticket_number" in data

    @patch('app.crud.crm_v31.CRMService.escalate_support_ticket')
    def test_escalate_support_ticket(self, mock_escalate):
        """Test support ticket escalation."""
        mock_ticket = SupportTicket()
        mock_ticket.id = "ticket-123"
        mock_ticket.is_escalated = True
        mock_ticket.escalated_to_id = "manager-456"
        mock_escalate.return_value = mock_ticket

        escalation_request = {
            "ticket_id": "ticket-123",
            "escalated_to_id": "manager-456",
            "escalation_reason": "Customer escalation requested"
        }

        response = client.post("/api/v1/support-tickets/ticket-123/escalate", json=escalation_request)

        assert response.status_code == 200
        data = response.json()
        assert data["is_escalated"] is True
        assert data["escalated_to_id"] == "manager-456"


class TestCRMAnalytics:
    """Test suite for CRM Analytics endpoints."""

    @patch('app.crud.crm_v31.CRMService.get_crm_dashboard_metrics')
    def test_get_dashboard_metrics(self, mock_get_metrics):
        """Test CRM dashboard metrics retrieval."""
        mock_metrics = {
            "organization_id": "org-123",
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "leads_created": 125,
            "leads_converted": 25,
            "lead_conversion_rate": 20.0,
            "opportunities_created": 30,
            "opportunities_won": 8,
            "win_rate": 26.7,
            "total_revenue": 2500000.0,
            "pipeline_value": 8750000.0,
            "new_customers": 8,
            "total_activities": 450,
            "metrics_date": datetime.now().isoformat()
        }
        mock_get_metrics.return_value = mock_metrics

        response = client.get(
            "/api/v1/analytics/dashboard",
            params={
                "organization_id": "org-123",
                "period_start": "2024-01-01",
                "period_end": "2024-01-31"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["leads_created"] == 125
        assert data["win_rate"] == 26.7

    @patch('app.crud.crm_v31.CRMService.get_pipeline_analytics')
    def test_get_pipeline_analytics(self, mock_get_analytics):
        """Test pipeline analytics retrieval."""
        mock_analytics = {
            "pipeline_value_by_stage": {
                "qualification": 2000000.0,
                "proposal": 3500000.0,
                "negotiation": 1500000.0
            },
            "average_deal_size": 350000.0,
            "average_sales_cycle_days": 75.5,
            "velocity_metrics": {
                "deals_moved": 15,
                "stage_progression_rate": 85.7
            }
        }
        mock_get_analytics.return_value = mock_analytics

        response = client.get(
            "/api/v1/analytics/pipeline",
            params={
                "organization_id": "org-123",
                "sales_rep_id": "user-456"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["average_deal_size"] == 350000.0


class TestPipelineManagement:
    """Test suite for Sales Pipeline Management endpoints."""

    @patch('app.crud.crm_v31.CRMService.get_pipeline_overview')
    def test_get_pipeline_overview(self, mock_get_overview):
        """Test pipeline overview retrieval."""
        mock_overview = {
            "total_pipeline_value": 10000000.0,
            "weighted_pipeline_value": 3500000.0,
            "opportunities_count": 25,
            "stage_distribution": {
                "prospecting": 8,
                "qualification": 7,
                "proposal": 5,
                "negotiation": 3,
                "closed_won": 2
            },
            "key_metrics": {
                "conversion_rate": 28.5,
                "average_deal_size": 400000.0,
                "pipeline_velocity": 82.3
            }
        }
        mock_get_overview.return_value = mock_overview

        response = client.get(
            "/api/v1/pipeline/overview",
            params={
                "organization_id": "org-123",
                "time_period": "current_quarter"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_pipeline_value"] == 10000000.0
        assert data["opportunities_count"] == 25

    @patch('app.crud.crm_v31.CRMService.bulk_update_opportunities')
    def test_bulk_update_pipeline(self, mock_bulk_update):
        """Test bulk pipeline updates."""
        mock_result = {
            "updated_count": 5,
            "failed_count": 0,
            "total_requested": 5,
            "success_rate": 100.0,
            "updated_opportunities": ["opp-1", "opp-2", "opp-3", "opp-4", "opp-5"]
        }
        mock_bulk_update.return_value = mock_result

        updates = [
            {"opportunity_id": "opp-1", "stage": "proposal", "probability": 60.0},
            {"opportunity_id": "opp-2", "stage": "negotiation", "probability": 75.0},
            {"opportunity_id": "opp-3", "probability": 85.0}
        ]

        response = client.post("/api/v1/pipeline/bulk-update", json=updates)

        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 5
        assert data["success_rate"] == 100.0


class TestLeadConversion:
    """Test suite for Lead Conversion Analysis endpoints."""

    @patch('app.crud.crm_v31.CRMService.get_lead_conversion_analytics')
    def test_get_lead_conversion_analytics(self, mock_get_analytics):
        """Test lead conversion analytics retrieval."""
        mock_analytics = {
            "conversion_funnel": {
                "leads_generated": 500,
                "marketing_qualified": 200,
                "sales_qualified": 100,
                "opportunities_created": 50,
                "deals_won": 12
            },
            "conversion_rates": {
                "lead_to_mql": 40.0,
                "mql_to_sql": 50.0,
                "sql_to_opportunity": 50.0,
                "opportunity_to_deal": 24.0
            },
            "source_performance": {
                "website": {"leads": 200, "conversions": 8, "rate": 4.0},
                "referral": {"leads": 150, "conversions": 6, "rate": 4.0},
                "social_media": {"leads": 100, "conversions": 2, "rate": 2.0}
            }
        }
        mock_get_analytics.return_value = mock_analytics

        response = client.get(
            "/api/v1/analytics/lead-conversion",
            params={
                "organization_id": "org-123",
                "period_start": "2024-01-01",
                "period_end": "2024-03-31"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversion_funnel"]["leads_generated"] == 500
        assert data["conversion_rates"]["lead_to_mql"] == 40.0

    @patch('app.crud.crm_v31.CRMService.calculate_lead_conversion_probability')
    def test_get_lead_conversion_probability(self, mock_calculate_probability):
        """Test lead conversion probability calculation."""
        mock_probability = {
            "lead_id": "lead-123",
            "conversion_probability": 73.5,
            "confidence_interval": [65.2, 81.8],
            "key_factors": {
                "demographic_score": 85,
                "behavioral_score": 70,
                "engagement_level": 68,
                "source_quality": 80
            },
            "recommended_actions": [
                "Schedule demo call",
                "Send case study materials",
                "Connect with decision maker"
            ]
        }
        mock_calculate_probability.return_value = mock_probability

        response = client.get("/api/v1/leads/lead-123/conversion-probability")

        assert response.status_code == 200
        data = response.json()
        assert data["conversion_probability"] == 73.5
        assert len(data["recommended_actions"]) == 3


class TestSystemHealth:
    """Test suite for CRM system health and status endpoints."""

    @patch('app.crud.crm_v31.CRMService.get_system_health')
    def test_crm_health_check_success(self, mock_get_health):
        """Test successful CRM health check."""
        mock_health = {
            "status": "healthy",
            "database_connection": "OK",
            "services_available": True,
            "performance_metrics": {
                "avg_response_time_ms": 125,
                "active_connections": 15,
                "cache_hit_rate": 94.5
            },
            "version": "31.0",
            "timestamp": datetime.now().isoformat()
        }
        mock_get_health.return_value = mock_health

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services_available"] is True

    @patch('app.crud.crm_v31.CRMService.get_system_health')
    def test_crm_health_check_failure(self, mock_get_health):
        """Test CRM health check failure handling."""
        mock_get_health.side_effect = Exception("Database connection failed")

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "Database connection failed" in data["error"]


# Integration test scenarios
class TestCRMIntegrationScenarios:
    """Integration test scenarios for complete CRM workflows."""

    @patch('app.crud.crm_v31.CRMService')
    def test_complete_lead_to_customer_journey(self, mock_service):
        """Test complete journey from lead creation to customer conversion."""
        # Setup mocks for the entire journey
        mock_service_instance = mock_service.return_value

        # 1. Create lead
        mock_lead = LeadExtended(id="lead-123", email="prospect@test.com")
        mock_service_instance.create_lead.return_value = mock_lead

        # 2. Assign lead
        mock_lead.assigned_to_id = "sales-rep-456"
        mock_service_instance.assign_lead.return_value = mock_lead

        # 3. Convert lead
        mock_conversion = {
            "lead_id": "lead-123",
            "customer_id": "customer-789",
            "contact_id": "contact-012"
        }
        mock_service_instance.convert_lead_to_customer.return_value = mock_conversion

        # 4. Create opportunity
        mock_opportunity = OpportunityExtended(id="opp-345", customer_id="customer-789")
        mock_service_instance.create_opportunity.return_value = mock_opportunity

        # Execute the journey
        # Step 1: Create lead
        lead_data = {
            "organization_id": "org-123",
            "email": "prospect@test.com",
            "first_name": "Test",
            "last_name": "Prospect",
            "lead_source": "website"
        }

        lead_response = client.post("/api/v1/leads", json=lead_data)
        assert lead_response.status_code == 201

        # Step 2: Assign lead
        assignment_data = {"assigned_to_id": "sales-rep-456"}
        assign_response = client.post("/api/v1/leads/lead-123/assign", json=assignment_data)
        assert assign_response.status_code == 200

        # Step 3: Convert lead
        conversion_data = {"lead_id": "lead-123"}
        convert_response = client.post("/api/v1/leads/lead-123/convert", json=conversion_data)
        assert convert_response.status_code == 200

        # Step 4: Create opportunity
        opp_data = {
            "customer_id": "customer-789",
            "organization_id": "org-123",
            "name": "New Opportunity",
            "amount": "100000.00",
            "expected_close_date": (date.today() + timedelta(days=30)).isoformat(),
            "sales_rep_id": "sales-rep-456"
        }

        opp_response = client.post("/api/v1/opportunities", json=opp_data)
        assert opp_response.status_code == 201

    @patch('app.crud.crm_v31.CRMService')
    def test_customer_lifecycle_management(self, mock_service):
        """Test comprehensive customer lifecycle management."""
        mock_service_instance = mock_service.return_value

        # Mock customer and related entities
        mock_customer = CustomerExtended(id="customer-123")
        mock_contact = ContactExtended(id="contact-456")
        mock_activity = CRMActivity(id="activity-789")
        mock_ticket = SupportTicket(id="ticket-012")

        mock_service_instance.create_customer.return_value = mock_customer
        mock_service_instance.create_contact.return_value = mock_contact
        mock_service_instance.create_activity.return_value = mock_activity
        mock_service_instance.create_support_ticket.return_value = mock_ticket

        # Customer lifecycle workflow
        customer_data = {
            "organization_id": "org-123",
            "company_name": "Test Customer Corp"
        }

        contact_data = {
            "customer_id": "customer-123",
            "organization_id": "org-123",
            "first_name": "John",
            "last_name": "Doe"
        }

        activity_data = {
            "organization_id": "org-123",
            "customer_id": "customer-123",
            "activity_type": "call",
            "subject": "Welcome call",
            "activity_date": datetime.now().isoformat(),
            "owner_id": "user-123"
        }

        ticket_data = {
            "customer_id": "customer-123",
            "organization_id": "org-123",
            "subject": "Setup assistance",
            "description": "Customer needs help with initial setup"
        }

        # Execute workflow
        customer_resp = client.post("/api/v1/customers", json=customer_data)
        assert customer_resp.status_code == 201

        contact_resp = client.post("/api/v1/contacts", json=contact_data)
        assert contact_resp.status_code == 201

        activity_resp = client.post("/api/v1/activities", json=activity_data)
        assert activity_resp.status_code == 201

        ticket_resp = client.post("/api/v1/support-tickets", json=ticket_data)
        assert ticket_resp.status_code == 201


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
