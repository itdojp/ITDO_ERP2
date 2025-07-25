"""Shipping management API endpoints for CC02 v61.0 - Day 6: Shipping Management System."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.shipping_management import (
    CarrierConfiguration,
    Shipment,
    ShipmentStatus,
    ShippingCarrier,
    ShippingMethod,
)
from app.models.user import User
from app.schemas.shipping import (
    AddressCreate,
    CarrierConfigurationCreate,
    CarrierConfigurationResponse,
    ShipmentCreate,
    ShipmentItemCreate,
    ShipmentResponse,
    ShipmentSearch,
    ShipmentStatusUpdate,
    ShipmentTrackingResponse,
    ShippingAnalytics,
    ShippingRateRequest,
    ShippingRateResponse,
)
from app.services.shipping_service import ShippingService

router = APIRouter(prefix="/shipping", tags=["Shipping Management"])


@router.post("/carriers", response_model=CarrierConfigurationResponse)
async def create_carrier_configuration(
    carrier_data: CarrierConfigurationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CarrierConfigurationResponse:
    """Create a new carrier configuration."""
    
    carrier_config = CarrierConfiguration(
        organization_id=current_user.organization_id,
        carrier=carrier_data.carrier,
        api_endpoint=carrier_data.api_endpoint,
        api_key=carrier_data.api_key,
        api_secret=carrier_data.api_secret,
        account_number=carrier_data.account_number,
        carrier_name=carrier_data.carrier_name,
        is_active=carrier_data.is_active,
        is_default=carrier_data.is_default,
        supported_methods=carrier_data.supported_methods,
        base_rate=carrier_data.base_rate,
        weight_rate=carrier_data.weight_rate,
        distance_rate=carrier_data.distance_rate,
        max_weight_kg=carrier_data.max_weight_kg,
        max_dimensions_cm=carrier_data.max_dimensions_cm,
        service_areas=carrier_data.service_areas,
        business_rules=carrier_data.business_rules,
        pricing_rules=carrier_data.pricing_rules
    )
    
    db.add(carrier_config)
    await db.commit()
    await db.refresh(carrier_config)
    
    return CarrierConfigurationResponse.from_orm(carrier_config)


@router.get("/carriers", response_model=List[CarrierConfigurationResponse])
async def get_carrier_configurations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CarrierConfigurationResponse]:
    """Get all carrier configurations for the organization."""
    
    result = await db.execute(
        select(CarrierConfiguration)
        .where(CarrierConfiguration.organization_id == current_user.organization_id)
        .order_by(CarrierConfiguration.is_default.desc(), CarrierConfiguration.carrier_name)
    )
    carriers = list(result.scalars().all())
    
    return [CarrierConfigurationResponse.from_orm(carrier) for carrier in carriers]


@router.put("/carriers/{carrier_id}", response_model=CarrierConfigurationResponse)
async def update_carrier_configuration(
    carrier_id: int,
    carrier_data: CarrierConfigurationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CarrierConfigurationResponse:
    """Update a carrier configuration."""
    
    result = await db.execute(
        select(CarrierConfiguration)
        .where(
            and_(
                CarrierConfiguration.id == carrier_id,
                CarrierConfiguration.organization_id == current_user.organization_id
            )
        )
    )
    carrier = result.scalar_one_or_none()
    
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrier configuration not found"
        )
    
    # Update carrier configuration
    for field, value in carrier_data.dict(exclude_unset=True).items():
        setattr(carrier, field, value)
    
    await db.commit()
    await db.refresh(carrier)
    
    return CarrierConfigurationResponse.from_orm(carrier)


@router.delete("/carriers/{carrier_id}")
async def delete_carrier_configuration(
    carrier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Delete a carrier configuration."""
    
    result = await db.execute(
        select(CarrierConfiguration)
        .where(
            and_(
                CarrierConfiguration.id == carrier_id,
                CarrierConfiguration.organization_id == current_user.organization_id
            )
        )
    )
    carrier = result.scalar_one_or_none()
    
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrier configuration not found"
        )
    
    await db.delete(carrier)
    await db.commit()
    
    return {"message": "Carrier configuration deleted successfully"}


@router.post("/rates", response_model=List[ShippingRateResponse])
async def get_shipping_rates(
    rate_request: ShippingRateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ShippingRateResponse]:
    """Get shipping rates from multiple carriers."""
    
    service = ShippingService(db)
    
    rates = await service.get_shipping_rates(
        from_postal_code=rate_request.from_postal_code,
        to_postal_code=rate_request.to_postal_code,
        weight_kg=rate_request.weight_kg,
        dimensions_cm=rate_request.dimensions_cm,
        organization_id=current_user.organization_id,
        shipping_method=rate_request.shipping_method,
        package_type=rate_request.package_type,
        declared_value=rate_request.declared_value
    )
    
    return [ShippingRateResponse(**rate) for rate in rates]


