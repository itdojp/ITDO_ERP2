"""Tests for permission inheritance API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_test_organization, create_test_user
from tests.factories.permission import create_test_permission


@pytest.mark.skip(reason="create_test_role and create_test_user_role not yet implemented")
class TestPermissionInheritanceAPI:
    """Test permission inheritance API endpoints."""

    def test_create_inheritance_rule_success(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test successful creation of inheritance rule."""
        # Given: Parent and child roles
        org = create_test_organization(db_session)
        parent_role = create_test_role(
            db_session, organization_id=org.id, code="PARENT_ROLE"
        )
        child_role = create_test_role(
            db_session, organization_id=org.id, code="CHILD_ROLE"
        )
        db_session.commit()

        # When: Creating inheritance rule via API
        response = client.post(
            "/api/v1/permission-inheritance/inheritance-rules",
            json={
                "parent_role_id": parent_role.id,
                "child_role_id": child_role.id,
                "inherit_all": True,
                "priority": 50,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Rule should be created successfully
        assert response.status_code == 200
        data = response.json()
        assert data["parent_role_id"] == parent_role.id
        assert data["child_role_id"] == child_role.id
        assert data["inherit_all"] is True
        assert data["priority"] == 50

    def test_create_inheritance_rule_circular_error(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test circular inheritance prevention via API."""
        # Given: Two roles with existing inheritance
        org = create_test_organization(db_session)
        role_a = create_test_role(db_session, organization_id=org.id, code="ROLE_A")
        role_b = create_test_role(db_session, organization_id=org.id, code="ROLE_B")
        db_session.commit()

        # Create A -> B inheritance
        client.post(
            "/api/v1/permission-inheritance/inheritance-rules",
            json={
                "parent_role_id": role_a.id,
                "child_role_id": role_b.id,
                "inherit_all": True,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # When: Trying to create B -> A (circular)
        response = client.post(
            "/api/v1/permission-inheritance/inheritance-rules",
            json={
                "parent_role_id": role_b.id,
                "child_role_id": role_a.id,
                "inherit_all": True,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should return error
        assert response.status_code == 400
        assert "Circular inheritance" in response.json()["detail"]

    def test_get_effective_permissions(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test getting effective permissions for a role."""
        # Given: Role with inherited permissions
        org = create_test_organization(db_session)
        parent_role = create_test_role(
            db_session, organization_id=org.id, code="PARENT_ROLE"
        )
        child_role = create_test_role(
            db_session, organization_id=org.id, code="CHILD_ROLE"
        )
        permission = create_test_permission(db_session, code="test:permission")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Create inheritance and grant permission
        from app.services.permission_inheritance import PermissionInheritanceService

        service = PermissionInheritanceService(db_session)
        service.create_inheritance_rule(
            parent_role_id=parent_role.id,
            child_role_id=child_role.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )
        service.grant_permission_to_role(
            parent_role.id, permission.id, admin, db_session
        )

        # When: Getting effective permissions via API
        response = client.get(
            f"/api/v1/permission-inheritance/roles/{child_role.id}/effective-permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should return inherited permission
        assert response.status_code == 200
        permissions = response.json()
        assert permissions.get("test:permission") is True

    def test_get_effective_permissions_with_source(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test getting effective permissions with source information."""
        # Given: Role with inherited permissions
        org = create_test_organization(db_session)
        parent_role = create_test_role(
            db_session, organization_id=org.id, code="PARENT_ROLE"
        )
        child_role = create_test_role(
            db_session, organization_id=org.id, code="CHILD_ROLE"
        )
        permission = create_test_permission(db_session, code="test:permission")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Create inheritance and grant permission
        from app.services.permission_inheritance import PermissionInheritanceService

        service = PermissionInheritanceService(db_session)
        service.create_inheritance_rule(
            parent_role_id=parent_role.id,
            child_role_id=child_role.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )
        service.grant_permission_to_role(
            parent_role.id, permission.id, admin, db_session
        )

        # When: Getting effective permissions with source info
        response = client.get(
            f"/api/v1/permission-inheritance/roles/{child_role.id}/effective-permissions?include_source=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should return permission with source information
        assert response.status_code == 200
        permissions = response.json()
        perm_info = permissions.get("test:permission")
        assert perm_info is not None
        assert perm_info["granted"] is True
        assert perm_info["source_role_code"] == "PARENT_ROLE"
        assert perm_info["inheritance_depth"] == 1

    def test_get_inheritance_audit_logs(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test getting inheritance audit logs."""
        # Given: Role with inheritance changes
        org = create_test_organization(db_session)
        parent_role = create_test_role(
            db_session, organization_id=org.id, code="PARENT_ROLE"
        )
        child_role = create_test_role(
            db_session, organization_id=org.id, code="CHILD_ROLE"
        )
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Create inheritance rule to generate audit log
        from app.services.permission_inheritance import PermissionInheritanceService

        service = PermissionInheritanceService(db_session)
        service.create_inheritance_rule(
            parent_role_id=parent_role.id,
            child_role_id=child_role.id,
            creator=admin,
            db=db_session,
            inherit_all=True,
        )

        # When: Getting audit logs via API
        response = client.get(
            f"/api/v1/permission-inheritance/roles/{child_role.id}/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should return audit logs
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) >= 1
        assert logs[0]["action"] == "inheritance_created"

    def test_create_permission_dependency(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test creating permission dependency."""
        # Given: Two permissions
        perm_read = create_test_permission(db_session, code="resource:read")
        perm_write = create_test_permission(db_session, code="resource:write")
        db_session.commit()

        # When: Creating dependency via API
        response = client.post(
            "/api/v1/permission-inheritance/permission-dependencies",
            json={
                "permission_id": perm_write.id,
                "requires_permission_id": perm_read.id,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Dependency should be created
        assert response.status_code == 200
        data = response.json()
        assert data["permission_id"] == perm_write.id
        assert data["requires_permission_id"] == perm_read.id
        assert data["permission_code"] == "resource:write"
        assert data["requires_permission_code"] == "resource:read"

    def test_unauthorized_access(self, client: TestClient, db_session: Session) -> None:
        """Test unauthorized access to inheritance endpoints."""
        # When: Accessing without token
        response = client.get(
            "/api/v1/permission-inheritance/roles/1/effective-permissions"
        )

        # Then: Should return unauthorized or forbidden
        assert response.status_code in [401, 403]
