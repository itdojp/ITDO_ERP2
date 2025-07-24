"""
Feature Flag Management System for ITDO ERP
Provides dynamic feature toggling, A/B testing, and progressive rollouts
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import redis
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import get_settings
from app.core.database import get_redis

Base = declarative_base()

class FeatureFlagStrategy(str, Enum):
    """Feature flag rollout strategies"""
    ALL_ON = "all_on"
    ALL_OFF = "all_off"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    USER_PERCENTAGE = "user_percentage"
    ORGANIZATION = "organization"
    ROLE_BASED = "role_based"
    GRADUAL_ROLLOUT = "gradual_rollout"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"

class EnvironmentType(str, Enum):
    """Environment types for feature flags"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class FeatureFlagRule:
    """Individual rule for feature flag evaluation"""
    strategy: FeatureFlagStrategy
    enabled: bool = True
    percentage: Optional[float] = None
    user_ids: Optional[List[str]] = None
    organization_ids: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureFlagContext:
    """Context information for feature flag evaluation"""
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    user_roles: Optional[List[str]] = None
    environment: Optional[str] = None
    request_ip: Optional[str] = None
    user_agent: Optional[str] = None
    custom_attributes: Dict[str, Any] = field(default_factory=dict)

class FeatureFlag(Base):
    """Database model for feature flags"""
    __tablename__ = "feature_flags"

    key = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=False)
    strategy = Column(String(50), default=FeatureFlagStrategy.ALL_OFF)
    rules = Column(Text)  # JSON encoded rules
    environments = Column(Text)  # JSON encoded environment config
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(String(255))
    updated_by = Column(String(255))

