"""Permission Matrix implementation for hierarchical role-based access control."""

from enum import Enum
from typing import Any, Dict, Optional, Set, Union

from app.models.user import User


class PermissionLevel(Enum):
    """Permission levels in hierarchical order."""

    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class PermissionMatrix:
    """
    Permission matrix for hierarchical role-based access control.

    Defines permission hierarchy: Admin > Manager > Member > Viewer
    Each level inherits permissions from lower levels.
    """

    # Permission hierarchy (higher index = higher permission)
    PERMISSION_HIERARCHY = [
        PermissionLevel.VIEWER,
        PermissionLevel.MEMBER,
        PermissionLevel.MANAGER,
        PermissionLevel.ADMIN,
    ]

    # Base permissions for each level
    BASE_PERMISSIONS = {
        PermissionLevel.VIEWER: {
            # Read-only access
            "read:own_profile",
            "read:organization_basic",
            "read:department_basic",
            "read:public_announcements",
        },
        PermissionLevel.MEMBER: {
            # Member-level permissions (inherit viewer)
            "read:team_members",
            "read:department_structure",
            "write:own_profile",
            "write:own_timesheet",
            "read:own_tasks",
            "write:own_tasks",
        },
        PermissionLevel.MANAGER: {
            # Manager-level permissions (inherit member)
            "read:team_performance",
            "read:department_reports",
            "write:team_assignments",
            "write:team_schedules",
            "read:user_profiles",
            "write:user_profiles",
            "read:department_users",
            "write:department_users",
            "read:role_assignments",
            "write:role_assignments",
        },
        PermissionLevel.ADMIN: {
            # Admin-level permissions (inherit manager)
            "read:system_settings",
            "write:system_settings",
            "read:audit_logs",
            "write:audit_logs",
            "read:all_organizations",
            "write:all_organizations",
            "read:all_departments",
            "write:all_departments",
            "read:all_users",
            "write:all_users",
            "read:all_roles",
            "write:all_roles",
            "delete:organizations",
            "delete:departments",
            "delete:users",
            "delete:roles",
            "admin:system",
            "admin:organizations",
            "admin:departments",
            "admin:users",
            "admin:roles",
        },
    }

    # Context-specific permissions
    CONTEXT_PERMISSIONS = {
        "organization": {
            PermissionLevel.VIEWER: {
                "org:read:basic",
                "org:read:structure",
            },
            PermissionLevel.MEMBER: {
                "org:read:members",
                "org:read:departments",
            },
            PermissionLevel.MANAGER: {
                "org:read:reports",
                "org:write:members",
                "org:write:departments",
            },
            PermissionLevel.ADMIN: {
                "org:read:all",
                "org:write:all",
                "org:delete:all",
                "org:admin:all",
            },
        },
        "department": {
            PermissionLevel.VIEWER: {
                "dept:read:basic",
                "dept:read:structure",
            },
            PermissionLevel.MEMBER: {
                "dept:read:members",
                "dept:read:tasks",
            },
            PermissionLevel.MANAGER: {
                "dept:read:reports",
                "dept:write:members",
                "dept:write:tasks",
                "dept:write:structure",
            },
            PermissionLevel.ADMIN: {
                "dept:read:all",
                "dept:write:all",
                "dept:delete:all",
                "dept:admin:all",
            },
        },
    }

    def __init__(self) -> None:
        """Initialize permission matrix."""
        self._permission_cache: Dict[str, Set[str]] = {}
        self._build_permission_cache()

    def _build_permission_cache(self) -> None:
        """Build permission cache for efficient lookups."""
        for level in self.PERMISSION_HIERARCHY:
            permissions = set()

            # Add permissions from current level and all lower levels
            for lower_level in self.PERMISSION_HIERARCHY:
                if self._is_level_lower_or_equal(lower_level, level):
                    permissions.update(self.BASE_PERMISSIONS.get(lower_level, set()))

            self._permission_cache[level.value] = permissions

    def _is_level_lower_or_equal(
        self, level1: PermissionLevel, level2: PermissionLevel
    ) -> bool:
        """Check if level1 is lower than or equal to level2."""
        return self.PERMISSION_HIERARCHY.index(
            level1
        ) <= self.PERMISSION_HIERARCHY.index(level2)

    def get_permissions_for_level(self, level: Union[str, PermissionLevel]) -> Set[str]:
        """
        Get all permissions for a specific level (including inherited).

        Args:
            level: Permission level (string or enum)

        Returns:
            Set of permissions for the level
        """
        if isinstance(level, str):
            level = PermissionLevel(level)

        return self._permission_cache.get(level.value, set()).copy()

    def get_context_permissions(
        self, level: Union[str, PermissionLevel], context: str
    ) -> Set[str]:
        """
        Get context-specific permissions for a level.

        Args:
            level: Permission level
            context: Context (organization, department, etc.)

        Returns:
            Set of context-specific permissions
        """
        if isinstance(level, str):
            level = PermissionLevel(level)

        context_perms = self.CONTEXT_PERMISSIONS.get(context, {})
        permissions = set()

        # Add permissions from current level and all lower levels
        for lower_level in self.PERMISSION_HIERARCHY:
            if self._is_level_lower_or_equal(lower_level, level):
                permissions.update(context_perms.get(lower_level, set()))

        return permissions

    def has_permission(
        self,
        user_level: Union[str, PermissionLevel],
        permission: str,
        context: Optional[str] = None,
    ) -> bool:
        """
        Check if a user level has a specific permission.

        Args:
            user_level: User's permission level
            permission: Permission to check
            context: Optional context for context-specific permissions

        Returns:
            True if user has permission, False otherwise
        """
        if isinstance(user_level, str):
            user_level = PermissionLevel(user_level)

        # Check base permissions
        base_permissions = self.get_permissions_for_level(user_level)
        if permission in base_permissions:
            return True

        # Check context-specific permissions
        if context:
            context_permissions = self.get_context_permissions(user_level, context)
            if permission in context_permissions:
                return True

        # Check wildcard permissions
        return self._check_wildcard_permissions(base_permissions, permission)

    def _check_wildcard_permissions(
        self, permissions: Set[str], permission: str
    ) -> bool:
        """Check if any wildcard permissions match the requested permission."""
        for perm in permissions:
            if perm.endswith("*"):
                prefix = perm[:-1]
                if permission.startswith(prefix):
                    return True
            elif perm == "*":
                return True

        return False

    def get_user_effective_level(
        self, user: User, organization_id: int, department_id: Optional[int] = None
    ) -> PermissionLevel:
        """
        Get the effective permission level for a user in a specific context.

        Args:
            user: User object
            organization_id: Organization ID
            department_id: Optional department ID

        Returns:
            Effective permission level
        """
        if user.is_superuser:
            return PermissionLevel.ADMIN

        # Get user's roles in the organization/department
        user_roles = [
            ur
            for ur in user.user_roles
            if ur.organization_id == organization_id
            and (department_id is None or ur.department_id == department_id)
            and not ur.is_expired
        ]

        if not user_roles:
            return PermissionLevel.VIEWER  # Default level

        # Find the highest permission level
        highest_level = PermissionLevel.VIEWER

        for user_role in user_roles:
            role_level = self._get_role_permission_level(user_role.role.code)
            if self.PERMISSION_HIERARCHY.index(
                role_level
            ) > self.PERMISSION_HIERARCHY.index(highest_level):
                highest_level = role_level

        return highest_level

    def _get_role_permission_level(self, role_code: str) -> PermissionLevel:
        """
        Map role code to permission level.

        Args:
            role_code: Role code

        Returns:
            Permission level
        """
        role_level_mapping = {
            "SYSTEM_ADMIN": PermissionLevel.ADMIN,
            "ORG_ADMIN": PermissionLevel.ADMIN,
            "DEPT_MANAGER": PermissionLevel.MANAGER,
            "MANAGER": PermissionLevel.MANAGER,
            "MEMBER": PermissionLevel.MEMBER,
            "USER": PermissionLevel.MEMBER,
            "VIEWER": PermissionLevel.VIEWER,
        }

        return role_level_mapping.get(role_code, PermissionLevel.VIEWER)

    def check_user_permission(
        self,
        user: User,
        permission: str,
        organization_id: int,
        department_id: Optional[int] = None,
        context: Optional[str] = None,
    ) -> bool:
        """
        Check if a user has a specific permission in a given context.

        Args:
            user: User object
            permission: Permission to check
            organization_id: Organization ID
            department_id: Optional department ID
            context: Optional context (organization, department, etc.)

        Returns:
            True if user has permission, False otherwise
        """
        # Get user's effective level
        effective_level = self.get_user_effective_level(
            user, organization_id, department_id
        )

        # Check permission
        return self.has_permission(effective_level, permission, context)

    def get_all_permissions(
        self, level: Union[str, PermissionLevel]
    ) -> Dict[str, Union[Set[str], Dict[str, Set[str]]]]:
        """
        Get all permissions (base + context-specific) for a level.

        Args:
            level: Permission level

        Returns:
            Dictionary with base permissions and context-specific permissions
        """
        if isinstance(level, str):
            level = PermissionLevel(level)

        contexts: Dict[str, Set[str]] = {}
        for context in self.CONTEXT_PERMISSIONS.keys():
            contexts[context] = self.get_context_permissions(level, context)

        result: Dict[str, Union[Set[str], Dict[str, Set[str]]]] = {
            "base": self.get_permissions_for_level(level),
            "contexts": contexts,
        }
        return result

    def validate_permission_hierarchy(self) -> bool:
        """
        Validate that the permission hierarchy is correctly configured.

        Returns:
            True if hierarchy is valid, False otherwise
        """
        # Check that higher levels have at least the same permissions as lower levels
        for i in range(1, len(self.PERMISSION_HIERARCHY)):
            lower_level = self.PERMISSION_HIERARCHY[i - 1]
            higher_level = self.PERMISSION_HIERARCHY[i]

            lower_perms = self.get_permissions_for_level(lower_level)
            higher_perms = self.get_permissions_for_level(higher_level)

            # Higher level should contain all permissions from lower level
            if not lower_perms.issubset(higher_perms):
                return False

        return True

    def get_permission_differences(
        self, level1: Union[str, PermissionLevel], level2: Union[str, PermissionLevel]
    ) -> Dict[str, Set[str]]:
        """
        Get permission differences between two levels.

        Args:
            level1: First permission level
            level2: Second permission level

        Returns:
            Dictionary with permissions unique to each level
        """
        if isinstance(level1, str):
            level1 = PermissionLevel(level1)
        if isinstance(level2, str):
            level2 = PermissionLevel(level2)

        perms1 = self.get_permissions_for_level(level1)
        perms2 = self.get_permissions_for_level(level2)

        return {
            f"{level1.value}_only": perms1 - perms2,
            f"{level2.value}_only": perms2 - perms1,
            "common": perms1 & perms2,
        }

    def generate_permission_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive permission report.

        Returns:
            Dictionary with permission matrix information
        """
        report: Dict[str, Any] = {
            "hierarchy": [level.value for level in self.PERMISSION_HIERARCHY],
            "levels": {},
            "validation": self.validate_permission_hierarchy(),
            "total_permissions": len(set().union(*self._permission_cache.values())),
        }

        for level in self.PERMISSION_HIERARCHY:
            report["levels"][level.value] = {
                "permissions": list(self.get_permissions_for_level(level)),
                "permission_count": len(self.get_permissions_for_level(level)),
                "contexts": {},
            }

            for context in self.CONTEXT_PERMISSIONS.keys():
                context_perms = self.get_context_permissions(level, context)
                report["levels"][level.value]["contexts"][context] = {
                    "permissions": list(context_perms),
                    "permission_count": len(context_perms),
                }

        return report


# Global permission matrix instance
permission_matrix = PermissionMatrix()


def get_permission_matrix() -> PermissionMatrix:
    """Get the global permission matrix instance."""
    return permission_matrix


def check_permission(
    user: User,
    permission: str,
    organization_id: int,
    department_id: Optional[int] = None,
    context: Optional[str] = None,
) -> bool:
    """
    Convenience function to check user permission.

    Args:
        user: User object
        permission: Permission to check
        organization_id: Organization ID
        department_id: Optional department ID
        context: Optional context

    Returns:
        True if user has permission, False otherwise
    """
    return permission_matrix.check_user_permission(
        user, permission, organization_id, department_id, context
    )


def get_user_permissions(
    user: User, organization_id: int, department_id: Optional[int] = None
) -> Dict[str, Union[Set[str], Dict[str, Set[str]]]]:
    """
    Get all permissions for a user in a specific context.

    Args:
        user: User object
        organization_id: Organization ID
        department_id: Optional department ID

    Returns:
        Dictionary with user's permissions
    """
    effective_level = permission_matrix.get_user_effective_level(
        user, organization_id, department_id
    )
    return permission_matrix.get_all_permissions(effective_level)


def get_permission_level(
    user: User, organization_id: int, department_id: Optional[int] = None
) -> PermissionLevel:
    """
    Get user's effective permission level.

    Args:
        user: User object
        organization_id: Organization ID
        department_id: Optional department ID

    Returns:
        Permission level
    """
    return permission_matrix.get_user_effective_level(
        user, organization_id, department_id
    )
