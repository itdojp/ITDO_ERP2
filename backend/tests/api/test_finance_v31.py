"""
Finance API Tests - CC02 v31.0 Phase 2

Comprehensive test suite for financial management API covering:
- Chart of Accounts Management
- Journal Entry Processing
- Budget Management
- Cost Center Operations
- Financial Period Management
- Financial Reporting
- Tax Configuration
- Trial Balance
- Budget Variance Analysis
- Financial Analytics
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAccountManagement:
    """Test cases for Chart of Accounts management."""

    @pytest.fixture
    def sample_account_data(self):
        """Sample account data for testing."""
        return {
            "organization_id": "org-123",
            "account_name": "Cash - Operating Account",
            "account_type": "asset",
            "normal_balance": "debit",
            "description": "Primary operating cash account",
            "is_active": True,
            "allow_transactions": True,
        }

    @pytest.fixture
    def sample_account_response(self):
        """Sample account response for mocking."""
        return {
            "id": "acc-123",
            "organization_id": "org-123",
            "account_code": "1001",
            "account_name": "Cash - Operating Account",
            "account_type": "asset",
            "account_level": 0,
            "account_path": "1001",
            "normal_balance": "debit",
            "current_balance": 10000.00,
            "is_active": True,
            "allow_transactions": True,
            "created_at": "2024-01-01T10:00:00Z",
            "created_by": "user-123",
        }

    @patch("app.api.v1.finance_v31.AccountCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_create_account_success(self, mock_user, mock_crud_class, sample_account_data, sample_account_response):
        """Test successful account creation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_code.return_value = None
        mock_crud.create_account.return_value = Mock(**sample_account_response)

        # Make request
        response = client.post("/finance/accounts", json=sample_account_data)

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["account_name"] == sample_account_data["account_name"]
        assert data["account_type"] == sample_account_data["account_type"]
        assert data["account_code"] == "1001"
        
        # Verify CRUD methods called
        mock_crud.get_by_code.assert_not_called()  # No code provided
        mock_crud.create_account.assert_called_once()

    @patch("app.api.v1.finance_v31.AccountCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_create_account_duplicate_code(self, mock_user, mock_crud_class, sample_account_data):
        """Test account creation with duplicate code."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_code.return_value = Mock(id="existing-123")

        # Add account code to trigger duplicate check
        sample_account_data["account_code"] = "1001"

        # Make request
        response = client.post("/finance/accounts", json=sample_account_data)

        # Assertions
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @patch("app.api.v1.finance_v31.AccountCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_get_account_success(self, mock_user, mock_crud_class, sample_account_response):
        """Test successful account retrieval."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.get.return_value = Mock(**sample_account_response)

        # Make request
        response = client.get("/finance/accounts/acc-123")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "acc-123"
        assert data["account_name"] == sample_account_response["account_name"]

    @patch("app.api.v1.finance_v31.AccountCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_get_account_not_found(self, mock_user, mock_crud_class):
        """Test account retrieval when not found."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.get.return_value = None

        # Make request
        response = client.get("/finance/accounts/nonexistent")

        # Assertions
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("app.api.v1.finance_v31.AccountCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_list_accounts_success(self, mock_user, mock_crud_class, sample_account_response):
        """Test successful account listing."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.get_account_hierarchy.return_value = [Mock(**sample_account_response)]

        # Make request
        response = client.get("/finance/accounts?organization_id=org-123")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "acc-123"

    @patch("app.api.v1.finance_v31.AccountCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_update_account_success(self, mock_user, mock_crud_class, sample_account_response):
        """Test successful account update."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        updated_account = Mock(**sample_account_response)
        updated_account.account_name = "Updated Cash Account"
        mock_crud.update.return_value = updated_account

        # Update data
        update_data = {"account_name": "Updated Cash Account"}

        # Make request
        response = client.put("/finance/accounts/acc-123", json=update_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["account_name"] == "Updated Cash Account"


class TestJournalEntryProcessing:
    """Test cases for Journal Entry processing."""

    @pytest.fixture
    def sample_journal_entry_data(self):
        """Sample journal entry data for testing."""
        return {
            "organization_id": "org-123",
            "transaction_date": "2024-01-15T10:00:00Z",
            "description": "Cash payment for office supplies",
            "memo": "Invoice #12345",
            "lines": [
                {
                    "account_id": "acc-supplies",
                    "description": "Office supplies expense",
                    "debit_amount": 150.00,
                    "credit_amount": 0,
                },
                {
                    "account_id": "acc-cash",
                    "description": "Cash payment",
                    "debit_amount": 0,
                    "credit_amount": 150.00,
                },
            ],
        }

    @pytest.fixture
    def sample_journal_entry_response(self):
        """Sample journal entry response for mocking."""
        return {
            "id": "je-123",
            "organization_id": "org-123",
            "entry_number": "JE202401001",
            "transaction_date": "2024-01-15T10:00:00Z",
            "description": "Cash payment for office supplies",
            "memo": "Invoice #12345",
            "total_debit": 150.00,
            "total_credit": 150.00,
            "is_posted": False,
            "is_reversed": False,
            "created_by": "user-123",
            "lines": [
                {
                    "id": "jel-1",
                    "account_id": "acc-supplies",
                    "line_number": 1,
                    "description": "Office supplies expense",
                    "debit_amount": 150.00,
                    "credit_amount": 0,
                },
                {
                    "id": "jel-2",
                    "account_id": "acc-cash",
                    "line_number": 2,
                    "description": "Cash payment",
                    "debit_amount": 0,
                    "credit_amount": 150.00,
                },
            ],
        }

    @patch("app.api.v1.finance_v31.JournalEntryCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_create_journal_entry_success(self, mock_user, mock_crud_class, 
                                        sample_journal_entry_data, sample_journal_entry_response):
        """Test successful journal entry creation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.create_journal_entry.return_value = Mock(**sample_journal_entry_response)

        # Make request
        response = client.post("/finance/journal-entries", json=sample_journal_entry_data)

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["entry_number"] == "JE202401001"
        assert data["total_debit"] == 150.00
        assert data["total_credit"] == 150.00
        assert len(data["lines"]) == 2

    @patch("app.api.v1.finance_v31.JournalEntryCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_create_journal_entry_unbalanced(self, mock_user, mock_crud_class):
        """Test journal entry creation with unbalanced entry."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.create_journal_entry.side_effect = ValueError("Debits must equal credits")

        # Unbalanced entry data
        unbalanced_data = {
            "organization_id": "org-123",
            "transaction_date": "2024-01-15T10:00:00Z",
            "description": "Unbalanced entry",
            "lines": [
                {
                    "account_id": "acc-1",
                    "debit_amount": 100.00,
                    "credit_amount": 0,
                },
                {
                    "account_id": "acc-2",
                    "debit_amount": 0,
                    "credit_amount": 50.00,  # Unbalanced!
                },
            ],
        }

        # Make request
        response = client.post("/finance/journal-entries", json=unbalanced_data)

        # Assertions
        assert response.status_code == 400

    @patch("app.api.v1.finance_v31.JournalEntryCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_post_journal_entry_success(self, mock_user, mock_crud_class, sample_journal_entry_response):
        """Test successful journal entry posting."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        posted_entry = Mock(**sample_journal_entry_response)
        posted_entry.is_posted = True
        mock_crud.post_journal_entry.return_value = posted_entry

        # Make request
        response = client.post("/finance/journal-entries/post", json={"journal_entry_id": "je-123"})

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["is_posted"] is True

    @patch("app.api.v1.finance_v31.JournalEntryCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_reverse_journal_entry_success(self, mock_user, mock_crud_class, sample_journal_entry_response):
        """Test successful journal entry reversal."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        
        # Create reversal entry
        reversal_entry = Mock(**sample_journal_entry_response)
        reversal_entry.id = "je-124"
        reversal_entry.entry_number = "JE202401002"
        reversal_entry.description = "REVERSAL: Cash payment for office supplies"
        mock_crud.reverse_journal_entry.return_value = reversal_entry

        # Make request
        reverse_data = {
            "journal_entry_id": "je-123",
            "reason": "Correction of posting error",
        }
        response = client.post("/finance/journal-entries/reverse", json=reverse_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "je-124"
        assert "REVERSAL" in data["description"]


class TestBudgetManagement:
    """Test cases for Budget management."""

    @pytest.fixture
    def sample_budget_data(self):
        """Sample budget data for testing."""
        return {
            "organization_id": "org-123",
            "period_id": "period-2024",
            "budget_name": "Annual Operating Budget 2024",
            "budget_code": "AOB2024",
            "budget_type": "operational",
            "budget_start_date": "2024-01-01T00:00:00Z",
            "budget_end_date": "2024-12-31T23:59:59Z",
            "description": "Annual operating budget for fiscal year 2024",
        }

    @pytest.fixture
    def sample_budget_response(self):
        """Sample budget response for mocking."""
        return {
            "id": "budget-123",
            "organization_id": "org-123",
            "period_id": "period-2024",
            "budget_name": "Annual Operating Budget 2024",
            "budget_code": "AOB2024",
            "status": "draft",
            "version": 1,
            "total_revenue_budget": 1000000.00,
            "total_expense_budget": 800000.00,
            "net_budget": 200000.00,
            "created_by": "user-123",
            "budget_lines": [],
        }

    @patch("app.api.v1.finance_v31.BudgetCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_create_budget_success(self, mock_user, mock_crud_class, 
                                 sample_budget_data, sample_budget_response):
        """Test successful budget creation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.create.return_value = Mock(**sample_budget_response)

        # Make request
        response = client.post("/finance/budgets", json=sample_budget_data)

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["budget_name"] == sample_budget_data["budget_name"]
        assert data["budget_code"] == sample_budget_data["budget_code"]
        assert data["status"] == "draft"

    @patch("app.api.v1.finance_v31.BudgetCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_approve_budget_success(self, mock_user, mock_crud_class, sample_budget_response):
        """Test successful budget approval."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        approved_budget = Mock(**sample_budget_response)
        approved_budget.status = "active"
        approved_budget.approved_by = "user-123"
        mock_crud.approve_budget.return_value = approved_budget

        # Make request
        approve_data = {
            "budget_id": "budget-123",
            "approval_notes": "Budget approved after review",
        }
        response = client.post("/finance/budgets/approve", json=approve_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["approved_by"] == "user-123"

    @patch("app.api.v1.finance_v31.BudgetCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_get_budget_variance_analysis_success(self, mock_user, mock_crud_class):
        """Test successful budget variance analysis."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        
        variance_analysis = {
            "budget_id": "budget-123",
            "budget_name": "Annual Operating Budget 2024",
            "analysis_date": datetime.utcnow(),
            "total_budget": 1000000.00,
            "total_actual": 950000.00,
            "total_variance": -50000.00,
            "line_variances": [
                {
                    "account_id": "acc-1",
                    "account_code": "4000",
                    "account_name": "Revenue",
                    "budget_amount": 1000000.00,
                    "actual_amount": 950000.00,
                    "variance_amount": -50000.00,
                    "variance_percentage": -5.0,
                    "status": "watch",
                }
            ],
        }
        mock_crud.get_budget_variance_analysis.return_value = variance_analysis

        # Make request
        response = client.get("/finance/budgets/budget-123/variance-analysis")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["budget_id"] == "budget-123"
        assert data["total_variance"] == -50000.00
        assert len(data["line_variances"]) == 1


class TestCostCenterOperations:
    """Test cases for Cost Center operations."""

    @pytest.fixture
    def sample_cost_center_data(self):
        """Sample cost center data for testing."""
        return {
            "organization_id": "org-123",
            "cost_center_name": "Information Technology",
            "cost_center_type": "service",
            "manager_id": "user-manager",
            "budget_amount": 500000.00,
            "effective_date": "2024-01-01T00:00:00Z",
            "description": "IT department cost center",
        }

    @pytest.fixture
    def sample_cost_center_response(self):
        """Sample cost center response for mocking."""
        return {
            "id": "cc-123",
            "organization_id": "org-123",
            "cost_center_code": "CC0001",
            "cost_center_name": "Information Technology",
            "cost_center_type": "service",
            "cost_center_level": 0,
            "budget_amount": 500000.00,
            "actual_amount": 0.00,
            "committed_amount": 0.00,
            "is_active": True,
            "created_by": "user-123",
        }

    @patch("app.api.v1.finance_v31.CostCenterCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_create_cost_center_success(self, mock_user, mock_crud_class,
                                      sample_cost_center_data, sample_cost_center_response):
        """Test successful cost center creation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.create_cost_center.return_value = Mock(**sample_cost_center_response)

        # Make request
        response = client.post("/finance/cost-centers", json=sample_cost_center_data)

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["cost_center_name"] == sample_cost_center_data["cost_center_name"]
        assert data["cost_center_code"] == "CC0001"

    @patch("app.api.v1.finance_v31.CostCenterCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_get_cost_center_performance_success(self, mock_user, mock_crud_class):
        """Test successful cost center performance retrieval."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        
        performance_data = {
            "cost_center_id": "cc-123",
            "cost_center_code": "CC0001",
            "cost_center_name": "Information Technology",
            "period_start": datetime(2024, 1, 1),
            "period_end": datetime(2024, 3, 31),
            "budget_amount": 500000.00,
            "actual_amount": 125000.00,
            "committed_amount": 50000.00,
            "available_amount": 325000.00,
            "budget_variance": -375000.00,
            "budget_variance_percentage": -75.0,
            "utilization_percentage": 25.0,
        }
        mock_crud.get_cost_center_performance.return_value = performance_data

        # Make request
        response = client.get(
            "/finance/cost-centers/cc-123/performance"
            "?start_date=2024-01-01T00:00:00Z&end_date=2024-03-31T23:59:59Z"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["cost_center_id"] == "cc-123"
        assert data["utilization_percentage"] == 25.0


class TestFinancialReporting:
    """Test cases for Financial Reporting."""

    @patch("app.api.v1.finance_v31.FinancialReportCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_generate_balance_sheet_success(self, mock_user, mock_crud_class):
        """Test successful balance sheet generation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        
        balance_sheet_data = {
            "report_type": "balance_sheet",
            "organization_id": "org-123",
            "as_of_date": datetime(2024, 3, 31),
            "assets": {
                "accounts": [
                    {
                        "account_id": "acc-1",
                        "account_code": "1000",
                        "account_name": "Cash",
                        "balance": 50000.00,
                        "debit_total": 100000.00,
                        "credit_total": 50000.00,
                    }
                ],
                "total": 50000.00,
            },
            "liabilities": {
                "accounts": [
                    {
                        "account_id": "acc-2",
                        "account_code": "2000",
                        "account_name": "Accounts Payable",
                        "balance": 10000.00,
                        "debit_total": 5000.00,
                        "credit_total": 15000.00,
                    }
                ],
                "total": 10000.00,
            },
            "equity": {
                "accounts": [
                    {
                        "account_id": "acc-3",
                        "account_code": "3000",
                        "account_name": "Owner's Equity",
                        "balance": 40000.00,
                        "debit_total": 0.00,
                        "credit_total": 40000.00,
                    }
                ],
                "total": 40000.00,
            },
            "total_liabilities_equity": 50000.00,
            "balanced": True,
        }
        mock_crud.generate_balance_sheet.return_value = balance_sheet_data

        # Make request
        response = client.get(
            "/finance/reports/balance-sheet"
            "?organization_id=org-123&as_of_date=2024-03-31T00:00:00Z"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "balance_sheet"
        assert data["balanced"] is True
        assert data["assets"]["total"] == 50000.00
        assert data["total_liabilities_equity"] == 50000.00

    @patch("app.api.v1.finance_v31.FinancialReportCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_generate_income_statement_success(self, mock_user, mock_crud_class):
        """Test successful income statement generation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        
        income_statement_data = {
            "report_type": "income_statement",
            "organization_id": "org-123",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 3, 31),
            "revenue": {
                "accounts": [
                    {
                        "account_id": "acc-revenue",
                        "account_code": "4000",
                        "account_name": "Service Revenue",
                        "balance": 100000.00,
                        "debit_total": 0.00,
                        "credit_total": 100000.00,
                    }
                ],
                "total": 100000.00,
            },
            "expenses": {
                "accounts": [
                    {
                        "account_id": "acc-expense",
                        "account_code": "5000",
                        "account_name": "Operating Expenses",
                        "balance": 60000.00,
                        "debit_total": 60000.00,
                        "credit_total": 0.00,
                    }
                ],
                "total": 60000.00,
            },
            "net_income": 40000.00,
            "gross_margin": 40000.00,
            "margin_percentage": 40.0,
        }
        mock_crud.generate_income_statement.return_value = income_statement_data

        # Make request
        response = client.get(
            "/finance/reports/income-statement"
            "?organization_id=org-123&start_date=2024-01-01T00:00:00Z&end_date=2024-03-31T23:59:59Z"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "income_statement"
        assert data["net_income"] == 40000.00
        assert data["margin_percentage"] == 40.0


class TestTaxConfiguration:
    """Test cases for Tax Configuration."""

    @pytest.fixture
    def sample_tax_data(self):
        """Sample tax configuration data for testing."""
        return {
            "organization_id": "org-123",
            "tax_name": "消費税",
            "tax_code": "JPY_VAT",
            "tax_type": "vat",
            "tax_rate": 10.0,
            "effective_date": "2024-01-01T00:00:00Z",
            "applies_to_sales": True,
            "applies_to_purchases": True,
        }

    @pytest.fixture
    def sample_tax_response(self):
        """Sample tax configuration response for mocking."""
        return {
            "id": "tax-123",
            "organization_id": "org-123",
            "tax_name": "消費税",
            "tax_code": "JPY_VAT",
            "tax_type": "vat",
            "tax_rate": 10.0,
            "is_active": True,
            "created_by": "user-123",
        }

    @patch("app.api.v1.finance_v31.TaxConfigurationCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_create_tax_configuration_success(self, mock_user, mock_crud_class,
                                            sample_tax_data, sample_tax_response):
        """Test successful tax configuration creation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        mock_crud.create.return_value = Mock(**sample_tax_response)

        # Make request
        response = client.post("/finance/tax-configurations", json=sample_tax_data)

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["tax_name"] == sample_tax_data["tax_name"]
        assert data["tax_code"] == sample_tax_data["tax_code"]
        assert data["tax_rate"] == 10.0

    @patch("app.api.v1.finance_v31.TaxConfigurationCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_calculate_tax_success(self, mock_user, mock_crud_class):
        """Test successful tax calculation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        
        calculation_result = {
            "tax_code": "JPY_VAT",
            "tax_name": "消費税",
            "tax_rate": 10.0,
            "base_amount": 1000.00,
            "tax_amount": 100.00,
            "total_amount": 1100.00,
            "tax_type": "vat",
        }
        mock_crud.calculate_tax.return_value = calculation_result

        # Make request
        calculation_request = {
            "tax_code": "JPY_VAT",
            "base_amount": 1000.00,
        }
        response = client.post(
            "/finance/tax-configurations/calculate?organization_id=org-123",
            json=calculation_request
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["tax_amount"] == 100.00
        assert data["total_amount"] == 1100.00


class TestTrialBalance:
    """Test cases for Trial Balance."""

    @patch("app.api.v1.finance_v31.JournalEntryCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_get_trial_balance_success(self, mock_user, mock_crud_class):
        """Test successful trial balance generation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        mock_crud = mock_crud_class.return_value
        
        trial_balance_data = [
            {
                "account_id": "acc-1",
                "account_code": "1000",
                "account_name": "Cash",
                "account_type": "asset",
                "debit_balance": 50000.00,
                "credit_balance": 0.00,
                "total_debits": 100000.00,
                "total_credits": 50000.00,
            },
            {
                "account_id": "acc-2",
                "account_code": "4000",
                "account_name": "Revenue",
                "account_type": "revenue",
                "debit_balance": 0.00,
                "credit_balance": 50000.00,
                "total_debits": 0.00,
                "total_credits": 50000.00,
            }
        ]
        mock_crud.get_trial_balance.return_value = trial_balance_data

        # Make request
        response = client.get(
            "/finance/trial-balance"
            "?organization_id=org-123&as_of_date=2024-03-31T00:00:00Z"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["organization_id"] == "org-123"
        assert len(data["accounts"]) == 2
        assert data["total_debits"] == 50000.00
        assert data["total_credits"] == 50000.00
        assert data["is_balanced"] is True


class TestFinancialAnalytics:
    """Test cases for Financial Analytics Dashboard."""

    @patch("app.api.v1.finance_v31.JournalEntryCRUD")
    @patch("app.api.v1.finance_v31.FinancialReportCRUD")
    @patch("app.api.v1.finance_v31.BudgetCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_get_financial_dashboard_success(self, mock_user, mock_budget_crud, mock_report_crud, mock_journal_crud):
        """Test successful financial dashboard generation."""
        # Setup mocks
        mock_user.return_value = {"sub": "user-123"}
        
        # Mock balance sheet
        balance_sheet = {
            "assets": {"total": 100000.00},
            "liabilities": {"total": 30000.00},
            "equity": {"total": 70000.00},
            "balanced": True,
        }
        mock_report_crud.return_value.generate_balance_sheet.return_value = balance_sheet
        
        # Mock income statement
        income_statement = {
            "revenue": {"total": 80000.00},
            "expenses": {"total": 50000.00},
            "net_income": 30000.00,
            "margin_percentage": 37.5,
        }
        mock_report_crud.return_value.generate_income_statement.return_value = income_statement
        
        # Mock trial balance
        trial_balance = [
            {"debit_balance": 60000.00, "credit_balance": 0.00},
            {"debit_balance": 0.00, "credit_balance": 60000.00},
        ]
        mock_journal_crud.return_value.get_trial_balance.return_value = trial_balance

        # Make request
        response = client.get(
            "/finance/analytics/dashboard"
            "?organization_id=org-123&period_start=2024-01-01T00:00:00Z&period_end=2024-03-31T23:59:59Z"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["organization_id"] == "org-123"
        assert "balance_sheet_summary" in data
        assert "income_statement_summary" in data
        assert "trial_balance_summary" in data
        assert "key_metrics" in data
        
        # Check balance sheet summary
        bs_summary = data["balance_sheet_summary"]
        assert bs_summary["total_assets"] == 100000.00
        assert bs_summary["is_balanced"] is True
        
        # Check income statement summary
        is_summary = data["income_statement_summary"]
        assert is_summary["net_income"] == 30000.00
        assert is_summary["margin_percentage"] == 37.5


class TestFinanceIntegration:
    """Integration tests for Finance API workflows."""

    @patch("app.api.v1.finance_v31.AccountCRUD")
    @patch("app.api.v1.finance_v31.JournalEntryCRUD")
    @patch("app.api.v1.finance_v31.get_current_user")
    def test_complete_transaction_workflow(self, mock_user, mock_journal_crud, mock_account_crud):
        """Test complete transaction workflow from account creation to posting."""
        # Setup user
        mock_user.return_value = {"sub": "user-123"}
        
        # Test data
        account_data = {
            "organization_id": "org-123",
            "account_name": "Test Cash Account",
            "account_type": "asset",
            "normal_balance": "debit",
        }
        
        entry_data = {
            "organization_id": "org-123",
            "transaction_date": "2024-01-15T10:00:00Z",
            "description": "Test transaction",
            "lines": [
                {"account_id": "acc-1", "debit_amount": 100.00, "credit_amount": 0},
                {"account_id": "acc-2", "debit_amount": 0, "credit_amount": 100.00},
            ],
        }

        # Mock account creation
        mock_account = Mock(id="acc-1", account_name="Test Cash Account")
        mock_account_crud.return_value.create_account.return_value = mock_account

        # Mock journal entry creation and posting
        mock_entry = Mock(id="je-1", is_posted=False)
        mock_posted_entry = Mock(id="je-1", is_posted=True)
        mock_journal_crud.return_value.create_journal_entry.return_value = mock_entry
        mock_journal_crud.return_value.post_journal_entry.return_value = mock_posted_entry

        # Step 1: Create account
        account_response = client.post("/finance/accounts", json=account_data)
        assert account_response.status_code == 201

        # Step 2: Create journal entry
        entry_response = client.post("/finance/journal-entries", json=entry_data)
        assert entry_response.status_code == 201

        # Step 3: Post journal entry
        post_response = client.post("/finance/journal-entries/post", json={"journal_entry_id": "je-1"})
        assert post_response.status_code == 200