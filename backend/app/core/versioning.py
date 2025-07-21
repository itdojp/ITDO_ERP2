"""API Versioning System for ITDO ERP.

This module provides comprehensive API versioning functionality including:
- URL-based and header-based version detection
- Version validation and compatibility checking
- Deprecation warnings and sunset dates
- OpenAPI schema versioning
- Breaking change detection
- Migration utilities

Usage:
    from app.core.versioning import APIVersionManager
    
    manager = APIVersionManager()
    manager.register_version("v2", {"description": "Version 2 API"})
    manager.deprecate_version("v1", deprecation_date, removal_date)
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import Response
import logging

logger = logging.getLogger(__name__)


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string into semantic version tuple.
    
    Args:
        version_str: Version string like "v1", "v1.2", "v1.2.3", "2.1.0"
        
    Returns:
        Tuple of (major, minor, patch) version numbers
        
    Raises:
        ValueError: If version string format is invalid
    """
    # Remove 'v' prefix if present
    clean_version = version_str.lstrip('v')
    
    # Validate format
    if not re.match(r'^\d+(\.\d+){0,2}$', clean_version):
        raise ValueError(f"Invalid version format: {version_str}")
    
    parts = clean_version.split('.')
    
    # Pad to 3 parts (major.minor.patch)
    while len(parts) < 3:
        parts.append('0')
    
    if len(parts) > 3:
        raise ValueError(f"Version cannot have more than 3 parts: {version_str}")
    
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as e:
        raise ValueError(f"Invalid version numbers in {version_str}: {e}")


def validate_version(version: str, supported_versions: List[str]) -> bool:
    """Validate if a version is supported.
    
    Args:
        version: Version string to validate
        supported_versions: List of supported version strings
        
    Returns:
        True if version is supported, False otherwise
    """
    return version in supported_versions


def get_version_from_request(request: Request) -> str:
    """Extract API version from request URL path or headers.
    
    Priority order:
    1. URL path (/api/v1/*, /api/v2/*)
    2. API-Version header
    3. Default version (v1)
    
    Args:
        request: FastAPI request object
        
    Returns:
        Version string (e.g., "v1", "v2.1")
    """
    # Try to extract from URL path first
    path = request.url.path
    url_version_match = re.search(r'/api/v(\d+(?:\.\d+)?)', path)
    if url_version_match:
        return f"v{url_version_match.group(1)}"
    
    # Try API-Version header
    api_version = request.headers.get("API-Version")
    if api_version:
        return api_version
    
    # Default version
    return "v1"


def generate_deprecation_warning(version: str, deprecation_date: datetime, removal_date: datetime) -> str:
    """Generate a deprecation warning message.
    
    Args:
        version: Deprecated version string
        deprecation_date: When version was deprecated
        removal_date: When version will be removed
        
    Returns:
        Formatted deprecation warning message
    """
    return (
        f"API version {version} is deprecated as of {deprecation_date.strftime('%Y-%m-%d')} "
        f"and will be removed on {removal_date.strftime('%Y-%m-%d')}. "
        f"Please migrate to a newer version."
    )


