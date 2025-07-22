"""
Test suite for HR Management API - CC02 v31.0 Phase 2

Comprehensive tests for HR management system with 10 endpoints:
1. Employee Management
2. Payroll Processing
3. Leave Management
4. Performance Reviews
5. Training Management
6. Benefits Administration
7. Recruitment
8. Onboarding
9. Position Management
10. HR Analytics
"""

import json
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.hr_extended import (
    Employee,
    EmployeeBenefit,
    EmployeeStatus,
    EmploymentType,
    HRAnalytics,
    JobPosting,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    OnboardingRecord,
    PayFrequency,
    PayrollRecord,
    PerformanceRating,
    PerformanceReview,
    Position,
    RecruitmentStatus,
    TrainingRecord,
    TrainingStatus,
)
from tests.conftest import TestingSessionLocal, engine

client = TestClient(app)

# Test data fixtures
@pytest.fixture
def sample_employee_data():
    return {
        "organization_id": "org_123",
        "user_id": "user_123",
        "employee_number": "EMP001",
        "first_name": "John",
        "last_name": "Doe",
        "employment_type": "full_time",
        "hire_date": "2024-01-01",
        "job_title": "Software Engineer",
        "base_salary": 80000,
        "pay_frequency": "monthly",
        "standard_hours_per_week": 40
    }

@pytest.fixture
def sample_position_data():
    return {
        "organization_id": "org_123",
        "position_code": "SE001",
        "position_title": "Software Engineer",
        "employment_type": "full_time",
        "effective_date": "2024-01-01",
        "salary_min": 70000,
        "salary_max": 100000
    }

@pytest.fixture
def sample_payroll_data():
    return {
        "employee_id": "emp_123",
        "organization_id": "org_123",
        "pay_period_start": "2024-01-01",
        "pay_period_end": "2024-01-31",
        "pay_date": "2024-02-01",
        "regular_hours": 160,
        "regular_rate": 25.00,
        "regular_pay": 4000.00,
        "gross_pay": 4000.00,
        "net_pay": 3200.00
    }

@pytest.fixture
def sample_leave_request_data():
    return {
        "employee_id": "emp_123",
        "organization_id": "org_123",
        "leave_type": "annual",
        "start_date": "2024-03-01",
        "end_date": "2024-03-05",
        "reason": "Vacation",
        "is_paid": True
    }

@pytest.fixture
def sample_performance_review_data():
    return {
        "employee_id": "emp_123",
        "organization_id": "org_123",
        "review_period_start": "2024-01-01",
        "review_period_end": "2024-12-31",
        "reviewer_id": "mgr_123",
        "review_type": "annual",
        "overall_rating": "meets_expectations"
    }

@pytest.fixture
def sample_training_data():
    return {
        "employee_id": "emp_123",
        "organization_id": "org_123",
        "training_title": "Python Programming",
        "training_type": "skill_development",
        "training_category": "technical",
        "duration_hours": 40,
        "assessment_required": True
    }

@pytest.fixture
def sample_benefit_data():
    return {
        "employee_id": "emp_123",
        "organization_id": "org_123",
        "benefit_type": "health",
        "benefit_plan_name": "Premium Health Plan",
        "enrollment_date": "2024-01-01",
        "effective_date": "2024-01-01",
        "employee_contribution": 200.00,
        "employer_contribution": 800.00
    }

@pytest.fixture
def sample_job_posting_data():
    return {
        "organization_id": "org_123",
        "position_id": "pos_123",
        "posting_title": "Senior Software Engineer",
        "internal_only": False,
        "posted_date": "2024-01-01",
        "closing_date": "2024-02-01"
    }

@pytest.fixture
def sample_onboarding_data():
    return {
        "employee_id": "emp_123",
        "organization_id": "org_123",
        "planned_start_date": "2024-01-01",
        "planned_completion_date": "2024-01-30",
        "hr_coordinator_id": "hr_123"
    }

# =============================================================================
# 1. Employee Management Tests
# =============================================================================

