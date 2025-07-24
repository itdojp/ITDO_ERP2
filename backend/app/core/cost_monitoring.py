"""
Cost Monitoring Framework for ITDO ERP
Provides comprehensive cost tracking, optimization, and FinOps capabilities
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import redis
from sqlalchemy import Boolean, Column, DateTime, Index, Numeric, String, Text
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import get_settings
from app.core.database import get_redis

Base = declarative_base()


class CostCategory(str, Enum):
    """Cost categorization for better tracking"""

    INFRASTRUCTURE = "infrastructure"
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    MONITORING = "monitoring"
    SECURITY = "security"
    DEVELOPMENT = "development"
    OPERATIONS = "operations"
    THIRD_PARTY = "third_party"
    LICENSING = "licensing"
    PERSONNEL = "personnel"
    OVERHEAD = "overhead"


class CostMetricType(str, Enum):
    """Types of cost metrics"""

    ABSOLUTE = "absolute"  # Fixed cost in currency
    RATE = "rate"  # Cost per unit (CPU hour, GB, etc.)
    PERCENTAGE = "percentage"  # Percentage of total
    BUDGET_UTILIZATION = "budget_utilization"  # % of budget used
    EFFICIENCY = "efficiency"  # Cost per unit of value


class TimeGranularity(str, Enum):
    """Time granularity for cost aggregation"""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class AlertSeverity(str, Enum):
    """Cost alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class CostMetric:
    """Individual cost metric"""

    name: str
    value: Decimal
    category: CostCategory
    metric_type: CostMetricType
    currency: str = "USD"
    unit: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostBudget:
    """Cost budget definition"""

    id: str
    name: str
    category: CostCategory
    amount: Decimal
    currency: str
    period: TimeGranularity
    start_date: datetime
    end_date: datetime
    alert_thresholds: List[Tuple[float, AlertSeverity]]  # [(percentage, severity)]
    owner: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostAlert:
    """Cost monitoring alert"""

    id: str
    budget_id: str
    severity: AlertSeverity
    title: str
    description: str
    current_spend: Decimal
    budget_amount: Decimal
    utilization_percentage: float
    threshold_percentage: float
    timestamp: datetime
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation"""

    id: str
    title: str
    description: str
    category: CostCategory
    potential_savings: Decimal
    confidence_score: float  # 0.0 to 1.0
    effort_level: str  # "low", "medium", "high"
    impact_level: str  # "low", "medium", "high"
    implementation_steps: List[str]
    timestamp: datetime
    status: str = "pending"  # pending, in_progress, completed, dismissed
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostRecord(Base):
    """Database model for cost records"""

    __tablename__ = "cost_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String(255), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)
    value = Column(Numeric(15, 4), nullable=False)
    currency = Column(String(10), default="USD")
    unit = Column(String(50))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    tags = Column(Text)  # JSON encoded
    metadata = Column(Text)  # JSON encoded
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_cost_records_category_timestamp", "category", "timestamp"),
        Index("idx_cost_records_metric_timestamp", "metric_name", "timestamp"),
    )


class CostBudgetRecord(Base):
    """Database model for cost budgets"""

    __tablename__ = "cost_budgets"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    amount = Column(Numeric(15, 4), nullable=False)
    currency = Column(String(10), default="USD")
    period = Column(String(50), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    alert_thresholds = Column(Text)  # JSON encoded
    owner = Column(String(255))
    description = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    metadata = Column(Text)  # JSON encoded


class CostAlertRecord(Base):
    """Database model for cost alerts"""

    __tablename__ = "cost_alerts"

    id = Column(String(36), primary_key=True)
    budget_id = Column(String(36), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    current_spend = Column(Numeric(15, 4), nullable=False)
    budget_amount = Column(Numeric(15, 4), nullable=False)
    utilization_percentage = Column(Numeric(5, 2), nullable=False)
    threshold_percentage = Column(Numeric(5, 2), nullable=False)
    resolved = Column(Boolean, default=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    resolution_timestamp = Column(DateTime(timezone=True))
    tags = Column(Text)  # JSON encoded
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class CostMonitoringService:
    """Comprehensive cost monitoring and optimization service"""

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> dict:
        self.redis = redis_client or get_redis()
        self.settings = get_settings()
        self.cache_ttl = 300  # 5 minutes
        self.cost_prefix = "cost_monitor:"

        # Default currency and precision
        self.default_currency = getattr(self.settings, "DEFAULT_CURRENCY", "USD")
        self.decimal_places = 4

        # Cost thresholds for automatic recommendations
        self.optimization_thresholds = {
            CostCategory.COMPUTE: Decimal("100.00"),  # $100/month
            CostCategory.STORAGE: Decimal("50.00"),  # $50/month
            CostCategory.DATABASE: Decimal("200.00"),  # $200/month
        }

    async def record_cost(self, metric: CostMetric) -> str:
        """
        Record a cost metric

        Args:
            metric: Cost metric to record

        Returns:
            str: Record ID
        """
        try:
            # Generate unique ID
            record_id = str(uuid.uuid4())

            # Prepare record data
            record_data = {
                "id": record_id,
                "metric_name": metric.name,
                "category": metric.category.value,
                "metric_type": metric.metric_type.value,
                "value": float(metric.value),
                "currency": metric.currency,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "tags": json.dumps(metric.tags),
                "metadata": json.dumps(metric.metadata),
            }

            # Store in Redis for real-time access
            await self.redis.setex(
                f"{self.cost_prefix}record:{record_id}",
                self.cache_ttl,
                json.dumps(record_data),
            )

            # Store in time-series format for aggregation
            timestamp_key = metric.timestamp.strftime("%Y-%m-%d-%H")
            await self.redis.zadd(
                f"{self.cost_prefix}timeseries:{metric.category.value}:{timestamp_key}",
                {record_id: float(metric.value)},
            )

            # Update category totals
            await self._update_category_totals(metric)

            # Check budget alerts
            await self._check_budget_alerts(metric)

            # Generate optimization recommendations if needed
            await self._check_optimization_opportunities(metric)

            return record_id

        except Exception as e:
            print(f"Error recording cost metric: {str(e)}")
            raise

    async def get_cost_summary(
        self,
        category: Optional[CostCategory] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        granularity: TimeGranularity = TimeGranularity.DAILY,
    ) -> Dict[str, Any]:
        """
        Get comprehensive cost summary

        Args:
            category: Filter by cost category
            time_range: Start and end dates for filtering
            granularity: Time granularity for aggregation

        Returns:
            Dict containing cost summary data
        """
        try:
            if time_range is None:
                # Default to last 30 days
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)

            # Get cached summary if available
            cache_key = self._get_summary_cache_key(category, time_range, granularity)
            cached_summary = await self.redis.get(cache_key)
            if cached_summary:
                return json.loads(cached_summary)

            # Build summary from stored data
            summary = await self._build_cost_summary(category, time_range, granularity)

            # Cache the summary
            await self.redis.setex(
                cache_key, self.cache_ttl, json.dumps(summary, default=str)
            )

            return summary

        except Exception as e:
            print(f"Error getting cost summary: {str(e)}")
            raise

    async def create_budget(
        self,
        name: str,
        category: CostCategory,
        amount: Decimal,
        period: TimeGranularity,
        start_date: datetime,
        end_date: datetime,
        alert_thresholds: List[Tuple[float, AlertSeverity]],
        owner: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Create a cost budget

        Args:
            name: Budget name
            category: Cost category
            amount: Budget amount
            period: Time period
            start_date: Budget start date
            end_date: Budget end date
            alert_thresholds: Alert thresholds [(percentage, severity)]
            owner: Budget owner
            description: Budget description

        Returns:
            str: Budget ID
        """
        budget_id = str(uuid.uuid4())

        budget = CostBudget(
            id=budget_id,
            name=name,
            category=category,
            amount=amount,
            currency=self.default_currency,
            period=period,
            start_date=start_date,
            end_date=end_date,
            alert_thresholds=alert_thresholds,
            owner=owner,
            description=description,
        )

        # Store budget
        budget_data = {
            "id": budget.id,
            "name": budget.name,
            "category": budget.category.value,
            "amount": float(budget.amount),
            "currency": budget.currency,
            "period": budget.period.value,
            "start_date": budget.start_date.isoformat(),
            "end_date": budget.end_date.isoformat(),
            "alert_thresholds": budget.alert_thresholds,
            "owner": budget.owner,
            "description": budget.description,
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        await self.redis.setex(
            f"{self.cost_prefix}budget:{budget_id}",
            86400,  # 24 hours
            json.dumps(budget_data),
        )

        return budget_id

    async def get_budget_utilization(self, budget_id: str) -> Dict[str, Any]:
        """
        Get budget utilization information

        Args:
            budget_id: Budget ID

        Returns:
            Dict containing budget utilization data
        """
        budget_data = await self.redis.get(f"{self.cost_prefix}budget:{budget_id}")
        if not budget_data:
            raise ValueError(f"Budget {budget_id} not found")

        budget = json.loads(budget_data)

        # Calculate current spend for the budget period
        start_date = datetime.fromisoformat(budget["start_date"])
        end_date = datetime.fromisoformat(budget["end_date"])
        category = CostCategory(budget["category"])

        current_spend = await self._calculate_category_spend(
            category, start_date, end_date
        )
        budget_amount = Decimal(str(budget["amount"]))

        utilization_percentage = (
            float((current_spend / budget_amount) * 100) if budget_amount > 0 else 0
        )

        return {
            "budget_id": budget_id,
            "budget_name": budget["name"],
            "category": budget["category"],
            "budget_amount": float(budget_amount),
            "current_spend": float(current_spend),
            "remaining_budget": float(budget_amount - current_spend),
            "utilization_percentage": utilization_percentage,
            "period": budget["period"],
            "start_date": budget["start_date"],
            "end_date": budget["end_date"],
            "days_remaining": (end_date - datetime.now(timezone.utc)).days,
            "projected_spend": float(
                await self._project_spend(category, start_date, end_date)
            ),
            "on_track": utilization_percentage <= 100.0,
        }

    async def get_optimization_recommendations(
        self,
        category: Optional[CostCategory] = None,
        min_savings: Optional[Decimal] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations

        Args:
            category: Filter by cost category
            min_savings: Minimum potential savings threshold

        Returns:
            List of optimization recommendations
        """
        try:
            recommendations = []

            # Get all stored recommendations
            pattern = f"{self.cost_prefix}recommendation:*"
            keys = await self.redis.keys(pattern)

            for key in keys:
                rec_data = await self.redis.get(key)
                if rec_data:
                    recommendation = json.loads(rec_data)

                    # Apply filters
                    if category and recommendation["category"] != category.value:
                        continue

                    if (
                        min_savings
                        and Decimal(str(recommendation["potential_savings"]))
                        < min_savings
                    ):
                        continue

                    recommendations.append(recommendation)

            # Sort by potential savings (descending)
            recommendations.sort(
                key=lambda x: float(x["potential_savings"]), reverse=True
            )

            return recommendations

        except Exception as e:
            print(f"Error getting optimization recommendations: {str(e)}")
            return []

    async def get_cost_alerts(
        self, severity: Optional[AlertSeverity] = None, resolved: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cost monitoring alerts

        Args:
            severity: Filter by alert severity
            resolved: Filter by resolution status

        Returns:
            List of cost alerts
        """
        try:
            alerts = []

            # Get all alerts
            pattern = f"{self.cost_prefix}alert:*"
            keys = await self.redis.keys(pattern)

            for key in keys:
                alert_data = await self.redis.get(key)
                if alert_data:
                    alert = json.loads(alert_data)

                    # Apply filters
                    if severity and alert["severity"] != severity.value:
                        continue

                    if resolved is not None and alert["resolved"] != resolved:
                        continue

                    alerts.append(alert)

            # Sort by timestamp (most recent first)
            alerts.sort(key=lambda x: x["timestamp"], reverse=True)

            return alerts

        except Exception as e:
            print(f"Error getting cost alerts: {str(e)}")
            return []

    # Private helper methods

    async def _update_category_totals(self, metric: CostMetric) -> None:
        """Update category total counters"""
        try:
            today = metric.timestamp.strftime("%Y-%m-%d")
            month = metric.timestamp.strftime("%Y-%m")

            # Daily total
            await self.redis.incrbyfloat(
                f"{self.cost_prefix}total:daily:{metric.category.value}:{today}",
                float(metric.value),
            )

            # Monthly total
            await self.redis.incrbyfloat(
                f"{self.cost_prefix}total:monthly:{metric.category.value}:{month}",
                float(metric.value),
            )

            # Set expiration for cleanup
            await self.redis.expire(
                f"{self.cost_prefix}total:daily:{metric.category.value}:{today}",
                86400 * 32,  # 32 days
            )
            await self.redis.expire(
                f"{self.cost_prefix}total:monthly:{metric.category.value}:{month}",
                86400 * 365,  # 1 year
            )

        except Exception as e:
            print(f"Error updating category totals: {str(e)}")

    async def _check_budget_alerts(self, metric: CostMetric) -> None:
        """Check if any budgets are exceeded and trigger alerts"""
        try:
            # Get all active budgets for this category
            pattern = f"{self.cost_prefix}budget:*"
            keys = await self.redis.keys(pattern)

            for key in keys:
                budget_data = await self.redis.get(key)
                if not budget_data:
                    continue

                budget = json.loads(budget_data)
                if budget["category"] != metric.category.value or not budget.get(
                    "active", True
                ):
                    continue

                # Check if we're within the budget period
                start_date = datetime.fromisoformat(budget["start_date"])
                end_date = datetime.fromisoformat(budget["end_date"])

                if not (start_date <= metric.timestamp <= end_date):
                    continue

                # Calculate current utilization
                utilization = await self.get_budget_utilization(budget["id"])
                utilization_pct = utilization["utilization_percentage"]

                # Check alert thresholds
                for threshold_pct, severity in budget["alert_thresholds"]:
                    if utilization_pct >= threshold_pct:
                        await self._create_budget_alert(
                            budget,
                            utilization_pct,
                            threshold_pct,
                            AlertSeverity(severity),
                        )
                        break

        except Exception as e:
            print(f"Error checking budget alerts: {str(e)}")

    async def _create_budget_alert(
        self,
        budget: Dict[str, Any],
        utilization_pct: float,
        threshold_pct: float,
        severity: AlertSeverity,
    ) -> None:
        """Create a budget alert"""
        alert_id = str(uuid.uuid4())

        alert_data = {
            "id": alert_id,
            "budget_id": budget["id"],
            "severity": severity.value,
            "title": f"Budget Alert: {budget['name']}",
            "description": f"Budget utilization is {utilization_pct:.1f}% (threshold: {threshold_pct}%)",
            "current_spend": budget["amount"] * (utilization_pct / 100),
            "budget_amount": budget["amount"],
            "utilization_percentage": utilization_pct,
            "threshold_percentage": threshold_pct,
            "resolved": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tags": {"category": budget["category"]},
        }

        await self.redis.setex(
            f"{self.cost_prefix}alert:{alert_id}",
            86400 * 7,  # 7 days
            json.dumps(alert_data),
        )

    async def _check_optimization_opportunities(self, metric: CostMetric) -> None:
        """Check for cost optimization opportunities"""
        try:
            # Get monthly spend for this category
            month = metric.timestamp.strftime("%Y-%m")
            monthly_key = (
                f"{self.cost_prefix}total:monthly:{metric.category.value}:{month}"
            )
            monthly_spend = await self.redis.get(monthly_key)

            if not monthly_spend:
                return

            monthly_amount = Decimal(str(monthly_spend))
            threshold = self.optimization_thresholds.get(
                metric.category, Decimal("50.00")
            )

            if monthly_amount > threshold:
                recommendations = await self._generate_optimization_recommendations(
                    metric.category, monthly_amount
                )

                for recommendation in recommendations:
                    rec_id = str(uuid.uuid4())
                    rec_data = {
                        "id": rec_id,
                        "title": recommendation["title"],
                        "description": recommendation["description"],
                        "category": metric.category.value,
                        "potential_savings": float(recommendation["potential_savings"]),
                        "confidence_score": recommendation["confidence_score"],
                        "effort_level": recommendation["effort_level"],
                        "impact_level": recommendation["impact_level"],
                        "implementation_steps": recommendation["implementation_steps"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "pending",
                    }

                    await self.redis.setex(
                        f"{self.cost_prefix}recommendation:{rec_id}",
                        86400 * 30,  # 30 days
                        json.dumps(rec_data),
                    )

        except Exception as e:
            print(f"Error checking optimization opportunities: {str(e)}")

    async def _generate_optimization_recommendations(
        self, category: CostCategory, current_spend: Decimal
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations for a category"""
        recommendations = []

        if category == CostCategory.COMPUTE:
            recommendations.extend(
                [
                    {
                        "title": "Right-size Compute Instances",
                        "description": "Review compute instance utilization and downsize underutilized resources",
                        "potential_savings": current_spend
                        * Decimal("0.20"),  # 20% savings
                        "confidence_score": 0.8,
                        "effort_level": "medium",
                        "impact_level": "high",
                        "implementation_steps": [
                            "Analyze CPU and memory utilization over the past 30 days",
                            "Identify instances with <20% average utilization",
                            "Create rightsizing recommendations",
                            "Schedule maintenance window for instance resizing",
                            "Monitor performance after changes",
                        ],
                    },
                    {
                        "title": "Implement Auto-Scaling",
                        "description": "Set up automatic scaling to optimize resource usage based on demand",
                        "potential_savings": current_spend
                        * Decimal("0.15"),  # 15% savings
                        "confidence_score": 0.7,
                        "effort_level": "high",
                        "impact_level": "high",
                        "implementation_steps": [
                            "Configure horizontal pod autoscaling (HPA)",
                            "Set up cluster autoscaling",
                            "Define scaling policies based on metrics",
                            "Test scaling behavior under load",
                            "Monitor scaling events and optimize thresholds",
                        ],
                    },
                ]
            )

        elif category == CostCategory.STORAGE:
            recommendations.extend(
                [
                    {
                        "title": "Implement Storage Tiering",
                        "description": "Move infrequently accessed data to lower-cost storage tiers",
                        "potential_savings": current_spend
                        * Decimal("0.30"),  # 30% savings
                        "confidence_score": 0.9,
                        "effort_level": "low",
                        "impact_level": "medium",
                        "implementation_steps": [
                            "Analyze storage access patterns",
                            "Identify data older than 90 days",
                            "Configure lifecycle policies",
                            "Migrate cold data to archive storage",
                            "Monitor access patterns and adjust policies",
                        ],
                    }
                ]
            )

        elif category == CostCategory.DATABASE:
            recommendations.extend(
                [
                    {
                        "title": "Optimize Database Configuration",
                        "description": "Review database sizing and configuration for cost optimization",
                        "potential_savings": current_spend
                        * Decimal("0.25"),  # 25% savings
                        "confidence_score": 0.6,
                        "effort_level": "medium",
                        "impact_level": "medium",
                        "implementation_steps": [
                            "Analyze database performance metrics",
                            "Review connection pooling settings",
                            "Optimize query performance",
                            "Consider read replicas for read-heavy workloads",
                            "Implement database connection scaling",
                        ],
                    }
                ]
            )

        return recommendations

    def _get_summary_cache_key(
        self,
        category: Optional[CostCategory],
        time_range: Tuple[datetime, datetime],
        granularity: TimeGranularity,
    ) -> str:
        """Generate cache key for cost summary"""
        cat_str = category.value if category else "all"
        start_str = time_range[0].strftime("%Y%m%d")
        end_str = time_range[1].strftime("%Y%m%d")
        return f"{self.cost_prefix}summary:{cat_str}:{start_str}:{end_str}:{granularity.value}"

    async def _build_cost_summary(
        self,
        category: Optional[CostCategory],
        time_range: Tuple[datetime, datetime],
        granularity: TimeGranularity,
    ) -> Dict[str, Any]:
        """Build cost summary from stored data"""
        # This would typically query the database
        # For now, we'll build from Redis data

        start_date, end_date = time_range
        summary = {
            "total_cost": 0.0,
            "currency": self.default_currency,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "granularity": granularity.value,
            },
            "categories": {},
            "trends": {},
            "top_cost_drivers": [],
        }

        # Calculate totals by category
        categories_to_check = [category] if category else list(CostCategory)

        for cat in categories_to_check:
            cat_total = await self._calculate_category_spend(cat, start_date, end_date)
            summary["categories"][cat.value] = float(cat_total)
            summary["total_cost"] += float(cat_total)

        return summary

    async def _calculate_category_spend(
        self, category: CostCategory, start_date: datetime, end_date: datetime
    ) -> Decimal:
        """Calculate total spend for a category in date range"""
        total = Decimal("0.00")

        # Iterate through each day in the range
        current_date = start_date.date()
        end_date_only = end_date.date()

        while current_date <= end_date_only:
            daily_key = f"{self.cost_prefix}total:daily:{category.value}:{current_date.strftime('%Y-%m-%d')}"
            daily_spend = await self.redis.get(daily_key)

            if daily_spend:
                total += Decimal(str(daily_spend))

            current_date += timedelta(days=1)

        return total

    async def _project_spend(
        self, category: CostCategory, start_date: datetime, end_date: datetime
    ) -> Decimal:
        """Project future spend based on current trends"""
        current_spend = await self._calculate_category_spend(
            category, start_date, datetime.now(timezone.utc)
        )

        if current_spend <= 0:
            return Decimal("0.00")

        # Simple linear projection
        days_elapsed = (datetime.now(timezone.utc) - start_date).days
        total_days = (end_date - start_date).days

        if days_elapsed <= 0:
            return current_spend

        daily_average = current_spend / days_elapsed
        projected_total = daily_average * total_days

        return projected_total


# Singleton service instance
_cost_monitoring_service: Optional[CostMonitoringService] = None


def get_cost_monitoring_service() -> CostMonitoringService:
    """Get or create cost monitoring service instance"""
    global _cost_monitoring_service
    if _cost_monitoring_service is None:
        _cost_monitoring_service = CostMonitoringService()
    return _cost_monitoring_service
