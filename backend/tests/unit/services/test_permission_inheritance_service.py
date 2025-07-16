"""
Permission inheritance service tests.

Tests for advanced permission inheritance and dependency management.
Following TDD approach - Red phase: Writing tests before implementation.
"""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.schemas.permission_inheritance import (
    InheritanceConflictResolution,
    PermissionInheritanceUpdate,
)
from app.services.permission_inheritance import PermissionInheritanceService
from tests.factories import (
    create_test_organization,
    create_test_role,
    create_test_user,
)
from tests.factories.permission import create_test_permission


@pytest.mark.skip(
    reason="create_test_role and create_test_user_role not yet implemented"
)
class TestPermissionInheritanceService:
    """Test cases for PermissionInheritanceService."""

    @pytest.fixture
    def service(self, db_session: Session) -> PermissionInheritanceService:
        """Create service instance."""
        return PermissionInheritanceService(db_session)

    def test_create_inheritance_rule(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test creating permission inheritance rule."""
        # Given: Parent and child roles
        org = create_test_organization(db_session)
        parent_role = create_test_role(
            db_session, organization_id=org.id, code="PARENT_ROLE"
        )
        child_role = create_test_role(
            db_session, organization_id=org.id, code="CHILD_ROLE"
        )
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: Creating inheritance rule
        rule = service.create_inheritance_rule(
            parent_role_id=parent_role.id,
            child_role_id=child_role.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )

        # Then: Rule should be created
        assert rule.parent_role_id == parent_role.id
        assert rule.child_role_id == child_role.id
        assert rule.inherit_all is True
        assert rule.is_active is True

    def test_circular_inheritance_prevention(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test prevention of circular inheritance."""
        # Given: Three roles in organization
        org = create_test_organization(db_session)
        role_a = create_test_role(db_session, organization_id=org.id, code="ROLE_A")
        role_b = create_test_role(db_session, organization_id=org.id, code="ROLE_B")
        role_c = create_test_role(db_session, organization_id=org.id, code="ROLE_C")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Create inheritance chain: A -> B -> C
        service.create_inheritance_rule(
            parent_role_id=role_a.id,
            child_role_id=role_b.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )
        service.create_inheritance_rule(
            parent_role_id=role_b.id,
            child_role_id=role_c.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )

        # When/Then: Trying to create C -> A should fail
        with pytest.raises(BusinessLogicError, match="Circular inheritance"):
            service.create_inheritance_rule(
                parent_role_id=role_c.id,
                child_role_id=role_a.id,
                creator=admin,
                db=db_session,
                inherit_all=True,
            )

    def test_permission_dependency_management(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test permission dependency management."""
        # Given: Permissions with dependencies
        perm_read = create_test_permission(db_session, code="resource:read")
        perm_write = create_test_permission(db_session, code="resource:write")
        perm_delete = create_test_permission(db_session, code="resource:delete")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: Creating dependencies (write requires read, delete requires write)
        dep1 = service.create_permission_dependency(
            permission_id=perm_write.id,
            requires_permission_id=perm_read.id,
            creator=admin,
            db=db_session,
        )
        dep2 = service.create_permission_dependency(
            permission_id=perm_delete.id,
            requires_permission_id=perm_write.id,
            creator=admin,
            db=db_session,
        )

        # Then: Dependencies should be created
        assert dep1.permission_id == perm_write.id
        assert dep1.requires_permission_id == perm_read.id
        assert dep2.permission_id == perm_delete.id
        assert dep2.requires_permission_id == perm_write.id

    def test_transitive_permission_dependencies(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test transitive permission dependency resolution."""
        # Given: Permissions with transitive dependencies
        perm_read = create_test_permission(db_session, code="resource:read")
        perm_write = create_test_permission(db_session, code="resource:write")
        perm_delete = create_test_permission(db_session, code="resource:delete")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Create dependency chain
        service.create_permission_dependency(
            permission_id=perm_write.id,
            requires_permission_id=perm_read.id,
            creator=admin,
            db=db_session,
        )
        service.create_permission_dependency(
            permission_id=perm_delete.id,
            requires_permission_id=perm_write.id,
            creator=admin,
            db=db_session,
        )

        # When: Getting all dependencies for delete permission
        all_deps = service.get_all_permission_dependencies(perm_delete.id)

        # Then: Should include both direct and transitive dependencies
        assert len(all_deps) == 2
        dep_codes = [dep.code for dep in all_deps]
        assert "resource:write" in dep_codes
        assert "resource:read" in dep_codes

    def test_inheritance_conflict_detection(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test detection of inheritance conflicts."""
        # Given: Roles with conflicting permissions
        org = create_test_organization(db_session)
        parent1 = create_test_role(db_session, organization_id=org.id, code="PARENT1")
        parent2 = create_test_role(db_session, organization_id=org.id, code="PARENT2")
        child = create_test_role(db_session, organization_id=org.id, code="CHILD")
        perm = create_test_permission(db_session, code="resource:manage")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Grant permission to parent1, deny to parent2
        service.grant_permission_to_role(parent1.id, perm.id, admin, db_session)
        service.deny_permission_to_role(parent2.id, perm.id, admin, db_session)

        # Create inheritance from both parents
        service.create_inheritance_rule(
            parent_role_id=parent1.id,
            child_role_id=child.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )
        service.create_inheritance_rule(
            parent_role_id=parent2.id,
            child_role_id=child.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )

        # When: Checking for conflicts
        conflicts = service.get_inheritance_conflicts(child.id)

        # Then: Should detect the conflict
        assert len(conflicts) == 1
        assert conflicts[0].permission_code == "resource:manage"
        assert conflicts[0].parent1_role_id == parent1.id
        assert conflicts[0].parent2_role_id == parent2.id
        assert conflicts[0].parent1_grants is True
        assert conflicts[0].parent2_grants is False

    def test_conflict_resolution_strategies(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test different conflict resolution strategies."""
        # Given: Conflict scenario
        org = create_test_organization(db_session)
        parent1 = create_test_role(db_session, organization_id=org.id, code="PARENT1")
        parent2 = create_test_role(db_session, organization_id=org.id, code="PARENT2")
        child = create_test_role(db_session, organization_id=org.id, code="CHILD")
        perm = create_test_permission(db_session, code="resource:manage")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Create conflict
        service.grant_permission_to_role(parent1.id, perm.id, admin, db_session)
        service.deny_permission_to_role(parent2.id, perm.id, admin, db_session)
        service.create_inheritance_rule(
            parent_role_id=parent1.id,
            child_role_id=child.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )
        service.create_inheritance_rule(
            parent_role_id=parent2.id,
            child_role_id=child.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )

        # When: Resolving with "deny wins" strategy
        resolution = InheritanceConflictResolution(
            strategy="deny_wins",
            permission_code="resource:manage",
        )
        service.resolve_inheritance_conflict(child.id, resolution, admin, db_session)

        # Then: Permission should be denied
        effective = service.get_effective_permissions(child.id)
        assert effective.get("resource:manage") is False

    def test_inheritance_priority_levels(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test inheritance with priority levels."""
        # Given: Multiple parent roles with priorities
        org = create_test_organization(db_session)
        high_priority = create_test_role(
            db_session, organization_id=org.id, code="HIGH_PRIORITY"
        )
        low_priority = create_test_role(
            db_session, organization_id=org.id, code="LOW_PRIORITY"
        )
        child = create_test_role(db_session, organization_id=org.id, code="CHILD")
        perm = create_test_permission(db_session, code="resource:access")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Grant to high priority, deny to low priority
        service.grant_permission_to_role(high_priority.id, perm.id, admin, db_session)
        service.deny_permission_to_role(low_priority.id, perm.id, admin, db_session)

        # When: Creating inheritance with priorities
        service.create_inheritance_rule(
            parent_role_id=high_priority.id,
            child_role_id=child.id,
            inherit_all=True,
            priority=100,  # Higher priority
            creator=admin,
            db=db_session,
        )
        service.create_inheritance_rule(
            parent_role_id=low_priority.id,
            child_role_id=child.id,
            inherit_all=True,
            priority=50,  # Lower priority
            creator=admin,
            db=db_session,
        )

        # Then: Higher priority should win
        effective = service.get_effective_permissions(child.id)
        assert effective.get("resource:access") is True

    def test_selective_inheritance(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test selective permission inheritance."""
        # Given: Parent role with multiple permissions
        org = create_test_organization(db_session)
        parent = create_test_role(db_session, organization_id=org.id, code="PARENT")
        child = create_test_role(db_session, organization_id=org.id, code="CHILD")
        perm1 = create_test_permission(db_session, code="resource:read")
        perm2 = create_test_permission(db_session, code="resource:write")
        perm3 = create_test_permission(db_session, code="resource:delete")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Grant all permissions to parent
        service.grant_permission_to_role(parent.id, perm1.id, admin, db_session)
        service.grant_permission_to_role(parent.id, perm2.id, admin, db_session)
        service.grant_permission_to_role(parent.id, perm3.id, admin, db_session)

        # When: Creating selective inheritance (only read and write)
        service.create_inheritance_rule(
            parent_role_id=parent.id,
            child_role_id=child.id,
            inherit_all=False,
            selected_permissions=["resource:read", "resource:write"],
            creator=admin,
            db=db_session,
        )

        # Then: Only selected permissions should be inherited
        effective = service.get_effective_permissions(child.id)
        assert effective.get("resource:read") is True
        assert effective.get("resource:write") is True
        assert effective.get("resource:delete") is None  # Not inherited, so not in dict

    def test_inheritance_audit_trail(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test audit trail for inheritance changes."""
        # Given: Inheritance rule
        org = create_test_organization(db_session)
        parent = create_test_role(db_session, organization_id=org.id, code="PARENT")
        child = create_test_role(db_session, organization_id=org.id, code="CHILD")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: Creating and modifying inheritance
        rule = service.create_inheritance_rule(
            parent_role_id=parent.id,
            child_role_id=child.id,
            inherit_all=True,
            creator=admin,
            db=db_session,
        )

        # Update the rule
        update_data = PermissionInheritanceUpdate(
            inherit_all=False,
            selected_permissions=["resource:read"],
        )
        service.update_inheritance_rule(rule.id, update_data, admin, db_session)

        # Then: Audit trail should be recorded
        audit_logs = service.get_inheritance_audit_logs(child.id)
        assert len(audit_logs) >= 2
        # Check that both actions are present (order may vary)
        actions = [log["action"] for log in audit_logs]
        assert "inheritance_created" in actions
        assert "inheritance_updated" in actions

    def test_permission_effective_source_tracking(
        self, service: PermissionInheritanceService, db_session: Session
    ) -> None:
        """Test tracking the source of effective permissions."""
        # Given: Complex inheritance hierarchy
        org = create_test_organization(db_session)
        grandparent = create_test_role(
            db_session, organization_id=org.id, code="GRANDPARENT"
        )
        parent = create_test_role(db_session, organization_id=org.id, code="PARENT")
        child = create_test_role(db_session, organization_id=org.id, code="CHILD")
        perm = create_test_permission(db_session, code="resource:manage")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Grant permission to grandparent
        service.grant_permission_to_role(grandparent.id, perm.id, admin, db_session)

        # Create inheritance chain
        service.create_inheritance_rule(
            parent_role_id=grandparent.id,
            child_role_id=parent.id,
            inherit_all=True,
            creator=admin,
            db=db_session,
        )
        service.create_inheritance_rule(
            parent_role_id=parent.id,
            child_role_id=child.id,
            inherit_all=True,
            creator=admin,
            db=db_session,
        )

        # When: Getting effective permissions with source
        effective_with_source = service.get_effective_permissions_with_source(child.id)

        # Then: Should track the source (direct parent is the source)
        perm_info = effective_with_source.get("resource:manage")
        assert perm_info is not None
        assert perm_info["granted"] is True
        assert perm_info["source_role_code"] == "PARENT"
        assert perm_info["inheritance_depth"] == 2
