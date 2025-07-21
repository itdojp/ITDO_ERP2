"""API versioning system with semantic versioning and backward compatibility."""

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from dataclasses import dataclass, field

from fastapi import Request, HTTPException, status
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field, validator


class VersionStatus(str, Enum):
    """API version status."""
    STABLE = "stable"
    BETA = "beta"
    ALPHA = "alpha"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


class BreakingChangeType(str, Enum):
    """Types of breaking changes."""
    FIELD_REMOVED = "field_removed"
    FIELD_TYPE_CHANGED = "field_type_changed"
    ENDPOINT_REMOVED = "endpoint_removed"
    REQUIRED_FIELD_ADDED = "required_field_added"
    BEHAVIOR_CHANGED = "behavior_changed"
    AUTHENTICATION_CHANGED = "authentication_changed"


@dataclass
class SemanticVersion:
    """Semantic version implementation following semver.org."""
    
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    def __post_init__(self):
        """Validate version components."""
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Version numbers cannot be negative")
    
    @classmethod
    def parse(cls, version_string: str) -> "SemanticVersion":
        """Parse version string into SemanticVersion object."""
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        match = re.match(pattern, version_string)
        
        if not match:
            raise ValueError(f"Invalid semantic version: {version_string}")
        
        major, minor, patch, prerelease, build = match.groups()
        
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease,
            build=build
        )
    
    def __str__(self) -> str:
        """String representation of version."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def __lt__(self, other: "SemanticVersion") -> bool:
        """Less than comparison."""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        
        # Handle prerelease comparison
        if self.prerelease is None and other.prerelease is not None:
            return False
        if self.prerelease is not None and other.prerelease is None:
            return True
        if self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease
        
        return False
    
    def __eq__(self, other: "SemanticVersion") -> bool:
        """Equality comparison."""
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )
    
    def __le__(self, other: "SemanticVersion") -> bool:
        """Less than or equal comparison."""
        return self < other or self == other
    
    def __gt__(self, other: "SemanticVersion") -> bool:
        """Greater than comparison."""
        return not self <= other
    
    def __ge__(self, other: "SemanticVersion") -> bool:
        """Greater than or equal comparison."""
        return not self < other
    
    def is_compatible_with(self, other: "SemanticVersion") -> bool:
        """Check if versions are compatible (same major version)."""
        return self.major == other.major
    
    def increment_major(self) -> "SemanticVersion":
        """Increment major version (breaking changes)."""
        return SemanticVersion(self.major + 1, 0, 0)
    
    def increment_minor(self) -> "SemanticVersion":
        """Increment minor version (new features)."""
        return SemanticVersion(self.major, self.minor + 1, 0)
    
    def increment_patch(self) -> "SemanticVersion":
        """Increment patch version (bug fixes)."""
        return SemanticVersion(self.major, self.minor, self.patch + 1)


@dataclass
class BreakingChange:
    """Breaking change documentation."""
    
    change_type: BreakingChangeType
    description: str
    affected_endpoints: List[str]
    migration_guide: str
    introduced_in_version: str
    removed_in_version: Optional[str] = None


@dataclass
class APIVersionInfo:
    """API version information."""
    
    version: SemanticVersion
    status: VersionStatus
    release_date: datetime
    sunset_date: Optional[datetime] = None
    description: str = ""
    breaking_changes: List[BreakingChange] = field(default_factory=list)
    changelog: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    
    def is_deprecated(self) -> bool:
        """Check if version is deprecated."""
        return self.status in [VersionStatus.DEPRECATED, VersionStatus.SUNSET]
    
    def is_sunset(self) -> bool:
        """Check if version is sunset."""
        return self.status == VersionStatus.SUNSET
    
    def days_until_sunset(self) -> Optional[int]:
        """Calculate days until sunset."""
        if not self.sunset_date:
            return None
        
        delta = self.sunset_date - datetime.utcnow()
        return max(0, delta.days)


class APIVersionRegistry:
    """Registry for managing API versions."""
    
    def __init__(self):
        """Initialize version registry."""
        self.versions: Dict[str, APIVersionInfo] = {}
        self.current_version: Optional[SemanticVersion] = None
        self.default_version: Optional[SemanticVersion] = None
    
    def register_version(
        self,
        version: Union[str, SemanticVersion],
        status: VersionStatus = VersionStatus.STABLE,
        description: str = "",
        sunset_date: Optional[datetime] = None,
        breaking_changes: Optional[List[BreakingChange]] = None,
        changelog: Optional[List[str]] = None,
        documentation_url: Optional[str] = None
    ) -> APIVersionInfo:
        """Register a new API version."""
        if isinstance(version, str):
            version = SemanticVersion.parse(version)
        
        version_info = APIVersionInfo(
            version=version,
            status=status,
            release_date=datetime.utcnow(),
            sunset_date=sunset_date,
            description=description,
            breaking_changes=breaking_changes or [],
            changelog=changelog or [],
            documentation_url=documentation_url
        )
        
        version_key = str(version)
        self.versions[version_key] = version_info
        
        # Update current version if this is newer
        if not self.current_version or version > self.current_version:
            self.current_version = version
        
        # Set as default if none set
        if not self.default_version:
            self.default_version = version
        
        return version_info
    
    def get_version(self, version: Union[str, SemanticVersion]) -> Optional[APIVersionInfo]:
        """Get version information."""
        if isinstance(version, SemanticVersion):
            version = str(version)
        return self.versions.get(version)
    
    def get_latest_version(self, include_prerelease: bool = False) -> Optional[APIVersionInfo]:
        """Get the latest stable version."""
        stable_versions = [
            info for info in self.versions.values()
            if info.status == VersionStatus.STABLE or 
            (include_prerelease and info.status in [VersionStatus.BETA, VersionStatus.ALPHA])
        ]
        
        if not stable_versions:
            return None
        
        latest = max(stable_versions, key=lambda x: x.version)
        return latest
    
    def get_compatible_versions(self, version: Union[str, SemanticVersion]) -> List[APIVersionInfo]:
        """Get all compatible versions (same major version)."""
        if isinstance(version, str):
            version = SemanticVersion.parse(version)
        
        compatible = [
            info for info in self.versions.values()
            if info.version.is_compatible_with(version)
        ]
        
        return sorted(compatible, key=lambda x: x.version, reverse=True)
    
    def deprecate_version(
        self,
        version: Union[str, SemanticVersion],
        sunset_date: Optional[datetime] = None,
        migration_version: Optional[Union[str, SemanticVersion]] = None
    ) -> bool:
        """Deprecate a version."""
        version_info = self.get_version(version)
        if not version_info:
            return False
        
        version_info.status = VersionStatus.DEPRECATED
        if sunset_date:
            version_info.sunset_date = sunset_date
        
        return True
    
    def sunset_version(self, version: Union[str, SemanticVersion]) -> bool:
        """Sunset a version (no longer supported)."""
        version_info = self.get_version(version)
        if not version_info:
            return False
        
        version_info.status = VersionStatus.SUNSET
        return True
    
    def list_versions(
        self,
        include_deprecated: bool = True,
        include_sunset: bool = False
    ) -> List[APIVersionInfo]:
        """List all versions."""
        versions = list(self.versions.values())
        
        if not include_deprecated:
            versions = [v for v in versions if not v.is_deprecated()]
        
        if not include_sunset:
            versions = [v for v in versions if not v.is_sunset()]
        
        return sorted(versions, key=lambda x: x.version, reverse=True)


class VersionExtractor:
    """Extract version from HTTP requests."""
    
    @staticmethod
    def from_header(request: Request, header_name: str = "API-Version") -> Optional[str]:
        """Extract version from header."""
        return request.headers.get(header_name)
    
    @staticmethod
    def from_accept_header(request: Request) -> Optional[str]:
        """Extract version from Accept header."""
        accept = request.headers.get("Accept", "")
        # Pattern: application/vnd.myapi.v1+json
        pattern = r'application/vnd\.[\w-]+\.v(\d+(?:\.\d+(?:\.\d+)?)?)'
        match = re.search(pattern, accept)
        return match.group(1) if match else None
    
    @staticmethod
    def from_query_param(request: Request, param_name: str = "version") -> Optional[str]:
        """Extract version from query parameter."""
        return request.query_params.get(param_name)
    
    @staticmethod
    def from_url_path(request: Request) -> Optional[str]:
        """Extract version from URL path."""
        # Pattern: /api/v1.2.3/... or /v1/...
        path = request.url.path
        pattern = r'/v(\d+(?:\.\d+(?:\.\d+)?)?)'
        match = re.search(pattern, path)
        return match.group(1) if match else None


class BackwardCompatibilityLayer:
    """Handle backward compatibility between API versions."""
    
    def __init__(self, registry: APIVersionRegistry):
        """Initialize compatibility layer."""
        self.registry = registry
        self.transformers: Dict[str, Dict[str, Callable]] = {}
    
    def register_transformer(
        self,
        from_version: str,
        to_version: str,
        transformer: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """Register a data transformer between versions."""
        if from_version not in self.transformers:
            self.transformers[from_version] = {}
        self.transformers[from_version][to_version] = transformer
    
    def transform_request(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """Transform request data from one version to another."""
        if from_version == to_version:
            return data
        
        # Direct transformation
        if (from_version in self.transformers and 
            to_version in self.transformers[from_version]):
            return self.transformers[from_version][to_version](data)
        
        # Chain transformations if needed
        return self._chain_transform(data, from_version, to_version)
    
    def transform_response(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """Transform response data from one version to another."""
        # For responses, transform in reverse direction
        return self.transform_request(data, to_version, from_version)
    
    def _chain_transform(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """Chain multiple transformations."""
        # Simple implementation - in practice, would use graph algorithms
        # to find optimal transformation path
        current_data = data
        current_version = from_version
        
        # Find intermediate versions
        from_sem = SemanticVersion.parse(from_version)
        to_sem = SemanticVersion.parse(to_version)
        
        # For now, just return original data if no direct path
        # In production, implement proper transformation chaining
        return data


class DeprecationManager:
    """Manage API deprecation lifecycle."""
    
    def __init__(self, registry: APIVersionRegistry):
        """Initialize deprecation manager."""
        self.registry = registry
        self.notifications: List[Dict[str, Any]] = []
    
    def check_deprecation_warnings(self, version: str) -> List[str]:
        """Check if version has deprecation warnings."""
        version_info = self.registry.get_version(version)
        if not version_info:
            return []
        
        warnings = []
        
        if version_info.is_deprecated():
            warnings.append(f"API version {version} is deprecated")
            
            if version_info.sunset_date:
                days_left = version_info.days_until_sunset()
                if days_left is not None:
                    if days_left == 0:
                        warnings.append(f"API version {version} sunsets today")
                    elif days_left <= 30:
                        warnings.append(f"API version {version} sunsets in {days_left} days")
        
        return warnings
    
    def get_migration_info(self, version: str) -> Dict[str, Any]:
        """Get migration information for deprecated version."""
        version_info = self.registry.get_version(version)
        if not version_info or not version_info.is_deprecated():
            return {}
        
        latest = self.registry.get_latest_version()
        
        return {
            "deprecated_version": version,
            "recommended_version": str(latest.version) if latest else None,
            "sunset_date": version_info.sunset_date.isoformat() if version_info.sunset_date else None,
            "breaking_changes": [
                {
                    "type": change.change_type,
                    "description": change.description,
                    "migration_guide": change.migration_guide
                }
                for change in version_info.breaking_changes
            ],
            "documentation_url": version_info.documentation_url
        }


class VersionedAPIRoute(APIRoute):
    """API route with version support."""
    
    def __init__(
        self,
        path: str,
        endpoint: Callable,
        *,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        deprecated_in: Optional[str] = None,
        removed_in: Optional[str] = None,
        **kwargs
    ):
        """Initialize versioned route."""
        super().__init__(path, endpoint, **kwargs)
        self.min_version = SemanticVersion.parse(min_version) if min_version else None
        self.max_version = SemanticVersion.parse(max_version) if max_version else None
        self.deprecated_in = SemanticVersion.parse(deprecated_in) if deprecated_in else None
        self.removed_in = SemanticVersion.parse(removed_in) if removed_in else None
    
    def matches(self, scope: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Check if route matches the request."""
        match, match_info = super().matches(scope)
        
        if not match:
            return match, match_info
        
        # Add version validation here if needed
        return match, match_info