@router.post("/shipments", response_model=ShipmentResponse)
async def create_shipment(
    shipment_data: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentResponse:
    """Create a new shipment."""
    
    service = ShippingService(db)
    
    # Convert address data to dict format
    from_address_dict = shipment_data.from_address.dict()
    to_address_dict = shipment_data.to_address.dict()
    items_dict = [item.dict() for item in shipment_data.items]
    
    shipment = await service.create_shipment(
        order_id=shipment_data.order_id,
        from_address_data=from_address_dict,
        to_address_data=to_address_dict,
        items=items_dict,
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        customer_reference=shipment_data.customer_reference,
        shipping_method=shipment_data.shipping_method,
        package_type=shipment_data.package_type,
        delivery_priority=shipment_data.delivery_priority,
        dimensions_cm=shipment_data.dimensions_cm,
        delivery_instructions=shipment_data.delivery_instructions,
        requires_signature=shipment_data.requires_signature,
        is_fragile=shipment_data.is_fragile,
        is_hazardous=shipment_data.is_hazardous,
        special_instructions=shipment_data.special_instructions,
        delivery_date_requested=shipment_data.delivery_date_requested
    )
    
    return ShipmentResponse.from_orm(shipment)


@router.get("/shipments/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(
    shipment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentResponse:
    """Get shipment by ID."""
    
    result = await db.execute(
        select(Shipment)
        .options(
            selectinload(Shipment.from_address),
            selectinload(Shipment.to_address),
            selectinload(Shipment.return_address),
            selectinload(Shipment.carrier_config),
            selectinload(Shipment.items),
            selectinload(Shipment.tracking_events),
            selectinload(Shipment.delivery_attempts)
        )
        .where(
            and_(
                Shipment.shipment_id == shipment_id,
                Shipment.organization_id == current_user.organization_id
            )
        )
    )
    shipment = result.scalar_one_or_none()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    return ShipmentResponse.from_orm(shipment)


@router.get("/shipments", response_model=List[ShipmentResponse])
async def search_shipments(
    search: ShipmentSearch = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ShipmentResponse]:
    """Search shipments with filters."""
    
    # Build filter conditions
    filters = [Shipment.organization_id == current_user.organization_id]
    
    if search.status:
        filters.append(Shipment.current_status.in_(search.status))
    
    if search.carrier:
        # Join with carrier configuration to filter by carrier
        pass  # Would need to modify query to join with CarrierConfiguration
    
    if search.order_id:
        filters.append(Shipment.order_id == search.order_id)
    
    if search.tracking_number:
        filters.append(Shipment.carrier_tracking_number.ilike(f"%{search.tracking_number}%"))
    
    if search.date_from:
        filters.append(Shipment.created_at >= search.date_from)
    
    if search.date_to:
        filters.append(Shipment.created_at <= search.date_to)
    
    # Execute query
    result = await db.execute(
        select(Shipment)
        .options(
            selectinload(Shipment.from_address),
            selectinload(Shipment.to_address),
            selectinload(Shipment.carrier_config),
            selectinload(Shipment.items)
        )
        .where(and_(*filters))
        .order_by(Shipment.created_at.desc())
        .limit(search.limit)
        .offset(search.offset)
    )
    shipments = list(result.scalars().all())
    
    return [ShipmentResponse.from_orm(shipment) for shipment in shipments]


@router.get("/shipments/{shipment_id}/tracking", response_model=ShipmentTrackingResponse)
async def track_shipment(
    shipment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentTrackingResponse:
    """Get shipment tracking information."""
    
    # Verify shipment belongs to organization
    result = await db.execute(
        select(Shipment)
        .where(
            and_(
                Shipment.shipment_id == shipment_id,
                Shipment.organization_id == current_user.organization_id
            )
        )
    )
    shipment = result.scalar_one_or_none()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    service = ShippingService(db)
    tracking_data = await service.track_shipment(shipment_id)
    
    return ShipmentTrackingResponse(**tracking_data)


@router.put("/shipments/{shipment_id}/status", response_model=Dict[str, Any])
async def update_shipment_status(
    shipment_id: str,
    status_update: ShipmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update shipment status."""
    
    # Verify shipment belongs to organization
    result = await db.execute(
        select(Shipment)
        .where(
            and_(
                Shipment.shipment_id == shipment_id,
                Shipment.organization_id == current_user.organization_id
            )
        )
    )
    shipment = result.scalar_one_or_none()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    service = ShippingService(db)
    success = await service.update_shipment_status(
        shipment_id=shipment_id,
        status=status_update.status,
        location=status_update.location,
        notes=status_update.notes
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update shipment status"
        )
    
    return {
        "success": True,
        "message": f"Shipment status updated to {status_update.status.value}",
        "updated_by": str(current_user.id),
        "timestamp": datetime.now().isoformat()
    }


@router.delete("/shipments/{shipment_id}/cancel", response_model=Dict[str, Any])
async def cancel_shipment(
    shipment_id: str,
    reason: str = Query(..., description="Reason for cancellation"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Cancel a shipment."""
    
    # Verify shipment belongs to organization
    result = await db.execute(
        select(Shipment)
        .where(
            and_(
                Shipment.shipment_id == shipment_id,
                Shipment.organization_id == current_user.organization_id
            )
        )
    )
    shipment = result.scalar_one_or_none()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    service = ShippingService(db)
    success = await service.cancel_shipment(
        shipment_id=shipment_id,
        reason=reason,
        cancelled_by=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel shipment"
        )
    
    return {
        "success": True,
        "message": "Shipment cancelled successfully",
        "reason": reason,
        "cancelled_by": str(current_user.id),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/shipments/status/{status}", response_model=List[ShipmentResponse])
async def get_shipments_by_status(
    status: ShipmentStatus,
    limit: int = Query(100, ge=1, le=1000, description="Number of shipments to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ShipmentResponse]:
    """Get shipments by status."""
    
    service = ShippingService(db)
    shipments = await service.get_shipments_by_status(
        organization_id=current_user.organization_id,
        status=status,
        limit=limit
    )
    
    return [ShipmentResponse.from_orm(shipment) for shipment in shipments]


@router.get("/analytics", response_model=ShippingAnalytics)
async def get_shipping_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShippingAnalytics:
    """Get shipping analytics."""
    
    service = ShippingService(db)
    analytics = await service.get_shipping_analytics(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return ShippingAnalytics(**analytics)


@router.get("/carriers/available", response_model=List[str])
async def get_available_carriers() -> List[str]:
    """Get list of available shipping carriers."""
    return [carrier.value for carrier in ShippingCarrier]


@router.get("/methods/available", response_model=List[str])
async def get_available_shipping_methods() -> List[str]:
    """Get list of available shipping methods."""
    return [method.value for method in ShippingMethod]


@router.get("/statuses/available", response_model=List[str])
async def get_available_shipment_statuses() -> List[str]:
    """Get list of available shipment statuses."""
    return [status.value for status in ShipmentStatus]


@router.post("/webhook/tracking", response_model=Dict[str, str])
async def handle_tracking_webhook(
    webhook_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Handle tracking webhook from carriers."""
    
    # This would be implemented to handle real carrier webhooks
    # For now, return a placeholder response
    
    tracking_number = webhook_data.get("tracking_number")
    if not tracking_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracking number is required"
        )
    
    # In a real implementation, this would:
    # 1. Validate the webhook signature
    # 2. Parse the carrier-specific data format
    # 3. Update the shipment status and tracking events
    # 4. Send notifications if needed
    
    return {
        "message": "Webhook processed successfully",
        "tracking_number": tracking_number
    }


@router.post("/labels/{shipment_id}/generate", response_model=Dict[str, Any])
async def generate_shipping_label(
    shipment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Generate shipping label for a shipment."""
    
    # Verify shipment belongs to organization
    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.carrier_config))
        .where(
            and_(
                Shipment.shipment_id == shipment_id,
                Shipment.organization_id == current_user.organization_id
            )
        )
    )
    shipment = result.scalar_one_or_none()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    # In a real implementation, this would:
    # 1. Call the carrier's API to generate a shipping label
    # 2. Store the label URL and tracking number
    # 3. Update shipment status to "label_created"
    
    # For now, simulate label generation
    label_url = f"https://labels.example.com/{shipment_id}.pdf"
    tracking_number = f"TN{shipment_id[-8:]}"
    
    # Update shipment with label information
    shipment.shipping_label_url = label_url
    shipment.carrier_tracking_number = tracking_number
    shipment.current_status = ShipmentStatus.LABEL_CREATED
    
    await db.commit()
    
    return {
        "success": True,
        "label_url": label_url,
        "tracking_number": tracking_number,
        "message": "Shipping label generated successfully"
    }