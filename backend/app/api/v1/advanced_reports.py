"""
Advanced Reporting API for Core ERP System
Business intelligence and analytics endpoints
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

# Import the stores from other modules
from app.api.v1.simple_products import products_store
from app.api.v1.simple_inventory import inventory_store, movements_store

router = APIRouter(prefix="/reports", tags=["Advanced Reports"])

class ProductPerformanceReport(BaseModel):
    """Product performance analytics."""
    product_code: str
    product_name: str
    category: str
    total_movements: int
    total_quantity_moved: float
    current_stock: float
    stock_value: float
    performance_score: float

class InventoryTurnoverReport(BaseModel):
    """Inventory turnover analytics."""
    warehouse: str
    total_items: int
    total_value: float
    total_movements: int
    turnover_rate: float
    slow_moving_items: int
    fast_moving_items: int

class CategoryAnalysisReport(BaseModel):
    """Category performance analysis."""
    category: str
    product_count: int
    total_value: float
    avg_price: float
    stock_movements: int
    category_performance: str

class WarehouseEfficiencyReport(BaseModel):
    """Warehouse efficiency metrics."""
    warehouse: str
    total_items: int
    total_value: float
    space_utilization: float
    movement_frequency: int
    efficiency_score: float

@router.get("/product-performance", response_model=List[ProductPerformanceReport])
async def get_product_performance_report(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Limit results")
) -> List[ProductPerformanceReport]:
    """Generate comprehensive product performance report."""
    
    reports = []
    
    for product_data in products_store.values():
        if not product_data["is_active"]:
            continue
            
        if category and product_data.get("category") != category:
            continue
        
        # Find related inventory items
        product_inventory = [
            item for item in inventory_store.values() 
            if item["product_code"] == product_data["code"] and item["is_active"]
        ]
        
        # Calculate movement statistics
        total_movements = 0
        total_quantity_moved = 0.0
        current_stock = 0.0
        stock_value = 0.0
        
        for inv_item in product_inventory:
            current_stock += inv_item["quantity_on_hand"]
            if inv_item.get("unit_cost"):
                stock_value += inv_item["quantity_on_hand"] * inv_item["unit_cost"]
            
            # Count movements for this inventory item
            item_movements = [
                mov for mov in movements_store.values()
                if mov["inventory_item_id"] == inv_item["id"]
            ]
            total_movements += len(item_movements)
            total_quantity_moved += sum(abs(mov["quantity"]) for mov in item_movements)
        
        # Calculate performance score (movements per unit of stock)
        performance_score = (
            (total_quantity_moved / max(current_stock, 1)) * 100
            if current_stock > 0 else 0
        )
        
        reports.append(ProductPerformanceReport(
            product_code=product_data["code"],
            product_name=product_data["name"],
            category=product_data.get("category", "Uncategorized"),
            total_movements=total_movements,
            total_quantity_moved=total_quantity_moved,
            current_stock=current_stock,
            stock_value=round(stock_value, 2),
            performance_score=round(performance_score, 2)
        ))
    
    # Sort by performance score descending
    reports.sort(key=lambda x: x.performance_score, reverse=True)
    
    return reports[:limit]

@router.get("/inventory-turnover", response_model=List[InventoryTurnoverReport])
async def get_inventory_turnover_report() -> List[InventoryTurnoverReport]:
    """Generate inventory turnover analysis by warehouse."""
    
    warehouse_data = {}
    
    # Aggregate data by warehouse
    for inv_item in inventory_store.values():
        if not inv_item["is_active"]:
            continue
            
        warehouse = inv_item["warehouse"]
        if warehouse not in warehouse_data:
            warehouse_data[warehouse] = {
                "items": [],
                "movements": [],
                "total_value": 0.0
            }
        
        warehouse_data[warehouse]["items"].append(inv_item)
        
        # Calculate value
        if inv_item.get("unit_cost"):
            value = inv_item["quantity_on_hand"] * inv_item["unit_cost"]
            warehouse_data[warehouse]["total_value"] += value
        
        # Get movements for this item
        item_movements = [
            mov for mov in movements_store.values()
            if mov["inventory_item_id"] == inv_item["id"]
        ]
        warehouse_data[warehouse]["movements"].extend(item_movements)
    
    reports = []
    
    for warehouse, data in warehouse_data.items():
        total_items = len(data["items"])
        total_movements = len(data["movements"])
        total_value = data["total_value"]
        
        # Calculate turnover rate (movements per item)
        turnover_rate = total_movements / max(total_items, 1)
        
        # Classify items as slow/fast moving
        slow_moving = 0
        fast_moving = 0
        
        for item in data["items"]:
            item_movements = [
                mov for mov in data["movements"]
                if mov["inventory_item_id"] == item["id"]
            ]
            movement_count = len(item_movements)
            
            if movement_count == 0:
                slow_moving += 1
            elif movement_count >= 2:
                fast_moving += 1
        
        reports.append(InventoryTurnoverReport(
            warehouse=warehouse,
            total_items=total_items,
            total_value=round(total_value, 2),
            total_movements=total_movements,
            turnover_rate=round(turnover_rate, 2),
            slow_moving_items=slow_moving,
            fast_moving_items=fast_moving
        ))
    
    return reports

@router.get("/category-analysis", response_model=List[CategoryAnalysisReport])
async def get_category_analysis_report() -> List[CategoryAnalysisReport]:
    """Generate category performance analysis."""
    
    category_data = {}
    
    # Aggregate products by category
    for product_data in products_store.values():
        if not product_data["is_active"]:
            continue
            
        category = product_data.get("category", "Uncategorized")
        if category not in category_data:
            category_data[category] = {
                "products": [],
                "total_value": 0.0,
                "movements": 0
            }
        
        category_data[category]["products"].append(product_data)
        category_data[category]["total_value"] += product_data["price"]
        
        # Count stock movements for this product
        product_movements = 0
        for inv_item in inventory_store.values():
            if inv_item["product_code"] == product_data["code"]:
                item_movements = [
                    mov for mov in movements_store.values()
                    if mov["inventory_item_id"] == inv_item["id"]
                ]
                product_movements += len(item_movements)
        
        category_data[category]["movements"] += product_movements
    
    reports = []
    
    for category, data in category_data.items():
        product_count = len(data["products"])
        total_value = data["total_value"]
        avg_price = total_value / max(product_count, 1)
        stock_movements = data["movements"]
        
        # Determine performance level
        if stock_movements >= 3:
            performance = "High"
        elif stock_movements >= 1:
            performance = "Medium"
        else:
            performance = "Low"
        
        reports.append(CategoryAnalysisReport(
            category=category,
            product_count=product_count,
            total_value=round(total_value, 2),
            avg_price=round(avg_price, 2),
            stock_movements=stock_movements,
            category_performance=performance
        ))
    
    # Sort by stock movements descending
    reports.sort(key=lambda x: x.stock_movements, reverse=True)
    
    return reports

@router.get("/warehouse-efficiency", response_model=List[WarehouseEfficiencyReport])
async def get_warehouse_efficiency_report() -> List[WarehouseEfficiencyReport]:
    """Generate warehouse efficiency analysis."""
    
    warehouse_metrics = {}
    
    # Calculate metrics per warehouse
    for inv_item in inventory_store.values():
        if not inv_item["is_active"]:
            continue
            
        warehouse = inv_item["warehouse"]
        if warehouse not in warehouse_metrics:
            warehouse_metrics[warehouse] = {
                "items": 0,
                "total_value": 0.0,
                "movements": 0,
                "locations": set()
            }
        
        metrics = warehouse_metrics[warehouse]
        metrics["items"] += 1
        
        if inv_item.get("unit_cost"):
            metrics["total_value"] += inv_item["quantity_on_hand"] * inv_item["unit_cost"]
        
        if inv_item.get("location"):
            metrics["locations"].add(inv_item["location"])
        
        # Count movements
        item_movements = [
            mov for mov in movements_store.values()
            if mov["inventory_item_id"] == inv_item["id"]
        ]
        metrics["movements"] += len(item_movements)
    
    reports = []
    
    for warehouse, metrics in warehouse_metrics.items():
        total_items = metrics["items"]
        total_value = metrics["total_value"]
        movement_frequency = metrics["movements"]
        unique_locations = len(metrics["locations"])
        
        # Calculate space utilization (based on unique locations)
        max_locations = 100  # Assume max 100 locations per warehouse
        space_utilization = (unique_locations / max_locations) * 100
        
        # Calculate efficiency score
        efficiency_components = [
            min(movement_frequency / max(total_items, 1) * 25, 25),  # Movement efficiency (max 25%)
            min(space_utilization, 25),  # Space utilization (max 25%)
            min(total_items * 2, 25),  # Item density (max 25%)
            min(total_value / 1000, 25)  # Value efficiency (max 25%)
        ]
        efficiency_score = sum(efficiency_components)
        
        reports.append(WarehouseEfficiencyReport(
            warehouse=warehouse,
            total_items=total_items,
            total_value=round(total_value, 2),
            space_utilization=round(space_utilization, 2),
            movement_frequency=movement_frequency,
            efficiency_score=round(efficiency_score, 2)
        ))
    
    # Sort by efficiency score descending
    reports.sort(key=lambda x: x.efficiency_score, reverse=True)
    
    return reports

@router.get("/executive-dashboard")
async def get_executive_dashboard() -> Dict[str, Any]:
    """Generate executive dashboard with key metrics."""
    
    # Product metrics
    total_products = len([p for p in products_store.values() if p["is_active"]])
    categories = len(set(p.get("category", "Uncategorized") for p in products_store.values() if p["is_active"]))
    
    # Inventory metrics  
    total_inventory_items = len([i for i in inventory_store.values() if i["is_active"]])
    total_inventory_value = sum(
        i["quantity_on_hand"] * (i.get("unit_cost", 0) or 0)
        for i in inventory_store.values() if i["is_active"]
    )
    
    # Movement metrics
    total_movements = len(movements_store)
    recent_movements = len([
        m for m in movements_store.values()
        if datetime.fromisoformat(m["created_at"].replace('Z', '+00:00')).date() == date.today()
    ])
    
    # Warehouse metrics
    warehouses = len(set(i["warehouse"] for i in inventory_store.values() if i["is_active"]))
    
    # Low stock alerts
    low_stock_count = sum(
        1 for i in inventory_store.values()
        if i["is_active"] and i.get("minimum_level") and i["quantity_available"] <= i["minimum_level"]
    )
    
    # Calculate trend indicators (simplified)
    movement_trend = "↑" if recent_movements > 0 else "→"
    inventory_trend = "↑" if total_inventory_value > 5000 else "→"
    
    return {
        "generated_at": datetime.now().isoformat(),
        "business_overview": {
            "total_products": total_products,
            "product_categories": categories,
            "total_inventory_items": total_inventory_items,
            "warehouse_count": warehouses
        },
        "financial_metrics": {
            "total_inventory_value": round(total_inventory_value, 2),
            "inventory_trend": inventory_trend,
            "avg_item_value": round(total_inventory_value / max(total_inventory_items, 1), 2)
        },
        "operational_metrics": {
            "total_movements": total_movements,
            "recent_movements": recent_movements,
            "movement_trend": movement_trend,
            "low_stock_alerts": low_stock_count
        },
        "performance_indicators": {
            "inventory_efficiency": round((total_movements / max(total_inventory_items, 1)) * 100, 2),
            "category_diversity": round((categories / max(total_products, 1)) * 100, 2),
            "warehouse_utilization": round((total_inventory_items / max(warehouses, 1)), 2)
        },
        "alerts_summary": {
            "critical_alerts": low_stock_count,
            "warning_alerts": 0,
            "info_alerts": recent_movements
        }
    }

@router.get("/monthly-trends")
async def get_monthly_trends(
    months_back: int = Query(3, ge=1, le=12, description="Months to analyze")
) -> Dict[str, Any]:
    """Generate monthly trend analysis."""
    
    # Since we're using in-memory storage, we'll simulate monthly data
    # In a real system, this would query historical data
    
    current_date = datetime.now()
    monthly_data = []
    
    for i in range(months_back):
        month_date = current_date - timedelta(days=30 * i)
        month_name = month_date.strftime("%B %Y")
        
        # Simulate monthly metrics based on current data
        base_products = len([p for p in products_store.values() if p["is_active"]])
        base_movements = len(movements_store)
        base_value = sum(
            i["quantity_on_hand"] * (i.get("unit_cost", 0) or 0)
            for i in inventory_store.values() if i["is_active"]
        )
        
        # Add some variation for demonstration
        variation_factor = 1.0 + (i * 0.1)  # Simulate growth
        
        monthly_data.append({
            "month": month_name,
            "products_count": max(1, int(base_products / variation_factor)),
            "movements_count": max(0, int(base_movements / variation_factor)),
            "inventory_value": round(base_value / variation_factor, 2),
            "new_products": max(0, int(base_products * 0.1 / variation_factor)),
            "stock_turnover": round(base_movements / max(base_products, 1) / variation_factor, 2)
        })
    
    # Reverse to show oldest first
    monthly_data.reverse()
    
    # Calculate trends
    if len(monthly_data) >= 2:
        latest = monthly_data[-1]
        previous = monthly_data[-2]
        
        product_growth = ((latest["products_count"] - previous["products_count"]) / max(previous["products_count"], 1)) * 100
        value_growth = ((latest["inventory_value"] - previous["inventory_value"]) / max(previous["inventory_value"], 1)) * 100
        movement_growth = ((latest["movements_count"] - previous["movements_count"]) / max(previous["movements_count"], 1)) * 100
    else:
        product_growth = value_growth = movement_growth = 0.0
    
    return {
        "analysis_period": f"Last {months_back} months",
        "generated_at": datetime.now().isoformat(),
        "monthly_data": monthly_data,
        "growth_metrics": {
            "product_growth_rate": round(product_growth, 2),
            "inventory_value_growth": round(value_growth, 2),
            "movement_growth_rate": round(movement_growth, 2)
        },
        "summary": {
            "total_months_analyzed": months_back,
            "avg_monthly_products": round(sum(m["products_count"] for m in monthly_data) / len(monthly_data), 1),
            "avg_monthly_movements": round(sum(m["movements_count"] for m in monthly_data) / len(monthly_data), 1),
            "avg_monthly_value": round(sum(m["inventory_value"] for m in monthly_data) / len(monthly_data), 2)
        }
    }