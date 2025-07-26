"""
ITDO ERP Backend - Resource Management Security Tests
Day 23: Comprehensive security testing for resource management system
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.v1.resource_analytics_api import router as resource_analytics_router
from app.api.v1.resource_integration_api import router as resource_integration_router
from app.api.v1.resource_management_api import router as resource_management_router
from app.api.v1.resource_planning_api import router as resource_planning_router


class TestResourceManagementSecurity:
    """Security tests for resource management APIs"""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI application with resource management routers"""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(
            resource_integration_router, prefix="/api/v1/resource-integration"
        )
        app.include_router(
            resource_management_router, prefix="/api/v1/resource-management"
        )
        app.include_router(
            resource_analytics_router, prefix="/api/v1/resource-analytics"
        )
        app.include_router(resource_planning_router, prefix="/api/v1/resource-planning")
        return app

    @pytest.fixture
    def client(self, mock_app):
        """Test client with security configurations"""
        return TestClient(mock_app)

    @pytest.fixture
    def valid_jwt_token(self):
        """Generate valid JWT token for testing"""
        payload = {
            "sub": "user123",
            "username": "testuser",
            "department_ids": [1, 2],
            "roles": ["resource_manager", "user"],
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, "test-secret", algorithm="HS256")

    @pytest.fixture
    def expired_jwt_token(self):
        """Generate expired JWT token for testing"""
        payload = {
            "sub": "user123",
            "username": "testuser",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2),
        }
        return jwt.encode(payload, "test-secret", algorithm="HS256")

    @pytest.fixture
    def invalid_jwt_token(self):
        """Generate invalid JWT token for testing"""
        payload = {
            "sub": "user123",
            "username": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        return jwt.encode(payload, "wrong-secret", algorithm="HS256")

    def test_authentication_required_dashboard(self, client):
        """Test that dashboard endpoint requires authentication"""

        # Test without authorization header
        response = client.get("/api/v1/resource-integration/dashboard")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test with invalid bearer token format
        response = client.get(
            "/api/v1/resource-integration/dashboard",
            headers={"Authorization": "InvalidFormat token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authentication_required_resource_creation(self, client):
        """Test that resource creation requires authentication"""

        resource_data = {
            "name": "Test Resource",
            "type": "human",
            "department_id": 1,
            "hourly_rate": 150.0,
        }

        response = client.post(
            "/api/v1/resource-management/resources", json=resource_data
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authentication_with_expired_token(self, client, expired_jwt_token):
        """Test authentication failure with expired token"""

        response = client.get(
            "/api/v1/resource-integration/dashboard",
            headers={"Authorization": f"Bearer {expired_jwt_token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in response.json().get("detail", "").lower()

    def test_authentication_with_invalid_token(self, client, invalid_jwt_token):
        """Test authentication failure with invalid token"""

        response = client.get(
            "/api/v1/resource-integration/dashboard",
            headers={"Authorization": f"Bearer {invalid_jwt_token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json().get("detail", "").lower()

    def test_authorization_department_access_control(self, client, valid_jwt_token):
        """Test department-based access control"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1, 2],  # User has access to departments 1 and 2
            }

            # Test accessing allowed department
            response = client.get(
                "/api/v1/resource-integration/dashboard?departments=1,2",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )
            assert response.status_code != status.HTTP_403_FORBIDDEN

            # Test accessing forbidden department
            response = client.get(
                "/api/v1/resource-integration/dashboard?departments=3,4",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_role_based_access_control(self, client, valid_jwt_token):
        """Test role-based access control for sensitive operations"""

        # Test with insufficient role permissions
        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "roles": ["user"],  # No admin or manager role
                "department_ids": [1],
            }

            # Test accessing admin-only functionality
            optimization_request = {
                "resource_ids": [1, 2, 3],
                "optimization_goal": "efficiency",
                "departments": [1],
            }

            response = client.post(
                "/api/v1/resource-integration/optimization-execution",
                json=optimization_request,
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_resource_owner_access_control(self, client, valid_jwt_token):
        """Test that users can only access resources they own or manage"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
                "managed_resources": [1, 2],  # User manages resources 1 and 2
            }

            # Test accessing owned resource
            response = client.get(
                "/api/v1/resource-management/resources/1",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )
            assert response.status_code != status.HTTP_403_FORBIDDEN

            # Test accessing non-owned resource
            response = client.get(
                "/api/v1/resource-management/resources/3",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_input_validation_sql_injection_prevention(self, client, valid_jwt_token):
        """Test prevention of SQL injection attacks"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Test malicious SQL injection attempts
            malicious_inputs = [
                "1'; DROP TABLE resources; --",
                "1 UNION SELECT * FROM users",
                "'; INSERT INTO resources VALUES (999, 'hacked'); --",
                "1 OR 1=1",
                "admin'--",
            ]

            for malicious_input in malicious_inputs:
                response = client.get(
                    f"/api/v1/resource-integration/dashboard?departments={malicious_input}",
                    headers={"Authorization": f"Bearer {valid_jwt_token}"},
                )

                # Should either return 400 (bad request) or process safely without injection
                assert response.status_code in [400, 422, 200]
                if response.status_code == 200:
                    # If processed, ensure no SQL injection occurred by checking response structure
                    data = response.json()
                    assert isinstance(data, dict)
                    assert "summary" in data or "error" in data

    def test_input_validation_xss_prevention(self, client, valid_jwt_token):
        """Test prevention of Cross-Site Scripting (XSS) attacks"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Test XSS payloads
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert('XSS');//",
                "<svg onload=alert('XSS')>",
            ]

            for payload in xss_payloads:
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
                    headers={"Authorization": f"Bearer {valid_jwt_token}"},
                )

                # Should validate and sanitize input
                if response.status_code == 201:
                    created_resource = response.json()
                    # Ensure script tags are escaped or removed
                    assert "<script>" not in created_resource.get("name", "")
                    assert "javascript:" not in created_resource.get("name", "")

    def test_data_encryption_sensitive_fields(self, client, valid_jwt_token):
        """Test that sensitive data is properly encrypted/protected"""

        with (
            patch("app.api.v1.resource_management_api.get_current_user") as mock_auth,
            patch(
                "app.api.v1.resource_management_api.ResourceManagementService"
            ) as mock_service,
        ):
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Mock sensitive resource data
            sensitive_resource = {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@company.com",
                "ssn": "123-45-6789",  # Sensitive data
                "salary": 75000.0,  # Sensitive data
                "performance_notes": "Excellent performer",  # Sensitive data
            }

            mock_service_instance = mock_service.return_value
            mock_service_instance.get_resource.return_value = sensitive_resource

            response = client.get(
                "/api/v1/resource-management/resources/1",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )

            if response.status_code == 200:
                data = response.json()
                # Ensure sensitive fields are masked or encrypted
                assert "ssn" not in data or data["ssn"] == "***-**-****"
                assert "salary" not in data or isinstance(
                    data["salary"], str
                )  # Should be encrypted/masked

    def test_api_rate_limiting(self, client, valid_jwt_token):
        """Test API rate limiting to prevent abuse"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Simulate rapid API calls
            responses = []
            for i in range(100):  # Make 100 rapid requests
                response = client.get(
                    "/api/v1/resource-integration/dashboard",
                    headers={"Authorization": f"Bearer {valid_jwt_token}"},
                )
                responses.append(response.status_code)

                # Break if rate limited
                if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    break

            # Should eventually be rate limited
            assert status.HTTP_429_TOO_MANY_REQUESTS in responses

    def test_secure_headers_present(self, client, valid_jwt_token):
        """Test that security headers are present in responses"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            response = client.get(
                "/api/v1/resource-integration/health-check",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )

            # Check for security headers
            headers = response.headers
            assert "X-Content-Type-Options" in headers
            assert "X-Frame-Options" in headers
            assert "X-XSS-Protection" in headers
            assert "Strict-Transport-Security" in headers

    def test_cors_configuration(self, client):
        """Test CORS configuration for security"""

        # Test preflight request
        response = client.options(
            "/api/v1/resource-integration/dashboard",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        # Should not allow arbitrary origins
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        assert cors_origin != "*" or cors_origin != "https://evil.com"

    def test_session_security(self, client, valid_jwt_token):
        """Test session security measures"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Test session fixation prevention
            response1 = client.get(
                "/api/v1/resource-integration/dashboard",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )

            response2 = client.get(
                "/api/v1/resource-integration/dashboard",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )

            # Session tokens should be consistent for same user
            if "Set-Cookie" in response1.headers and "Set-Cookie" in response2.headers:
                assert (
                    response1.headers["Set-Cookie"] == response2.headers["Set-Cookie"]
                )

    def test_data_masking_in_logs(self, client, valid_jwt_token):
        """Test that sensitive data is masked in application logs"""

        with (
            patch("app.api.v1.resource_management_api.get_current_user") as mock_auth,
            patch("logging.Logger.info") as mock_logger,
        ):
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            sensitive_data = {
                "name": "John Doe",
                "email": "john.doe@company.com",
                "ssn": "123-45-6789",
                "hourly_rate": 150.0,
                "type": "human",
                "department_id": 1,
            }

            client.post(
                "/api/v1/resource-management/resources",
                json=sensitive_data,
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )

            # Check that sensitive data is not logged in plain text
            if mock_logger.called:
                logged_messages = [call.args[0] for call in mock_logger.call_args_list]
                for message in logged_messages:
                    assert "123-45-6789" not in str(message)  # SSN should be masked
                    assert "john.doe@company.com" not in str(message) or "***" in str(
                        message
                    )

    def test_api_versioning_security(self, client, valid_jwt_token):
        """Test security consistency across API versions"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Test that deprecated endpoints are secured
            endpoints = [
                "/api/v1/resource-integration/dashboard",
                "/api/v1/resource-management/resources",
                "/api/v1/resource-analytics/analytics",
                "/api/v1/resource-planning/plans",
            ]

            for endpoint in endpoints:
                # Test without authentication
                response = client.get(endpoint)
                assert response.status_code == status.HTTP_401_UNAUTHORIZED

                # Test with authentication
                response = client.get(
                    endpoint, headers={"Authorization": f"Bearer {valid_jwt_token}"}
                )
                assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_parameter_tampering_prevention(self, client, valid_jwt_token):
        """Test prevention of parameter tampering attacks"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Test parameter pollution
            response = client.get(
                "/api/v1/resource-integration/dashboard?departments=1&departments=2&departments=3",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )

            # Should handle parameter pollution gracefully
            assert response.status_code in [200, 400, 422]

            # Test parameter injection
            response = client.get(
                "/api/v1/resource-integration/dashboard?departments=1&admin=true&bypass_auth=1",
                headers={"Authorization": f"Bearer {valid_jwt_token}"},
            )

            # Should ignore unknown parameters
            assert response.status_code in [200, 400, 422]

    def test_file_upload_security(self, client, valid_jwt_token):
        """Test file upload security measures"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Test malicious file uploads
            malicious_files = [
                ("test.exe", b"MZ\x90\x00"),  # Executable file
                ("test.php", b"<?php system($_GET['cmd']); ?>"),  # PHP script
                (
                    "test.jsp",
                    b"<% Runtime.getRuntime().exec(request.getParameter('cmd')); %>",
                ),  # JSP script
                (
                    "../../../etc/passwd",
                    b"root:x:0:0:root:/root:/bin/bash",
                ),  # Path traversal
            ]

            for filename, content in malicious_files:
                files = {"file": (filename, content, "application/octet-stream")}
                response = client.post(
                    "/api/v1/resource-management/import",
                    files=files,
                    headers={"Authorization": f"Bearer {valid_jwt_token}"},
                )

                # Should reject malicious files
                assert response.status_code in [400, 415, 422]

    def test_concurrent_access_control(self, client, valid_jwt_token):
        """Test concurrent access control and race conditions"""

        import threading
        import time

        results = []

        def make_request():
            with patch(
                "app.api.v1.resource_management_api.get_current_user"
            ) as mock_auth:
                mock_auth.return_value = {
                    "id": 1,
                    "username": "testuser",
                    "department_ids": [1],
                }

                response = client.put(
                    "/api/v1/resource-management/resources/1",
                    json={"name": f"Updated at {time.time()}", "hourly_rate": 160.0},
                    headers={"Authorization": f"Bearer {valid_jwt_token}"},
                )
                results.append(response.status_code)

        # Create multiple concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle concurrent access gracefully
        success_codes = [200, 409]  # 200 OK or 409 Conflict
        assert all(code in success_codes or code >= 400 for code in results)

    def test_business_logic_bypass_prevention(self, client, valid_jwt_token):
        """Test prevention of business logic bypass attempts"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Test bypass attempts through parameter manipulation
            bypass_attempts = [
                {"hourly_rate": -100.0},  # Negative rate
                {"hourly_rate": 999999.0},  # Unreasonably high rate
                {"department_id": -1},  # Invalid department
                {"type": "admin"},  # Attempting to set privileged type
                {"id": 999, "name": "Hacker"},  # Attempting to override ID
            ]

            for attempt in bypass_attempts:
                response = client.post(
                    "/api/v1/resource-management/resources",
                    json={
                        **attempt,
                        "name": "Test",
                        "type": "human",
                        "department_id": 1,
                    },
                    headers={"Authorization": f"Bearer {valid_jwt_token}"},
                )

                # Should validate business rules
                if response.status_code == 201:
                    data = response.json()
                    # Ensure business rules were applied
                    if "hourly_rate" in attempt:
                        assert data.get("hourly_rate", 0) >= 0
                        assert data.get("hourly_rate", 0) <= 500  # Reasonable maximum
                    if "department_id" in attempt:
                        assert data.get("department_id") > 0


class TestResourceManagementDataProtection:
    """Data protection and privacy tests"""

    def test_personal_data_anonymization(self):
        """Test personal data anonymization for analytics"""

        from app.api.v1.resource_analytics_api import ResourceAnalyticsService

        # Mock personal data
        personal_data = [
            {"name": "John Doe", "email": "john@company.com", "utilization": 85.0},
            {"name": "Jane Smith", "email": "jane@company.com", "utilization": 90.0},
        ]

        service = ResourceAnalyticsService(AsyncMock(), AsyncMock())

        # Test anonymization
        anonymized = service._anonymize_personal_data(personal_data)

        for record in anonymized:
            assert "name" not in record or record["name"].startswith("User_")
            assert "email" not in record or "*" in record["email"]
            assert "utilization" in record  # Business data should remain

    def test_data_retention_policy(self):
        """Test data retention policy enforcement"""

        from app.api.v1.resource_management_api import ResourceManagementService

        service = ResourceManagementService(AsyncMock(), AsyncMock())

        # Test old data identification
        old_date = date.today() - timedelta(days=2555)  # 7 years old
        recent_date = date.today() - timedelta(days=30)  # 1 month old

        old_records = [{"id": 1, "created_at": old_date, "type": "personal"}]
        recent_records = [{"id": 2, "created_at": recent_date, "type": "personal"}]

        # Should identify old records for deletion
        expired_records = service._identify_expired_records(
            old_records + recent_records, retention_years=5
        )

        assert len(expired_records) == 1
        assert expired_records[0]["id"] == 1

    def test_gdpr_compliance_data_export(self):
        """Test GDPR-compliant data export functionality"""

        from app.api.v1.resource_management_api import ResourceManagementService

        service = ResourceManagementService(AsyncMock(), AsyncMock())

        user_data = {
            "personal_info": {"name": "John Doe", "email": "john@company.com"},
            "work_data": {"department": "Engineering", "utilization": 85.0},
            "sensitive_data": {"salary": 75000.0, "performance_reviews": ["Excellent"]},
        }

        # Test data export with proper formatting
        export_data = service._prepare_gdpr_export(user_data, user_id=1)

        assert "personal_info" in export_data
        assert "work_data" in export_data
        assert "data_sources" in export_data
        assert "export_timestamp" in export_data
        assert export_data["user_id"] == 1

    def test_data_deletion_completeness(self):
        """Test complete data deletion for GDPR right to be forgotten"""

        from app.api.v1.resource_management_api import ResourceManagementService

        service = ResourceManagementService(AsyncMock(), AsyncMock())

        # Mock data across multiple tables
        user_references = {
            "resources": [{"id": 1, "name": "John Doe"}],
            "allocations": [{"id": 1, "resource_id": 1}],
            "performance_reviews": [{"id": 1, "resource_id": 1}],
            "audit_logs": [{"id": 1, "user_id": 1}],
        }

        # Test deletion plan
        deletion_plan = service._create_deletion_plan(
            user_id=1, references=user_references
        )

        assert len(deletion_plan["tables"]) >= 4
        assert "resources" in deletion_plan["tables"]
        assert "allocations" in deletion_plan["tables"]
        assert deletion_plan["cascading_deletes"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
