"""Test suite for API versioning system.

This module tests the comprehensive API versioning strategy including:
- URL-based versioning
- Version validation
- Deprecation warnings
- OpenAPI schema versioning
- Version migration utilities
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.versioning import (
    APIVersionManager,
    DeprecationWarningMiddleware,
    VersionValidationMiddleware,
    generate_deprecation_warning,
    get_version_from_request,
    parse_version,
    validate_version,
)


class TestAPIVersionParsing:
    """Test API version parsing utilities."""

    def test_parse_version_valid_formats(self):
        """Test parsing valid version formats."""
        assert parse_version("v1") == (1, 0, 0)
        assert parse_version("v1.0") == (1, 0, 0)
        assert parse_version("v1.2") == (1, 2, 0)
        assert parse_version("v1.2.3") == (1, 2, 3)
        assert parse_version("2.1.0") == (2, 1, 0)

    def test_parse_version_invalid_formats(self):
        """Test parsing invalid version formats."""
        with pytest.raises(ValueError):
            parse_version("invalid")
        with pytest.raises(ValueError):
            parse_version("v")
        with pytest.raises(ValueError):
            parse_version("v1.2.3.4")

    def test_validate_version_supported(self):
        """Test validation of supported versions."""
        supported_versions = ["v1", "v2", "v2.1"]

        assert validate_version("v1", supported_versions) is True
        assert validate_version("v2", supported_versions) is True
        assert validate_version("v2.1", supported_versions) is True

    def test_validate_version_unsupported(self):
        """Test validation of unsupported versions."""
        supported_versions = ["v1", "v2"]

        assert validate_version("v3", supported_versions) is False
        assert validate_version("v0.9", supported_versions) is False


class TestVersionDetection:
    """Test version detection from requests."""

    def test_get_version_from_url_path(self):
        """Test extracting version from URL path."""
        mock_request = Mock()
        mock_request.url.path = "/api/v1/users"
        assert get_version_from_request(mock_request) == "v1"

        mock_request.url.path = "/api/v2.1/organizations"
        assert get_version_from_request(mock_request) == "v2.1"

    def test_get_version_from_header(self):
        """Test extracting version from API-Version header."""
        mock_request = Mock()
        mock_request.url.path = "/api/users"
        mock_request.headers = {"API-Version": "v2"}
        assert get_version_from_request(mock_request) == "v2"

    def test_get_version_default(self):
        """Test default version when none specified."""
        mock_request = Mock()
        mock_request.url.path = "/api/users"
        mock_request.headers = {}
        assert get_version_from_request(mock_request) == "v1"  # Default


class TestAPIVersionManager:
    """Test the main API version manager."""

    def test_version_manager_initialization(self):
        """Test version manager initialization."""
        manager = APIVersionManager()
        assert manager.default_version == "v1"
        assert "v1" in manager.supported_versions

    def test_register_version(self):
        """Test registering new API versions."""
        manager = APIVersionManager()
        manager.register_version("v2", {"description": "Version 2 API"})
        assert "v2" in manager.supported_versions

    def test_deprecate_version(self):
        """Test deprecating API versions."""
        manager = APIVersionManager()
        manager.register_version("v1", {"description": "Version 1 API"})

        deprecation_date = datetime.now() - timedelta(days=30)  # Past date
        removal_date = datetime.now() + timedelta(days=180)

        manager.deprecate_version("v1", deprecation_date, removal_date)
        assert manager.is_deprecated("v1") is True
        assert manager.get_deprecation_info("v1") is not None

    def test_version_compatibility(self):
        """Test version compatibility checking."""
        manager = APIVersionManager()
        manager.register_version("v1", {"description": "Version 1"})
        manager.register_version("v2", {"description": "Version 2"})

        # v1 should be compatible with v1.x
        assert manager.is_compatible("v1", "v1.1") is True
        # v2 should not be compatible with v1
        assert manager.is_compatible("v1", "v2") is False


class TestDeprecationWarnings:
    """Test deprecation warning functionality."""

    def test_generate_deprecation_warning(self):
        """Test generating deprecation warning messages."""
        deprecation_date = datetime(2024, 12, 31)
        removal_date = datetime(2025, 6, 30)

        warning = generate_deprecation_warning("v1", deprecation_date, removal_date)

        assert "v1" in warning
        assert "deprecated" in warning.lower()
        assert "2024-12-31" in warning
        assert "2025-06-30" in warning

    def test_deprecation_warning_header_format(self):
        """Test deprecation warning header format compliance."""
        manager = APIVersionManager()
        deprecation_date = datetime(2024, 12, 31)
        removal_date = datetime(2025, 6, 30)

        manager.register_version("v1", {"description": "Version 1"})
        manager.deprecate_version("v1", deprecation_date, removal_date)

        header = manager.get_deprecation_header("v1")

        # Should follow RFC format
        assert header.startswith("true")
        assert "date=" in header
        assert "sunset=" in header


class TestVersionValidationMiddleware:
    """Test version validation middleware."""

    @pytest.fixture
    def app_with_middleware(self):
        """Create FastAPI app with version validation middleware."""
        app = FastAPI()

        # Create test version manager
        test_manager = APIVersionManager()
        test_manager.register_version("v2", {"description": "Version 2"})

        # Add our versioning middleware with test manager
        app.add_middleware(VersionValidationMiddleware, version_manager=test_manager)

        @app.get("/api/v1/test")
        async def test_v1():
            return {"version": "v1", "message": "test"}

        @app.get("/api/v2/test")
        async def test_v2():
            return {"version": "v2", "message": "test"}

        return app

    def test_valid_version_request(self, app_with_middleware):
        """Test requests with valid versions."""
        client = TestClient(app_with_middleware)

        response = client.get("/api/v1/test")
        assert response.status_code == 200
        assert response.json()["version"] == "v1"

    def test_invalid_version_request(self, app_with_middleware):
        """Test requests with invalid versions."""
        client = TestClient(app_with_middleware)

        # Test that middleware properly handles invalid versions
        with client:
            response = client.get("/api/v99/test")
            assert response.status_code == 400
            assert "unsupported" in response.json()["detail"].lower()

    def test_version_header_validation(self, app_with_middleware):
        """Test API-Version header validation."""
        client = TestClient(app_with_middleware)

        # Valid header
        response = client.get("/api/test", headers={"API-Version": "v1"})
        assert response.status_code in [200, 404]  # 404 is ok, route doesn't exist

        # Invalid header
        with client:
            response = client.get("/api/test", headers={"API-Version": "v99"})
            assert response.status_code == 400


class TestDeprecationWarningMiddleware:
    """Test deprecation warning middleware."""

    @pytest.fixture
    def app_with_deprecation_middleware(self):
        """Create FastAPI app with deprecation warning middleware."""
        app = FastAPI()

        # Setup version manager with deprecated version
        manager = APIVersionManager()
        deprecation_date = datetime.now() - timedelta(days=30)
        removal_date = datetime.now() + timedelta(days=150)
        manager.register_version("v1", {"description": "Version 1"})
        manager.deprecate_version("v1", deprecation_date, removal_date)

        app.add_middleware(DeprecationWarningMiddleware, version_manager=manager)

        @app.get("/api/v1/test")
        async def test_deprecated():
            return {"message": "deprecated endpoint"}

        @app.get("/api/v2/test")
        async def test_current():
            return {"message": "current endpoint"}

        return app

    def test_deprecation_warning_headers(self, app_with_deprecation_middleware):
        """Test that deprecation warnings are added to headers."""
        client = TestClient(app_with_deprecation_middleware)

        response = client.get("/api/v1/test")
        assert response.status_code == 200
        assert "Deprecation" in response.headers
        assert "Sunset" in response.headers

    def test_no_deprecation_for_current_version(self, app_with_deprecation_middleware):
        """Test that current versions don't get deprecation headers."""
        client = TestClient(app_with_deprecation_middleware)

        response = client.get("/api/v2/test")
        assert response.status_code == 200
        assert "Deprecation" not in response.headers


