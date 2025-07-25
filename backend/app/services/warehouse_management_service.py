"""
Warehouse Management Service for CC02 v62.0
Advanced warehouse operations, optimization, and multi-location inventory management
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BusinessLogicError, ValidationError
from app.models.inventory import InventoryItem, StockMovement, Warehouse, MovementType
from app.models.inventory_integration import (
    InventoryAnalytics,
    RealtimeInventoryAlert,
    ShippingInventorySync,
    AlertType,
)
from app.schemas.inventory_integration import WarehousePerformanceMetrics


class WarehouseOptimizationService:
    """Service for warehouse optimization and management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_warehouse_performance_metrics(
        self, 
        warehouse_id: int, 
        organization_id: int,
        period_days: int = 30
    ) -> WarehousePerformanceMetrics:
        """Get comprehensive performance metrics for a warehouse."""
        # Get warehouse info
        warehouse_query = select(Warehouse).where(
            and_(
                Warehouse.id == warehouse_id,
                Warehouse.organization_id == organization_id,
                Warehouse.deleted_at.is_(None)
            )
        )
        warehouse_result = await self.db.execute(warehouse_query)
        warehouse = warehouse_result.scalar_one_or_none()
        
        if not warehouse:
            raise ValidationError("Warehouse not found")
        
        # Get total items in warehouse
        items_query = select(func.count(InventoryItem.id)).where(
            and_(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.organization_id == organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        )
        items_result = await self.db.execute(items_query)
        total_items = items_result.scalar() or 0
        
        # Calculate utilization percentage
        utilization_percentage = warehouse.get_utilization_percentage()
        
        # Get total stock value
        total_stock_value = warehouse.get_total_stock_value()
        
        # Calculate monthly throughput
        period_start = datetime.utcnow() - timedelta(days=period_days)
        throughput_query = select(func.sum(func.abs(StockMovement.quantity))).where(
            and_(
                StockMovement.warehouse_id == warehouse_id,
                StockMovement.organization_id == organization_id,
                StockMovement.movement_date >= period_start,
                StockMovement.deleted_at.is_(None)
            )
        )
        throughput_result = await self.db.execute(throughput_query)
        monthly_throughput = throughput_result.scalar() or Decimal(0)
        
        # Calculate average fulfillment time
        avg_fulfillment_time = await self._calculate_average_fulfillment_time(
            warehouse_id, organization_id, period_days
        )
        
        # Calculate accuracy rate
        accuracy_rate = await self._calculate_accuracy_rate(
            warehouse_id, organization_id, period_days
        )
        
        # Calculate cost per unit handled
        cost_per_unit_handled = await self._calculate_cost_per_unit_handled(
            warehouse_id, organization_id, monthly_throughput
        )
        
        return WarehousePerformanceMetrics(
            warehouse_id=warehouse_id,
            warehouse_name=warehouse.name,
            total_items=total_items,
            utilization_percentage=utilization_percentage,
            total_stock_value=total_stock_value,
            monthly_throughput=monthly_throughput,
            average_fulfillment_time=avg_fulfillment_time,
            accuracy_rate=accuracy_rate,
            cost_per_unit_handled=cost_per_unit_handled
        )
    
    async def _calculate_average_fulfillment_time(
        self, 
        warehouse_id: int, 
        organization_id: int, 
        period_days: int
    ) -> Optional[Decimal]:
        """Calculate average fulfillment time based on shipping data."""
        period_start = datetime.utcnow() - timedelta(days=period_days)
        
        # Get completed shipments from this warehouse
        query = select(ShippingInventorySync).where(
            and_(
                ShippingInventorySync.warehouse_id == warehouse_id,
                ShippingInventorySync.organization_id == organization_id,
                ShippingInventorySync.status == "delivered",
                ShippingInventorySync.ship_date.is_not(None),
                ShippingInventorySync.actual_delivery_date.is_not(None),
                ShippingInventorySync.created_at >= period_start,
                ShippingInventorySync.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        shipments = result.scalars().all()
        
        if not shipments:
            return None
        
        total_fulfillment_time = 0
        count = 0
        
        for shipment in shipments:
            if shipment.ship_date and shipment.actual_delivery_date:
                fulfillment_time = (shipment.actual_delivery_date - shipment.ship_date).days
                total_fulfillment_time += fulfillment_time
                count += 1
        
        return Decimal(total_fulfillment_time / count) if count > 0 else None
    
    async def _calculate_accuracy_rate(
        self, 
        warehouse_id: int, 
        organization_id: int, 
        period_days: int
    ) -> Optional[Decimal]:
        """Calculate picking/packing accuracy rate."""
        period_start = datetime.utcnow() - timedelta(days=period_days)
        
        # Total movements in period
        total_movements_query = select(func.count(StockMovement.id)).where(
            and_(
                StockMovement.warehouse_id == warehouse_id,
                StockMovement.organization_id == organization_id,
                StockMovement.movement_date >= period_start,
                StockMovement.deleted_at.is_(None)
            )
        )
        total_result = await self.db.execute(total_movements_query)
        total_movements = total_result.scalar() or 0
        
        # Count adjustments (errors that needed correction)
        error_movements_query = select(func.count(StockMovement.id)).where(
            and_(
                StockMovement.warehouse_id == warehouse_id,
                StockMovement.organization_id == organization_id,
                StockMovement.movement_type == MovementType.ADJUSTMENT.value,
                StockMovement.movement_date >= period_start,
                StockMovement.reason.like("%error%"),  # Assume errors contain "error" in reason
                StockMovement.deleted_at.is_(None)
            )
        )
        error_result = await self.db.execute(error_movements_query)
        error_movements = error_result.scalar() or 0
        
        if total_movements == 0:
            return None
        
        accuracy_rate = (total_movements - error_movements) / total_movements
        return Decimal(str(max(0, accuracy_rate)))
    
    async def _calculate_cost_per_unit_handled(
        self, 
        warehouse_id: int, 
        organization_id: int, 
        throughput: Decimal
    ) -> Optional[Decimal]:
        """Calculate cost per unit handled (simplified calculation)."""
        if throughput <= 0:
            return None
        
        # Get warehouse info for operational costs
        warehouse_query = select(Warehouse).where(
            and_(
                Warehouse.id == warehouse_id,
                Warehouse.organization_id == organization_id,
                Warehouse.deleted_at.is_(None)
            )
        )
        warehouse_result = await self.db.execute(warehouse_query)
        warehouse = warehouse_result.scalar_one_or_none()
        
        if not warehouse:
            return None
        
        # Simplified cost calculation based on warehouse area and throughput
        # In reality, this would include labor, utilities, equipment costs, etc.
        base_cost_per_sqm = Decimal("100")  # Monthly cost per square meter
        area = warehouse.total_area or Decimal("1000")  # Default 1000 sqm
        monthly_operational_cost = area * base_cost_per_sqm
        
        cost_per_unit = monthly_operational_cost / throughput
        return cost_per_unit
    
    async def optimize_warehouse_layout(
        self, 
        warehouse_id: int, 
        organization_id: int
    ) -> dict[str, Any]:
        """Optimize warehouse layout based on product velocity and characteristics."""
        # Get all inventory items in warehouse with analytics
        items_query = select(InventoryItem).options(
            selectinload(InventoryItem.product)
        ).where(
            and_(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.organization_id == organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        )
        items_result = await self.db.execute(items_query)
        items = items_result.scalars().all()
        
        # Get recent analytics for each product
        analytics_by_product = {}
        for item in items:
            analytics_query = select(InventoryAnalytics).where(
                and_(
                    InventoryAnalytics.product_id == item.product_id,
                    InventoryAnalytics.warehouse_id == warehouse_id,
                    InventoryAnalytics.organization_id == organization_id,
                    InventoryAnalytics.deleted_at.is_(None)
                )
            ).order_by(desc(InventoryAnalytics.created_at)).limit(1)
            
            analytics_result = await self.db.execute(analytics_query)
            analytics = analytics_result.scalar_one_or_none()
            
            if analytics:
                analytics_by_product[item.product_id] = analytics
        
        # Categorize products by velocity (ABC analysis)
        high_velocity_items = []
        medium_velocity_items = []
        low_velocity_items = []
        
        for item in items:
            analytics = analytics_by_product.get(item.product_id)
            if analytics:
                if analytics.abc_classification == "A":
                    high_velocity_items.append(item)
                elif analytics.abc_classification == "B":
                    medium_velocity_items.append(item)
                else:
                    low_velocity_items.append(item)
            else:
                low_velocity_items.append(item)  # No analytics = low velocity
        
        # Generate layout recommendations
        recommendations = {
            "high_velocity_zone": {
                "description": "Place near picking areas and main aisles",
                "items_count": len(high_velocity_items),
                "recommended_locations": ["Zone A", "Main aisle proximity"],
                "products": [
                    {
                        "product_id": item.product_id,
                        "current_location": item.location_code,
                        "recommended_location": f"A{i+1:03d}"
                    }
                    for i, item in enumerate(high_velocity_items[:10])  # Top 10
                ]
            },
            "medium_velocity_zone": {
                "description": "Standard picking areas",
                "items_count": len(medium_velocity_items),
                "recommended_locations": ["Zone B", "Secondary aisles"],
                "products": [
                    {
                        "product_id": item.product_id,
                        "current_location": item.location_code,
                        "recommended_location": f"B{i+1:03d}"
                    }
                    for i, item in enumerate(medium_velocity_items[:10])
                ]
            },
            "low_velocity_zone": {
                "description": "Storage areas, upper shelves",
                "items_count": len(low_velocity_items),
                "recommended_locations": ["Zone C", "Upper levels", "Remote areas"],
                "products": [
                    {
                        "product_id": item.product_id,
                        "current_location": item.location_code,
                        "recommended_location": f"C{i+1:03d}"
                    }
                    for i, item in enumerate(low_velocity_items[:10])
                ]
            }
        }
        
        # Calculate potential efficiency gains
        efficiency_gains = {
            "estimated_picking_time_reduction": "15-25%",
            "estimated_travel_distance_reduction": "20-30%",
            "estimated_labor_cost_savings": "10-15%",
            "implementation_priority": self._calculate_implementation_priority(
                len(high_velocity_items), len(medium_velocity_items), len(low_velocity_items)
            )
        }
        
        return {
            "warehouse_id": warehouse_id,
            "optimization_date": datetime.utcnow().isoformat(),
            "total_items": len(items),
            "layout_recommendations": recommendations,
            "efficiency_gains": efficiency_gains,
            "next_review_date": (datetime.utcnow() + timedelta(days=90)).isoformat()
        }
    
    def _calculate_implementation_priority(
        self, 
        high_velocity_count: int, 
        medium_velocity_count: int, 
        low_velocity_count: int
    ) -> str:
        """Calculate implementation priority based on product distribution."""
        total_items = high_velocity_count + medium_velocity_count + low_velocity_count
        
        if total_items == 0:
            return "Low"
        
        high_velocity_ratio = high_velocity_count / total_items
        
        if high_velocity_ratio >= 0.3:  # 30% or more high velocity
            return "High"
        elif high_velocity_ratio >= 0.15:  # 15-30% high velocity
            return "Medium"
        else:
            return "Low"
    
    async def generate_picking_optimization(
        self, 
        warehouse_id: int, 
        organization_id: int,
        order_ids: list[str]
    ) -> dict[str, Any]:
        """Generate optimized picking routes for given orders."""
        # This is a simplified version - in reality would integrate with actual order data
        # Get all inventory items in warehouse
        items_query = select(InventoryItem).where(
            and_(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.organization_id == organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        )
        items_result = await self.db.execute(items_query)
        items = items_result.scalars().all()
        
        # Group items by zone for efficient picking
        zones = {}
        for item in items:
            zone = item.zone or "Default"
            if zone not in zones:
                zones[zone] = []
            zones[zone].append({
                "product_id": item.product_id,
                "location": item.location_code,
                "available_quantity": float(item.quantity_available)
            })
        
        # Generate optimized picking sequence
        picking_sequence = []
        for zone_name, zone_items in zones.items():
            # Sort items by location code for systematic picking
            sorted_items = sorted(zone_items, key=lambda x: x["location"] or "ZZZ")
            picking_sequence.append({
                "zone": zone_name,
                "sequence": len(picking_sequence) + 1,
                "items": sorted_items[:5],  # Limit to 5 items per zone for demo
                "estimated_time_minutes": len(sorted_items) * 2  # 2 minutes per item
            })
        
        return {
            "warehouse_id": warehouse_id,
            "optimization_date": datetime.utcnow().isoformat(),
            "total_zones": len(zones),
            "picking_sequence": picking_sequence,
            "total_estimated_time_minutes": sum(seq["estimated_time_minutes"] for seq in picking_sequence),
            "efficiency_notes": [
                "Follow zone sequence to minimize travel time",
                "Use picking equipment appropriate for item weight/size",
                "Verify quantities at each location before moving to next zone"
            ]
        }
    
    async def calculate_optimal_stock_levels(
        self, 
        warehouse_id: int, 
        organization_id: int
    ) -> dict[str, Any]:
        """Calculate optimal stock levels for all products in warehouse."""
        # Get all inventory items with recent analytics
        items_query = select(InventoryItem).options(
            selectinload(InventoryItem.product)
        ).where(
            and_(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.organization_id == organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        )
        items_result = await self.db.execute(items_query)
        items = items_result.scalars().all()
        
        optimizations = []
        
        for item in items:
            # Get recent analytics
            analytics_query = select(InventoryAnalytics).where(
                and_(
                    InventoryAnalytics.product_id == item.product_id,
                    InventoryAnalytics.warehouse_id == warehouse_id,
                    InventoryAnalytics.organization_id == organization_id,
                    InventoryAnalytics.deleted_at.is_(None)
                )
            ).order_by(desc(InventoryAnalytics.created_at)).limit(1)
            
            analytics_result = await self.db.execute(analytics_query)
            analytics = analytics_result.scalar_one_or_none()
            
            if analytics and analytics.average_daily_usage > 0:
                # Calculate optimal levels using various methods
                current_min = item.minimum_level or Decimal(0)
                current_reorder = item.reorder_point or Decimal(0)
                
                # Service level approach (95% service level)
                daily_usage = analytics.average_daily_usage
                demand_variance = analytics.demand_variance or Decimal(0)
                lead_time_days = 7  # Assume 7 days lead time
                
                # Safety stock calculation
                service_factor = Decimal("1.65")  # For 95% service level
                safety_stock = service_factor * (demand_variance * lead_time_days).sqrt() if demand_variance > 0 else daily_usage * 2
                
                # Optimal reorder point
                optimal_reorder_point = (daily_usage * lead_time_days) + safety_stock
                
                # Optimal minimum level (buffer stock)
                optimal_minimum_level = safety_stock + (daily_usage * 3)  # 3 days buffer
                
                # Economic Order Quantity (simplified)
                annual_demand = daily_usage * 365
                ordering_cost = Decimal("100")  # Assume $100 per order
                holding_cost_rate = Decimal("0.2")  # 20% of item cost
                item_cost = item.average_cost or Decimal("10")  # Default $10
                holding_cost = item_cost * holding_cost_rate
                
                if holding_cost > 0:
                    eoq = (2 * annual_demand * ordering_cost / holding_cost).sqrt()
                else:
                    eoq = daily_usage * 30  # 30 days supply
                
                optimizations.append({
                    "product_id": item.product_id,
                    "current_stock": float(item.quantity_on_hand),
                    "current_minimum_level": float(current_min),
                    "current_reorder_point": float(current_reorder),
                    "optimal_minimum_level": float(optimal_minimum_level),
                    "optimal_reorder_point": float(optimal_reorder_point),
                    "optimal_order_quantity": float(eoq),
                    "daily_usage": float(daily_usage),
                    "safety_stock": float(safety_stock),
                    "improvement_potential": {
                        "carrying_cost_reduction": float(abs(optimal_minimum_level - current_min) * item_cost * holding_cost_rate) if current_min > 0 else 0,
                        "service_level_improvement": "95%" if current_reorder < optimal_reorder_point else "Maintained",
                        "inventory_turnover_improvement": float(annual_demand / max(optimal_minimum_level, Decimal("1")))
                    }
                })
        
        return {
            "warehouse_id": warehouse_id,
            "calculation_date": datetime.utcnow().isoformat(),
            "total_products_analyzed": len(optimizations),
            "optimizations": optimizations[:20],  # Limit to 20 for response size
            "summary": {
                "products_needing_adjustment": len([opt for opt in optimizations if 
                    abs(opt["optimal_minimum_level"] - opt["current_minimum_level"]) > 1]),
                "total_potential_savings": sum(opt["improvement_potential"]["carrying_cost_reduction"] for opt in optimizations),
                "average_service_level_target": "95%"
            }
        }
    
    async def generate_warehouse_capacity_report(
        self, 
        warehouse_id: int, 
        organization_id: int
    ) -> dict[str, Any]:
        """Generate comprehensive warehouse capacity and utilization report."""
        # Get warehouse info
        warehouse_query = select(Warehouse).where(
            and_(
                Warehouse.id == warehouse_id,
                Warehouse.organization_id == organization_id,
                Warehouse.deleted_at.is_(None)
            )
        )
        warehouse_result = await self.db.execute(warehouse_query)
        warehouse = warehouse_result.scalar_one_or_none()
        
        if not warehouse:
            raise ValidationError("Warehouse not found")
        
        # Get all inventory items
        items_query = select(InventoryItem).where(
            and_(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.organization_id == organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        )
        items_result = await self.db.execute(items_query)
        items = items_result.scalars().all()
        
        # Calculate capacity metrics
        total_capacity = warehouse.storage_capacity or Decimal("10000")  # Default capacity
        used_capacity = sum(item.quantity_on_hand for item in items)
        utilization_percentage = (used_capacity / total_capacity * 100) if total_capacity > 0 else Decimal(0)
        
        # Categorize utilization by zones
        zone_utilization = {}
        for item in items:
            zone = item.zone or "Default"
            if zone not in zone_utilization:
                zone_utilization[zone] = {"items": 0, "quantity": Decimal(0)}
            
            zone_utilization[zone]["items"] += 1
            zone_utilization[zone]["quantity"] += item.quantity_on_hand
        
        # Calculate growth projections based on recent trends
        growth_projection = await self._calculate_growth_projection(warehouse_id, organization_id)
        
        # Generate recommendations
        recommendations = []
        
        if utilization_percentage > 90:
            recommendations.append({
                "type": "critical",
                "message": "Warehouse is at critical capacity. Consider expansion or optimization.",
                "action": "immediate_action_required"
            })
        elif utilization_percentage > 80:
            recommendations.append({
                "type": "warning", 
                "message": "Warehouse utilization is high. Monitor closely and plan for expansion.",
                "action": "plan_expansion"
            })
        elif utilization_percentage < 50:
            recommendations.append({
                "type": "info",
                "message": "Warehouse has significant unused capacity. Consider consolidation opportunities.",
                "action": "optimize_layout"
            })
        
        return {
            "warehouse_id": warehouse_id,
            "warehouse_name": warehouse.name,
            "report_date": datetime.utcnow().isoformat(),
            "capacity_metrics": {
                "total_capacity": float(total_capacity),
                "used_capacity": float(used_capacity),
                "available_capacity": float(total_capacity - used_capacity),
                "utilization_percentage": float(utilization_percentage),
                "total_items": len(items),
                "total_stock_value": float(warehouse.get_total_stock_value())
            },
            "zone_breakdown": {
                zone: {
                    "items_count": data["items"],
                    "quantity": float(data["quantity"]),
                    "utilization_percentage": float(data["quantity"] / total_capacity * 100) if total_capacity > 0 else 0
                }
                for zone, data in zone_utilization.items()
            },
            "growth_projection": growth_projection,
            "recommendations": recommendations,
            "next_review_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
    
    async def _calculate_growth_projection(
        self, 
        warehouse_id: int, 
        organization_id: int
    ) -> dict[str, Any]:
        """Calculate warehouse capacity growth projection."""
        # Get stock movements for the last 6 months
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        movements_query = select(StockMovement).where(
            and_(
                StockMovement.warehouse_id == warehouse_id,
                StockMovement.organization_id == organization_id,
                StockMovement.movement_date >= six_months_ago,
                StockMovement.movement_type == MovementType.IN.value,
                StockMovement.deleted_at.is_(None)
            )
        ).order_by(StockMovement.movement_date)
        
        movements_result = await self.db.execute(movements_query)
        movements = movements_result.scalars().all()
        
        if len(movements) < 2:
            return {
                "trend": "insufficient_data",
                "projected_growth_rate": 0,
                "months_to_capacity": None,
                "confidence": "low"
            }
        
        # Calculate monthly inbound quantities
        monthly_inbound = {}
        for movement in movements:
            month_key = movement.movement_date.strftime("%Y-%m")
            if month_key not in monthly_inbound:
                monthly_inbound[month_key] = Decimal(0)
            monthly_inbound[month_key] += movement.quantity
        
        # Simple linear regression for growth trend
        months = list(monthly_inbound.keys())
        quantities = list(monthly_inbound.values())
        
        if len(quantities) >= 3:
            # Calculate trend
            x_values = list(range(len(quantities)))
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(float(q) for q in quantities)
            sum_xy = sum(x * float(y) for x, y in zip(x_values, quantities))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
            
            growth_rate = slope / (sum_y / n) * 100 if sum_y > 0 else 0  # Percentage growth
            
            return {
                "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                "projected_monthly_growth_rate": round(growth_rate, 2),
                "data_points": len(quantities),
                "confidence": "high" if len(quantities) >= 6 else "medium"
            }
        
        return {
            "trend": "stable",
            "projected_monthly_growth_rate": 0,
            "data_points": len(quantities),
            "confidence": "low"
        }