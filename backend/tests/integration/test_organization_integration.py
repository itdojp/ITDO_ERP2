"""Integration tests for Organization-Role integration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.organization_role_integration import (
    OrganizationRoleIntegrationService,
)


class TestOrganizationIntegration:
    """Test suite for organization-role integration."""

    @pytest.fixture
    def integration_service(
        self, db_session: Session
    ) -> OrganizationRoleIntegrationService:
        """Create integration service instance."""
        return OrganizationRoleIntegrationService(db_session)

    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create test user."""
        from app.core.security import hash_password

        user = User(
            email="test@example.com",
            hashed_password=hash_password("testpassword"),
            full_name="Test User",
            is_active=True,
            is_superuser=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    async def test_complete_organization_creation(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test complete organization creation with default roles."""
        org_data = {
            "organization": {
                "code": "TEST001",
                "name": "Test Corporation",
                "description": "Test organization for integration testing",
                "is_active": True,
            }
        }

        response = client.post(
            "/api/v1/integration/organizations/complete",
            json=org_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        result = response.json()

        # Verify organization creation
        assert "organization" in result
        assert result["organization"]["code"] == "TEST001"
        assert result["organization"]["name"] == "Test Corporation"

        # Verify default roles creation
        assert "roles" in result
        roles = result["roles"]
        assert len(roles) >= 4  # Should have 4 default roles

        # Check for expected role types
        role_codes = [role["code"] for role in roles]
        org_id = result["organization"]["id"]
        expected_roles = [
            f"org_admin_{org_id}",
            f"org_manager_{org_id}",
            f"org_member_{org_id}",
            f"org_viewer_{org_id}",
        ]

        for expected_role in expected_roles:
            assert any(expected_role in code for code in role_codes)

        # Verify creator gets admin role
        admin_role = next(
            (role for role in roles if "admin" in role["code"]), None
        )
        assert admin_role is not None
        assert "organization" in admin_role["permissions"]

    async def test_organization_with_roles_retrieval(
        self,
        integration_service: OrganizationRoleIntegrationService,
        test_user: User,
        db_session: Session,
    ):
        """Test retrieving organization with role information."""
        from app.schemas.organization import OrganizationCreate

        # Create organization with roles
        org_data = OrganizationCreate(
            code="TEST002",
            name="Test Org 2",
            is_active=True,
            settings=None,  # Avoid dict serialization issue
        )

        organization = await integration_service.create_organization_with_default_roles(
            org_data, test_user.id
        )

        # Retrieve organization with roles
        org_with_roles = await integration_service.get_organization_with_roles(
            organization.id, test_user.id
        )

        # Verify structure
        assert org_with_roles.organization.id == organization.id
        assert len(org_with_roles.available_roles) >= 4
        assert len(org_with_roles.user_roles) >= 1  # User should have admin role

        # Verify user has admin role
        user_role_codes = [
            ur.role.code for ur in org_with_roles.user_roles if ur.is_active
        ]
        assert any("admin" in code for code in user_role_codes)

    async def test_organization_cloning(
        self,
        integration_service: OrganizationRoleIntegrationService,
        test_user: User,
        db_session: Session,
    ):
        """Test cloning organization structure."""
        from app.schemas.organization import OrganizationCreate

        # Create source organization
        source_data = OrganizationCreate(
            code="SOURCE001",
            name="Source Organization",
            is_active=True,
            settings=None,
        )

        source_org = await integration_service.create_organization_with_default_roles(
            source_data, test_user.id
        )

        # Clone to target organization
        target_data = OrganizationCreate(
            code="TARGET001",
            name="Target Organization",
            is_active=True,
            settings=None,
        )

        target_org = integration_service.clone_organization_structure(
            source_org.id, target_data, test_user.id
        )

        # Verify target organization exists
        assert target_org.id != source_org.id
        assert target_org.code == "TARGET001"

        # Verify roles were cloned
        source_roles = integration_service.role_service.get_organization_roles(
            source_org.id
        )
        target_roles = integration_service.role_service.get_organization_roles(
            target_org.id
        )

        # Should have similar number of roles (excluding system roles)
        source_custom_roles = [r for r in source_roles if not r.is_system]
        target_custom_roles = [r for r in target_roles if not r.is_system]
        assert len(target_custom_roles) >= len(source_custom_roles)

    async def test_user_organization_transfer(
        self,
        integration_service: OrganizationRoleIntegrationService,
        test_user: User,
        db_session: Session,
    ):
        """Test transferring user between organizations."""
        from app.schemas.organization import OrganizationCreate

        # Create two organizations
        org1_data = OrganizationCreate(
            code="ORG001", name="Organization 1", is_active=True, settings=None
        )
        org2_data = OrganizationCreate(
            code="ORG002", name="Organization 2", is_active=True, settings=None
        )

        org1 = await integration_service.create_organization_with_default_roles(
            org1_data, test_user.id
        )
        org2 = await integration_service.create_organization_with_default_roles(
            org2_data, test_user.id
        )

        # Create another user for transfer
        from app.core.security import hash_password

        transfer_user = User(
            email="transfer@example.com",
            hashed_password=hash_password("transferpassword"),
            full_name="Transfer User",
            is_active=True,
        )
        db_session.add(transfer_user)
        db_session.commit()
        db_session.refresh(transfer_user)

        # Assign user to org1
        org1_roles = integration_service.role_service.get_organization_roles(org1.id)
        member_role = next((r for r in org1_roles if "member" in r.code), None)
        assert member_role is not None

        integration_service.role_service.assign_user_role(
            user_id=transfer_user.id,
            role_id=member_role.id,
            organization_id=org1.id,
            assigned_by=test_user.id,
        )

        # Get org2 member role for transfer
        org2_roles = integration_service.role_service.get_organization_roles(org2.id)
        org2_member_role = next((r for r in org2_roles if "member" in r.code), None)
        assert org2_member_role is not None

        # Transfer user from org1 to org2
        result = integration_service.transfer_user_organization(
            user_id=transfer_user.id,
            from_org_id=org1.id,
            to_org_id=org2.id,
            new_role_code=org2_member_role.code,
            transferred_by=test_user.id,
        )

        # Verify transfer result
        assert result["status"] == "completed"
        assert result["old_roles_deactivated"] >= 1
        assert result["new_role_assigned"] is not None

        # Verify user no longer has active roles in org1
        org1_user_roles = integration_service.role_service.get_user_roles(
            transfer_user.id, organization_id=org1.id
        )
        active_org1_roles = [ur for ur in org1_user_roles if ur.is_active]
        assert len(active_org1_roles) == 0

        # Verify user has active role in org2
        org2_user_roles = integration_service.role_service.get_user_roles(
            transfer_user.id, organization_id=org2.id
        )
        active_org2_roles = [ur for ur in org2_user_roles if ur.is_active]
        assert len(active_org2_roles) >= 1

    async def test_organization_hierarchy_with_roles(
        self,
        integration_service: OrganizationRoleIntegrationService,
        test_user: User,
        db_session: Session,
    ):
        """Test getting organization hierarchy with role information."""
        from app.schemas.organization import OrganizationCreate

        # Create parent organization
        parent_data = OrganizationCreate(
            code="PARENT001",
            name="Parent Organization",
            is_active=True,
            settings=None,
        )

        parent_org = await integration_service.create_organization_with_default_roles(
            parent_data, test_user.id
        )

        # Create child organization
        child_data = OrganizationCreate(
            code="CHILD001",
            name="Child Organization",
            parent_id=parent_org.id,
            is_active=True,
            settings=None,
        )

        await integration_service.create_organization_with_default_roles(
            child_data, test_user.id
        )

        # Get hierarchy with roles
        hierarchy = integration_service.get_organization_hierarchy_with_roles()

        # Find our organizations in hierarchy
        def find_org_in_hierarchy(org_id, nodes):
            for node in nodes:
                if node.get("id") == org_id:
                    return node
                if "children" in node:
                    found = find_org_in_hierarchy(org_id, node["children"])
                    if found:
                        return found
            return None

        parent_node = find_org_in_hierarchy(parent_org.id, hierarchy)
        assert parent_node is not None
        assert "role_summary" in parent_node
        assert parent_node["role_summary"]["total_roles"] >= 4

    async def test_bulk_role_assignment(
        self,
        integration_service: OrganizationRoleIntegrationService,
        test_user: User,
        db_session: Session,
    ):
        """Test bulk role assignment functionality."""
        from app.schemas.organization import OrganizationCreate

        # Create organization
        org_data = OrganizationCreate(
            code="BULK001",
            name="Bulk Test Organization",
            is_active=True,
            settings=None,
        )

        organization = await integration_service.create_organization_with_default_roles(
            org_data, test_user.id
        )

        # Create additional users
        from app.core.security import hash_password

        users = []
        for i in range(3):
            user = User(
                email=f"bulk{i}@example.com",
                hashed_password=hash_password(f"bulkpassword{i}"),
                full_name=f"Bulk User {i}",
                is_active=True,
            )
            db_session.add(user)
            users.append(user)

        db_session.commit()
        for user in users:
            db_session.refresh(user)

        # Get organization roles
        org_roles = integration_service.role_service.get_organization_roles(
            organization.id
        )
        member_role = next((r for r in org_roles if "member" in r.code), None)
        assert member_role is not None

        # Prepare bulk assignments
        assignments = [
            {"user_id": user.id, "role_code": member_role.code}
            for user in users
        ]

        # Perform bulk assignment
        result = integration_service.bulk_role_assignment(
            organization_id=organization.id,
            role_assignments=assignments,
            assigned_by=test_user.id,
        )

        # Verify results
        assert result["total_assignments"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0

        # Verify users have roles
        for user in users:
            user_roles = integration_service.role_service.get_user_roles(
                user.id, organization_id=organization.id
            )
            active_roles = [ur for ur in user_roles if ur.is_active]
            assert len(active_roles) >= 1

    async def test_organization_access_matrix(
        self,
        integration_service: OrganizationRoleIntegrationService,
        test_user: User,
        db_session: Session,
    ):
        """Test organization access matrix generation."""
        from app.schemas.organization import OrganizationCreate

        # Create organization
        org_data = OrganizationCreate(
            code="MATRIX001",
            name="Matrix Test Organization",
            is_active=True,
            settings=None,
        )

        organization = await integration_service.create_organization_with_default_roles(
            org_data, test_user.id
        )

        # Get access matrix
        access_matrix = integration_service.get_organization_access_matrix(
            organization.id
        )

        # Verify matrix structure
        assert "organization_id" in access_matrix
        assert access_matrix["organization_id"] == organization.id
        assert "permission_matrix" in access_matrix
        assert "user_role_mapping" in access_matrix
        assert "summary" in access_matrix

        # Verify matrix content
        permission_matrix = access_matrix["permission_matrix"]
        assert len(permission_matrix) >= 4  # Should have default roles

        # Verify admin role exists and has proper permissions
        admin_role_key = next(
            (key for key in permission_matrix.keys() if "admin" in key), None
        )
        assert admin_role_key is not None
        assert "permissions" in permission_matrix[admin_role_key]
        assert "user_count" in permission_matrix[admin_role_key]

        # Verify summary
        summary = access_matrix["summary"]
        assert summary["total_roles"] >= 4
        assert summary["total_users"] >= 1  # At least the test user

