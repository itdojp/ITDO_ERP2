"""
Feature Flag System Tests
Comprehensive test suite for feature flag functionality
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.feature_flags import (
    FeatureFlagContext,
    FeatureFlagRule,
    FeatureFlagService,
    FeatureFlagStrategy,
    get_feature_variant,
    is_feature_enabled,
)


class TestFeatureFlagService:
    """Test suite for FeatureFlagService"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis_mock = AsyncMock()
        return redis_mock

    @pytest.fixture
    def service(self, mock_redis):
        """Feature flag service instance with mocked Redis"""
        return FeatureFlagService(redis_client=mock_redis)

    @pytest.fixture
    def context(self):
        """Sample evaluation context"""
        return FeatureFlagContext(
            user_id="user123",
            organization_id="org456",
            user_roles=["premium_user", "beta_tester"],
            environment="development",
            request_ip="192.168.1.100",
            custom_attributes={"country": "US", "subscription_tier": "premium"}
        )

    @pytest.mark.asyncio
    async def test_get_flag_all_on(self, service, context, mock_redis):
        """Test ALL_ON strategy always returns True"""
        flag_config = {
            "key": "test_flag",
            "enabled": True,
            "strategy": FeatureFlagStrategy.ALL_ON,
            "rules": [],
            "environments": {}
        }
        mock_redis.get.return_value = None  # No cache
        service._get_flag_config = AsyncMock(return_value=flag_config)
        service._cache_evaluation = AsyncMock()
        service._log_evaluation = AsyncMock()

        result = await service.get_flag("test_flag", context)

        assert result is True
        service._log_evaluation.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_flag_all_off(self, service, context, mock_redis):
        """Test ALL_OFF strategy always returns False"""
        flag_config = {
            "key": "test_flag",
            "enabled": True,
            "strategy": FeatureFlagStrategy.ALL_OFF,
            "rules": [],
            "environments": {}
        }
        service._get_flag_config = AsyncMock(return_value=flag_config)
        service._cache_evaluation = AsyncMock()
        service._log_evaluation = AsyncMock()

        result = await service.get_flag("test_flag", context)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_flag_disabled_globally(self, service, context):
        """Test globally disabled flag always returns False"""
        flag_config = {
            "key": "test_flag",
            "enabled": False,
            "strategy": FeatureFlagStrategy.ALL_ON,
            "rules": [],
            "environments": {}
        }
        service._get_flag_config = AsyncMock(return_value=flag_config)
        service._cache_evaluation = AsyncMock()
        service._log_evaluation = AsyncMock()

        result = await service.get_flag("test_flag", context)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_flag_nonexistent(self, service, context):
        """Test nonexistent flag returns False"""
        service._get_flag_config = AsyncMock(return_value=None)

        result = await service.get_flag("nonexistent_flag", context)

        assert result is False

    @pytest.mark.asyncio
    async def test_percentage_rollout(self, service, context):
        """Test percentage-based rollout"""
        flag_config = {
            "key": "test_flag",
            "enabled": True,
            "strategy": FeatureFlagStrategy.PERCENTAGE,
            "percentage": 50.0,
            "rules": [],
            "environments": {}
        }
        service._get_flag_config = AsyncMock(return_value=flag_config)
        service._cache_evaluation = AsyncMock()
        service._log_evaluation = AsyncMock()

        # Mock consistent hash result
        service._evaluate_percentage = MagicMock(return_value=True)

        result = await service.get_flag("test_flag", context)

        assert result is True
        service._evaluate_percentage.assert_called_once_with(flag_config, context)

    @pytest.mark.asyncio
    async def test_user_list_strategy(self, service, context):
        """Test user list strategy"""
        flag_config = {
            "key": "test_flag",
            "enabled": True,
            "strategy": FeatureFlagStrategy.USER_LIST,
            "user_ids": ["user123", "user456"],
            "rules": [],
            "environments": {}
        }
        service._get_flag_config = AsyncMock(return_value=flag_config)
        service._cache_evaluation = AsyncMock()
        service._log_evaluation = AsyncMock()

        result = await service.get_flag("test_flag", context)

        assert result is True

        # Test with user not in list
        context.user_id = "user789"
        result = await service.get_flag("test_flag", context)
        assert result is False

    @pytest.mark.asyncio
    async def test_organization_strategy(self, service, context):
        """Test organization-based strategy"""
        flag_config = {
            "key": "test_flag",
            "enabled": True,
            "strategy": FeatureFlagStrategy.ORGANIZATION,
            "organization_ids": ["org456", "org789"],
            "rules": [],
            "environments": {}
        }
        service._get_flag_config = AsyncMock(return_value=flag_config)
        service._cache_evaluation = AsyncMock()
        service._log_evaluation = AsyncMock()

        result = await service.get_flag("test_flag", context)

        assert result is True

    @pytest.mark.asyncio
    async def test_role_based_strategy(self, service, context):
        """Test role-based strategy"""
        flag_config = {
            "key": "test_flag",
            "enabled": True,
            "strategy": FeatureFlagStrategy.ROLE_BASED,
            "roles": ["premium_user", "admin"],
            "rules": [],
            "environments": {}
        }
        service._get_flag_config = AsyncMock(return_value=flag_config)
        service._cache_evaluation = AsyncMock()
        service._log_evaluation = AsyncMock()

        result = await service.get_flag("test_flag", context)

        assert result is True

        # Test without required role
        context.user_roles = ["basic_user"]
        result = await service.get_flag("test_flag", context)
        assert result is False

    @pytest.mark.asyncio
    async def test_environment_filtering(self, service, context):
        """Test environment-specific configuration"""
        flag_config = {
            "key": "test_flag",
            "enabled": True,
            "strategy": FeatureFlagStrategy.ALL_ON,
            "rules": [],
            "environments": {
                "development": {"enabled": False},
                "production": {"enabled": True}
            }
        }
        service._get_flag_config = AsyncMock(return_value=flag_config)
        service._cache_evaluation = AsyncMock()
        service._log_evaluation = AsyncMock()

        # Should be disabled in development
        result = await service.get_flag("test_flag", context)
        assert result is False

        # Should be enabled in production
        context.environment = "production"
        result = await service.get_flag("test_flag", context)
        assert result is True

    @pytest.mark.asyncio
    async def test_a_b_testing_variant(self, service, context):
        """Test A/B testing variant assignment"""
        service._log_variant_assignment = AsyncMock()

        variant = await service.get_variant("test_flag", context, ["A", "B"])

        assert variant in ["A", "B"]
        service._log_variant_assignment.assert_called_once_with(
            "test_flag", context, variant
        )

    @pytest.mark.asyncio
    async def test_variant_consistency(self, service, context):
        """Test that variant assignment is consistent for same user"""
        service._log_variant_assignment = AsyncMock()

        variant1 = await service.get_variant("test_flag", context, ["A", "B", "C"])
        variant2 = await service.get_variant("test_flag", context, ["A", "B", "C"])

        assert variant1 == variant2

    @pytest.mark.asyncio
    async def test_gradual_rollout_percentage(self, service, context):
        """Test gradual rollout percentage management"""
        flag_config = {
            "key": "test_flag",
            "enabled": True,
            "strategy": FeatureFlagStrategy.GRADUAL_ROLLOUT,
            "rules": [
                {
                    "strategy": FeatureFlagStrategy.GRADUAL_ROLLOUT,
                    "percentage": 25.0
                }
            ],
            "environments": {}
        }
        service._get_flag_config = AsyncMock(return_value=flag_config)
        mock_redis = service.redis
        mock_redis.setex = AsyncMock()
        service._invalidate_flag_cache = AsyncMock()

        # Test getting rollout percentage
        percentage = await service.get_rollout_percentage("test_flag")
        assert percentage == 25.0

        # Test updating rollout percentage
        await service.update_rollout_percentage("test_flag", 75.0)
        mock_redis.setex.assert_called()

    @pytest.mark.asyncio
    async def test_caching(self, service, context, mock_redis):
        """Test evaluation result caching"""
        # Setup cache hit
        mock_redis.get.return_value = b'true'
        service._get_cached_evaluation = AsyncMock(return_value=True)

        result = await service.get_flag("test_flag", context)

        assert result is True
        # Should not call flag config or evaluation since cached
        service._get_cached_evaluation.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, service, context):
        """Test error handling returns safe default"""
        service._get_flag_config = AsyncMock(side_effect=Exception("Redis error"))

        result = await service.get_flag("test_flag", context)

        # Should fail safe to False
        assert result is False

    @pytest.mark.asyncio
    async def test_flag_creation_and_deletion(self, service, mock_redis):
        """Test flag creation and deletion"""
        mock_redis.setex = AsyncMock()
        mock_redis.delete = AsyncMock()
        service._invalidate_flag_cache = AsyncMock()

        # Create flag
        rule = FeatureFlagRule(
            strategy=FeatureFlagStrategy.PERCENTAGE,
            percentage=50.0
        )
        await service.set_flag(
            key="new_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rules=[rule]
        )

        mock_redis.setex.assert_called()
        service._invalidate_flag_cache.assert_called_with("new_flag")

        # Delete flag
        await service.delete_flag("new_flag")
        mock_redis.delete.assert_called_with("feature_flag:new_flag")

    def test_rule_to_dict_conversion(self, service):
        """Test rule object to dictionary conversion"""
        rule = FeatureFlagRule(
            strategy=FeatureFlagStrategy.USER_LIST,
            enabled=True,
            user_ids=["user1", "user2"],
            start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
            metadata={"created_by": "admin"}
        )

        result = service._rule_to_dict(rule)

        assert result["strategy"] == FeatureFlagStrategy.USER_LIST
        assert result["enabled"] is True
        assert result["user_ids"] == ["user1", "user2"]
        assert result["start_time"] == "2024-01-01T00:00:00+00:00"
        assert result["metadata"] == {"created_by": "admin"}


