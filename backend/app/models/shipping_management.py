"""Shipping management models for CC02 v61.0 - Day 6: Shipping Management System."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ShippingCarrier(str, Enum):
    """Available shipping carriers."""
    
    YAMATO = "yamato"  # ヤマト運輸
    SAGAWA = "sagawa"  # 佐川急便
    JAPAN_POST = "japan_post"  # 日本郵便
    FEDEX = "fedex"
    UPS = "ups"
    DHL = "dhl"
    CUSTOM = "custom"


class ShippingMethod(str, Enum):
    """Shipping method types."""
    
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"
    SAME_DAY = "same_day"
    PICKUP = "pickup"
    INTERNATIONAL = "international"


class ShipmentStatus(str, Enum):
    """Shipment status enumeration."""
    
    DRAFT = "draft"
    PENDING = "pending"
    LABEL_CREATED = "label_created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED_DELIVERY = "failed_delivery"
    RETURNED = "returned"
    CANCELLED = "cancelled"
    LOST = "lost"


class PackageType(str, Enum):
    """Package type enumeration."""
    
    ENVELOPE = "envelope"
    BOX = "box"
    TUBE = "tube"
    PAK = "pak"
    PALLET = "pallet"
    CUSTOM = "custom"


class DeliveryPriority(str, Enum):
    """Delivery priority levels."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class CarrierConfiguration(Base):
    """Carrier configuration and settings."""
    
    __tablename__ = "carrier_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    carrier: Mapped[ShippingCarrier] = mapped_column(String(50), nullable=False)
    
    # API Configuration
    api_endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key: Mapped[Optional[str]] = mapped_column(String(500))
    api_secret: Mapped[Optional[str]] = mapped_column(String(500))
    account_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Carrier Settings
    carrier_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supported_methods: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Rate Configuration
    base_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    weight_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # per kg
    distance_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # per km
    
    # Service Configuration
    max_weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    max_dimensions_cm: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # {length, width, height}
    service_areas: Mapped[Optional[List[str]]] = mapped_column(JSON)  # List of postal codes or regions
    
    # Business Rules
    business_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    pricing_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    shipments: Mapped[List["Shipment"]] = relationship("Shipment", back_populates="carrier_config")


class Address(Base):
    """Shipping address information."""
    
    __tablename__ = "shipping_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Address Details
    address_type: Mapped[str] = mapped_column(String(50), nullable=False)  # shipping, billing, return
    company_name: Mapped[Optional[str]] = mapped_column(String(200))
    contact_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Location
    address_line_1: Mapped[str] = mapped_column(String(500), nullable=False)
    address_line_2: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state_province: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="JP")
    
    # Contact Information
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Validation
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Geolocation
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    shipments_from: Mapped[List["Shipment"]] = relationship("Shipment", foreign_keys="[Shipment.from_address_id]", back_populates="from_address")
    shipments_to: Mapped[List["Shipment"]] = relationship("Shipment", foreign_keys="[Shipment.to_address_id]", back_populates="to_address")
    shipments_return: Mapped[List["Shipment"]] = relationship("Shipment", foreign_keys="[Shipment.return_address_id]", back_populates="return_address")


