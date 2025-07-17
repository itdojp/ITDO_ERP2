"""
Unit tests for Role Management API endpoints.
ロール管理APIエンドポイントのユニットテスト（Issue #40）
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.main import app
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.role import (
    RoleCreate,
    RoleResponse,
    RoleSummary,
    UserRoleAssignment,
    UserRoleResponse,
)


@pytest.fixture
def mock_role_service():
    """Mock role service for testing."""
    service = MagicMock()
    
    # Mock role data
    mock_role = Role(
        id=1,
        code="TEST_ROLE",
        name="Test Role",
        name_en="Test Role EN",
        description="Test role for unit testing",
        role_type="custom",
        organization_id=1,
        is_active=True,
        is_system=False,
        created_by=1,
        updated_by=1,
    )
    
    # Mock service methods
    service.get_role.return_value = mock_role
    service.list_roles.return_value = ([mock_role], 1)
    service.create_role.return_value = mock_role
    service.update_role.return_value = mock_role
    service.delete_role.return_value = True
    service.user_has_permission.return_value = True
    service.get_role_response.return_value = RoleResponse(
        id=1,
        code="TEST_ROLE",
        name="Test Role",
        name_en="Test Role EN",
        description="Test role for unit testing",
        is_active=True,
        role_type="custom",
        parent_id=None,
        parent=None,
        is_system=False,
        is_inherited=False,
        users_count=0,
        permissions={},
        all_permissions={},
        display_order=0,
        icon=None,
        color=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted_at=None,
        created_by=1,
        updated_by=1,
        deleted_by=None,
        is_deleted=False,
    )
    service.get_role_summary.return_value = RoleSummary(
        id=1,
        code="TEST_ROLE",
        name="Test Role",
        name_en="Test Role EN",
        role_type="custom",
        is_active=True,
        is_system=False,
        description="Test role for unit testing",
        user_count=0,
        permission_count=0,
    )
    
    return service


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.full_name = "Test User"
    user.is_superuser = True
    user.is_active = True
    return user


@pytest.mark.asyncio
class TestRoleManagementAPI:
    """Test cases for Role Management API."""

    async def test_list_roles_success(self, mock_role_service, mock_user):
        """Test successful role listing."""
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/roles/")
                
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert len(data["items"]) == 1
                assert data["items"][0]["code"] == "TEST_ROLE"

    async def test_get_role_success(self, mock_role_service, mock_user):
        """Test successful role retrieval."""
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/roles/1")
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == 1
                assert data["code"] == "TEST_ROLE"
                assert data["name"] == "Test Role"

    async def test_get_role_not_found(self, mock_role_service, mock_user):
        """Test role not found error."""
        mock_role_service.get_role.return_value = None
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/roles/999")
                
                assert response.status_code == 404

    async def test_create_role_success(self, mock_role_service, mock_user):
        """Test successful role creation."""
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'), \
             patch('app.services.organization.OrganizationService') as mock_org_service:
            
            # Mock organization service
            mock_org_instance = MagicMock()
            mock_org_instance.get_organization.return_value = MagicMock(id=1, name="Test Org")
            mock_org_service.return_value = mock_org_instance
            
            role_data = {
                "code": "NEW_ROLE",
                "name": "New Role",
                "description": "A new test role",
                "organization_id": 1,
                "role_type": "custom",
                "is_active": True,
                "permissions": {},
                "display_order": 0,
            }
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/roles/", json=role_data)
                
                assert response.status_code == 201
                data = response.json()
                assert data["code"] == "TEST_ROLE"  # Mocked return value

    async def test_create_role_permission_denied(self, mock_role_service, mock_user):
        """Test role creation with insufficient permissions."""
        mock_user.is_superuser = False
        mock_role_service.user_has_permission.return_value = False
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            role_data = {
                "code": "NEW_ROLE",
                "name": "New Role",
                "organization_id": 1,
                "role_type": "custom",
                "permissions": {},
            }
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/roles/", json=role_data)
                
                assert response.status_code == 403

    async def test_update_role_success(self, mock_role_service, mock_user):
        """Test successful role update."""
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            update_data = {
                "name": "Updated Role Name",
                "description": "Updated description",
            }
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put("/api/v1/roles/1", json=update_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == 1

    async def test_delete_role_success(self, mock_role_service, mock_user):
        """Test successful role deletion."""
        mock_role_service.is_role_in_use.return_value = False
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete("/api/v1/roles/1")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    async def test_delete_role_in_use(self, mock_role_service, mock_user):
        """Test role deletion when role is in use."""
        mock_role_service.is_role_in_use.return_value = True
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete("/api/v1/roles/1")
                
                assert response.status_code == 409

    async def test_assign_role_to_user_success(self, mock_role_service, mock_user):
        """Test successful role assignment to user."""
        mock_user_role = MagicMock(spec=UserRole)
        mock_user_role.id = 1
        mock_user_role.user_id = 2
        mock_user_role.role_id = 1
        mock_user_role.organization_id = 1
        
        mock_role_service.assign_role_to_user.return_value = mock_user_role
        mock_role_service.get_user_role_response.return_value = UserRoleResponse(
            id=1,
            user_id=2,
            role=MagicMock(),
            organization=MagicMock(),
            department=None,
            assigned_by=None,
            assigned_at=datetime.utcnow(),
            valid_from=datetime.utcnow(),
            expires_at=None,
            is_active=True,
            is_primary=False,
            is_expired=False,
            is_valid=True,
            days_until_expiry=None,
            notes=None,
            approval_status=None,
            approved_by=None,
            approved_at=None,
            effective_permissions={},
            created_at=datetime.utcnow(),
            created_by=1,
            updated_at=datetime.utcnow(),
            updated_by=1,
        )
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db') as mock_db:
            
            # Mock user query
            mock_db_instance = MagicMock()
            mock_db_instance.query.return_value.filter.return_value.first.return_value = mock_user
            mock_db.return_value = mock_db_instance
            
            assignment_data = {
                "user_id": 2,
                "role_id": 1,
                "organization_id": 1,
                "department_id": None,
                "valid_from": datetime.utcnow().isoformat(),
                "expires_at": None,
            }
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/roles/assign", json=assignment_data)
                
                assert response.status_code == 201

    async def test_remove_role_from_user_success(self, mock_role_service, mock_user):
        """Test successful role removal from user."""
        mock_role_service.remove_role_from_user.return_value = True
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete("/api/v1/roles/assign/2/1")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    async def test_get_user_roles_success(self, mock_role_service, mock_user):
        """Test successful user roles retrieval."""
        mock_role_service.get_user_roles.return_value = []
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db') as mock_db:
            
            # Mock user query
            mock_db_instance = MagicMock()
            mock_db_instance.query.return_value.filter.return_value.first.return_value = mock_user
            mock_db.return_value = mock_db_instance
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/roles/user/2")
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)

    async def test_get_user_permissions_success(self, mock_role_service, mock_user):
        """Test successful user permissions retrieval."""
        # Create a mock role with permissions
        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.name = "Test Role"
        mock_role.get_all_permissions.return_value = {
            "user.view": {
                "id": 1,
                "code": "user.view",
                "name": "View Users",
                "category": "user",
                "inherited": False,
            }
        }
        
        mock_user_role = MagicMock()
        mock_user_role.role = mock_role
        mock_user_role.organization_id = 1
        
        mock_role_service.get_user_roles.return_value = [mock_user_role]
        mock_role_service.get_role.return_value = mock_role
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db') as mock_db:
            
            # Mock user query
            mock_target_user = MagicMock()
            mock_target_user.id = 2
            mock_target_user.first_name = "Target"
            mock_target_user.last_name = "User"
            mock_target_user.full_name = "Target User"
            mock_target_user.is_superuser = False
            
            mock_db_instance = MagicMock()
            mock_db_instance.query.return_value.filter.return_value.first.return_value = mock_target_user
            mock_db.return_value = mock_db_instance
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/roles/user/2/permissions")
                
                assert response.status_code == 200
                data = response.json()
                assert "user_id" in data
                assert "effective_permissions" in data
                assert "permissions_by_role" in data
                assert data["user_id"] == 2
                assert "user.view" in data["effective_permissions"]

    async def test_get_user_permissions_user_not_found(self, mock_role_service, mock_user):
        """Test user permissions retrieval for non-existent user."""
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db') as mock_db:
            
            # Mock user query to return None
            mock_db_instance = MagicMock()
            mock_db_instance.query.return_value.filter.return_value.first.return_value = None
            mock_db.return_value = mock_db_instance
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/roles/user/999/permissions")
                
                assert response.status_code == 404

    async def test_update_role_permissions_success(self, mock_role_service, mock_user):
        """Test successful role permissions update."""
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            permission_codes = ["user.view", "user.create", "user.edit"]
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/roles/1/permissions",
                    json=permission_codes
                )
                
                assert response.status_code == 200

    async def test_get_role_tree_success(self, mock_role_service, mock_user):
        """Test successful role tree retrieval."""
        from app.schemas.role import RoleTree
        
        mock_role_service.get_role_tree.return_value = [
            RoleTree(
                id=1,
                code="ROOT_ROLE",
                name="Root Role",
                description="Root role",
                role_type="system",
                is_active=True,
                level=0,
                parent_id=None,
                user_count=1,
                permission_count=5,
                children=[],
            )
        ]
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'), \
             patch('app.services.organization.OrganizationService') as mock_org_service:
            
            # Mock organization service
            mock_org_instance = MagicMock()
            mock_org_instance.get_organization.return_value = MagicMock(id=1, name="Test Org")
            mock_org_service.return_value = mock_org_instance
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/roles/organization/1/tree")
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 1
                assert data[0]["code"] == "ROOT_ROLE"

    async def test_list_permissions_success(self, mock_role_service, mock_user):
        """Test successful permissions listing."""
        from app.schemas.role import PermissionBasic
        
        mock_role_service.list_all_permissions.return_value = [
            PermissionBasic(
                id=1,
                code="user.view",
                name="View Users",
                category="user",
                description="View user information",
            )
        ]
        
        with patch('app.api.v1.roles.RoleService', return_value=mock_role_service), \
             patch('app.api.v1.roles.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.roles.get_db'):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/roles/permissions")
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 1
                assert data[0]["code"] == "user.view"