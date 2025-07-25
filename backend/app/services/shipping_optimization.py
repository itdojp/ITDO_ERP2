"""Shipping optimization service for CC02 v61.0 - Day 6: Shipping Cost Optimization."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_management import (
    CarrierConfiguration,
    DeliveryPriority,
    PackageType,
    Shipment,
    ShippingCarrier,
    ShippingMethod,
    ShippingRate,
    ShippingZone,
)
from app.types import OrganizationId

logger = logging.getLogger(__name__)


class ShippingOptimizationService:
    """Service for optimizing shipping costs and routes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def optimize_shipping_selection(
        self,
        organization_id: OrganizationId,
        from_postal_code: str,
        to_postal_code: str,
        weight_kg: float,
        dimensions_cm: Dict[str, float],
        priority: DeliveryPriority = DeliveryPriority.NORMAL,
        max_cost: Optional[float] = None,
        required_delivery_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Optimize carrier and method selection for best cost/service balance."""
        
        # Get all available carriers
        carriers = await self._get_available_carriers(organization_id)
        
        if not carriers:
            raise ValueError("No carriers configured for organization")
        
        # Get shipping zones for optimization
        zones = await self._get_shipping_zones(organization_id)
        
        # Calculate rates for all carrier/method combinations
        options = []
        
        for carrier in carriers:
            for method in ShippingMethod:
                if method.value in carrier.supported_methods or not carrier.supported_methods:
                    try:
                        rate_info = await self._calculate_optimized_rate(
                            carrier=carrier,
                            shipping_method=method,
                            from_postal_code=from_postal_code,
                            to_postal_code=to_postal_code,
                            weight_kg=weight_kg,
                            dimensions_cm=dimensions_cm,
                            zones=zones
                        )
                        
                        if rate_info:
                            # Apply optimization scoring
                            score = await self._calculate_optimization_score(
                                rate_info=rate_info,
                                priority=priority,
                                max_cost=max_cost,
                                required_delivery_date=required_delivery_date
                            )
                            
                            options.append({
                                "carrier": carrier.carrier.value,
                                "carrier_name": carrier.carrier_name,
                                "method": method.value,
                                "cost": rate_info["total_cost"],
                                "estimated_delivery": rate_info["estimated_delivery"],
                                "delivery_days": rate_info["delivery_days"],
                                "service_features": rate_info["service_features"],
                                "optimization_score": score,
                                "cost_breakdown": rate_info["cost_breakdown"]
                            })
                    except Exception as e:
                        logger.warning(f"Failed to calculate rate for {carrier.carrier}/{method}: {str(e)}")
                        continue
        
        if not options:
            raise ValueError("No shipping options available")
        
        # Sort by optimization score (higher is better)
        options.sort(key=lambda x: x["optimization_score"], reverse=True)
        
        # Return optimization results
        return {
            "recommended_option": options[0],
            "all_options": options,
            "savings_analysis": self._analyze_cost_savings(options),
            "optimization_factors": {
                "priority_weight": self._get_priority_weight(priority),
                "cost_sensitivity": 0.4,
                "time_sensitivity": 0.3,
                "reliability_weight": 0.3
            }
        }

    async def optimize_bulk_shipments(
        self,
        organization_id: OrganizationId,
        shipments_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Optimize multiple shipments for cost and efficiency."""
        
        if not shipments_data:
            return {"optimized_shipments": [], "total_savings": 0}
        
        carriers = await self._get_available_carriers(organization_id)
        zones = await self._get_shipping_zones(organization_id)
        
        optimized_shipments = []
        total_original_cost = 0
        total_optimized_cost = 0
        
        # Group shipments by destination zones for bulk optimization
        zone_groups = await self._group_shipments_by_zone(shipments_data, zones)
        
        for group_key, group_shipments in zone_groups.items():
            group_optimization = await self._optimize_shipment_group(
                group_shipments, carriers, zones
            )
            
            optimized_shipments.extend(group_optimization["shipments"])
            total_original_cost += group_optimization["original_cost"]
            total_optimized_cost += group_optimization["optimized_cost"]
        
        total_savings = total_original_cost - total_optimized_cost
        savings_percentage = (total_savings / total_original_cost * 100) if total_original_cost > 0 else 0
        
        return {
            "optimized_shipments": optimized_shipments,
            "optimization_summary": {
                "total_shipments": len(shipments_data),
                "original_total_cost": total_original_cost,
                "optimized_total_cost": total_optimized_cost,
                "total_savings": total_savings,
                "savings_percentage": round(savings_percentage, 2)
            },
            "recommendations": self._generate_bulk_recommendations(optimized_shipments)
        }

    async def analyze_shipping_patterns(
        self,
        organization_id: OrganizationId,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Analyze shipping patterns to identify optimization opportunities."""
        
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Get historical shipments
        result = await self.db.execute(
            select(Shipment)
            .where(
                and_(
                    Shipment.organization_id == organization_id,
                    Shipment.created_at >= start_date
                )
            )
        )
        shipments = list(result.scalars().all())
        
        if not shipments:
            return {"message": "No historical data available for analysis"}
        
        # Analyze patterns
        patterns = {
            "route_analysis": self._analyze_routes(shipments),
            "carrier_performance": await self._analyze_carrier_performance(shipments),
            "cost_analysis": self._analyze_cost_patterns(shipments),
            "delivery_performance": self._analyze_delivery_patterns(shipments),
            "optimization_opportunities": []
        }
        
        # Identify optimization opportunities
        opportunities = await self._identify_optimization_opportunities(patterns, organization_id)
        patterns["optimization_opportunities"] = opportunities
        
        return patterns

    async def get_rate_predictions(
        self,
        organization_id: OrganizationId,
        from_postal_code: str,
        to_postal_code: str,
        weight_kg: float,
        dimensions_cm: Dict[str, float],
        future_date: datetime
    ) -> Dict[str, Any]:
        """Predict shipping rates for future dates based on historical data."""
        
        # Get historical rates for this route
        historical_rates = await self._get_historical_rates(
            organization_id, from_postal_code, to_postal_code
        )
        
        # Calculate current rates
        current_options = await self.optimize_shipping_selection(
            organization_id=organization_id,
            from_postal_code=from_postal_code,
            to_postal_code=to_postal_code,
            weight_kg=weight_kg,
            dimensions_cm=dimensions_cm
        )
        
        # Apply prediction algorithms
        predictions = []
        for option in current_options["all_options"]:
            predicted_cost = await self._predict_rate_change(
                historical_rates=historical_rates,
                current_rate=option["cost"],
                carrier=option["carrier"],
                future_date=future_date
            )
            
            predictions.append({
                "carrier": option["carrier"],
                "method": option["method"],
                "current_cost": option["cost"],
                "predicted_cost": predicted_cost,
                "cost_change": predicted_cost - option["cost"],
                "cost_change_percentage": ((predicted_cost - option["cost"]) / option["cost"] * 100) if option["cost"] > 0 else 0,
                "confidence_level": self._calculate_prediction_confidence(historical_rates, option["carrier"])
            })
        
        return {
            "predictions": predictions,
            "prediction_date": future_date,
            "recommendation": "Consider booking now" if any(p["cost_change"] > 0 for p in predictions) else "Rates may improve",
            "factors_considered": [
                "Historical rate trends",
                "Seasonal patterns",
                "Carrier-specific factors",
                "Market conditions"
            ]
        }

    # Private helper methods

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
        )
        
        return list(result.scalars().all())

    async def _get_shipping_zones(self, organization_id: OrganizationId) -> List[ShippingZone]:
        """Get shipping zones for optimization."""
        
        result = await self.db.execute(
            select(ShippingZone)
            .where(
                and_(
                    ShippingZone.organization_id == organization_id,
                    ShippingZone.is_active == True
                )
            )
        )
        
        return list(result.scalars().all())

    async def _calculate_optimized_rate(
        self,
        carrier: CarrierConfiguration,
        shipping_method: ShippingMethod,
        from_postal_code: str,
        to_postal_code: str,
        weight_kg: float,
        dimensions_cm: Dict[str, float],
        zones: List[ShippingZone]
    ) -> Optional[Dict[str, Any]]:
        """Calculate optimized shipping rate."""
        
        # Check carrier constraints
        if carrier.max_weight_kg and weight_kg > carrier.max_weight_kg:
            return None
        
        # Find applicable zone
        zone = self._find_applicable_zone(to_postal_code, zones)
        
        # Calculate base costs
        base_rate = zone.base_rate if zone else carrier.base_rate
        weight_rate = zone.per_kg_rate if zone else carrier.weight_rate
        
        # Calculate dimensional weight
        dim_weight = self._calculate_dimensional_weight(dimensions_cm)
        billable_weight = max(weight_kg, dim_weight)
        
        # Apply method multipliers
        method_multipliers = {
            ShippingMethod.STANDARD: 1.0,
            ShippingMethod.EXPRESS: 1.5,
            ShippingMethod.OVERNIGHT: 2.0,
            ShippingMethod.SAME_DAY: 3.0
        }
        multiplier = method_multipliers.get(shipping_method, 1.0)
        
        # Calculate distance-based pricing
        distance_cost = await self._calculate_distance_cost(
            from_postal_code, to_postal_code, carrier.distance_rate
        )
        
        # Calculate total cost
        weight_cost = billable_weight * weight_rate
        total_cost = (base_rate + weight_cost + distance_cost) * multiplier
        
        # Apply minimum charge if zone has one
        if zone and zone.minimum_charge:
            total_cost = max(total_cost, zone.minimum_charge)
        
        # Estimate delivery time
        delivery_days = self._estimate_delivery_days(shipping_method, zone)
        estimated_delivery = datetime.now() + timedelta(days=delivery_days)
        
        return {
            "total_cost": round(total_cost, 2),
            "cost_breakdown": {
                "base_rate": base_rate,
                "weight_cost": weight_cost,
                "distance_cost": distance_cost,
                "method_multiplier": multiplier,
                "billable_weight": billable_weight
            },
            "delivery_days": delivery_days,
            "estimated_delivery": estimated_delivery,
            "service_features": self._get_service_features(carrier, shipping_method, zone)
        }

    async def _calculate_optimization_score(
        self,
        rate_info: Dict[str, Any],
        priority: DeliveryPriority,
        max_cost: Optional[float],
        required_delivery_date: Optional[datetime]
    ) -> float:
        """Calculate optimization score for a shipping option."""
        
        score = 0.0
        
        # Cost factor (40% weight)
        cost = rate_info["total_cost"]
        if max_cost:
            if cost <= max_cost:
                cost_score = (max_cost - cost) / max_cost * 40
            else:
                cost_score = -20  # Penalty for exceeding budget
        else:
            # Normalize cost score (lower cost = higher score)
            cost_score = max(0, 40 - (cost / 100))
        
        score += cost_score
        
        # Time factor (30% weight)
        delivery_days = rate_info["delivery_days"]
        priority_weight = self._get_priority_weight(priority)
        
        if required_delivery_date:
            days_until_required = (required_delivery_date - datetime.now()).days
            if delivery_days <= days_until_required:
                time_score = 30
            else:
                time_score = -30  # Penalty for late delivery
        else:
            # Score based on speed and priority
            time_score = max(0, 30 - (delivery_days * priority_weight))
        
        score += time_score
        
        # Service features factor (20% weight)
        features = rate_info.get("service_features", [])
        feature_score = min(20, len(features) * 4)
        score += feature_score
        
        # Reliability factor (10% weight) - placeholder
        reliability_score = 10  # Would be based on historical carrier performance
        score += reliability_score
        
        return max(0, score)

    def _get_priority_weight(self, priority: DeliveryPriority) -> float:
        """Get priority weight for optimization scoring."""
        
        weights = {
            DeliveryPriority.LOW: 0.5,
            DeliveryPriority.NORMAL: 1.0,
            DeliveryPriority.HIGH: 2.0,
            DeliveryPriority.URGENT: 3.0,
            DeliveryPriority.CRITICAL: 5.0
        }
        
        return weights.get(priority, 1.0)

    def _analyze_cost_savings(self, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze potential cost savings from optimization."""
        
        if len(options) < 2:
            return {"potential_savings": 0, "savings_percentage": 0}
        
        cheapest = min(options, key=lambda x: x["cost"])
        most_expensive = max(options, key=lambda x: x["cost"])
        
        potential_savings = most_expensive["cost"] - cheapest["cost"]
        savings_percentage = (potential_savings / most_expensive["cost"] * 100) if most_expensive["cost"] > 0 else 0
        
        return {
            "potential_savings": round(potential_savings, 2),
            "savings_percentage": round(savings_percentage, 2),
            "cheapest_option": cheapest,
            "most_expensive_option": most_expensive
        }

    def _find_applicable_zone(self, postal_code: str, zones: List[ShippingZone]) -> Optional[ShippingZone]:
        """Find applicable shipping zone for postal code."""
        
        for zone in zones:
            if postal_code in zone.postal_codes:
                return zone
            
            # Check if postal code matches any patterns (simplified)
            for zone_postal in zone.postal_codes:
                if zone_postal.endswith('*') and postal_code.startswith(zone_postal[:-1]):
                    return zone
        
        return None

    def _calculate_dimensional_weight(self, dimensions_cm: Dict[str, float]) -> float:
        """Calculate dimensional weight."""
        
        length = dimensions_cm.get("length", 0)
        width = dimensions_cm.get("width", 0)
        height = dimensions_cm.get("height", 0)
        
        # Standard dimensional weight divisor for Japan (5000)
        dim_weight = (length * width * height) / 5000
        
        return max(dim_weight, 0)

    async def _calculate_distance_cost(
        self,
        from_postal_code: str,
        to_postal_code: str,
        distance_rate: float
    ) -> float:
        """Calculate distance-based cost."""
        
        # Simplified distance calculation
        # In a real implementation, this would use a mapping service
        
        # Estimate distance based on postal code differences (very simplified)
        try:
            from_num = int(''.join(filter(str.isdigit, from_postal_code)))
            to_num = int(''.join(filter(str.isdigit, to_postal_code)))
            estimated_distance = abs(from_num - to_num) / 1000  # Very rough estimate
        except (ValueError, ZeroDivisionError):
            estimated_distance = 100  # Default distance
        
        return estimated_distance * distance_rate

    def _estimate_delivery_days(
        self,
        shipping_method: ShippingMethod,
        zone: Optional[ShippingZone]
    ) -> int:
        """Estimate delivery days."""
        
        if zone:
            if shipping_method == ShippingMethod.SAME_DAY and zone.same_day_available:
                return 0
            elif shipping_method == ShippingMethod.EXPRESS:
                return zone.express_delivery_days
            else:
                return zone.standard_delivery_days
        
        # Default estimates
        default_days = {
            ShippingMethod.SAME_DAY: 0,
            ShippingMethod.OVERNIGHT: 1,
            ShippingMethod.EXPRESS: 2,
            ShippingMethod.STANDARD: 3
        }
        
        return default_days.get(shipping_method, 3)

    def _get_service_features(
        self,
        carrier: CarrierConfiguration,
        shipping_method: ShippingMethod,
        zone: Optional[ShippingZone]
    ) -> List[str]:
        """Get service features for carrier/method/zone combination."""
        
        features = ["tracking", "insurance_available"]
        
        if carrier.carrier == ShippingCarrier.YAMATO:
            features.extend(["signature_service", "time_definite"])
        elif carrier.carrier == ShippingCarrier.SAGAWA:
            features.extend(["business_delivery", "large_item_handling"])
        elif carrier.carrier == ShippingCarrier.JAPAN_POST:
            features.extend(["postal_network", "international_capability"])
        
        if shipping_method in [ShippingMethod.EXPRESS, ShippingMethod.OVERNIGHT]:
            features.append("priority_handling")
        
        if zone and zone.same_day_available and shipping_method == ShippingMethod.SAME_DAY:
            features.append("same_day_delivery")
        
        return features

    async def _group_shipments_by_zone(
        self,
        shipments_data: List[Dict[str, Any]],
        zones: List[ShippingZone]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group shipments by destination zones for bulk optimization."""
        
        groups = {}
        
        for shipment in shipments_data:
            to_postal = shipment.get("to_postal_code", "")
            zone = self._find_applicable_zone(to_postal, zones)
            
            zone_key = zone.zone_code if zone else "default"
            
            if zone_key not in groups:
                groups[zone_key] = []
            
            groups[zone_key].append(shipment)
        
        return groups

    async def _optimize_shipment_group(
        self,
        group_shipments: List[Dict[str, Any]],
        carriers: List[CarrierConfiguration],
        zones: List[ShippingZone]
    ) -> Dict[str, Any]:
        """Optimize a group of shipments."""
        
        optimized_shipments = []
        original_cost = 0
        optimized_cost = 0
        
        for shipment in group_shipments:
            # Calculate best option for this shipment
            best_option = None
            best_score = 0
            
            for carrier in carriers:
                try:
                    rate_info = await self._calculate_optimized_rate(
                        carrier=carrier,
                        shipping_method=ShippingMethod.STANDARD,  # Default for bulk
                        from_postal_code=shipment.get("from_postal_code", ""),
                        to_postal_code=shipment.get("to_postal_code", ""),
                        weight_kg=shipment.get("weight_kg", 1.0),
                        dimensions_cm=shipment.get("dimensions_cm", {"length": 30, "width": 20, "height": 10}),
                        zones=zones
                    )
                    
                    if rate_info:
                        score = rate_info["total_cost"] * -1  # Negative because we want lowest cost
                        if score > best_score:
                            best_score = score
                            best_option = {
                                "carrier": carrier.carrier.value,
                                "cost": rate_info["total_cost"],
                                "estimated_delivery": rate_info["estimated_delivery"]
                            }
                except Exception as e:
                    logger.warning(f"Failed to calculate rate for bulk shipment: {str(e)}")
                    continue
            
            if best_option:
                optimized_shipments.append({
                    **shipment,
                    "recommended_carrier": best_option["carrier"],
                    "optimized_cost": best_option["cost"],
                    "estimated_delivery": best_option["estimated_delivery"]
                })
                
                # Assume original cost would be 20% higher (simplified)
                original_shipment_cost = best_option["cost"] * 1.2
                original_cost += original_shipment_cost
                optimized_cost += best_option["cost"]
        
        return {
            "shipments": optimized_shipments,
            "original_cost": original_cost,
            "optimized_cost": optimized_cost
        }

    def _generate_bulk_recommendations(self, optimized_shipments: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for bulk shipment optimization."""
        
        recommendations = []
        
        # Carrier distribution analysis
        carrier_counts = {}
        for shipment in optimized_shipments:
            carrier = shipment.get("recommended_carrier", "unknown")
            carrier_counts[carrier] = carrier_counts.get(carrier, 0) + 1
        
        if len(carrier_counts) > 3:
            recommendations.append("Consider consolidating shipments with fewer carriers for better rates")
        
        # Weight consolidation opportunities
        light_shipments = [s for s in optimized_shipments if s.get("weight_kg", 0) < 5]
        if len(light_shipments) > 5:
            recommendations.append("Consider consolidating light shipments to reduce per-unit costs")
        
        # Route optimization
        destinations = set(s.get("to_postal_code", "") for s in optimized_shipments)
        if len(destinations) < len(optimized_shipments) * 0.7:
            recommendations.append("Route optimization could reduce costs for shipments to similar destinations")
        
        return recommendations

    def _analyze_routes(self, shipments: List[Shipment]) -> Dict[str, Any]:
        """Analyze shipping routes for patterns."""
        
        routes = {}
        for shipment in shipments:
            from_code = shipment.from_address.postal_code if shipment.from_address else "unknown"
            to_code = shipment.to_address.postal_code if shipment.to_address else "unknown"
            route_key = f"{from_code}-{to_code}"
            
            if route_key not in routes:
                routes[route_key] = {
                    "count": 0,
                    "total_cost": 0,
                    "avg_weight": 0,
                    "carriers_used": set()
                }
            
            routes[route_key]["count"] += 1
            routes[route_key]["total_cost"] += shipment.total_cost or 0
            routes[route_key]["avg_weight"] += shipment.weight_kg
            if shipment.carrier_config:
                routes[route_key]["carriers_used"].add(shipment.carrier_config.carrier.value)
        
        # Convert sets to lists for JSON serialization
        for route_data in routes.values():
            route_data["carriers_used"] = list(route_data["carriers_used"])
            if route_data["count"] > 0:
                route_data["avg_cost"] = route_data["total_cost"] / route_data["count"]
                route_data["avg_weight"] = route_data["avg_weight"] / route_data["count"]
        
        # Find top routes
        top_routes = sorted(routes.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
        
        return {
            "total_routes": len(routes),
            "top_routes": dict(top_routes),
            "route_diversity": len(routes) / len(shipments) if shipments else 0
        }

    async def _analyze_carrier_performance(self, shipments: List[Shipment]) -> Dict[str, Any]:
        """Analyze carrier performance."""
        
        carrier_stats = {}
        
        for shipment in shipments:
            if not shipment.carrier_config:
                continue
                
            carrier = shipment.carrier_config.carrier.value
            if carrier not in carrier_stats:
                carrier_stats[carrier] = {
                    "shipment_count": 0,
                    "total_cost": 0,
                    "on_time_deliveries": 0,
                    "late_deliveries": 0,
                    "avg_delivery_days": 0,
                    "total_delivery_days": 0
                }
            
            stats = carrier_stats[carrier]
            stats["shipment_count"] += 1
            stats["total_cost"] += shipment.total_cost or 0
            
            # Calculate delivery performance
            if shipment.actual_delivery and shipment.estimated_delivery:
                if shipment.actual_delivery <= shipment.estimated_delivery:
                    stats["on_time_deliveries"] += 1
                else:
                    stats["late_deliveries"] += 1
                
                delivery_days = (shipment.actual_delivery - shipment.created_at).days
                stats["total_delivery_days"] += delivery_days
        
        # Calculate averages
        for carrier, stats in carrier_stats.items():
            if stats["shipment_count"] > 0:
                stats["avg_cost"] = stats["total_cost"] / stats["shipment_count"]
                stats["on_time_rate"] = (stats["on_time_deliveries"] / 
                                       (stats["on_time_deliveries"] + stats["late_deliveries"]) * 100
                                       if (stats["on_time_deliveries"] + stats["late_deliveries"]) > 0 else 0)
                stats["avg_delivery_days"] = (stats["total_delivery_days"] / stats["shipment_count"]
                                            if stats["total_delivery_days"] > 0 else 0)
        
        return carrier_stats

    def _analyze_cost_patterns(self, shipments: List[Shipment]) -> Dict[str, Any]:
        """Analyze cost patterns."""
        
        costs = [s.total_cost for s in shipments if s.total_cost]
        
        if not costs:
            return {"message": "No cost data available"}
        
        return {
            "total_cost": sum(costs),
            "avg_cost": sum(costs) / len(costs),
            "min_cost": min(costs),
            "max_cost": max(costs),
            "cost_variance": self._calculate_variance(costs),
            "high_cost_threshold": sum(costs) / len(costs) * 1.5,
            "cost_distribution": self._analyze_cost_distribution(costs)
        }

    def _analyze_delivery_patterns(self, shipments: List[Shipment]) -> Dict[str, Any]:
        """Analyze delivery patterns."""
        
        delivered = [s for s in shipments if s.actual_delivery]
        
        if not delivered:
            return {"message": "No delivery data available"}
        
        delivery_days = []
        for shipment in delivered:
            days = (shipment.actual_delivery - shipment.created_at).days
            delivery_days.append(days)
        
        return {
            "total_delivered": len(delivered),
            "avg_delivery_days": sum(delivery_days) / len(delivery_days) if delivery_days else 0,
            "min_delivery_days": min(delivery_days) if delivery_days else 0,
            "max_delivery_days": max(delivery_days) if delivery_days else 0,
            "delivery_consistency": 100 - (self._calculate_variance(delivery_days) / 
                                         (sum(delivery_days) / len(delivery_days)) * 100
                                         if delivery_days and sum(delivery_days) > 0 else 0)
        }

    async def _identify_optimization_opportunities(
        self,
        patterns: Dict[str, Any],
        organization_id: OrganizationId
    ) -> List[Dict[str, Any]]:
        """Identify optimization opportunities based on patterns."""
        
        opportunities = []
        
        # High-volume route optimization
        route_analysis = patterns.get("route_analysis", {})
        top_routes = route_analysis.get("top_routes", {})
        
        for route, data in top_routes.items():
            if data["count"] > 10 and len(data["carriers_used"]) > 1:
                opportunities.append({
                    "type": "route_consolidation",
                    "description": f"Route {route} uses multiple carriers - consolidation could save costs",
                    "potential_impact": "medium",
                    "shipment_count": data["count"]
                })
        
        # Carrier performance opportunities
        carrier_performance = patterns.get("carrier_performance", {})
        for carrier, stats in carrier_performance.items():
            if stats.get("on_time_rate", 0) < 80:
                opportunities.append({
                    "type": "carrier_reliability",
                    "description": f"Carrier {carrier} has low on-time rate ({stats.get('on_time_rate', 0):.1f}%)",
                    "potential_impact": "high",
                    "affected_shipments": stats["shipment_count"]
                })
        
        # Cost optimization opportunities
        cost_analysis = patterns.get("cost_analysis", {})
        if cost_analysis.get("cost_variance", 0) > cost_analysis.get("avg_cost", 0):
            opportunities.append({
                "type": "cost_standardization",
                "description": "High cost variance indicates potential for rate negotiation",
                "potential_impact": "medium",
                "current_variance": cost_analysis.get("cost_variance", 0)
            })
        
        return opportunities

    async def _get_historical_rates(
        self,
        organization_id: OrganizationId,
        from_postal_code: str,
        to_postal_code: str
    ) -> List[ShippingRate]:
        """Get historical shipping rates for a route."""
        
        result = await self.db.execute(
            select(ShippingRate)
            .where(
                and_(
                    ShippingRate.organization_id == organization_id,
                    ShippingRate.from_postal_code == from_postal_code,
                    ShippingRate.to_postal_code == to_postal_code,
                    ShippingRate.is_valid == True
                )
            )
            .order_by(ShippingRate.created_at.desc())
            .limit(50)
        )
        
        return list(result.scalars().all())

    async def _predict_rate_change(
        self,
        historical_rates: List[ShippingRate],
        current_rate: float,
        carrier: str,
        future_date: datetime
    ) -> float:
        """Predict rate change based on historical data."""
        
        if not historical_rates:
            return current_rate
        
        # Simple trend analysis
        carrier_rates = [r for r in historical_rates if r.carrier.value == carrier]
        
        if len(carrier_rates) < 2:
            return current_rate
        
        # Calculate trend
        recent_rates = carrier_rates[:10]  # Last 10 rates
        older_rates = carrier_rates[10:20] if len(carrier_rates) > 10 else []
        
        if not older_rates:
            return current_rate
        
        recent_avg = sum(r.total_rate for r in recent_rates) / len(recent_rates)
        older_avg = sum(r.total_rate for r in older_rates) / len(older_rates)
        
        trend_rate = (recent_avg - older_avg) / len(recent_rates)
        
        # Apply trend to future prediction
        days_ahead = (future_date - datetime.now()).days
        predicted_change = trend_rate * days_ahead
        
        return max(0, current_rate + predicted_change)

    def _calculate_prediction_confidence(
        self,
        historical_rates: List[ShippingRate],
        carrier: str
    ) -> float:
        """Calculate confidence level for rate prediction."""
        
        carrier_rates = [r for r in historical_rates if r.carrier.value == carrier]
        
        if len(carrier_rates) < 5:
            return 0.3  # Low confidence
        elif len(carrier_rates) < 20:
            return 0.6  # Medium confidence
        else:
            return 0.8  # High confidence

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        
        if not values:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        return variance

    def _analyze_cost_distribution(self, costs: List[float]) -> Dict[str, int]:
        """Analyze cost distribution in ranges."""
        
        ranges = {
            "0-1000": 0,
            "1000-3000": 0,
            "3000-5000": 0,
            "5000-10000": 0,
            "10000+": 0
        }
        
        for cost in costs:
            if cost < 1000:
                ranges["0-1000"] += 1
            elif cost < 3000:
                ranges["1000-3000"] += 1
            elif cost < 5000:
                ranges["3000-5000"] += 1
            elif cost < 10000:
                ranges["5000-10000"] += 1
            else:
                ranges["10000+"] += 1
        
        return ranges