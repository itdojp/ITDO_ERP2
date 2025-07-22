"""
Feature Flag API Endpoints for ITDO ERP
Provides REST API for managing and evaluating feature flags
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.feature_flags import (
    FeatureFlagService,
    FeatureFlagContext,
    FeatureFlagRule,
    FeatureFlagStrategy,
    get_feature_flag_service
)
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()
security = HTTPBearer()

class FeatureFlagRequest(BaseModel):
    """Request model for feature flag evaluation"""
    key: str = Field(..., description="Feature flag key")
    user_id: Optional[str] = Field(None, description="User ID for evaluation context")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    user_roles: Optional[List[str]] = Field(None, description="User roles")
    environment: Optional[str] = Field(None, description="Environment")
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)

class FeatureFlagResponse(BaseModel):
    """Response model for feature flag evaluation"""
    key: str
    enabled: bool
    variant: Optional[str] = None
    evaluation_context: Dict[str, Any]
    timestamp: datetime

class CreateFeatureFlagRequest(BaseModel):
    """Request model for creating feature flags"""
    key: str = Field(..., description="Unique flag key")
    name: str = Field(..., description="Human readable name")
    description: Optional[str] = Field(None, description="Flag description")
    enabled: bool = Field(True, description="Global enable/disable")
    strategy: FeatureFlagStrategy = Field(FeatureFlagStrategy.ALL_OFF)
    percentage: Optional[float] = Field(None, ge=0, le=100, description="Rollout percentage")
    user_ids: Optional[List[str]] = Field(None, description="Allowed user IDs")
    organization_ids: Optional[List[str]] = Field(None, description="Allowed organization IDs")
    roles: Optional[List[str]] = Field(None, description="Required roles")
    environments: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Environment-specific config")

class UpdateFeatureFlagRequest(BaseModel):
    """Request model for updating feature flags"""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    strategy: Optional[FeatureFlagStrategy] = None
    percentage: Optional[float] = Field(None, ge=0, le=100)
    user_ids: Optional[List[str]] = None
    organization_ids: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    environments: Optional[Dict[str, Dict[str, Any]]] = None

class VariantRequest(BaseModel):
    """Request model for A/B testing variants"""
    key: str
    variants: List[str] = Field(default=["A", "B"], description="Available variants")
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)

@router.post("/evaluate", response_model=FeatureFlagResponse)
async def evaluate_feature_flag(
    request: FeatureFlagRequest,
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    Evaluate a feature flag for the current context
    
    This endpoint evaluates whether a feature flag is enabled for the given context.
    The context includes user information, environment, and custom attributes.
    """
    context = FeatureFlagContext(
        user_id=request.user_id or str(current_user.id),
        organization_id=request.organization_id or getattr(current_user, 'organization_id', None),
        user_roles=request.user_roles or getattr(current_user, 'roles', []),
        environment=request.environment,
        custom_attributes=request.custom_attributes
    )
    
    enabled = await service.get_flag(request.key, context)
    
    return FeatureFlagResponse(
        key=request.key,
        enabled=enabled,
        evaluation_context={
            "user_id": context.user_id,
            "organization_id": context.organization_id,
            "environment": context.environment
        },
        timestamp=datetime.utcnow()
    )

