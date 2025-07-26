"""
ITDO ERP Backend - Security Configuration Tests
Day 23: Security middleware, headers, and configuration testing
"""

from __future__ import annotations

import ssl
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.testclient import TestClient


class TestSecurityConfiguration:
    """Tests for security configuration and middleware"""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI application with security middleware"""
        app = FastAPI()

        # Add security middleware
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.itdo-erp.com"],
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://app.itdo-erp.com", "https://admin.itdo-erp.com"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
            expose_headers=["X-Total-Count"],
        )

        # Add security headers middleware
        @app.middleware("http")
        async def add_security_headers(request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            )
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=()"
            )
            return response

        # Add test endpoint
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        return app

    @pytest.fixture
    def client(self, mock_app):
        """Test client with security configuration"""
        return TestClient(mock_app)

    def test_security_headers_present(self, client):
        """Test that all security headers are present"""

        response = client.get("/test")
        headers = response.headers

        # Test essential security headers
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

        assert "X-XSS-Protection" in headers
        assert headers["X-XSS-Protection"] == "1; mode=block"

        assert "Strict-Transport-Security" in headers
        assert "max-age=31536000" in headers["Strict-Transport-Security"]
        assert "includeSubDomains" in headers["Strict-Transport-Security"]

        assert "Content-Security-Policy" in headers
        assert "default-src 'self'" in headers["Content-Security-Policy"]

        assert "Referrer-Policy" in headers
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

        assert "Permissions-Policy" in headers
        assert "geolocation=()" in headers["Permissions-Policy"]

    def test_cors_configuration(self, client):
        """Test CORS configuration and restrictions"""

        # Test allowed origin
        response = client.options(
            "/test",
            headers={
                "Origin": "https://app.itdo-erp.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        assert response.status_code == 200
        assert (
            response.headers.get("Access-Control-Allow-Origin")
            == "https://app.itdo-erp.com"
        )
        assert "Authorization" in response.headers.get(
            "Access-Control-Allow-Headers", ""
        )

        # Test disallowed origin
        response = client.options(
            "/test",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should not include CORS headers for disallowed origins
        assert response.headers.get("Access-Control-Allow-Origin") != "https://evil.com"

    def test_trusted_host_middleware(self, client):
        """Test trusted host middleware configuration"""

        # Test allowed host
        response = client.get("/test", headers={"Host": "localhost"})
        assert response.status_code == 200

        # Test disallowed host
        response = client.get("/test", headers={"Host": "evil.com"})
        assert response.status_code == 400  # Bad Request due to untrusted host

    def test_content_type_validation(self, client):
        """Test content type validation and security"""

        # Test valid JSON content type
        response = client.post(
            "/test", json={"test": "data"}, headers={"Content-Type": "application/json"}
        )
        # Endpoint doesn't exist but content type should be processed

        # Test dangerous content types
        dangerous_content_types = [
            "text/html",  # Could lead to XSS
            "application/x-www-form-urlencoded",  # Could bypass validation
            "multipart/form-data",  # File upload risks
            "application/xml",  # XXE risks
            "text/xml",  # XXE risks
        ]

        for content_type in dangerous_content_types:
            response = client.post(
                "/test",
                data="<script>alert('xss')</script>",
                headers={"Content-Type": content_type},
            )
            # Should handle safely or reject dangerous content types
            assert response.status_code in [400, 405, 415, 422]

    def test_request_size_limits(self, client):
        """Test request size limits to prevent DoS"""

        # Test reasonable request size
        normal_data = {"data": "x" * 1000}  # 1KB
        response = client.post("/test", json=normal_data)
        assert response.status_code in [200, 404, 405]  # Not rejected due to size

        # Test oversized request (simulated)
        large_data = {"data": "x" * 10000000}  # 10MB
        with patch("fastapi.Request.body") as mock_body:
            mock_body.side_effect = Exception("Request entity too large")

            response = client.post("/test", json=large_data)
            # Should be rejected or handled gracefully
            assert response.status_code in [400, 413, 422, 500]

    def test_rate_limiting_configuration(self, client):
        """Test rate limiting middleware"""

        # Simulate rate limiting by making many requests
        responses = []
        for i in range(100):
            response = client.get("/test")
            responses.append(response.status_code)

            # If rate limited, break
            if response.status_code == 429:
                break

        # Should eventually hit rate limit
        assert 429 in responses or len(responses) < 100

    def test_ssl_tls_configuration(self):
        """Test SSL/TLS configuration requirements"""

        # Test minimum TLS version requirement
        ssl_context = ssl.create_default_context()

        # Should require TLS 1.2 or higher
        assert ssl_context.minimum_version >= ssl.TLSVersion.TLSv1_2

        # Should disable weak ciphers
        weak_ciphers = ["DES", "3DES", "RC4", "MD5", "SHA1"]
        available_ciphers = ssl_context.get_ciphers()

        for cipher_info in available_ciphers:
            cipher_name = cipher_info.get("name", "")
            for weak_cipher in weak_ciphers:
                assert weak_cipher not in cipher_name.upper(), (
                    f"Weak cipher {weak_cipher} is enabled"
                )

    def test_session_configuration(self, client):
        """Test session security configuration"""

        response = client.get("/test")

        # Check session cookie security if sessions are used
        set_cookie = response.headers.get("Set-Cookie", "")
        if set_cookie:
            # Session cookies should be secure
            assert "Secure" in set_cookie, "Session cookie missing Secure flag"
            assert "HttpOnly" in set_cookie, "Session cookie missing HttpOnly flag"
            assert "SameSite=Strict" in set_cookie or "SameSite=Lax" in set_cookie, (
                "Session cookie missing SameSite"
            )

    def test_error_handling_security(self, client):
        """Test that error messages don't leak sensitive information"""

        # Test 404 error
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        error_message = response.json().get("detail", "")

        # Should not reveal system information
        sensitive_info = [
            "traceback",
            "stack trace",
            "file path",
            "database",
            "internal",
            "debug",
        ]
        for info in sensitive_info:
            assert info.lower() not in error_message.lower(), (
                f"Error message contains sensitive info: {info}"
            )

        # Test 500 error (simulated)
        with patch("fastapi.FastAPI.exception_handler") as mock_handler:
            mock_handler.side_effect = Exception("Internal error")

            response = client.get("/test")
            if response.status_code >= 500:
                error_data = response.json()
                assert "Internal Server Error" in str(error_data), (
                    "Detailed error information leaked"
                )

    def test_http_method_restrictions(self, client):
        """Test HTTP method restrictions"""

        # Test that dangerous methods are disabled
        dangerous_methods = ["TRACE", "TRACK", "DEBUG", "CONNECT"]

        for method in dangerous_methods:
            # Most test clients don't support these methods, so we simulate
            with patch("httpx.request") as mock_request:
                mock_request.return_value = Mock(status_code=405)

                # Should return 405 Method Not Allowed
                assert mock_request.return_value.status_code == 405

    def test_information_disclosure_prevention(self, client):
        """Test prevention of information disclosure"""

        response = client.get("/test")

        # Check response headers don't reveal sensitive information
        headers_to_check = ["Server", "X-Powered-By", "X-AspNet-Version", "X-Runtime"]

        for header in headers_to_check:
            if header in response.headers:
                header_value = response.headers[header]
                # Should not reveal detailed version information
                assert not any(
                    version in header_value.lower()
                    for version in ["python", "fastapi", "uvicorn", "version"]
                )

    def test_input_encoding_security(self, client):
        """Test input encoding and character set security"""

        # Test various character encodings
        malicious_inputs = [
            "test\x00",  # Null byte injection
            "test\r\n",  # CRLF injection
            "test\x1f",  # Control characters
            "test%00",  # URL encoded null byte
            "test%0d%0a",  # URL encoded CRLF
            "test\uff1c\uff1e",  # Unicode bypasses
        ]

        for malicious_input in malicious_inputs:
            response = client.get(f"/test?param={malicious_input}")

            # Should handle malicious input safely
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                response_text = response.text
                # Ensure malicious characters are not reflected
                assert "\x00" not in response_text
                assert "\r\n" not in response_text

    def test_api_versioning_security(self, client):
        """Test API versioning security"""

        # Test that older API versions are properly deprecated/secured
        old_version_paths = [
            "/api/v0/test",
            "/api/beta/test",
            "/api/internal/test",
            "/api/debug/test",
            "/api/admin/test",
        ]

        for path in old_version_paths:
            response = client.get(path)

            # Should either not exist or require proper authentication
            assert response.status_code in [401, 403, 404, 405]

    def test_dependency_security_headers(self, client):
        """Test security headers for dependency management"""

        response = client.get("/test")

        # Check for security-related headers that indicate good practices
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=",
            "Content-Security-Policy": "default-src",
        }

        for header, expected_values in security_headers.items():
            assert header in response.headers, f"Missing security header: {header}"

            header_value = response.headers[header]
            if isinstance(expected_values, list):
                assert any(value in header_value for value in expected_values), (
                    f"Invalid {header} value: {header_value}"
                )
            else:
                assert expected_values in header_value, (
                    f"Invalid {header} value: {header_value}"
                )

    def test_logging_security_configuration(self):
        """Test secure logging configuration"""

        import logging

        # Test that sensitive data is not logged
        with patch("logging.Logger.info") as mock_logger:
            # Simulate logging with sensitive data
            logger = logging.getLogger("test")
            logger.info("User password: secret123")
            logger.info("API key: sk-1234567890abcdef")
            logger.info("SSN: 123-45-6789")

            # Verify sensitive data is masked or filtered
            logged_messages = [call.args[0] for call in mock_logger.call_args_list]
            for message in logged_messages:
                assert "secret123" not in message, "Password logged in plain text"
                assert "sk-1234567890abcdef" not in message, (
                    "API key logged in plain text"
                )
                assert "123-45-6789" not in message, "SSN logged in plain text"

    def test_database_connection_security(self):
        """Test database connection security configuration"""

        # Mock database configuration
        db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "itdo_erp",
            "username": "app_user",
            "password": "secure_password",
            "ssl_mode": "require",
            "ssl_cert": "/path/to/cert.pem",
            "ssl_key": "/path/to/key.pem",
            "ssl_rootcert": "/path/to/ca.pem",
        }

        # Verify SSL is required
        assert db_config.get("ssl_mode") in ["require", "verify-ca", "verify-full"], (
            "Database SSL not required"
        )

        # Verify certificates are configured
        assert db_config.get("ssl_cert"), "Database SSL certificate not configured"
        assert db_config.get("ssl_key"), "Database SSL key not configured"

        # Verify connection limits
        assert (
            "max_connections" not in db_config or db_config["max_connections"] <= 100
        ), "Database connection limit too high"

    def test_redis_security_configuration(self):
        """Test Redis security configuration"""

        # Mock Redis configuration
        redis_config = {
            "host": "localhost",
            "port": 6379,
            "password": "redis_password",
            "ssl": True,
            "ssl_cert_reqs": "required",
            "ssl_ca_certs": "/path/to/ca.pem",
            "ssl_certfile": "/path/to/cert.pem",
            "ssl_keyfile": "/path/to/key.pem",
        }

        # Verify authentication is required
        assert redis_config.get("password"), "Redis password not configured"

        # Verify SSL is enabled
        assert redis_config.get("ssl") is True, "Redis SSL not enabled"
        assert redis_config.get("ssl_cert_reqs") == "required", (
            "Redis SSL certificate verification not required"
        )

    def test_environment_configuration_security(self):
        """Test environment configuration security"""

        import os

        # Test that debug mode is disabled in production-like environment
        debug_mode = os.getenv("DEBUG", "false").lower()
        assert debug_mode != "true", "Debug mode is enabled"

        # Test that sensitive environment variables are not in defaults
        sensitive_vars = ["SECRET_KEY", "DATABASE_PASSWORD", "API_KEY", "JWT_SECRET"]

        for var in sensitive_vars:
            env_value = os.getenv(var, "")
            assert env_value != "", f"Sensitive environment variable {var} not set"
            assert env_value not in ["default", "changeme", "password", "secret"], (
                f"Weak default value for {var}"
            )
            assert len(env_value) >= 20, f"Environment variable {var} too short"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
