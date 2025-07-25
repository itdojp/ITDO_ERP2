"""Shipping management service for CC02 v61.0 - Day 6: Shipping Management System."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.shipping_management import (
    Address,
    CarrierConfiguration,
    DeliveryAttempt,
    DeliveryPriority,
    PackageType,
    Shipment,
    ShipmentItem,
    ShipmentStatus,
    ShipmentTracking,
    ShippingCarrier,
    ShippingMethod,
    ShippingNotification,
    ShippingRate,
    ShippingRule,
    ShippingZone,
)
from app.models.user import User
from app.types import OrganizationId, UserId

logger = logging.getLogger(__name__)


class ShippingService:
    """Service for managing shipping operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_shipment(
        self,
        order_id: str,
        from_address_data: Dict[str, Any],
        to_address_data: Dict[str, Any],
        items: List[Dict[str, Any]],
        organization_id: OrganizationId,
        created_by: UserId,
        **kwargs
    ) -> Shipment:
        """Create a new shipment."""
        
        # Create addresses
        from_address = await self._create_address(from_address_data, organization_id, "shipping")
        to_address = await self._create_address(to_address_data, organization_id, "delivery")
        
        # Calculate total weight and dimensions
        total_weight = sum(item.get("weight_kg", 0) for item in items)
        total_value = sum(item.get("total_value", 0) for item in items)
        
        # Determine optimal carrier
        carrier_config = await self._select_optimal_carrier(
            from_postal_code=from_address_data.get("postal_code"),
            to_postal_code=to_address_data.get("postal_code"),
            weight_kg=total_weight,
            dimensions_cm=kwargs.get("dimensions_cm", {"length": 30, "width": 20, "height": 10}),
            organization_id=organization_id,
            priority=kwargs.get("delivery_priority", DeliveryPriority.NORMAL),
            shipping_method=kwargs.get("shipping_method", ShippingMethod.STANDARD)
        )
        
        # Generate shipment ID
        shipment_id = await self._generate_shipment_id(organization_id)
        
        # Create shipment
        shipment = Shipment(
            shipment_id=shipment_id,
            organization_id=organization_id,
            order_id=order_id,
            carrier_config_id=carrier_config.id,
            from_address_id=from_address.id,
            to_address_id=to_address.id,
            shipping_method=kwargs.get("shipping_method", ShippingMethod.STANDARD),
            package_type=kwargs.get("package_type", PackageType.BOX),
            delivery_priority=kwargs.get("delivery_priority", DeliveryPriority.NORMAL),
            weight_kg=total_weight,
            dimensions_cm=kwargs.get("dimensions_cm", {"length": 30, "width": 20, "height": 10}),
            declared_value=total_value,
            customer_reference=kwargs.get("customer_reference"),
            delivery_instructions=kwargs.get("delivery_instructions"),
            requires_signature=kwargs.get("requires_signature", False),
            is_fragile=kwargs.get("is_fragile", False),
            is_hazardous=kwargs.get("is_hazardous", False),
            special_instructions=kwargs.get("special_instructions"),
            delivery_date_requested=kwargs.get("delivery_date_requested"),
            created_by=created_by
        )
        
        self.db.add(shipment)
        await self.db.commit()
        await self.db.refresh(shipment)
        
        # Create shipment items
        for item_data in items:
            await self._create_shipment_item(shipment.id, item_data)
        
        # Calculate shipping rates
        await self._calculate_shipping_rates(shipment)
        
        # Create initial tracking entry
        await self._create_initial_tracking(shipment)
        
        logger.info(f"Created shipment {shipment_id} for order {order_id}")
        return shipment

    async def get_shipping_rates(
        self,
        from_postal_code: str,
        to_postal_code: str,
        weight_kg: float,
        dimensions_cm: Dict[str, float],
        organization_id: OrganizationId,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get shipping rates from multiple carriers."""
        
        # Get available carriers
        carriers = await self._get_available_carriers(organization_id)
        rates = []
        
        for carrier in carriers:
            try:
                rate = await self._calculate_carrier_rate(
                    carrier=carrier,
                    from_postal_code=from_postal_code,
                    to_postal_code=to_postal_code,
                    weight_kg=weight_kg,
                    dimensions_cm=dimensions_cm,
                    shipping_method=kwargs.get("shipping_method", ShippingMethod.STANDARD)
                )
                
                if rate:
                    rates.append({
                        "carrier": carrier.carrier.value,
                        "carrier_name": carrier.carrier_name,
                        "service_type": kwargs.get("shipping_method", ShippingMethod.STANDARD).value,
                        "total_rate": rate["total_rate"],
                        "currency": rate["currency"],
                        "estimated_days": rate["estimated_days"],
                        "estimated_delivery": rate["estimated_delivery"],
                        "service_features": rate["service_features"]
                    })
            except Exception as e:
                logger.warning(f"Failed to get rate from {carrier.carrier}: {str(e)}")
                continue
        
        # Sort rates by total cost
        rates.sort(key=lambda x: x["total_rate"])
        
        return rates

    async def track_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """Get shipment tracking information."""
        
        shipment = await self._get_shipment_by_id(shipment_id)
        if not shipment:
            raise ValueError(f"Shipment {shipment_id} not found")
        
        # Get latest tracking events
        result = await self.db.execute(
            select(ShipmentTracking)
            .where(ShipmentTracking.shipment_id == shipment.id)
            .order_by(ShipmentTracking.event_timestamp.desc())
        )
        tracking_events = list(result.scalars().all())
        
        # Format tracking response
        tracking_data = {
            "shipment_id": shipment.shipment_id,
            "tracking_number": shipment.carrier_tracking_number,
            "current_status": shipment.current_status.value,
            "estimated_delivery": shipment.estimated_delivery,
            "actual_delivery": shipment.actual_delivery,
            "events": [
                {
                    "timestamp": event.event_timestamp,
                    "status": event.status.value,
                    "description": event.status_description,
                    "location": event.location_name,
                    "city": event.city,
                    "country": event.country_code
                }
                for event in tracking_events
            ],
            "delivery_attempts": len(shipment.delivery_attempts),
            "is_delivered": shipment.current_status == ShipmentStatus.DELIVERED
        }
        
        return tracking_data

    async def update_shipment_status(
        self,
        shipment_id: str,
        status: ShipmentStatus,
        location: Optional[str] = None,
        notes: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Update shipment status with tracking event."""
        
        shipment = await self._get_shipment_by_id(shipment_id)
        if not shipment:
            return False
        
        # Update shipment status
        previous_status = shipment.current_status
        shipment.current_status = status
        shipment.last_status_update = datetime.now()
        
        # Update status history
        history = shipment.status_history or []
        history.append({
            "status": status.value,
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "notes": notes,
            "previous_status": previous_status.value
        })
        shipment.status_history = history
        
        # Create tracking event
        tracking_event = ShipmentTracking(
            shipment_id=shipment.id,
            tracking_number=shipment.carrier_tracking_number or shipment.shipment_id,
            status=status,
            status_description=notes or f"Status updated to {status.value}",
            event_timestamp=datetime.now(),
            event_type="status_update",
            location_name=location,
            data_source="internal"
        )
        
        self.db.add(tracking_event)
        
        # Handle special status updates
        if status == ShipmentStatus.DELIVERED:
            shipment.actual_delivery = datetime.now()
            # Send delivery notification
            await self._send_delivery_notification(shipment)
        elif status == ShipmentStatus.FAILED_DELIVERY:
            # Create delivery attempt record
            await self._record_delivery_attempt(shipment, False, notes)
        
        await self.db.commit()
        
        logger.info(f"Updated shipment {shipment_id} status to {status}")
        return True

    async def cancel_shipment(
        self,
        shipment_id: str,
        reason: str,
        cancelled_by: UserId
    ) -> bool:
        """Cancel a shipment."""
        
        shipment = await self._get_shipment_by_id(shipment_id)
        if not shipment:
            return False
        
        if shipment.current_status in [ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED]:
            return False
        
        # Update status to cancelled
        return await self.update_shipment_status(
            shipment_id=shipment_id,
            status=ShipmentStatus.CANCELLED,
            notes=f"Cancelled by user {cancelled_by}: {reason}"
        )

    async def get_shipments_by_status(
        self,
        organization_id: OrganizationId,
        status: ShipmentStatus,
        limit: int = 100
    ) -> List[Shipment]:
        """Get shipments by status."""
        
        result = await self.db.execute(
            select(Shipment)
            .options(
                selectinload(Shipment.from_address),
                selectinload(Shipment.to_address),
                selectinload(Shipment.carrier_config),
                selectinload(Shipment.items)
            )
            .where(
                and_(
                    Shipment.organization_id == organization_id,
                    Shipment.current_status == status
                )
            )
            .order_by(Shipment.created_at.desc())
            .limit(limit)
        )
        
        return list(result.scalars().all())

    async def get_shipping_analytics(
        self,
        organization_id: OrganizationId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get shipping analytics."""
        
        filters = [Shipment.organization_id == organization_id]
        if start_date:
            filters.append(Shipment.created_at >= start_date)
        if end_date:
            filters.append(Shipment.created_at <= end_date)
        
        # Get all shipments in period
        result = await self.db.execute(
            select(Shipment)
            .where(and_(*filters))
        )
        shipments = list(result.scalars().all())
        
        if not shipments:
            return {
                "total_shipments": 0,
                "status_distribution": {},
                "carrier_distribution": {},
                "shipping_costs": {"total": 0, "average": 0},
                "delivery_performance": {"on_time_rate": 0, "average_delivery_days": 0}
            }
        
        # Status distribution
        status_dist = {}
        for shipment in shipments:
            status = shipment.current_status.value
            status_dist[status] = status_dist.get(status, 0) + 1
        
        # Carrier distribution
        carrier_dist = {}
        for shipment in shipments:
            if shipment.carrier_config:
                carrier = shipment.carrier_config.carrier.value
                carrier_dist[carrier] = carrier_dist.get(carrier, 0) + 1
        
        # Shipping costs
        costs = [s.total_cost for s in shipments if s.total_cost]
        total_cost = sum(costs) if costs else 0
        avg_cost = total_cost / len(costs) if costs else 0
        
        # Delivery performance
        delivered_shipments = [s for s in shipments if s.current_status == ShipmentStatus.DELIVERED]
        on_time_count = 0
        delivery_days = []
        
        for shipment in delivered_shipments:
            if shipment.actual_delivery and shipment.estimated_delivery:
                if shipment.actual_delivery <= shipment.estimated_delivery:
                    on_time_count += 1
                
                days = (shipment.actual_delivery - shipment.created_at).days
                delivery_days.append(days)
        
        on_time_rate = (on_time_count / len(delivered_shipments) * 100) if delivered_shipments else 0
        avg_delivery_days = sum(delivery_days) / len(delivery_days) if delivery_days else 0
        
        return {
            "total_shipments": len(shipments),
            "status_distribution": status_dist,
            "carrier_distribution": carrier_dist,
            "shipping_costs": {
                "total": total_cost,
                "average": avg_cost
            },
            "delivery_performance": {
                "on_time_rate": round(on_time_rate, 2),
                "average_delivery_days": round(avg_delivery_days, 1)
            }
        }

    # Private helper methods

    async def _create_address(
        self,
        address_data: Dict[str, Any],
        organization_id: OrganizationId,
        address_type: str
    ) -> Address:
        """Create a shipping address."""
        
        address = Address(
            organization_id=organization_id,
            address_type=address_type,
            company_name=address_data.get("company_name"),
            contact_name=address_data["contact_name"],
            address_line_1=address_data["address_line_1"],
            address_line_2=address_data.get("address_line_2"),
            city=address_data["city"],
            state_province=address_data.get("state_province"),
            postal_code=address_data["postal_code"],
            country_code=address_data.get("country_code", "JP"),
            phone=address_data.get("phone"),
            email=address_data.get("email")
        )
        
        self.db.add(address)
        await self.db.commit()
        await self.db.refresh(address)
        
        return address

    async def _create_shipment_item(self, shipment_id: int, item_data: Dict[str, Any]) -> ShipmentItem:
        """Create a shipment item."""
        
        item = ShipmentItem(
            shipment_id=shipment_id,
            item_name=item_data["item_name"],
            item_description=item_data.get("item_description"),
            sku=item_data.get("sku"),
            quantity=item_data.get("quantity", 1),
            weight_kg=item_data["weight_kg"],
            dimensions_cm=item_data.get("dimensions_cm"),
            unit_value=item_data["unit_value"],
            total_value=item_data["total_value"],
            currency=item_data.get("currency", "JPY"),
            hs_code=item_data.get("hs_code"),
            country_of_origin=item_data.get("country_of_origin"),
            material=item_data.get("material"),
            is_fragile=item_data.get("is_fragile", False),
            is_hazardous=item_data.get("is_hazardous", False)
        )
        
        self.db.add(item)
        await self.db.commit()
        
        return item

    async def _select_optimal_carrier(
        self,
        from_postal_code: str,
        to_postal_code: str,
        weight_kg: float,
        dimensions_cm: Dict[str, float],
        organization_id: OrganizationId,
        priority: DeliveryPriority,
        shipping_method: ShippingMethod
    ) -> CarrierConfiguration:
        """Select the optimal carrier based on requirements."""
        
        # Get available carriers
        carriers = await self._get_available_carriers(organization_id)
        
        if not carriers:
            raise ValueError("No active carriers configured")
        
        # Apply business rules
        rules = await self._get_shipping_rules(organization_id, "carrier_selection")
        
        best_carrier = None
        best_score = 0
        
        for carrier in carriers:
            score = await self._calculate_carrier_score(
                carrier=carrier,
                from_postal_code=from_postal_code,
                to_postal_code=to_postal_code,
                weight_kg=weight_kg,
                dimensions_cm=dimensions_cm,
                priority=priority,
                shipping_method=shipping_method,
                rules=rules
            )
            
            if score > best_score:
                best_score = score
                best_carrier = carrier
        
        return best_carrier or carriers[0]

    async def _get_available_carriers(self, organization_id: OrganizationId) -> List[CarrierConfiguration]:
        """Get available carrier configurations."""
        
        result = await self.db.execute(
            select(CarrierConfiguration)
            .where(
                and_(
                    CarrierConfiguration.organization_id == organization_id,
                    CarrierConfiguration.is_active == True
                )
            )
            .order_by(CarrierConfiguration.is_default.desc())
        )
        
        return list(result.scalars().all())

    async def _calculate_carrier_rate(
        self,
        carrier: CarrierConfiguration,
        from_postal_code: str,
        to_postal_code: str,
        weight_kg: float,
        dimensions_cm: Dict[str, float],
        shipping_method: ShippingMethod
    ) -> Optional[Dict[str, Any]]:
        """Calculate shipping rate for a specific carrier."""
        
        # Check carrier limits
        if carrier.max_weight_kg and weight_kg > carrier.max_weight_kg:
            return None
        
        # Calculate base rate
        base_rate = carrier.base_rate
        weight_charge = weight_kg * carrier.weight_rate
        
        # Calculate distance-based charge (simplified)
        distance_charge = 0  # Would integrate with mapping service
        
        # Calculate dimensional weight if applicable
        dim_weight = self._calculate_dimensional_weight(dimensions_cm)
        billable_weight = max(weight_kg, dim_weight)
        
        # Apply shipping method multiplier
        method_multipliers = {
            ShippingMethod.STANDARD: 1.0,
            ShippingMethod.EXPRESS: 1.5,
            ShippingMethod.OVERNIGHT: 2.0,
            ShippingMethod.SAME_DAY: 3.0
        }
        multiplier = method_multipliers.get(shipping_method, 1.0)
        
        total_rate = (base_rate + (billable_weight * carrier.weight_rate) + distance_charge) * multiplier
        
        # Estimate delivery time
        base_days = {
            ShippingMethod.STANDARD: 3,
            ShippingMethod.EXPRESS: 1,
            ShippingMethod.OVERNIGHT: 1,
            ShippingMethod.SAME_DAY: 0
        }
        estimated_days = base_days.get(shipping_method, 3)
        estimated_delivery = datetime.now() + timedelta(days=estimated_days)
        
        return {
            "total_rate": round(total_rate, 2),
            "currency": "JPY",
            "estimated_days": estimated_days,
            "estimated_delivery": estimated_delivery,
            "service_features": self._get_service_features(carrier, shipping_method)
        }

    def _calculate_dimensional_weight(self, dimensions_cm: Dict[str, float]) -> float:
        """Calculate dimensional weight."""
        
        length = dimensions_cm.get("length", 0)
        width = dimensions_cm.get("width", 0)
        height = dimensions_cm.get("height", 0)
        
        # Standard dimensional weight divisor for Japan (5000)
        dim_weight = (length * width * height) / 5000
        
        return max(dim_weight, 0)

    def _get_service_features(self, carrier: CarrierConfiguration, method: ShippingMethod) -> List[str]:
        """Get service features for carrier and method."""
        
        features = []
        
        if carrier.carrier == ShippingCarrier.YAMATO:
            features.extend(["tracking", "signature_required", "insurance"])
            if method == ShippingMethod.EXPRESS:
                features.append("time_definite")
        elif carrier.carrier == ShippingCarrier.SAGAWA:
            features.extend(["tracking", "delivery_confirmation"])
            if method in [ShippingMethod.EXPRESS, ShippingMethod.OVERNIGHT]:
                features.append("priority_handling")
        elif carrier.carrier == ShippingCarrier.JAPAN_POST:
            features.extend(["tracking", "postal_network"])
            
        return features

    async def _calculate_carrier_score(
        self,
        carrier: CarrierConfiguration,
        from_postal_code: str,
        to_postal_code: str,
        weight_kg: float,
        dimensions_cm: Dict[str, float],
        priority: DeliveryPriority,
        shipping_method: ShippingMethod,
        rules: List[ShippingRule]
    ) -> float:
        """Calculate carrier selection score."""
        
        score = 50.0  # Base score
        
        # Rate competitiveness (40% weight)
        rate_data = await self._calculate_carrier_rate(
            carrier, from_postal_code, to_postal_code, weight_kg, dimensions_cm, shipping_method
        )
        if rate_data:
            # Lower cost = higher score (simplified)
            cost_score = max(0, 100 - (rate_data["total_rate"] / 100))
            score += cost_score * 0.4
        
        # Service capability (30% weight)
        service_score = len(self._get_service_features(carrier, shipping_method)) * 10
        score += min(service_score, 30)
        
        # Priority alignment (20% weight)
        if priority == DeliveryPriority.URGENT and shipping_method in [ShippingMethod.EXPRESS, ShippingMethod.OVERNIGHT]:
            score += 20
        elif priority == DeliveryPriority.NORMAL and shipping_method == ShippingMethod.STANDARD:
            score += 15
        
        # Default carrier bonus (10% weight)
        if carrier.is_default:
            score += 10
        
        return score

    async def _get_shipping_rules(self, organization_id: OrganizationId, rule_type: str) -> List[ShippingRule]:
        """Get shipping rules by type."""
        
        result = await self.db.execute(
            select(ShippingRule)
            .where(
                and_(
                    ShippingRule.organization_id == organization_id,
                    ShippingRule.rule_type == rule_type,
                    ShippingRule.is_active == True
                )
            )
            .order_by(ShippingRule.priority.desc())
        )
        
        return list(result.scalars().all())

    async def _generate_shipment_id(self, organization_id: OrganizationId) -> str:
        """Generate unique shipment ID."""
        
        # Simple implementation - in production would use more sophisticated logic
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        org_prefix = organization_id[:3].upper()
        
        return f"SH-{org_prefix}-{timestamp}"

    async def _get_shipment_by_id(self, shipment_id: str) -> Optional[Shipment]:
        """Get shipment by ID."""
        
        result = await self.db.execute(
            select(Shipment)
            .options(
                selectinload(Shipment.from_address),
                selectinload(Shipment.to_address),
                selectinload(Shipment.carrier_config),
                selectinload(Shipment.items),
                selectinload(Shipment.tracking_events),
                selectinload(Shipment.delivery_attempts)
            )
            .where(Shipment.shipment_id == shipment_id)
        )
        
        return result.scalar_one_or_none()

    async def _calculate_shipping_rates(self, shipment: Shipment) -> None:
        """Calculate and store shipping rates."""
        
        rate_data = await self._calculate_carrier_rate(
            carrier=shipment.carrier_config,
            from_postal_code=shipment.from_address.postal_code,
            to_postal_code=shipment.to_address.postal_code,
            weight_kg=shipment.weight_kg,
            dimensions_cm=shipment.dimensions_cm,
            shipping_method=shipment.shipping_method
        )
        
        if rate_data:
            shipment.shipping_cost = rate_data["total_rate"]
            shipment.total_cost = rate_data["total_rate"]
            shipment.estimated_delivery = rate_data["estimated_delivery"]
            
            await self.db.commit()

    async def _create_initial_tracking(self, shipment: Shipment) -> None:
        """Create initial tracking entry."""
        
        tracking_event = ShipmentTracking(
            shipment_id=shipment.id,
            tracking_number=shipment.shipment_id,
            status=ShipmentStatus.DRAFT,
            status_description="Shipment created",
            event_timestamp=datetime.now(),
            event_type="created",
            data_source="internal"
        )
        
        self.db.add(tracking_event)
        await self.db.commit()

    async def _send_delivery_notification(self, shipment: Shipment) -> None:
        """Send delivery notification."""
        
        notification = ShippingNotification(
            shipment_id=shipment.id,
            notification_type="delivery_confirmation",
            notification_method="email",
            recipient_email=shipment.to_address.email,
            subject=f"Package Delivered - {shipment.shipment_id}",
            message_body=f"Your package {shipment.shipment_id} has been delivered successfully."
        )
        
        self.db.add(notification)
        await self.db.commit()

    async def _record_delivery_attempt(self, shipment: Shipment, successful: bool, notes: str) -> None:
        """Record delivery attempt."""
        
        attempt_count = len(shipment.delivery_attempts) + 1
        
        attempt = DeliveryAttempt(
            shipment_id=shipment.id,
            attempt_number=attempt_count,
            attempt_date=datetime.now(),
            delivery_status="delivered" if successful else "failed",
            failure_reason=notes if not successful else None,
            next_attempt_scheduled=datetime.now() + timedelta(days=1) if not successful else None
        )
        
        self.db.add(attempt)
        await self.db.commit()