@router.post("/variant", response_model=Dict[str, str])
async def get_feature_variant(
    request: VariantRequest,
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    Get A/B testing variant for a feature flag
    
    Returns a consistent variant assignment for the user based on stable hashing.
    Useful for A/B testing and gradual feature rollouts.
    """
    context = FeatureFlagContext(
        user_id=request.user_id or str(current_user.id),
        organization_id=request.organization_id or getattr(current_user, 'organization_id', None),
        custom_attributes=request.custom_attributes
    )
    
    variant = await service.get_variant(request.key, context, request.variants)
    
    return {
        "key": request.key,
        "variant": variant,
        "user_id": context.user_id
    }

@router.get("/flags", response_model=List[Dict[str, Any]])
async def list_feature_flags(
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    List all feature flags
    
    Returns a list of all configured feature flags with their current settings.
    Requires administrative privileges.
    """
    # Check if user has admin privileges
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Administrative privileges required")
    
    flags = await service.list_flags()
    return flags

@router.get("/flags/{flag_key}", response_model=Dict[str, Any])
async def get_feature_flag_status(
    flag_key: str,
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    Get detailed status of a specific feature flag
    
    Returns configuration, statistics, and evaluation history for a flag.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Administrative privileges required")
    
    status = await service.get_flag_status(flag_key)
    if not status:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    return status

@router.post("/flags", response_model=Dict[str, str])
async def create_feature_flag(
    request: CreateFeatureFlagRequest,
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    Create a new feature flag
    
    Creates a new feature flag with the specified configuration.
    Requires administrative privileges.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Administrative privileges required")
    
    # Create rules from request
    rules = []
    
    if request.strategy == FeatureFlagStrategy.PERCENTAGE and request.percentage is not None:
        rules.append(FeatureFlagRule(
            strategy=FeatureFlagStrategy.PERCENTAGE,
            percentage=request.percentage
        ))
    elif request.strategy == FeatureFlagStrategy.USER_LIST and request.user_ids:
        rules.append(FeatureFlagRule(
            strategy=FeatureFlagStrategy.USER_LIST,
            user_ids=request.user_ids
        ))
    elif request.strategy == FeatureFlagStrategy.ORGANIZATION and request.organization_ids:
        rules.append(FeatureFlagRule(
            strategy=FeatureFlagStrategy.ORGANIZATION,
            organization_ids=request.organization_ids
        ))
    elif request.strategy == FeatureFlagStrategy.ROLE_BASED and request.roles:
        rules.append(FeatureFlagRule(
            strategy=FeatureFlagStrategy.ROLE_BASED,
            roles=request.roles
        ))
    
    await service.set_flag(
        key=request.key,
        enabled=request.enabled,
        strategy=request.strategy,
        rules=rules,
        environments=request.environments
    )
    
    return {"message": f"Feature flag '{request.key}' created successfully"}

@router.put("/flags/{flag_key}", response_model=Dict[str, str])
async def update_feature_flag(
    flag_key: str,
    request: UpdateFeatureFlagRequest,
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    Update an existing feature flag
    
    Updates the configuration of an existing feature flag.
    Only provided fields will be updated.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Administrative privileges required")
    
    # Get current flag config
    current_config = await service._get_flag_config(flag_key)
    if not current_config:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    # Update only provided fields
    if request.enabled is not None:
        current_config["enabled"] = request.enabled
    if request.strategy is not None:
        current_config["strategy"] = request.strategy
    if request.environments is not None:
        current_config["environments"] = request.environments
    
    # Update rules based on new parameters
    if any([request.percentage, request.user_ids, request.organization_ids, request.roles]):
        rules = []
        
        if request.percentage is not None:
            rules.append(FeatureFlagRule(
                strategy=FeatureFlagStrategy.PERCENTAGE,
                percentage=request.percentage
            ))
        if request.user_ids is not None:
            rules.append(FeatureFlagRule(
                strategy=FeatureFlagStrategy.USER_LIST,
                user_ids=request.user_ids
            ))
        if request.organization_ids is not None:
            rules.append(FeatureFlagRule(
                strategy=FeatureFlagStrategy.ORGANIZATION,
                organization_ids=request.organization_ids
            ))
        if request.roles is not None:
            rules.append(FeatureFlagRule(
                strategy=FeatureFlagStrategy.ROLE_BASED,
                roles=request.roles
            ))
        
        await service.set_flag(
            key=flag_key,
            enabled=current_config["enabled"],
            strategy=current_config["strategy"],
            rules=rules,
            environments=current_config.get("environments")
        )
    
    return {"message": f"Feature flag '{flag_key}' updated successfully"}

@router.delete("/flags/{flag_key}", response_model=Dict[str, str])
async def delete_feature_flag(
    flag_key: str,
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    Delete a feature flag
    
    Permanently removes a feature flag and all its configuration.
    This action cannot be undone.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Administrative privileges required")
    
    # Check if flag exists
    flag_config = await service._get_flag_config(flag_key)
    if not flag_config:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    await service.delete_flag(flag_key)
    
    return {"message": f"Feature flag '{flag_key}' deleted successfully"}

@router.post("/flags/{flag_key}/rollout", response_model=Dict[str, Any])
async def update_rollout_percentage(
    flag_key: str,
    percentage: float = Body(..., ge=0, le=100, description="Rollout percentage (0-100)"),
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    Update gradual rollout percentage
    
    Updates the rollout percentage for gradual rollout feature flags.
    Useful for progressive feature deployment.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Administrative privileges required")
    
    await service.update_rollout_percentage(flag_key, percentage)
    current_percentage = await service.get_rollout_percentage(flag_key)
    
    return {
        "flag_key": flag_key,
        "previous_percentage": await service.get_rollout_percentage(flag_key),
        "new_percentage": current_percentage,
        "message": f"Rollout percentage updated to {percentage}%"
    }

@router.get("/flags/{flag_key}/rollout", response_model=Dict[str, float])
async def get_rollout_percentage(
    flag_key: str,
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    Get current rollout percentage
    
    Returns the current rollout percentage for a gradual rollout feature flag.
    """
    percentage = await service.get_rollout_percentage(flag_key)
    
    return {
        "flag_key": flag_key,
        "rollout_percentage": percentage
    }

@router.post("/bulk-evaluate", response_model=List[FeatureFlagResponse])
async def bulk_evaluate_feature_flags(
    flag_keys: List[str] = Body(..., description="List of feature flag keys to evaluate"),
    context: Dict[str, Any] = Body(default_factory=dict, description="Evaluation context"),
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """
    Bulk evaluate multiple feature flags
    
    Evaluates multiple feature flags in a single request for improved performance.
    Useful for frontend applications that need multiple flags.
    """
    flag_context = FeatureFlagContext(
        user_id=context.get("user_id") or str(current_user.id),
        organization_id=context.get("organization_id") or getattr(current_user, 'organization_id', None),
        user_roles=context.get("user_roles") or getattr(current_user, 'roles', []),
        environment=context.get("environment"),
        custom_attributes=context.get("custom_attributes", {})
    )
    
    results = []
    
    for flag_key in flag_keys:
        enabled = await service.get_flag(flag_key, flag_context)
        results.append(FeatureFlagResponse(
            key=flag_key,
            enabled=enabled,
            evaluation_context={
                "user_id": flag_context.user_id,
                "organization_id": flag_context.organization_id,
                "environment": flag_context.environment
            },
            timestamp=datetime.utcnow()
        ))
    
    return results