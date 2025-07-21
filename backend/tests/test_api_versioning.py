"""Tests for API versioning system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from app.core.versioning import (
    SemanticVersion,
    APIVersionInfo,
    APIVersionRegistry,
    VersionStatus,
    BreakingChange,
    BreakingChangeType,
    VersionExtractor,
    BackwardCompatibilityLayer,
    DeprecationManager,
)
from app.core.sdk_generator import (
    SDKConfiguration,
    PythonSDKGenerator,
    TypeScriptSDKGenerator,
    SDKGeneratorFactory,
    APIEndpoint,
)


class TestSemanticVersion:
    """Tests for semantic version implementation."""

    def test_version_parsing(self):
        """Test version string parsing."""
        version = SemanticVersion.parse("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease is None
        assert version.build is None

    def test_version_parsing_with_prerelease(self):
        """Test version parsing with prerelease."""
        version = SemanticVersion.parse("1.2.3-beta.1")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease == "beta.1"

    def test_version_parsing_with_build(self):
        """Test version parsing with build metadata."""
        version = SemanticVersion.parse("1.2.3+20230101")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.build == "20230101"

    def test_version_parsing_full(self):
        """Test version parsing with all components."""
        version = SemanticVersion.parse("1.2.3-beta.1+20230101")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease == "beta.1"
        assert version.build == "20230101"

    def test_invalid_version_parsing(self):
        """Test invalid version strings."""
        with pytest.raises(ValueError):
            SemanticVersion.parse("1.2")
        
        with pytest.raises(ValueError):
            SemanticVersion.parse("1.2.3.4")
        
        with pytest.raises(ValueError):
            SemanticVersion.parse("v1.2.3")

    def test_version_comparison(self):
        """Test version comparison operators."""
        v1 = SemanticVersion.parse("1.0.0")
        v2 = SemanticVersion.parse("1.1.0")
        v3 = SemanticVersion.parse("2.0.0")
        v4 = SemanticVersion.parse("1.0.0-beta")
        
        assert v1 < v2
        assert v2 < v3
        assert v4 < v1  # prerelease is less than normal version
        assert v1 == SemanticVersion.parse("1.0.0")

    def test_version_compatibility(self):
        """Test version compatibility checking."""
        v1 = SemanticVersion.parse("1.2.3")
        v2 = SemanticVersion.parse("1.3.0")
        v3 = SemanticVersion.parse("2.0.0")
        
        assert v1.is_compatible_with(v2)
        assert not v1.is_compatible_with(v3)

    def test_version_increment(self):
        """Test version increment methods."""
        version = SemanticVersion.parse("1.2.3")
        
        major = version.increment_major()
        assert str(major) == "2.0.0"
        
        minor = version.increment_minor()
        assert str(minor) == "1.3.0"
        
        patch = version.increment_patch()
        assert str(patch) == "1.2.4"

    def test_version_string_representation(self):
        """Test version string representation."""
        version = SemanticVersion(1, 2, 3, "beta.1", "20230101")
        assert str(version) == "1.2.3-beta.1+20230101"


class TestAPIVersionRegistry:
    """Tests for API version registry."""

    def test_register_version(self):
        """Test version registration."""
        registry = APIVersionRegistry()
        
        version_info = registry.register_version(
            "1.0.0",
            status=VersionStatus.STABLE,
            description="Initial release"
        )
        
        assert version_info.version == SemanticVersion.parse("1.0.0")
        assert version_info.status == VersionStatus.STABLE
        assert version_info.description == "Initial release"

    def test_get_version(self):
        """Test getting version information."""
        registry = APIVersionRegistry()
        registry.register_version("1.0.0")
        
        version_info = registry.get_version("1.0.0")
        assert version_info is not None
        assert str(version_info.version) == "1.0.0"
        
        # Test non-existent version
        assert registry.get_version("2.0.0") is None

    def test_get_latest_version(self):
        """Test getting latest version."""
        registry = APIVersionRegistry()
        
        registry.register_version("1.0.0", VersionStatus.STABLE)
        registry.register_version("1.1.0", VersionStatus.STABLE)
        registry.register_version("2.0.0", VersionStatus.BETA)
        
        latest = registry.get_latest_version(include_prerelease=False)
        assert str(latest.version) == "1.1.0"
        
        latest_with_prerelease = registry.get_latest_version(include_prerelease=True)
        assert str(latest_with_prerelease.version) == "2.0.0"

    def test_get_compatible_versions(self):
        """Test getting compatible versions."""
        registry = APIVersionRegistry()
        
        registry.register_version("1.0.0")
        registry.register_version("1.1.0")
        registry.register_version("1.2.0")
        registry.register_version("2.0.0")
        
        compatible = registry.get_compatible_versions("1.1.0")
        compatible_versions = [str(v.version) for v in compatible]
        
        assert "1.2.0" in compatible_versions
        assert "1.1.0" in compatible_versions
        assert "1.0.0" in compatible_versions
        assert "2.0.0" not in compatible_versions

    def test_deprecate_version(self):
        """Test version deprecation."""
        registry = APIVersionRegistry()
        registry.register_version("1.0.0")
        
        sunset_date = datetime.utcnow() + timedelta(days=90)
        success = registry.deprecate_version("1.0.0", sunset_date)
        
        assert success
        
        version_info = registry.get_version("1.0.0")
        assert version_info.status == VersionStatus.DEPRECATED
        assert version_info.sunset_date == sunset_date

    def test_sunset_version(self):
        """Test version sunsetting."""
        registry = APIVersionRegistry()
        registry.register_version("1.0.0")
        
        success = registry.sunset_version("1.0.0")
        assert success
        
        version_info = registry.get_version("1.0.0")
        assert version_info.status == VersionStatus.SUNSET

    def test_list_versions_filtering(self):
        """Test version listing with filters."""
        registry = APIVersionRegistry()
        
        registry.register_version("1.0.0", VersionStatus.DEPRECATED)
        registry.register_version("1.1.0", VersionStatus.STABLE)
        registry.register_version("1.2.0", VersionStatus.SUNSET)
        
        all_versions = registry.list_versions()
        assert len(all_versions) == 3
        
        active_only = registry.list_versions(include_deprecated=False)
        assert len(active_only) == 1
        assert str(active_only[0].version) == "1.1.0"
        
        no_sunset = registry.list_versions(include_sunset=False)
        assert len(no_sunset) == 2


class TestVersionExtractor:
    """Tests for version extraction from requests."""

    def test_extract_from_header(self):
        """Test version extraction from header."""
        mock_request = Mock()
        mock_request.headers = {"API-Version": "1.2.3"}
        
        version = VersionExtractor.from_header(mock_request)
        assert version == "1.2.3"

    def test_extract_from_accept_header(self):
        """Test version extraction from Accept header."""
        mock_request = Mock()
        mock_request.headers = {"Accept": "application/vnd.myapi.v1.2+json"}
        
        version = VersionExtractor.from_accept_header(mock_request)
        assert version == "1.2"

    def test_extract_from_query_param(self):
        """Test version extraction from query parameter."""
        mock_request = Mock()
        mock_request.query_params = {"version": "1.2.3"}
        
        version = VersionExtractor.from_query_param(mock_request)
        assert version == "1.2.3"

    def test_extract_from_url_path(self):
        """Test version extraction from URL path."""
        mock_request = Mock()
        mock_request.url.path = "/api/v1.2.3/users"
        
        version = VersionExtractor.from_url_path(mock_request)
        assert version == "1.2.3"


class TestBackwardCompatibilityLayer:
    """Tests for backward compatibility layer."""

    def test_register_transformer(self):
        """Test transformer registration."""
        registry = APIVersionRegistry()
        compatibility = BackwardCompatibilityLayer(registry)
        
        def transformer(data):
            data["new_field"] = data.pop("old_field")
            return data
        
        compatibility.register_transformer("1.0.0", "2.0.0", transformer)
        
        assert "1.0.0" in compatibility.transformers
        assert "2.0.0" in compatibility.transformers["1.0.0"]

    def test_transform_request(self):
        """Test request transformation."""
        registry = APIVersionRegistry()
        compatibility = BackwardCompatibilityLayer(registry)
        
        def transformer(data):
            data["new_field"] = data.pop("old_field")
            return data
        
        compatibility.register_transformer("1.0.0", "2.0.0", transformer)
        
        input_data = {"old_field": "value"}
        result = compatibility.transform_request(input_data, "1.0.0", "2.0.0")
        
        assert "new_field" in result
        assert "old_field" not in result
        assert result["new_field"] == "value"

    def test_transform_same_version(self):
        """Test transformation with same version."""
        registry = APIVersionRegistry()
        compatibility = BackwardCompatibilityLayer(registry)
        
        input_data = {"field": "value"}
        result = compatibility.transform_request(input_data, "1.0.0", "1.0.0")
        
        assert result == input_data


class TestDeprecationManager:
    """Tests for deprecation management."""

    def test_check_deprecation_warnings(self):
        """Test deprecation warning checks."""
        registry = APIVersionRegistry()
        manager = DeprecationManager(registry)
        
        # Register deprecated version
        registry.register_version("1.0.0", VersionStatus.DEPRECATED)
        
        warnings = manager.check_deprecation_warnings("1.0.0")
        assert len(warnings) > 0
        assert "deprecated" in warnings[0].lower()

    def test_check_sunset_warnings(self):
        """Test sunset warning checks."""
        registry = APIVersionRegistry()
        manager = DeprecationManager(registry)
        
        # Register version with sunset date
        sunset_date = datetime.utcnow() + timedelta(days=15)
        registry.register_version("1.0.0", VersionStatus.DEPRECATED, sunset_date=sunset_date)
        
        warnings = manager.check_deprecation_warnings("1.0.0")
        assert any("sunsets in" in warning for warning in warnings)

    def test_get_migration_info(self):
        """Test migration information retrieval."""
        registry = APIVersionRegistry()
        manager = DeprecationManager(registry)
        
        # Register deprecated version with breaking changes
        breaking_change = BreakingChange(
            change_type=BreakingChangeType.FIELD_REMOVED,
            description="Field removed",
            affected_endpoints=["/api/users"],
            migration_guide="Use new_field instead",
            introduced_in_version="2.0.0"
        )
        
        registry.register_version(
            "1.0.0",
            VersionStatus.DEPRECATED,
            breaking_changes=[breaking_change]
        )
        registry.register_version("2.0.0", VersionStatus.STABLE)
        
        migration_info = manager.get_migration_info("1.0.0")
        
        assert migration_info["deprecated_version"] == "1.0.0"
        assert migration_info["recommended_version"] == "2.0.0"
        assert len(migration_info["breaking_changes"]) == 1


class TestSDKGeneration:
    """Tests for SDK generation."""

    def test_sdk_configuration(self):
        """Test SDK configuration creation."""
        config = SDKConfiguration(
            package_name="test-api",
            version="1.0.0",
            language="python",
            api_base_url="http://localhost:8000"
        )
        
        assert config.package_name == "test-api"
        assert config.version == "1.0.0"
        assert config.language == "python"

    def test_python_sdk_generator(self):
        """Test Python SDK generation."""
        config = SDKConfiguration(
            package_name="test-api",
            version="1.0.0",
            language="python",
            api_base_url="http://localhost:8000"
        )
        
        generator = PythonSDKGenerator(config)
        
        # Add test endpoint
        endpoint = APIEndpoint(
            path="/users",
            method="get",
            operation_id="list_users",
            summary="List users"
        )
        generator.add_endpoint(endpoint)
        
        # Add test model
        generator.add_model("User", {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"}
            }
        })
        
        files = generator.generate()
        
        assert "client.py" in files
        assert "models.py" in files
        assert "setup.py" in files
        assert "list_users" in files["client.py"]

    def test_typescript_sdk_generator(self):
        """Test TypeScript SDK generation."""
        config = SDKConfiguration(
            package_name="test-api",
            version="1.0.0",
            language="typescript",
            api_base_url="http://localhost:8000"
        )
        
        generator = TypeScriptSDKGenerator(config)
        
        # Add test endpoint
        endpoint = APIEndpoint(
            path="/users",
            method="get",
            operation_id="listUsers",
            summary="List users"
        )
        generator.add_endpoint(endpoint)
        
        files = generator.generate()
        
        assert "src/client.ts" in files
        assert "src/types.ts" in files
        assert "package.json" in files
        assert "listUsers" in files["src/client.ts"]

    def test_sdk_generator_factory(self):
        """Test SDK generator factory."""
        config = SDKConfiguration(
            package_name="test-api",
            version="1.0.0",
            language="python",
            api_base_url="http://localhost:8000"
        )
        
        generator = SDKGeneratorFactory.create_generator("python", config)
        assert isinstance(generator, PythonSDKGenerator)
        
        generator = SDKGeneratorFactory.create_generator("typescript", config)
        assert isinstance(generator, TypeScriptSDKGenerator)
        
        with pytest.raises(ValueError):
            SDKGeneratorFactory.create_generator("unsupported", config)

    def test_supported_languages(self):
        """Test supported languages listing."""
        languages = SDKGeneratorFactory.supported_languages()
        assert "python" in languages
        assert "typescript" in languages


class TestAPIVersionInfo:
    """Tests for API version info."""

    def test_version_info_creation(self):
        """Test API version info creation."""
        version = SemanticVersion.parse("1.0.0")
        info = APIVersionInfo(
            version=version,
            status=VersionStatus.STABLE,
            release_date=datetime.utcnow(),
            description="Test version"
        )
        
        assert info.version == version
        assert info.status == VersionStatus.STABLE
        assert info.description == "Test version"

    def test_deprecation_checks(self):
        """Test deprecation status checks."""
        version = SemanticVersion.parse("1.0.0")
        
        deprecated_info = APIVersionInfo(
            version=version,
            status=VersionStatus.DEPRECATED,
            release_date=datetime.utcnow()
        )
        
        sunset_info = APIVersionInfo(
            version=version,
            status=VersionStatus.SUNSET,
            release_date=datetime.utcnow()
        )
        
        stable_info = APIVersionInfo(
            version=version,
            status=VersionStatus.STABLE,
            release_date=datetime.utcnow()
        )
        
        assert deprecated_info.is_deprecated()
        assert sunset_info.is_deprecated()
        assert sunset_info.is_sunset()
        assert not stable_info.is_deprecated()

    def test_sunset_date_calculation(self):
        """Test sunset date calculations."""
        version = SemanticVersion.parse("1.0.0")
        sunset_date = datetime.utcnow() + timedelta(days=30)
        
        info = APIVersionInfo(
            version=version,
            status=VersionStatus.DEPRECATED,
            release_date=datetime.utcnow(),
            sunset_date=sunset_date
        )
        
        days_left = info.days_until_sunset()
        assert days_left is not None
        assert 29 <= days_left <= 30  # Account for timing differences