class Shipment(Base):
    """Main shipment entity."""
    
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Order Information
    order_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    customer_reference: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Carrier Information
    carrier_config_id: Mapped[int] = mapped_column(Integer, ForeignKey("carrier_configurations.id"), nullable=False)
    carrier_tracking_number: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    carrier_service: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Addresses
    from_address_id: Mapped[int] = mapped_column(Integer, ForeignKey("shipping_addresses.id"), nullable=False)
    to_address_id: Mapped[int] = mapped_column(Integer, ForeignKey("shipping_addresses.id"), nullable=False)
    return_address_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("shipping_addresses.id"))
    
    # Shipment Details
    current_status: Mapped[ShipmentStatus] = mapped_column(String(50), nullable=False, default=ShipmentStatus.DRAFT, index=True)
    shipping_method: Mapped[ShippingMethod] = mapped_column(String(50), nullable=False)
    package_type: Mapped[PackageType] = mapped_column(String(50), nullable=False, default=PackageType.BOX)
    delivery_priority: Mapped[DeliveryPriority] = mapped_column(String(50), nullable=False, default=DeliveryPriority.NORMAL)
    
    # Package Information
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    dimensions_cm: Mapped[Dict[str, float]] = mapped_column(JSON, nullable=False)  # length, width, height
    declared_value: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="JPY")
    
    # Insurance & Special Services
    insurance_value: Mapped[Optional[float]] = mapped_column(Float)
    requires_signature: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fragile: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_hazardous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text)
    
    # Delivery Options
    delivery_instructions: Mapped[Optional[str]] = mapped_column(Text)
    delivery_date_requested: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivery_time_window: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Pricing
    shipping_cost: Mapped[Optional[float]] = mapped_column(Float)
    insurance_cost: Mapped[Optional[float]] = mapped_column(Float)
    additional_fees: Mapped[Optional[float]] = mapped_column(Float)
    total_cost: Mapped[Optional[float]] = mapped_column(Float)
    cost_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Status Tracking
    status_history: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    last_status_update: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Label & Documentation
    shipping_label_url: Mapped[Optional[str]] = mapped_column(String(1000))
    commercial_invoice_url: Mapped[Optional[str]] = mapped_column(String(1000))
    customs_forms_url: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Delivery Information
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actual_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivery_confirmation: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Business Data
    shipment_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    carrier_config: Mapped["CarrierConfiguration"] = relationship("CarrierConfiguration", back_populates="shipments")
    from_address: Mapped["Address"] = relationship("Address", foreign_keys=[from_address_id], back_populates="shipments_from")
    to_address: Mapped["Address"] = relationship("Address", foreign_keys=[to_address_id], back_populates="shipments_to")
    return_address: Mapped[Optional["Address"]] = relationship("Address", foreign_keys=[return_address_id], back_populates="shipments_return")
    tracking_events: Mapped[List["ShipmentTracking"]] = relationship("ShipmentTracking", back_populates="shipment", cascade="all, delete-orphan")
    items: Mapped[List["ShipmentItem"]] = relationship("ShipmentItem", back_populates="shipment", cascade="all, delete-orphan")
    delivery_attempts: Mapped[List["DeliveryAttempt"]] = relationship("DeliveryAttempt", back_populates="shipment", cascade="all, delete-orphan")


class ShipmentItem(Base):
    """Individual items within a shipment."""
    
    __tablename__ = "shipment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("shipments.id"), nullable=False)
    
    # Item Details
    item_name: Mapped[str] = mapped_column(String(500), nullable=False)
    item_description: Mapped[Optional[str]] = mapped_column(Text)
    sku: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Physical Properties
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    dimensions_cm: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON)
    
    # Value & Classification
    unit_value: Mapped[float] = mapped_column(Float, nullable=False)
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="JPY")
    
    # Customs & Classification
    hs_code: Mapped[Optional[str]] = mapped_column(String(20))  # Harmonized System code
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(2))
    material: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Handling Requirements
    is_fragile: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_hazardous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_special_handling: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    handling_instructions: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    item_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="items")


class ShipmentTracking(Base):
    """Shipment tracking events and status updates."""
    
    __tablename__ = "shipment_tracking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("shipments.id"), nullable=False)
    
    # Tracking Information
    tracking_number: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    status: Mapped[ShipmentStatus] = mapped_column(String(50), nullable=False, index=True)
    status_description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Event Details
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_code: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Location Information
    location_name: Mapped[Optional[str]] = mapped_column(String(500))
    location_code: Mapped[Optional[str]] = mapped_column(String(50))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state_province: Mapped[Optional[str]] = mapped_column(String(100))
    country_code: Mapped[Optional[str]] = mapped_column(String(2))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Additional Data
    carrier_status_code: Mapped[Optional[str]] = mapped_column(String(50))
    next_expected_event: Mapped[Optional[str]] = mapped_column(String(500))
    estimated_delivery_update: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Source Information
    data_source: Mapped[str] = mapped_column(String(100), nullable=False)  # carrier_api, webhook, manual
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="tracking_events")