# Decorator for version-aware endpoints
def versioned(
    min_version: Optional[str] = None,
    max_version: Optional[str] = None,
    deprecated_in: Optional[str] = None,
    removed_in: Optional[str] = None
):
    """Decorator to mark endpoints with version constraints."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Version validation would happen here
            return await func(*args, **kwargs)
        
        # Store version metadata
        wrapper._min_version = min_version
        wrapper._max_version = max_version
        wrapper._deprecated_in = deprecated_in
        wrapper._removed_in = removed_in
        
        return wrapper
    return decorator


# Global version registry instance
version_registry = APIVersionRegistry()

# Initialize with default versions
version_registry.register_version(
    "1.0.0",
    status=VersionStatus.STABLE,
    description="Initial stable release",
    changelog=["Initial API implementation"]
)

version_registry.register_version(
    "1.1.0",
    status=VersionStatus.STABLE,
    description="Feature additions",
    changelog=["Added notification system", "Enhanced security features"]
)

version_registry.register_version(
    "2.0.0-beta.1",
    status=VersionStatus.BETA,
    description="Major version with breaking changes",
    changelog=["GraphQL API", "Microservices architecture", "Breaking: Removed legacy endpoints"]
)


# Middleware for version handling
class APIVersionMiddleware:
    """Middleware to handle API versioning."""
    
    def __init__(
        self,
        app,
        registry: APIVersionRegistry,
        compatibility_layer: BackwardCompatibilityLayer,
        deprecation_manager: DeprecationManager,
        default_version_strategy: str = "latest"  # latest, explicit, header
    ):
        """Initialize version middleware."""
        self.app = app
        self.registry = registry
        self.compatibility_layer = compatibility_layer
        self.deprecation_manager = deprecation_manager
        self.default_version_strategy = default_version_strategy
    
    async def __call__(self, scope, receive, send):
        """Process request with version handling."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract version from request
        request = Request(scope, receive)
        version = self._extract_version(request)
        
        # Validate version
        if version and not self.registry.get_version(version):
            # Invalid version
            response = {
                "type": "http.response.start",
                "status": 400,
                "headers": [[b"content-type", b"application/json"]]
            }
            await send(response)
            
            body = b'{"error": "Invalid API version"}'
            await send({
                "type": "http.response.body",
                "body": body
            })
            return
        
        # Add version info to scope
        scope["api_version"] = version
        scope["version_info"] = self.registry.get_version(version) if version else None
        
        # Check deprecation warnings
        if version:
            warnings = self.deprecation_manager.check_deprecation_warnings(version)
            scope["deprecation_warnings"] = warnings
        
        await self.app(scope, receive, send)
    
    def _extract_version(self, request: Request) -> Optional[str]:
        """Extract version from request."""
        # Try multiple extraction methods
        version = (
            VersionExtractor.from_header(request) or
            VersionExtractor.from_accept_header(request) or
            VersionExtractor.from_query_param(request) or
            VersionExtractor.from_url_path(request)
        )
        
        if not version and self.default_version_strategy == "latest":
            latest = self.registry.get_latest_version()
            version = str(latest.version) if latest else None
        
        return version


# Utility functions
def get_current_version() -> Optional[SemanticVersion]:
    """Get current API version."""
    return version_registry.current_version


def get_version_info(version: Optional[str] = None) -> Optional[APIVersionInfo]:
    """Get version information."""
    if not version:
        latest = version_registry.get_latest_version()
        return latest
    return version_registry.get_version(version)


def is_version_supported(version: str) -> bool:
    """Check if version is supported."""
    version_info = version_registry.get_version(version)
    return version_info is not None and not version_info.is_sunset()


def get_deprecation_info(version: str) -> Dict[str, Any]:
    """Get deprecation information for version."""
    deprecation_manager = DeprecationManager(version_registry)
    return deprecation_manager.get_migration_info(version)