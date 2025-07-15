"""Integration tests for Role and Permission system."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role, UserRole
from app.models.user import User
from app.services.permission_matrix import PermissionLevel, get_permission_matrix
from app.services.role import RoleService


class TestRolePermissionIntegration:
    """Integration tests for Role and Permission system."""

    @pytest.fixture
    def test_organization(self, db_session: Session) -> Organization:
        """Create test organization."""
        org = Organization.create(
            db=db_session,
            code="TEST_ORG",
            name="Test Organization",
            created_by=1,
        )
        db_session.commit()
        return org

    @pytest.fixture
    def admin_role(self, db_session: Session, test_admin: User) -> Role:
        """Create admin role."""
        role = Role.create(
            db=db_session,
            code="ORG_ADMIN",
            name="Organization Admin",
            permissions=["*"],
            created_by=test_admin.id,
        )
        db_session.commit()
        return role

    @pytest.fixture
    def manager_role(self, db_session: Session, test_admin: User) -> Role:
        """Create manager role."""
        role = Role.create(
            db=db_session,
            code="MANAGER",
            name="Manager",
            permissions=["read:*", "write:team", "role:assign"],
            created_by=test_admin.id,
        )
        db_session.commit()
        return role

    @pytest.fixture
    def member_role(self, db_session: Session, test_admin: User) -> Role:
        """Create member role."""
        role = Role.create(
            db=db_session,
            code="MEMBER",
            name="Member",
            permissions=["read:own", "write:own"],
            created_by=test_admin.id,
        )
        db_session.commit()
        return role

    @pytest.fixture
    def test_manager_user(self, db_session: Session) -> User:
        """Create test manager user."""
        user = User.create(
            db_session,
            email="manager@example.com",
            password="ManagerPass123!",
            full_name="Manager User",
        )
        db_session.commit()
        return user

    @pytest.fixture
    def test_member_user(self, db_session: Session) -> User:
        """Create test member user."""
        user = User.create(
            db_session,
            email="member@example.com",
            password="MemberPass123!",
            full_name="Member User",
        )
        db_session.commit()
        return user

    def test_end_to_end_role_assignment_and_permission_check(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_admin: User,
        test_manager_user: User,
        test_member_user: User,
        manager_role: Role,
        member_role: Role,
        db_session: Session,
    ) -> None:
        """Test complete end-to-end role assignment and permission checking."""
        # Step 1: Assign manager role to manager user
        assignment_data = {
            "user_id": test_manager_user.id,
            "role_id": manager_role.id,
            "organization_id": test_organization.id,
        }

        response = client.post(
            "/api/v1/roles/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=assignment_data,
        )
        assert response.status_code == 201

        # Step 2: Assign member role to member user
        assignment_data = {
            "user_id": test_member_user.id,
            "role_id": member_role.id,
            "organization_id": test_organization.id,
        }

        response = client.post(
            "/api/v1/roles/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=assignment_data,
        )
        assert response.status_code == 201

        # Step 3: Check manager user has manager-level permissions
        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": "read:team_performance",
                "organization_id": test_organization.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_permission"] is True

        # Step 4: Check member user doesn't have manager-level permissions
        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_member_user.id,
                "permission": "read:team_performance",
                "organization_id": test_organization.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_permission"] is False

        # Step 5: Check permission levels
        response = client.get(
            "/api/v1/permissions/user/level",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "organization_id": test_organization.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["permission_level"] == "manager"

        response = client.get(
            "/api/v1/permissions/user/level",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_member_user.id,
                "organization_id": test_organization.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["permission_level"] == "member"

    def test_permission_inheritance_hierarchy(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_admin: User,
        test_manager_user: User,
        manager_role: Role,
        db_session: Session,
    ) -> None:
        """Test that permission inheritance works correctly."""
        # Given: Manager user with manager role
        UserRole.create(
            db=db_session,
            user_id=test_manager_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Checking various permission levels
        viewer_permission = "read:own_profile"
        member_permission = "write:own_profile"
        manager_permission = "read:team_performance"
        admin_permission = "admin:system"

        # Then: Manager should have viewer and member permissions (inherited)
        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": viewer_permission,
                "organization_id": test_organization.id,
            },
        )
        assert response.status_code == 200
        assert response.json()["has_permission"] is True

        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": member_permission,
                "organization_id": test_organization.id,
            },
        )
        assert response.status_code == 200
        assert response.json()["has_permission"] is True

        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": manager_permission,
                "organization_id": test_organization.id,
            },
        )
        assert response.status_code == 200
        assert response.json()["has_permission"] is True

        # But should not have admin permissions
        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": admin_permission,
                "organization_id": test_organization.id,
            },
        )
        assert response.status_code == 200
        assert response.json()["has_permission"] is False

    def test_context_specific_permissions(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_admin: User,
        test_manager_user: User,
        manager_role: Role,
        db_session: Session,
    ) -> None:
        """Test context-specific permission checking."""
        # Given: Manager user with manager role
        UserRole.create(
            db=db_session,
            user_id=test_manager_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Checking organization context permissions
        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": "org:write:members",
                "organization_id": test_organization.id,
                "context": "organization",
            },
        )

        # Then: Should have organization context permissions
        assert response.status_code == 200
        assert response.json()["has_permission"] is True

        # When: Checking department context permissions
        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": "dept:write:members",
                "organization_id": test_organization.id,
                "context": "department",
            },
        )

        # Then: Should have department context permissions
        assert response.status_code == 200
        assert response.json()["has_permission"] is True

    def test_role_expiration_affects_permissions(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_admin: User,
        test_manager_user: User,
        manager_role: Role,
        db_session: Session,
    ) -> None:
        """Test that expired roles don't grant permissions."""
        # Given: Manager user with expired manager role
        expired_date = datetime.utcnow() - timedelta(days=1)
        UserRole.create(
            db=db_session,
            user_id=test_manager_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
            expires_at=expired_date,
        )
        db_session.commit()

        # When: Checking permission level
        response = client.get(
            "/api/v1/permissions/user/level",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "organization_id": test_organization.id,
            },
        )

        # Then: Should fall back to default viewer level
        assert response.status_code == 200
        data = response.json()
        assert data["permission_level"] == "viewer"

        # When: Checking manager permission
        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": "read:team_performance",
                "organization_id": test_organization.id,
            },
        )

        # Then: Should not have manager permission
        assert response.status_code == 200
        assert response.json()["has_permission"] is False

    def test_multiple_roles_highest_level_wins(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_admin: User,
        test_manager_user: User,
        manager_role: Role,
        member_role: Role,
        admin_role: Role,
        db_session: Session,
    ) -> None:
        """Test that with multiple roles, highest permission level wins."""
        # Given: User with multiple roles
        UserRole.create(
            db=db_session,
            user_id=test_manager_user.id,
            role_id=member_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        UserRole.create(
            db=db_session,
            user_id=test_manager_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        UserRole.create(
            db=db_session,
            user_id=test_manager_user.id,
            role_id=admin_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Checking permission level
        response = client.get(
            "/api/v1/permissions/user/level",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "organization_id": test_organization.id,
            },
        )

        # Then: Should have highest level (admin)
        assert response.status_code == 200
        data = response.json()
        assert data["permission_level"] == "admin"

        # When: Checking admin permission
        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": "admin:system",
                "organization_id": test_organization.id,
            },
        )

        # Then: Should have admin permission
        assert response.status_code == 200
        assert response.json()["has_permission"] is True

    def test_permission_matrix_validation(
        self,
        client: TestClient,
        admin_token: str,
    ) -> None:
        """Test permission matrix validation."""
        # When: Validating permission matrix
        response = client.post(
            "/api/v1/permissions/matrix/validate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should be valid
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert "hierarchy" in data
        assert data["hierarchy"] == ["viewer", "member", "manager", "admin"]

    def test_permission_matrix_report(
        self,
        client: TestClient,
        admin_token: str,
    ) -> None:
        """Test permission matrix report generation."""
        # When: Getting permission matrix report
        response = client.get(
            "/api/v1/permissions/matrix/report",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should return comprehensive report
        assert response.status_code == 200
        data = response.json()
        assert "hierarchy" in data
        assert "levels" in data
        assert "validation" in data
        assert "total_permissions" in data

        # Should have all permission levels
        assert "viewer" in data["levels"]
        assert "member" in data["levels"]
        assert "manager" in data["levels"]
        assert "admin" in data["levels"]

        # Should be valid
        assert data["validation"] is True

    def test_permission_level_comparison(
        self,
        client: TestClient,
        admin_token: str,
    ) -> None:
        """Test permission level comparison."""
        # When: Comparing viewer and admin levels
        response = client.get(
            "/api/v1/permissions/matrix/compare",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "level1": "viewer",
                "level2": "admin",
            },
        )

        # Then: Should return comparison
        assert response.status_code == 200
        data = response.json()
        assert data["level1"] == "viewer"
        assert data["level2"] == "admin"
        assert "differences" in data
        assert "common" in data["differences"]
        assert "viewer_only" in data["differences"]
        assert "admin_only" in data["differences"]

        # Admin should have more permissions
        assert len(data["differences"]["admin_only"]) > 0

    def test_get_user_all_permissions(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_admin: User,
        test_manager_user: User,
        manager_role: Role,
        db_session: Session,
    ) -> None:
        """Test getting all user permissions."""
        # Given: Manager user with manager role
        UserRole.create(
            db=db_session,
            user_id=test_manager_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Getting all user permissions
        response = client.get(
            "/api/v1/permissions/user/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "organization_id": test_organization.id,
            },
        )

        # Then: Should return all permissions
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert "base" in data["permissions"]
        assert "contexts" in data["permissions"]
        assert "organization" in data["permissions"]["contexts"]
        assert "department" in data["permissions"]["contexts"]

        # Should have manager-level permissions
        assert "read:team_performance" in data["permissions"]["base"]
        assert "org:write:members" in data["permissions"]["contexts"]["organization"]

    def test_service_layer_integration(
        self,
        db_session: Session,
        test_organization: Organization,
        test_admin: User,
        test_manager_user: User,
        manager_role: Role,
    ) -> None:
        """Test service layer integration between RoleService and PermissionMatrix."""
        # Given: Role service and permission matrix
        role_service = RoleService()
        permission_matrix = get_permission_matrix()

        # When: Assigning role via service
        user_role = role_service.assign_role_to_user(
            user_id=test_manager_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigner=test_admin,
            db=db_session,
        )

        # Then: Role assignment should be created
        assert user_role.user_id == test_manager_user.id
        assert user_role.role_id == manager_role.id

        # When: Checking permission via matrix
        has_permission = permission_matrix.check_user_permission(
            test_manager_user,
            "read:team_performance",
            test_organization.id,
        )

        # Then: Should have permission
        assert has_permission is True

        # When: Getting effective level
        effective_level = permission_matrix.get_user_effective_level(
            test_manager_user,
            test_organization.id,
        )

        # Then: Should be manager level
        assert effective_level == PermissionLevel.MANAGER

    def test_permission_denied_for_non_admin(
        self,
        client: TestClient,
        user_token: str,
        test_organization: Organization,
    ) -> None:
        """Test that non-admin users can't access matrix endpoints."""
        # When: Non-admin tries to access matrix report
        response = client.get(
            "/api/v1/permissions/matrix/report",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Then: Should be denied
        assert response.status_code == 403

        # When: Non-admin tries to validate matrix
        response = client.post(
            "/api/v1/permissions/matrix/validate",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Then: Should be denied
        assert response.status_code == 403

    def test_department_specific_permissions(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_admin: User,
        test_manager_user: User,
        manager_role: Role,
        db_session: Session,
    ) -> None:
        """Test department-specific permission checking."""
        # Given: Manager with department-specific role
        UserRole.create(
            db=db_session,
            user_id=test_manager_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            department_id=1,  # Specific department
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Checking permission with department context
        response = client.get(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "permission": "read:team_performance",
                "organization_id": test_organization.id,
                "department_id": 1,
            },
        )

        # Then: Should have permission in that department
        assert response.status_code == 200
        assert response.json()["has_permission"] is True

        # When: Checking permission level with department context
        response = client.get(
            "/api/v1/permissions/user/level",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_manager_user.id,
                "organization_id": test_organization.id,
                "department_id": 1,
            },
        )

        # Then: Should have manager level in that department
        assert response.status_code == 200
        data = response.json()
        assert data["permission_level"] == "manager"