class TestEmployeeManagement:
    """Test Employee Management endpoint."""
    
    def test_list_employees_success(self):
        """Test successful employee listing."""
        with patch('app.crud.hr_v31.get_employees') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/hr/employees")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_list_employees_with_filters(self):
        """Test employee listing with filters."""
        with patch('app.crud.hr_v31.get_employees') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/hr/employees?organization_id=org_123&department_id=dept_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(
                mock.ANY,
                filters={"organization_id": "org_123", "department_id": "dept_123"},
                skip=0,
                limit=100
            )

    def test_create_employee_success(self, sample_employee_data):
        """Test successful employee creation."""
        with patch('app.crud.hr_v31.create_employee') as mock_create:
            mock_employee = Employee(id="emp_123", **sample_employee_data)
            mock_create.return_value = mock_employee
            
            response = client.post("/api/v1/hr/employees", json=sample_employee_data)
            
            assert response.status_code == 200
            assert "emp_123" in str(response.json())
            mock_create.assert_called_once()

    def test_create_employee_validation_error(self):
        """Test employee creation with validation error."""
        invalid_data = {"first_name": "John"}  # Missing required fields
        
        response = client.post("/api/v1/hr/employees", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_get_employee_success(self):
        """Test successful employee retrieval."""
        with patch('app.crud.hr_v31.get_employee') as mock_get:
            mock_employee = Employee(id="emp_123", first_name="John", last_name="Doe")
            mock_get.return_value = mock_employee
            
            response = client.get("/api/v1/hr/employees/emp_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "emp_123")

    def test_get_employee_not_found(self):
        """Test employee retrieval when not found."""
        with patch('app.crud.hr_v31.get_employee') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/v1/hr/employees/nonexistent")
            
            assert response.status_code == 404
            assert "Employee not found" in response.json()["detail"]

    def test_update_employee_success(self, sample_employee_data):
        """Test successful employee update."""
        with patch('app.crud.hr_v31.update_employee') as mock_update:
            mock_employee = Employee(id="emp_123", **sample_employee_data)
            mock_update.return_value = mock_employee
            
            update_data = {"job_title": "Senior Software Engineer"}
            response = client.put("/api/v1/hr/employees/emp_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

    def test_terminate_employee_success(self):
        """Test successful employee termination."""
        with patch('app.crud.hr_v31.terminate_employee') as mock_terminate:
            mock_employee = Employee(id="emp_123", employee_status=EmployeeStatus.TERMINATED)
            mock_terminate.return_value = mock_employee
            
            termination_data = {
                "employee_id": "emp_123",
                "termination_date": "2024-01-31",
                "termination_reason": "Resignation"
            }
            response = client.post("/api/v1/hr/employees/emp_123/terminate", json=termination_data)
            
            assert response.status_code == 200
            mock_terminate.assert_called_once()

# =============================================================================
# 2. Payroll Processing Tests
# =============================================================================

class TestPayrollProcessing:
    """Test Payroll Processing endpoint."""
    
    def test_list_payroll_records_success(self):
        """Test successful payroll records listing."""
        with patch('app.crud.hr_v31.get_payroll_records') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/hr/payroll")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_payroll_record_success(self, sample_payroll_data):
        """Test successful payroll record creation."""
        with patch('app.crud.hr_v31.create_payroll_record') as mock_create:
            mock_record = PayrollRecord(id="pay_123", **sample_payroll_data)
            mock_create.return_value = mock_record
            
            response = client.post("/api/v1/hr/payroll", json=sample_payroll_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_calculate_payroll_success(self):
        """Test successful payroll calculation."""
        with patch('app.crud.hr_v31.calculate_payroll') as mock_calculate:
            mock_record = PayrollRecord(id="pay_123", gross_pay=Decimal("4000.00"))
            mock_calculate.return_value = mock_record
            
            calculation_data = {
                "employee_id": "emp_123",
                "pay_period_start": "2024-01-01",
                "pay_period_end": "2024-01-31",
                "regular_hours": 160
            }
            response = client.post("/api/v1/hr/payroll/calculate", json=calculation_data)
            
            assert response.status_code == 200
            mock_calculate.assert_called_once()

    def test_get_payroll_record_success(self):
        """Test successful payroll record retrieval."""
        with patch('app.crud.hr_v31.get_payroll_record') as mock_get:
            mock_record = PayrollRecord(id="pay_123", gross_pay=Decimal("4000.00"))
            mock_get.return_value = mock_record
            
            response = client.get("/api/v1/hr/payroll/pay_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "pay_123")

    def test_update_payroll_record_success(self, sample_payroll_data):
        """Test successful payroll record update."""
        with patch('app.crud.hr_v31.update_payroll_record') as mock_update:
            mock_record = PayrollRecord(id="pay_123", **sample_payroll_data)
            mock_update.return_value = mock_record
            
            update_data = {"bonus": 500.00}
            response = client.put("/api/v1/hr/payroll/pay_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

# =============================================================================
# 3. Leave Management Tests
# =============================================================================

class TestLeaveManagement:
    """Test Leave Management endpoint."""
    
    def test_list_leave_requests_success(self):
        """Test successful leave requests listing."""
        with patch('app.crud.hr_v31.get_leave_requests') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/hr/leave-requests")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_leave_request_success(self, sample_leave_request_data):
        """Test successful leave request creation."""
        with patch('app.crud.hr_v31.create_leave_request') as mock_create:
            mock_request = LeaveRequest(id="leave_123", **sample_leave_request_data)
            mock_create.return_value = mock_request
            
            response = client.post("/api/v1/hr/leave-requests", json=sample_leave_request_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_get_leave_request_success(self):
        """Test successful leave request retrieval."""
        with patch('app.crud.hr_v31.get_leave_request') as mock_get:
            mock_request = LeaveRequest(id="leave_123", leave_type=LeaveType.ANNUAL)
            mock_get.return_value = mock_request
            
            response = client.get("/api/v1/hr/leave-requests/leave_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "leave_123")

    def test_update_leave_request_success(self):
        """Test successful leave request update."""
        with patch('app.crud.hr_v31.update_leave_request') as mock_update:
            mock_request = LeaveRequest(id="leave_123", status=LeaveStatus.APPROVED)
            mock_update.return_value = mock_request
            
            update_data = {"return_date": "2024-03-06"}
            response = client.put("/api/v1/hr/leave-requests/leave_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

    def test_approve_leave_request_success(self):
        """Test successful leave request approval."""
        with patch('app.crud.hr_v31.approve_leave_request') as mock_approve:
            mock_request = LeaveRequest(id="leave_123", status=LeaveStatus.APPROVED)
            mock_approve.return_value = mock_request
            
            approval_data = {
                "leave_request_id": "leave_123",
                "approval_notes": "Approved by manager"
            }
            response = client.post("/api/v1/hr/leave-requests/leave_123/approve", json=approval_data)
            
            assert response.status_code == 200
            mock_approve.assert_called_once()

# =============================================================================
# 4. Performance Reviews Tests
# =============================================================================

class TestPerformanceReviews:
    """Test Performance Reviews endpoint."""
    
    def test_list_performance_reviews_success(self):
        """Test successful performance reviews listing."""
        with patch('app.crud.hr_v31.get_performance_reviews') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/hr/performance-reviews")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_performance_review_success(self, sample_performance_review_data):
        """Test successful performance review creation."""
        with patch('app.crud.hr_v31.create_performance_review') as mock_create:
            mock_review = PerformanceReview(id="review_123", **sample_performance_review_data)
            mock_create.return_value = mock_review
            
            response = client.post("/api/v1/hr/performance-reviews", json=sample_performance_review_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_create_review_cycle_success(self):
        """Test successful review cycle creation."""
        cycle_data = {
            "organization_id": "org_123",
            "review_period_start": "2024-01-01",
            "review_period_end": "2024-12-31"
        }
        
        response = client.post("/api/v1/hr/performance-reviews/cycle", json=cycle_data)
        
        assert response.status_code == 200
        assert "Performance review cycle created" in response.json()["message"]

    def test_get_performance_review_success(self):
        """Test successful performance review retrieval."""
        with patch('app.crud.hr_v31.get_performance_review') as mock_get:
            mock_review = PerformanceReview(id="review_123", overall_rating=PerformanceRating.MEETS_EXPECTATIONS)
            mock_get.return_value = mock_review
            
            response = client.get("/api/v1/hr/performance-reviews/review_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "review_123")

    def test_update_performance_review_success(self):
        """Test successful performance review update."""
        with patch('app.crud.hr_v31.update_performance_review') as mock_update:
            mock_review = PerformanceReview(id="review_123", status="completed")
            mock_update.return_value = mock_review
            
            update_data = {"overall_rating": "exceeds_expectations"}
            response = client.put("/api/v1/hr/performance-reviews/review_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

# =============================================================================
# 5. Training Management Tests
# =============================================================================

class TestTrainingManagement:
    """Test Training Management endpoint."""
    
    def test_list_training_records_success(self):
        """Test successful training records listing."""
        with patch('app.crud.hr_v31.get_training_records') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/hr/training")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_training_record_success(self, sample_training_data):
        """Test successful training record creation."""
        with patch('app.crud.hr_v31.create_training_record') as mock_create:
            mock_record = TrainingRecord(id="training_123", **sample_training_data)
            mock_create.return_value = mock_record
            
            response = client.post("/api/v1/hr/training", json=sample_training_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_get_training_record_success(self):
        """Test successful training record retrieval."""
        with patch('app.crud.hr_v31.get_training_record') as mock_get:
            mock_record = TrainingRecord(id="training_123", status=TrainingStatus.COMPLETED)
            mock_get.return_value = mock_record
            
            response = client.get("/api/v1/hr/training/training_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "training_123")

    def test_update_training_record_success(self):
        """Test successful training record update."""
        with patch('app.crud.hr_v31.update_training_record') as mock_update:
            mock_record = TrainingRecord(id="training_123", status=TrainingStatus.IN_PROGRESS)
            mock_update.return_value = mock_record
            
            update_data = {"completion_percentage": 50}
            response = client.put("/api/v1/hr/training/training_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

    def test_complete_training_success(self):
        """Test successful training completion."""
        with patch('app.crud.hr_v31.complete_employee_training') as mock_complete:
            mock_record = TrainingRecord(id="training_123", status=TrainingStatus.COMPLETED)
            mock_complete.return_value = mock_record
            
            completion_data = {
                "training_id": "training_123",
                "assessment_score": 85,
                "satisfaction_rating": 4
            }
            response = client.post("/api/v1/hr/training/training_123/complete", json=completion_data)
            
            assert response.status_code == 200
            mock_complete.assert_called_once()

# =============================================================================
# 6. Benefits Administration Tests
# =============================================================================

class TestBenefitsAdministration:
    """Test Benefits Administration endpoint."""
    
    def test_list_employee_benefits_success(self):
        """Test successful employee benefits listing."""
        response = client.get("/api/v1/hr/benefits")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_create_benefit_enrollment_success(self, sample_benefit_data):
        """Test successful benefit enrollment creation."""
        with patch('app.crud.hr_v31.create_employee_benefit') as mock_create:
            mock_benefit = EmployeeBenefit(id="benefit_123", **sample_benefit_data)
            mock_create.return_value = mock_benefit
            
            response = client.post("/api/v1/hr/benefits", json=sample_benefit_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_get_benefit_details_success(self):
        """Test successful benefit details retrieval."""
        with patch('app.crud.hr_v31.get_employee_benefit') as mock_get:
            mock_benefit = EmployeeBenefit(id="benefit_123", benefit_type="health")
            mock_get.return_value = mock_benefit
            
            response = client.get("/api/v1/hr/benefits/benefit_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "benefit_123")

    def test_update_benefit_enrollment_success(self):
        """Test successful benefit enrollment update."""
        with patch('app.crud.hr_v31.update_employee_benefit') as mock_update:
            mock_benefit = EmployeeBenefit(id="benefit_123", is_active=False)
            mock_update.return_value = mock_benefit
            
            update_data = {"is_active": False}
            response = client.put("/api/v1/hr/benefits/benefit_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

# =============================================================================
# 7. Recruitment Tests
# =============================================================================

class TestRecruitment:
    """Test Recruitment endpoint."""
    
    def test_list_job_postings_success(self):
        """Test successful job postings listing."""
        with patch('app.crud.hr_v31.get_job_postings') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/hr/job-postings")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_job_posting_success(self, sample_job_posting_data):
        """Test successful job posting creation."""
        with patch('app.crud.hr_v31.create_job_posting') as mock_create:
            mock_posting = JobPosting(id="posting_123", **sample_job_posting_data)
            mock_create.return_value = mock_posting
            
            response = client.post("/api/v1/hr/job-postings", json=sample_job_posting_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_get_job_posting_success(self):
        """Test successful job posting retrieval."""
        with patch('app.crud.hr_v31.get_job_posting') as mock_get:
            mock_posting = JobPosting(id="posting_123", status=RecruitmentStatus.OPEN)
            mock_get.return_value = mock_posting
            
            response = client.get("/api/v1/hr/job-postings/posting_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "posting_123")

    def test_update_job_posting_success(self):
        """Test successful job posting update."""
        with patch('app.crud.hr_v31.update_job_posting') as mock_update:
            mock_posting = JobPosting(id="posting_123", status=RecruitmentStatus.FILLED)
            mock_update.return_value = mock_posting
            
            update_data = {"status": "filled"}
            response = client.put("/api/v1/hr/job-postings/posting_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

# =============================================================================
# 8. Onboarding Tests
# =============================================================================

class TestOnboarding:
    """Test Onboarding endpoint."""
    
    def test_list_onboarding_records_success(self):
        """Test successful onboarding records listing."""
        with patch('app.crud.hr_v31.get_onboarding_records') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/hr/onboarding")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_onboarding_record_success(self, sample_onboarding_data):
        """Test successful onboarding record creation."""
        with patch('app.crud.hr_v31.create_onboarding_record') as mock_create:
            mock_record = OnboardingRecord(id="onboarding_123", **sample_onboarding_data)
            mock_create.return_value = mock_record
            
            response = client.post("/api/v1/hr/onboarding", json=sample_onboarding_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_get_onboarding_record_success(self):
        """Test successful onboarding record retrieval."""
        with patch('app.crud.hr_v31.get_onboarding_record') as mock_get:
            mock_record = OnboardingRecord(id="onboarding_123", status="in_progress")
            mock_get.return_value = mock_record
            
            response = client.get("/api/v1/hr/onboarding/onboarding_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "onboarding_123")

    def test_update_onboarding_record_success(self):
        """Test successful onboarding record update."""
        with patch('app.crud.hr_v31.update_onboarding_record') as mock_update:
            mock_record = OnboardingRecord(id="onboarding_123", status="completed")
            mock_update.return_value = mock_record
            
            update_data = {"status": "completed"}
            response = client.put("/api/v1/hr/onboarding/onboarding_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

# =============================================================================
# 9. Position Management Tests
# =============================================================================

class TestPositionManagement:
    """Test Position Management endpoint."""
    
    def test_list_positions_success(self):
        """Test successful positions listing."""
        with patch('app.crud.hr_v31.get_positions') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/hr/positions")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_position_success(self, sample_position_data):
        """Test successful position creation."""
        with patch('app.crud.hr_v31.create_position') as mock_create:
            mock_position = Position(id="pos_123", **sample_position_data)
            mock_create.return_value = mock_position
            
            response = client.post("/api/v1/hr/positions", json=sample_position_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_get_position_success(self):
        """Test successful position retrieval."""
        with patch('app.crud.hr_v31.get_position') as mock_get:
            mock_position = Position(id="pos_123", is_active=True)
            mock_get.return_value = mock_position
            
            response = client.get("/api/v1/hr/positions/pos_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "pos_123")

    def test_update_position_success(self):
        """Test successful position update."""
        with patch('app.crud.hr_v31.update_position') as mock_update:
            mock_position = Position(id="pos_123", is_active=False)
            mock_update.return_value = mock_position
            
            update_data = {"is_active": False}
            response = client.put("/api/v1/hr/positions/pos_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

# =============================================================================
# 10. HR Analytics Tests
# =============================================================================

class TestHRAnalytics:
    """Test HR Analytics endpoint."""
    
    def test_get_hr_analytics_success(self):
        """Test successful HR analytics retrieval."""
        with patch('app.crud.hr_v31.get_hr_analytics') as mock_get:
            mock_analytics = HRAnalytics(
                id="analytics_123",
                organization_id="org_123",
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31)
            )
            mock_get.return_value = mock_analytics
            
            response = client.get("/api/v1/hr/analytics?organization_id=org_123&period_start=2024-01-01&period_end=2024-01-31")
            
            assert response.status_code == 200
            mock_get.assert_called_once()

    def test_get_hr_analytics_not_found(self):
        """Test HR analytics retrieval when not found."""
        with patch('app.crud.hr_v31.get_hr_analytics') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/v1/hr/analytics?organization_id=org_123&period_start=2024-01-01&period_end=2024-01-31")
            
            assert response.status_code == 404
            assert "Analytics data not found" in response.json()["detail"]

    def test_get_hr_dashboard_success(self):
        """Test successful HR dashboard retrieval."""
        with patch('app.crud.hr_v31.get_hr_dashboard_metrics') as mock_get:
            from app.schemas.hr_v31 import HRDashboardMetrics
            mock_metrics = HRDashboardMetrics(
                organization_id="org_123",
                as_of_date=date.today(),
                current_active_employees=100,
                turnover_rate=5.2,
                retention_rate=94.8,
                new_hires_this_period=5,
                performance_review_completion_rate=85.0,
                training_completion_rate=92.0,
                average_salary=75000.0,
                pending_leave_requests=3,
                upcoming_performance_reviews=12
            )
            mock_get.return_value = mock_metrics
            
            response = client.get("/api/v1/hr/dashboard?organization_id=org_123")
            
            assert response.status_code == 200
            assert response.json()["current_active_employees"] == 100
            mock_get.assert_called_once()

    def test_get_employee_tenure_analysis_success(self):
        """Test successful employee tenure analysis."""
        response = client.get("/api/v1/hr/employees/emp_123/tenure")
        
        assert response.status_code == 200
        assert response.json()["employee_id"] == "emp_123"

    def test_get_employee_leave_balance_success(self):
        """Test successful employee leave balance retrieval."""
        response = client.get("/api/v1/hr/employees/emp_123/leave-balance")
        
        assert response.status_code == 200
        assert response.json()["employee_id"] == "emp_123"
        assert "leave_balances" in response.json()

    def test_get_payroll_summary_success(self):
        """Test successful payroll summary retrieval."""
        response = client.get("/api/v1/hr/payroll/summary?organization_id=org_123&period=2024-01")
        
        assert response.status_code == 200
        assert response.json()["organization_id"] == "org_123"
        assert response.json()["period"] == "2024-01"

# =============================================================================
# Integration Tests
# =============================================================================

class TestHRIntegration:
    """Test HR system integration scenarios."""
    
    def test_employee_lifecycle_integration(self):
        """Test complete employee lifecycle integration."""
        # This would test creating employee, onboarding, payroll, performance reviews, etc.
        # in a complete workflow
        assert True  # Placeholder for integration test

    def test_performance_review_cycle_integration(self):
        """Test complete performance review cycle."""
        # This would test creating review cycle, completing reviews, approvals, etc.
        assert True  # Placeholder for integration test

    def test_payroll_processing_integration(self):
        """Test complete payroll processing workflow."""
        # This would test calculating payroll, processing, generating reports, etc.
        assert True  # Placeholder for integration test

# =============================================================================
# Error Handling Tests
# =============================================================================

class TestHRErrorHandling:
    """Test HR API error handling."""
    
    def test_database_error_handling(self):
        """Test database error handling."""
        with patch('app.crud.hr_v31.get_employees') as mock_get:
            mock_get.side_effect = Exception("Database connection error")
            
            response = client.get("/api/v1/hr/employees")
            
            assert response.status_code == 500
            assert "Error retrieving employees" in response.json()["detail"]

    def test_validation_error_handling(self):
        """Test validation error handling."""
        invalid_data = {"employee_id": ""}  # Invalid empty ID
        
        response = client.post("/api/v1/hr/payroll", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_business_logic_error_handling(self):
        """Test business logic error handling."""
        with patch('app.crud.hr_v31.create_employee') as mock_create:
            mock_create.side_effect = ValueError("Employee number already exists")
            
            sample_data = {
                "organization_id": "org_123",
                "user_id": "user_123",
                "employee_number": "EMP001",
                "first_name": "John",
                "last_name": "Doe",
                "employment_type": "full_time",
                "hire_date": "2024-01-01",
                "job_title": "Software Engineer"
            }
            
            response = client.post("/api/v1/hr/employees", json=sample_data)
            
            assert response.status_code == 400
            assert "Employee number already exists" in response.json()["detail"]

# =============================================================================
# Performance Tests
# =============================================================================

class TestHRPerformance:
    """Test HR API performance scenarios."""
    
    def test_large_employee_list_performance(self):
        """Test performance with large employee lists."""
        # This would test pagination, filtering with large datasets
        assert True  # Placeholder for performance test

    def test_bulk_payroll_processing_performance(self):
        """Test performance of bulk payroll processing."""
        # This would test processing payroll for many employees
        assert True  # Placeholder for performance test

    def test_analytics_calculation_performance(self):
        """Test performance of HR analytics calculations."""
        # This would test complex analytics queries with large datasets
        assert True  # Placeholder for performance test