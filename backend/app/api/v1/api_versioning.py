"""API versioning management endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.versioning import (
    SemanticVersion,
    VersionStatus,
    APIVersionInfo,
    BreakingChange,
    BreakingChangeType,
    version_registry,
    get_current_version,
    get_version_info,
    is_version_supported,
    get_deprecation_info,
    VersionExtractor,
)
from app.core.sdk_generator import (
    SDKConfiguration,
    SDKGeneratorFactory,
    generate_sdk_for_api,
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class VersionInfoResponse(BaseModel):
    """API version information response."""
    version: str
    status: VersionStatus
    release_date: datetime
    sunset_date: Optional[datetime]
    description: str
    breaking_changes: List[Dict[str, Any]]
    changelog: List[str]
    documentation_url: Optional[str]
    days_until_sunset: Optional[int]

    class Config:
        from_attributes = True


class BreakingChangeCreate(BaseModel):
    """Create breaking change schema."""
    change_type: BreakingChangeType
    description: str = Field(..., max_length=1000)
    affected_endpoints: List[str]
    migration_guide: str = Field(..., max_length=2000)
    introduced_in_version: str
    removed_in_version: Optional[str] = None


class VersionCreate(BaseModel):
    """Create new version schema."""
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$')
    status: VersionStatus = VersionStatus.BETA
    description: str = Field("", max_length=500)
    sunset_date: Optional[datetime] = None
    breaking_changes: List[BreakingChangeCreate] = []
    changelog: List[str] = []
    documentation_url: Optional[str] = None


class VersionUpdate(BaseModel):
    """Update version schema."""
    status: Optional[VersionStatus] = None
    description: Optional[str] = Field(None, max_length=500)
    sunset_date: Optional[datetime] = None
    documentation_url: Optional[str] = None


class DeprecationRequest(BaseModel):
    """Deprecate version request."""
    sunset_date: Optional[datetime] = None
    migration_version: Optional[str] = None
    reason: str = Field(..., max_length=500)


class SDKGenerationRequest(BaseModel):
    """SDK generation request."""
    language: str = Field(..., pattern=r'^(python|typescript|javascript|go|java|csharp|php|ruby)$')
    package_name: str = Field(..., max_length=100)
    version: Optional[str] = None
    api_base_url: Optional[str] = None
    include_models: bool = True
    include_examples: bool = True
    include_tests: bool = True


class CompatibilityCheckRequest(BaseModel):
    """Version compatibility check request."""
    from_version: str
    to_version: str
    endpoint_path: Optional[str] = None


class CompatibilityCheckResponse(BaseModel):
    """Version compatibility check response."""
    compatible: bool
    breaking_changes: List[Dict[str, Any]]
    migration_required: bool
    recommendations: List[str]


@router.get("/versions", response_model=List[VersionInfoResponse])
async def list_versions(
    include_deprecated: bool = True,
    include_sunset: bool = False,
    current_user: User = Depends(get_current_user)
):
    """List all API versions."""
    versions = version_registry.list_versions(
        include_deprecated=include_deprecated,
        include_sunset=include_sunset
    )
    
    return [
        VersionInfoResponse(
            version=str(v.version),
            status=v.status,
            release_date=v.release_date,
            sunset_date=v.sunset_date,
            description=v.description,
            breaking_changes=[
                {
                    "type": bc.change_type,
                    "description": bc.description,
                    "affected_endpoints": bc.affected_endpoints,
                    "migration_guide": bc.migration_guide,
                    "introduced_in_version": bc.introduced_in_version,
                    "removed_in_version": bc.removed_in_version
                }
                for bc in v.breaking_changes
            ],
            changelog=v.changelog,
            documentation_url=v.documentation_url,
            days_until_sunset=v.days_until_sunset()
        )
        for v in versions
    ]


@router.get("/versions/current", response_model=VersionInfoResponse)
async def get_current_api_version():
    """Get current API version."""
    current = get_current_version()
    if not current:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current version defined"
        )
    
    version_info = get_version_info(str(current))
    if not version_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current version info not found"
        )
    
    return VersionInfoResponse(
        version=str(version_info.version),
        status=version_info.status,
        release_date=version_info.release_date,
        sunset_date=version_info.sunset_date,
        description=version_info.description,
        breaking_changes=[
            {
                "type": bc.change_type,
                "description": bc.description,
                "affected_endpoints": bc.affected_endpoints,
                "migration_guide": bc.migration_guide,
                "introduced_in_version": bc.introduced_in_version,
                "removed_in_version": bc.removed_in_version
            }
            for bc in version_info.breaking_changes
        ],
        changelog=version_info.changelog,
        documentation_url=version_info.documentation_url,
        days_until_sunset=version_info.days_until_sunset()
    )


@router.get("/versions/{version}", response_model=VersionInfoResponse)
async def get_version(version: str):
    """Get specific version information."""
    try:
        SemanticVersion.parse(version)  # Validate version format
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid version format"
        )
    
    version_info = get_version_info(version)
    if not version_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    return VersionInfoResponse(
        version=str(version_info.version),
        status=version_info.status,
        release_date=version_info.release_date,
        sunset_date=version_info.sunset_date,
        description=version_info.description,
        breaking_changes=[
            {
                "type": bc.change_type,
                "description": bc.description,
                "affected_endpoints": bc.affected_endpoints,
                "migration_guide": bc.migration_guide,
                "introduced_in_version": bc.introduced_in_version,
                "removed_in_version": bc.removed_in_version
            }
            for bc in version_info.breaking_changes
        ],
        changelog=version_info.changelog,
        documentation_url=version_info.documentation_url,
        days_until_sunset=version_info.days_until_sunset()
    )


@router.post("/versions", response_model=VersionInfoResponse)
async def create_version(
    version_data: VersionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new API version."""
    # Check if user has admin permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        # Validate version format
        semantic_version = SemanticVersion.parse(version_data.version)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid version format: {str(e)}"
        )
    
    # Check if version already exists
    if version_registry.get_version(version_data.version):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Version already exists"
        )
    
    # Convert breaking changes
    breaking_changes = [
        BreakingChange(
            change_type=bc.change_type,
            description=bc.description,
            affected_endpoints=bc.affected_endpoints,
            migration_guide=bc.migration_guide,
            introduced_in_version=bc.introduced_in_version,
            removed_in_version=bc.removed_in_version
        )
        for bc in version_data.breaking_changes
    ]
    
    # Register new version
    version_info = version_registry.register_version(
        version=semantic_version,
        status=version_data.status,
        description=version_data.description,
        sunset_date=version_data.sunset_date,
        breaking_changes=breaking_changes,
        changelog=version_data.changelog,
        documentation_url=version_data.documentation_url
    )
    
    return VersionInfoResponse(
        version=str(version_info.version),
        status=version_info.status,
        release_date=version_info.release_date,
        sunset_date=version_info.sunset_date,
        description=version_info.description,
        breaking_changes=[
            {
                "type": bc.change_type,
                "description": bc.description,
                "affected_endpoints": bc.affected_endpoints,
                "migration_guide": bc.migration_guide,
                "introduced_in_version": bc.introduced_in_version,
                "removed_in_version": bc.removed_in_version
            }
            for bc in version_info.breaking_changes
        ],
        changelog=version_info.changelog,
        documentation_url=version_info.documentation_url,
        days_until_sunset=version_info.days_until_sunset()
    )


