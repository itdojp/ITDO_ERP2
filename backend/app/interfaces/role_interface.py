"""Role Service Interface for RBAC system integration."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from app.types import OrganizationId, UserId


class PermissionScope(Enum):
    """Permission scope levels."""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    DEPARTMENT = "department"
    PROJECT = "project"
    PERSONAL = "personal"


class RoleType(Enum):
    """Role type classifications."""
    SYSTEM = "system"  # Built-in system roles
    ORGANIZATION = "organization"  # Organization-specific roles
    DEPARTMENT = "department"  # Department-specific roles
    PROJECT = "project"  # Project-specific roles
    CUSTOM = "custom"  # Custom user-defined roles


class PermissionEffect(Enum):
    """Permission effect types."""
    ALLOW = "allow"
    DENY = "deny"


class RoleServiceInterface(ABC):
    """Interface for Role Service used by other services."""

    @abstractmethod
    def get_role(self, role_id: int) -> Optional["RoleInfo"]:
        """Get role by ID."""
        pass

    @abstractmethod
    def get_user_roles(
        self, user_id: UserId, organization_id: Optional[OrganizationId] = None
    ) -> List["RoleInfo"]:
        """Get all roles assigned to a user."""
        pass

    @abstractmethod
    def get_user_permissions(
        self,
        user_id: UserId,
        scope: PermissionScope,
        resource_id: Optional[int] = None
    ) -> List["PermissionInfo"]:
        """Get all permissions for a user in a specific scope."""
        pass

    @abstractmethod
    def user_has_permission(
        self,
        user_id: UserId,
        permission: str,
        scope: PermissionScope,
        resource_id: Optional[int] = None,
    ) -> bool:
        """Check if user has a specific permission."""
        pass

    @abstractmethod
    def assign_role_to_user(
        self,
        user_id: UserId,
        role_id: int,
        scope: PermissionScope,
        resource_id: Optional[int] = None,
        assigned_by: Optional[UserId] = None,
    ) -> bool:
        """Assign role to user."""
        pass

    @abstractmethod
    def revoke_role_from_user(
        self,
        user_id: UserId,
        role_id: int,
        scope: PermissionScope,
        resource_id: Optional[int] = None,
        revoked_by: Optional[UserId] = None,
    ) -> bool:
        """Revoke role from user."""
        pass

    @abstractmethod
    def get_organization_roles(self, organization_id: OrganizationId) -> List["RoleInfo"]:
        """Get all roles available in an organization."""
        pass

    @abstractmethod
    def get_department_roles(self, department_id: int) -> List["RoleInfo"]:
        """Get all roles available in a department."""
        pass


class PermissionValidationMixin:
    """Mixin providing permission validation methods."""

    def validate_permission_format(self, permission: str) -> bool:
        """Validate permission string format (e.g., 'resource.action')."""
        if not permission or not isinstance(permission, str):
            return False

        parts = permission.split(".")
        return len(parts) >= 2 and all(part.isalnum() or "_" in part for part in parts)

    def get_permission_hierarchy(self, permission: str) -> List[str]:
        """Get permission hierarchy (e.g., 'org.dept.read' -> ['org.*', 'org.dept.*'])."""
        if not self.validate_permission_format(permission):
            return []

        parts = permission.split(".")
        hierarchy = []

        for i in range(len(parts) - 1):
            hierarchy.append(".".join(parts[:i+1]) + ".*")

        return hierarchy

    def check_permission_conflicts(
        self, permissions: List["PermissionInfo"]
    ) -> List[Dict[str, Any]]:
        """Check for permission conflicts (allow vs deny)."""
        conflicts = []
        permission_map = {}

        for perm in permissions:
            key = f"{perm.permission}:{perm.scope.value}:{perm.resource_id or 'global'}"
            if key not in permission_map:
                permission_map[key] = []
            permission_map[key].append(perm)

        for key, perms in permission_map.items():
            if len(perms) > 1:
                effects = set(p.effect for p in perms)
                if len(effects) > 1:  # Has both ALLOW and DENY
                    conflicts.append({
                        "permission": perms[0].permission,
                        "scope": perms[0].scope,
                        "resource_id": perms[0].resource_id,
                        "conflicting_effects": list(effects),
                        "roles": [p.role_id for p in perms],
                    })

        return conflicts

    def resolve_permission_precedence(
        self, permissions: List["PermissionInfo"]
    ) -> Dict[str, "PermissionInfo"]:
        """Resolve permission precedence (DENY wins over ALLOW)."""
        resolved = {}

        for perm in permissions:
            key = f"{perm.permission}:{perm.scope.value}:{perm.resource_id or 'global'}"

            if key not in resolved:
                resolved[key] = perm
            else:
                # DENY takes precedence over ALLOW
                if perm.effect == PermissionEffect.DENY:
                    resolved[key] = perm
                elif resolved[key].effect == PermissionEffect.ALLOW and perm.effect == PermissionEffect.ALLOW:
                    # Keep the more specific permission (higher role priority)
                    if perm.role_priority > resolved[key].role_priority:
                        resolved[key] = perm

        return resolved


# Data Transfer Objects for Role Service integration

class RoleInfo:
    """Role information for service integration."""

    def __init__(
        self,
        id: int,
        name: str,
        description: Optional[str],
        role_type: RoleType,
        scope: PermissionScope,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
        is_active: bool = True,
        priority: int = 0,
        permissions: Optional[List["PermissionInfo"]] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.role_type = role_type
        self.scope = scope
        self.organization_id = organization_id
        self.department_id = department_id
        self.is_active = is_active
        self.priority = priority
        self.permissions = permissions or []

    @property
    def is_system_role(self) -> bool:
        """Check if this is a system role."""
        return self.role_type == RoleType.SYSTEM

    @property
    def is_organization_role(self) -> bool:
        """Check if this is an organization role."""
        return self.role_type == RoleType.ORGANIZATION

    @property
    def is_department_role(self) -> bool:
        """Check if this is a department role."""
        return self.role_type == RoleType.DEPARTMENT

    def can_assign_to_scope(self, scope: PermissionScope, resource_id: Optional[int] = None) -> bool:
        """Check if role can be assigned to a specific scope."""
        if self.scope == PermissionScope.GLOBAL:
            return True
        elif self.scope == PermissionScope.ORGANIZATION:
            return scope in [PermissionScope.ORGANIZATION, PermissionScope.DEPARTMENT, PermissionScope.PROJECT]
        elif self.scope == PermissionScope.DEPARTMENT:
            return scope in [PermissionScope.DEPARTMENT, PermissionScope.PROJECT]
        elif self.scope == PermissionScope.PROJECT:
            return scope == PermissionScope.PROJECT
        else:
            return False


class PermissionInfo:
    """Permission information for service integration."""

    def __init__(
        self,
        permission: str,
        effect: PermissionEffect,
        scope: PermissionScope,
        resource_id: Optional[int] = None,
        role_id: Optional[int] = None,
        role_name: Optional[str] = None,
        role_priority: int = 0,
        conditions: Optional[Dict[str, Any]] = None,
    ):
        self.permission = permission
        self.effect = effect
        self.scope = scope
        self.resource_id = resource_id
        self.role_id = role_id
        self.role_name = role_name
        self.role_priority = role_priority
        self.conditions = conditions or {}

    @property
    def is_allow(self) -> bool:
        """Check if this is an ALLOW permission."""
        return self.effect == PermissionEffect.ALLOW

    @property
    def is_deny(self) -> bool:
        """Check if this is a DENY permission."""
        return self.effect == PermissionEffect.DENY

    def matches_permission(self, permission: str) -> bool:
        """Check if this permission matches or covers the given permission."""
        if self.permission == permission:
            return True

        # Check wildcard permissions
        if self.permission.endswith("*"):
            prefix = self.permission[:-1]
            return permission.startswith(prefix)

        return False

    def applies_to_resource(self, resource_id: Optional[int]) -> bool:
        """Check if this permission applies to the given resource."""
        return self.resource_id is None or self.resource_id == resource_id


class RoleAssignment:
    """Role assignment information."""

    def __init__(
        self,
        user_id: UserId,
        role_id: int,
        scope: PermissionScope,
        resource_id: Optional[int] = None,
        assigned_by: Optional[UserId] = None,
        assigned_at: Optional[str] = None,
        expires_at: Optional[str] = None,
        is_active: bool = True,
    ):
        self.user_id = user_id
        self.role_id = role_id
        self.scope = scope
        self.resource_id = resource_id
        self.assigned_by = assigned_by
        self.assigned_at = assigned_at
        self.expires_at = expires_at
        self.is_active = is_active

    @property
    def is_expired(self) -> bool:
        """Check if the assignment is expired."""
        if not self.expires_at:
            return False

        from datetime import datetime
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expires
        except (ValueError, TypeError):
            return False

    @property
    def is_valid(self) -> bool:
        """Check if the assignment is valid (active and not expired)."""
        return self.is_active and not self.is_expired


# Integration events for Role Service

class RoleEvent:
    """Base class for role events."""

    def __init__(self, event_type: str, role_id: int):
        self.event_type = event_type
        self.role_id = role_id


class RoleAssignedEvent(RoleEvent):
    """Event fired when role is assigned to user."""

    def __init__(
        self,
        role_id: int,
        user_id: UserId,
        scope: PermissionScope,
        resource_id: Optional[int] = None
    ):
        super().__init__("role_assigned", role_id)
        self.user_id = user_id
        self.scope = scope
        self.resource_id = resource_id


class RoleRevokedEvent(RoleEvent):
    """Event fired when role is revoked from user."""

    def __init__(
        self,
        role_id: int,
        user_id: UserId,
        scope: PermissionScope,
        resource_id: Optional[int] = None
    ):
        super().__init__("role_revoked", role_id)
        self.user_id = user_id
        self.scope = scope
        self.resource_id = resource_id


class RoleCreatedEvent(RoleEvent):
    """Event fired when new role is created."""

    def __init__(self, role_id: int, organization_id: Optional[OrganizationId] = None):
        super().__init__("role_created", role_id)
        self.organization_id = organization_id


class RoleDeletedEvent(RoleEvent):
    """Event fired when role is deleted."""

    def __init__(self, role_id: int, organization_id: Optional[OrganizationId] = None):
        super().__init__("role_deleted", role_id)
        self.organization_id = organization_id


class PermissionChangedEvent(RoleEvent):
    """Event fired when role permissions are changed."""

    def __init__(
        self,
        role_id: int,
        added_permissions: List[str] = None,
        removed_permissions: List[str] = None
    ):
        super().__init__("permission_changed", role_id)
        self.added_permissions = added_permissions or []
        self.removed_permissions = removed_permissions or []


# Predefined system roles and permissions

class SystemRoles:
    """Predefined system roles."""

    SUPER_ADMIN = "system.super_admin"
    ORG_ADMIN = "system.org_admin"
    DEPT_MANAGER = "system.dept_manager"
    PROJECT_MANAGER = "system.project_manager"
    USER = "system.user"
    VIEWER = "system.viewer"


class SystemPermissions:
    """Predefined system permissions."""

    # Organization permissions
    ORG_CREATE = "organizations.create"
    ORG_READ = "organizations.read"
    ORG_UPDATE = "organizations.update"
    ORG_DELETE = "organizations.delete"
    ORG_MANAGE = "organizations.manage"

    # Department permissions
    DEPT_CREATE = "departments.create"
    DEPT_READ = "departments.read"
    DEPT_UPDATE = "departments.update"
    DEPT_DELETE = "departments.delete"
    DEPT_MANAGE = "departments.manage"

    # User permissions
    USER_CREATE = "users.create"
    USER_READ = "users.read"
    USER_UPDATE = "users.update"
    USER_DELETE = "users.delete"
    USER_MANAGE = "users.manage"

    # Role permissions
    ROLE_CREATE = "roles.create"
    ROLE_READ = "roles.read"
    ROLE_UPDATE = "roles.update"
    ROLE_DELETE = "roles.delete"
    ROLE_ASSIGN = "roles.assign"
    ROLE_REVOKE = "roles.revoke"

    # Project permissions
    PROJECT_CREATE = "projects.create"
    PROJECT_READ = "projects.read"
    PROJECT_UPDATE = "projects.update"
    PROJECT_DELETE = "projects.delete"
    PROJECT_MANAGE = "projects.manage"

    # System permissions
    SYSTEM_CONFIG = "system.config"
    SYSTEM_MONITOR = "system.monitor"
    SYSTEM_AUDIT = "system.audit"


# Role-based access control helper functions

def check_role_hierarchy(user_role_priority: int, target_role_priority: int) -> bool:
    """Check if user can assign/revoke roles based on hierarchy."""
    return user_role_priority >= target_role_priority


def get_effective_permissions(role_assignments: List[RoleAssignment]) -> List[PermissionInfo]:
    """Get effective permissions from role assignments."""
    # This would be implemented in the actual Role Service
    # Returns consolidated permissions considering precedence and conflicts
    pass


def validate_role_assignment(
    assigner_roles: List[RoleInfo],
    target_role: RoleInfo,
    scope: PermissionScope,
    resource_id: Optional[int] = None,
) -> bool:
    """Validate if user can assign the given role."""
    # Check if assigner has sufficient privileges
    for role in assigner_roles:
        if role.priority >= target_role.priority:
            if target_role.can_assign_to_scope(scope, resource_id):
                return True
    return False
