"""Permission inheritance related schemas."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class PermissionDependency(BaseModel):
    """Schema for permission dependency."""

    id: int
    permission_id: int
    permission_code: str
    requires_permission_id: int
    requires_permission_code: str
    is_active: bool = True
    created_at: datetime
    created_by: int


class PermissionDependencyCreate(BaseModel):
    """Schema for creating permission dependency."""

    permission_id: int
    requires_permission_id: int
    is_active: bool = True


class PermissionInheritanceRule(BaseModel):
    """Schema for permission inheritance rule."""

    id: int
    parent_role_id: int
    parent_role_code: str
    child_role_id: int
    child_role_code: str
    inherit_all: bool = True
    selected_permissions: list[str] | None = None
    priority: int = Field(default=50, ge=0, le=100)
    is_active: bool = True
    created_at: datetime
    created_by: int
    updated_at: datetime | None = None
    updated_by: int | None = None


class PermissionInheritanceCreate(BaseModel):
    """Schema for creating inheritance rule."""

    parent_role_id: int
    child_role_id: int
    inherit_all: bool = True
    selected_permissions: list[str] | None = None
    priority: int = Field(default=50, ge=0, le=100)


class PermissionInheritanceUpdate(BaseModel):
    """Schema for updating inheritance rule."""

    inherit_all: bool | None = None
    selected_permissions: list[str] | None = None
    priority: int | None = Field(None, ge=0, le=100)
    is_active: bool | None = None


class InheritanceConflict(BaseModel):
    """Schema for inheritance conflict."""

    permission_code: str
    permission_name: str
    parent1_role_id: int
    parent1_role_code: str
    parent1_grants: bool
    parent2_role_id: int
    parent2_role_code: str
    parent2_grants: bool
    conflict_type: Literal["grant_vs_deny", "different_conditions"]


class InheritanceConflictResolution(BaseModel):
    """Schema for conflict resolution."""

    permission_code: str
    strategy: Literal["deny_wins", "grant_wins", "priority", "manual"]
    manual_decision: bool | None = None  # For manual strategy
    reason: str | None = None


class EffectivePermissionInfo(BaseModel):
    """Schema for effective permission with source information."""

    granted: bool
    source_role_id: int
    source_role_code: str
    inheritance_depth: int
    has_conflicts: bool = False
    conflict_resolution: str | None = None


class InheritanceAuditLog(BaseModel):
    """Schema for inheritance audit log."""

    id: int
    role_id: int
    action: Literal[
        "inheritance_created",
        "inheritance_updated",
        "inheritance_deleted",
        "conflict_resolved",
        "dependency_created",
        "dependency_deleted",
    ]
    details: dict[str, Any]
    performed_by: int
    performed_by_name: str
    performed_at: datetime


class PermissionInheritanceTree(BaseModel):
    """Schema for permission inheritance tree visualization."""

    role_id: int
    role_code: str
    role_name: str
    parents: list["PermissionInheritanceTree"] = []
    children: list["PermissionInheritanceTree"] = []
    direct_permissions: list[str] = []
    inherited_permissions: list[str] = []
    conflicts: list[InheritanceConflict] = []


# Enable forward references
PermissionInheritanceTree.model_rebuild()


class PermissionDependencyGraph(BaseModel):
    """Schema for permission dependency graph."""

    permission_code: str
    permission_name: str
    requires: list["PermissionDependencyGraph"] = []
    required_by: list["PermissionDependencyGraph"] = []
    is_circular: bool = False


# Enable forward references
PermissionDependencyGraph.model_rebuild()