@router.put("/versions/{version}", response_model=VersionInfoResponse)
async def update_version(
    version: str,
    update_data: VersionUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update version information."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    version_info = version_registry.get_version(version)
    if not version_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Update fields
    if update_data.status is not None:
        version_info.status = update_data.status
    if update_data.description is not None:
        version_info.description = update_data.description
    if update_data.sunset_date is not None:
        version_info.sunset_date = update_data.sunset_date
    if update_data.documentation_url is not None:
        version_info.documentation_url = update_data.documentation_url
    
    return VersionInfoResponse(
        version=str(version_info.version),
        status=version_info.status,
        release_date=version_info.release_date,
        sunset_date=version_info.sunset_date,
        description=version_info.description,
        breaking_changes=[
            {
                "type": bc.change_type,
                "description": bc.description,
                "affected_endpoints": bc.affected_endpoints,
                "migration_guide": bc.migration_guide,
                "introduced_in_version": bc.introduced_in_version,
                "removed_in_version": bc.removed_in_version
            }
            for bc in version_info.breaking_changes
        ],
        changelog=version_info.changelog,
        documentation_url=version_info.documentation_url,
        days_until_sunset=version_info.days_until_sunset()
    )


@router.post("/versions/{version}/deprecate")
async def deprecate_version(
    version: str,
    deprecation_data: DeprecationRequest,
    current_user: User = Depends(get_current_user)
):
    """Deprecate a version."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    success = version_registry.deprecate_version(
        version=version,
        sunset_date=deprecation_data.sunset_date
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    return {"message": f"Version {version} deprecated successfully"}


@router.post("/versions/{version}/sunset")
async def sunset_version(
    version: str,
    current_user: User = Depends(get_current_user)
):
    """Sunset a version (no longer supported)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    success = version_registry.sunset_version(version)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    return {"message": f"Version {version} sunset successfully"}


@router.get("/versions/{version}/deprecation-info")
async def get_version_deprecation_info(version: str):
    """Get deprecation information for a version."""
    info = get_deprecation_info(version)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found or not deprecated"
        )
    
    return info


