"""Organization-Department integration tests."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.organization import Organization
from app.models.user import User
from tests.factories import DepartmentFactory, OrganizationFactory, UserFactory


class TestOrganizationDepartmentIntegration:
    """Test Organization and Department service integration."""

    def test_create_department_in_organization(
        self, db_session: Session, test_admin: User
    ) -> None:
        """Test creating department within organization."""
        # Given
        org = OrganizationFactory.create(db_session, name="統合テスト組織")

        # When
        dept = DepartmentFactory.create_with_organization(
            db_session, org, name="統合テスト部門", code="INTEGRATION-DEPT"
        )

        # Then
        assert dept.organization_id == org.id
        assert dept.organization.name == "統合テスト組織"
        assert dept in org.departments

    def test_department_hierarchy_within_organization(
        self, db_session: Session, test_admin: User
    ) -> None:
        """Test department hierarchy within organization boundaries."""
        # Given
        org = OrganizationFactory.create(db_session, name="階層テスト組織")

        # When
        parent_dept = DepartmentFactory.create_with_organization(
            db_session, org, name="親部門", code="PARENT"
        )
        child_dept = DepartmentFactory.create_with_organization(
            db_session, org, name="子部門", code="CHILD", parent=parent_dept
        )

        # Then
        assert child_dept.parent_id == parent_dept.id
        assert child_dept.organization_id == org.id
        assert parent_dept.organization_id == org.id
        assert child_dept in parent_dept.children

    def test_organization_department_user_assignment(
        self, db_session: Session, test_admin: User
    ) -> None:
        """Test user assignment to organization department."""
        # Given
        org = OrganizationFactory.create(db_session, name="ユーザー割り当て組織")
        dept = DepartmentFactory.create_with_organization(
            db_session, org, name="割り当て部門"
        )
        user = UserFactory.create(db_session, email="dept_user@example.com")

        # When
        user.department_id = dept.id
        db_session.add(user)
        db_session.commit()

        # Then
        assert user.department_id == dept.id
        # User should be accessible through department's organization
        user_orgs = [o.id for o in user.get_organizations()]
        assert org.id in user_orgs

    def test_cross_organization_department_isolation(
        self, db_session: Session, test_admin: User
    ) -> None:
        """Test department isolation between organizations."""
        # Given
        org1 = OrganizationFactory.create(db_session, name="組織1")
        org2 = OrganizationFactory.create(db_session, name="組織2")

        dept1 = DepartmentFactory.create_with_organization(
            db_session, org1, name="組織1部門"
        )
        dept2 = DepartmentFactory.create_with_organization(
            db_session, org2, name="組織2部門"
        )

        # Then
        assert dept1.organization_id != dept2.organization_id
        assert dept1 not in org2.departments
        assert dept2 not in org1.departments

    def test_department_deletion_cascade_rules(
        self, db_session: Session, test_admin: User
    ) -> None:
        """Test department deletion rules within organization."""
        # Given
        org = OrganizationFactory.create(db_session, name="削除テスト組織")
        parent_dept = DepartmentFactory.create_with_organization(
            db_session, org, name="親部門"
        )
        child_dept = DepartmentFactory.create_with_organization(
            db_session, org, name="子部門", parent=parent_dept
        )

        # When - Delete parent department (soft delete)
        parent_dept.soft_delete(deleted_by=test_admin.id)
        db_session.commit()

        # Then - Child should still exist but be orphaned
        db_session.refresh(child_dept)
        assert parent_dept.is_deleted
        assert not child_dept.is_deleted
        # Child department should have parent_id cleared or handled gracefully

    def test_organization_department_permissions_integration(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test permission flow from organization through department."""
        # Given
        system = complete_test_system
        org = system["organization"]
        _dept = list(system["departments"]["root_department"].children)[0]
        admin_user = system["users"]["org_admin"]

        # When - Check user permissions in department context
        permissions = admin_user.get_effective_permissions(org.id)

        # Then
        assert len(permissions) > 0
        # Admin should have department management permissions
        expected_permissions = ["dept.view", "dept.edit", "user.assign"]
        for perm in expected_permissions:
            assert any(perm in p for p in permissions)

    def test_department_manager_permissions(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test department manager specific permissions."""
        # Given
        system = complete_test_system
        org = system["organization"]
        dept_manager = system["users"]["dept_manager"]

        # When
        can_manage_dept = dept_manager.has_permission("dept.manage", org.id)
        can_delete_org = dept_manager.has_permission("org.delete", org.id)

        # Then
        assert can_manage_dept  # Department manager can manage department
        assert not can_delete_org  # But cannot delete entire organization


class TestOrganizationDepartmentAPI:
    """Test Organization-Department API integration."""

    def test_create_department_via_api(
        self, client: TestClient, admin_token: str, test_organization: Organization
    ) -> None:
        """Test department creation via API."""
        # Given
        headers = {"Authorization": f"Bearer {admin_token}"}
        dept_data = {
            "name": "API作成部門",
            "code": "API-DEPT",
            "organization_id": test_organization.id,
            "description": "API経由で作成された部門",
        }

        # When
        response = client.post("/api/v1/departments/", json=dept_data, headers=headers)

        # Then
        assert response.status_code == 201
        created_dept = response.json()
        assert created_dept["name"] == "API作成部門"
        assert created_dept["organization_id"] == test_organization.id

    def test_list_departments_by_organization(
        self, client: TestClient, admin_token: str, test_department_tree
    ) -> None:
        """Test listing departments filtered by organization."""
        # Given
        headers = {"Authorization": f"Bearer {admin_token}"}
        org_id = test_department_tree["root_department"].organization_id

        # When
        response = client.get(
            f"/api/v1/departments/?organization_id={org_id}", headers=headers
        )

        # Then
        assert response.status_code == 200
        departments = response.json()["items"]
        assert len(departments) > 0
        # All departments should belong to the same organization
        for dept in departments:
            assert dept["organization_id"] == org_id

    def test_department_hierarchy_api_response(
        self, client: TestClient, admin_token: str, test_department_tree
    ) -> None:
        """Test department hierarchy in API responses."""
        # Given
        headers = {"Authorization": f"Bearer {admin_token}"}
        root_dept = test_department_tree["root_department"]

        # When
        response = client.get(f"/api/v1/departments/{root_dept.id}", headers=headers)

        # Then
        assert response.status_code == 200
        dept_data = response.json()
        assert dept_data["id"] == root_dept.id
        assert "children" in dept_data or dept_data.get("child_count", 0) > 0
        assert dept_data["parent_id"] is None  # Root department

    def test_cross_organization_department_access_denied(
        self, client: TestClient, manager_token: str, db_session: Session
    ) -> None:
        """Test that users cannot access departments from other organizations."""
        # Given
        other_org = OrganizationFactory.create(db_session, name="他組織")
        other_dept = DepartmentFactory.create_with_organization(
            db_session, other_org, name="他組織部門"
        )
        headers = {"Authorization": f"Bearer {manager_token}"}

        # When
        response = client.get(f"/api/v1/departments/{other_dept.id}", headers=headers)

        # Then
        assert response.status_code in [403, 404]  # Forbidden or Not Found

    def test_department_update_organization_consistency(
        self, client: TestClient, admin_token: str, test_department: Department
    ) -> None:
        """Test department update maintains organization consistency."""
        # Given
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {"name": "更新された部門名", "description": "更新された説明"}

        # When
        response = client.put(
            f"/api/v1/departments/{test_department.id}",
            json=update_data,
            headers=headers,
        )

        # Then
        assert response.status_code == 200
        updated_dept = response.json()
        assert updated_dept["name"] == "更新された部門名"
        # Organization should remain unchanged
        assert updated_dept["organization_id"] == test_department.organization_id


class TestMultiTenantDepartmentAccess:
    """Test multi-tenant access control for departments."""

    def test_organization_admin_department_access(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test organization admin can access all departments in their org."""
        # Given
        system = complete_test_system
        org_admin = system["users"]["org_admin"]
        org = system["organization"]
        departments = system["departments"]

        # When
        admin_orgs = [o.id for o in org_admin.get_organizations()]
        accessible_depts = [
            dept
            for dept in departments.values()
            if hasattr(dept, "organization_id") and dept.organization_id in admin_orgs
        ]

        # Then
        assert org.id in admin_orgs
        assert len(accessible_depts) > 0

    def test_department_manager_limited_access(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test department manager has limited access within organization."""
        # Given
        system = complete_test_system
        dept_manager = system["users"]["dept_manager"]

        # When
        manager_permissions = dept_manager.get_effective_permissions(
            system["organization"].id
        )

        # Then
        # Should have department-level permissions
        dept_permissions = [p for p in manager_permissions if "dept." in p]
        assert len(dept_permissions) > 0

        # Should not have organization-level delete permissions
        org_delete_permissions = [p for p in manager_permissions if "org.delete" in p]
        assert len(org_delete_permissions) == 0

    def test_user_department_boundary_enforcement(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test users can only access data within their department boundaries."""
        # Given
        system = complete_test_system
        regular_user = system["users"]["regular_user"]
        org_id = system["organization"].id

        # When
        user_departments = regular_user.get_departments(org_id)
        user_permissions = regular_user.get_effective_permissions(org_id)

        # Then
        # User should have limited permissions
        assert len(user_permissions) < len(
            system["users"]["org_admin"].get_effective_permissions(org_id)
        )

        # User should only access assigned departments
        if user_departments:
            assigned_dept_ids = [d.id for d in user_departments]
            assert len(assigned_dept_ids) <= 2  # Limited department access
