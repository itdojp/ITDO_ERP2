"""
ITDO ERP Backend - Multi-Currency Schemas
Day 25: Pydantic schemas for multi-currency financial operations

This module provides:
- Currency management schemas
- Exchange rate validation schemas
- Currency conversion calculation schemas
- Multi-currency hedging schemas
- Organization currency configuration schemas
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.types import BaseId

# Type aliases
CurrencyId = BaseId
ExchangeRateId = BaseId
CurrencyConversionId = BaseId
OrganizationId = BaseId
UserId = BaseId


# Enums for validation
class RoundingMethod(str, Enum):
    ROUND = "round"
    FLOOR = "floor"
    CEILING = "ceiling"


class RateType(str, Enum):
    SPOT = "spot"
    FORWARD = "forward"
    AVERAGE = "average"
    OFFICIAL = "official"
    MARKET = "market"


class ConversionType(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    HEDGED = "hedged"
    SPOT = "spot"


class HedgingStrategy(str, Enum):
    NONE = "none"
    NATURAL = "natural"
    FORWARD = "forward"
    OPTIONS = "options"
    SWAP = "swap"


class HedgeInstrumentType(str, Enum):
    FORWARD = "forward"
    FUTURES = "futures"
    OPTIONS = "options"
    SWAP = "swap"
    NATURAL = "natural"


# ===============================
# Currency Schemas
# ===============================


class CurrencyBase(BaseModel):
    """Base schema for currencies"""

    currency_code: str = Field(..., min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    currency_name: str = Field(..., min_length=1, max_length=100)
    currency_symbol: str = Field(..., min_length=1, max_length=10)
    numeric_code: Optional[int] = Field(None, ge=1, le=999)
    decimal_places: int = Field(default=2, ge=0, le=8)
    rounding_method: RoundingMethod = RoundingMethod.ROUND
    country_code: Optional[str] = Field(
        None, min_length=2, max_length=2, pattern="^[A-Z]{2}$"
    )
    region: Optional[str] = Field(None, max_length=50)
    is_active: bool = Field(default=True)
    is_base_currency: bool = Field(default=False)
    supports_fractional: bool = Field(default=True)
    display_format: str = Field(default="{symbol}{amount}", max_length=50)
    thousand_separator: str = Field(default=",", min_length=1, max_length=1)
    decimal_separator: str = Field(default=".", min_length=1, max_length=1)
    currency_properties: Dict[str, Any] = Field(default_factory=dict)

    @validator("currency_code")
    def validate_currency_code(cls, v):
        """Validate ISO 4217 currency code format"""
        if not v.isupper():
            raise ValueError("Currency code must be uppercase")
        return v

    @validator("display_format")
    def validate_display_format(cls, v):
        """Validate display format contains required placeholders"""
        if "{amount}" not in v:
            raise ValueError("Display format must contain {amount} placeholder")
        return v


class CurrencyCreate(CurrencyBase):
    """Schema for creating currencies"""

    pass


class CurrencyUpdate(BaseModel):
    """Schema for updating currencies"""

    currency_name: Optional[str] = Field(None, min_length=1, max_length=100)
    currency_symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    decimal_places: Optional[int] = Field(None, ge=0, le=8)
    rounding_method: Optional[RoundingMethod] = None
    country_code: Optional[str] = Field(
        None, min_length=2, max_length=2, pattern="^[A-Z]{2}$"
    )
    region: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_base_currency: Optional[bool] = None
    supports_fractional: Optional[bool] = None
    display_format: Optional[str] = Field(None, max_length=50)
    thousand_separator: Optional[str] = Field(None, min_length=1, max_length=1)
    decimal_separator: Optional[str] = Field(None, min_length=1, max_length=1)
    currency_properties: Optional[Dict[str, Any]] = None


class CurrencyResponse(CurrencyBase):
    """Schema for currency responses"""

    id: CurrencyId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Exchange Rate Schemas
# ===============================


class ExchangeRateBase(BaseModel):
    """Base schema for exchange rates"""

    base_currency_id: CurrencyId
    target_currency_id: CurrencyId
    rate_date: date
    exchange_rate: Decimal = Field(
        ..., gt=Decimal("0.000001"), le=Decimal("9999999999.999999")
    )
    inverse_rate: Decimal = Field(
        ..., gt=Decimal("0.000001"), le=Decimal("9999999999.999999")
    )
    rate_type: RateType = RateType.SPOT
    rate_source: str = Field(..., min_length=1, max_length=100)
    bid_rate: Optional[Decimal] = Field(None, gt=Decimal("0.000001"))
    ask_rate: Optional[Decimal] = Field(None, gt=Decimal("0.000001"))
    spread: Optional[Decimal] = Field(None, ge=Decimal("0.000001"))
    effective_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    is_active: bool = Field(default=True)
    confidence_score: Decimal = Field(
        default=Decimal("95.00"), ge=Decimal("0.00"), le=Decimal("100.00")
    )
    volatility_index: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    rate_metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("inverse_rate")
    def validate_inverse_rate(cls, v, values):
        """Validate inverse rate is approximately 1/exchange_rate"""
        if "exchange_rate" in values:
            expected_inverse = Decimal("1") / values["exchange_rate"]
            tolerance = Decimal("0.0001")
            if abs(v - expected_inverse) > tolerance:
                raise ValueError("Inverse rate must be approximately 1/exchange_rate")
        return v

    @validator("base_currency_id")
    def validate_different_currencies(cls, v, values):
        """Ensure base and target currencies are different"""
        if "target_currency_id" in values and v == values["target_currency_id"]:
            raise ValueError("Base and target currencies must be different")
        return v

    @validator("ask_rate")
    def validate_bid_ask_spread(cls, v, values):
        """Validate bid rate is less than ask rate"""
        if v is not None and "bid_rate" in values and values["bid_rate"] is not None:
            if values["bid_rate"] >= v:
                raise ValueError("Bid rate must be less than ask rate")
        return v

    @validator("expiry_time")
    def validate_time_range(cls, v, values):
        """Validate expiry time is after effective time"""
        if (
            v is not None
            and "effective_time" in values
            and values["effective_time"] is not None
        ):
            if v <= values["effective_time"]:
                raise ValueError("Expiry time must be after effective time")
        return v


class ExchangeRateCreate(ExchangeRateBase):
    """Schema for creating exchange rates"""

    pass


class ExchangeRateUpdate(BaseModel):
    """Schema for updating exchange rates"""

    exchange_rate: Optional[Decimal] = Field(None, gt=Decimal("0.000001"))
    inverse_rate: Optional[Decimal] = Field(None, gt=Decimal("0.000001"))
    rate_type: Optional[RateType] = None
    rate_source: Optional[str] = Field(None, min_length=1, max_length=100)
    bid_rate: Optional[Decimal] = Field(None, gt=Decimal("0.000001"))
    ask_rate: Optional[Decimal] = Field(None, gt=Decimal("0.000001"))
    spread: Optional[Decimal] = Field(None, ge=Decimal("0.000001"))
    effective_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    is_active: Optional[bool] = None
    confidence_score: Optional[Decimal] = Field(
        None, ge=Decimal("0.00"), le=Decimal("100.00")
    )
    volatility_index: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    rate_metadata: Optional[Dict[str, Any]] = None


class ExchangeRateResponse(ExchangeRateBase):
    """Schema for exchange rate responses"""

    id: ExchangeRateId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Currency Conversion Schemas
# ===============================


class CurrencyConversionRequest(BaseModel):
    """Schema for currency conversion requests"""

    source_currency_code: str = Field(..., min_length=3, max_length=3)
    target_currency_code: str = Field(..., min_length=3, max_length=3)
    source_amount: Decimal = Field(..., gt=Decimal("0.01"))
    conversion_date: date = Field(default_factory=date.today)
    include_fees: bool = Field(default=True)
    rate_type: RateType = RateType.SPOT

    @validator("target_currency_code")
    def validate_different_currencies(cls, v, values):
        """Ensure source and target currencies are different"""
        if "source_currency_code" in values and v == values["source_currency_code"]:
            raise ValueError("Source and target currencies must be different")
        return v


class CurrencyConversionCalculation(BaseModel):
    """Schema for currency conversion calculation results"""

    source_currency_code: str
    target_currency_code: str
    source_amount: Decimal
    target_amount: Decimal
    exchange_rate: Decimal
    conversion_fee: Decimal
    total_cost: Decimal
    rate_timestamp: datetime
    rate_source: str
    calculation_method: str


class CurrencyConversionBase(BaseModel):
    """Base schema for currency conversion records"""

    organization_id: OrganizationId
    conversion_date: date
    source_currency_id: CurrencyId
    source_amount: Decimal = Field(..., gt=Decimal("0.01"))
    target_currency_id: CurrencyId
    target_amount: Decimal = Field(..., gt=Decimal("0.01"))
    applied_rate: Decimal = Field(..., gt=Decimal("0.000001"))
    conversion_type: ConversionType = ConversionType.AUTOMATIC
    conversion_method: str = Field(default="real_time", max_length=50)
    conversion_fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    fee_currency_id: Optional[CurrencyId] = None
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[str] = Field(None, max_length=100)
    conversion_metadata: Dict[str, Any] = Field(default_factory=dict)


class CurrencyConversionCreate(CurrencyConversionBase):
    """Schema for creating currency conversions"""

    pass


class CurrencyConversionResponse(CurrencyConversionBase):
    """Schema for currency conversion responses"""

    id: CurrencyConversionId
    exchange_rate_id: Optional[ExchangeRateId] = None
    created_by: UserId
    created_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Organization Currency Schemas
# ===============================


class OrganizationCurrencyBase(BaseModel):
    """Base schema for organization currency configuration"""

    organization_id: OrganizationId
    currency_id: CurrencyId
    is_primary_currency: bool = Field(default=False)
    is_reporting_currency: bool = Field(default=False)
    is_allowed_for_transactions: bool = Field(default=True)
    default_exchange_rate_source: Optional[str] = Field(None, max_length=100)
    auto_conversion_enabled: bool = Field(default=False)
    conversion_threshold: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    display_priority: int = Field(default=1, ge=1, le=100)
    custom_display_format: Optional[str] = Field(None, max_length=100)
    exposure_limit: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    hedging_strategy: Optional[HedgingStrategy] = None
    enabled_date: date = Field(default_factory=date.today)
    disabled_date: Optional[date] = None
    is_active: bool = Field(default=True)
    currency_settings: Dict[str, Any] = Field(default_factory=dict)

    @validator("disabled_date")
    def validate_disabled_after_enabled(cls, v, values):
        """Validate disabled date is after enabled date"""
        if v is not None and "enabled_date" in values:
            if v <= values["enabled_date"]:
                raise ValueError("Disabled date must be after enabled date")
        return v


class OrganizationCurrencyCreate(OrganizationCurrencyBase):
    """Schema for creating organization currency configuration"""

    pass


class OrganizationCurrencyUpdate(BaseModel):
    """Schema for updating organization currency configuration"""

    is_primary_currency: Optional[bool] = None
    is_reporting_currency: Optional[bool] = None
    is_allowed_for_transactions: Optional[bool] = None
    default_exchange_rate_source: Optional[str] = Field(None, max_length=100)
    auto_conversion_enabled: Optional[bool] = None
    conversion_threshold: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    display_priority: Optional[int] = Field(None, ge=1, le=100)
    custom_display_format: Optional[str] = Field(None, max_length=100)
    exposure_limit: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    hedging_strategy: Optional[HedgingStrategy] = None
    disabled_date: Optional[date] = None
    is_active: Optional[bool] = None
    currency_settings: Optional[Dict[str, Any]] = None


class OrganizationCurrencyResponse(OrganizationCurrencyBase):
    """Schema for organization currency responses"""

    id: BaseId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Currency Hedging Schemas
# ===============================


class CurrencyHedgeBase(BaseModel):
    """Base schema for currency hedges"""

    organization_id: OrganizationId
    hedge_name: str = Field(..., min_length=1, max_length=255)
    instrument_type: HedgeInstrumentType
    base_currency_id: CurrencyId
    hedge_currency_id: CurrencyId
    notional_amount: Decimal = Field(..., gt=Decimal("0.01"))
    hedge_ratio: Decimal = Field(
        default=Decimal("1.0000"), gt=Decimal("0.0001"), le=Decimal("10.0000")
    )
    contract_rate: Optional[Decimal] = Field(None, gt=Decimal("0.000001"))
    premium_paid: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    contract_date: date
    maturity_date: date
    settlement_date: Optional[date] = None
    effectiveness_test_method: str = Field(default="dollar_offset")
    effectiveness_ratio: Optional[Decimal] = Field(
        None, ge=Decimal("0.80"), le=Decimal("1.25")
    )
    last_effectiveness_test: Optional[date] = None
    accounting_method: str = Field(default="fair_value")
    hedge_designation: str = Field(..., min_length=1, max_length=255)
    hedge_status: str = Field(default="active")
    fair_value: Optional[Decimal] = None
    unrealized_gain_loss: Optional[Decimal] = None
    hedge_details: Dict[str, Any] = Field(default_factory=dict)

    @validator("maturity_date")
    def validate_maturity_after_contract(cls, v, values):
        """Validate maturity date is after contract date"""
        if "contract_date" in values and v <= values["contract_date"]:
            raise ValueError("Maturity date must be after contract date")
        return v

    @validator("settlement_date")
    def validate_settlement_date(cls, v, values):
        """Validate settlement date is within reasonable range"""
        if v is not None and "maturity_date" in values:
            if v < values["maturity_date"]:
                raise ValueError("Settlement date cannot be before maturity date")
        return v

    @validator("hedge_currency_id")
    def validate_different_currencies(cls, v, values):
        """Ensure base and hedge currencies are different"""
        if "base_currency_id" in values and v == values["base_currency_id"]:
            raise ValueError("Base and hedge currencies must be different")
        return v


class CurrencyHedgeCreate(CurrencyHedgeBase):
    """Schema for creating currency hedges"""

    pass


class CurrencyHedgeUpdate(BaseModel):
    """Schema for updating currency hedges"""

    hedge_name: Optional[str] = Field(None, min_length=1, max_length=255)
    hedge_ratio: Optional[Decimal] = Field(
        None, gt=Decimal("0.0001"), le=Decimal("10.0000")
    )
    contract_rate: Optional[Decimal] = Field(None, gt=Decimal("0.000001"))
    settlement_date: Optional[date] = None
    effectiveness_ratio: Optional[Decimal] = Field(
        None, ge=Decimal("0.80"), le=Decimal("1.25")
    )
    last_effectiveness_test: Optional[date] = None
    hedge_designation: Optional[str] = Field(None, min_length=1, max_length=255)
    hedge_status: Optional[str] = None
    fair_value: Optional[Decimal] = None
    unrealized_gain_loss: Optional[Decimal] = None
    hedge_details: Optional[Dict[str, Any]] = None


class CurrencyHedgeResponse(CurrencyHedgeBase):
    """Schema for currency hedge responses"""

    id: BaseId
    created_by: UserId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===============================
# Pagination and Listing Schemas
# ===============================


class CurrencyListResponse(BaseModel):
    """Schema for currency list responses"""

    items: List[CurrencyResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ExchangeRateListResponse(BaseModel):
    """Schema for exchange rate list responses"""

    items: List[ExchangeRateResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class CurrencyConversionListResponse(BaseModel):
    """Schema for currency conversion list responses"""

    items: List[CurrencyConversionResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class OrganizationCurrencyListResponse(BaseModel):
    """Schema for organization currency list responses"""

    items: List[OrganizationCurrencyResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class CurrencyHedgeListResponse(BaseModel):
    """Schema for currency hedge list responses"""

    items: List[CurrencyHedgeResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


# ===============================
# Analytics and Reporting Schemas
# ===============================


class CurrencyExposureAnalysis(BaseModel):
    """Schema for currency exposure analysis"""

    organization_id: OrganizationId
    analysis_date: date
    base_currency: str
    total_exposure: Decimal
    currency_exposures: Dict[str, Decimal]
    hedged_percentage: Decimal
    var_1_day: Optional[Decimal] = None
    var_30_day: Optional[Decimal] = None
    risk_level: str
    recommendations: List[str]


class ExchangeRateVolatilityReport(BaseModel):
    """Schema for exchange rate volatility reports"""

    currency_pair: str
    analysis_period: str
    volatility_metrics: Dict[str, Decimal]
    trend_analysis: Dict[str, Any]
    risk_indicators: List[str]
    hedging_recommendations: List[str]
