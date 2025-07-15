"""Permission inheritance service implementation."""

from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.permission import Permission
from app.models.permission_inheritance import (
    InheritanceAuditLog,
    InheritanceConflictResolution,
    PermissionDependency,
    RoleInheritanceRule,
)
from app.models.role import Role, RolePermission
from app.models.user import User
from app.schemas.permission_inheritance import (
    InheritanceConflict,
    PermissionInheritanceUpdate,
)
from app.schemas.permission_inheritance import (
    InheritanceConflictResolution as ConflictResolutionSchema,
)
from app.schemas.permission_inheritance import (
    PermissionDependency as PermissionDependencySchema,
)
from app.schemas.permission_inheritance import (
    PermissionInheritanceRule as PermissionInheritanceRuleSchema,
)


class PermissionInheritanceService:
    """Service for managing permission inheritance and dependencies."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    def create_inheritance_rule(
        self,
        parent_role_id: int,
        child_role_id: int,
        creator: User,
        db: Session,
        inherit_all: bool = True,
        selected_permissions: list[str] | None = None,
        priority: int = 50,
    ) -> PermissionInheritanceRuleSchema:
        """Create a new inheritance rule."""
        # Validate roles exist
        parent_role = db.query(Role).filter(Role.id == parent_role_id).first()
        child_role = db.query(Role).filter(Role.id == child_role_id).first()

        if not parent_role or not child_role:
            raise NotFound("Parent or child role not found")

        # Check if roles are in same organization
        if parent_role.organization_id != child_role.organization_id:
            raise BusinessLogicError(
                "Inheritance can only be created between roles in the same organization"
            )

        # Prevent self-inheritance
        if parent_role_id == child_role_id:
            raise BusinessLogicError("Role cannot inherit from itself")

        # Check for circular inheritance
        if self._would_create_circular_inheritance(parent_role_id, child_role_id, db):
            raise BusinessLogicError("Circular inheritance detected")

        # Check permissions
        if not creator.is_superuser and not self._can_manage_role_inheritance(
            creator, parent_role, child_role
        ):
            raise PermissionDenied(
                "Insufficient permissions to create inheritance rule"
            )

        # Create rule
        rule = RoleInheritanceRule(
            parent_role_id=parent_role_id,
            child_role_id=child_role_id,
            inherit_all=inherit_all,
            selected_permissions=selected_permissions if not inherit_all else None,
            priority=priority,
            created_by=creator.id,
        )

        db.add(rule)
        db.commit()
        db.refresh(rule)

        # Log the creation
        self._log_inheritance_action(
            child_role_id,
            "inheritance_created",
            {
                "parent_role_id": parent_role_id,
                "inherit_all": inherit_all,
                "selected_permissions": selected_permissions,
                "priority": priority,
            },
            creator.id,
            db,
        )

        return PermissionInheritanceRuleSchema(
            id=rule.id,
            parent_role_id=rule.parent_role_id,
            parent_role_code=parent_role.code,
            child_role_id=rule.child_role_id,
            child_role_code=child_role.code,
            inherit_all=rule.inherit_all,
            selected_permissions=rule.selected_permissions,
            priority=rule.priority,
            is_active=rule.is_active,
            created_at=rule.created_at,
            created_by=rule.created_by,
            updated_at=rule.updated_at,
            updated_by=rule.updated_by,
        )

    def _would_create_circular_inheritance(
        self, parent_role_id: int, child_role_id: int, db: Session
    ) -> bool:
        """Check if creating inheritance would create a circular dependency."""
        # Check if parent_role_id can reach child_role_id through inheritance chain
        # If it can, then adding child_role_id -> parent_role_id would create a cycle
        visited = set()

        def has_path_to_target(current_role_id: int, target_role_id: int) -> bool:
            if current_role_id in visited:
                return False
            if current_role_id == target_role_id:
                return True

            visited.add(current_role_id)

            # Check all roles that current_role inherits from (parent roles)
            parent_rules = (
                db.query(RoleInheritanceRule)
                .filter(
                    and_(
                        RoleInheritanceRule.child_role_id == current_role_id,
                        RoleInheritanceRule.is_active,
                    )
                )
                .all()
            )

            for rule in parent_rules:
                if has_path_to_target(rule.parent_role_id, target_role_id):
                    return True

            return False

        # If parent_role_id has a path to child_role_id, creating
        # child_role_id -> parent_role_id would create a cycle
        return has_path_to_target(parent_role_id, child_role_id)

    def create_permission_dependency(
        self,
        permission_id: int,
        requires_permission_id: int,
        creator: User,
        db: Session,
    ) -> PermissionDependencySchema:
        """Create a permission dependency."""
        # Validate permissions exist
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        required_permission = (
            db.query(Permission).filter(Permission.id == requires_permission_id).first()
        )

        if not permission or not required_permission:
            raise NotFound("Permission not found")

        # Prevent self-dependency
        if permission_id == requires_permission_id:
            raise BusinessLogicError("Permission cannot depend on itself")

        # Check for circular dependencies
        if self._would_create_circular_dependency(
            permission_id, requires_permission_id, db
        ):
            raise BusinessLogicError("Circular dependency detected")

        # Check permissions
        if not creator.is_superuser:
            raise PermissionDenied("Only superusers can create permission dependencies")

        # Create dependency
        dependency = PermissionDependency(
            permission_id=permission_id,
            requires_permission_id=requires_permission_id,
            created_by=creator.id,
        )

        db.add(dependency)
        db.commit()
        db.refresh(dependency)

        return PermissionDependencySchema(
            id=dependency.id,
            permission_id=dependency.permission_id,
            permission_code=permission.code,
            requires_permission_id=dependency.requires_permission_id,
            requires_permission_code=required_permission.code,
            is_active=dependency.is_active,
            created_at=dependency.created_at,
            created_by=dependency.created_by,
        )

    def _would_create_circular_dependency(
        self, permission_id: int, requires_permission_id: int, db: Session
    ) -> bool:
        """Check if creating dependency would create a circular dependency."""
        visited = set()

        def has_path_to_permission(current_permission_id: int) -> bool:
            if current_permission_id in visited:
                return False
            if current_permission_id == permission_id:
                return True

            visited.add(current_permission_id)

            # Check all dependencies of current permission
            dependencies = (
                db.query(PermissionDependency)
                .filter(
                    and_(
                        PermissionDependency.requires_permission_id
                        == current_permission_id,
                        PermissionDependency.is_active,
                    )
                )
                .all()
            )

            for dep in dependencies:
                if has_path_to_permission(dep.permission_id):
                    return True

            return False

        return has_path_to_permission(requires_permission_id)

    def get_all_permission_dependencies(self, permission_id: int) -> list[Permission]:
        """Get all dependencies (direct and transitive) for a permission."""
        all_dependencies = set()
        visited = set()


        def collect_dependencies(perm_id: int) -> None:

        def collect_dependencies(perm_id: int):

            if perm_id in visited:
                return
            visited.add(perm_id)

            dependencies = (
                self.db.query(PermissionDependency)
                .filter(
                    and_(
                        PermissionDependency.permission_id == perm_id,
                        PermissionDependency.is_active,
                    )
                )
                .all()
            )

            for dep in dependencies:
                all_dependencies.add(dep.requires_permission_id)
                collect_dependencies(dep.requires_permission_id)

        collect_dependencies(permission_id)

        return (
            self.db.query(Permission).filter(Permission.id.in_(all_dependencies)).all()
        )

    def get_inheritance_conflicts(self, role_id: int) -> list[InheritanceConflict]:
        """Get inheritance conflicts for a role."""

        conflicts: list[InheritanceConflict] = []

        conflicts = []


        # Get all parent roles
        parent_rules = (
            self.db.query(RoleInheritanceRule)
            .filter(
                and_(
                    RoleInheritanceRule.child_role_id == role_id,
                    RoleInheritanceRule.is_active,
                )
            )
            .all()
        )

        if len(parent_rules) < 2:
            return conflicts

        # Check for conflicts between parent permissions
        for i, rule1 in enumerate(parent_rules):
            for rule2 in parent_rules[i + 1 :]:
                role1_perms = self._get_role_permissions_map(rule1.parent_role_id)
                role2_perms = self._get_role_permissions_map(rule2.parent_role_id)

                # Find conflicting permissions
                common_perms = set(role1_perms.keys()) & set(role2_perms.keys())
                for perm_code in common_perms:
                    if role1_perms[perm_code] != role2_perms[perm_code]:
                        permission = (
                            self.db.query(Permission)
                            .filter(Permission.code == perm_code)
                            .first()
                        )
                        if permission:
                            conflicts.append(
                                InheritanceConflict(
                                    permission_code=perm_code,
                                    permission_name=permission.name,
                                    parent1_role_id=rule1.parent_role_id,
                                    parent1_role_code=rule1.parent_role.code,
                                    parent1_grants=role1_perms[perm_code],
                                    parent2_role_id=rule2.parent_role_id,
                                    parent2_role_code=rule2.parent_role.code,
                                    parent2_grants=role2_perms[perm_code],
                                    conflict_type="grant_vs_deny",
                                )
                            )

        return conflicts

    def _get_role_permissions_map(self, role_id: int) -> dict[str, bool]:
        """Get role permissions as a map of permission code to granted status."""
        role_permissions = (
            self.db.query(RolePermission)
            .join(Permission)
            .filter(RolePermission.role_id == role_id)
            .all()
        )

        return {rp.permission.code: rp.is_granted for rp in role_permissions}

    def resolve_inheritance_conflict(
        self,
        role_id: int,
        resolution: ConflictResolutionSchema,
        resolver: User,
        db: Session,
    ) -> None:
        """Resolve an inheritance conflict."""
        permission = (
            db.query(Permission)
            .filter(Permission.code == resolution.permission_code)
            .first()
        )
        if not permission:
            raise NotFound("Permission not found")

        # Check permissions
        if not resolver.is_superuser:
            raise PermissionDenied("Only superusers can resolve inheritance conflicts")

        # Apply resolution strategy
        if resolution.strategy == "manual":
            final_decision = resolution.manual_decision
        elif resolution.strategy == "deny_wins":
            final_decision = False
        elif resolution.strategy == "grant_wins":
            final_decision = True
        else:  # priority strategy
            # Implement priority-based resolution
            final_decision = self._resolve_by_priority(role_id, permission.id, db)

        # Create or update role permission
        existing_rp = (
            db.query(RolePermission)
            .filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission.id,
                )
            )
            .first()
        )

        if existing_rp:

            existing_rp.is_granted = bool(final_decision)

            existing_rp.is_granted = final_decision

        else:
            rp = RolePermission(
                role_id=role_id,
                permission_id=permission.id,
                is_granted=final_decision,
                granted_by=resolver.id,
            )
            db.add(rp)

        # Record conflict resolution
        conflict_resolution = InheritanceConflictResolution(
            role_id=role_id,
            permission_id=permission.id,
            strategy=resolution.strategy,
            manual_decision=resolution.manual_decision,
            reason=resolution.reason,
            resolved_by=resolver.id,
        )
        db.add(conflict_resolution)

        # Log the resolution
        self._log_inheritance_action(
            role_id,
            "conflict_resolved",
            {
                "permission_code": resolution.permission_code,
                "strategy": resolution.strategy,
                "final_decision": final_decision,
                "reason": resolution.reason,
            },
            resolver.id,
            db,
        )

        db.commit()

    def _resolve_by_priority(
        self, role_id: int, permission_id: int, db: Session
    ) -> bool:
        """Resolve conflict by inheritance rule priority."""
        # Get parent rules sorted by priority (highest first)
        parent_rules = (
            db.query(RoleInheritanceRule)
            .filter(
                and_(
                    RoleInheritanceRule.child_role_id == role_id,
                    RoleInheritanceRule.is_active,
                )
            )
            .order_by(RoleInheritanceRule.priority.desc())
            .all()
        )

        for rule in parent_rules:
            rp = (
                db.query(RolePermission)
                .filter(
                    and_(
                        RolePermission.role_id == rule.parent_role_id,
                        RolePermission.permission_id == permission_id,
                    )
                )
                .first()
            )
            if rp:
                return rp.is_granted

        return False  # Default to deny if no explicit grant

    def get_effective_permissions(self, role_id: int) -> dict[str, bool]:
        """Get effective permissions for a role including inheritance."""
        effective_permissions = {}
        visited_roles = set()


        def collect_permissions(current_role_id: int, depth: int = 0) -> None:

        def collect_permissions(current_role_id: int, depth: int = 0):

            if current_role_id in visited_roles or depth > 10:  # Prevent infinite loops
                return
            visited_roles.add(current_role_id)

            # Get direct permissions
            role_permissions = (
                self.db.query(RolePermission)
                .join(Permission)
                .filter(RolePermission.role_id == current_role_id)
                .all()
            )

            for rp in role_permissions:
                perm_code = rp.permission.code
                if perm_code not in effective_permissions:
                    effective_permissions[perm_code] = rp.is_granted

            # Get inherited permissions
            parent_rules = (
                self.db.query(RoleInheritanceRule)
                .filter(
                    and_(
                        RoleInheritanceRule.child_role_id == current_role_id,
                        RoleInheritanceRule.is_active,
                    )
                )
                .order_by(RoleInheritanceRule.priority.desc())  # Higher priority first
                .all()
            )

            for rule in parent_rules:
                if rule.inherit_all:
                    collect_permissions(rule.parent_role_id, depth + 1)
                else:
                    # Selective inheritance - only inherit selected permissions
                    if rule.selected_permissions:
                        parent_permissions = (
                            self.db.query(RolePermission)
                            .join(Permission)
                            .filter(
                                and_(
                                    RolePermission.role_id == rule.parent_role_id,
                                    Permission.code.in_(rule.selected_permissions),
                                )
                            )
                            .all()
                        )

                        for rp in parent_permissions:
                            perm_code = rp.permission.code
                            if perm_code not in effective_permissions:
                                effective_permissions[perm_code] = rp.is_granted

        collect_permissions(role_id)
        return effective_permissions

    def get_effective_permissions_with_source(
        self, role_id: int
    ) -> dict[str, dict[str, Any]]:
        """Get effective permissions with source information."""
        permissions_with_source = {}
        visited_roles = set()

        def collect_permissions_with_source(
            current_role_id: int,
            depth: int = 0,
            original_source_role_id: int | None = None,

        ) -> None:

        ):

            if current_role_id in visited_roles or depth > 10:
                return
            visited_roles.add(current_role_id)

            current_role = (
                self.db.query(Role).filter(Role.id == current_role_id).first()
            )
            if not current_role:
                return

            # Get direct permissions
            role_permissions = (
                self.db.query(RolePermission)
                .join(Permission)
                .filter(RolePermission.role_id == current_role_id)
                .all()
            )

            for rp in role_permissions:
                perm_code = rp.permission.code
                if perm_code not in permissions_with_source:
                    # For direct permissions (depth 0), source is the role itself
                    # For inherited permissions, track the original source
                    if depth == 0:
                        source_role_id = current_role_id
                        source_role_code = current_role.code
                    else:
                        source_role_id = original_source_role_id or current_role_id
                        # Get the source role's code
                        source_role = (
                            self.db.query(Role)
                            .filter(Role.id == source_role_id)
                            .first()
                        )
                        source_role_code = (
                            source_role.code if source_role else current_role.code
                        )

                    permissions_with_source[perm_code] = {
                        "granted": rp.is_granted,
                        "source_role_id": source_role_id,
                        "source_role_code": source_role_code,
                        "inheritance_depth": depth,
                        "has_conflicts": False,
                    }

            # Get inherited permissions
            parent_rules = (
                self.db.query(RoleInheritanceRule)
                .filter(
                    and_(
                        RoleInheritanceRule.child_role_id == current_role_id,
                        RoleInheritanceRule.is_active,
                    )
                )
                .order_by(RoleInheritanceRule.priority.desc())
                .all()
            )

            for rule in parent_rules:
                parent_role = (
                    self.db.query(Role).filter(Role.id == rule.parent_role_id).first()
                )
                if parent_role:
                    # For inheritance chain starting from root (depth 0),
                    # the first parent becomes the source
                    # For deeper inheritance, preserve the existing source
                    if depth == 0:
                        # First level of inheritance - parent becomes the source
                        collect_permissions_with_source(
                            rule.parent_role_id,
                            depth + 1,
                            rule.parent_role_id,
                        )
                    else:
                        # Deeper inheritance - preserve original source
                        collect_permissions_with_source(
                            rule.parent_role_id,
                            depth + 1,
                            original_source_role_id,
                        )

        collect_permissions_with_source(role_id)
        return permissions_with_source

    def grant_permission_to_role(
        self, role_id: int, permission_id: int, granter: User, db: Session
    ) -> None:
        """Grant a permission to a role."""
        self._set_role_permission(role_id, permission_id, True, granter, db)

    def deny_permission_to_role(
        self, role_id: int, permission_id: int, granter: User, db: Session
    ) -> None:
        """Deny a permission to a role."""
        self._set_role_permission(role_id, permission_id, False, granter, db)

    def _set_role_permission(
        self,
        role_id: int,
        permission_id: int,
        is_granted: bool,
        granter: User,
        db: Session,
    ) -> None:
        """Set role permission (grant or deny)."""
        # Check if role and permission exist
        role = db.query(Role).filter(Role.id == role_id).first()
        permission = db.query(Permission).filter(Permission.id == permission_id).first()

        if not role or not permission:
            raise NotFound("Role or permission not found")

        # Check permissions
        if not granter.is_superuser and not self._can_manage_role_permissions(
            granter, role
        ):
            raise PermissionDenied(
                "Insufficient permissions to modify role permissions"
            )

        # Create or update role permission
        existing_rp = (
            db.query(RolePermission)
            .filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id,
                )
            )
            .first()
        )

        if existing_rp:
            existing_rp.is_granted = is_granted
        else:
            rp = RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                is_granted=is_granted,
                granted_by=granter.id,
            )
            db.add(rp)

        db.commit()

    def get_inheritance_audit_logs(self, role_id: int) -> list[dict[str, Any]]:
        """Get audit logs for inheritance changes."""
        logs = (
            self.db.query(InheritanceAuditLog)
            .filter(InheritanceAuditLog.role_id == role_id)
            .order_by(InheritanceAuditLog.performed_at.desc())
            .all()
        )

        result = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "action": log.action,
                "details": log.details,
                "performed_by": log.performed_by,
                "performed_at": log.performed_at,
            }
            # Try to get performer name if performer relationship exists
            try:
                if hasattr(log, "performer") and log.performer:
                    log_dict["performed_by_name"] = log.performer.full_name
                else:
                    log_dict["performed_by_name"] = "Unknown"
            except Exception:
                log_dict["performed_by_name"] = "Unknown"

            result.append(log_dict)

        return result

    def update_inheritance_rule(
        self,
        rule_id: int,
        update_data: PermissionInheritanceUpdate,
        updater: User,
        db: Session,
    ) -> PermissionInheritanceRuleSchema:
        """Update an inheritance rule."""
        rule = (
            db.query(RoleInheritanceRule)
            .filter(RoleInheritanceRule.id == rule_id)
            .first()
        )
        if not rule:
            raise NotFound("Inheritance rule not found")

        # Check permissions
        if not updater.is_superuser and not self._can_manage_role_inheritance(
            updater, rule.parent_role, rule.child_role
        ):
            raise PermissionDenied(
                "Insufficient permissions to update inheritance rule"
            )

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(rule, field, value)

        rule.updated_by = updater.id
        db.commit()
        db.refresh(rule)

        # Log the update
        self._log_inheritance_action(
            rule.child_role_id,
            "inheritance_updated",
            {"rule_id": rule_id, "changes": update_dict},
            updater.id,
            db,
        )

        return PermissionInheritanceRuleSchema(
            id=rule.id,
            parent_role_id=rule.parent_role_id,
            parent_role_code=rule.parent_role.code,
            child_role_id=rule.child_role_id,
            child_role_code=rule.child_role.code,
            inherit_all=rule.inherit_all,
            selected_permissions=rule.selected_permissions,
            priority=rule.priority,
            is_active=rule.is_active,
            created_at=rule.created_at,
            created_by=rule.created_by,
            updated_at=rule.updated_at,
            updated_by=rule.updated_by,
        )

    def _can_manage_role_inheritance(
        self, user: User, parent_role: Role, child_role: Role
    ) -> bool:
        """Check if user can manage inheritance between roles."""
        # Implementation depends on your permission model
        return user.is_superuser

    def _can_manage_role_permissions(self, user: User, role: Role) -> bool:
        """Check if user can manage role permissions."""
        # Implementation depends on your permission model
        return user.is_superuser

    def _log_inheritance_action(
        self,
        role_id: int,
        action: str,
        details: dict[str, Any],
        performed_by: int,
        db: Session,
    ) -> None:
        """Log an inheritance action."""
        log = InheritanceAuditLog(
            role_id=role_id,
            action=action,
            details=details,
            performed_by=performed_by,
        )
        db.add(log)
        db.commit()
