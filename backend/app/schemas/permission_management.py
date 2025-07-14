"""Permission management schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PermissionDetail(BaseModel):
    """Permission detail information."""

    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: str
    is_active: bool
    is_system: bool


class RolePermissionAssignment(BaseModel):
    """Role permission assignment request."""

    role_id: int = Field(..., description="Role ID to assign permissions to")
    permission_ids: List[int] = Field(..., description="List of permission IDs to assign")
    granted_by: Optional[int] = Field(None, description="User ID who grants the permissions")


class UserPermissionOverride(BaseModel):
    """User-specific permission override."""

    user_id: int = Field(..., description="User ID")
    permission_id: int = Field(..., description="Permission ID")
    action: str = Field(..., description="Action: 'grant' or 'revoke'")
    reason: Optional[str] = Field(None, description="Reason for override")
    expires_at: Optional[datetime] = Field(None, description="When the override expires")


class PermissionInheritanceInfo(BaseModel):
    """Information about permission inheritance."""

    permission: PermissionDetail
    source: str = Field(..., description="Source of permission: 'direct', 'role', 'department', 'organization'")
    source_id: Optional[int] = Field(None, description="ID of the source (role_id, department_id, etc.)")
    source_name: Optional[str] = Field(None, description="Name of the source")
    inherited_at: Optional[datetime] = Field(None, description="When the permission was inherited")
    can_override: bool = Field(False, description="Whether this permission can be overridden")


class UserEffectivePermissions(BaseModel):
    """User's effective permissions including inheritance."""

    user_id: int
    direct_permissions: List[PermissionDetail]
    inherited_permissions: List[PermissionInheritanceInfo]
    overridden_permissions: List[UserPermissionOverride]
    all_permission_codes: List[str]
    evaluation_time: datetime = Field(default_factory=datetime.utcnow)


class PermissionAuditLog(BaseModel):
    """Permission change audit log entry."""

    id: int
    user_id: int
    permission_id: int
    action: str = Field(..., description="Action taken: 'granted', 'revoked', 'expired'")
    performed_by: int
    performed_at: datetime
    reason: Optional[str] = None
    previous_state: Optional[dict] = None
    new_state: Optional[dict] = None


class PermissionCheckRequest(BaseModel):
    """Request to check if user has specific permissions."""

    user_id: int
    permission_codes: List[str] = Field(..., description="List of permission codes to check")
    context: Optional[dict] = Field(None, description="Additional context for permission evaluation")


class PermissionCheckResponse(BaseModel):
    """Response for permission check."""

    user_id: int
    results: dict[str, bool] = Field(..., description="Map of permission code to allowed status")
    missing_permissions: List[str] = Field(..., description="List of permissions the user doesn't have")
    evaluation_time: datetime = Field(default_factory=datetime.utcnow)


class PermissionTemplate(BaseModel):
    """Permission template for common role configurations."""

    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionDetail]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PermissionTemplateCreate(BaseModel):
    """Create a new permission template."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    permission_ids: List[int] = Field(..., description="List of permission IDs in this template")
    is_active: bool = Field(True)


class PermissionBulkOperation(BaseModel):
    """Bulk permission operation request."""

    operation: str = Field(..., description="Operation type: 'grant', 'revoke', 'sync'")
    target_type: str = Field(..., description="Target type: 'users', 'roles', 'departments'")
    target_ids: List[int] = Field(..., description="List of target IDs")
    permission_ids: List[int] = Field(..., description="List of permission IDs")
    reason: Optional[str] = Field(None, description="Reason for bulk operation")
    expires_at: Optional[datetime] = Field(None, description="When these permissions expire")


class PermissionBulkOperationResponse(BaseModel):
    """Response for bulk permission operation."""

    operation_id: str
    success_count: int
    failure_count: int
    failures: Optional[List[dict]] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)