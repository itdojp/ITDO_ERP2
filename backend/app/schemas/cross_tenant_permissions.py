"""Cross-tenant permissions schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CrossTenantPermissionRule(BaseModel):
    """Cross-tenant permission rule model."""
    
    id: int
    source_organization_id: int
    target_organization_id: int
    permission_pattern: str = Field(
        ..., 
        description="Permission pattern (e.g., 'read:*', 'user:*', specific permission)"
    )
    rule_type: str = Field(
        default="allow", 
        description="Rule type: allow, deny"
    )
    priority: int = Field(
        default=100, 
        description="Rule priority (higher number = higher priority)"
    )
    is_active: bool = True
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class CrossTenantPermissionRuleCreate(BaseModel):
    """Schema for creating cross-tenant permission rules."""
    
    source_organization_id: int
    target_organization_id: int
    permission_pattern: str = Field(
        ..., 
        description="Permission pattern (e.g., 'read:*', 'user:*', specific permission)"
    )
    rule_type: str = Field(
        default="allow", 
        description="Rule type: allow, deny"
    )
    priority: int = Field(
        default=100, 
        description="Rule priority (higher number = higher priority)"
    )
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class CrossTenantPermissionRuleUpdate(BaseModel):
    """Schema for updating cross-tenant permission rules."""
    
    permission_pattern: Optional[str] = None
    rule_type: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class UserCrossTenantAccess(BaseModel):
    """User's cross-tenant access information."""
    
    user_id: int
    source_organization_id: int
    target_organization_id: int
    allowed_permissions: List[str]
    denied_permissions: List[str]
    effective_permissions: List[str]
    access_level: str = Field(
        description="Access level: full, read_only, restricted, none"
    )
    last_accessed: Optional[datetime] = None

    class Config:
        from_attributes = True


class CrossTenantPermissionCheck(BaseModel):
    """Request for cross-tenant permission check."""
    
    user_id: int
    source_organization_id: int
    target_organization_id: int
    permission: str


class CrossTenantPermissionResult(BaseModel):
    """Result of cross-tenant permission check."""
    
    user_id: int
    source_organization_id: int
    target_organization_id: int
    permission: str
    allowed: bool
    reason: str = Field(description="Reason for allow/deny decision")
    matching_rules: List[CrossTenantPermissionRule] = []


class OrganizationCrossTenantSummary(BaseModel):
    """Summary of organization's cross-tenant permissions."""
    
    organization_id: int
    organization_name: str
    outbound_rules: int = Field(description="Rules granting access to other orgs")
    inbound_rules: int = Field(description="Rules allowing access from other orgs")
    active_cross_tenant_users: int
    total_shared_permissions: int
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


class CrossTenantAuditLog(BaseModel):
    """Cross-tenant permission audit log."""
    
    id: int
    user_id: int
    source_organization_id: int
    target_organization_id: int
    permission: str
    action: str = Field(description="Action: check, grant, deny, revoke")
    result: str = Field(description="Result: allowed, denied")
    rule_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BatchCrossTenantPermissionCheck(BaseModel):
    """Batch cross-tenant permission check request."""
    
    user_id: int
    source_organization_id: int
    target_organization_id: int
    permissions: List[str]


class BatchCrossTenantPermissionResult(BaseModel):
    """Batch cross-tenant permission check result."""
    
    user_id: int
    source_organization_id: int
    target_organization_id: int
    results: List[CrossTenantPermissionResult]
    summary: dict = Field(
        description="Summary with allowed/denied counts"
    )


class CrossTenantPermissionMatrix(BaseModel):
    """Permission matrix for cross-tenant access."""
    
    source_organization_id: int
    target_organizations: List[dict] = Field(
        description="List of target orgs with their permission mappings"
    )
    
    class Config:
        from_attributes = True