@router.post("/versions/compatibility-check", response_model=CompatibilityCheckResponse)
async def check_version_compatibility(
    request_data: CompatibilityCheckRequest
):
    """Check compatibility between two versions."""
    try:
        from_version = SemanticVersion.parse(request_data.from_version)
        to_version = SemanticVersion.parse(request_data.to_version)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid version format: {str(e)}"
        )
    
    # Check if versions exist
    from_info = version_registry.get_version(request_data.from_version)
    to_info = version_registry.get_version(request_data.to_version)
    
    if not from_info or not to_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both versions not found"
        )
    
    # Determine compatibility
    compatible = from_version.is_compatible_with(to_version)
    breaking_changes = []
    recommendations = []
    
    if not compatible:
        # Collect breaking changes between versions
        breaking_changes = [
            {
                "type": bc.change_type,
                "description": bc.description,
                "affected_endpoints": bc.affected_endpoints,
                "migration_guide": bc.migration_guide
            }
            for bc in to_info.breaking_changes
        ]
        
        recommendations = [
            "Review breaking changes carefully",
            "Update client code according to migration guides",
            "Test thoroughly before upgrading"
        ]
    
    return CompatibilityCheckResponse(
        compatible=compatible,
        breaking_changes=breaking_changes,
        migration_required=not compatible,
        recommendations=recommendations
    )


@router.get("/versions/{version}/supported")
async def check_version_support(version: str):
    """Check if a version is still supported."""
    supported = is_version_supported(version)
    
    return {
        "version": version,
        "supported": supported,
        "message": "Version is supported" if supported else "Version is no longer supported"
    }


@router.post("/sdk/generate")
async def generate_sdk(
    request_data: SDKGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate SDK for specified language and version."""
    # Validate language
    if request_data.language not in SDKGeneratorFactory.supported_languages():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: {request_data.language}"
        )
    
    # Use current version if not specified
    version = request_data.version or str(get_current_version())
    if not version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No version specified and no current version available"
        )
    
    # Validate version
    if not is_version_supported(version):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Version {version} is not supported"
        )
    
    try:
        # Create SDK configuration
        config = SDKConfiguration(
            package_name=request_data.package_name,
            version=version,
            language=request_data.language,
            api_base_url=request_data.api_base_url or "http://localhost:8000/api/v1",
            include_models=request_data.include_models,
            include_examples=request_data.include_examples,
            include_tests=request_data.include_tests
        )
        
        # Generate mock OpenAPI spec for demonstration
        # In production, this would come from actual OpenAPI spec
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": version},
            "paths": {},
            "components": {"schemas": {}}
        }
        
        # Generate SDK files
        generated_files = generate_sdk_for_api(openapi_spec, request_data.language, config)
        
        return {
            "message": f"SDK generated successfully for {request_data.language}",
            "version": version,
            "package_name": request_data.package_name,
            "files_generated": len(generated_files),
            "output_directory": config.output_directory
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SDK generation failed: {str(e)}"
        )


@router.get("/sdk/languages")
async def list_supported_languages():
    """List supported SDK languages."""
    return {
        "supported_languages": SDKGeneratorFactory.supported_languages(),
        "message": "List of supported SDK generation languages"
    }


@router.get("/version-detection", include_in_schema=False)
async def detect_version_from_request(request: Request):
    """Detect API version from current request (utility endpoint)."""
    version_header = VersionExtractor.from_header(request)
    version_accept = VersionExtractor.from_accept_header(request)
    version_query = VersionExtractor.from_query_param(request)
    version_path = VersionExtractor.from_url_path(request)
    
    return {
        "detected_versions": {
            "header": version_header,
            "accept_header": version_accept,
            "query_parameter": version_query,
            "url_path": version_path
        },
        "recommended_method": "header",
        "example_header": "API-Version: 1.2.3"
    }