class FeatureFlagService:
    """Service for managing and evaluating feature flags"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or get_redis()
        self.settings = get_settings()
        self.cache_ttl = 300  # 5 minutes default cache
        self.flag_prefix = "feature_flag:"

    async def get_flag(self, key: str, context: FeatureFlagContext) -> bool:
        """
        Evaluate a feature flag for given context

        Args:
            key: Feature flag key
            context: Evaluation context

        Returns:
            bool: Whether the feature is enabled
        """
        try:
            # Try cache first
            cached_result = await self._get_cached_evaluation(key, context)
            if cached_result is not None:
                return cached_result

            # Get flag configuration
            flag_config = await self._get_flag_config(key)
            if not flag_config:
                # Flag doesn't exist, return default (False)
                return False

            # Evaluate flag
            result = await self._evaluate_flag(flag_config, context)

            # Cache result
            await self._cache_evaluation(key, context, result)

            # Log evaluation for analytics
            await self._log_evaluation(key, context, result)

            return result

        except Exception as e:
            # Fail safe: return False on any error
            print(f"Feature flag evaluation error for {key}: {str(e)}")
            return False

    async def set_flag(
        self,
        key: str,
        enabled: bool,
        strategy: FeatureFlagStrategy = FeatureFlagStrategy.ALL_ON,
        rules: Optional[List[FeatureFlagRule]] = None,
        environments: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create or update a feature flag

        Args:
            key: Feature flag key
            enabled: Global enable/disable
            strategy: Rollout strategy
            rules: List of evaluation rules
            environments: Environment-specific configuration
        """
        flag_config = {
            "key": key,
            "enabled": enabled,
            "strategy": strategy,
            "rules": [self._rule_to_dict(rule) for rule in (rules or [])],
            "environments": environments or {},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        # Store in Redis
        await self.redis.setex(
            f"{self.flag_prefix}{key}",
            self.cache_ttl,
            json.dumps(flag_config)
        )

        # Invalidate evaluation cache
        await self._invalidate_flag_cache(key)

    async def delete_flag(self, key: str) -> None:
        """Delete a feature flag"""
        await self.redis.delete(f"{self.flag_prefix}{key}")
        await self._invalidate_flag_cache(key)

    async def list_flags(self) -> List[Dict[str, Any]]:
        """List all feature flags"""
        keys = await self.redis.keys(f"{self.flag_prefix}*")
        flags = []

        for key in keys:
            flag_data = await self.redis.get(key)
            if flag_data:
                flags.append(json.loads(flag_data))

        return flags

    async def get_flag_status(self, key: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a feature flag"""
        flag_config = await self._get_flag_config(key)
        if not flag_config:
            return None

        # Get evaluation statistics
        stats = await self._get_flag_statistics(key)

        return {
            "config": flag_config,
            "statistics": stats,
            "last_evaluated": await self._get_last_evaluation_time(key)
        }

    # A/B Testing Support
    async def get_variant(
        self,
        key: str,
        context: FeatureFlagContext,
        variants: List[str] = ["A", "B"]
    ) -> str:
        """
        Get A/B test variant for user

        Args:
            key: Feature flag key
            context: Evaluation context
            variants: Available variants

        Returns:
            str: Selected variant
        """
        if not context.user_id:
            return variants[0]  # Default variant

        # Use consistent hashing for stable assignment
        hash_input = f"{key}:{context.user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        variant_index = hash_value % len(variants)

        selected_variant = variants[variant_index]

        # Log variant assignment
        await self._log_variant_assignment(key, context, selected_variant)

        return selected_variant

    # Progressive Rollout Support
    async def get_rollout_percentage(self, key: str) -> float:
        """Get current rollout percentage for gradual rollout"""
        flag_config = await self._get_flag_config(key)
        if not flag_config:
            return 0.0

        strategy = flag_config.get("strategy")
        if strategy == FeatureFlagStrategy.GRADUAL_ROLLOUT:
            rules = flag_config.get("rules", [])
            for rule in rules:
                if rule.get("strategy") == FeatureFlagStrategy.GRADUAL_ROLLOUT:
                    return rule.get("percentage", 0.0)

        return 0.0 if not flag_config.get("enabled") else 100.0

    async def update_rollout_percentage(self, key: str, percentage: float) -> None:
        """Update rollout percentage for gradual rollout"""
        flag_config = await self._get_flag_config(key)
        if not flag_config:
            return

        # Update the percentage in gradual rollout rules
        rules = flag_config.get("rules", [])
        updated = False

        for rule in rules:
            if rule.get("strategy") == FeatureFlagStrategy.GRADUAL_ROLLOUT:
                rule["percentage"] = percentage
                updated = True

        if not updated:
            # Add new gradual rollout rule
            rules.append({
                "strategy": FeatureFlagStrategy.GRADUAL_ROLLOUT,
                "enabled": True,
                "percentage": percentage
            })

        flag_config["rules"] = rules
        flag_config["updated_at"] = datetime.now(timezone.utc).isoformat()

        await self.redis.setex(
            f"{self.flag_prefix}{key}",
            self.cache_ttl,
            json.dumps(flag_config)
        )

        await self._invalidate_flag_cache(key)

    # Private helper methods
    async def _get_flag_config(self, key: str) -> Optional[Dict[str, Any]]:
        """Get flag configuration from cache/storage"""
        cached_config = await self.redis.get(f"{self.flag_prefix}{key}")
        if cached_config:
            return json.loads(cached_config)
        return None

    async def _evaluate_flag(
        self,
        flag_config: Dict[str, Any],
        context: FeatureFlagContext
    ) -> bool:
        """Evaluate flag based on configuration and context"""
        if not flag_config.get("enabled", False):
            return False

        strategy = flag_config.get("strategy", FeatureFlagStrategy.ALL_OFF)
        rules = flag_config.get("rules", [])

        # Environment check
        environments = flag_config.get("environments", {})
        if context.environment and environments:
            env_config = environments.get(context.environment)
            if env_config is not None and not env_config.get("enabled", True):
                return False

        # Strategy-based evaluation
        if strategy == FeatureFlagStrategy.ALL_ON:
            return True
        elif strategy == FeatureFlagStrategy.ALL_OFF:
            return False
        elif strategy == FeatureFlagStrategy.PERCENTAGE:
            return self._evaluate_percentage(flag_config, context)
        elif strategy == FeatureFlagStrategy.USER_LIST:
            return self._evaluate_user_list(flag_config, context)
        elif strategy == FeatureFlagStrategy.USER_PERCENTAGE:
            return self._evaluate_user_percentage(flag_config, context)
        elif strategy == FeatureFlagStrategy.ORGANIZATION:
            return self._evaluate_organization(flag_config, context)
        elif strategy == FeatureFlagStrategy.ROLE_BASED:
            return self._evaluate_role_based(flag_config, context)
        elif strategy == FeatureFlagStrategy.GRADUAL_ROLLOUT:
            return self._evaluate_gradual_rollout(flag_config, context)

        # Evaluate custom rules
        for rule in rules:
            if self._evaluate_rule(rule, context):
                return True

        return False

    def _evaluate_percentage(
        self,
        flag_config: Dict[str, Any],
        context: FeatureFlagContext
    ) -> bool:
        """Evaluate percentage-based flag"""
        percentage = flag_config.get("percentage", 0.0)
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True

        # Use request IP or user ID for consistent hashing
        hash_input = context.request_ip or context.user_id or "anonymous"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        return (hash_value % 100) < percentage

    def _evaluate_user_percentage(
        self,
        flag_config: Dict[str, Any],
        context: FeatureFlagContext
    ) -> bool:
        """Evaluate user percentage-based flag"""
        if not context.user_id:
            return False

        percentage = flag_config.get("percentage", 0.0)
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True

        hash_value = int(hashlib.md5(context.user_id.encode()).hexdigest(), 16)
        return (hash_value % 100) < percentage

    def _evaluate_user_list(
        self,
        flag_config: Dict[str, Any],
        context: FeatureFlagContext
    ) -> bool:
        """Evaluate user list-based flag"""
        user_ids = flag_config.get("user_ids", [])
        return context.user_id in user_ids if context.user_id else False

    def _evaluate_organization(
        self,
        flag_config: Dict[str, Any],
        context: FeatureFlagContext
    ) -> bool:
        """Evaluate organization-based flag"""
        organization_ids = flag_config.get("organization_ids", [])
        return (context.organization_id in organization_ids
                if context.organization_id else False)

    def _evaluate_role_based(
        self,
        flag_config: Dict[str, Any],
        context: FeatureFlagContext
    ) -> bool:
        """Evaluate role-based flag"""
        required_roles = flag_config.get("roles", [])
        user_roles = context.user_roles or []
        return bool(set(required_roles) & set(user_roles))

    def _evaluate_gradual_rollout(
        self,
        flag_config: Dict[str, Any],
        context: FeatureFlagContext
    ) -> bool:
        """Evaluate gradual rollout flag"""
        return self._evaluate_user_percentage(flag_config, context)

    def _evaluate_rule(self, rule: Dict[str, Any], context: FeatureFlagContext) -> bool:
        """Evaluate individual rule"""
        if not rule.get("enabled", True):
            return False

        # Time-based evaluation
        now = datetime.now(timezone.utc)
        start_time = rule.get("start_time")
        end_time = rule.get("end_time")

        if start_time and now < datetime.fromisoformat(start_time):
            return False
        if end_time and now > datetime.fromisoformat(end_time):
            return False

        strategy = rule.get("strategy")
        if strategy == FeatureFlagStrategy.USER_LIST:
            return self._evaluate_user_list(rule, context)
        elif strategy == FeatureFlagStrategy.PERCENTAGE:
            return self._evaluate_percentage(rule, context)
        # Add more rule strategies as needed

        return False

    def _rule_to_dict(self, rule: FeatureFlagRule) -> Dict[str, Any]:
        """Convert rule object to dictionary"""
        return {
            "strategy": rule.strategy,
            "enabled": rule.enabled,
            "percentage": rule.percentage,
            "user_ids": rule.user_ids,
            "organization_ids": rule.organization_ids,
            "roles": rule.roles,
            "start_time": rule.start_time.isoformat() if rule.start_time else None,
            "end_time": rule.end_time.isoformat() if rule.end_time else None,
            "metadata": rule.metadata
        }

    # Caching methods
    async def _get_cached_evaluation(
        self,
        key: str,
        context: FeatureFlagContext
    ) -> Optional[bool]:
        """Get cached evaluation result"""
        cache_key = self._get_evaluation_cache_key(key, context)
        cached_result = await self.redis.get(cache_key)
        return json.loads(cached_result) if cached_result else None

    async def _cache_evaluation(
        self,
        key: str,
        context: FeatureFlagContext,
        result: bool
    ) -> None:
        """Cache evaluation result"""
        cache_key = self._get_evaluation_cache_key(key, context)
        await self.redis.setex(cache_key, 60, json.dumps(result))  # 1 minute cache

    def _get_evaluation_cache_key(
        self,
        key: str,
        context: FeatureFlagContext
    ) -> str:
        """Generate cache key for evaluation"""
        context_hash = hashlib.md5(
            f"{context.user_id}:{context.organization_id}:{context.environment}".encode()
        ).hexdigest()[:8]
        return f"ff_eval:{key}:{context_hash}"

    async def _invalidate_flag_cache(self, key: str) -> None:
        """Invalidate all cached evaluations for a flag"""
        pattern = f"ff_eval:{key}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    # Analytics methods
    async def _log_evaluation(
        self,
        key: str,
        context: FeatureFlagContext,
        result: bool
    ) -> None:
        """Log feature flag evaluation for analytics"""
        log_entry = {
            "flag_key": key,
            "result": result,
            "user_id": context.user_id,
            "organization_id": context.organization_id,
            "environment": context.environment,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Store in analytics queue
        await self.redis.lpush("ff_analytics", json.dumps(log_entry))
        await self.redis.ltrim("ff_analytics", 0, 10000)  # Keep last 10k events

    async def _log_variant_assignment(
        self,
        key: str,
        context: FeatureFlagContext,
        variant: str
    ) -> None:
        """Log A/B test variant assignment"""
        log_entry = {
            "flag_key": key,
            "variant": variant,
            "user_id": context.user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self.redis.lpush("ff_variants", json.dumps(log_entry))
        await self.redis.ltrim("ff_variants", 0, 10000)

    async def _get_flag_statistics(self, key: str) -> Dict[str, Any]:
        """Get evaluation statistics for a flag"""
        # This would typically query a more robust analytics store
        analytics_data = await self.redis.lrange("ff_analytics", 0, -1)

        total_evaluations = 0
        enabled_count = 0

        for entry_json in analytics_data:
            entry = json.loads(entry_json)
            if entry["flag_key"] == key:
                total_evaluations += 1
                if entry["result"]:
                    enabled_count += 1

        return {
            "total_evaluations": total_evaluations,
            "enabled_count": enabled_count,
            "enabled_percentage": (enabled_count / total_evaluations * 100)
                                if total_evaluations > 0 else 0
        }

    async def _get_last_evaluation_time(self, key: str) -> Optional[str]:
        """Get timestamp of last evaluation"""
        analytics_data = await self.redis.lrange("ff_analytics", 0, 100)

        for entry_json in analytics_data:
            entry = json.loads(entry_json)
            if entry["flag_key"] == key:
                return entry["timestamp"]

        return None

# Singleton service instance
_feature_flag_service: Optional[FeatureFlagService] = None

def get_feature_flag_service() -> FeatureFlagService:
    """Get or create feature flag service instance"""
    global _feature_flag_service
    if _feature_flag_service is None:
        _feature_flag_service = FeatureFlagService()
    return _feature_flag_service

# Convenience functions
async def is_feature_enabled(
    flag_key: str,
    context: FeatureFlagContext
) -> bool:
    """Check if a feature flag is enabled"""
    service = get_feature_flag_service()
    return await service.get_flag(flag_key, context)

async def get_feature_variant(
    flag_key: str,
    context: FeatureFlagContext,
    variants: List[str] = ["A", "B"]
) -> str:
    """Get feature variant for A/B testing"""
    service = get_feature_flag_service()
    return await service.get_variant(flag_key, context, variants)
