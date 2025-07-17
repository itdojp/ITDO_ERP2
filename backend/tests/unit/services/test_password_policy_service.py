"""Tests for Password Policy Service - Issue #41."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

from app.services.password_policy_service import PasswordPolicyService
from app.models.password_policy import PasswordPolicy
from app.models.password_history import PasswordHistory
from app.models.user import User


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def password_policy_service(mock_db):
    """Password policy service instance."""
    return PasswordPolicyService(mock_db)


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.phone = "123-456-7890"
    user.organization_id = 1
    user.hashed_password = "hashed_old_password"
    user.password_changed_at = datetime.now(timezone.utc) - timedelta(days=30)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.password_must_change = False
    return user


@pytest.fixture
def sample_policy():
    """Sample password policy for testing."""
    policy = Mock(spec=PasswordPolicy)
    policy.id = 1
    policy.name = "Test Policy"
    policy.organization_id = 1
    policy.minimum_length = 8
    policy.require_uppercase = True
    policy.require_lowercase = True
    policy.require_numbers = True
    policy.require_special_chars = True
    policy.special_chars_set = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    policy.password_history_count = 3
    policy.password_expiry_days = 90
    policy.password_warning_days = 7
    policy.max_failed_attempts = 5
    policy.lockout_duration_minutes = 30
    policy.disallow_user_info = True
    policy.disallow_common_passwords = True
    policy.is_active = True
    
    # Mock methods
    policy.validate_password_complexity.return_value = []
    policy.get_password_strength_score.return_value = 75
    
    return policy


class TestPasswordPolicyService:
    """Test suite for PasswordPolicyService."""

    @pytest.mark.asyncio
    async def test_get_policy_for_user_organization_specific(
        self, password_policy_service, mock_db, sample_user, sample_policy
    ):
        """Test getting organization-specific policy for user."""
        # Mock user query
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        # Mock org policy query (first call)
        org_policy_result = Mock()
        org_policy_result.scalar_one_or_none.return_value = sample_policy
        mock_db.execute.return_value = org_policy_result
        
        policy = await password_policy_service.get_policy_for_user(1)
        
        assert policy == sample_policy
        assert mock_db.execute.call_count >= 1

    @pytest.mark.asyncio
    async def test_get_policy_for_user_global_fallback(
        self, password_policy_service, mock_db, sample_user, sample_policy
    ):
        """Test falling back to global policy when no org policy exists."""
        sample_user.organization_id = 1
        sample_policy.organization_id = None  # Global policy
        
        # Mock user query
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        
        # Mock org policy query (returns None), then global policy query
        org_policy_result = Mock()
        org_policy_result.scalar_one_or_none.return_value = None
        
        global_policy_result = Mock()
        global_policy_result.scalar_one_or_none.return_value = sample_policy
        
        mock_db.execute.side_effect = [user_result, org_policy_result, global_policy_result]
        
        policy = await password_policy_service.get_policy_for_user(1)
        
        assert policy == sample_policy

    @pytest.mark.asyncio
    async def test_create_default_policy(self, password_policy_service, mock_db):
        """Test creating default password policy."""
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        policy = await password_policy_service.create_default_policy()
        
        assert policy.name == "Default Security Policy"
        assert policy.minimum_length == 8
        assert policy.require_uppercase is True
        assert policy.password_history_count == 3
        assert policy.max_failed_attempts == 5
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_password_success(
        self, password_policy_service, mock_db, sample_user, sample_policy
    ):
        """Test successful password validation."""
        # Mock user query
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        # Mock get_policy_for_user
        password_policy_service.get_policy_for_user = AsyncMock(return_value=sample_policy)
        password_policy_service._check_common_passwords = AsyncMock(return_value=[])
        password_policy_service._check_password_history = AsyncMock(return_value=[])
        
        # Mock policy validation
        sample_policy.validate_password_complexity.return_value = []
        sample_policy.get_password_strength_score.return_value = 85
        
        result = await password_policy_service.validate_password("StrongPass123!", 1)
        
        assert result["is_valid"] is True
        assert result["errors"] == []
        assert result["strength_score"] == 85
        assert result["policy_name"] == "Test Policy"

    @pytest.mark.asyncio
    async def test_validate_password_failure(
        self, password_policy_service, mock_db, sample_user, sample_policy
    ):
        """Test password validation with errors."""
        # Mock user query
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        # Mock get_policy_for_user
        password_policy_service.get_policy_for_user = AsyncMock(return_value=sample_policy)
        password_policy_service._check_common_passwords = AsyncMock(return_value=["Password is too common"])
        password_policy_service._check_password_history = AsyncMock(return_value=[])
        
        # Mock policy validation with errors
        sample_policy.validate_password_complexity.return_value = ["Password too short"]
        sample_policy.get_password_strength_score.return_value = 25
        
        result = await password_policy_service.validate_password("weak", 1)
        
        assert result["is_valid"] is False
        assert "Password too short" in result["errors"]
        assert "Password is too common" in result["errors"]
        assert result["strength_score"] == 25

    @pytest.mark.asyncio
    async def test_check_common_passwords(self, password_policy_service):
        """Test common password detection."""
        # Test common password
        errors = await password_policy_service._check_common_passwords("password")
        assert len(errors) > 0
        assert "too common" in errors[0].lower()
        
        # Test sequential numbers
        errors = await password_policy_service._check_common_passwords("123456789")
        assert len(errors) > 0
        assert "sequential" in errors[0].lower()
        
        # Test all same character
        errors = await password_policy_service._check_common_passwords("aaaaaaa")
        assert len(errors) > 0
        assert "same character" in errors[0].lower()
        
        # Test strong password
        errors = await password_policy_service._check_common_passwords("Str0ng!P@ssw0rd")
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_check_password_history(
        self, password_policy_service, mock_db
    ):
        """Test password history checking."""
        from app.core.security import hash_password
        
        # Mock password history query
        history_record = Mock(spec=PasswordHistory)
        history_record.password_hash = hash_password("old_password")
        
        history_result = Mock()
        history_result.scalars.return_value.all.return_value = [history_record]
        mock_db.execute.return_value = history_result
        
        # Test reused password
        errors = await password_policy_service._check_password_history("old_password", 1, 3)
        assert len(errors) > 0
        assert "same as any of the last" in errors[0]
        
        # Test new password
        errors = await password_policy_service._check_password_history("new_password", 1, 3)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, password_policy_service, mock_db, sample_user
    ):
        """Test successful password change."""
        # Mock user query
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        # Mock password validation
        password_policy_service.validate_password = AsyncMock(return_value={
            "is_valid": True,
            "errors": [],
            "strength_score": 90
        })
        password_policy_service.get_policy_for_user = AsyncMock()
        password_policy_service._cleanup_password_history = AsyncMock()
        
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        
        result = await password_policy_service.change_password(
            user_id=1,
            new_password="NewStr0ng!Pass",
            current_password="old_password"
        )
        
        assert result["success"] is True
        assert result["strength_score"] == 90
        assert sample_user.password_must_change is False
        assert sample_user.failed_login_attempts == 0

    @pytest.mark.asyncio
    async def test_change_password_invalid_current(
        self, password_policy_service, mock_db, sample_user
    ):
        """Test password change with invalid current password."""
        # Mock user query
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        result = await password_policy_service.change_password(
            user_id=1,
            new_password="NewStr0ng!Pass",
            current_password="wrong_password"
        )
        
        assert result["success"] is False
        assert "Current password is incorrect" in result["errors"]

    @pytest.mark.asyncio
    async def test_check_password_expiry(
        self, password_policy_service, mock_db, sample_user, sample_policy
    ):
        """Test password expiry checking."""
        # Set password changed 85 days ago (close to 90-day expiry)
        sample_user.password_changed_at = datetime.now(timezone.utc) - timedelta(days=85)
        
        # Mock user query
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        password_policy_service.get_policy_for_user = AsyncMock(return_value=sample_policy)
        
        result = await password_policy_service.check_password_expiry(1)
        
        assert result["is_expired"] is False
        assert result["warning"] is True  # Within 7-day warning period
        assert result["days_until_expiry"] == 5
        assert result["password_age_days"] == 85

    @pytest.mark.asyncio
    async def test_handle_failed_login(
        self, password_policy_service, mock_db, sample_user, sample_policy
    ):
        """Test failed login handling and lockout."""
        sample_user.failed_login_attempts = 4  # One before lockout
        
        # Mock user query
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        password_policy_service.get_policy_for_user = AsyncMock(return_value=sample_policy)
        mock_db.commit = AsyncMock()
        
        result = await password_policy_service.handle_failed_login(1)
        
        assert result["locked"] is True
        assert sample_user.failed_login_attempts == 5
        assert sample_user.locked_until is not None
        assert result["lockout_duration_minutes"] == 30

    @pytest.mark.asyncio
    async def test_unlock_account(
        self, password_policy_service, mock_db, sample_user
    ):
        """Test manual account unlock."""
        sample_user.failed_login_attempts = 5
        sample_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        # Mock user query
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        mock_db.commit = AsyncMock()
        
        result = await password_policy_service.unlock_account(1)
        
        assert result is True
        assert sample_user.failed_login_attempts == 0
        assert sample_user.locked_until is None

    @pytest.mark.asyncio
    async def test_is_account_locked(
        self, password_policy_service, mock_db, sample_user
    ):
        """Test account lock status checking."""
        # Test locked account
        sample_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        is_locked = await password_policy_service.is_account_locked(1)
        assert is_locked is True
        
        # Test expired lock (should be cleared)
        sample_user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=10)
        mock_db.commit = AsyncMock()
        
        is_locked = await password_policy_service.is_account_locked(1)
        assert is_locked is False
        assert sample_user.locked_until is None

    def test_password_policy_properties(self, sample_policy):
        """Test password policy property methods."""
        # Test global policy check
        sample_policy.organization_id = None
        assert sample_policy.is_global_policy is True
        
        sample_policy.organization_id = 1
        assert sample_policy.is_global_policy is False