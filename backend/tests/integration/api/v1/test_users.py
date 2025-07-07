"""Integration tests for User API endpoints."""

import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization import Organization
from app.models.department import Department
from tests.conftest import create_auth_headers


class TestUserAPI:
    """Test cases for User API endpoints."""
    
    def test_list_users_success(
        self,
        client: TestClient,
        test_admin: User,
        admin_token: str,
        db_session: Session
    ) -> None:
        """Test successful list users operation."""
        response = client.get(
            "/api/v1/users",
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1  # At least the admin user
        
    def test_list_users_with_filters(
        self,
        client: TestClient,
        test_organization: Organization,
        test_department: Department,
        admin_token: str,
        db_session: Session
    ) -> None:
        """Test list users with organization and department filters."""
        # Create test user with department
        from tests.factories import UserFactory
        user = UserFactory.create(
            db_session,
            department_id=test_department.id
        )
        
        # Filter by organization
        response = client.get(
            f"/api/v1/users?organization_id={test_organization.id}",
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        
        # Filter by department
        response = client.get(
            f"/api/v1/users?department_id={test_department.id}",
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert any(item["id"] == user.id for item in data["items"])
        
    def test_get_user_success(
        self,
        client: TestClient,
        test_user: User,
        admin_token: str
    ) -> None:
        """Test successful get user operation."""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        
    def test_get_user_not_found(
        self,
        client: TestClient,
        admin_token: str
    ) -> None:
        """Test get user with non-existent ID."""
        response = client.get(
            "/api/v1/users/99999",
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 404
        
    def test_create_user_success(
        self,
        client: TestClient,
        test_organization: Organization,
        test_department: Department,
        admin_token: str
    ) -> None:
        """Test successful create user operation."""
        payload = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User",
            "phone": "080-1234-5678",
            "department_id": test_department.id,
            "is_active": True
        }
        
        response = client.post(
            "/api/v1/users",
            json=payload,
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["full_name"] == payload["full_name"]
        assert data["phone"] == payload["phone"]
        assert data["department_id"] == payload["department_id"]
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password
        
    def test_create_user_duplicate_email(
        self,
        client: TestClient,
        test_user: User,
        admin_token: str
    ) -> None:
        """Test create user with duplicate email."""
        payload = {
            "email": test_user.email,  # Duplicate email
            "password": "SecurePass123!",
            "full_name": "Duplicate User",
            "is_active": True
        }
        
        response = client.post(
            "/api/v1/users",
            json=payload,
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        
    def test_create_user_invalid_password(
        self,
        client: TestClient,
        admin_token: str
    ) -> None:
        """Test create user with invalid password."""
        payload = {
            "email": "weakpass@example.com",
            "password": "weak",  # Too short
            "full_name": "Weak Password User",
            "is_active": True
        }
        
        response = client.post(
            "/api/v1/users",
            json=payload,
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 422
        
    def test_update_user_success(
        self,
        client: TestClient,
        test_user: User,
        admin_token: str
    ) -> None:
        """Test successful update user operation."""
        payload = {
            "full_name": "Updated Name",
            "phone": "090-9876-5432"
        }
        
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=payload,
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == payload["full_name"]
        assert data["phone"] == payload["phone"]
        
    def test_update_user_not_found(
        self,
        client: TestClient,
        admin_token: str
    ) -> None:
        """Test update user with non-existent ID."""
        payload = {"full_name": "Updated Name"}
        
        response = client.put(
            "/api/v1/users/99999",
            json=payload,
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 404
        
    def test_delete_user_success(
        self,
        client: TestClient,
        db_session: Session,
        admin_token: str
    ) -> None:
        """Test successful delete user operation."""
        # Create a user to delete
        from tests.factories import UserFactory
        user = UserFactory.create(db_session)
        
        response = client.delete(
            f"/api/v1/users/{user.id}",
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["id"] == user.id
        
        # Verify user is soft deleted
        db_session.refresh(user)
        assert user.is_deleted is True
        assert user.is_active is False
        
    def test_delete_user_not_found(
        self,
        client: TestClient,
        admin_token: str
    ) -> None:
        """Test delete user with non-existent ID."""
        response = client.delete(
            "/api/v1/users/99999",
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 404
        
    def test_user_self_access(
        self,
        client: TestClient,
        test_user: User,
        user_token: str
    ) -> None:
        """Test user can access their own data."""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=create_auth_headers(user_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        
    def test_user_cannot_access_others(
        self,
        client: TestClient,
        test_admin: User,
        user_token: str
    ) -> None:
        """Test user cannot access other users' data."""
        response = client.get(
            f"/api/v1/users/{test_admin.id}",
            headers=create_auth_headers(user_token)
        )
        
        assert response.status_code == 403
        
    def test_unauthorized_access(
        self,
        client: TestClient
    ) -> None:
        """Test access without authentication."""
        response = client.get("/api/v1/users")
        assert response.status_code == 401
        
        response = client.get("/api/v1/users/1")
        assert response.status_code == 401
        
        response = client.post("/api/v1/users", json={})
        assert response.status_code == 401
        
        response = client.put("/api/v1/users/1", json={})
        assert response.status_code == 401
        
        response = client.delete("/api/v1/users/1")
        assert response.status_code == 401


class TestUserPasswordManagement:
    """Test cases for user password management."""
    
    def test_change_password_success(
        self,
        client: TestClient,
        test_user: User,
        user_token: str
    ) -> None:
        """Test successful password change."""
        payload = {
            "current_password": "TestPassword123!",
            "new_password": "NewSecurePass456!"
        }
        
        response = client.put(
            f"/api/v1/users/{test_user.id}/password",
            json=payload,
            headers=create_auth_headers(user_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password changed successfully"
        
    def test_change_password_wrong_current(
        self,
        client: TestClient,
        test_user: User,
        user_token: str
    ) -> None:
        """Test password change with wrong current password."""
        payload = {
            "current_password": "WrongPassword123!",
            "new_password": "NewSecurePass456!"
        }
        
        response = client.put(
            f"/api/v1/users/{test_user.id}/password",
            json=payload,
            headers=create_auth_headers(user_token)
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "現在のパスワードが正しくありません" in data["detail"]
        
    def test_change_password_weak_new_password(
        self,
        client: TestClient,
        test_user: User,
        user_token: str
    ) -> None:
        """Test password change with weak new password."""
        payload = {
            "current_password": "TestPassword123!",
            "new_password": "weak"
        }
        
        response = client.put(
            f"/api/v1/users/{test_user.id}/password",
            json=payload,
            headers=create_auth_headers(user_token)
        )
        
        assert response.status_code == 422