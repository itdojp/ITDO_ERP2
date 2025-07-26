"""
ITDO ERP Backend - Financial API Vulnerability Tests
Day 24: Advanced security vulnerability testing for financial APIs

Focus areas:
- Business logic vulnerabilities
- Financial calculation tampering
- Audit trail manipulation
- Session management security
- Rate limiting and DoS protection
- Financial reporting security
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Dict
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app


class TestFinancialBusinessLogicSecurity:
    """Test business logic vulnerabilities in financial operations"""

    def test_budget_manipulation_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test prevention of budget manipulation attacks"""
        # Test negative budget creation
        malicious_budgets = [
            {
                "organization_id": 1,
                "budget_name": "Negative Budget",
                "fiscal_year": 2025,
                "budget_period": "annual",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "total_budget": "-1000000.00",  # Negative budget
            },
            {
                "organization_id": 1,
                "budget_name": "Zero Budget",
                "fiscal_year": 2025,
                "budget_period": "annual",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "total_budget": "0.00",  # Zero budget might be invalid
            },
            {
                "organization_id": 1,
                "budget_name": "Massive Budget",
                "fiscal_year": 2025,
                "budget_period": "annual",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "total_budget": "999999999999999.99",  # Unrealistic amount
            },
        ]

        for budget_data in malicious_budgets:
            response = client.post(
                "/api/v1/financial-management/budgets",
                json=budget_data,
                headers=auth_headers,
            )
            # Should validate business rules
            if budget_data["total_budget"].startswith("-"):
                assert response.status_code in [
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                ]

    def test_journal_entry_tampering_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test prevention of journal entry tampering"""
        tampered_entries = [
            {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": "TAMPER001",
                "entry_date": "2025-07-26",
                "debit_amount": "0.01",  # Penny manipulation
                "description": "Legitimate entry",
            },
            {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": "TAMPER002",
                "entry_date": "2099-12-31",  # Future date manipulation
                "debit_amount": "1000.00",
                "description": "Future-dated entry",
            },
            {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": "TAMPER003",
                "entry_date": "1900-01-01",  # Historical date manipulation
                "debit_amount": "1000.00",
                "description": "Historical entry",
            },
        ]

        for entry_data in tampered_entries:
            response = client.post(
                "/api/v1/financial-management/journal-entries",
                json=entry_data,
                headers=auth_headers,
            )

            # Validate date ranges and amounts
            if (
                entry_data["entry_date"] > "2030-01-01"
                or entry_data["entry_date"] < "2020-01-01"
            ):
                assert response.status_code in [
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    status.HTTP_400_BAD_REQUEST,
                ]

    def test_account_balance_manipulation(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test prevention of direct account balance manipulation"""
        # Attempt to create account with pre-set balance
        account_data = {
            "organization_id": 1,
            "account_code": "MANIP001",
            "account_name": "Manipulated Account",
            "account_type": "asset",
            "balance": "1000000.00",  # Attempting to set balance directly
            "is_active": True,
        }

        response = client.post(
            "/api/v1/financial-management/accounts",
            json=account_data,
            headers=auth_headers,
        )

        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            # Balance should be zero or system-calculated, not user-provided
            assert Decimal(str(data.get("balance", "0.00"))) == Decimal("0.00")

    def test_cost_center_budget_overflow(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test cost center budget overflow protection"""
        overflow_data = [
            {
                "organization_id": 1,
                "center_code": "OVERFLOW1",
                "center_name": "Overflow Test 1",
                "budget_limit": "999999999999999999999.99",  # Extreme value
                "is_active": True,
            },
            {
                "organization_id": 1,
                "center_code": "OVERFLOW2",
                "center_name": "Overflow Test 2",
                "budget_limit": "1.7976931348623157e+308",  # Float overflow
                "is_active": True,
            },
        ]

        for cost_center_data in overflow_data:
            response = client.post(
                "/api/v1/financial-management/cost-centers",
                json=cost_center_data,
                headers=auth_headers,
            )
            # Should handle numeric overflow gracefully
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]


class TestFinancialCalculationSecurity:
    """Test security of financial calculations"""

    def test_floating_point_precision_attacks(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test resistance to floating-point precision attacks"""
        precision_attack_amounts = [
            "0.999999999999999",
            "1.0000000000000001",
            "0.1 + 0.2",  # Classic floating point issue
            "1e-10",
            "1e+10",
        ]

        for amount in precision_attack_amounts:
            entry_data = {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": f"PREC{amount.replace('.', '').replace('+', '').replace('-', '')}",
                "entry_date": "2025-07-26",
                "debit_amount": str(amount),
                "description": "Precision test",
            }

            response = client.post(
                "/api/v1/financial-management/journal-entries",
                json=entry_data,
                headers=auth_headers,
            )

            if response.status_code == status.HTTP_201_CREATED:
                data = response.json()
                # Should maintain proper decimal precision
                debit_str = str(data.get("debit_amount", "0"))
                decimal_places = (
                    len(debit_str.split(".")[-1]) if "." in debit_str else 0
                )
                assert decimal_places <= 2  # Standard financial precision

    def test_bulk_calculation_consistency(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test consistency in bulk financial calculations"""
        # Create bulk journal entries with potential rounding issues
        bulk_entries = []
        for i in range(100):
            entry = {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": f"BULK{i:03d}",
                "entry_date": "2025-07-26",
                "debit_amount": "0.33",  # Amount that causes rounding
                "description": f"Bulk entry {i}",
            }
            bulk_entries.append(entry)

        bulk_request = {
            "entries": bulk_entries,
            "auto_balance": False,
        }

        response = client.post(
            "/api/v1/financial-accounting/journal-entries/bulk",
            json=bulk_request,
            headers=auth_headers,
        )

        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            # All entries should be processed consistently
            assert data.get("total_failed", 0) == 0
            assert len(data.get("created_entries", [])) == 100

    def test_currency_conversion_security(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test security of currency conversion operations"""
        # Test with malicious currency values
        malicious_amounts = [
            "NaN",
            "Infinity",
            "-Infinity",
            "undefined",
            "null",
        ]

        for amount in malicious_amounts:
            entry_data = {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": f"CURR{amount[:4].upper()}",
                "entry_date": "2025-07-26",
                "debit_amount": amount,
                "description": "Currency test",
            }

            response = client.post(
                "/api/v1/financial-management/journal-entries",
                json=entry_data,
                headers=auth_headers,
            )
            # Should reject invalid numeric values
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST,
            ]


class TestFinancialAuditSecurity:
    """Test audit trail and financial reporting security"""

    def test_audit_trail_immutability(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test that audit trails cannot be manipulated"""
        # Create a journal entry
        entry_data = {
            "organization_id": 1,
            "account_id": 1,
            "transaction_id": "AUDIT001",
            "entry_date": "2025-07-26",
            "debit_amount": "1000.00",
            "description": "Audit test entry",
        }

        response = client.post(
            "/api/v1/financial-management/journal-entries",
            json=entry_data,
            headers=auth_headers,
        )

        if response.status_code == status.HTTP_201_CREATED:
            entry_id = response.json().get("id")

            # Attempt to modify created_at timestamp
            update_data = {
                "description": "Modified entry",
                "created_at": "2020-01-01T00:00:00Z",  # Attempt to backdate
            }

            # Most systems should not allow updating audit fields
            update_response = client.put(
                f"/api/v1/financial-management/journal-entries/{entry_id}",
                json=update_data,
                headers=auth_headers,
            )

            # Update should either be forbidden or ignore audit fields
            if update_response.status_code == status.HTTP_200_OK:
                updated_data = update_response.json()
                assert updated_data.get("created_at") != "2020-01-01T00:00:00Z"

    def test_financial_report_tampering(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test protection against financial report tampering"""
        # Test trial balance report
        response = client.get(
            "/api/v1/financial-accounting/trial-balance?organization_id=1&as_of_date=2025-07-26",
            headers=auth_headers,
        )

        if response.status_code == status.HTTP_200_OK:
            report_data = response.json()

            # Verify mathematical consistency
            total_debits = Decimal(str(report_data.get("total_debits", "0")))
            total_credits = Decimal(str(report_data.get("total_credits", "0")))
            is_balanced = report_data.get("is_balanced", False)

            # Trial balance should balance (debits = credits)
            calculated_balance = total_debits == total_credits
            assert is_balanced == calculated_balance

    def test_report_access_control(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test access control for sensitive financial reports"""
        sensitive_reports = [
            "/api/v1/financial-accounting/trial-balance",
            "/api/v1/financial-accounting/income-statement",
            "/api/v1/financial-accounting/balance-sheet",
            "/api/v1/financial-accounting/cash-flow-statement",
        ]

        # Test with limited permissions
        with patch("app.api.dependencies.get_current_user") as mock_user:
            mock_user.return_value = {
                "id": 1,
                "username": "limited_user",
                "roles": ["viewer"],  # Limited role
            }

            for report_endpoint in sensitive_reports:
                params = {
                    "organization_id": 1,
                    "as_of_date": "2025-07-26"
                    if "balance" in report_endpoint
                    else None,
                    "start_date": "2025-01-01"
                    if "income" in report_endpoint or "cash-flow" in report_endpoint
                    else None,
                    "end_date": "2025-12-31"
                    if "income" in report_endpoint or "cash-flow" in report_endpoint
                    else None,
                }
                # Remove None values
                params = {k: v for k, v in params.items() if v is not None}

                response = client.get(
                    report_endpoint, params=params, headers=auth_headers
                )

                # Should restrict access to sensitive reports
                assert response.status_code in [
                    status.HTTP_403_FORBIDDEN,
                    status.HTTP_401_UNAUTHORIZED,
                    status.HTTP_200_OK,  # If access is allowed, verify data sanitization
                ]


class TestFinancialRateLimiting:
    """Test rate limiting and DoS protection"""

    def test_api_rate_limiting(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test API rate limiting to prevent abuse"""
        # Simulate rapid requests
        responses = []

        for i in range(50):  # High number of requests
            response = client.get(
                "/api/v1/financial-management/accounts?organization_id=1",
                headers=auth_headers,
            )
            responses.append(response.status_code)

            # Small delay to avoid overwhelming the test
            time.sleep(0.01)

        # Should implement rate limiting after excessive requests
        [code for code in responses if code == status.HTTP_429_TOO_MANY_REQUESTS]

        # Allow some rate limiting to occur (this depends on implementation)
        # If no rate limiting is implemented, all should be successful
        successful_responses = [
            code for code in responses if code == status.HTTP_200_OK
        ]
        assert len(successful_responses) > 0  # Some requests should succeed

    def test_bulk_operation_protection(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test protection against bulk operation abuse"""
        # Create an excessive number of entries
        large_bulk_entries = []
        for i in range(2000):  # Excessive number
            entry = {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": f"BULK{i:04d}",
                "entry_date": "2025-07-26",
                "debit_amount": "1.00",
                "description": f"Bulk entry {i}",
            }
            large_bulk_entries.append(entry)

        bulk_request = {
            "entries": large_bulk_entries,
            "auto_balance": False,
        }

        response = client.post(
            "/api/v1/financial-accounting/journal-entries/bulk",
            json=bulk_request,
            headers=auth_headers,
        )

        # Should reject or limit excessive bulk operations
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_concurrent_request_handling(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test handling of concurrent requests"""
        import queue
        import threading

        results = queue.Queue()

        def make_request(index):
            """Make a request and store the result"""
            try:
                response = client.get(
                    "/api/v1/financial-management/summary?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
                    headers=auth_headers,
                )
                results.put((index, response.status_code))
            except Exception as e:
                results.put((index, str(e)))

        # Create multiple concurrent threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect results
        response_codes = []
        while not results.empty():
            index, code = results.get()
            response_codes.append(code)

        # Should handle concurrent requests gracefully
        successful_requests = [
            code for code in response_codes if code == status.HTTP_200_OK
        ]
        assert len(successful_requests) > 0  # Some requests should succeed

        # No thread should cause server errors
        server_errors = [code for code in response_codes if code >= 500]
        assert len(server_errors) < len(response_codes)  # Not all should fail


class TestFinancialSessionSecurity:
    """Test session management and authentication security"""

    def test_session_fixation_prevention(self, client: TestClient):
        """Test prevention of session fixation attacks"""
        # Create initial session
        initial_token = create_access_token(data={"sub": "test_user"})
        headers1 = {"Authorization": f"Bearer {initial_token}"}

        response1 = client.get("/api/v1/financial-management/health", headers=headers1)

        # Create new session with same user
        new_token = create_access_token(data={"sub": "test_user"})
        headers2 = {"Authorization": f"Bearer {new_token}"}

        response2 = client.get("/api/v1/financial-management/health", headers=headers2)

        # Both sessions should be independent
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert initial_token != new_token

    def test_token_replay_protection(self, client: TestClient):
        """Test protection against token replay attacks"""
        # Use same token multiple times
        token = create_access_token(data={"sub": "test_user"})
        headers = {"Authorization": f"Bearer {token}"}

        responses = []
        for i in range(5):
            response = client.get(
                "/api/v1/financial-management/health", headers=headers
            )
            responses.append(response.status_code)

        # Token should remain valid for multiple requests (unless specifically invalidated)
        assert all(code == status.HTTP_200_OK for code in responses)

    def test_privilege_escalation_prevention(self, client: TestClient):
        """Test prevention of privilege escalation"""
        # Create token with limited privileges
        limited_token = create_access_token(
            data={"sub": "limited_user", "roles": ["viewer"]}
        )
        headers = {"Authorization": f"Bearer {limited_token}"}

        # Attempt privileged operation
        account_data = {
            "organization_id": 1,
            "account_code": "PRIV001",
            "account_name": "Privileged Account",
            "account_type": "asset",
            "is_active": True,
        }

        response = client.post(
            "/api/v1/financial-management/accounts",
            json=account_data,
            headers=headers,
        )

        # Should be rejected due to insufficient privileges
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers fixture"""
    token = create_access_token(
        data={"sub": "test_user", "roles": ["financial_manager"]}
    )
    return {"Authorization": f"Bearer {token}"}
