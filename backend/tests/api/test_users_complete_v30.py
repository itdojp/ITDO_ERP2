from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from httpx import AsyncClient

from app.main import app
from app.models.user_extended import User


class TestUsersCompleteV30:
    """Complete User Management API Tests"""

    @pytest.fixture
    async def mock_user(self):
        """Create a mock user for testing"""
        user = User()
        user.id = "test-user-123"
        user.email = "test@example.com"
        user.username = "testuser"
        user.full_name = "Test User"
        user.is_active = True
        user.is_verified = False
        user.is_superuser = False
        user.created_at = datetime.utcnow()
        return user

    @pytest.fixture
    async def mock_admin_user(self):
        """Create a mock admin user for testing"""
        user = User()
        user.id = "admin-user-123"
        user.email = "admin@example.com"
        user.username = "admin"
        user.full_name = "Admin User"
        user.is_active = True
        user.is_verified = True
        user.is_superuser = True
        user.created_at = datetime.utcnow()
        return user

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_admin_user):
        """Test successful user creation"""
        with (
            patch(
                "app.api.v1.users_complete_v30.require_admin",
                return_value=mock_admin_user,
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_user = User()
            mock_user.id = "new-user-123"
            mock_user.email = "newuser@example.com"
            mock_user.username = "newuser"

            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_user
            mock_crud_instance.log_activity.return_value = None

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/users",
                    json={
                        "email": "newuser@example.com",
                        "username": "newuser",
                        "password": "Test1234!",
                        "confirm_password": "Test1234!",
                        "full_name": "New User",
                    },
                )

            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "newuser@example.com"
            assert "password" not in data

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, mock_admin_user):
        """Test user creation with duplicate email"""
        with (
            patch(
                "app.api.v1.users_complete_v30.require_admin",
                return_value=mock_admin_user,
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            from app.crud.user_extended_v30 import DuplicateError

            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.side_effect = DuplicateError(
                "Email already registered"
            )

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/users",
                    json={
                        "email": "existing@example.com",
                        "username": "newuser",
                        "password": "Test1234!",
                        "confirm_password": "Test1234!",
                        "full_name": "New User",
                    },
                )

            assert response.status_code == 400
            assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, mock_user):
        """Test users list with pagination"""
        with (
            patch(
                "app.api.v1.users_complete_v30.get_current_user", return_value=mock_user
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_users = [mock_user for _ in range(5)]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_multi.return_value = (mock_users, 25)

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/users?page=1&per_page=10")

            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "items" in data
            assert data["total"] == 25
            assert len(data["items"]) == 5
            assert data["page"] == 1
            assert data["per_page"] == 10

    @pytest.mark.asyncio
    async def test_list_users_with_search_filter(self, mock_user):
        """Test users list with search filter"""
        with (
            patch(
                "app.api.v1.users_complete_v30.get_current_user", return_value=mock_user
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            filtered_users = [mock_user]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_multi.return_value = (filtered_users, 1)

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/users?search=test&is_active=true")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1

            # Verify filters were passed correctly
            mock_crud_instance.get_multi.assert_called_once()
            call_args = mock_crud_instance.get_multi.call_args
            filters = call_args[1]["filters"]
            assert filters["search"] == "test"
            assert filters["is_active"]

    @pytest.mark.asyncio
    async def test_get_current_user_info(self, mock_user):
        """Test get current user info"""
        with patch(
            "app.api.v1.users_complete_v30.get_current_user", return_value=mock_user
        ):
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/users/me")

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == mock_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, mock_user):
        """Test get user by ID"""
        with (
            patch(
                "app.api.v1.users_complete_v30.get_current_user", return_value=mock_user
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_by_id.return_value = mock_user

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/users/{mock_user.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == mock_user.id

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, mock_user):
        """Test get user with non-existent ID"""
        with (
            patch(
                "app.api.v1.users_complete_v30.get_current_user", return_value=mock_user
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_by_id.return_value = None

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/users/non-existent-id")

            assert response.status_code == 404
            assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_user_success(self, mock_user):
        """Test successful user update"""
        with (
            patch(
                "app.api.v1.users_complete_v30.get_current_user", return_value=mock_user
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            updated_user = User()
            updated_user.id = mock_user.id
            updated_user.email = mock_user.email
            updated_user.full_name = "Updated Name"

            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.update.return_value = updated_user
            mock_crud_instance.log_activity.return_value = None

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.put(
                    f"/api/v1/users/{mock_user.id}", json={"full_name": "Updated Name"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["full_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_user_unauthorized(self, mock_user):
        """Test update user without authorization"""
        other_user = User()
        other_user.id = "other-user-123"
        other_user.is_superuser = False

        with patch(
            "app.api.v1.users_complete_v30.get_current_user", return_value=other_user
        ):
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.put(
                    f"/api/v1/users/{mock_user.id}", json={"full_name": "Updated Name"}
                )

            assert response.status_code == 403
            assert "Not authorized" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_user_success(self, mock_admin_user):
        """Test successful user deletion"""
        with (
            patch(
                "app.api.v1.users_complete_v30.require_admin",
                return_value=mock_admin_user,
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.delete.return_value = True
            mock_crud_instance.log_activity.return_value = None

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.delete("/api/v1/users/test-user-123")

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_reset_password_success(self, mock_admin_user):
        """Test successful password reset"""
        with (
            patch(
                "app.api.v1.users_complete_v30.require_admin",
                return_value=mock_admin_user,
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.reset_password.return_value = True
            mock_crud_instance.log_activity.return_value = None

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/users/test-user-123/reset-password",
                    json={
                        "new_password": "NewTest1234!",
                        "confirm_password": "NewTest1234!",
                    },
                )

            assert response.status_code == 200
            assert "Password reset successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_verify_user_success(self, mock_admin_user):
        """Test successful user verification"""
        with (
            patch(
                "app.api.v1.users_complete_v30.require_admin",
                return_value=mock_admin_user,
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.verify_user.return_value = True
            mock_crud_instance.log_activity.return_value = None

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post("/api/v1/users/test-user-123/verify")

            assert response.status_code == 200
            assert "User verified successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_get_user_activities(self, mock_user):
        """Test get user activities"""
        with (
            patch(
                "app.api.v1.users_complete_v30.get_current_user", return_value=mock_user
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_activities = []
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_user_activities.return_value = mock_activities

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/users/{mock_user.id}/activities")

            assert response.status_code == 200
            assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_user_stats(self, mock_admin_user):
        """Test get user statistics"""
        with (
            patch(
                "app.api.v1.users_complete_v30.require_admin",
                return_value=mock_admin_user,
            ),
            patch("app.api.v1.users_complete_v30.get_db"),
            patch("app.crud.user_extended_v30.UserCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_stats = {
                "total_users": 100,
                "active_users": 85,
                "verified_users": 75,
                "new_users_this_month": 12,
                "departments": {"IT": 25, "Sales": 30, "Marketing": 15},
            }
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_user_stats.return_value = mock_stats

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/users/stats/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["total_users"] == 100
            assert data["active_users"] == 85
            assert "departments" in data