class TestOpenAPIVersioning:
    """Test OpenAPI schema versioning."""

    def test_version_specific_openapi_schemas(self):
        """Test generation of version-specific OpenAPI schemas."""
        manager = APIVersionManager()
        manager.register_version(
            "v1",
            {"description": "Version 1 API", "openapi_schema": {"version": "1.0.0"}},
        )
        manager.register_version(
            "v2",
            {"description": "Version 2 API", "openapi_schema": {"version": "2.0.0"}},
        )

        v1_schema = manager.get_openapi_schema("v1")
        v2_schema = manager.get_openapi_schema("v2")

        assert v1_schema["version"] == "1.0.0"
        assert v2_schema["version"] == "2.0.0"

    def test_version_specific_docs_urls(self):
        """Test generation of version-specific documentation URLs."""
        manager = APIVersionManager()

        v1_docs = manager.get_docs_url("v1")
        v2_docs = manager.get_docs_url("v2")

        assert "/v1/docs" in v1_docs
        assert "/v2/docs" in v2_docs


class TestVersionMigrationUtilities:
    """Test API version migration utilities."""

    def test_breaking_change_detection(self):
        """Test detection of breaking changes between versions."""
        manager = APIVersionManager()

        v1_schema = {
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        v2_schema = {
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "properties": {
                                                "user_id": {
                                                    "type": "integer"
                                                },  # Breaking: renamed field
                                                "name": {"type": "string"},
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        changes = manager.detect_breaking_changes(v1_schema, v2_schema)
        assert len(changes) > 0
        assert any(
            "field renamed" in change.lower() or "property" in change.lower()
            for change in changes
        )

    def test_migration_guide_generation(self):
        """Test generation of migration guides."""
        manager = APIVersionManager()

        guide = manager.generate_migration_guide("v1", "v2")
        assert isinstance(guide, dict)
        assert "from_version" in guide
        assert "to_version" in guide
        assert guide["from_version"] == "v1"
        assert guide["to_version"] == "v2"


class TestVersionRoutingIntegration:
    """Test integration with FastAPI routing."""

    def test_version_specific_route_registration(self):
        """Test registering routes for specific versions."""
        app = FastAPI()
        manager = APIVersionManager()

        # This would be implemented in the actual versioning system
        v1_routes = manager.get_version_routes("v1")
        v2_routes = manager.get_version_routes("v2")

        # Test that different versions can have different routes
        assert isinstance(v1_routes, (list, dict))
        assert isinstance(v2_routes, (list, dict))

    def test_version_prefix_handling(self):
        """Test URL prefix handling for different versions."""
        manager = APIVersionManager()

        v1_prefix = manager.get_version_prefix("v1")
        v2_prefix = manager.get_version_prefix("v2")

        assert v1_prefix == "/api/v1"
        assert v2_prefix == "/api/v2"
