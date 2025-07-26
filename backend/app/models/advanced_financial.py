"""
ITDO ERP Backend - Advanced Financial Models
Day 25: Advanced financial analytics with AI prediction and risk analysis

This module provides:
- AI-powered financial forecasting models
- Risk analysis and scoring
- Advanced financial metrics calculation
- Predictive analytics for cash flow
- Market volatility analysis
- Financial optimization algorithms
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.types import BaseId

# Type aliases for better readability
FinancialForecastId = BaseId
RiskAssessmentId = BaseId
MarketDataId = BaseId
FinancialOptimizationId = BaseId
CashFlowPredictionId = BaseId
OrganizationId = BaseId
AccountId = BaseId
UserId = BaseId


class FinancialForecast(Base):
    """AI-powered financial forecast model"""

    __tablename__ = "financial_forecasts"

    id: Mapped[FinancialForecastId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    forecast_name: Mapped[str] = mapped_column(String(255), nullable=False)
    forecast_type: Mapped[str] = mapped_column(
        SQLEnum(
            "revenue",
            "expense",
            "cash_flow",
            "profit",
            "budget",
            name="forecast_type_enum",
        ),
        nullable=False,
    )
    forecast_horizon: Mapped[str] = mapped_column(
        SQLEnum(
            "monthly", "quarterly", "annual", "multi_year", name="forecast_horizon_enum"
        ),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # AI Model Configuration
    ai_model_type: Mapped[str] = mapped_column(
        SQLEnum(
            "linear_regression",
            "arima",
            "lstm",
            "prophet",
            "ensemble",
            name="ai_model_enum",
        ),
        nullable=False,
        default="ensemble",
    )
    training_data_period: Mapped[int] = mapped_column(
        Integer, nullable=False, default=24
    )  # months
    confidence_interval: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("95.00")
    )

    # Forecast Results
    forecast_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    accuracy_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    mean_absolute_error: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4), nullable=True
    )

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UserId] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Model configuration parameters
    model_parameters: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    def __repr__(self) -> str:
        return f"<FinancialForecast(id={self.id}, name={self.forecast_name}, type={self.forecast_type})>"


class RiskAssessment(Base):
    """Financial risk assessment and scoring model"""

    __tablename__ = "risk_assessments"

    id: Mapped[RiskAssessmentId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_type: Mapped[str] = mapped_column(
        SQLEnum(
            "credit",
            "market",
            "liquidity",
            "operational",
            "comprehensive",
            name="risk_type_enum",
        ),
        nullable=False,
    )
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Risk Scores (0-100 scale)
    overall_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    credit_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    market_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    liquidity_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    operational_risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )

    # Risk Categories
    risk_level: Mapped[str] = mapped_column(
        SQLEnum(
            "very_low", "low", "medium", "high", "very_high", name="risk_level_enum"
        ),
        nullable=False,
    )

    # Detailed Analysis
    risk_factors: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    mitigation_strategies: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    recommendations: Mapped[List[str]] = mapped_column(JSONB, nullable=False)

    # Confidence and Reliability
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    data_quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UserId] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<RiskAssessment(id={self.id}, name={self.assessment_name}, level={self.risk_level})>"


class MarketData(Base):
    """Market data for financial analysis and risk assessment"""

    __tablename__ = "market_data"

    id: Mapped[MarketDataId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    data_type: Mapped[str] = mapped_column(
        SQLEnum(
            "interest_rate",
            "exchange_rate",
            "stock_price",
            "commodity",
            "index",
            name="market_data_type_enum",
        ),
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(100), nullable=False)
    data_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Market Values
    open_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    close_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 6), nullable=True
    )
    high_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    low_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Volatility Metrics
    volatility: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    beta: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)

    # Additional Market Indicators
    market_indicators: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Data Quality
    data_source: Mapped[str] = mapped_column(String(100), nullable=False)
    quality_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("95.00")
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<MarketData(id={self.id}, symbol={self.symbol}, date={self.data_date})>"
        )


class CashFlowPrediction(Base):
    """Advanced cash flow prediction with AI models"""

    __tablename__ = "cash_flow_predictions"

    id: Mapped[CashFlowPredictionId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    prediction_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prediction_type: Mapped[str] = mapped_column(
        SQLEnum(
            "operating", "investing", "financing", "total", name="cashflow_type_enum"
        ),
        nullable=False,
    )
    prediction_period: Mapped[str] = mapped_column(
        SQLEnum(
            "daily", "weekly", "monthly", "quarterly", name="prediction_period_enum"
        ),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Prediction Results
    predicted_cashflow: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    confidence_intervals: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    scenario_analysis: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Model Performance
    model_accuracy: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    prediction_variance: Mapped[Decimal] = mapped_column(Numeric(15, 6), nullable=False)

    # Risk Factors
    risk_factors: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    sensitivity_analysis: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Optimization Suggestions
    optimization_recommendations: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False
    )

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UserId] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<CashFlowPrediction(id={self.id}, name={self.prediction_name}, type={self.prediction_type})>"


class FinancialOptimization(Base):
    """Financial optimization recommendations and strategies"""

    __tablename__ = "financial_optimizations"

    id: Mapped[FinancialOptimizationId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    optimization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    optimization_type: Mapped[str] = mapped_column(
        SQLEnum(
            "cost_reduction",
            "revenue_enhancement",
            "risk_mitigation",
            "efficiency",
            "comprehensive",
            name="optimization_type_enum",
        ),
        nullable=False,
    )
    priority_level: Mapped[str] = mapped_column(
        SQLEnum("low", "medium", "high", "critical", name="priority_level_enum"),
        nullable=False,
    )

    # Current State Analysis
    current_metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    baseline_performance: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Optimization Strategy
    recommended_actions: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    implementation_steps: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    required_resources: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Expected Outcomes
    projected_savings: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    projected_revenue_increase: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    roi_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    payback_period_months: Mapped[int] = mapped_column(Integer, nullable=False)

    # Risk Assessment
    implementation_risk: Mapped[str] = mapped_column(
        SQLEnum("low", "medium", "high", name="implementation_risk_enum"),
        nullable=False,
    )
    risk_mitigation_plan: Mapped[List[str]] = mapped_column(JSONB, nullable=False)

    # Implementation Timeline
    estimated_duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    target_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Status Tracking
    implementation_status: Mapped[str] = mapped_column(
        SQLEnum(
            "proposed",
            "approved",
            "in_progress",
            "completed",
            "cancelled",
            name="implementation_status_enum",
        ),
        nullable=False,
        default="proposed",
    )
    progress_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UserId] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    approved_by: Mapped[Optional[UserId]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<FinancialOptimization(id={self.id}, name={self.optimization_name}, type={self.optimization_type})>"


class FinancialMetrics(Base):
    """Advanced financial metrics and KPIs"""

    __tablename__ = "financial_metrics"

    id: Mapped[BaseId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_category: Mapped[str] = mapped_column(
        SQLEnum(
            "profitability",
            "liquidity",
            "efficiency",
            "leverage",
            "market",
            "growth",
            name="metric_category_enum",
        ),
        nullable=False,
    )
    calculation_period: Mapped[str] = mapped_column(
        SQLEnum(
            "daily",
            "weekly",
            "monthly",
            "quarterly",
            "annual",
            name="calculation_period_enum",
        ),
        nullable=False,
    )
    calculation_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Metric Values
    metric_value: Mapped[Decimal] = mapped_column(Numeric(15, 6), nullable=False)
    benchmark_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 6), nullable=True
    )
    industry_average: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 6), nullable=True
    )

    # Trend Analysis
    previous_period_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 6), nullable=True
    )
    year_over_year_change: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    trend_direction: Mapped[Optional[str]] = mapped_column(
        SQLEnum("improving", "stable", "declining", name="trend_direction_enum"),
        nullable=True,
    )

    # Performance Indicators
    performance_rating: Mapped[str] = mapped_column(
        SQLEnum(
            "excellent",
            "good",
            "average",
            "below_average",
            "poor",
            name="performance_rating_enum",
        ),
        nullable=False,
    )
    alert_threshold_breached: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Calculation Details
    calculation_method: Mapped[str] = mapped_column(Text, nullable=False)
    data_sources: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    calculation_parameters: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<FinancialMetrics(id={self.id}, name={self.metric_name}, value={self.metric_value})>"
