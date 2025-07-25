"""Payment Processing Schemas

Pydantic schemas for payment processing API requests and responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator

from app.models.payment_processing import (
    PaymentStatus,
    PaymentMethod,
    PaymentProvider,
    RefundReason,
)


# Base schemas
class PaymentProcessingBase(BaseModel):
    """Base payment processing schema"""
    
    class Config:
        from_attributes = True
        use_enum_values = True


# Payment request schemas
class PaymentMethodInfoRequest(PaymentProcessingBase):
    """Payment method information for requests"""
    card_token: Optional[str] = Field(None, description="Secure card token")
    card_number: Optional[str] = Field(None, description="Card number (testing only)", min_length=13, max_length=19)
    card_exp_month: Optional[int] = Field(None, description="Card expiration month", ge=1, le=12)
    card_exp_year: Optional[int] = Field(None, description="Card expiration year", ge=2024, le=2034)
    card_cvv: Optional[str] = Field(None, description="Card CVV", min_length=3, max_length=4)
    
    # Bank transfer info
    bank_account_token: Optional[str] = Field(None, description="Bank account token")
    
    # Digital wallet info
    wallet_email: Optional[str] = Field(None, description="Wallet email address")
    wallet_phone: Optional[str] = Field(None, description="Wallet phone number")
    
    @validator('card_number')
    def validate_card_number(cls, v):
        if v and not v.replace(' ', '').isdigit():
            raise ValueError('Card number must contain only digits')
        return v.replace(' ', '') if v else v


class CustomerInfoRequest(PaymentProcessingBase):
    """Customer information for fraud detection"""
    email: Optional[str] = Field(None, description="Customer email")
    ip_address: Optional[str] = Field(None, description="Customer IP address")
    user_agent: Optional[str] = Field(None, description="Customer user agent")
    
    # Billing address
    billing_address_line1: Optional[str] = Field(None, description="Billing address line 1")
    billing_address_line2: Optional[str] = Field(None, description="Billing address line 2")
    billing_city: Optional[str] = Field(None, description="Billing city")
    billing_state: Optional[str] = Field(None, description="Billing state/province")
    billing_postal_code: Optional[str] = Field(None, description="Billing postal code")
    billing_country: Optional[str] = Field(None, description="Billing country code")


class PaymentCreateRequest(PaymentProcessingBase):
    """Payment creation request"""
    amount: Decimal = Field(..., description="Payment amount", gt=0)
    currency: str = Field("JPY", description="Currency code")
    payment_method: PaymentMethod = Field(PaymentMethod.CREDIT_CARD, description="Payment method")
    payment_provider: PaymentProvider = Field(PaymentProvider.STRIPE, description="Payment provider")
    
    # Order information
    customer_id: Optional[uuid.UUID] = Field(None, description="Customer ID")
    order_id: Optional[str] = Field(None, description="Order ID")
    invoice_id: Optional[str] = Field(None, description="Invoice ID")
    description: Optional[str] = Field(None, description="Payment description")
    
    # Payment method info
    payment_method_info: Optional[PaymentMethodInfoRequest] = Field(None, description="Payment method details")
    
    # Customer info for fraud detection
    customer_info: Optional[CustomerInfoRequest] = Field(None, description="Customer information")
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('currency')
    def validate_currency(cls, v):
        valid_currencies = ['JPY', 'USD', 'EUR', 'GBP', 'AUD', 'CAD']
        if v not in valid_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(valid_currencies)}')
        return v


class PaymentRefundRequest(PaymentProcessingBase):
    """Payment refund request"""
    amount: Optional[Decimal] = Field(None, description="Refund amount (null for full refund)", gt=0)
    reason: RefundReason = Field(RefundReason.CUSTOMER_REQUEST, description="Refund reason")
    reason_details: Optional[str] = Field(None, description="Detailed reason for refund")
    notify_customer: bool = Field(True, description="Whether to notify customer")


class PaymentSearchRequest(PaymentProcessingBase):
    """Payment search request"""
    customer_id: Optional[uuid.UUID] = Field(None, description="Filter by customer ID")
    status: Optional[PaymentStatus] = Field(None, description="Filter by payment status")
    payment_method: Optional[PaymentMethod] = Field(None, description="Filter by payment method")
    payment_provider: Optional[PaymentProvider] = Field(None, description="Filter by payment provider")
    
    # Date range
    date_from: Optional[datetime] = Field(None, description="Start date for search")
    date_to: Optional[datetime] = Field(None, description="End date for search")
    
    # Amount range
    min_amount: Optional[Decimal] = Field(None, description="Minimum amount", ge=0)
    max_amount: Optional[Decimal] = Field(None, description="Maximum amount", ge=0)
    
    # Pagination
    limit: int = Field(100, description="Number of results to return", ge=1, le=1000)
    offset: int = Field(0, description="Number of results to skip", ge=0)
    
    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        if v and values.get('min_amount') and v < values['min_amount']:
            raise ValueError('max_amount must be greater than min_amount')
        return v


# Response schemas
class PaymentMethodInfoResponse(PaymentProcessingBase):
    """Payment method information response"""
    id: uuid.UUID
    
    # Secure card information (only last 4 digits)
    card_last_four: Optional[str] = Field(None, description="Last 4 digits of card")
    card_brand: Optional[str] = Field(None, description="Card brand (visa, mastercard, etc.)")
    card_type: Optional[str] = Field(None, description="Card type (credit, debit)")
    card_exp_month: Optional[int] = Field(None, description="Card expiration month")
    card_exp_year: Optional[int] = Field(None, description="Card expiration year")
    
    # Bank information
    bank_name: Optional[str] = Field(None, description="Bank name")
    bank_account_last_four: Optional[str] = Field(None, description="Last 4 digits of account")
    
    # Digital wallet info
    wallet_email: Optional[str] = Field(None, description="Wallet email (masked)")
    
    # Security verification
    three_d_secure_used: bool = Field(False, description="Whether 3D Secure was used")
    cvv_verified: bool = Field(False, description="Whether CVV was verified")
    address_verified: bool = Field(False, description="Whether address was verified")
    
    created_at: datetime


class PaymentRefundResponse(PaymentProcessingBase):
    """Payment refund response"""
    id: uuid.UUID
    refund_id: str = Field(..., description="Unique refund identifier")
    external_refund_id: Optional[str] = Field(None, description="External provider refund ID")
    
    amount: Decimal = Field(..., description="Refund amount")
    currency: str = Field(..., description="Currency code")
    reason: RefundReason = Field(..., description="Refund reason")
    reason_details: Optional[str] = Field(None, description="Detailed reason")
    
    status: PaymentStatus = Field(..., description="Refund status")
    processed_by: Optional[str] = Field(None, description="User who processed refund")
    
    created_at: datetime
    processed_at: Optional[datetime] = Field(None, description="When refund was processed")


class PaymentProcessingLogResponse(PaymentProcessingBase):
    """Payment processing log response"""
    id: uuid.UUID
    action: str = Field(..., description="Processing action")
    status: str = Field(..., description="Action status")
    message: Optional[str] = Field(None, description="Status message")
    
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    retry_count: int = Field(0, description="Number of retries")
    
    created_at: datetime


class PaymentTransactionResponse(PaymentProcessingBase):
    """Payment transaction response"""
    id: uuid.UUID
    transaction_id: str = Field(..., description="Unique transaction identifier")
    external_transaction_id: Optional[str] = Field(None, description="External provider transaction ID")
    
    # Amount information
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    tax_amount: Optional[Decimal] = Field(None, description="Tax amount")
    fee_amount: Optional[Decimal] = Field(None, description="Processing fee")
    net_amount: Optional[Decimal] = Field(None, description="Net amount received")
    
    # Payment details
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    payment_provider: PaymentProvider = Field(..., description="Payment provider used")
    status: PaymentStatus = Field(..., description="Payment status")
    
    # References
    customer_id: Optional[uuid.UUID] = Field(None, description="Customer ID")
    order_id: Optional[str] = Field(None, description="Order ID")
    invoice_id: Optional[str] = Field(None, description="Invoice ID")
    
    # Provider details
    provider_payment_id: Optional[str] = Field(None, description="Provider payment ID")
    
    # Security and fraud
    risk_score: Optional[int] = Field(None, description="Fraud risk score (0-100)")
    is_fraud_flagged: bool = Field(False, description="Whether flagged as potential fraud")
    fraud_reason: Optional[str] = Field(None, description="Fraud detection reason")
    
    # Processing timestamps
    created_at: datetime
    authorized_at: Optional[datetime] = Field(None, description="When payment was authorized")
    captured_at: Optional[datetime] = Field(None, description="When payment was captured")
    completed_at: Optional[datetime] = Field(None, description="When payment was completed")
    failed_at: Optional[datetime] = Field(None, description="When payment failed")
    
    # Failure details
    failure_code: Optional[str] = Field(None, description="Failure error code")
    failure_message: Optional[str] = Field(None, description="Failure error message")
    
    # Additional info
    description: Optional[str] = Field(None, description="Payment description")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    # Related data
    payment_method_info: Optional[PaymentMethodInfoResponse] = None
    refunds: List[PaymentRefundResponse] = Field(default_factory=list)
    processing_logs: List[PaymentProcessingLogResponse] = Field(default_factory=list)


class PaymentResponse(PaymentProcessingBase):
    """Simple payment response for create/update operations"""
    success: bool = Field(..., description="Whether operation was successful")
    transaction_id: str = Field(..., description="Transaction identifier")
    external_id: Optional[str] = Field(None, description="External provider ID")
    status: PaymentStatus = Field(..., description="Payment status")
    message: Optional[str] = Field(None, description="Status message")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    risk_score: Optional[int] = Field(None, description="Fraud risk score")
    requires_action: bool = Field(False, description="Whether additional action is required")
    action_url: Optional[str] = Field(None, description="URL for additional action")


class PaymentSearchResponse(PaymentProcessingBase):
    """Payment search results response"""
    transactions: List[PaymentTransactionResponse] = Field(..., description="Found transactions")
    total_count: int = Field(..., description="Total number of matching transactions")
    limit: int = Field(..., description="Results limit used")
    offset: int = Field(..., description="Results offset used")
    has_more: bool = Field(..., description="Whether more results are available")
    
    @validator('has_more', pre=False, always=True)
    def calculate_has_more(cls, v, values):
        total = values.get('total_count', 0)
        limit = values.get('limit', 0)
        offset = values.get('offset', 0)
        return offset + limit < total


# Analytics schemas
class PaymentAnalyticsBreakdown(PaymentProcessingBase):
    """Analytics breakdown by category"""
    count: int = Field(..., description="Number of transactions")
    amount: float = Field(..., description="Total amount")
    percentage: float = Field(..., description="Percentage of total")


class PaymentAnalyticsTotals(PaymentProcessingBase):
    """Payment analytics totals"""
    transactions: int = Field(..., description="Total number of transactions")
    successful_transactions: int = Field(..., description="Number of successful transactions")
    failed_transactions: int = Field(..., description="Number of failed transactions")
    total_amount: float = Field(..., description="Total transaction amount")
    successful_amount: float = Field(..., description="Successfully processed amount")
    success_rate: float = Field(..., description="Success rate percentage")
    average_risk_score: float = Field(..., description="Average fraud risk score")
    average_transaction_amount: float = Field(..., description="Average transaction amount")


class PaymentAnalyticsResponse(PaymentProcessingBase):
    """Payment analytics response"""
    period: Dict[str, str] = Field(..., description="Analysis period")
    totals: PaymentAnalyticsTotals = Field(..., description="Overall totals")
    breakdown: Dict[str, Dict[str, PaymentAnalyticsBreakdown]] = Field(..., description="Detailed breakdowns")
    
    # Trend data
    daily_trends: Optional[List[Dict[str, Any]]] = Field(None, description="Daily trend data")
    hourly_patterns: Optional[List[Dict[str, Any]]] = Field(None, description="Hourly patterns")
    
    # Top performers
    top_customers: Optional[List[Dict[str, Any]]] = Field(None, description="Top customers by volume")
    top_payment_methods: Optional[List[Dict[str, Any]]] = Field(None, description="Most used payment methods")


# Webhook schemas
class PaymentWebhookEvent(PaymentProcessingBase):
    """Payment webhook event"""
    event_type: str = Field(..., description="Type of webhook event")
    transaction_id: str = Field(..., description="Related transaction ID")
    event_data: Dict[str, Any] = Field(..., description="Event-specific data")
    timestamp: datetime = Field(..., description="Event timestamp")
    provider: PaymentProvider = Field(..., description="Payment provider")
    signature: Optional[str] = Field(None, description="Webhook signature for verification")


# Provider configuration schemas
class PaymentProviderConfigResponse(PaymentProcessingBase):
    """Payment provider configuration response"""
    id: uuid.UUID
    provider: PaymentProvider = Field(..., description="Payment provider")
    is_active: bool = Field(..., description="Whether provider is active")
    is_sandbox: bool = Field(..., description="Whether in sandbox mode")
    
    supported_currencies: List[str] = Field(..., description="Supported currencies")
    supported_payment_methods: List[str] = Field(..., description="Supported payment methods")
    max_transaction_amount: Optional[Decimal] = Field(None, description="Maximum transaction amount")
    min_transaction_amount: Optional[Decimal] = Field(None, description="Minimum transaction amount")
    
    rate_limit_per_minute: int = Field(..., description="Rate limit per minute")
    max_retry_attempts: int = Field(..., description="Maximum retry attempts")
    retry_delay_seconds: int = Field(..., description="Retry delay in seconds")
    
    created_at: datetime
    updated_at: datetime