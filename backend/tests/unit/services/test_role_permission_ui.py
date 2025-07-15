"""Tests for role permission UI service."""

import pytest
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User
from app.schemas.role_permission_ui import (
    PermissionCategory,
    PermissionMatrixUpdate,
)
from app.services.role_permission_ui import RolePermissionUIService
from tests.factories import OrganizationFactory, RoleFactory, UserFactory


class TestRolePermissionUIService:
    """Test role permission UI service functionality."""

    @pytest.fixture
    def ui_service(self, db_session: Session) -> RolePermissionUIService:
        """Create role permission UI service instance."""
        return RolePermissionUIService(db_session)

    @pytest.fixture
    def organization(self, db_session: Session) -> Organization:
        """Create test organization."""
        return OrganizationFactory.create(db_session, name="Test Org")

    @pytest.fixture
    def admin_user(self, db_session: Session) -> User:
        """Create admin user."""
        return UserFactory.create_with_password(
            db_session,
            password="password123",
            email="admin@example.com",
            is_superuser=True,
        )

    @pytest.fixture
    def org_admin_user(self, db_session: Session, organization: Organization) -> User:
        """Create organization admin user."""
        user = UserFactory.create_with_password(
            db_session, password="password123", email="orgadmin@example.com"
        )
<<<<<<< HEAD
        # Add org admin role with permission management
        import uuid

        admin_role = RoleFactory.create(
            db_session,
            code=f"ORG_ADMIN_{uuid.uuid4().hex[:8]}",
            name="Organization Admin",
            permissions={"role": {"manage": True}},
        )
        user.assign_role(admin_role, organization)
=======
        # TODO: Implement role assignment with admin role
>>>>>>> main
        return user

    @pytest.fixture
    def role(self, db_session: Session) -> Role:
        """Create test role."""
        import uuid

        unique_code = f"TEST_ROLE_{uuid.uuid4().hex[:8]}"
        return RoleFactory.create(db_session, code=unique_code, name="Test Role")

    def test_get_permission_definitions(
        self, ui_service: RolePermissionUIService
    ) -> None:
        """Test getting all permission definitions."""
        definitions = ui_service.get_permission_definitions()

        # Should have multiple categories
        assert len(definitions) >= 3  # At least user, organization, system categories

        # Check user management category
        user_category = next(
            (
                cat
                for cat in definitions
                if cat.category == PermissionCategory.USER_MANAGEMENT
            ),
            None,
        )
        assert user_category is not None
        assert len(user_category.groups) > 0

        # Check specific permissions exist
        user_group = user_category.groups[0]
        assert any(p.code == "user.create" for p in user_group.permissions)
        assert any(p.code == "user.read" for p in user_group.permissions)
        assert any(p.code == "user.update" for p in user_group.permissions)
        assert any(p.code == "user.delete" for p in user_group.permissions)

    def test_get_role_permission_matrix(
        self,
        ui_service: RolePermissionUIService,
        role: Role,
        organization: Organization,
    ) -> None:
        """Test getting role permission matrix."""
        matrix = ui_service.get_role_permission_matrix(
            role_id=role.id, organization_id=organization.id
        )

        assert matrix.role_id == role.id
        assert matrix.role_name == role.name
        assert matrix.organization_id == organization.id
        assert isinstance(matrix.permissions, dict)

        # Initially, most permissions should be False
        assert all(not enabled for enabled in matrix.permissions.values())

<<<<<<< HEAD
=======
    @pytest.mark.skip(
        reason="RolePermissionUIService.update_role_permissions not implemented yet"
    )
>>>>>>> main
    def test_update_role_permissions(
        self,
        ui_service: RolePermissionUIService,
        role: Role,
        organization: Organization,
        org_admin_user: User,
    ) -> None:
        """Test updating role permissions."""
        # Set some permissions
        update_data = PermissionMatrixUpdate(
            permissions={
                "user.read": True,
                "user.create": True,
                "user.update": False,
                "user.delete": False,
            }
        )

        updated_matrix = ui_service.update_role_permissions(
            role_id=role.id,
            organization_id=organization.id,
            update_data=update_data,
            updater=org_admin_user,
        )

        assert updated_matrix.permissions["user.read"] is True
        assert updated_matrix.permissions["user.create"] is True
        assert updated_matrix.permissions["user.update"] is False
        assert updated_matrix.permissions["user.delete"] is False

<<<<<<< HEAD
=======
    @pytest.mark.skip(reason="Depends on unimplemented update_role_permissions")
