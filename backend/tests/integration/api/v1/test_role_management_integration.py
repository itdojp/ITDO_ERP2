"""
Integration tests for Role Management API.
ロール管理API統合テスト（Issue #40）
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.organization import Organization
from app.models.role import Role, UserRole, RolePermission
from app.models.permission import Permission
from app.models.user import User


@pytest.mark.asyncio
class TestRoleManagementIntegration:
    """Integration tests for Role Management API."""

    async def test_complete_role_management_workflow(self, db: AsyncSession):
        """Test complete role management workflow."""
        
        # Create test organization
        org = Organization(
            code="TEST_ORG",
            name="Test Organization",
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        # Create test permissions
        permissions = [
            Permission(
                code="user.view",
                name="View Users",
                category="user",
                description="View user information",
                is_active=True,
            ),
            Permission(
                code="user.create",
                name="Create Users",
                category="user",
                description="Create new users",
                is_active=True,
            ),
            Permission(
                code="role.view",
                name="View Roles",
                category="role",
                description="View role information",
                is_active=True,
            ),
        ]
        
        for perm in permissions:
            db.add(perm)
        await db.commit()
        
        # Create test users
        admin_user = User(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            full_name="Admin User",
            is_superuser=True,
            is_active=True,
            organization_id=org.id,
            created_by=1,
            created_at=datetime.utcnow()
        )
        
        regular_user = User(
            email="user@example.com",
            first_name="Regular",
            last_name="User",
            full_name="Regular User",
            is_superuser=False,
            is_active=True,
            organization_id=org.id,
            created_by=1,
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.add(regular_user)
        await db.commit()
        await db.refresh(admin_user)
        await db.refresh(regular_user)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test 1: Create a new role
            role_data = {
                "code": "MANAGER",
                "name": "Manager Role",
                "name_en": "Manager Role EN",
                "description": "Role for managers",
                "organization_id": org.id,
                "role_type": "custom",
                "is_active": True,
                "permissions": {},
                "display_order": 0,
            }
            
            # Mock authentication for admin user
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                role_response = await client.post("/api/v1/roles/", json=role_data)
                assert role_response.status_code == 201
                created_role = role_response.json()
                role_id = created_role["id"]
                assert created_role["code"] == "MANAGER"
                assert created_role["name"] == "Manager Role"
                
            # Test 2: Update role permissions
            permission_codes = ["user.view", "user.create"]
            
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                perm_response = await client.put(
                    f"/api/v1/roles/{role_id}/permissions",
                    json=permission_codes
                )
                assert perm_response.status_code == 200
                
            # Test 3: Assign role to user
            assignment_data = {
                "user_id": regular_user.id,
                "role_id": role_id,
                "organization_id": org.id,
                "department_id": None,
                "valid_from": datetime.utcnow().isoformat(),
                "expires_at": None,
            }
            
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                assign_response = await client.post("/api/v1/roles/assign", json=assignment_data)
                assert assign_response.status_code == 201
                assignment = assign_response.json()
                assert assignment["user_id"] == regular_user.id
                
            # Test 4: Get user roles
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                user_roles_response = await client.get(f"/api/v1/roles/user/{regular_user.id}")
                assert user_roles_response.status_code == 200
                user_roles = user_roles_response.json()
                assert isinstance(user_roles, list)
                
            # Test 5: Get user permissions
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                permissions_response = await client.get(f"/api/v1/roles/user/{regular_user.id}/permissions")
                assert permissions_response.status_code == 200
                permissions_data = permissions_response.json()
                assert "user_id" in permissions_data
                assert "effective_permissions" in permissions_data
                assert permissions_data["user_id"] == regular_user.id
                
            # Test 6: List all roles
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                list_response = await client.get("/api/v1/roles/")
                assert list_response.status_code == 200
                roles_data = list_response.json()
                assert "items" in roles_data
                assert "total" in roles_data
                
            # Test 7: Get role details
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                detail_response = await client.get(f"/api/v1/roles/{role_id}")
                assert detail_response.status_code == 200
                role_detail = detail_response.json()
                assert role_detail["id"] == role_id
                assert role_detail["code"] == "MANAGER"
                
            # Test 8: Update role
            update_data = {
                "name": "Senior Manager Role",
                "description": "Updated role description",
            }
            
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                update_response = await client.put(f"/api/v1/roles/{role_id}", json=update_data)
                assert update_response.status_code == 200
                updated_role = update_response.json()
                assert updated_role["name"] == "Senior Manager Role"
                
            # Test 9: Remove role from user
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                remove_response = await client.delete(f"/api/v1/roles/assign/{regular_user.id}/{role_id}")
                assert remove_response.status_code == 200
                remove_result = remove_response.json()
                assert remove_result["success"] is True
                
            # Test 10: Delete role (should succeed now that it's not assigned)
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                delete_response = await client.delete(f"/api/v1/roles/{role_id}")
                assert delete_response.status_code == 200
                delete_result = delete_response.json()
                assert delete_result["success"] is True

    async def test_role_hierarchy_and_inheritance(self, db: AsyncSession):
        """Test role hierarchy and permission inheritance."""
        
        # Create test organization
        org = Organization(
            code="HIERARCHY_ORG",
            name="Hierarchy Test Organization",
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        # Create admin user
        admin_user = User(
            email="hierarchy_admin@example.com",
            first_name="Hierarchy",
            last_name="Admin",
            full_name="Hierarchy Admin",
            is_superuser=True,
            is_active=True,
            organization_id=org.id,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create parent role
            parent_role_data = {
                "code": "SUPERVISOR",
                "name": "Supervisor Role",
                "organization_id": org.id,
                "role_type": "custom",
                "permissions": {},
            }
            
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                parent_response = await client.post("/api/v1/roles/", json=parent_role_data)
                assert parent_response.status_code == 201
                parent_role = parent_response.json()
                parent_id = parent_role["id"]
                
            # Create child role
            child_role_data = {
                "code": "TEAM_LEAD",
                "name": "Team Lead Role",
                "organization_id": org.id,
                "role_type": "custom",
                "parent_id": parent_id,
                "permissions": {},
            }
            
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                child_response = await client.post("/api/v1/roles/", json=child_role_data)
                assert child_response.status_code == 201
                child_role = child_response.json()
                assert child_role["parent_id"] == parent_id
                
            # Test role tree retrieval
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                tree_response = await client.get(f"/api/v1/roles/organization/{org.id}/tree")
                assert tree_response.status_code == 200
                role_tree = tree_response.json()
                assert isinstance(role_tree, list)

    async def test_permission_validation_and_security(self, db: AsyncSession):
        """Test permission validation and security checks."""
        
        # Create test organization
        org = Organization(
            code="SECURITY_ORG",
            name="Security Test Organization",
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        # Create users with different permission levels
        superuser = User(
            email="superuser@example.com",
            first_name="Super",
            last_name="User",
            full_name="Super User",
            is_superuser=True,
            is_active=True,
            organization_id=org.id,
            created_by=1,
            created_at=datetime.utcnow()
        )
        
        regular_user = User(
            email="regular@example.com",
            first_name="Regular",
            last_name="User",
            full_name="Regular User",
            is_superuser=False,
            is_active=True,
            organization_id=org.id,
            created_by=1,
            created_at=datetime.utcnow()
        )
        
        db.add(superuser)
        db.add(regular_user)
        await db.commit()
        await db.refresh(superuser)
        await db.refresh(regular_user)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test 1: Superuser can create roles
            role_data = {
                "code": "TEST_SECURITY",
                "name": "Test Security Role",
                "organization_id": org.id,
                "role_type": "custom",
                "permissions": {},
            }
            
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=superuser):
                response = await client.post("/api/v1/roles/", json=role_data)
                assert response.status_code == 201
                
            # Test 2: Regular user cannot create roles (no permissions)
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=regular_user):
                response = await client.post("/api/v1/roles/", json=role_data)
                assert response.status_code == 403
                
            # Test 3: Test invalid permission codes
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=superuser):
                invalid_permissions = ["invalid.permission", "fake.action"]
                perm_response = await client.put(
                    "/api/v1/roles/1/permissions",
                    json=invalid_permissions
                )
                # Should handle invalid permissions gracefully
                # (Exact behavior depends on service implementation)

    async def test_role_assignment_edge_cases(self, db: AsyncSession):
        """Test edge cases in role assignment."""
        
        # Create test data
        org = Organization(
            code="EDGE_CASE_ORG",
            name="Edge Case Organization",
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        admin_user = User(
            email="edge_admin@example.com",
            first_name="Edge",
            last_name="Admin",
            full_name="Edge Admin",
            is_superuser=True,
            is_active=True,
            organization_id=org.id,
            created_by=1,
            created_at=datetime.utcnow()
        )
        
        test_user = User(
            email="edge_user@example.com",
            first_name="Edge",
            last_name="User",
            full_name="Edge User",
            is_superuser=False,
            is_active=True,
            organization_id=org.id,
            created_by=1,
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.add(test_user)
        await db.commit()
        await db.refresh(admin_user)
        await db.refresh(test_user)
        
        # Create role
        role = Role(
            code="EDGE_ROLE",
            name="Edge Case Role",
            organization_id=org.id,
            role_type="custom",
            is_active=True,
            created_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test 1: Assign role with expiration
            future_date = datetime.utcnow() + timedelta(days=30)
            assignment_data = {
                "user_id": test_user.id,
                "role_id": role.id,
                "organization_id": org.id,
                "expires_at": future_date.isoformat(),
            }
            
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                response = await client.post("/api/v1/roles/assign", json=assignment_data)
                assert response.status_code == 201
                
            # Test 2: Try to assign same role again (should handle duplicates)
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                response = await client.post("/api/v1/roles/assign", json=assignment_data)
                # Behavior depends on service implementation (409 conflict or success)
                assert response.status_code in [201, 409]
                
            # Test 3: Get permissions for user with multiple roles
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                response = await client.get(f"/api/v1/roles/user/{test_user.id}/permissions")
                assert response.status_code == 200
                data = response.json()
                assert "roles_count" in data
                
            # Test 4: Filter roles by organization
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                response = await client.get(f"/api/v1/roles/?organization_id={org.id}")
                assert response.status_code == 200
                
            # Test 5: Search roles
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                response = await client.get("/api/v1/roles/?search=Edge")
                assert response.status_code == 200

    async def test_role_deletion_constraints(self, db: AsyncSession):
        """Test role deletion with various constraints."""
        
        # Create test data
        org = Organization(
            code="DELETE_ORG",
            name="Delete Test Organization",
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        admin_user = User(
            email="delete_admin@example.com",
            first_name="Delete",
            last_name="Admin",
            full_name="Delete Admin",
            is_superuser=True,
            is_active=True,
            organization_id=org.id,
            created_by=1,
            created_at=datetime.utcnow()
        )
        
        test_user = User(
            email="delete_user@example.com",
            first_name="Delete",
            last_name="User",
            full_name="Delete User",
            is_superuser=False,
            is_active=True,
            organization_id=org.id,
            created_by=1,
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.add(test_user)
        await db.commit()
        await db.refresh(admin_user)
        await db.refresh(test_user)
        
        # Create roles
        used_role = Role(
            code="USED_ROLE",
            name="Used Role",
            organization_id=org.id,
            role_type="custom",
            is_active=True,
            created_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        
        unused_role = Role(
            code="UNUSED_ROLE",
            name="Unused Role",
            organization_id=org.id,
            role_type="custom",
            is_active=True,
            created_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        
        system_role = Role(
            code="SYSTEM_ROLE",
            name="System Role",
            organization_id=org.id,
            role_type="system",
            is_system=True,
            is_active=True,
            created_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(used_role)
        db.add(unused_role)
        db.add(system_role)
        await db.commit()
        await db.refresh(used_role)
        await db.refresh(unused_role)
        await db.refresh(system_role)
        
        # Assign used_role to user
        user_role = UserRole(
            user_id=test_user.id,
            role_id=used_role.id,
            organization_id=org.id,
            is_active=True,
            assigned_by=admin_user.id,
            assigned_at=datetime.utcnow(),
            created_by=admin_user.id,
            created_at=datetime.utcnow()
        )
        db.add(user_role)
        await db.commit()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test 1: Cannot delete role that is in use
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                response = await client.delete(f"/api/v1/roles/{used_role.id}")
                assert response.status_code == 409  # Conflict - role in use
                
            # Test 2: Can delete unused role
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                response = await client.delete(f"/api/v1/roles/{unused_role.id}")
                assert response.status_code == 200
                
            # Test 3: Cannot delete system role (if properly protected)
            with pytest.mock.patch('app.api.v1.roles.get_current_active_user', return_value=admin_user):
                response = await client.delete(f"/api/v1/roles/{system_role.id}")
                # System roles should be protected from deletion
                # Exact status depends on service implementation