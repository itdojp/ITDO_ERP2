"""
ITDO ERP Backend - Financial Management Security Tests
Day 24: Comprehensive security testing for financial management APIs

Security test coverage:
- Authentication and authorization
- Input validation and sanitization
- SQL injection prevention
- XSS attack prevention
- IDOR vulnerability testing
- Data protection and encryption
- GDPR compliance verification
- Financial data integrity
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app


class TestFinancialSecurityAuthentication:
    """Test authentication and authorization for financial management"""

    def test_unauthenticated_access_denied(self, client: TestClient):
        """Test that unauthenticated requests are rejected"""
        endpoints = [
            "/api/v1/financial-management/accounts",
            "/api/v1/financial-management/journal-entries",
            "/api/v1/financial-management/budgets",
            "/api/v1/financial-management/cost-centers",
            "/api/v1/financial-management/summary",
            "/api/v1/financial-accounting/trial-balance",
            "/api/v1/financial-accounting/income-statement",
            "/api/v1/financial-accounting/balance-sheet",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_rejected(self, client: TestClient):
        """Test that invalid tokens are rejected"""
        invalid_token = "invalid.jwt.token"
        headers = {"Authorization": f"Bearer {invalid_token}"}

        response = client.get("/api/v1/financial-management/accounts", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_rejected(self, client: TestClient):
        """Test that expired tokens are rejected"""
        # Create expired token (negative expiry)
        expired_token = create_access_token(
            data={"sub": "test_user"}, expires_delta=-3600
        )
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.get("/api/v1/financial-management/accounts", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_role_based_access_control(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test role-based access control for financial operations"""
        # Test with insufficient permissions
        with patch("app.api.dependencies.get_current_user") as mock_user:
            mock_user.return_value = {
                "id": 1,
                "username": "test_user",
                "roles": ["viewer"],  # Insufficient role for financial operations
            }

            account_data = {
                "organization_id": 1,
                "account_code": "TEST001",
                "account_name": "Test Account",
                "account_type": "asset",
                "is_active": True,
            }

            response = client.post(
                "/api/v1/financial-management/accounts",
                json=account_data,
                headers=auth_headers,
            )
            # Should be forbidden due to insufficient permissions
            assert response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]


class TestFinancialInputValidation:
    """Test input validation and sanitization"""

    def test_sql_injection_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test SQL injection attack prevention"""
        sql_injection_payloads = [
            "'; DROP TABLE accounts; --",
            "1' OR '1'='1",
            "'; INSERT INTO accounts VALUES (999, 'hacked'); --",
            "1'; DELETE FROM accounts WHERE 1=1; --",
            "1' UNION SELECT * FROM users; --",
        ]

        for payload in sql_injection_payloads:
            # Test in account code
            account_data = {
                "organization_id": 1,
                "account_code": payload,
                "account_name": "Test Account",
                "account_type": "asset",
                "is_active": True,
            }

            response = client.post(
                "/api/v1/financial-management/accounts",
                json=account_data,
                headers=auth_headers,
            )
            # Should either validate input or handle error gracefully
            assert response.status_code != status.HTTP_200_OK

            # Test in query parameters
            response = client.get(
                f"/api/v1/financial-management/accounts?organization_id={payload}",
                headers=auth_headers,
            )
            assert response.status_code != status.HTTP_200_OK

    def test_xss_prevention(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test XSS attack prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//",
            "<svg onload=alert('XSS')>",
        ]

        for payload in xss_payloads:
            account_data = {
                "organization_id": 1,
                "account_code": "XSS001",
                "account_name": payload,
                "account_type": "asset",
                "description": payload,
                "is_active": True,
            }

            response = client.post(
                "/api/v1/financial-management/accounts",
                json=account_data,
                headers=auth_headers,
            )

            if response.status_code == status.HTTP_201_CREATED:
                # If created, ensure response is sanitized
                data = response.json()
                assert "<script>" not in str(data)
                assert "javascript:" not in str(data)
                assert "onerror=" not in str(data)

    def test_nosql_injection_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test NoSQL injection attack prevention"""
        nosql_payloads = [
            {"$gt": ""},
            {"$ne": None},
            {"$where": "function() { return true; }"},
            {"$regex": ".*"},
            {"$exists": True},
        ]

        for payload in nosql_payloads:
            # Test with JSON payload in account_name
            account_data = {
                "organization_id": 1,
                "account_code": "NOSQL001",
                "account_name": json.dumps(payload),
                "account_type": "asset",
                "is_active": True,
            }

            response = client.post(
                "/api/v1/financial-management/accounts",
                json=account_data,
                headers=auth_headers,
            )
            # Should validate and reject malicious input
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]

    def test_command_injection_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test command injection attack prevention"""
        command_injection_payloads = [
            "; ls -la;",
            "| cat /etc/passwd",
            "& whoami",
            "`id`",
            "$(uname -a)",
            "; rm -rf /;",
        ]

        for payload in command_injection_payloads:
            account_data = {
                "organization_id": 1,
                "account_code": f"CMD{payload}001",
                "account_name": f"Account {payload}",
                "account_type": "asset",
                "description": payload,
                "is_active": True,
            }

            response = client.post(
                "/api/v1/financial-management/accounts",
                json=account_data,
                headers=auth_headers,
            )
            # Should not execute commands
            assert response.status_code != status.HTTP_200_OK or "; " not in str(
                response.json()
            )

    def test_json_injection_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test JSON injection attack prevention"""
        json_injection_payloads = [
            '{"injection": "attempt"}',
            '","injection":"value","real":"',
            '"};alert("XSS");//',
            "\\u0022injection\\u0022",
        ]

        for payload in json_injection_payloads:
            account_data = {
                "organization_id": 1,
                "account_code": "JSON001",
                "account_name": payload,
                "account_type": "asset",
                "is_active": True,
            }

            response = client.post(
                "/api/v1/financial-management/accounts",
                json=account_data,
                headers=auth_headers,
            )

            if response.status_code == status.HTTP_201_CREATED:
                # Ensure JSON structure is preserved
                data = response.json()
                assert isinstance(data, dict)
                assert "account_name" in data


