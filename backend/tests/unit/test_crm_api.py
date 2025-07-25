"""
CC02 v53.0 CRM API Tests - Issue #568
10-Day ERP Business API Implementation Sprint - Day 7-8 Phase 3
Comprehensive Test-Driven Development Test Suite
"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import date, datetime
import uuid
from typing import List, Dict, Any

from app.main_super_minimal import app

class TestCRMAPIv53:
    """CC02 v53.0 CRM Management API Test Suite"""
    
    @pytest.fixture(autouse=True)
    def setup_clean_state(self):
        """Clear in-memory stores before each test"""
        from app.api.v1.endpoints.crm_v53 import (
            leads_store, opportunities_store, contacts_store, 
            activities_store, campaigns_store
        )
        leads_store.clear()
        opportunities_store.clear()
        contacts_store.clear()
        activities_store.clear()
        campaigns_store.clear()
    
    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for CC02 v53.0 CRM API testing."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_lead_data(self) -> Dict[str, Any]:
        """Sample lead data for testing."""
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "company": "Acme Corp",
            "job_title": "CEO",
            "lead_source": "website",
            "status": "new",
            "estimated_value": "50000.00",
            "probability": "25.0",
            "expected_close_date": "2024-03-15",
            "industry": "Technology",
            "company_size": 50,
            "annual_revenue": "5000000.00",
            "notes": "High-value potential customer from website inquiry"
        }
    
    @pytest.fixture
    def sample_opportunity_data(self) -> Dict[str, Any]:
        """Sample opportunity data for testing."""
        return {
            "name": "Enterprise Software Deal",
            "stage": "qualification",
            "amount": "75000.00",
            "probability": "40.0",
            "expected_close_date": "2024-04-30",
            "lead_source": "referral",
            "next_step": "Schedule technical demo",
            "description": "Large enterprise opportunity for our software suite"
        }
    
    @pytest.fixture
    def sample_activity_data(self) -> Dict[str, Any]:
        """Sample activity data for testing."""
        return {
            "subject": "Follow-up call with prospect",
            "activity_type": "call",
            "status": "scheduled",
            "priority": "high",
            "due_date": "2024-02-15T14:30:00",
            "duration_minutes": 30,
            "description": "Discuss their requirements and present our solution"
        }
    
    @pytest.fixture
    def sample_campaign_data(self) -> Dict[str, Any]:
        """Sample campaign data for testing."""
        return {
            "name": "Q1 Digital Marketing Campaign",
            "campaign_type": "email",
            "status": "planned",
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "budget": "25000.00",
            "expected_revenue": "150000.00",
            "target_audience": "Technology executives in mid-size companies",
            "description": "Comprehensive email marketing campaign for Q1"
        }
    
    # Lead Management Tests
    
    def test_create_lead_basic(self, client: TestClient, sample_lead_data):
        """Test basic lead creation with required fields only"""
        basic_lead = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com"
        }
        
        response = client.post("/api/v1/crm-v53/leads/", json=basic_lead)
        assert response.status_code == 201
        
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
        assert data["full_name"] == "Jane Smith"
        assert data["email"] == "jane.smith@example.com"
        assert data["status"] == "new"
        assert data["lead_source"] == "other"
        assert data["is_converted"] is False
        assert "id" in data
        assert "created_at" in data
    
    def test_create_lead_comprehensive(self, client: TestClient, sample_lead_data):
        """Test comprehensive lead creation with all fields"""
        response = client.post("/api/v1/crm-v53/leads/", json=sample_lead_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["first_name"] == sample_lead_data["first_name"]
        assert data["last_name"] == sample_lead_data["last_name"]
        assert data["full_name"] == "John Doe"
        assert data["email"] == sample_lead_data["email"]
        assert data["phone"] == sample_lead_data["phone"]
        assert data["company"] == sample_lead_data["company"]
        assert data["job_title"] == sample_lead_data["job_title"]
        assert data["lead_source"] == sample_lead_data["lead_source"]
        assert data["status"] == sample_lead_data["status"]
        assert float(data["estimated_value"]) == float(sample_lead_data["estimated_value"])
        assert float(data["probability"]) == float(sample_lead_data["probability"])
        assert data["industry"] == sample_lead_data["industry"]
        assert data["company_size"] == sample_lead_data["company_size"]
        assert data["notes"] == sample_lead_data["notes"]
    
    def test_create_lead_duplicate_email(self, client: TestClient):
        """Test lead creation with duplicate email fails"""
        lead_data = {
            "first_name": "Lead",
            "last_name": "One",
            "email": "duplicate@test.com"
        }
        
        # Create first lead
        response1 = client.post("/api/v1/crm-v53/leads/", json=lead_data)
        assert response1.status_code == 201
        
        # Try to create second lead with same email
        lead_data["first_name"] = "Lead Two"
        response2 = client.post("/api/v1/crm-v53/leads/", json=lead_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    def test_list_leads_empty(self, client: TestClient):
        """Test listing leads when none exist"""
        response = client.get("/api/v1/crm-v53/leads/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 50
        assert data["pages"] == 0
    
    def test_list_leads_with_filtering(self, client: TestClient, sample_lead_data):
        """Test listing leads with comprehensive filtering"""
        # Create test leads
        leads = []
        for i in range(3):
            lead_data = sample_lead_data.copy()
            lead_data["first_name"] = f"Lead{i+1}"
            lead_data["last_name"] = f"Test{i+1}"
            lead_data["email"] = f"lead{i+1}@test.com"
            lead_data["status"] = "qualified" if i % 2 == 0 else "new"
            lead_data["lead_source"] = "website" if i % 2 == 0 else "referral"
            response = client.post("/api/v1/crm-v53/leads/", json=lead_data)
            assert response.status_code == 201
            leads.append(response.json())
        
        # Test basic listing
        response = client.get("/api/v1/crm-v53/leads/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        
        # Test filtering by status
        response = client.get("/api/v1/crm-v53/leads/?status=qualified")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # Leads 1 and 3
        
        # Test filtering by lead source
        response = client.get("/api/v1/crm-v53/leads/?lead_source=referral")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1  # Lead 2
        
        # Test search functionality
        response = client.get("/api/v1/crm-v53/leads/?search=Lead1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["first_name"] == "Lead1"
    
    def test_get_lead_not_found(self, client: TestClient):
        """Test getting non-existent lead"""
        response = client.get("/api/v1/crm-v53/leads/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_lead_with_activity_metrics(self, client: TestClient, sample_lead_data):
        """Test getting lead with calculated activity metrics"""
        # Create lead
        response = client.post("/api/v1/crm-v53/leads/", json=sample_lead_data)
        assert response.status_code == 201
        lead = response.json()
        lead_id = lead["id"]
        
        # Get lead details
        response = client.get(f"/api/v1/crm-v53/leads/{lead_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == lead_id
        assert data["activities_count"] == 0  # No activities yet
        assert data["last_contacted"] is None
    
    def test_update_lead(self, client: TestClient, sample_lead_data):
        """Test updating lead"""
        # Create lead
        response = client.post("/api/v1/crm-v53/leads/", json=sample_lead_data)
        assert response.status_code == 201
        lead = response.json()
        
        # Update lead
        update_data = {
            "status": "qualified",
            "probability": "75.0",
            "notes": "Updated after successful qualification call"
        }
        
        response = client.put(f"/api/v1/crm-v53/leads/{lead['id']}", json=update_data)
        assert response.status_code == 200
        
        updated_lead = response.json()
        assert updated_lead["status"] == "qualified"
        assert float(updated_lead["probability"]) == 75.0
        assert updated_lead["notes"] == "Updated after successful qualification call"
        assert updated_lead["updated_at"] != lead["updated_at"]
    
    def test_convert_lead_to_opportunity(self, client: TestClient, sample_lead_data):
        """Test converting lead to opportunity"""
        # Create lead
        response = client.post("/api/v1/crm-v53/leads/", json=sample_lead_data)
        assert response.status_code == 201
        lead = response.json()
        
        # Convert lead
        conversion_data = {
            "create_customer": True,
            "create_opportunity": True,
            "create_contact": True,
            "opportunity_name": "Converted Opportunity",
            "opportunity_amount": "60000.00",
            "opportunity_stage": "needs_analysis",
            "conversion_notes": "Successful lead conversion after demo"
        }
        
        response = client.post(f"/api/v1/crm-v53/leads/{lead['id']}/convert", json=conversion_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["lead_id"] == lead["id"]
        assert result["customer_id"] is not None
        assert result["opportunity_id"] is not None
        assert result["contact_id"] is not None
        assert result["notes"] == conversion_data["conversion_notes"]
        
        # Check lead is marked as converted
        response = client.get(f"/api/v1/crm-v53/leads/{lead['id']}")
        updated_lead = response.json()
        assert updated_lead["is_converted"] is True
        assert updated_lead["status"] == "converted"
        assert updated_lead["converted_opportunity_id"] == result["opportunity_id"]
    
    def test_convert_lead_already_converted(self, client: TestClient, sample_lead_data):
        """Test converting already converted lead"""
        # Create and convert lead
        response = client.post("/api/v1/crm-v53/leads/", json=sample_lead_data)
        lead = response.json()
        
        conversion_data = {"create_opportunity": True}
        response = client.post(f"/api/v1/crm-v53/leads/{lead['id']}/convert", json=conversion_data)
        assert response.status_code == 200
        
        # Try to convert again
        response = client.post(f"/api/v1/crm-v53/leads/{lead['id']}/convert", json=conversion_data)
        assert response.status_code == 400
        assert "already converted" in response.json()["detail"]
    
    # Opportunity Management Tests
    
    def test_create_opportunity_basic(self, client: TestClient, sample_opportunity_data):
        """Test basic opportunity creation"""
        response = client.post("/api/v1/crm-v53/opportunities/", json=sample_opportunity_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_opportunity_data["name"]
        assert data["stage"] == sample_opportunity_data["stage"]
        assert float(data["amount"]) == float(sample_opportunity_data["amount"])
        assert float(data["probability"]) == float(sample_opportunity_data["probability"])
        assert data["next_step"] == sample_opportunity_data["next_step"]
        assert data["description"] == sample_opportunity_data["description"]
        assert data["is_won"] is False
        assert data["is_lost"] is False
        assert float(data["weighted_amount"]) == float(sample_opportunity_data["amount"]) * float(sample_opportunity_data["probability"]) / 100
        assert "id" in data
        assert "created_at" in data
    
    def test_create_opportunity_with_lead(self, client: TestClient, sample_lead_data, sample_opportunity_data):
        """Test creating opportunity linked to lead"""
        # Create lead first
        response = client.post("/api/v1/crm-v53/leads/", json=sample_lead_data)
        assert response.status_code == 201
        lead = response.json()
        
        # Create opportunity linked to lead
        opp_data = sample_opportunity_data.copy()
        opp_data["lead_id"] = lead["id"]
        
        response = client.post("/api/v1/crm-v53/opportunities/", json=opp_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["lead_id"] == lead["id"]
        assert data["lead_name"] == lead["full_name"]
    
    def test_list_opportunities_empty(self, client: TestClient):
        """Test listing opportunities when none exist"""
        response = client.get("/api/v1/crm-v53/opportunities/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
    
    def test_list_opportunities_with_filtering(self, client: TestClient, sample_opportunity_data):
        """Test listing opportunities with comprehensive filtering"""
        # Create test opportunities
        stages = ["qualification", "needs_analysis", "proposal"]
        amounts = ["25000.00", "50000.00", "75000.00"]
        
        for i in range(3):
            opp_data = sample_opportunity_data.copy()
            opp_data["name"] = f"Opportunity {i+1}"
            opp_data["stage"] = stages[i]
            opp_data["amount"] = amounts[i]
            response = client.post("/api/v1/crm-v53/opportunities/", json=opp_data)
            assert response.status_code == 201
        
        # Test basic listing
        response = client.get("/api/v1/crm-v53/opportunities/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Test filtering by stage
        response = client.get("/api/v1/crm-v53/opportunities/?stage=qualification")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["stage"] == "qualification"
        
        # Test filtering by amount range
        response = client.get("/api/v1/crm-v53/opportunities/?min_amount=50000")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # 50k and 75k opportunities
        
        response = client.get("/api/v1/crm-v53/opportunities/?max_amount=50000")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # 25k and 50k opportunities
    
    def test_get_opportunity_not_found(self, client: TestClient):
        """Test getting non-existent opportunity"""
        response = client.get("/api/v1/crm-v53/opportunities/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_opportunity_with_metrics(self, client: TestClient, sample_opportunity_data):
        """Test getting opportunity with calculated metrics"""
        # Create opportunity
        response = client.post("/api/v1/crm-v53/opportunities/", json=sample_opportunity_data)
        assert response.status_code == 201
        opportunity = response.json()
        
        # Get opportunity details
        response = client.get(f"/api/v1/crm-v53/opportunities/{opportunity['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == opportunity["id"]
        assert data["activities_count"] == 0
        assert data["age_days"] >= 0
        assert data["last_activity_date"] is None
    
    # Activity Management Tests
    
    def test_create_activity_basic(self, client: TestClient, sample_activity_data):
        """Test basic activity creation"""
        response = client.post("/api/v1/crm-v53/activities/", json=sample_activity_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["subject"] == sample_activity_data["subject"]
        assert data["activity_type"] == sample_activity_data["activity_type"]
        assert data["status"] == sample_activity_data["status"]
        assert data["priority"] == sample_activity_data["priority"]
        assert data["duration_minutes"] == sample_activity_data["duration_minutes"]
        assert data["description"] == sample_activity_data["description"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_activity_with_relationships(self, client: TestClient, sample_lead_data, sample_opportunity_data, sample_activity_data):
        """Test creating activity with lead and opportunity relationships"""
        # Create lead and opportunity
        response = client.post("/api/v1/crm-v53/leads/", json=sample_lead_data)
        lead = response.json()
        
        response = client.post("/api/v1/crm-v53/opportunities/", json=sample_opportunity_data)
        opportunity = response.json()
        
        # Create activity with relationships
        activity_data = sample_activity_data.copy()
        activity_data["lead_id"] = lead["id"]
        activity_data["opportunity_id"] = opportunity["id"]
        
        response = client.post("/api/v1/crm-v53/activities/", json=activity_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["lead_id"] == lead["id"]
        assert data["lead_name"] == lead["full_name"]
        assert data["opportunity_id"] == opportunity["id"]
        assert data["opportunity_name"] == opportunity["name"]
    
    def test_list_activities_with_filtering(self, client: TestClient, sample_activity_data):
        """Test listing activities with comprehensive filtering"""
        # Create test activities
        activity_types = ["call", "email", "meeting"]
        statuses = ["scheduled", "completed", "cancelled"]
        
        for i in range(3):
            activity_data = sample_activity_data.copy()
            activity_data["subject"] = f"Activity {i+1}"
            activity_data["activity_type"] = activity_types[i]
            activity_data["status"] = statuses[i]
            response = client.post("/api/v1/crm-v53/activities/", json=activity_data)
            assert response.status_code == 201
        
        # Test basic listing
        response = client.get("/api/v1/crm-v53/activities/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Test filtering by activity type
        response = client.get("/api/v1/crm-v53/activities/?activity_type=call")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["activity_type"] == "call"
        
        # Test filtering by status
        response = client.get("/api/v1/crm-v53/activities/?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "completed"
    
    # Campaign Management Tests
    
    def test_create_campaign_basic(self, client: TestClient, sample_campaign_data):
        """Test basic campaign creation"""
        response = client.post("/api/v1/crm-v53/campaigns/", json=sample_campaign_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_campaign_data["name"]
        assert data["campaign_type"] == sample_campaign_data["campaign_type"]
        assert data["status"] == sample_campaign_data["status"]
        assert float(data["budget"]) == float(sample_campaign_data["budget"])
        assert float(data["expected_revenue"]) == float(sample_campaign_data["expected_revenue"])
        assert data["target_audience"] == sample_campaign_data["target_audience"]
        assert data["description"] == sample_campaign_data["description"]
        assert data["leads_generated"] == 0
        assert data["is_active"] is False  # Status is planned
        assert "id" in data
        assert "created_at" in data
    
    def test_create_campaign_with_date_validation(self, client: TestClient):
        """Test campaign creation with end date before start date fails"""
        campaign_data = {
            "name": "Invalid Campaign",
            "campaign_type": "email",
            "start_date": "2024-03-01",
            "end_date": "2024-02-15"  # Before start date
        }
        
        response = client.post("/api/v1/crm-v53/campaigns/", json=campaign_data)
        assert response.status_code == 422  # Validation error
    
    # CRM Statistics Tests
    
    def test_get_crm_statistics_empty(self, client: TestClient):
        """Test CRM statistics when no data exists"""
        response = client.get("/api/v1/crm-v53/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_leads"] == 0
        assert data["total_opportunities"] == 0
        assert data["total_activities"] == 0
        assert data["total_contacts"] == 0
        assert data["total_campaigns"] == 0
        assert float(data["total_pipeline_value"]) == 0.0
        assert data["calculation_time_ms"] < 200  # Performance requirement
    
    def test_get_crm_statistics_with_data(self, client: TestClient, sample_lead_data, sample_opportunity_data, sample_activity_data, sample_campaign_data):
        """Test CRM statistics with comprehensive data"""
        # Create leads
        for i in range(3):
            lead_data = sample_lead_data.copy()
            lead_data["first_name"] = f"Lead{i+1}"
            lead_data["email"] = f"lead{i+1}@test.com"
            lead_data["status"] = ["new", "qualified", "converted"][i % 3]
            response = client.post("/api/v1/crm-v53/leads/", json=lead_data)
            assert response.status_code == 201
        
        # Create opportunities
        for i in range(2):
            opp_data = sample_opportunity_data.copy()
            opp_data["name"] = f"Opportunity {i+1}"
            opp_data["stage"] = ["qualification", "closed_won"][i]
            response = client.post("/api/v1/crm-v53/opportunities/", json=opp_data)
            assert response.status_code == 201
        
        # Create activities
        for i in range(4):
            activity_data = sample_activity_data.copy()
            activity_data["subject"] = f"Activity {i+1}"
            activity_data["status"] = "completed" if i % 2 == 0 else "scheduled"
            response = client.post("/api/v1/crm-v53/activities/", json=activity_data)
            assert response.status_code == 201
        
        # Create campaign
        response = client.post("/api/v1/crm-v53/campaigns/", json=sample_campaign_data)
        assert response.status_code == 201
        
        # Get statistics
        response = client.get("/api/v1/crm-v53/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_leads"] == 3
        assert data["qualified_leads"] == 1
        assert data["converted_leads"] == 1
        assert data["total_opportunities"] == 2
        assert data["won_opportunities"] == 1
        assert data["total_activities"] == 4
        assert data["completed_activities"] == 2
        assert data["total_campaigns"] == 1
        assert float(data["lead_conversion_rate"]) > 0
        assert float(data["opportunity_win_rate"]) > 0
        assert float(data["activity_completion_rate"]) == 50.0
        assert data["calculation_time_ms"] < 200  # Performance requirement
        
        # Check breakdown data
        assert "leads_by_source" in data
        assert "opportunities_by_stage" in data
        assert "activities_by_type" in data
    
    # Bulk Operations Tests
    
    def test_bulk_create_leads_validation_only(self, client: TestClient, sample_lead_data):
        """Test bulk lead creation with validation only"""
        lead1 = sample_lead_data.copy()
        lead1["email"] = "bulk1@test.com"
        
        lead2 = sample_lead_data.copy()
        lead2["first_name"] = "Bulk2"
        lead2["email"] = "bulk2@test.com"
        
        bulk_data = {
            "leads": [lead1, lead2],
            "validate_only": True
        }
        
        response = client.post("/api/v1/crm-v53/leads/bulk", json=bulk_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["created_count"] == 2
        assert data["failed_count"] == 0
        assert len(data["created_items"]) == 0  # No actual creation in validation mode
        assert data["execution_time_ms"] is not None
    
    def test_bulk_create_leads_actual(self, client: TestClient, sample_lead_data):
        """Test actual bulk lead creation"""
        lead1 = sample_lead_data.copy()
        lead1["email"] = "bulk1@test.com"
        
        lead2 = sample_lead_data.copy()
        lead2["first_name"] = "Bulk2"
        lead2["email"] = "bulk2@test.com"
        
        bulk_data = {
            "leads": [lead1, lead2],
            "validate_only": False,
            "assign_to": "user123"
        }
        
        response = client.post("/api/v1/crm-v53/leads/bulk", json=bulk_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["created_count"] == 2
        assert data["failed_count"] == 0
        assert len(data["created_items"]) == 2
        assert all("id" in item for item in data["created_items"])
        assert all(item["assigned_to"] == "user123" for item in data["created_items"])
    
    def test_bulk_create_leads_with_errors(self, client: TestClient, sample_lead_data):
        """Test bulk lead creation with duplicate email error"""
        # Create one lead first
        first_lead = sample_lead_data.copy()
        first_lead["email"] = "duplicate@test.com"
        response = client.post("/api/v1/crm-v53/leads/", json=first_lead)
        assert response.status_code == 201
        
        # Valid lead
        valid_lead = sample_lead_data.copy()
        valid_lead["email"] = "valid@test.com"
        valid_lead["first_name"] = "Valid"
        
        # Lead with duplicate email (should fail)
        duplicate_lead = sample_lead_data.copy()
        duplicate_lead["email"] = "duplicate@test.com"
        duplicate_lead["first_name"] = "Duplicate"
        
        bulk_data = {
            "leads": [valid_lead, duplicate_lead],
            "validate_only": False,
            "stop_on_error": False
        }
        
        response = client.post("/api/v1/crm-v53/leads/bulk", json=bulk_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["created_count"] == 1
        assert data["failed_count"] == 1
        assert len(data["created_items"]) == 1
        assert len(data["failed_items"]) == 1
        assert "error" in data["failed_items"][0]
    
    # Performance Tests
    
    def test_create_lead_performance(self, client: TestClient, sample_lead_data):
        """Test lead creation performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.post("/api/v1/crm-v53/leads/", json=sample_lead_data)
        end_time = time.time()
        
        assert response.status_code == 201
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Lead creation took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    def test_create_opportunity_performance(self, client: TestClient, sample_opportunity_data):
        """Test opportunity creation performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.post("/api/v1/crm-v53/opportunities/", json=sample_opportunity_data)
        end_time = time.time()
        
        assert response.status_code == 201
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Opportunity creation took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    def test_statistics_performance(self, client: TestClient):
        """Test statistics calculation performance (<200ms)"""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/crm-v53/statistics")
        end_time = time.time()
        
        assert response.status_code == 200
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 200, f"Statistics calculation took {execution_time_ms:.2f}ms, exceeding 200ms limit"
    
    # Health Check Test
    
    def test_crm_health_check(self, client: TestClient):
        """Test CRM API health check endpoint"""
        response = client.get("/api/v1/crm-v53/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "CRM Management API v53.0" in data["service"]
        assert "leads_count" in data
        assert "opportunities_count" in data
        assert "contacts_count" in data
        assert "activities_count" in data
        assert "campaigns_count" in data
        assert "timestamp" in data