class DeliveryAttempt(Base):
    """Delivery attempt records."""
    
    __tablename__ = "delivery_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("shipments.id"), nullable=False)
    
    # Attempt Information
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Result
    delivery_status: Mapped[str] = mapped_column(String(50), nullable=False)  # delivered, failed, rescheduled
    failure_reason: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Delivery Details
    delivered_to: Mapped[Optional[str]] = mapped_column(String(200))
    delivery_location: Mapped[Optional[str]] = mapped_column(String(500))
    signature_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    signature_obtained: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    signature_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Proof of Delivery
    photo_url: Mapped[Optional[str]] = mapped_column(String(1000))
    signature_url: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Next Attempt
    next_attempt_scheduled: Mapped[Optional[datetime]] = mapped_column(DateTime)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text)
    
    # Driver Information
    driver_id: Mapped[Optional[str]] = mapped_column(String(100))
    vehicle_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Metadata
    attempt_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="delivery_attempts")


class ShippingRate(Base):
    """Shipping rate calculations and caching."""
    
    __tablename__ = "shipping_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Rate Request Details
    from_postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    to_postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    dimensions_cm: Mapped[Dict[str, float]] = mapped_column(JSON, nullable=False)
    
    # Carrier Information
    carrier: Mapped[ShippingCarrier] = mapped_column(String(50), nullable=False)
    service_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Rate Information
    base_rate: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_surcharge: Mapped[Optional[float]] = mapped_column(Float)
    insurance_cost: Mapped[Optional[float]] = mapped_column(Float)
    additional_fees: Mapped[Optional[float]] = mapped_column(Float)
    total_rate: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="JPY")
    
    # Service Details
    estimated_days: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime)
    service_features: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Cache Information
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    rate_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class ShippingZone(Base):
    """Shipping zones for rate calculation optimization."""
    
    __tablename__ = "shipping_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Zone Information
    zone_name: Mapped[str] = mapped_column(String(200), nullable=False)
    zone_code: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Coverage Area
    postal_codes: Mapped[List[str]] = mapped_column(JSON, default=list)
    cities: Mapped[List[str]] = mapped_column(JSON, default=list)
    prefectures: Mapped[List[str]] = mapped_column(JSON, default=list)  # For Japan
    
    # Rate Configuration
    base_rate: Mapped[float] = mapped_column(Float, nullable=False)
    per_kg_rate: Mapped[float] = mapped_column(Float, nullable=False)
    minimum_charge: Mapped[Optional[float]] = mapped_column(Float)
    
    # Service Options
    standard_delivery_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    express_delivery_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    same_day_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Business Rules
    max_weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    restricted_items: Mapped[List[str]] = mapped_column(JSON, default=list)
    special_requirements: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    zone_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class ShippingNotification(Base):
    """Shipping notifications and alerts."""
    
    __tablename__ = "shipping_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("shipments.id"), nullable=False)
    
    # Notification Details
    notification_type: Mapped[str] = mapped_column(String(100), nullable=False)  # status_update, delivery_alert, exception
    notification_method: Mapped[str] = mapped_column(String(50), nullable=False)  # email, sms, webhook
    
    # Recipient Information
    recipient_email: Mapped[Optional[str]] = mapped_column(String(255))
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(50))
    webhook_url: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Message Content
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    message_body: Mapped[str] = mapped_column(Text, nullable=False)
    template_used: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Delivery Status
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivery_status: Mapped[Optional[str]] = mapped_column(String(50))  # delivered, bounced, failed
    
    # Retry Logic
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Response Tracking
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    response_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Metadata
    notification_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class ShippingRule(Base):
    """Business rules for shipping automation."""
    
    __tablename__ = "shipping_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Rule Definition
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_description: Mapped[Optional[str]] = mapped_column(Text)
    rule_type: Mapped[str] = mapped_column(String(100), nullable=False)  # carrier_selection, rate_override, notification
    
    # Conditions
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Actions
    actions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Priority & Status
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Usage Statistics
    execution_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_executed: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Metadata
    rule_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)