class VersionInfo:
    """Information about an API version."""
    
    def __init__(
        self,
        version: str,
        description: str = "",
        openapi_schema: Optional[Dict[str, Any]] = None,
        deprecation_date: Optional[datetime] = None,
        removal_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.version = version
        self.description = description
        self.openapi_schema = openapi_schema or {}
        self.deprecation_date = deprecation_date
        self.removal_date = removal_date
        self.metadata = metadata or {}
    
    @property
    def is_deprecated(self) -> bool:
        """Check if this version is deprecated."""
        return self.deprecation_date is not None and datetime.now() >= self.deprecation_date
    
    @property
    def is_removed(self) -> bool:
        """Check if this version should be removed."""
        return self.removal_date is not None and datetime.now() >= self.removal_date
    
    def get_deprecation_header(self) -> str:
        """Get RFC-compliant deprecation header value."""
        if not self.is_deprecated:
            return ""
        
        header_parts = ["true"]
        
        if self.deprecation_date:
            header_parts.append(f'date="{self.deprecation_date.strftime("%a, %d %b %Y %H:%M:%S GMT")}"')
        
        if self.removal_date:
            header_parts.append(f'sunset="{self.removal_date.strftime("%a, %d %b %Y %H:%M:%S GMT")}"')
        
        return "; ".join(header_parts)


class APIVersionManager:
    """Manages API versions, deprecation, and compatibility."""
    
    def __init__(self, default_version: str = "v1"):
        self.default_version = default_version
        self._versions: Dict[str, VersionInfo] = {}
        
        # Register default version
        self.register_version(default_version, {"description": "Default API version"})
    
    @property
    def supported_versions(self) -> List[str]:
        """Get list of supported (non-removed) versions."""
        return [v for v, info in self._versions.items() if not info.is_removed]
    
    def register_version(
        self,
        version: str,
        config: Dict[str, Any]
    ) -> None:
        """Register a new API version.
        
        Args:
            version: Version string (e.g., "v2", "v2.1")
            config: Version configuration including description, schema, etc.
        """
        version_info = VersionInfo(
            version=version,
            description=config.get("description", ""),
            openapi_schema=config.get("openapi_schema"),
            metadata=config.get("metadata", {})
        )
        
        self._versions[version] = version_info
        logger.info(f"Registered API version {version}")
    
    def deprecate_version(
        self,
        version: str,
        deprecation_date: datetime,
        removal_date: datetime
    ) -> None:
        """Mark a version as deprecated.
        
        Args:
            version: Version to deprecate
            deprecation_date: When version was/will be deprecated
            removal_date: When version will be removed
            
        Raises:
            ValueError: If version doesn't exist or dates are invalid
        """
        if version not in self._versions:
            raise ValueError(f"Version {version} not found")
        
        if removal_date <= deprecation_date:
            raise ValueError("Removal date must be after deprecation date")
        
        self._versions[version].deprecation_date = deprecation_date
        self._versions[version].removal_date = removal_date
        
        logger.warning(f"Version {version} deprecated. Removal scheduled for {removal_date}")
    
    def is_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated."""
        if version not in self._versions:
            return False
        return self._versions[version].is_deprecated
    
    def is_supported(self, version: str) -> bool:
        """Check if a version is supported (registered and not removed)."""
        if version not in self._versions:
            return False
        return not self._versions[version].is_removed
    
    def get_deprecation_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get deprecation information for a version."""
        if version not in self._versions or not self._versions[version].is_deprecated:
            return None
        
        info = self._versions[version]
        return {
            "version": version,
            "deprecation_date": info.deprecation_date,
            "removal_date": info.removal_date,
            "warning": generate_deprecation_warning(
                version, info.deprecation_date, info.removal_date
            ) if info.deprecation_date and info.removal_date else None
        }
    
    def get_deprecation_header(self, version: str) -> str:
        """Get RFC-compliant deprecation header for a version."""
        if version not in self._versions:
            return ""
        return self._versions[version].get_deprecation_header()
    
    def is_compatible(self, version1: str, version2: str) -> bool:
        """Check if two versions are compatible.
        
        Compatible versions have the same major version number.
        """
        try:
            v1_parts = parse_version(version1)
            v2_parts = parse_version(version2)
            return v1_parts[0] == v2_parts[0]  # Same major version
        except ValueError:
            return False
    
    def get_openapi_schema(self, version: str) -> Dict[str, Any]:
        """Get OpenAPI schema for a specific version."""
        if version not in self._versions:
            return {}
        return self._versions[version].openapi_schema
    
    def get_docs_url(self, version: str) -> str:
        """Get documentation URL for a specific version."""
        return f"/api/{version}/docs"
    
    def get_version_prefix(self, version: str) -> str:
        """Get URL prefix for a specific version."""
        return f"/api/{version}"
    
    def get_version_routes(self, version: str) -> Dict[str, Any]:
        """Get routes configuration for a specific version."""
        if version not in self._versions:
            return {}
        return self._versions[version].metadata.get("routes", {})
    
    def detect_breaking_changes(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> List[str]:
        """Detect breaking changes between two API schemas.
        
        This is a simplified implementation. In production, you'd want
        a more sophisticated schema comparison tool.
        """
        breaking_changes = []
        
        # Compare paths
        old_paths = set(old_schema.get("paths", {}).keys())
        new_paths = set(new_schema.get("paths", {}).keys())
        
        removed_paths = old_paths - new_paths
        if removed_paths:
            breaking_changes.extend([f"Removed endpoint: {path}" for path in removed_paths])
        
        # Compare response schemas for common paths
        for path in old_paths.intersection(new_paths):
            old_path_schema = old_schema["paths"][path]
            new_path_schema = new_schema["paths"][path]
            
            # Check if response properties were removed
            for method in old_path_schema.keys():
                if method in new_path_schema:
                    old_props = self._extract_response_properties(old_path_schema[method])
                    new_props = self._extract_response_properties(new_path_schema[method])
                    
                    removed_props = old_props - new_props
                    if removed_props:
                        breaking_changes.extend([
                            f"Removed property in {path} {method}: {prop}"
                            for prop in removed_props
                        ])
        
        return breaking_changes
    
    def _extract_response_properties(self, method_schema: Dict[str, Any]) -> set:
        """Extract property names from response schema."""
        properties = set()
        
        responses = method_schema.get("responses", {})
        for response in responses.values():
            content = response.get("content", {})
            for media_type in content.values():
                schema = media_type.get("schema", {})
                props = schema.get("properties", {})
                properties.update(props.keys())
        
        return properties
    
    def generate_migration_guide(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Generate a migration guide between two versions."""
        return {
            "from_version": from_version,
            "to_version": to_version,
            "migration_steps": [
                f"Update API base URL from /api/{from_version} to /api/{to_version}",
                "Review breaking changes in the changelog",
                "Update client code to handle new response formats",
                "Test all integrations with the new version"
            ],
            "breaking_changes": [],  # Would be populated with actual changes
            "new_features": [],      # Would be populated with new features
            "deprecated_features": [] # Would be populated with deprecated features
        }


class VersionValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API versions and block unsupported versions."""
    
    def __init__(self, app, version_manager: Optional[APIVersionManager] = None):
        super().__init__(app)
        self.version_manager = version_manager or APIVersionManager()
    
    async def dispatch(self, request: Request, call_next):
        """Validate API version and process request."""
        # Skip validation for non-API routes
        if not request.url.path.startswith('/api/'):
            return await call_next(request)
        
        # Extract version from request
        version = get_version_from_request(request)
        
        # Validate version
        if not self.version_manager.is_supported(version):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported API version: {version}. "
                       f"Supported versions: {', '.join(self.version_manager.supported_versions)}"
            )
        
        # Add version info to request state
        request.state.api_version = version
        
        return await call_next(request)


class DeprecationWarningMiddleware(BaseHTTPMiddleware):
    """Middleware to add deprecation warnings to responses."""
    
    def __init__(self, app, version_manager: APIVersionManager):
        super().__init__(app)
        self.version_manager = version_manager
    
    async def dispatch(self, request: Request, call_next):
        """Add deprecation headers to responses for deprecated versions."""
        response = await call_next(request)
        
        # Skip for non-API routes
        if not request.url.path.startswith('/api/'):
            return response
        
        # Get version from request
        version = getattr(request.state, 'api_version', None) or get_version_from_request(request)
        
        # Add deprecation headers if version is deprecated
        if self.version_manager.is_deprecated(version):
            deprecation_info = self.version_manager.get_deprecation_info(version)
            if deprecation_info:
                response.headers["Deprecation"] = self.version_manager.get_deprecation_header(version)
                if deprecation_info.get("removal_date"):
                    sunset_date = deprecation_info["removal_date"]
                    response.headers["Sunset"] = sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
                
                # Add warning message
                if deprecation_info.get("warning"):
                    response.headers["Warning"] = f'299 - "{deprecation_info["warning"]}"'
        
        return response


# Global version manager instance
version_manager = APIVersionManager()

# Register commonly used versions
version_manager.register_version("v1", {
    "description": "ITDO ERP API Version 1 - Initial release",
    "openapi_schema": {"version": "1.0.0"}
})

version_manager.register_version("v2", {
    "description": "ITDO ERP API Version 2 - Enhanced features and performance",
    "openapi_schema": {"version": "2.0.0"}
})

# Example: Deprecate v1 (future date - 6 months from now)
# version_manager.deprecate_version(
#     "v1", 
#     datetime.now() + timedelta(days=180),  # Deprecation date
#     datetime.now() + timedelta(days=365)   # Removal date
# )