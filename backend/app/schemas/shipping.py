"""Shipping management schemas for CC02 v61.0 - Day 6: Shipping Management System."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.shipping_management import (
    DeliveryPriority,
    PackageType,
    ShipmentStatus,
    ShippingCarrier,
    ShippingMethod,
)


class AddressBase(BaseModel):
    """Base address schema."""
    
    company_name: Optional[str] = Field(None, description="Company name")
    contact_name: str = Field(..., description="Contact person name")
    address_line_1: str = Field(..., description="Primary address line")
    address_line_2: Optional[str] = Field(None, description="Secondary address line")
    city: str = Field(..., description="City")
    state_province: Optional[str] = Field(None, description="State or province")
    postal_code: str = Field(..., description="Postal code")
    country_code: str = Field("JP", description="Country code")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")


class AddressCreate(AddressBase):
    """Schema for creating an address."""
    pass


class AddressResponse(AddressBase):
    """Schema for address response."""
    
    id: int
    address_type: str
    is_validated: bool
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CarrierConfigurationBase(BaseModel):
    """Base carrier configuration schema."""
    
    carrier: ShippingCarrier = Field(..., description="Carrier type")
    api_endpoint: str = Field(..., description="API endpoint URL")
    api_key: Optional[str] = Field(None, description="API key")
    api_secret: Optional[str] = Field(None, description="API secret")
    account_number: Optional[str] = Field(None, description="Account number")
    carrier_name: str = Field(..., description="Carrier display name")
    is_active: bool = Field(True, description="Is carrier active")
    is_default: bool = Field(False, description="Is default carrier")
    supported_methods: List[str] = Field(default_factory=list, description="Supported shipping methods")
    base_rate: float = Field(0.0, ge=0, description="Base shipping rate")
    weight_rate: float = Field(0.0, ge=0, description="Rate per kg")
    distance_rate: float = Field(0.0, ge=0, description="Rate per km")
    max_weight_kg: Optional[float] = Field(None, ge=0, description="Maximum weight in kg")
    max_dimensions_cm: Optional[Dict[str, float]] = Field(None, description="Maximum dimensions")
    service_areas: Optional[List[str]] = Field(None, description="Service area codes")
    business_rules: Optional[Dict[str, Any]] = Field(None, description="Business rules")
    pricing_rules: Optional[Dict[str, Any]] = Field(None, description="Pricing rules")


class CarrierConfigurationCreate(CarrierConfigurationBase):
    """Schema for creating carrier configuration."""
    pass


class CarrierConfigurationResponse(CarrierConfigurationBase):
    """Schema for carrier configuration response."""
    
    id: int
    organization_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShipmentItemBase(BaseModel):
    """Base shipment item schema."""
    
    item_name: str = Field(..., description="Item name")
    item_description: Optional[str] = Field(None, description="Item description")
    sku: Optional[str] = Field(None, description="SKU")
    quantity: int = Field(1, ge=1, description="Quantity")
    weight_kg: float = Field(..., ge=0, description="Weight in kg")
    dimensions_cm: Optional[Dict[str, float]] = Field(None, description="Dimensions in cm")
    unit_value: float = Field(..., ge=0, description="Unit value")
    total_value: float = Field(..., ge=0, description="Total value")
    currency: str = Field("JPY", description="Currency code")
    hs_code: Optional[str] = Field(None, description="HS code")
    country_of_origin: Optional[str] = Field(None, description="Country of origin")
    material: Optional[str] = Field(None, description="Material")
    is_fragile: bool = Field(False, description="Is fragile")
    is_hazardous: bool = Field(False, description="Is hazardous")
    requires_special_handling: bool = Field(False, description="Requires special handling")
    handling_instructions: Optional[str] = Field(None, description="Handling instructions")


class ShipmentItemCreate(ShipmentItemBase):
    """Schema for creating shipment item."""
    pass


class ShipmentItemResponse(ShipmentItemBase):
    """Schema for shipment item response."""
    
    id: int
    shipment_id: int
    item_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShipmentBase(BaseModel):
    """Base shipment schema."""
    
    order_id: Optional[str] = Field(None, description="Order ID reference")
    customer_reference: Optional[str] = Field(None, description="Customer reference")
    shipping_method: ShippingMethod = Field(..., description="Shipping method")
    package_type: PackageType = Field(PackageType.BOX, description="Package type")
    delivery_priority: DeliveryPriority = Field(DeliveryPriority.NORMAL, description="Delivery priority")
    dimensions_cm: Dict[str, float] = Field(..., description="Package dimensions")
    declared_value: Optional[float] = Field(None, ge=0, description="Declared value")
    currency: str = Field("JPY", description="Currency code")
    insurance_value: Optional[float] = Field(None, ge=0, description="Insurance value")
    requires_signature: bool = Field(False, description="Requires signature")
    is_fragile: bool = Field(False, description="Is fragile")
    is_hazardous: bool = Field(False, description="Is hazardous")
    special_instructions: Optional[str] = Field(None, description="Special instructions")
    delivery_instructions: Optional[str] = Field(None, description="Delivery instructions")
    delivery_date_requested: Optional[datetime] = Field(None, description="Requested delivery date")
    delivery_time_window: Optional[Dict[str, Any]] = Field(None, description="Delivery time window")


class ShipmentCreate(ShipmentBase):
    """Schema for creating shipment."""
    
    from_address: AddressCreate = Field(..., description="Sender address")
    to_address: AddressCreate = Field(..., description="Recipient address")
    return_address: Optional[AddressCreate] = Field(None, description="Return address")
    items: List[ShipmentItemCreate] = Field(..., description="Shipment items")


class ShipmentTrackingEventResponse(BaseModel):
    """Schema for tracking event response."""
    
    timestamp: datetime
    status: str
    description: str
    location: Optional[str]
    city: Optional[str]
    country: Optional[str]
    event_type: str
    event_code: Optional[str]


class ShipmentResponse(ShipmentBase):
    """Schema for shipment response."""
    
    id: int
    shipment_id: str
    organization_id: str
    current_status: ShipmentStatus
    carrier_tracking_number: Optional[str]
    carrier_service: Optional[str]
    weight_kg: float
    
    # Addresses
    from_address: AddressResponse
    to_address: AddressResponse
    return_address: Optional[AddressResponse]
    
    # Carrier information
    carrier_config: CarrierConfigurationResponse
    
    # Items
    items: List[ShipmentItemResponse]
    
    # Pricing
    shipping_cost: Optional[float]
    insurance_cost: Optional[float]
    additional_fees: Optional[float]
    total_cost: Optional[float]
    cost_breakdown: Optional[Dict[str, Any]]
    
    # Status tracking
    status_history: Optional[List[Dict[str, Any]]]
    last_status_update: Optional[datetime]
    
    # Labels & documentation
    shipping_label_url: Optional[str]
    commercial_invoice_url: Optional[str]
    customs_forms_url: Optional[str]
    
    # Delivery information
    estimated_delivery: Optional[datetime]
    actual_delivery: Optional[datetime]
    delivery_confirmation: Optional[Dict[str, Any]]
    
    # Processing information
    is_processed: bool
    processed_at: Optional[datetime]
    created_by: Optional[str]
    
    # Metadata
    shipment_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShipmentSearch(BaseModel):
    """Schema for searching shipments."""
    
    status: Optional[List[ShipmentStatus]] = Field(None, description="Filter by status")
    carrier: Optional[ShippingCarrier] = Field(None, description="Filter by carrier")
    order_id: Optional[str] = Field(None, description="Filter by order ID")
    tracking_number: Optional[str] = Field(None, description="Filter by tracking number")
    customer_reference: Optional[str] = Field(None, description="Filter by customer reference")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    limit: int = Field(100, ge=1, le=1000, description="Result limit")
    offset: int = Field(0, ge=0, description="Result offset")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        date_from = values.get('date_from')
        if date_from is not None and v is not None and v < date_from:
            raise ValueError('date_to must be greater than date_from')
        return v


class ShipmentStatusUpdate(BaseModel):
    """Schema for updating shipment status."""
    
    status: ShipmentStatus = Field(..., description="New status")
    location: Optional[str] = Field(None, description="Current location")
    notes: Optional[str] = Field(None, description="Status update notes")


class ShipmentTrackingResponse(BaseModel):
    """Schema for shipment tracking response."""
    
    shipment_id: str
    tracking_number: Optional[str]
    current_status: str
    estimated_delivery: Optional[datetime]
    actual_delivery: Optional[datetime]
    events: List[ShipmentTrackingEventResponse]
    delivery_attempts: int
    is_delivered: bool


class ShippingRateRequest(BaseModel):
    """Schema for shipping rate request."""
    
    from_postal_code: str = Field(..., description="Origin postal code")
    to_postal_code: str = Field(..., description="Destination postal code")
    weight_kg: float = Field(..., ge=0, description="Package weight in kg")
    dimensions_cm: Dict[str, float] = Field(..., description="Package dimensions")
    shipping_method: ShippingMethod = Field(ShippingMethod.STANDARD, description="Shipping method")
    package_type: PackageType = Field(PackageType.BOX, description="Package type")
    declared_value: Optional[float] = Field(None, ge=0, description="Declared value")
    insurance_required: bool = Field(False, description="Insurance required")


class ShippingRateResponse(BaseModel):
    """Schema for shipping rate response."""
    
    carrier: str
    carrier_name: str
    service_type: str
    total_rate: float
    currency: str
    estimated_days: Optional[int]
    estimated_delivery: Optional[datetime]
    service_features: List[str]


class DeliveryAttemptResponse(BaseModel):
    """Schema for delivery attempt response."""
    
    id: int
    attempt_number: int
    attempt_date: datetime
    delivery_status: str
    failure_reason: Optional[str]
    delivered_to: Optional[str]
    delivery_location: Optional[str]
    signature_required: bool
    signature_obtained: bool
    signature_name: Optional[str]
    photo_url: Optional[str]
    signature_url: Optional[str]
    next_attempt_scheduled: Optional[datetime]
    special_instructions: Optional[str]
    
    class Config:
        from_attributes = True


class ShippingNotificationResponse(BaseModel):
    """Schema for shipping notification response."""
    
    id: int
    notification_type: str
    notification_method: str
    recipient_email: Optional[str]
    recipient_phone: Optional[str]
    subject: str
    message_body: str
    is_sent: bool
    sent_at: Optional[datetime]
    delivery_status: Optional[str]
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ShippingAnalytics(BaseModel):
    """Schema for shipping analytics."""
    
    total_shipments: int = Field(..., description="Total number of shipments")
    status_distribution: Dict[str, int] = Field(..., description="Distribution by status")
    carrier_distribution: Dict[str, int] = Field(..., description="Distribution by carrier")
    shipping_costs: Dict[str, float] = Field(..., description="Shipping cost statistics")
    delivery_performance: Dict[str, float] = Field(..., description="Delivery performance metrics")


class ShippingZoneBase(BaseModel):
    """Base shipping zone schema."""
    
    zone_name: str = Field(..., description="Zone name")
    zone_code: str = Field(..., description="Zone code")
    postal_codes: List[str] = Field(default_factory=list, description="Postal codes in zone")
    cities: List[str] = Field(default_factory=list, description="Cities in zone")
    prefectures: List[str] = Field(default_factory=list, description="Prefectures in zone")
    base_rate: float = Field(..., ge=0, description="Base rate for zone")
    per_kg_rate: float = Field(..., ge=0, description="Rate per kg")
    minimum_charge: Optional[float] = Field(None, ge=0, description="Minimum charge")
    standard_delivery_days: int = Field(3, ge=0, description="Standard delivery days")
    express_delivery_days: int = Field(1, ge=0, description="Express delivery days")
    same_day_available: bool = Field(False, description="Same day delivery available")
    max_weight_kg: Optional[float] = Field(None, ge=0, description="Maximum weight")
    restricted_items: List[str] = Field(default_factory=list, description="Restricted items")
    special_requirements: Optional[Dict[str, Any]] = Field(None, description="Special requirements")
    is_active: bool = Field(True, description="Is zone active")


class ShippingZoneCreate(ShippingZoneBase):
    """Schema for creating shipping zone."""
    pass


class ShippingZoneResponse(ShippingZoneBase):
    """Schema for shipping zone response."""
    
    id: int
    organization_id: str
    zone_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShippingRuleBase(BaseModel):
    """Base shipping rule schema."""
    
    rule_name: str = Field(..., description="Rule name")
    rule_description: Optional[str] = Field(None, description="Rule description")
    rule_type: str = Field(..., description="Rule type")
    conditions: Dict[str, Any] = Field(..., description="Rule conditions")
    actions: Dict[str, Any] = Field(..., description="Rule actions")
    priority: int = Field(100, description="Rule priority")
    is_active: bool = Field(True, description="Is rule active")


class ShippingRuleCreate(ShippingRuleBase):
    """Schema for creating shipping rule."""
    
    @validator('rule_type')
    def validate_rule_type(cls, v):
        valid_types = ['carrier_selection', 'rate_override', 'notification', 'routing']
        if v not in valid_types:
            raise ValueError(f'Rule type must be one of: {", ".join(valid_types)}')
        return v


class ShippingRuleResponse(ShippingRuleBase):
    """Schema for shipping rule response."""
    
    id: int
    organization_id: str
    execution_count: int
    success_count: int
    last_executed: Optional[datetime]
    rule_data: Optional[Dict[str, Any]]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BulkShipmentAction(BaseModel):
    """Schema for bulk shipment actions."""
    
    shipment_ids: List[str] = Field(..., description="List of shipment IDs")
    action: str = Field(..., description="Action to perform")
    action_data: Optional[Dict[str, Any]] = Field(None, description="Action data")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['cancel', 'update_status', 'generate_labels', 'send_notifications']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {", ".join(valid_actions)}')
        return v
    
    @validator('shipment_ids')
    def validate_shipment_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one shipment ID must be provided')
        if len(v) > 100:
            raise ValueError('Cannot perform bulk action on more than 100 shipments')
        return v


class ShippingMetrics(BaseModel):
    """Schema for shipping metrics."""
    
    avg_delivery_time_hours: float = Field(..., description="Average delivery time in hours")
    on_time_delivery_rate: float = Field(..., description="On-time delivery rate percentage")
    cost_per_shipment: float = Field(..., description="Average cost per shipment")
    carrier_performance: Dict[str, float] = Field(..., description="Carrier performance scores")
    damage_rate: float = Field(..., description="Damage rate percentage")
    return_rate: float = Field(..., description="Return rate percentage")
    
    total_shipped_weight: float = Field(..., description="Total shipped weight")
    total_shipping_cost: float = Field(..., description="Total shipping cost")
    total_shipments: int = Field(..., description="Total number of shipments")
    
    status_transition_counts: Dict[str, int] = Field(..., description="Status transition counts")
    popular_routes: List[Dict[str, Any]] = Field(..., description="Popular shipping routes")


class ShippingPerformance(BaseModel):
    """Schema for shipping performance metrics."""
    
    period: str = Field(..., description="Performance period")
    shipment_volume: int = Field(..., description="Number of shipments")
    throughput_rate: float = Field(..., description="Shipments processed per hour")
    avg_processing_time_hours: float = Field(..., description="Average processing time")
    bottleneck_statuses: List[str] = Field(..., description="Statuses causing bottlenecks")
    efficiency_score: float = Field(..., ge=0, le=100, description="Overall efficiency score")
    
    delivery_time_by_method: Dict[str, float] = Field(..., description="Avg delivery time by method")
    carrier_reliability: Dict[str, Any] = Field(..., description="Carrier reliability metrics")
    cost_analysis: Dict[str, Any] = Field(..., description="Cost analysis by various factors")