>>>>>>> main
    def test_copy_permissions_from_role(
        self,
        ui_service: RolePermissionUIService,
        organization: Organization,
        org_admin_user: User,
        db_session: Session,
    ) -> None:
        """Test copying permissions from one role to another."""
        # Create source and target roles
        import uuid

        source_role = RoleFactory.create(
            db_session, code=f"SOURCE_{uuid.uuid4().hex[:8]}", name="Source Role"
        )
        target_role = RoleFactory.create(
            db_session, code=f"TARGET_{uuid.uuid4().hex[:8]}", name="Target Role"
        )

        # Set permissions on source role
        source_update = PermissionMatrixUpdate(
            permissions={
                "user.read": True,
                "user.create": True,
                "organization.read": True,
            }
        )
        ui_service.update_role_permissions(
            role_id=source_role.id,
            organization_id=organization.id,
            update_data=source_update,
            updater=org_admin_user,
        )

        # Copy to target role
        copied_matrix = ui_service.copy_permissions_from_role(
            source_role_id=source_role.id,
            target_role_id=target_role.id,
            organization_id=organization.id,
            copier=org_admin_user,
        )

        # Target should have same permissions as source
        assert copied_matrix.permissions["user.read"] is True
        assert copied_matrix.permissions["user.create"] is True
        assert copied_matrix.permissions["organization.read"] is True

    def test_get_permission_inheritance_tree(
        self,
        ui_service: RolePermissionUIService,
        organization: Organization,
        db_session: Session,
    ) -> None:
        """Test getting permission inheritance tree."""
        # Create role hierarchy
        import uuid

        parent_role = RoleFactory.create(
            db_session, code=f"PARENT_{uuid.uuid4().hex[:8]}", name="Parent Role"
        )
        child_role = RoleFactory.create(
            db_session,
            code=f"CHILD_{uuid.uuid4().hex[:8]}",
            name="Child Role",
            parent_id=parent_role.id,
        )

        tree = ui_service.get_permission_inheritance_tree(
            role_id=child_role.id, organization_id=organization.id
        )

        assert tree.role_id == child_role.id
        assert tree.role_name == child_role.name
        assert tree.parent_role_id == parent_role.id
        assert tree.parent_role_name == parent_role.name
        assert isinstance(tree.inherited_permissions, dict)
        assert isinstance(tree.own_permissions, dict)

<<<<<<< HEAD
=======
    @pytest.mark.skip(reason="Depends on unimplemented update_role_permissions")
>>>>>>> main
    def test_bulk_update_permissions(
        self,
        ui_service: RolePermissionUIService,
        organization: Organization,
        admin_user: User,
        db_session: Session,
    ) -> None:
        """Test bulk updating permissions for multiple roles."""
        # Create multiple roles
        import uuid

        roles = [
            RoleFactory.create(
                db_session, code=f"ROLE{i}_{uuid.uuid4().hex[:8]}", name=f"Role {i}"
            )
            for i in range(3)
        ]

        # Bulk update
        bulk_update = {
            roles[0].id: {"user.read": True, "user.create": False},
            roles[1].id: {"user.read": True, "user.update": True},
            roles[2].id: {"user.delete": True},
        }

        results = ui_service.bulk_update_permissions(
            organization_id=organization.id,
            role_permissions=bulk_update,
            updater=admin_user,
        )

        assert len(results) == 3
        assert results[0].permissions["user.read"] is True
        assert results[0].permissions["user.create"] is False
        assert results[1].permissions["user.update"] is True
        assert results[2].permissions["user.delete"] is True

<<<<<<< HEAD
=======
    @pytest.mark.skip(reason="Depends on unimplemented update_role_permissions")
