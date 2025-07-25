"""Payment Processing Models

Complete payment processing system models with multi-provider support,
security compliance, and automated workflow management.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class PaymentStatus(str, Enum):
    """Payment processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"
    EXPIRED = "expired"


class PaymentMethod(str, Enum):
    """Supported payment methods"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    PAYPAY = "paypay"
    LINE_PAY = "line_pay"
    D_PAYMENT = "d_payment"
    RAKUTEN_PAY = "rakuten_pay"
    AMAZON_PAY = "amazon_pay"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


class PaymentProvider(str, Enum):
    """Payment gateway providers"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    GMO_PAYMENT = "gmo_payment"
    SQUARE = "square"
    RAZORPAY = "razorpay"
    ADYEN = "adyen"
    AUTHORIZE_NET = "authorize_net"
    BRAINTREE = "braintree"


class RefundReason(str, Enum):
    """Refund reasons"""
    CUSTOMER_REQUEST = "customer_request"
    FRAUD_DETECTED = "fraud_detected"
    DUPLICATE_PAYMENT = "duplicate_payment"
    PRODUCT_NOT_DELIVERED = "product_not_delivered"
    PRODUCT_DEFECTIVE = "product_defective"
    PROCESSING_ERROR = "processing_error"
    CHARGEBACK = "chargeback"
    OTHER = "other"


class PaymentTransaction(Base):
    """Core payment transaction model"""
    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Basic transaction info
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    external_transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Amount and currency
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="JPY")
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    fee_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    net_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    
    # Payment details
    payment_method: Mapped[PaymentMethod] = mapped_column(String(50))
    payment_provider: Mapped[PaymentProvider] = mapped_column(String(50))
    status: Mapped[PaymentStatus] = mapped_column(String(50), default=PaymentStatus.PENDING)
    
    # Customer and order references
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    order_id: Mapped[Optional[str]] = mapped_column(String(100))
    invoice_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Payment provider details
    provider_payment_id: Mapped[Optional[str]] = mapped_column(String(255))
    provider_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    provider_response: Mapped[Optional[Dict]] = mapped_column(JSON)
    
    # Security and fraud detection
    risk_score: Mapped[Optional[int]] = mapped_column(Integer)  # 0-100
    is_fraud_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    fraud_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Processing timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    authorized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Failure details
    failure_code: Mapped[Optional[str]] = mapped_column(String(100))
    failure_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Additional metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    extra_data: Mapped[Optional[Dict]] = mapped_column(JSON)
    
    # Relationships
    payment_method_info: Mapped[Optional["PaymentMethodInfo"]] = relationship(
        "PaymentMethodInfo", back_populates="transaction", uselist=False
    )
    refunds: Mapped[List["PaymentRefund"]] = relationship(
        "PaymentRefund", back_populates="transaction"
    )
    processing_logs: Mapped[List["PaymentProcessingLog"]] = relationship(
        "PaymentProcessingLog", back_populates="transaction"
    )


class PaymentMethodInfo(Base):
    """Secure payment method information storage"""
    __tablename__ = "payment_method_info"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_transactions.id")
    )
    
    # Tokenized payment method data (PCI DSS compliant)
    payment_token: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Card information (last 4 digits only for security)
    card_last_four: Mapped[Optional[str]] = mapped_column(String(4))
    card_brand: Mapped[Optional[str]] = mapped_column(String(50))  # visa, mastercard, etc.
    card_type: Mapped[Optional[str]] = mapped_column(String(50))   # credit, debit
    card_exp_month: Mapped[Optional[int]] = mapped_column(Integer)
    card_exp_year: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Bank account info (for bank transfers)
    bank_name: Mapped[Optional[str]] = mapped_column(String(200))
    bank_account_type: Mapped[Optional[str]] = mapped_column(String(50))
    bank_account_last_four: Mapped[Optional[str]] = mapped_column(String(4))
    
    # Digital wallet info
    wallet_email: Mapped[Optional[str]] = mapped_column(String(255))
    wallet_phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Security features
    three_d_secure_used: Mapped[bool] = mapped_column(Boolean, default=False)
    cvv_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    address_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    transaction: Mapped["PaymentTransaction"] = relationship(
        "PaymentTransaction", back_populates="payment_method_info"
    )


class PaymentRefund(Base):
    """Payment refund tracking"""
    __tablename__ = "payment_refunds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_transactions.id")
    )
    
    refund_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    external_refund_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Refund details
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="JPY")
    reason: Mapped[RefundReason] = mapped_column(String(50))
    reason_details: Mapped[Optional[str]] = mapped_column(Text)
    
    # Processing info
    status: Mapped[PaymentStatus] = mapped_column(String(50), default=PaymentStatus.PENDING)
    processed_by: Mapped[Optional[str]] = mapped_column(String(255))
    provider_response: Mapped[Optional[Dict]] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    transaction: Mapped["PaymentTransaction"] = relationship(
        "PaymentTransaction", back_populates="refunds"
    )


class PaymentProcessingLog(Base):
    """Detailed payment processing audit log"""
    __tablename__ = "payment_processing_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_transactions.id")
    )
    
    # Log details
    action: Mapped[str] = mapped_column(String(100))  # authorize, capture, refund, etc.
    status: Mapped[str] = mapped_column(String(50))
    message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Provider interaction
    provider_action: Mapped[Optional[str]] = mapped_column(String(100))
    provider_request: Mapped[Optional[Dict]] = mapped_column(JSON)
    provider_response: Mapped[Optional[Dict]] = mapped_column(JSON)
    
    # Timing and performance
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Security and compliance
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    transaction: Mapped["PaymentTransaction"] = relationship(
        "PaymentTransaction", back_populates="processing_logs"
    )


class PaymentProviderConfig(Base):
    """Payment provider configuration"""
    __tablename__ = "payment_provider_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    provider: Mapped[PaymentProvider] = mapped_column(String(50), unique=True)
    
    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_sandbox: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # API credentials (encrypted)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    api_secret_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    webhook_secret_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    
    # Provider settings
    supported_currencies: Mapped[List[str]] = mapped_column(JSON, default=list)
    supported_payment_methods: Mapped[List[str]] = mapped_column(JSON, default=list)
    max_transaction_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    min_transaction_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    
    # Rate limiting and retry settings
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=100)
    max_retry_attempts: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=5)
    
    # Webhook configuration
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500))
    webhook_events: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class PaymentAnalytics(Base):
    """Payment analytics and reporting"""
    __tablename__ = "payment_analytics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Time period
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_type: Mapped[str] = mapped_column(String(20))  # daily, weekly, monthly
    
    # Transaction metrics
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    successful_transactions: Mapped[int] = mapped_column(Integer, default=0)
    failed_transactions: Mapped[int] = mapped_column(Integer, default=0)
    
    # Amount metrics
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    successful_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    refunded_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Performance metrics
    average_processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    success_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    
    # Fraud metrics
    fraud_detected_count: Mapped[int] = mapped_column(Integer, default=0)
    fraud_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Provider breakdown
    provider_stats: Mapped[Dict] = mapped_column(JSON, default=dict)
    payment_method_stats: Mapped[Dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint('date', 'period_type', name='unique_analytics_period'),
    )