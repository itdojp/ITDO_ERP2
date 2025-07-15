"""Role permission UI service."""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.models.role import Role
from app.models.user import User
from app.schemas.role_permission_ui import (
    PermissionCategory,
    PermissionConflict,
    PermissionDefinition,
    PermissionInheritanceTree,
    PermissionMatrix,
    PermissionMatrixUpdate,
    PermissionSearchResult,
    UIPermissionCategory,
    UIPermissionGroup,
)


class RolePermissionUIService:
    """Role permission UI management service."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self._permission_definitions = self._initialize_permission_definitions()

    def get_permission_definitions(self) -> List[UIPermissionCategory]:
        """Get all permission definitions organized by category."""
        return self._permission_definitions

    def get_role_permission_matrix(
        self, role_id: int, organization_id: int
    ) -> PermissionMatrix:
        """Get permission matrix for a role."""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Get role permissions
        role_permissions = [
            rp.permission.code for rp in role.role_permissions if rp.is_granted
        ]

        # Create permission matrix
        permissions = {}
        for category in self._permission_definitions:
            for group in category.groups:
                for perm_def in group.permissions:
                    permissions[perm_def.code] = perm_def.code in role_permissions

        return PermissionMatrix(
            role_id=role.id,
            role_name=role.name,
            organization_id=organization_id,
            permissions=permissions,
        )

    def update_role_permissions(
        self,
        role_id: int,
        organization_id: int,
        update_data: PermissionMatrixUpdate,
        updater: User,
        enforce_dependencies: bool = False,
    ) -> PermissionMatrix:
        """Update role permissions."""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Permission check
        if not hasattr(updater, "is_superuser") or not updater.is_superuser:
            # Check if user has role management permissions
            # Users need 'role.manage' permission in the role's organization
            if hasattr(updater, "has_permission") and role.organization_id:
                has_permission = updater.has_permission("role.manage", role.organization_id)
                if not has_permission:
                    raise PermissionDenied("ロール権限を更新する権限がありません")
            else:
                raise PermissionDenied("ロール権限を更新する権限がありません")

        # Enforce dependencies if requested
        final_permissions = update_data.permissions.copy()
        if enforce_dependencies:
            final_permissions = self._enforce_permission_dependencies(final_permissions)

        # Update permissions in database using RolePermission model
        from app.models.permission import Permission
        from app.models.role import RolePermission

        for permission_code, enabled in final_permissions.items():
            # Find the permission by code
            permission = self.db.query(Permission).filter(Permission.code == permission_code).first()
            if not permission:
                continue

            # Check if role-permission relationship exists
            role_permission = (
                self.db.query(RolePermission)
                .filter(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission.id
                )
                .first()
            )

            if enabled:
                # Add permission if not exists
                if not role_permission:
                    role_permission = RolePermission(
                        role_id=role_id,
                        permission_id=permission.id
                    )
                    self.db.add(role_permission)
            else:
                # Remove permission if exists
                if role_permission:
                    self.db.delete(role_permission)

        self.db.commit()

        # Return updated matrix
        return self.get_role_permission_matrix(role_id, organization_id)

    def copy_permissions_from_role(
        self,
        source_role_id: int,
        target_role_id: int,
        organization_id: int,
        copier: User,
    ) -> PermissionMatrix:
        """Copy permissions from one role to another."""
        # Permission check - copier needs role management permissions
        if not hasattr(copier, "is_superuser") or not copier.is_superuser:
            # Check if user has role management permissions in the organization
            if hasattr(copier, "has_permission"):
                has_permission = copier.has_permission("role.manage", organization_id)
                if not has_permission:
                    raise PermissionDenied("ロール権限をコピーする権限がありません")
            else:
                raise PermissionDenied("ロール権限をコピーする権限がありません")

        source_matrix = self.get_role_permission_matrix(source_role_id, organization_id)

        # Create update data from source permissions
        update_data = PermissionMatrixUpdate(permissions=source_matrix.permissions)

        return self.update_role_permissions(
            target_role_id, organization_id, update_data, copier
        )

    def get_permission_inheritance_tree(
        self, role_id: int, organization_id: int
    ) -> PermissionInheritanceTree:
        """Get permission inheritance tree for a role."""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Get parent permissions
        inherited_permissions = {}
        parent_role = None
        if role.parent_id:
            parent_role = self.db.query(Role).filter(Role.id == role.parent_id).first()
            if parent_role:
                parent_perms = [
                    rp.permission.code
                    for rp in parent_role.role_permissions
                    if rp.is_granted
                ]
                for perm_code in self._get_all_permission_codes():
                    inherited_permissions[perm_code] = perm_code in parent_perms

        # Get own permissions
        own_permissions = {}
        role_perms = [
            rp.permission.code for rp in role.role_permissions if rp.is_granted
        ]
        for perm_code in self._get_all_permission_codes():
            own_permissions[perm_code] = perm_code in role_perms

        # Calculate effective permissions
        effective_permissions = inherited_permissions.copy()
        effective_permissions.update(own_permissions)

        return PermissionInheritanceTree(
            role_id=role.id,
            role_name=role.name,
            parent_role_id=parent_role.id if parent_role else None,
            parent_role_name=parent_role.name if parent_role else None,
            inherited_permissions=inherited_permissions,
            own_permissions=own_permissions,
            effective_permissions=effective_permissions,
        )

    def bulk_update_permissions(
        self,
        organization_id: int,
        role_permissions: Dict[int, Dict[str, bool]],
        updater: User,
    ) -> List[PermissionMatrix]:
        """Bulk update permissions for multiple roles."""
        if not hasattr(updater, "is_superuser") or not updater.is_superuser:
            # Check if user has role management permissions for bulk operations
            if hasattr(updater, "has_permission"):
                has_permission = updater.has_permission("role.manage", organization_id)
                if not has_permission:
                    raise PermissionDenied("一括権限更新を行う権限がありません")
            else:
                raise PermissionDenied("一括権限更新を行う権限がありません")

        results = []
        for role_id, permissions in role_permissions.items():
            update_data = PermissionMatrixUpdate(permissions=permissions)
            matrix = self.update_role_permissions(
                role_id, organization_id, update_data, updater
            )
            results.append(matrix)

        return results

    def get_effective_permissions(
        self, role_id: int, organization_id: int
    ) -> Dict[str, bool]:
        """Get effective permissions including inheritance."""
        tree = self.get_permission_inheritance_tree(role_id, organization_id)
        return tree.effective_permissions

    def get_permission_ui_structure(self) -> Dict[str, Any]:
        """Get permission structure for UI rendering."""
        categories_data = []
        for category in self._permission_definitions:
            groups_data = []
            for group in category.groups:
                permissions_data = [
                    {
                        "code": perm.code,
                        "name": perm.name,
                        "description": perm.description,
                        "is_dangerous": perm.is_dangerous,
                        "requires": perm.requires,
                    }
                    for perm in group.permissions
                ]
                groups_data.append(
                    {
                        "name": group.name,
                        "icon": group.icon,
                        "permissions": permissions_data,
                    }
                )

            categories_data.append(
                {
                    "name": category.name,
                    "description": category.description,
                    "icon": category.icon,
                    "groups": groups_data,
                }
            )

        return {
            "categories": categories_data,
            "total_permissions": sum(
                len(group.permissions)
                for category in self._permission_definitions
                for group in category.groups
            ),
        }

    def search_permissions(self, query: str) -> List[PermissionSearchResult]:
        """Search permissions by name or code."""
        results = []
        query_lower = query.lower()

        for category in self._permission_definitions:
            for group in category.groups:
                for permission in group.permissions:
                    score = 0.0

                    # Exact matches get highest score
                    if query_lower == permission.code.lower():
                        score = 1.0
                    elif query_lower == permission.name.lower():
                        score = 0.9
                    # Partial matches
                    elif query_lower in permission.code.lower():
                        score = 0.7
                    elif query_lower in permission.name.lower():
                        score = 0.6
                    elif query_lower in permission.description.lower():
                        score = 0.4

                    if score > 0:
                        results.append(
                            PermissionSearchResult(
                                permission=permission,
                                category_name=category.name,
                                group_name=group.name,
                                match_score=score,
                            )
                        )

        # Sort by score descending
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results

    def get_permission_conflicts(
        self, role_id: int, organization_id: int
    ) -> List[PermissionConflict]:
        """Get permission conflicts in inheritance chain."""
        tree = self.get_permission_inheritance_tree(role_id, organization_id)
        conflicts = []

        # Check for conflicts between inherited and own permissions
        for perm_code in tree.inherited_permissions:
            inherited_value = tree.inherited_permissions.get(perm_code, False)
            own_value = tree.own_permissions.get(perm_code)

            if own_value is not None and inherited_value != own_value:
                perm_def = self._get_permission_by_code(perm_code)
                conflicts.append(
                    PermissionConflict(
                        permission_code=perm_code,
                        permission_name=perm_def.name if perm_def else perm_code,
                        source_role_id=tree.parent_role_id or 0,
                        source_role_name=tree.parent_role_name or "Unknown",
                        value=own_value,
                        conflict_type="override",
                        resolution="Own permission takes precedence",
                    )
                )

        return conflicts

    def _initialize_permission_definitions(self) -> List[UIPermissionCategory]:
        """Initialize permission definitions."""
        return [
            UIPermissionCategory(
                category=PermissionCategory.USER_MANAGEMENT,
                name="ユーザー管理",
                description="ユーザーアカウントの管理",
                icon="users",
                groups=[
                    UIPermissionGroup(
                        name="基本操作",
                        icon="user",
                        permissions=[
                            PermissionDefinition(
                                code="user.read",
                                name="ユーザー閲覧",
                                description="ユーザー情報を閲覧する",
                                category=PermissionCategory.USER_MANAGEMENT,
                            ),
                            PermissionDefinition(
                                code="user.create",
                                name="ユーザー作成",
                                description="新しいユーザーを作成する",
                                category=PermissionCategory.USER_MANAGEMENT,
                                requires=["user.read"],
                            ),
                            PermissionDefinition(
                                code="user.update",
                                name="ユーザー更新",
                                description="ユーザー情報を更新する",
                                category=PermissionCategory.USER_MANAGEMENT,
                                requires=["user.read"],
                            ),
                            PermissionDefinition(
                                code="user.delete",
                                name="ユーザー削除",
                                description="ユーザーを削除する",
                                category=PermissionCategory.USER_MANAGEMENT,
                                requires=["user.read"],
                                is_dangerous=True,
                            ),
                        ],
                    ),
                ],
            ),
            UIPermissionCategory(
                category=PermissionCategory.ORGANIZATION_MANAGEMENT,
                name="組織管理",
                description="組織・部門の管理",
                icon="building",
                groups=[
                    UIPermissionGroup(
                        name="組織操作",
                        icon="sitemap",
                        permissions=[
                            PermissionDefinition(
                                code="organization.read",
                                name="組織閲覧",
                                description="組織情報を閲覧する",
                                category=PermissionCategory.ORGANIZATION_MANAGEMENT,
                            ),
                            PermissionDefinition(
                                code="organization.create",
                                name="組織作成",
                                description="新しい組織を作成する",
                                category=PermissionCategory.ORGANIZATION_MANAGEMENT,
                                requires=["organization.read"],
                                is_dangerous=True,
                            ),
                            PermissionDefinition(
                                code="organization.update",
                                name="組織更新",
                                description="組織情報を更新する",
                                category=PermissionCategory.ORGANIZATION_MANAGEMENT,
                                requires=["organization.read"],
                            ),
                        ],
                    ),
                ],
            ),
            UIPermissionCategory(
                category=PermissionCategory.ROLE_MANAGEMENT,
                name="権限管理",
                description="ロールと権限の管理",
                icon="shield",
                groups=[
                    UIPermissionGroup(
                        name="ロール操作",
                        icon="key",
                        permissions=[
                            PermissionDefinition(
                                code="role.read",
                                name="ロール閲覧",
                                description="ロール情報を閲覧する",
                                category=PermissionCategory.ROLE_MANAGEMENT,
                            ),
                            PermissionDefinition(
                                code="role.manage",
                                name="ロール管理",
                                description="ロールと権限を管理する",
                                category=PermissionCategory.ROLE_MANAGEMENT,
                                requires=["role.read"],
                                is_dangerous=True,
                            ),
                        ],
                    ),
                ],
            ),
        ]

    def _get_all_permission_codes(self) -> List[str]:
        """Get all permission codes."""
        codes = []
        for category in self._permission_definitions:
            for group in category.groups:
                for permission in group.permissions:
                    codes.append(permission.code)
        return codes

    def _get_permission_by_code(self, code: str) -> PermissionDefinition | None:
        """Get permission definition by code."""
        for category in self._permission_definitions:
            for group in category.groups:
                for permission in group.permissions:
                    if permission.code == code:
                        return permission
        return None

    def _enforce_permission_dependencies(
        self, permissions: Dict[str, bool]
    ) -> Dict[str, bool]:
        """Enforce permission dependencies."""
        result = permissions.copy()

        for perm_code, enabled in permissions.items():
            if enabled:
                perm_def = self._get_permission_by_code(perm_code)
                if perm_def and perm_def.requires:
                    for required_perm in perm_def.requires:
                        result[required_perm] = True

        return result
