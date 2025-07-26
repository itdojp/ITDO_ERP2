"""
ITDO ERP Backend - Multi-Currency Support Models
Day 25: Multi-currency financial management with exchange rates

This module provides:
- Currency management and configuration
- Exchange rate tracking and historical data
- Multi-currency financial transactions
- Currency conversion and calculation
- Regional financial compliance
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
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.types import BaseId

# Type aliases
CurrencyId = BaseId
ExchangeRateId = BaseId
CurrencyConversionId = BaseId
OrganizationId = BaseId
UserId = BaseId


class Currency(Base):
    """Currency master data model"""

    __tablename__ = "currencies"

    id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    currency_code: Mapped[str] = mapped_column(
        String(3), nullable=False, unique=True
    )  # ISO 4217
    currency_name: Mapped[str] = mapped_column(String(100), nullable=False)
    currency_symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    numeric_code: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # ISO 4217 numeric

    # Currency properties
    decimal_places: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    rounding_method: Mapped[str] = mapped_column(
        SQLEnum("round", "floor", "ceiling", name="rounding_method_enum"),
        nullable=False,
        default="round",
    )

    # Regional information
    country_code: Mapped[Optional[str]] = mapped_column(
        String(2), nullable=True
    )  # ISO 3166-1
    region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status and configuration
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_base_currency: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    supports_fractional: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # Display formatting
    display_format: Mapped[str] = mapped_column(
        String(50), nullable=False, default="{symbol}{amount}"
    )
    thousand_separator: Mapped[str] = mapped_column(
        String(1), nullable=False, default=","
    )
    decimal_separator: Mapped[str] = mapped_column(
        String(1), nullable=False, default="."
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Additional properties
    currency_properties: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    def __repr__(self) -> str:
        return f"<Currency(code={self.currency_code}, name={self.currency_name})>"


class ExchangeRate(Base):
    """Exchange rate tracking model"""

    __tablename__ = "exchange_rates"

    id: Mapped[ExchangeRateId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    base_currency_id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_currency_id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Exchange rate values
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    inverse_rate: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)

    # Rate type and source
    rate_type: Mapped[str] = mapped_column(
        SQLEnum(
            "spot", "forward", "average", "official", "market", name="rate_type_enum"
        ),
        nullable=False,
        default="spot",
    )
    rate_source: Mapped[str] = mapped_column(String(100), nullable=False)

    # Bid/Ask spread for market rates
    bid_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 10), nullable=True)
    ask_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 10), nullable=True)
    spread: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)

    # Rate validity and status
    effective_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expiry_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Data quality and reliability
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("95.00")
    )
    volatility_index: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 6), nullable=True
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Rate metadata
    rate_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Relationships
    base_currency: Mapped[Currency] = relationship(
        "Currency", foreign_keys=[base_currency_id]
    )
    target_currency: Mapped[Currency] = relationship(
        "Currency", foreign_keys=[target_currency_id]
    )

    def __repr__(self) -> str:
        return f"<ExchangeRate(base={self.base_currency_id}, target={self.target_currency_id}, rate={self.exchange_rate})>"


class CurrencyConversion(Base):
    """Currency conversion transaction log"""

    __tablename__ = "currency_conversions"

    id: Mapped[CurrencyConversionId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversion_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Source currency details
    source_currency_id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)

    # Target currency details
    target_currency_id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)

    # Exchange rate used
    exchange_rate_id: Mapped[Optional[ExchangeRateId]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exchange_rates.id"), nullable=True
    )
    applied_rate: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)

    # Conversion details
    conversion_type: Mapped[str] = mapped_column(
        SQLEnum("automatic", "manual", "hedged", "spot", name="conversion_type_enum"),
        nullable=False,
        default="automatic",
    )
    conversion_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="real_time"
    )

    # Fees and charges
    conversion_fee: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 6), nullable=True
    )
    fee_currency_id: Mapped[Optional[CurrencyId]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id"), nullable=True
    )

    # Transaction references
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    created_by: Mapped[UserId] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Conversion metadata
    conversion_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Relationships
    source_currency: Mapped[Currency] = relationship(
        "Currency", foreign_keys=[source_currency_id]
    )
    target_currency: Mapped[Currency] = relationship(
        "Currency", foreign_keys=[target_currency_id]
    )
    exchange_rate: Mapped[Optional[ExchangeRate]] = relationship("ExchangeRate")

    def __repr__(self) -> str:
        return f"<CurrencyConversion(source={self.source_amount}, target={self.target_amount}, rate={self.applied_rate})>"


class OrganizationCurrency(Base):
    """Organization-specific currency configuration"""

    __tablename__ = "organization_currencies"

    id: Mapped[BaseId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    currency_id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Currency role in organization
    is_primary_currency: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_reporting_currency: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_allowed_for_transactions: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # Organization-specific settings
    default_exchange_rate_source: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    auto_conversion_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    conversion_threshold: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )

    # Display preferences
    display_priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    custom_display_format: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # Risk management
    exposure_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2), nullable=True
    )
    hedging_strategy: Mapped[Optional[str]] = mapped_column(
        SQLEnum(
            "none",
            "natural",
            "forward",
            "options",
            "swap",
            name="hedging_strategy_enum",
        ),
        nullable=True,
    )

    # Metadata
    enabled_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    disabled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Configuration metadata
    currency_settings: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Relationships
    currency: Mapped[Currency] = relationship("Currency")

    def __repr__(self) -> str:
        return f"<OrganizationCurrency(org={self.organization_id}, currency={self.currency_id})>"


class CurrencyHedge(Base):
    """Currency hedging instruments and positions"""

    __tablename__ = "currency_hedges"

    id: Mapped[BaseId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    hedge_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Hedge instrument details
    instrument_type: Mapped[str] = mapped_column(
        SQLEnum(
            "forward",
            "futures",
            "options",
            "swap",
            "natural",
            name="hedge_instrument_enum",
        ),
        nullable=False,
    )
    base_currency_id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    hedge_currency_id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Position details
    notional_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    hedge_ratio: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("1.0000")
    )

    # Contract terms
    contract_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 10), nullable=True
    )
    premium_paid: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 6), nullable=True
    )
    contract_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    settlement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Hedge effectiveness
    effectiveness_test_method: Mapped[str] = mapped_column(
        SQLEnum(
            "dollar_offset",
            "regression",
            "critical_terms",
            name="effectiveness_method_enum",
        ),
        nullable=False,
        default="dollar_offset",
    )
    effectiveness_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    last_effectiveness_test: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Accounting treatment
    accounting_method: Mapped[str] = mapped_column(
        SQLEnum(
            "fair_value", "cash_flow", "net_investment", name="hedge_accounting_enum"
        ),
        nullable=False,
        default="fair_value",
    )
    hedge_designation: Mapped[str] = mapped_column(String(255), nullable=False)

    # Current status
    hedge_status: Mapped[str] = mapped_column(
        SQLEnum(
            "active", "matured", "terminated", "ineffective", name="hedge_status_enum"
        ),
        nullable=False,
        default="active",
    )
    fair_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    unrealized_gain_loss: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 6), nullable=True
    )

    # Metadata
    created_by: Mapped[UserId] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Contract details
    hedge_details: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Relationships
    base_currency: Mapped[Currency] = relationship(
        "Currency", foreign_keys=[base_currency_id]
    )
    hedge_currency: Mapped[Currency] = relationship(
        "Currency", foreign_keys=[hedge_currency_id]
    )

    def __repr__(self) -> str:
        return f"<CurrencyHedge(name={self.hedge_name}, type={self.instrument_type}, amount={self.notional_amount})>"


class CurrencyRateAlert(Base):
    """Currency rate alerts and notifications"""

    __tablename__ = "currency_rate_alerts"

    id: Mapped[BaseId] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    alert_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Currency pair
    base_currency_id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_currency_id: Mapped[CurrencyId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Alert conditions
    alert_type: Mapped[str] = mapped_column(
        SQLEnum(
            "threshold",
            "percentage_change",
            "volatility",
            "trend",
            name="alert_type_enum",
        ),
        nullable=False,
    )
    condition_operator: Mapped[str] = mapped_column(
        SQLEnum(
            "greater_than",
            "less_than",
            "equals",
            "between",
            name="condition_operator_enum",
        ),
        nullable=False,
    )
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    secondary_threshold: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 10), nullable=True
    )

    # Alert settings
    monitoring_frequency: Mapped[str] = mapped_column(
        SQLEnum(
            "real_time", "hourly", "daily", "weekly", name="monitoring_frequency_enum"
        ),
        nullable=False,
        default="hourly",
    )
    alert_priority: Mapped[str] = mapped_column(
        SQLEnum("low", "medium", "high", "critical", name="alert_priority_enum"),
        nullable=False,
        default="medium",
    )

    # Notification preferences
    notification_methods: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    notification_recipients: Mapped[List[str]] = mapped_column(JSONB, nullable=False)

    # Alert status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_triggered: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trigger_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Metadata
    created_by: Mapped[UserId] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Alert configuration
    alert_settings: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Relationships
    base_currency: Mapped[Currency] = relationship(
        "Currency", foreign_keys=[base_currency_id]
    )
    target_currency: Mapped[Currency] = relationship(
        "Currency", foreign_keys=[target_currency_id]
    )

    def __repr__(self) -> str:
        return f"<CurrencyRateAlert(name={self.alert_name}, type={self.alert_type})>"
