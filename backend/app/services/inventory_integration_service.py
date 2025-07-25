"""
Inventory Integration Service for CC02 v62.0
Comprehensive inventory management service with real-time tracking, auto-ordering, analytics, and predictions
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BusinessLogicError, ValidationError
from app.models.inventory import InventoryItem, StockMovement, Warehouse, MovementType
from app.models.inventory_integration import (
    AutoOrder,
    AutoOrderRule,
    AutoOrderStatus,
    InventoryAnalytics,
    InventoryPrediction,
    PredictionModel,
    RealtimeInventoryAlert,
    ShippingInventorySync,
    AlertType,
    ShipmentStatus,
)
from app.schemas.inventory_integration import (
    AutoOrderCreate,
    AutoOrderRuleCreate,
    InventoryAnalyticsCreate,
    PredictionModelCreate,
    RealtimeAlertCreate,
    RealtimeInventorySnapshot,
    RealtimeInventoryUpdate,
    ShippingInventorySyncCreate,
)

logger = logging.getLogger(__name__)


class RealtimeInventoryTrackingService:
    """Service for real-time inventory tracking and monitoring."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._websocket_connections: dict[str, Any] = {}
    
    async def get_realtime_snapshot(
        self, 
        product_id: int, 
        warehouse_id: int, 
        organization_id: int
    ) -> RealtimeInventorySnapshot:
        """Get current real-time inventory snapshot."""
        query = select(InventoryItem).where(
            and_(
                InventoryItem.product_id == product_id,
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.organization_id == organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        inventory_item = result.scalar_one_or_none()
        
        if not inventory_item:
            # Create default snapshot for non-existent items
            return RealtimeInventorySnapshot(
                product_id=product_id,
                warehouse_id=warehouse_id,
                current_stock=Decimal(0),
                reserved_stock=Decimal(0),
                available_stock=Decimal(0),
                in_transit_stock=Decimal(0),
                last_movement_at=datetime.utcnow(),
                alerts_count=0
            )
        
        # Count active alerts for this item
        alerts_query = select(func.count(RealtimeInventoryAlert.id)).where(
            and_(
                RealtimeInventoryAlert.inventory_item_id == inventory_item.id,
                RealtimeInventoryAlert.is_active == True,
                RealtimeInventoryAlert.deleted_at.is_(None)
            )
        )
        alerts_result = await self.db.execute(alerts_query)
        alerts_count = alerts_result.scalar() or 0
        
        return RealtimeInventorySnapshot(
            product_id=product_id,
            warehouse_id=warehouse_id,
            current_stock=inventory_item.quantity_on_hand,
            reserved_stock=inventory_item.quantity_reserved,
            available_stock=inventory_item.quantity_available,
            in_transit_stock=inventory_item.quantity_in_transit,
            last_movement_at=inventory_item.updated_at,
            alerts_count=alerts_count
        )
    
    async def process_realtime_update(
        self, 
        update: RealtimeInventoryUpdate, 
        organization_id: int
    ) -> RealtimeInventorySnapshot:
        """Process real-time inventory update and trigger alerts if needed."""
        # Get or create inventory item
        query = select(InventoryItem).where(
            and_(
                InventoryItem.product_id == update.product_id,
                InventoryItem.warehouse_id == update.warehouse_id,
                InventoryItem.organization_id == organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        inventory_item = result.scalar_one_or_none()
        
        if not inventory_item:
            # Create new inventory item
            inventory_item = InventoryItem(
                product_id=update.product_id,
                warehouse_id=update.warehouse_id,
                organization_id=organization_id,
                quantity_on_hand=Decimal(0),
                quantity_reserved=Decimal(0),
                quantity_available=Decimal(0),
                quantity_in_transit=Decimal(0)
            )
            self.db.add(inventory_item)
            await self.db.flush()
        
        # Store previous quantities for stock movement
        previous_quantity = inventory_item.quantity_on_hand
        
        # Apply quantity change based on movement type
        if update.movement_type == MovementType.IN.value:
            inventory_item.quantity_on_hand += update.quantity_change
        elif update.movement_type == MovementType.OUT.value:
            inventory_item.quantity_on_hand -= update.quantity_change
        elif update.movement_type == MovementType.ADJUSTMENT.value:
            inventory_item.quantity_on_hand += update.quantity_change
        
        # Recalculate available quantity
        inventory_item.calculate_available_quantity()
        
        # Update timestamps
        inventory_item.updated_at = update.timestamp
        if update.movement_type == MovementType.IN.value:
            inventory_item.last_received_date = update.timestamp
        elif update.movement_type == MovementType.OUT.value:
            inventory_item.last_issued_date = update.timestamp
        
        # Create stock movement record
        stock_movement = StockMovement(
            transaction_number=f"RT-{update.timestamp.strftime('%Y%m%d%H%M%S')}-{inventory_item.id}",
            inventory_item_id=inventory_item.id,
            product_id=update.product_id,
            warehouse_id=update.warehouse_id,
            organization_id=organization_id,
            movement_type=update.movement_type,
            movement_date=update.timestamp,
            quantity=update.quantity_change,
            quantity_before=previous_quantity,
            quantity_after=inventory_item.quantity_on_hand,
            reason=update.reason,
            reference_id=update.reference_id,
            performed_by=update.user_id,
            created_by=update.user_id
        )
        self.db.add(stock_movement)
        
        # Check for alert conditions
        await self._check_and_create_alerts(inventory_item, organization_id)
        
        await self.db.commit()
        
        # Get updated snapshot
        snapshot = await self.get_realtime_snapshot(
            update.product_id, 
            update.warehouse_id, 
            organization_id
        )
        
        # Broadcast update via WebSocket
        await self._broadcast_inventory_update(snapshot)
        
        return snapshot
    
    async def _check_and_create_alerts(
        self, 
        inventory_item: InventoryItem, 
        organization_id: int
    ) -> None:
        """Check inventory conditions and create alerts if needed."""
        alerts_to_create = []
        
        # Check for low stock
        if inventory_item.is_low_stock:
            alerts_to_create.append(RealtimeAlertCreate(
                alert_type=AlertType.LOW_STOCK.value,
                severity="high",
                title=f"Low Stock Alert - Product {inventory_item.product_id}",
                message=f"Stock level ({inventory_item.quantity_available}) is below minimum threshold ({inventory_item.minimum_level})",
                product_id=inventory_item.product_id,
                warehouse_id=inventory_item.warehouse_id,
                inventory_item_id=inventory_item.id,
                current_value=inventory_item.quantity_available,
                threshold_value=inventory_item.minimum_level,
                context_data={
                    "warehouse_name": inventory_item.warehouse.name if inventory_item.warehouse else None,
                    "product_code": inventory_item.product.code if inventory_item.product else None
                }
            ))
        
        # Check for out of stock
        if inventory_item.quantity_available <= 0:
            alerts_to_create.append(RealtimeAlertCreate(
                alert_type=AlertType.OUT_OF_STOCK.value,
                severity="critical",
                title=f"Out of Stock Alert - Product {inventory_item.product_id}",
                message=f"Product is completely out of stock in warehouse",
                product_id=inventory_item.product_id,
                warehouse_id=inventory_item.warehouse_id,
                inventory_item_id=inventory_item.id,
                current_value=inventory_item.quantity_available,
                threshold_value=Decimal(0),
                context_data={
                    "reserved_stock": str(inventory_item.quantity_reserved),
                    "in_transit": str(inventory_item.quantity_in_transit)
                }
            ))
        
        # Check for reorder point
        if inventory_item.needs_reorder:
            alerts_to_create.append(RealtimeAlertCreate(
                alert_type=AlertType.REORDER_POINT.value,
                severity="medium",
                title=f"Reorder Point Reached - Product {inventory_item.product_id}",
                message=f"Stock level has reached reorder point. Consider placing new order.",
                product_id=inventory_item.product_id,
                warehouse_id=inventory_item.warehouse_id,
                inventory_item_id=inventory_item.id,
                current_value=inventory_item.quantity_available,
                threshold_value=inventory_item.reorder_point,
                auto_resolve_after_hours=24
            ))
        
        # Check for expiry warning
        if inventory_item.is_near_expiry(30):  # 30 days threshold
            alerts_to_create.append(RealtimeAlertCreate(
                alert_type=AlertType.EXPIRY_WARNING.value,
                severity="high",
                title=f"Expiry Warning - Product {inventory_item.product_id}",
                message=f"Product will expire in {inventory_item.days_until_expiry} days",
                product_id=inventory_item.product_id,
                warehouse_id=inventory_item.warehouse_id,
                inventory_item_id=inventory_item.id,
                current_value=Decimal(inventory_item.days_until_expiry or 0),
                threshold_value=Decimal(30),
                context_data={
                    "expiry_date": inventory_item.expiry_date.isoformat() if inventory_item.expiry_date else None,
                    "lot_number": inventory_item.lot_number
                }
            ))
        
        # Create alerts
        for alert_data in alerts_to_create:
            # Check if similar alert already exists and is active
            existing_alert_query = select(RealtimeInventoryAlert).where(
                and_(
                    RealtimeInventoryAlert.alert_type == alert_data.alert_type,
                    RealtimeInventoryAlert.inventory_item_id == inventory_item.id,
                    RealtimeInventoryAlert.is_active == True,
                    RealtimeInventoryAlert.deleted_at.is_(None)
                )
            )
            existing_result = await self.db.execute(existing_alert_query)
            existing_alert = existing_result.scalar_one_or_none()
            
            if not existing_alert:
                alert = RealtimeInventoryAlert(
                    organization_id=organization_id,
                    **alert_data.model_dump()
                )
                self.db.add(alert)
                
                # Broadcast alert via WebSocket
                await self._broadcast_alert(alert)
    
    async def _broadcast_inventory_update(self, snapshot: RealtimeInventorySnapshot) -> None:
        """Broadcast inventory update to connected WebSocket clients."""
        message = {
            "type": "inventory_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": snapshot.model_dump()
        }
        
        # Broadcast to all connected clients (implementation depends on WebSocket manager)
        logger.info(f"Broadcasting inventory update: {message}")
    
    async def _broadcast_alert(self, alert: RealtimeInventoryAlert) -> None:
        """Broadcast alert to connected WebSocket clients."""
        message = {
            "type": "alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "product_id": alert.product_id,
                "warehouse_id": alert.warehouse_id
            }
        }
        
        # Broadcast to all connected clients
        logger.info(f"Broadcasting alert: {message}")


class AutoOrderingService:
    """Service for automatic ordering and replenishment."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_auto_order_rule(
        self, 
        rule_data: AutoOrderRuleCreate, 
        organization_id: int,
        created_by: int
    ) -> AutoOrderRule:
        """Create a new auto order rule."""
        # Validate product and warehouse exist
        warehouse_query = select(Warehouse).where(
            and_(
                Warehouse.id == rule_data.warehouse_id,
                Warehouse.organization_id == organization_id,
                Warehouse.deleted_at.is_(None)
            )
        )
        warehouse_result = await self.db.execute(warehouse_query)
        warehouse = warehouse_result.scalar_one_or_none()
        
        if not warehouse:
            raise ValidationError("Warehouse not found or not accessible")
        
        # Check for existing rule
        existing_rule_query = select(AutoOrderRule).where(
            and_(
                AutoOrderRule.product_id == rule_data.product_id,
                AutoOrderRule.warehouse_id == rule_data.warehouse_id,
                AutoOrderRule.organization_id == organization_id,
                AutoOrderRule.is_active == True,
                AutoOrderRule.deleted_at.is_(None)
            )
        )
        existing_result = await self.db.execute(existing_rule_query)
        existing_rule = existing_result.scalar_one_or_none()
        
        if existing_rule:
            raise BusinessLogicError("Active auto order rule already exists for this product and warehouse")
        
        # Create new rule
        rule = AutoOrderRule(
            organization_id=organization_id,
            created_by=created_by,
            **rule_data.model_dump()
        )
        
        # Set next scheduled check if schedule is enabled
        if rule.schedule_enabled and rule.schedule_frequency_days:
            rule.next_scheduled_check = datetime.utcnow() + timedelta(days=rule.schedule_frequency_days)
        
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        
        return rule
    
    async def check_and_process_auto_orders(self, organization_id: int) -> list[AutoOrder]:
        """Check all active rules and create auto orders where needed."""
        # Get all active auto order rules
        rules_query = select(AutoOrderRule).options(
            selectinload(AutoOrderRule.product),
            selectinload(AutoOrderRule.warehouse)
        ).where(
            and_(
                AutoOrderRule.organization_id == organization_id,
                AutoOrderRule.is_active == True,
                AutoOrderRule.deleted_at.is_(None)
            )
        )
        rules_result = await self.db.execute(rules_query)
        rules = rules_result.scalars().all()
        
        created_orders = []
        
        for rule in rules:
            try:
                # Get current inventory for this product/warehouse
                inventory_query = select(InventoryItem).where(
                    and_(
                        InventoryItem.product_id == rule.product_id,
                        InventoryItem.warehouse_id == rule.warehouse_id,
                        InventoryItem.organization_id == organization_id,
                        InventoryItem.deleted_at.is_(None)
                    )
                )
                inventory_result = await self.db.execute(inventory_query)
                inventory_item = inventory_result.scalar_one_or_none()
                
                if not inventory_item:
                    continue
                
                # Check if reorder is needed
                if rule.is_reorder_needed(inventory_item.quantity_on_hand, inventory_item.quantity_reserved):
                    # Check if there's already a pending order for this rule
                    pending_order_query = select(AutoOrder).where(
                        and_(
                            AutoOrder.order_rule_id == rule.id,
                            AutoOrder.status.in_([
                                AutoOrderStatus.PENDING.value,
                                AutoOrderStatus.PROCESSED.value,
                                AutoOrderStatus.APPROVED.value,
                                AutoOrderStatus.PLACED.value
                            ]),
                            AutoOrder.deleted_at.is_(None)
                        )
                    )
                    pending_result = await self.db.execute(pending_order_query)
                    pending_order = pending_result.scalar_one_or_none()
                    
                    if not pending_order:
                        # Create new auto order
                        order = await self._create_auto_order(rule, inventory_item, organization_id)
                        created_orders.append(order)
                        
                        # Update rule statistics
                        rule.last_order_date = datetime.utcnow()
                        if rule.schedule_enabled and rule.schedule_frequency_days:
                            rule.next_scheduled_check = datetime.utcnow() + timedelta(days=rule.schedule_frequency_days)
                
            except Exception as e:
                logger.error(f"Error processing auto order rule {rule.id}: {str(e)}")
                continue
        
        await self.db.commit()
        return created_orders
    
    async def _create_auto_order(
        self, 
        rule: AutoOrderRule, 
        inventory_item: InventoryItem, 
        organization_id: int
    ) -> AutoOrder:
        """Create an auto order based on rule configuration."""
        # Calculate order quantity
        order_quantity = rule.order_quantity
        
        if rule.use_economic_order_quantity:
            # Calculate EOQ based on historical data (simplified)
            annual_demand = await self._calculate_annual_demand(rule.product_id, rule.warehouse_id)
            if annual_demand > 0:
                ordering_cost = Decimal("100")  # Default ordering cost
                holding_cost = rule.supplier_unit_cost * Decimal("0.2") if rule.supplier_unit_cost else Decimal("10")  # 20% of unit cost
                eoq = rule.calculate_eoq(annual_demand, ordering_cost, holding_cost)
                order_quantity = max(eoq, rule.minimum_order_quantity)
                if rule.maximum_order_quantity:
                    order_quantity = min(order_quantity, rule.maximum_order_quantity)
        
        # Generate order number
        order_number = f"AO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{rule.id}"
        
        # Calculate costs
        unit_cost = rule.supplier_unit_cost
        total_cost = unit_cost * order_quantity if unit_cost else None
        
        # Determine if approval is required
        requires_approval = rule.requires_manual_approval
        if rule.auto_approve_threshold and total_cost and total_cost > rule.auto_approve_threshold:
            requires_approval = True
        
        # Create order
        order = AutoOrder(
            order_number=order_number,
            order_rule_id=rule.id,
            product_id=rule.product_id,
            warehouse_id=rule.warehouse_id,
            organization_id=organization_id,
            quantity_ordered=order_quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            stock_level_at_creation=inventory_item.quantity_available,
            trigger_level_at_creation=rule.trigger_level,
            supplier_id=rule.preferred_supplier_id,
            expected_delivery_date=datetime.utcnow() + timedelta(days=rule.lead_time_days),
            requires_approval=requires_approval,
            status=AutoOrderStatus.PENDING.value,
            created_by=1  # System user
        )
        
        self.db.add(order)
        await self.db.flush()
        
        # Update rule statistics
        if order.status != AutoOrderStatus.CANCELLED.value:
            rule.successful_orders += 1
            if total_cost:
                rule.total_order_value += total_cost
        
        return order
    
    async def _calculate_annual_demand(self, product_id: int, warehouse_id: int) -> Decimal:
        """Calculate annual demand based on historical stock movements."""
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        
        query = select(func.sum(StockMovement.quantity)).where(
            and_(
                StockMovement.product_id == product_id,
                StockMovement.warehouse_id == warehouse_id,
                StockMovement.movement_type == MovementType.OUT.value,
                StockMovement.movement_date >= one_year_ago,
                StockMovement.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        annual_demand = result.scalar() or Decimal(0)
        
        return abs(annual_demand)  # Ensure positive value
    
    async def approve_auto_order(
        self, 
        order_id: int, 
        approved_by: int, 
        approval_notes: Optional[str] = None
    ) -> AutoOrder:
        """Approve an auto order."""
        query = select(AutoOrder).where(
            and_(
                AutoOrder.id == order_id,
                AutoOrder.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValidationError("Auto order not found")
        
        if order.status != AutoOrderStatus.PENDING.value:
            raise BusinessLogicError("Only pending orders can be approved")
        
        order.status = AutoOrderStatus.APPROVED.value
        order.approved_by = approved_by
        order.approval_date = datetime.utcnow()
        order.approval_notes = approval_notes
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order


class InventoryAnalyticsService:
    """Service for inventory analytics and forecasting."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_analytics(
        self, 
        product_id: int, 
        warehouse_id: int,
        organization_id: int,
        period_days: int = 30
    ) -> InventoryAnalytics:
        """Generate comprehensive inventory analytics for a product/warehouse."""
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)
        
        # Get stock movements for the period
        movements_query = select(StockMovement).where(
            and_(
                StockMovement.product_id == product_id,
                StockMovement.warehouse_id == warehouse_id,
                StockMovement.organization_id == organization_id,
                StockMovement.movement_date >= period_start,
                StockMovement.movement_date <= period_end,
                StockMovement.deleted_at.is_(None)
            )
        )
        movements_result = await self.db.execute(movements_query)
        movements = movements_result.scalars().all()
        
        # Calculate movement metrics
        total_inbound = sum(
            m.quantity for m in movements 
            if m.movement_type in [MovementType.IN.value, MovementType.RETURN.value] and m.quantity > 0
        )
        total_outbound = sum(
            abs(m.quantity) for m in movements 
            if m.movement_type == MovementType.OUT.value and m.quantity < 0
        )
        total_adjustments = sum(
            m.quantity for m in movements 
            if m.movement_type == MovementType.ADJUSTMENT.value
        )
        
        average_daily_usage = total_outbound / period_days if period_days > 0 else Decimal(0)
        
        # Calculate demand variance
        daily_usage = []
        for i in range(period_days):
            day_start = period_start + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_usage = sum(
                abs(m.quantity) for m in movements
                if (m.movement_date >= day_start and m.movement_date < day_end and 
                    m.movement_type == MovementType.OUT.value and m.quantity < 0)
            )
            daily_usage.append(float(day_usage))
        
        demand_variance = Decimal(str(sum((x - float(average_daily_usage))**2 for x in daily_usage) / len(daily_usage))) if daily_usage else None
        
        # Get current inventory item for additional metrics
        inventory_query = select(InventoryItem).where(
            and_(
                InventoryItem.product_id == product_id,
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.organization_id == organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        )
        inventory_result = await self.db.execute(inventory_query)
        inventory_item = inventory_result.scalar_one_or_none()
        
        # Calculate turnover rate
        turnover_rate = None
        carrying_cost = None
        if inventory_item and inventory_item.average_cost and inventory_item.quantity_on_hand > 0:
            avg_inventory_value = inventory_item.average_cost * inventory_item.quantity_on_hand
            if avg_inventory_value > 0:
                turnover_rate = (total_outbound * inventory_item.average_cost) / avg_inventory_value
                carrying_cost = avg_inventory_value * Decimal("0.2")  # Assume 20% carrying cost
        
        # Calculate ABC classification (simplified)
        abc_classification = await self._calculate_abc_classification(
            product_id, warehouse_id, organization_id
        )
        
        # Calculate risk scores (simplified)
        stockout_risk_score = self._calculate_stockout_risk(inventory_item, average_daily_usage) if inventory_item else None
        overstock_risk_score = self._calculate_overstock_risk(inventory_item, average_daily_usage) if inventory_item else None
        
        # Create analytics record
        analytics_data = InventoryAnalyticsCreate(
            product_id=product_id,
            warehouse_id=warehouse_id,
            period_start=period_start,
            period_end=period_end,
            total_inbound=total_inbound,
            total_outbound=total_outbound,
            total_adjustments=total_adjustments,
            average_daily_usage=average_daily_usage,
            demand_variance=demand_variance,
            abc_classification=abc_classification,
            stockout_risk_score=stockout_risk_score,
            overstock_risk_score=overstock_risk_score,
            turnover_rate=turnover_rate,
            carrying_cost=carrying_cost
        )
        
        analytics = InventoryAnalytics(
            organization_id=organization_id,
            created_by=1,  # System user
            **analytics_data.model_dump()
        )
        
        self.db.add(analytics)
        await self.db.commit()
        await self.db.refresh(analytics)
        
        return analytics
    
    async def _calculate_abc_classification(
        self, 
        product_id: int, 
        warehouse_id: int, 
        organization_id: int
    ) -> Optional[str]:
        """Calculate ABC classification based on revenue contribution."""
        # Get total revenue for this product over the last year
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        
        product_revenue_query = select(
            func.sum(StockMovement.quantity * StockMovement.unit_cost)
        ).where(
            and_(
                StockMovement.product_id == product_id,
                StockMovement.warehouse_id == warehouse_id,
                StockMovement.organization_id == organization_id,
                StockMovement.movement_type == MovementType.OUT.value,
                StockMovement.movement_date >= one_year_ago,
                StockMovement.unit_cost.is_not(None),
                StockMovement.deleted_at.is_(None)
            )
        )
        product_result = await self.db.execute(product_revenue_query)
        product_revenue = product_result.scalar() or Decimal(0)
        
        # Get total revenue for all products in the warehouse
        total_revenue_query = select(
            func.sum(StockMovement.quantity * StockMovement.unit_cost)
        ).where(
            and_(
                StockMovement.warehouse_id == warehouse_id,
                StockMovement.organization_id == organization_id,
                StockMovement.movement_type == MovementType.OUT.value,
                StockMovement.movement_date >= one_year_ago,
                StockMovement.unit_cost.is_not(None),
                StockMovement.deleted_at.is_(None)
            )
        )
        total_result = await self.db.execute(total_revenue_query)
        total_revenue = total_result.scalar() or Decimal(0)
        
        if total_revenue <= 0:
            return None
        
        revenue_percentage = (abs(product_revenue) / total_revenue) * 100
        
        # ABC classification thresholds
        if revenue_percentage >= 20:  # Top 20% of revenue
            return "A"
        elif revenue_percentage >= 5:  # Next 15% of revenue
            return "B"
        else:
            return "C"
    
    def _calculate_stockout_risk(
        self, 
        inventory_item: InventoryItem, 
        average_daily_usage: Decimal
    ) -> Decimal:
        """Calculate stockout risk score (0-1)."""
        if average_daily_usage <= 0:
            return Decimal("0.1")  # Low risk if no usage
        
        days_of_stock = inventory_item.quantity_available / average_daily_usage
        
        # Risk increases as days of stock decreases
        if days_of_stock <= 1:
            return Decimal("0.9")  # High risk
        elif days_of_stock <= 7:
            return Decimal("0.7")  # Medium-high risk
        elif days_of_stock <= 30:
            return Decimal("0.4")  # Medium risk
        else:
            return Decimal("0.1")  # Low risk
    
    def _calculate_overstock_risk(
        self, 
        inventory_item: InventoryItem, 
        average_daily_usage: Decimal
    ) -> Decimal:
        """Calculate overstock risk score (0-1)."""
        if average_daily_usage <= 0:
            return Decimal("0.8") if inventory_item.quantity_on_hand > 0 else Decimal("0.1")
        
        days_of_stock = inventory_item.quantity_on_hand / average_daily_usage
        
        # Risk increases as days of stock increases
        if days_of_stock >= 180:  # 6 months
            return Decimal("0.9")  # High risk
        elif days_of_stock >= 90:  # 3 months
            return Decimal("0.7")  # Medium-high risk
        elif days_of_stock >= 60:  # 2 months
            return Decimal("0.4")  # Medium risk
        else:
            return Decimal("0.1")  # Low risk


class ShippingInventoryIntegrationService:
    """Service for shipping and inventory synchronization."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_shipping_sync(
        self, 
        sync_data: ShippingInventorySyncCreate, 
        organization_id: int
    ) -> ShippingInventorySync:
        """Create a new shipping inventory sync record."""
        # Validate inventory item exists
        inventory_query = select(InventoryItem).where(
            and_(
                InventoryItem.id == sync_data.inventory_item_id,
                InventoryItem.organization_id == organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        )
        inventory_result = await self.db.execute(inventory_query)
        inventory_item = inventory_result.scalar_one_or_none()
        
        if not inventory_item:
            raise ValidationError("Inventory item not found")
        
        # Check if sync record already exists
        existing_sync_query = select(ShippingInventorySync).where(
            and_(
                ShippingInventorySync.sync_id == sync_data.sync_id,
                ShippingInventorySync.organization_id == organization_id,
                ShippingInventorySync.deleted_at.is_(None)
            )
        )
        existing_result = await self.db.execute(existing_sync_query)
        existing_sync = existing_result.scalar_one_or_none()
        
        if existing_sync:
            raise BusinessLogicError("Shipping sync record already exists with this sync_id")
        
        # Create sync record
        sync_record = ShippingInventorySync(
            organization_id=organization_id,
            created_by=1,  # System user
            **sync_data.model_dump()
        )
        
        self.db.add(sync_record)
        
        # Reserve inventory when shipment is created
        if inventory_item.quantity_available >= sync_data.quantity_shipped:
            inventory_item.reserve_stock(sync_data.quantity_shipped)
            sync_record.inventory_reserved_at_ship = True
        else:
            logger.warning(f"Insufficient inventory to reserve {sync_data.quantity_shipped} units for shipment {sync_data.shipment_id}")
        
        await self.db.commit()
        await self.db.refresh(sync_record)
        
        return sync_record
    
    async def update_shipment_status(
        self, 
        sync_id: str, 
        new_status: str,
        tracking_events: Optional[list[dict[str, Any]]] = None,
        organization_id: Optional[int] = None
    ) -> ShippingInventorySync:
        """Update shipment status and sync inventory accordingly."""
        query = select(ShippingInventorySync).options(
            selectinload(ShippingInventorySync.inventory_item)
        ).where(
            and_(
                ShippingInventorySync.sync_id == sync_id,
                ShippingInventorySync.deleted_at.is_(None)
            )
        )
        
        if organization_id:
            query = query.where(ShippingInventorySync.organization_id == organization_id)
        
        result = await self.db.execute(query)
        sync_record = result.scalar_one_or_none()
        
        if not sync_record:
            raise ValidationError("Shipping sync record not found")
        
        old_status = sync_record.status
        
        # Update status
        sync_record.update_status(new_status, tracking_events)
        
        # Handle inventory updates based on status change
        inventory_item = sync_record.inventory_item
        
        if old_status != ShipmentStatus.SHIPPED.value and new_status == ShipmentStatus.SHIPPED.value:
            # Reduce inventory when shipped
            if not sync_record.inventory_reduced_at_ship and inventory_item:
                inventory_item.quantity_on_hand -= sync_record.quantity_shipped
                if sync_record.inventory_reserved_at_ship:
                    inventory_item.release_reservation(sync_record.quantity_shipped)
                inventory_item.calculate_available_quantity()
                sync_record.inventory_reduced_at_ship = True
                
                # Create stock movement
                stock_movement = StockMovement(
                    transaction_number=f"SHIP-{sync_record.shipment_id}",
                    inventory_item_id=inventory_item.id,
                    product_id=inventory_item.product_id,
                    warehouse_id=inventory_item.warehouse_id,
                    organization_id=sync_record.organization_id,
                    movement_type=MovementType.OUT.value,
                    quantity=-sync_record.quantity_shipped,
                    quantity_before=inventory_item.quantity_on_hand + sync_record.quantity_shipped,
                    quantity_after=inventory_item.quantity_on_hand,
                    reference_type="shipment",
                    reference_number=sync_record.shipment_id,
                    reference_id=sync_record.id,
                    reason="Shipped to customer",
                    created_by=1  # System user
                )
                self.db.add(stock_movement)
        
        elif old_status != ShipmentStatus.RETURNED.value and new_status == ShipmentStatus.RETURNED.value:
            # Restore inventory when returned
            if not sync_record.inventory_restored_on_return and inventory_item:
                returned_quantity = sync_record.quantity_returned or sync_record.quantity_shipped
                inventory_item.quantity_on_hand += returned_quantity
                inventory_item.calculate_available_quantity()
                sync_record.inventory_restored_on_return = True
                
                # Create stock movement
                stock_movement = StockMovement(
                    transaction_number=f"RET-{sync_record.shipment_id}",
                    inventory_item_id=inventory_item.id,
                    product_id=inventory_item.product_id,
                    warehouse_id=inventory_item.warehouse_id,
                    organization_id=sync_record.organization_id,
                    movement_type=MovementType.RETURN.value,
                    quantity=returned_quantity,
                    quantity_before=inventory_item.quantity_on_hand - returned_quantity,
                    quantity_after=inventory_item.quantity_on_hand,
                    reference_type="return",
                    reference_number=sync_record.shipment_id,
                    reference_id=sync_record.id,
                    reason="Returned from customer",
                    created_by=1  # System user
                )
                self.db.add(stock_movement)
        
        sync_record.sync_status = "synced"
        
        await self.db.commit()
        await self.db.refresh(sync_record)
        
        return sync_record
    
    async def sync_all_pending_shipments(self, organization_id: int) -> dict[str, int]:
        """Synchronize all pending shipments with external systems."""
        pending_query = select(ShippingInventorySync).where(
            and_(
                ShippingInventorySync.organization_id == organization_id,
                ShippingInventorySync.sync_status == "pending",
                ShippingInventorySync.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(pending_query)
        pending_syncs = result.scalars().all()
        
        successful_syncs = 0
        failed_syncs = 0
        
        for sync_record in pending_syncs:
            try:
                # Here you would integrate with external shipping APIs
                # For now, we'll simulate the sync process
                await asyncio.sleep(0.1)  # Simulate API call
                
                # Update sync status
                sync_record.sync_status = "synced"
                sync_record.last_sync_at = datetime.utcnow()
                successful_syncs += 1
                
            except Exception as e:
                sync_record.sync_status = "failed"
                sync_record.sync_error = str(e)
                failed_syncs += 1
                logger.error(f"Failed to sync shipment {sync_record.shipment_id}: {str(e)}")
        
        await self.db.commit()
        
        return {
            "total_processed": len(pending_syncs),
            "successful": successful_syncs,
            "failed": failed_syncs
        }