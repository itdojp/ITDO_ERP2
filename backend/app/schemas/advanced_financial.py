"""
ITDO ERP Backend - Advanced Financial Schemas
Day 25: Pydantic schemas for advanced financial analytics and AI predictions

This module provides:
- Request/Response schemas for AI financial forecasting
- Risk assessment and scoring schemas
- Market data integration schemas
- Cash flow prediction schemas
- Financial optimization schemas
- Advanced metrics and KPI schemas
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.types import BaseId

# Type aliases
FinancialForecastId = BaseId
RiskAssessmentId = BaseId
MarketDataId = BaseId
FinancialOptimizationId = BaseId
CashFlowPredictionId = BaseId
OrganizationId = BaseId
UserId = BaseId


# Enums for validation
class ForecastType(str, Enum):
    REVENUE = "revenue"
    EXPENSE = "expense"
    CASH_FLOW = "cash_flow"
    PROFIT = "profit"
    BUDGET = "budget"


class ForecastHorizon(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    MULTI_YEAR = "multi_year"


class AIModelType(str, Enum):
    LINEAR_REGRESSION = "linear_regression"
    ARIMA = "arima"
    LSTM = "lstm"
    PROPHET = "prophet"
    ENSEMBLE = "ensemble"


class RiskType(str, Enum):
    CREDIT = "credit"
    MARKET = "market"
    LIQUIDITY = "liquidity"
    OPERATIONAL = "operational"
    COMPREHENSIVE = "comprehensive"


class RiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MarketDataType(str, Enum):
    INTEREST_RATE = "interest_rate"
    EXCHANGE_RATE = "exchange_rate"
    STOCK_PRICE = "stock_price"
    COMMODITY = "commodity"
    INDEX = "index"


class OptimizationType(str, Enum):
    COST_REDUCTION = "cost_reduction"
    REVENUE_ENHANCEMENT = "revenue_enhancement"
    RISK_MITIGATION = "risk_mitigation"
    EFFICIENCY = "efficiency"
    COMPREHENSIVE = "comprehensive"


# ===============================
# Financial Forecast Schemas
# ===============================


class FinancialForecastBase(BaseModel):
    """Base schema for financial forecasts"""

    forecast_name: str = Field(..., min_length=1, max_length=255)
    forecast_type: ForecastType
    forecast_horizon: ForecastHorizon
    start_date: date
    end_date: date
    ai_model_type: AIModelType = AIModelType.ENSEMBLE
    training_data_period: int = Field(default=24, ge=6, le=120)  # 6 months to 10 years
    confidence_interval: Decimal = Field(
        default=Decimal("95.00"), ge=Decimal("50.00"), le=Decimal("99.99")
    )
    model_parameters: Dict[str, Any] = Field(default_factory=dict)

    @validator("end_date")
    def validate_date_range(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v

    @validator("confidence_interval")
    def validate_confidence_interval(cls, v):
        if not (50 <= v <= 99.99):
            raise ValueError("Confidence interval must be between 50% and 99.99%")
        return v


class FinancialForecastCreate(FinancialForecastBase):
    """Schema for creating financial forecasts"""

    organization_id: OrganizationId


class FinancialForecastUpdate(BaseModel):
    """Schema for updating financial forecasts"""

    forecast_name: Optional[str] = Field(None, min_length=1, max_length=255)
    ai_model_type: Optional[AIModelType] = None
    training_data_period: Optional[int] = Field(None, ge=6, le=120)
    confidence_interval: Optional[Decimal] = Field(
        None, ge=Decimal("50.00"), le=Decimal("99.99")
    )
    model_parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class FinancialForecastResponse(FinancialForecastBase):
    """Schema for financial forecast responses"""

    id: FinancialForecastId
    organization_id: OrganizationId
    forecast_data: Dict[str, Any]
    accuracy_score: Optional[Decimal] = None
    mean_absolute_error: Optional[Decimal] = None
    is_active: bool
    created_by: UserId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Risk Assessment Schemas
# ===============================


class RiskAssessmentBase(BaseModel):
    """Base schema for risk assessments"""

    assessment_name: str = Field(..., min_length=1, max_length=255)
    assessment_type: RiskType
    assessment_date: date
    overall_risk_score: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    credit_risk_score: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    market_risk_score: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    liquidity_risk_score: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    operational_risk_score: Decimal = Field(
        ..., ge=Decimal("0.00"), le=Decimal("100.00")
    )
    risk_level: RiskLevel
    risk_factors: Dict[str, Any] = Field(default_factory=dict)
    mitigation_strategies: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    confidence_score: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    data_quality_score: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))

    @validator("risk_level")
    def validate_risk_level_consistency(cls, v, values):
        if "overall_risk_score" in values:
            score = values["overall_risk_score"]
            expected_levels = {
                (0, 20): RiskLevel.VERY_LOW,
                (20, 40): RiskLevel.LOW,
                (40, 60): RiskLevel.MEDIUM,
                (60, 80): RiskLevel.HIGH,
                (80, 100): RiskLevel.VERY_HIGH,
            }

            for (min_score, max_score), expected_level in expected_levels.items():
                if min_score <= score < max_score or (
                    max_score == 100 and score == 100
                ):
                    if v != expected_level:
                        raise ValueError(
                            f"Risk level {v} inconsistent with score {score}"
                        )
                    break
        return v


class RiskAssessmentCreate(RiskAssessmentBase):
    """Schema for creating risk assessments"""

    organization_id: OrganizationId


class RiskAssessmentUpdate(BaseModel):
    """Schema for updating risk assessments"""

    assessment_name: Optional[str] = Field(None, min_length=1, max_length=255)
    overall_risk_score: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    credit_risk_score: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    market_risk_score: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    liquidity_risk_score: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    operational_risk_score: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    risk_level: Optional[RiskLevel] = None
    risk_factors: Optional[Dict[str, Any]] = None
    mitigation_strategies: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    confidence_score: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    data_quality_score: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    is_active: Optional[bool] = None


class RiskAssessmentResponse(RiskAssessmentBase):
    """Schema for risk assessment responses"""

    id: RiskAssessmentId
    organization_id: OrganizationId
    is_active: bool
    created_by: UserId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Market Data Schemas
# ===============================


class MarketDataBase(BaseModel):
    """Base schema for market data"""

    data_type: MarketDataType
    symbol: str = Field(..., min_length=1, max_length=50)
    market: str = Field(..., min_length=1, max_length=100)
    data_date: date
    open_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    close_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    high_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    low_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    volume: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    volatility: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    beta: Optional[Decimal] = None
    market_indicators: Dict[str, Any] = Field(default_factory=dict)
    data_source: str = Field(..., min_length=1, max_length=100)
    quality_score: Decimal = Field(
        default=Decimal("95.00"), ge=Decimal("0.00"), le=Decimal("100.00")
    )

    @validator("high_price")
    def validate_high_price(cls, v, values):
        if v is not None and "low_price" in values and values["low_price"] is not None:
            if v < values["low_price"]:
                raise ValueError("High price cannot be less than low price")
        return v


class MarketDataCreate(MarketDataBase):
    """Schema for creating market data"""

    pass


class MarketDataUpdate(BaseModel):
    """Schema for updating market data"""

    open_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    close_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    high_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    low_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    volume: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    volatility: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    beta: Optional[Decimal] = None
    market_indicators: Optional[Dict[str, Any]] = None
    quality_score: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )


class MarketDataResponse(MarketDataBase):
    """Schema for market data responses"""

    id: MarketDataId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Cash Flow Prediction Schemas
# ===============================


class CashFlowPredictionBase(BaseModel):
    """Base schema for cash flow predictions"""

    prediction_name: str = Field(..., min_length=1, max_length=255)
    prediction_type: str = Field(..., pattern="^(operating|investing|financing|total)$")
    prediction_period: str = Field(..., pattern="^(daily|weekly|monthly|quarterly)$")
    start_date: date
    end_date: date
    predicted_cashflow: Dict[str, Any] = Field(default_factory=dict)
    confidence_intervals: Dict[str, Any] = Field(default_factory=dict)
    scenario_analysis: Dict[str, Any] = Field(default_factory=dict)
    model_accuracy: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    prediction_variance: Decimal = Field(..., ge=Decimal("0.00"))
    risk_factors: List[str] = Field(default_factory=list)
    sensitivity_analysis: Dict[str, Any] = Field(default_factory=dict)
    optimization_recommendations: List[str] = Field(default_factory=list)

    @validator("end_date")
    def validate_prediction_date_range(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class CashFlowPredictionCreate(CashFlowPredictionBase):
    """Schema for creating cash flow predictions"""

    organization_id: OrganizationId


class CashFlowPredictionUpdate(BaseModel):
    """Schema for updating cash flow predictions"""

    prediction_name: Optional[str] = Field(None, min_length=1, max_length=255)
    predicted_cashflow: Optional[Dict[str, Any]] = None
    confidence_intervals: Optional[Dict[str, Any]] = None
    scenario_analysis: Optional[Dict[str, Any]] = None
    model_accuracy: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    risk_factors: Optional[List[str]] = None
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    optimization_recommendations: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CashFlowPredictionResponse(CashFlowPredictionBase):
    """Schema for cash flow prediction responses"""

    id: CashFlowPredictionId
    organization_id: OrganizationId
    is_active: bool
    created_by: UserId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Financial Optimization Schemas
# ===============================


class FinancialOptimizationBase(BaseModel):
    """Base schema for financial optimizations"""

    optimization_name: str = Field(..., min_length=1, max_length=255)
    optimization_type: OptimizationType
    priority_level: str = Field(..., pattern="^(low|medium|high|critical)$")
    current_metrics: Dict[str, Any] = Field(default_factory=dict)
    baseline_performance: Dict[str, Any] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    implementation_steps: List[str] = Field(default_factory=list)
    required_resources: Dict[str, Any] = Field(default_factory=dict)
    projected_savings: Decimal = Field(..., ge=Decimal("0.00"))
    projected_revenue_increase: Decimal = Field(..., ge=Decimal("0.00"))
    roi_percentage: Decimal = Field(..., ge=Decimal("-100.00"))  # Allow negative ROI
    payback_period_months: int = Field(..., ge=1, le=240)  # 1 month to 20 years
    implementation_risk: str = Field(..., pattern="^(low|medium|high)$")
    risk_mitigation_plan: List[str] = Field(default_factory=list)
    estimated_duration_months: int = Field(..., ge=1, le=120)  # 1 month to 10 years
    target_start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    implementation_status: str = Field(
        default="proposed",
        pattern="^(proposed|approved|in_progress|completed|cancelled)$",
    )
    progress_percentage: Decimal = Field(
        default=Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("100.00")
    )

    @validator("target_completion_date")
    def validate_completion_date(cls, v, values):
        if (
            v is not None
            and "target_start_date" in values
            and values["target_start_date"] is not None
        ):
            if v <= values["target_start_date"]:
                raise ValueError("Target completion date must be after start date")
        return v

    @validator("roi_percentage")
    def validate_roi(cls, v, values):
        if "projected_savings" in values and "required_resources" in values:
            # Basic ROI validation could be added here
            pass
        return v


class FinancialOptimizationCreate(FinancialOptimizationBase):
    """Schema for creating financial optimizations"""

    organization_id: OrganizationId


class FinancialOptimizationUpdate(BaseModel):
    """Schema for updating financial optimizations"""

    optimization_name: Optional[str] = Field(None, min_length=1, max_length=255)
    priority_level: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    current_metrics: Optional[Dict[str, Any]] = None
    recommended_actions: Optional[List[str]] = None
    implementation_steps: Optional[List[str]] = None
    required_resources: Optional[Dict[str, Any]] = None
    projected_savings: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    projected_revenue_increase: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    roi_percentage: Optional[Decimal] = Field(None, ge=Decimal("-100.00"))
    target_start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    implementation_status: Optional[str] = Field(
        None, pattern="^(proposed|approved|in_progress|completed|cancelled)$"
    )
    progress_percentage: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    is_active: Optional[bool] = None


class FinancialOptimizationResponse(FinancialOptimizationBase):
    """Schema for financial optimization responses"""

    id: FinancialOptimizationId
    organization_id: OrganizationId
    is_active: bool
    created_by: UserId
    approved_by: Optional[UserId] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Advanced Analytics Schemas
# ===============================


class FinancialAnalyticsRequest(BaseModel):
    """Schema for financial analytics requests"""

    organization_id: OrganizationId
    analysis_type: str = Field(
        ..., pattern="^(forecast|risk|optimization|prediction|comprehensive)$"
    )
    start_date: date
    end_date: date
    parameters: Dict[str, Any] = Field(default_factory=dict)
    include_ai_insights: bool = Field(default=True)
    confidence_level: Decimal = Field(
        default=Decimal("95.00"), ge=Decimal("50.00"), le=Decimal("99.99")
    )

    @validator("end_date")
    def validate_analytics_date_range(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class FinancialAnalyticsResponse(BaseModel):
    """Schema for financial analytics responses"""

    analysis_type: str
    organization_id: OrganizationId
    analysis_date: datetime
    results: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    confidence_score: Decimal
    data_quality_score: Decimal
    risk_factors: List[str]
    next_review_date: Optional[date] = None


# ===============================
# Bulk Operation Schemas
# ===============================


class BulkFinancialAnalysisRequest(BaseModel):
    """Schema for bulk financial analysis requests"""

    organization_ids: List[OrganizationId] = Field(..., min_items=1, max_items=100)
    analysis_types: List[str] = Field(..., min_items=1)
    common_parameters: Dict[str, Any] = Field(default_factory=dict)
    start_date: date
    end_date: date

    @validator("analysis_types")
    def validate_analysis_types(cls, v):
        valid_types = {
            "forecast",
            "risk",
            "optimization",
            "prediction",
            "comprehensive",
        }
        for analysis_type in v:
            if analysis_type not in valid_types:
                raise ValueError(f"Invalid analysis type: {analysis_type}")
        return v


class BulkFinancialAnalysisResponse(BaseModel):
    """Schema for bulk financial analysis responses"""

    total_organizations: int
    successful_analyses: int
    failed_analyses: int
    results: List[FinancialAnalyticsResponse]
    errors: List[str]
    processing_time_seconds: float


# ===============================
# Pagination and Listing Schemas
# ===============================


class FinancialForecastListResponse(BaseModel):
    """Schema for financial forecast list responses"""

    items: List[FinancialForecastResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class RiskAssessmentListResponse(BaseModel):
    """Schema for risk assessment list responses"""

    items: List[RiskAssessmentResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class CashFlowPredictionListResponse(BaseModel):
    """Schema for cash flow prediction list responses"""

    items: List[CashFlowPredictionResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class FinancialOptimizationListResponse(BaseModel):
    """Schema for financial optimization list responses"""

    items: List[FinancialOptimizationResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