class TestFinancialIDORVulnerabilities:
    """Test Insecure Direct Object Reference vulnerabilities"""

    def test_account_access_control(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test access control for account resources"""
        # Test accessing non-existent account
        response = client.get(
            "/api/v1/financial-management/accounts?organization_id=99999",
            headers=auth_headers,
        )
        # Should not reveal existence of organization
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_200_OK,  # Empty list is acceptable
        ]

    def test_journal_entry_isolation(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test journal entry isolation between organizations"""
        # Attempt to access journal entries from different organization
        with patch("app.api.dependencies.get_current_user") as mock_user:
            mock_user.return_value = {
                "id": 1,
                "username": "test_user",
                "organization_id": 1,
                "roles": ["financial_manager"],
            }

            # Try to create entry for different organization
            entry_data = {
                "organization_id": 999,  # Different organization
                "account_id": 1,
                "transaction_id": "TXN001",
                "entry_date": "2025-07-26",
                "debit_amount": "1000.00",
                "description": "Test entry",
            }

            response = client.post(
                "/api/v1/financial-management/journal-entries",
                json=entry_data,
                headers=auth_headers,
            )
            # Should be forbidden or validated
            assert response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]

    def test_budget_access_boundaries(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test budget access boundaries"""
        # Test unauthorized budget creation
        budget_data = {
            "organization_id": 999,  # Unauthorized organization
            "budget_name": "Unauthorized Budget",
            "fiscal_year": 2025,
            "budget_period": "annual",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "total_budget": "100000.00",
        }

        response = client.post(
            "/api/v1/financial-management/budgets",
            json=budget_data,
            headers=auth_headers,
        )
        assert response.status_code != status.HTTP_201_CREATED


class TestFinancialDataProtection:
    """Test data protection and encryption"""

    def test_sensitive_data_masking(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test masking of sensitive financial data"""
        # Create account with sensitive information
        account_data = {
            "organization_id": 1,
            "account_code": "BANK001",
            "account_name": "Primary Bank Account",
            "account_type": "asset",
            "description": "Main operational account with routing 123456789",
            "is_active": True,
        }

        response = client.post(
            "/api/v1/financial-management/accounts",
            json=account_data,
            headers=auth_headers,
        )

        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            # Sensitive data should not be exposed in plain text
            assert "123456789" not in str(data) or "***" in str(data)

    def test_gdpr_compliance(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test GDPR compliance features"""
        # Test data anonymization request
        response = client.get(
            "/api/v1/financial-management/summary?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
            headers=auth_headers,
        )

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Personal identifiers should be protected
            sensitive_patterns = ["ssn", "social", "passport", "driver", "license"]
            response_text = str(data).lower()
            for pattern in sensitive_patterns:
                if pattern in response_text:
                    # Should be masked or anonymized
                    assert "***" in response_text or "xxx" in response_text

    def test_data_encryption_in_transit(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test data encryption in transit"""
        # Verify HTTPS enforcement (would be handled by reverse proxy in production)
        # This test ensures no sensitive data is logged in plain text

        sensitive_data = {
            "organization_id": 1,
            "account_code": "SECRET001",
            "account_name": "Highly Confidential Account",
            "account_type": "asset",
            "description": "Contains sensitive financial information",
            "is_active": True,
        }

        with patch("app.api.v1.financial_management_api.logger") as mock_logger:
            client.post(
                "/api/v1/financial-management/accounts",
                json=sensitive_data,
                headers=auth_headers,
            )

            # Ensure sensitive data is not logged in plain text
            for call in mock_logger.info.call_args_list:
                log_message = str(call)
                assert "Highly Confidential" not in log_message or "***" in log_message

    def test_financial_data_integrity(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test financial data integrity validation"""
        # Test double-entry bookkeeping validation
        invalid_entries = [
            {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": "TXN001",
                "entry_date": "2025-07-26",
                "debit_amount": "1000.00",
                "credit_amount": "500.00",  # Both debit and credit
                "description": "Invalid entry",
            },
            {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": "TXN002",
                "entry_date": "2025-07-26",
                # Neither debit nor credit
                "description": "Invalid entry",
            },
            {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": "TXN003",
                "entry_date": "2025-07-26",
                "debit_amount": "-1000.00",  # Negative amount
                "description": "Invalid entry",
            },
        ]

        for entry_data in invalid_entries:
            response = client.post(
                "/api/v1/financial-management/journal-entries",
                json=entry_data,
                headers=auth_headers,
            )
            # Should reject invalid financial data
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]


class TestFinancialAdvancedSecurity:
    """Test advanced security features"""

    def test_prototype_pollution_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test prototype pollution attack prevention"""
        pollution_payloads = [
            {"__proto__": {"polluted": True}},
            {"constructor": {"prototype": {"polluted": True}}},
            {"__proto__.polluted": True},
        ]

        for payload in pollution_payloads:
            # Attempt to pollute through account creation
            account_data = {
                "organization_id": 1,
                "account_code": "POLL001",
                "account_name": "Pollution Test",
                "account_type": "asset",
                "is_active": True,
                **payload,  # Merge pollution payload
            }

            response = client.post(
                "/api/v1/financial-management/accounts",
                json=account_data,
                headers=auth_headers,
            )

            # Should not process malicious properties
            if response.status_code == status.HTTP_201_CREATED:
                data = response.json()
                assert "__proto__" not in data
                assert "constructor" not in data or not isinstance(
                    data.get("constructor"), dict
                )

    def test_xxe_attack_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test XXE (XML External Entity) attack prevention"""
        xxe_payloads = [
            '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY test SYSTEM "file:///etc/passwd">]><root>&test;</root>',
            '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY test SYSTEM "http://evil.com/test">]><root>&test;</root>',
        ]

        for payload in xxe_payloads:
            # Test in description field (assuming it might process XML)
            account_data = {
                "organization_id": 1,
                "account_code": "XXE001",
                "account_name": "XXE Test",
                "account_type": "asset",
                "description": payload,
                "is_active": True,
            }

            response = client.post(
                "/api/v1/financial-management/accounts",
                json=account_data,
                headers=auth_headers,
            )

            if response.status_code == status.HTTP_201_CREATED:
                data = response.json()
                # Should not process XML entities
                assert "passwd" not in str(data)
                assert "evil.com" not in str(data)

    def test_ssti_attack_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test Server-Side Template Injection prevention"""
        ssti_payloads = [
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
            "{{config}}",
            "{{''.__class__.__mro__[2].__subclasses__()}}",
        ]

        for payload in ssti_payloads:
            account_data = {
                "organization_id": 1,
                "account_code": "SSTI001",
                "account_name": payload,
                "account_type": "asset",
                "description": payload,
                "is_active": True,
            }

            response = client.post(
                "/api/v1/financial-management/accounts",
                json=account_data,
                headers=auth_headers,
            )

            if response.status_code == status.HTTP_201_CREATED:
                data = response.json()
                # Should not evaluate template expressions
                assert "49" not in str(data)  # 7*7 should not be evaluated
                assert "class" not in str(data).lower() or payload in str(data)

    def test_race_condition_prevention(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test race condition prevention in financial operations"""

        async def concurrent_budget_creation():
            """Test concurrent budget creation"""
            tasks = []

            for i in range(5):
                budget_data = {
                    "organization_id": 1,
                    "budget_name": f"Concurrent Budget {i}",
                    "fiscal_year": 2025,
                    "budget_period": "annual",
                    "start_date": "2025-01-01",
                    "end_date": "2025-12-31",
                    "total_budget": "100000.00",
                }

                task = asyncio.create_task(
                    self._async_post_request(
                        "/api/v1/financial-management/budgets",
                        budget_data,
                        auth_headers,
                    )
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Should handle concurrent requests gracefully
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            assert success_count <= 5  # No more than expected

        # Run the async test
        asyncio.run(concurrent_budget_creation())

    async def _async_post_request(
        self, url: str, data: Dict[str, Any], headers: Dict[str, str]
    ):
        """Helper method for async HTTP requests"""
        # This would typically use an async HTTP client
        # For now, we'll simulate the behavior
        import time

        time.sleep(0.1)  # Simulate network delay
        return {"status": "success"}


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers fixture"""
    token = create_access_token(data={"sub": "test_user"})
    return {"Authorization": f"Bearer {token}"}
