"""Role permission UI schemas."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PermissionCategory(str, Enum):
    """Permission category enumeration."""

    USER_MANAGEMENT = "user_management"
    ORGANIZATION_MANAGEMENT = "organization_management"
    ROLE_MANAGEMENT = "role_management"
    TASK_MANAGEMENT = "task_management"
    SYSTEM_ADMINISTRATION = "system_administration"
    REPORTING = "reporting"
    AUDIT = "audit"


class PermissionDefinition(BaseModel):
    """Single permission definition."""

    code: str = Field(description="Permission code (e.g., 'user.create')")
    name: str = Field(description="Display name")
    description: str = Field(description="Permission description")
    category: PermissionCategory = Field(description="Permission category")
    requires: List[str] = Field(
        default_factory=list, description="Required permissions"
    )
    conflicts_with: List[str] = Field(
        default_factory=list, description="Conflicting permissions"
    )
    is_dangerous: bool = Field(default=False, description="Requires extra confirmation")


class UIPermissionGroup(BaseModel):
    """Group of related permissions for UI display."""

    name: str = Field(description="Group name")
    icon: str = Field(description="Group icon")
    permissions: List[PermissionDefinition] = Field(description="Permissions in group")


class UIPermissionCategory(BaseModel):
    """Permission category for UI display."""

    category: PermissionCategory = Field(description="Category type")
    name: str = Field(description="Category display name")
    description: str = Field(description="Category description")
    icon: str = Field(description="Category icon")
    groups: List[UIPermissionGroup] = Field(description="Permission groups")


class PermissionMatrix(BaseModel):
    """Role permission matrix."""

    role_id: int = Field(description="Role ID")
    role_name: str = Field(description="Role name")
    organization_id: int = Field(description="Organization ID")
    permissions: Dict[str, bool] = Field(
        description="Permission code to enabled mapping"
    )
    last_updated: Optional[datetime] = Field(
        default=None, description="Last update time"
    )
    updated_by: Optional[str] = Field(default=None, description="Last updater name")


class PermissionMatrixUpdate(BaseModel):
    """Update permission matrix request."""

    permissions: Dict[str, bool] = Field(description="Permission changes")


class PermissionInheritanceTree(BaseModel):
    """Permission inheritance tree for a role."""

    role_id: int = Field(description="Role ID")
    role_name: str = Field(description="Role name")
    parent_role_id: Optional[int] = Field(default=None, description="Parent role ID")
    parent_role_name: Optional[str] = Field(
        default=None, description="Parent role name"
    )
    inherited_permissions: Dict[str, bool] = Field(
        description="Permissions inherited from parent"
    )
    own_permissions: Dict[str, bool] = Field(description="Role's own permissions")
    effective_permissions: Dict[str, bool] = Field(
        description="Combined effective permissions"
    )
    children: List["PermissionInheritanceTree"] = Field(
        default_factory=list, description="Child roles"
    )


class PermissionConflict(BaseModel):
    """Permission conflict information."""

    permission_code: str = Field(description="Permission code")
    permission_name: str = Field(description="Permission name")
    source_role_id: int = Field(description="Role providing permission")
    source_role_name: str = Field(description="Role name")
    value: bool = Field(description="Permission value")
    conflict_type: str = Field(description="Type of conflict")
    resolution: str = Field(description="How conflict was resolved")


class RolePermissionUI(BaseModel):
    """Complete UI data for role permissions."""

    categories: List[UIPermissionCategory] = Field(description="Permission categories")
    total_permissions: int = Field(description="Total number of permissions")
    dangerous_permissions: List[str] = Field(
        description="Permission codes requiring confirmation"
    )


class BulkPermissionUpdate(BaseModel):
    """Bulk permission update request."""

    role_permissions: Dict[int, Dict[str, bool]] = Field(
        description="Role ID to permission updates mapping"
    )


class PermissionSearchResult(BaseModel):
    """Permission search result."""

    permission: PermissionDefinition = Field(description="Permission definition")
    category_name: str = Field(description="Category name")
    group_name: str = Field(description="Group name")
    match_score: float = Field(description="Search relevance score")


# Update forward references
PermissionInheritanceTree.model_rebuild()
