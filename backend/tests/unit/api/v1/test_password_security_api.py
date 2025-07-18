"""Tests for Password Security API endpoints - Issue #41."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.password_policy import PasswordPolicy
from app.models.role import Role
from app.models.user import User


@pytest.fixture
def regular_user():
    """Mock regular user."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "user@example.com"
    user.full_name = "Regular User"
    user.is_superuser = False
    user.organization_id = 1
    user.roles = []

    return user


@pytest.fixture
def admin_user():
    """Mock admin user."""
    user = Mock(spec=User)
    user.id = 2
    user.email = "admin@example.com"
    user.full_name = "Admin User"
    user.is_superuser = True
    user.organization_id = 1
    user.roles = []

    return user


@pytest.fixture
def security_officer_user():
    """Mock security officer user."""
    user = Mock(spec=User)
    user.id = 3
    user.email = "security@example.com"
    user.full_name = "Security Officer"
    user.is_superuser = False
    user.organization_id = 1

    # Mock security_officer role
    role = Mock(spec=Role)
    role.name = "security_officer"
    user.roles = [role]

    return user


@pytest.fixture
def sample_policy():
    """Sample password policy."""
    policy = Mock(spec=PasswordPolicy)
    policy.id = 1
    policy.name = "Test Policy"
    policy.organization_id = 1
    policy.minimum_length = 8
    policy.require_uppercase = True
    policy.require_lowercase = True
    policy.require_numbers = True
    policy.require_special_chars = True
    policy.password_history_count = 3
    policy.password_expiry_days = 90
    policy.max_failed_attempts = 5
    policy.lockout_duration_minutes = 30
    policy.is_active = True

    return policy