>>>>>>> main
    def test_get_effective_permissions(
        self,
        ui_service: RolePermissionUIService,
        organization: Organization,
<<<<<<< HEAD
=======
        admin_user: User,
>>>>>>> main
        db_session: Session,
    ) -> None:
        """Test getting effective permissions including inheritance."""
        # Create role hierarchy with permissions
        import uuid

        parent_role = RoleFactory.create(
            db_session, code=f"PARENT_{uuid.uuid4().hex[:8]}", name="Parent"
        )
        child_role = RoleFactory.create(
            db_session,
            code=f"CHILD_{uuid.uuid4().hex[:8]}",
            name="Child",
            parent_id=parent_role.id,
        )

        # Set parent permissions
        parent_update = PermissionMatrixUpdate(
            permissions={"user.read": True, "user.create": True}
        )
        ui_service.update_role_permissions(
            role_id=parent_role.id,
            organization_id=organization.id,
            update_data=parent_update,
<<<<<<< HEAD
            updater=db_session.query(User).filter(User.is_superuser).first(),
=======
            updater=admin_user,
>>>>>>> main
        )

        # Set child permissions (override one)
        child_update = PermissionMatrixUpdate(
            permissions={"user.create": False, "user.update": True}
        )
        ui_service.update_role_permissions(
            role_id=child_role.id,
            organization_id=organization.id,
            update_data=child_update,
<<<<<<< HEAD
            updater=db_session.query(User).filter(User.is_superuser).first(),
=======
            updater=admin_user,
>>>>>>> main
        )

        # Get effective permissions
        effective = ui_service.get_effective_permissions(
            role_id=child_role.id, organization_id=organization.id
        )

        # Should inherit from parent but child overrides take precedence
        assert effective["user.read"] is True  # Inherited
        assert effective["user.create"] is False  # Overridden
        assert effective["user.update"] is True  # Child's own

    def test_permission_ui_grouping(self, ui_service: RolePermissionUIService) -> None:
        """Test permission UI grouping and categorization."""
        ui_data = ui_service.get_permission_ui_structure()

        # Check structure
        assert "categories" in ui_data
        assert len(ui_data["categories"]) > 0

        # Check each category has proper structure
        for category in ui_data["categories"]:
            assert "name" in category
            assert "icon" in category
            assert "groups" in category
            assert len(category["groups"]) > 0

            # Check each group
            for group in category["groups"]:
                assert "name" in group
                assert "permissions" in group
                assert len(group["permissions"]) > 0

                # Check each permission
                for permission in group["permissions"]:
                    assert "code" in permission
                    assert "name" in permission
                    assert "description" in permission

    def test_permission_search(self, ui_service: RolePermissionUIService) -> None:
        """Test searching permissions."""
        # Search for user-related permissions
        results = ui_service.search_permissions("user")

        assert len(results) > 0
        assert all(
<<<<<<< HEAD
            "user" in p.code.lower() or "user" in p.name.lower() for p in results
=======
            "user" in p.permission.code.lower() or "user" in p.permission.name.lower()
            for p in results
>>>>>>> main
        )

        # Search for create permissions
        create_results = ui_service.search_permissions("create")

        assert len(create_results) > 0
        assert all(
<<<<<<< HEAD
            "create" in p.code.lower() or "create" in p.name.lower()
            for p in create_results
        )

=======
            "create" in p.permission.code.lower()
            or "create" in p.permission.name.lower()
            for p in create_results
        )

    @pytest.mark.skip(reason="Depends on unimplemented update_role_permissions")
>>>>>>> main
    def test_permission_dependencies(
        self,
        ui_service: RolePermissionUIService,
        role: Role,
        organization: Organization,
        org_admin_user: User,
    ) -> None:
        """Test permission dependencies (e.g., delete requires read)."""
        # Try to set delete without read - should auto-add read
        update_data = PermissionMatrixUpdate(permissions={"user.delete": True})

        updated = ui_service.update_role_permissions(
            role_id=role.id,
            organization_id=organization.id,
            update_data=update_data,
            updater=org_admin_user,
            enforce_dependencies=True,
        )

        # Should automatically enable read permission
        assert updated.permissions["user.read"] is True
        assert updated.permissions["user.delete"] is True

<<<<<<< HEAD
=======
    @pytest.mark.skip(reason="Depends on unimplemented update_role_permissions")
>>>>>>> main
    def test_permission_conflict_resolution(
        self,
        ui_service: RolePermissionUIService,
        organization: Organization,
        db_session: Session,
    ) -> None:
        """Test resolving permission conflicts in inheritance."""
        # Create complex hierarchy
        import uuid

        grandparent = RoleFactory.create(
            db_session, code=f"GP_{uuid.uuid4().hex[:8]}", name="Grandparent"
        )
        parent1 = RoleFactory.create(
            db_session,
            code=f"P1_{uuid.uuid4().hex[:8]}",
            name="Parent1",
            parent_id=grandparent.id,
        )
        RoleFactory.create(
            db_session,
            code=f"P2_{uuid.uuid4().hex[:8]}",
            name="Parent2",
            parent_id=grandparent.id,
        )
        child = RoleFactory.create(
            db_session,
            code=f"CHILD_{uuid.uuid4().hex[:8]}",
            name="Child",
            parent_id=parent1.id,
        )

        # Set conflicting permissions
<<<<<<< HEAD
        admin = db_session.query(User).filter(User.is_superuser).first()
=======
        admin = UserFactory.create_with_password(
            db_session,
            password="password",
            email="conflict_admin@example.com",
            is_superuser=True,
        )
>>>>>>> main

        ui_service.update_role_permissions(
            grandparent.id,
            organization.id,
            PermissionMatrixUpdate(permissions={"user.read": True}),
            admin,
        )
        ui_service.update_role_permissions(
            parent1.id,
            organization.id,
            PermissionMatrixUpdate(permissions={"user.read": False}),
            admin,
        )

        # Check conflict resolution
        conflicts = ui_service.get_permission_conflicts(child.id, organization.id)
        assert len(conflicts) > 0
        assert any(c.permission_code == "user.read" for c in conflicts)