class TestFeatureFlagEvaluation:
    """Test feature flag evaluation edge cases"""

    @pytest.mark.asyncio
    async def test_percentage_edge_cases(self):
        """Test percentage evaluation edge cases"""
        service = FeatureFlagService()
        context = FeatureFlagContext(user_id="test_user")

        # 0% should always be False
        flag_config = {"percentage": 0.0}
        result = service._evaluate_percentage(flag_config, context)
        assert result is False

        # 100% should always be True
        flag_config = {"percentage": 100.0}
        result = service._evaluate_percentage(flag_config, context)
        assert result is True

    def test_hash_consistency(self):
        """Test that hash-based evaluation is consistent"""
        service = FeatureFlagService()
        context = FeatureFlagContext(user_id="consistent_user")

        flag_config = {"percentage": 50.0}

        # Should get same result multiple times
        result1 = service._evaluate_percentage(flag_config, context)
        result2 = service._evaluate_percentage(flag_config, context)

        assert result1 == result2


class TestConvenienceFunctions:
    """Test convenience functions"""

    @pytest.mark.asyncio
    async def test_is_feature_enabled(self):
        """Test is_feature_enabled convenience function"""
        context = FeatureFlagContext(user_id="test_user")

        with pytest.mock.patch('app.core.feature_flags.get_feature_flag_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_flag.return_value = True
            mock_get_service.return_value = mock_service

            result = await is_feature_enabled("test_flag", context)

            assert result is True
            mock_service.get_flag.assert_called_once_with("test_flag", context)

    @pytest.mark.asyncio
    async def test_get_feature_variant(self):
        """Test get_feature_variant convenience function"""
        context = FeatureFlagContext(user_id="test_user")

        with pytest.mock.patch('app.core.feature_flags.get_feature_flag_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_variant.return_value = "B"
            mock_get_service.return_value = mock_service

            result = await get_feature_variant("test_flag", context, ["A", "B"])

            assert result == "B"
            mock_service.get_variant.assert_called_once_with("test_flag", context, ["A", "B"])


class TestFeatureFlagIntegration:
    """Integration tests for feature flag system"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete feature flag workflow"""
        # This would typically use a real Redis instance or test container
        # For now, we'll mock the workflow

        service = FeatureFlagService()
        context = FeatureFlagContext(
            user_id="integration_test_user",
            organization_id="test_org",
            environment="testing"
        )

        with pytest.mock.patch.object(service, 'redis') as mock_redis:
            mock_redis.get.return_value = None
            mock_redis.setex = AsyncMock()
            mock_redis.delete = AsyncMock()
            mock_redis.keys.return_value = []
            mock_redis.lpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()

            # Create a feature flag
            rule = FeatureFlagRule(
                strategy=FeatureFlagStrategy.PERCENTAGE,
                percentage=100.0
            )
            await service.set_flag(
                key="integration_test_flag",
                enabled=True,
                strategy=FeatureFlagStrategy.PERCENTAGE,
                rules=[rule]
            )

            # Mock flag config for evaluation
            flag_config = {
                "key": "integration_test_flag",
                "enabled": True,
                "strategy": FeatureFlagStrategy.PERCENTAGE,
                "rules": [{
                    "strategy": FeatureFlagStrategy.PERCENTAGE,
                    "percentage": 100.0,
                    "enabled": True
                }],
                "environments": {}
            }
            service._get_flag_config = AsyncMock(return_value=flag_config)

            # Evaluate the flag
            result = await service.get_flag("integration_test_flag", context)
            assert result is True

            # Clean up
            await service.delete_flag("integration_test_flag")
            mock_redis.delete.assert_called_with("feature_flag:integration_test_flag")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
