"""Unit tests for permission service."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.role import RolePermission, UserRole
from app.services.permission import PermissionService
from tests.factories import PermissionFactory, RoleFactory, UserFactory


class TestPermissionService:
    """Test cases for PermissionService."""

    @pytest.fixture
    def permission_service(self, db_session: Session) -> PermissionService:
        """Create PermissionService instance."""
        return PermissionService(db_session)

    @pytest.fixture
    def test_permissions(self, db_session: Session) -> dict:
        """Create test permissions."""
        return PermissionFactory.create_standard_permissions(db_session)

    @pytest.fixture
    def test_user_with_role(self, db_session: Session, test_permissions: dict) -> tuple:
        """Create test user with role and permissions."""
        # Create user
        user = UserFactory.create(db_session)

        # Create organization
        from tests.factories import OrganizationFactory

        org = OrganizationFactory.create(db_session)

        # Create role
        role = RoleFactory.create_with_organization(
            db_session, org, name="Test Role", code="test.role"
        )

        # Assign permissions to role
        for permission in test_permissions["users"][:3]:  # First 3 user permissions
            role_perm = RolePermission(role_id=role.id, permission_id=permission.id)
            db_session.add(role_perm)

        # Assign role to user
        user_role = UserRole(
            user_id=user.id, role_id=role.id, organization_id=org.id, is_active=True
        )
        db_session.add(user_role)
        db_session.commit()

        return user, role, test_permissions

    def test_get_user_effective_permissions(
        self,
        permission_service: PermissionService,
        test_user_with_role: tuple,
        db_session: Session,
    ) -> None:
        """Test getting user's effective permissions."""
        user, role, permissions = test_user_with_role

        # Get effective permissions
        result = permission_service.get_user_effective_permissions(user.id)

        # Verify result
        assert result.user_id == user.id
        assert len(result.inherited_permissions) == 3
        assert len(result.all_permission_codes) == 3

        # Check inherited permissions details
        for perm_info in result.inherited_permissions:
            assert perm_info.source == "role"
            assert perm_info.source_id == role.id
            assert perm_info.source_name == role.name
            assert perm_info.can_override is True

    def test_get_user_effective_permissions_nonexistent_user(
        self, permission_service: PermissionService
    ) -> None:
        """Test getting permissions for non-existent user."""
        with pytest.raises(ValueError, match="User with id 9999 not found"):
            permission_service.get_user_effective_permissions(9999)

    def test_check_user_permissions(
        self, permission_service: PermissionService, test_user_with_role: tuple
    ) -> None:
        """Test checking specific user permissions."""
        user, role, permissions = test_user_with_role

        # Get permission codes
        user_perms = permissions["users"]
        granted_codes = [p.code for p in user_perms[:3]]
        not_granted_codes = [p.code for p in user_perms[3:]]

        # Check permissions
        result = permission_service.check_user_permissions(
            user.id, granted_codes + not_granted_codes
        )

        # Verify results
        assert result.user_id == user.id
        for code in granted_codes:
            assert result.results[code] is True
        for code in not_granted_codes:
            assert result.results[code] is False
        assert set(result.missing_permissions) == set(not_granted_codes)

    def test_user_has_permission(
        self, permission_service: PermissionService, test_user_with_role: tuple
    ) -> None:
        """Test checking single permission."""
        user, role, permissions = test_user_with_role

        # Test granted permission
        granted_code = permissions["users"][0].code
        assert permission_service.user_has_permission(user.id, granted_code) is True

        # Test not granted permission
        not_granted_code = permissions["users"][4].code
        assert (
            permission_service.user_has_permission(user.id, not_granted_code) is False
        )

    def test_assign_permissions_to_role(
        self,
        permission_service: PermissionService,
        test_permissions: dict,
        db_session: Session,
    ) -> None:
        """Test assigning permissions to role."""
        # Create organization and role
        from tests.factories import OrganizationFactory

        org = OrganizationFactory.create(db_session)
        role = RoleFactory.create_with_organization(db_session, org, name="New Role")

        # Get permission IDs
        permission_ids = [p.id for p in test_permissions["users"][:5]]

        # Assign permissions
        count = permission_service.assign_permissions_to_role(
            role.id, permission_ids, granted_by=1
        )

        # Verify
        assert count == 5

        # Check permissions were assigned
        role_perms = (
            db_session.query(RolePermission)
            .filter(RolePermission.role_id == role.id)
            .all()
        )
        assert len(role_perms) == 5
        assert all(rp.granted_by == 1 for rp in role_perms)

    def test_assign_permissions_to_nonexistent_role(
        self, permission_service: PermissionService, test_permissions: dict
    ) -> None:
        """Test assigning permissions to non-existent role."""
        permission_ids = [p.id for p in test_permissions["users"][:2]]

        with pytest.raises(ValueError, match="Role with id 9999 not found"):
            permission_service.assign_permissions_to_role(9999, permission_ids)

    def test_create_user_permission_override(
        self,
        permission_service: PermissionService,
        test_user_with_role: tuple,
        test_permissions: dict,
    ) -> None:
        """Test creating user permission override."""
        user, role, permissions = test_user_with_role
        permission = permissions["system"][0]  # System permission

        # Create override
        result = permission_service.create_user_permission_override(
            user.id,
            permission.id,
            "grant",
            reason="Special access needed",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            created_by=1,
        )

        # Verify (mock implementation returns object with id)
        assert hasattr(result, "id")

    def test_create_override_invalid_action(
        self,
        permission_service: PermissionService,
        test_user_with_role: tuple,
        test_permissions: dict,
    ) -> None:
        """Test creating override with invalid action."""
        user, role, permissions = test_user_with_role
        permission = permissions["system"][0]

        with pytest.raises(Exception, match="Action must be 'grant' or 'revoke'"):
            permission_service.create_user_permission_override(
                user.id, permission.id, "invalid_action"
            )

    def test_list_permission_templates(
        self, permission_service: PermissionService, test_permissions: dict
    ) -> None:
        """Test listing permission templates."""
        templates = permission_service.list_permission_templates()

        # Verify we have templates
        assert len(templates) > 0

        # Check template structure
        for template in templates:
            assert template.id > 0
            assert template.name
            assert len(template.permissions) > 0
            assert template.is_active is True

    def test_list_permission_templates_filtered(
        self, permission_service: PermissionService, test_permissions: dict
    ) -> None:
        """Test listing permission templates with filter."""
        # Get active templates
        active_templates = permission_service.list_permission_templates(is_active=True)
        assert all(t.is_active for t in active_templates)

        # Get inactive templates (should be empty with current implementation)
        inactive_templates = permission_service.list_permission_templates(
            is_active=False
        )
        assert len(inactive_templates) == 0

    def test_execute_bulk_permission_operation(
        self,
        permission_service: PermissionService,
        test_permissions: dict,
        db_session: Session,
    ) -> None:
        """Test bulk permission operation."""
        # Create roles
        from tests.factories import OrganizationFactory

        org = OrganizationFactory.create(db_session)

        role_ids = []
        for i in range(3):
            role = RoleFactory.create_with_organization(
                db_session, org, name=f"Bulk Role {i}"
            )
            role_ids.append(role.id)

        # Get permission IDs
        permission_ids = [p.id for p in test_permissions["users"][:3]]

        # Execute bulk grant
        result = permission_service.execute_bulk_permission_operation(
            "grant",
            "roles",
            role_ids,
            permission_ids,
            reason="Bulk assignment test",
            performed_by=1,
        )

        # Verify
        assert result.success_count == 3
        assert result.failure_count == 0
        assert result.failures is None

    def test_bulk_operation_invalid_params(
        self, permission_service: PermissionService
    ) -> None:
        """Test bulk operation with invalid parameters."""
        # Invalid operation
        with pytest.raises(ValueError, match="Invalid operation type"):
            permission_service.execute_bulk_permission_operation(
                "invalid_op", "roles", [1], [1]
            )

        # Invalid target type
        with pytest.raises(ValueError, match="Invalid target type"):
            permission_service.execute_bulk_permission_operation(
                "grant", "invalid_target", [1], [1]
            )