class TestPasswordSecurityAPI:
    """Test suite for Password Security API endpoints."""

    @pytest.mark.asyncio
    async def test_get_password_policy_success(self, client: AsyncClient, regular_user, sample_policy):
        """Test successful password policy retrieval."""
        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.get_policy_for_user", return_value=sample_policy):
                response = await client.get("/api/v1/password-security/policy")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Test Policy"
        assert data["minimum_length"] == 8
        assert data["require_uppercase"] is True

    @pytest.mark.asyncio
    async def test_get_password_policy_organization_specific(self, client: AsyncClient, regular_user, sample_policy):
        """Test getting organization-specific policy."""
        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.get_policy_for_user", return_value=sample_policy):
                response = await client.get("/api/v1/password-security/policy?organization_id=1")

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_password_policy_forbidden(self, client: AsyncClient, regular_user, sample_policy):
        """Test access denied for different organization policy."""
        regular_user.organization_id = 2  # Different org

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            response = await client.get("/api/v1/password-security/policy?organization_id=1")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Access denied" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_password_success(self, client: AsyncClient, regular_user):
        """Test successful password validation."""
        mock_validation_result = {
            "is_valid": True,
            "errors": [],
            "strength_score": 85,
            "policy_name": "Test Policy"
        }

        request_data = {
            "password": "StrongPass123!",
            "user_id": 1,
            "check_history": True
        }

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.validate_password", return_value=mock_validation_result):
                response = await client.post("/api/v1/password-security/validate", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_valid"] is True
        assert data["strength_score"] == 85
        assert data["policy_name"] == "Test Policy"

    @pytest.mark.asyncio
    async def test_validate_password_failure(self, client: AsyncClient, regular_user):
        """Test password validation with errors."""
        mock_validation_result = {
            "is_valid": False,
            "errors": ["Password too short", "Password too weak"],
            "strength_score": 25,
            "policy_name": "Test Policy"
        }

        request_data = {
            "password": "weak",
            "user_id": 1,
            "check_history": True
        }

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.validate_password", return_value=mock_validation_result):
                response = await client.post("/api/v1/password-security/validate", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_valid"] is False
        assert "Password too short" in data["errors"]
        assert data["strength_score"] == 25

    @pytest.mark.asyncio
    async def test_validate_password_forbidden(self, client: AsyncClient, regular_user):
        """Test validation forbidden for different user."""
        request_data = {
            "password": "password",
            "user_id": 999,  # Different user
            "check_history": True
        }

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            response = await client.post("/api/v1/password-security/validate", json=request_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, regular_user):
        """Test successful password change."""
        mock_change_result = {
            "success": True,
            "message": "Password changed successfully",
            "strength_score": 90
        }

        request_data = {
            "current_password": "OldPass123!",
            "new_password": "NewStrongPass456!",
            "force_change": False
        }

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.change_password", return_value=mock_change_result):
                response = await client.post("/api/v1/password-security/change", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["strength_score"] == 90

    @pytest.mark.asyncio
    async def test_change_password_failure(self, client: AsyncClient, regular_user):
        """Test password change failure."""
        mock_change_result = {
            "success": False,
            "errors": ["Current password is incorrect"]
        }

        request_data = {
            "current_password": "WrongPass",
            "new_password": "NewStrongPass456!",
            "force_change": False
        }

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.change_password", return_value=mock_change_result):
                response = await client.post("/api/v1/password-security/change", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert "Current password is incorrect" in data["errors"]

    @pytest.mark.asyncio
    async def test_check_password_strength(self, client: AsyncClient, regular_user, sample_policy):
        """Test password strength checking."""
        request_data = {
            "password": "TestPassword123!",
            "user_id": 1
        }

        # Mock policy strength calculation
        sample_policy.get_password_strength_score.return_value = 75

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.get_policy_for_user", return_value=sample_policy):
                response = await client.post("/api/v1/password-security/strength-check", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["strength_score"] == 75
        assert data["strength_level"] == "good"  # 75 is in "good" range
        assert isinstance(data["feedback"], list)

    @pytest.mark.asyncio
    async def test_get_user_security_status_own_user(self, client: AsyncClient, regular_user):
        """Test getting security status for own user."""
        # Mock user query
        mock_user = Mock()
        mock_user.failed_login_attempts = 1
        mock_user.password_must_change = False
        mock_user.last_login_at = datetime.now(timezone.utc)
        mock_user.password_changed_at = datetime.now(timezone.utc) - timedelta(days=30)

        mock_expiry_info = {
            "is_expired": False,
            "warning": False,
            "days_until_expiry": 60
        }

        mock_policy = Mock()
        mock_policy.name = "Test Policy"

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.is_account_locked", return_value=False):
                with patch("app.services.password_policy_service.PasswordPolicyService.check_password_expiry", return_value=mock_expiry_info):
                    with patch("app.services.password_policy_service.PasswordPolicyService.get_policy_for_user", return_value=mock_policy):
                        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
                            mock_result = Mock()
                            mock_result.scalar_one_or_none.return_value = mock_user
                            mock_execute.return_value = mock_result

                            response = await client.get("/api/v1/password-security/users/1/security-status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == 1
        assert data["account_locked"] is False
        assert data["password_expired"] is False
        assert data["failed_login_attempts"] == 1

    @pytest.mark.asyncio
    async def test_get_user_security_status_forbidden(self, client: AsyncClient, regular_user):
        """Test getting security status forbidden for different user."""
        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            response = await client.get("/api/v1/password-security/users/999/security-status")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_unlock_user_account_success(self, client: AsyncClient, admin_user):
        """Test successful account unlock by admin."""
        request_data = {
            "user_id": 1,
            "reason": "Administrative unlock"
        }

        with patch("app.core.dependencies.get_current_user", return_value=admin_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.unlock_account", return_value=True):
                response = await client.post("/api/v1/password-security/users/1/unlock", params=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "unlocked successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_unlock_user_account_forbidden(self, client: AsyncClient, regular_user):
        """Test account unlock forbidden for non-admin."""
        request_data = {
            "user_id": 1,
            "reason": "Unlock attempt"
        }

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            response = await client.post("/api/v1/password-security/users/1/unlock", params=request_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_force_password_change_success(self, client: AsyncClient, security_officer_user):
        """Test forcing password change by security officer."""
        request_data = {
            "user_id": 1,
            "reason": "Security policy violation"
        }

        # Mock user query
        mock_user = Mock()
        mock_user.password_must_change = False

        with patch("app.core.dependencies.get_current_user", return_value=security_officer_user):
            with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
                with patch("sqlalchemy.ext.asyncio.AsyncSession.commit"):
                    mock_result = Mock()
                    mock_result.scalar_one_or_none.return_value = mock_user
                    mock_execute.return_value = mock_result

                    response = await client.post("/api/v1/password-security/users/1/force-password-change", params=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert mock_user.password_must_change is True

    @pytest.mark.asyncio
    async def test_force_password_change_forbidden(self, client: AsyncClient, regular_user):
        """Test force password change forbidden for regular user."""
        request_data = {
            "user_id": 1,
            "reason": "Unauthorized attempt"
        }

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            response = await client.post("/api/v1/password-security/users/1/force-password-change", params=request_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_password_expiry_info(self, client: AsyncClient, regular_user):
        """Test getting password expiry information."""
        mock_expiry_info = {
            "is_expired": False,
            "days_until_expiry": 60,
            "warning": False,
            "password_age_days": 30,
            "policy_expiry_days": 90
        }

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.check_password_expiry", return_value=mock_expiry_info):
                response = await client.get("/api/v1/password-security/users/1/password-expiry")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_expired"] is False
        assert data["days_until_expiry"] == 60
        assert data["password_age_days"] == 30

    @pytest.mark.asyncio
    async def test_get_password_expiry_info_forbidden(self, client: AsyncClient, regular_user):
        """Test getting password expiry info forbidden for different user."""
        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            response = await client.get("/api/v1/password-security/users/999/password-expiry")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_admin_can_access_all_endpoints(self, client: AsyncClient, admin_user):
        """Test that admin users can access all security endpoints."""
        # Test validation for different user
        request_data = {
            "password": "TestPass123!",
            "user_id": 999,
            "check_history": True
        }

        mock_validation_result = {
            "is_valid": True,
            "errors": [],
            "strength_score": 85,
            "policy_name": "Test Policy"
        }

        with patch("app.core.dependencies.get_current_user", return_value=admin_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.validate_password", return_value=mock_validation_result):
                response = await client.post("/api/v1/password-security/validate", json=request_data)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_password_strength_feedback_generation(self, client: AsyncClient, regular_user, sample_policy):
        """Test that appropriate feedback is generated based on strength score."""
        request_data = {
            "password": "weak",
            "user_id": 1
        }

        # Test weak password (score < 25)
        sample_policy.get_password_strength_score.return_value = 20

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.get_policy_for_user", return_value=sample_policy):
                response = await client.post("/api/v1/password-security/strength-check", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["strength_level"] == "weak"
        assert any("too weak" in feedback.lower() for feedback in data["feedback"])

        # Test strong password (score >= 75)
        sample_policy.get_password_strength_score.return_value = 90

        with patch("app.core.dependencies.get_current_user", return_value=regular_user):
            with patch("app.services.password_policy_service.PasswordPolicyService.get_policy_for_user", return_value=sample_policy):
                response = await client.post("/api/v1/password-security/strength-check", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["strength_level"] == "strong"
        assert any("excellent" in feedback.lower() for feedback in data["feedback"])
