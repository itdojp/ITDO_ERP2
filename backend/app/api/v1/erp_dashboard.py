"""
ERP Dashboard API
Comprehensive dashboard with key metrics and insights
"""

import logging
from datetime import datetime, UTC, date, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_active_user, get_db
from app.core.tenant_deps import TenantDep, RequireApiAccess
from app.models.user import User
from app.models.organization import Organization
from app.models.product import Product
from app.models.sales import Customer, SalesOrder
from app.models.warehouse import InventoryItem, StockMovement

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/erp-dashboard", tags=["ERP Dashboard"])


# Pydantic schemas
class DashboardMetrics(BaseModel):
    """Core dashboard metrics"""
    total_customers: int
    active_customers: int
    total_products: int
    active_products: int
    total_orders: int
    pending_orders: int
    total_revenue: float
    monthly_revenue: float
    low_stock_items: int
    overdue_orders: int


class RevenueMetrics(BaseModel):
    """Revenue metrics with trends"""
    total_revenue: float
    monthly_revenue: float
    yearly_revenue: float
    revenue_growth: float  # Percentage change from previous period
    average_order_value: float
    revenue_by_month: List[Dict[str, Any]]


class InventoryMetrics(BaseModel):
    """Inventory metrics"""
    total_products: int
    total_stock_value: float
    low_stock_items: int
    out_of_stock_items: int
    expired_items: int
    near_expiry_items: int
    top_products_by_value: List[Dict[str, Any]]
    stock_movements_today: int


class CustomerMetrics(BaseModel):
    """Customer metrics"""
    total_customers: int
    active_customers: int
    new_customers_this_month: int
    top_customers_by_revenue: List[Dict[str, Any]]
    customer_growth_rate: float


class OrderMetrics(BaseModel):
    """Order metrics"""
    total_orders: int
    pending_orders: int
    processing_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int
    overdue_orders: int
    orders_by_status: Dict[str, int]
    recent_orders: List[Dict[str, Any]]


class ActivityFeed(BaseModel):
    """Recent activity feed"""
    timestamp: str
    activity_type: str  # order_created, stock_adjusted, customer_added, etc.
    description: str
    user_name: Optional[str]
    reference_id: Optional[int]
    reference_type: Optional[str]


class DashboardSummary(BaseModel):
    """Complete dashboard summary"""
    metrics: DashboardMetrics
    revenue: RevenueMetrics
    inventory: InventoryMetrics
    customers: CustomerMetrics
    orders: OrderMetrics
    recent_activities: List[ActivityFeed]
    alerts: List[Dict[str, Any]]
    last_updated: str


class AlertItem(BaseModel):
    """Dashboard alert item"""
    alert_type: str  # warning, error, info
    title: str
    message: str
    count: Optional[int]
    action_url: Optional[str]
    priority: int = 1  # 1=high, 2=medium, 3=low


# Dashboard Endpoints
@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    organization_id: Optional[int] = Query(None, description="Organization ID filter"),
    date_from: Optional[date] = Query(None, description="Start date for metrics"),
    date_to: Optional[date] = Query(None, description="End date for metrics"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get comprehensive dashboard summary"""
    try:
        # Set default date range if not provided
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=30)
        
        # Core metrics
        metrics = await _get_core_metrics(db, organization_id)
        
        # Revenue metrics
        revenue = await _get_revenue_metrics(db, organization_id, date_from, date_to)
        
        # Inventory metrics
        inventory = await _get_inventory_metrics(db, organization_id)
        
        # Customer metrics
        customers = await _get_customer_metrics(db, organization_id, date_from, date_to)
        
        # Order metrics
        orders = await _get_order_metrics(db, organization_id, date_from, date_to)
        
        # Recent activities
        recent_activities = await _get_recent_activities(db, organization_id, limit=10)
        
        # Alerts
        alerts = await _generate_alerts(db, organization_id)
        
        return DashboardSummary(
            metrics=metrics,
            revenue=revenue,
            inventory=inventory,
            customers=customers,
            orders=orders,
            recent_activities=recent_activities,
            alerts=alerts,
            last_updated=datetime.now(UTC).isoformat()
        )
    
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard summary"
        )


@router.get("/metrics", response_model=DashboardMetrics)
async def get_core_metrics(
    organization_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get core dashboard metrics"""
    try:
        return await _get_core_metrics(db, organization_id)
    except Exception as e:
        logger.error(f"Failed to get core metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve core metrics"
        )


@router.get("/revenue", response_model=RevenueMetrics)
async def get_revenue_metrics(
    organization_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get revenue metrics and trends"""
    try:
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=365)  # Full year for revenue trends
        
        return await _get_revenue_metrics(db, organization_id, date_from, date_to)
    except Exception as e:
        logger.error(f"Failed to get revenue metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve revenue metrics"
        )


@router.get("/activities", response_model=List[ActivityFeed])
async def get_recent_activities(
    organization_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    activity_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get recent system activities"""
    try:
        return await _get_recent_activities(db, organization_id, limit, activity_type)
    except Exception as e:
        logger.error(f"Failed to get recent activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent activities"
        )


@router.get("/alerts", response_model=List[AlertItem])
async def get_dashboard_alerts(
    organization_id: Optional[int] = Query(None),
    alert_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get dashboard alerts and warnings"""
    try:
        alerts = await _generate_alerts(db, organization_id)
        
        if alert_type:
            alerts = [alert for alert in alerts if alert["alert_type"] == alert_type]
        
        return alerts
    except Exception as e:
        logger.error(f"Failed to get dashboard alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard alerts"
        )


# Helper functions
async def _get_core_metrics(db: Session, organization_id: Optional[int]) -> DashboardMetrics:
    """Get core dashboard metrics"""
    # Customer metrics
    customer_query = db.query(Customer).filter(Customer.deleted_at.is_(None))
    if organization_id:
        customer_query = customer_query.filter(Customer.organization_id == organization_id)
    
    total_customers = customer_query.count()
    active_customers = customer_query.filter(Customer.is_active == True).count()
    
    # Product metrics
    product_query = db.query(Product).filter(Product.deleted_at.is_(None))
    if organization_id:
        product_query = product_query.filter(Product.organization_id == organization_id)
    
    total_products = product_query.count()
    active_products = product_query.filter(Product.is_active == True).count()
    
    # Order metrics
    order_query = db.query(SalesOrder).filter(SalesOrder.deleted_at.is_(None))
    if organization_id:
        order_query = order_query.filter(SalesOrder.organization_id == organization_id)
    
    total_orders = order_query.count()
    pending_orders = order_query.filter(SalesOrder.status.in_(["draft", "pending"])).count()
    
    # Revenue
    total_revenue = order_query.with_entities(func.sum(SalesOrder.total_amount)).scalar() or 0
    
    # Monthly revenue (current month)
    current_month_start = date.today().replace(day=1)
    monthly_revenue = order_query.filter(
        SalesOrder.order_date >= current_month_start
    ).with_entities(func.sum(SalesOrder.total_amount)).scalar() or 0
    
    # Inventory alerts
    inventory_query = db.query(InventoryItem).filter(InventoryItem.deleted_at.is_(None))
    if organization_id:
        inventory_query = inventory_query.filter(InventoryItem.organization_id == organization_id)
    
    low_stock_items = inventory_query.filter(
        InventoryItem.quantity_available <= InventoryItem.minimum_level
    ).count()
    
    # Overdue orders
    today = date.today()
    overdue_orders = order_query.filter(
        and_(
            SalesOrder.required_date < today,
            SalesOrder.status.not_in(["delivered", "cancelled", "refunded"])
        )
    ).count()
    
    return DashboardMetrics(
        total_customers=total_customers,
        active_customers=active_customers,
        total_products=total_products,
        active_products=active_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_revenue=float(total_revenue),
        monthly_revenue=float(monthly_revenue),
        low_stock_items=low_stock_items,
        overdue_orders=overdue_orders
    )


async def _get_revenue_metrics(
    db: Session,
    organization_id: Optional[int],
    date_from: date,
    date_to: date
) -> RevenueMetrics:
    """Get revenue metrics with trends"""
    order_query = db.query(SalesOrder).filter(
        and_(
            SalesOrder.deleted_at.is_(None),
            SalesOrder.order_date >= date_from,
            SalesOrder.order_date <= date_to
        )
    )
    
    if organization_id:
        order_query = order_query.filter(SalesOrder.organization_id == organization_id)
    
    # Current period revenue
    total_revenue = order_query.with_entities(func.sum(SalesOrder.total_amount)).scalar() or 0
    
    # Monthly revenue (current month)
    current_month_start = date.today().replace(day=1)
    monthly_revenue = order_query.filter(
        SalesOrder.order_date >= current_month_start
    ).with_entities(func.sum(SalesOrder.total_amount)).scalar() or 0
    
    # Yearly revenue
    year_start = date.today().replace(month=1, day=1)
    yearly_revenue = order_query.filter(
        SalesOrder.order_date >= year_start
    ).with_entities(func.sum(SalesOrder.total_amount)).scalar() or 0
    
    # Previous period for growth calculation
    period_days = (date_to - date_from).days
    prev_date_to = date_from - timedelta(days=1)
    prev_date_from = prev_date_to - timedelta(days=period_days)
    
    prev_revenue = db.query(SalesOrder).filter(
        and_(
            SalesOrder.deleted_at.is_(None),
            SalesOrder.order_date >= prev_date_from,
            SalesOrder.order_date <= prev_date_to
        )
    )
    
    if organization_id:
        prev_revenue = prev_revenue.filter(SalesOrder.organization_id == organization_id)
    
    prev_revenue = prev_revenue.with_entities(func.sum(SalesOrder.total_amount)).scalar() or 0
    
    # Growth calculation
    revenue_growth = 0.0
    if prev_revenue > 0:
        revenue_growth = ((float(total_revenue) - float(prev_revenue)) / float(prev_revenue)) * 100
    
    # Average order value
    order_count = order_query.count()
    average_order_value = float(total_revenue) / order_count if order_count > 0 else 0
    
    # Monthly revenue breakdown
    monthly_stats = order_query.with_entities(
        func.extract('year', SalesOrder.order_date).label('year'),
        func.extract('month', SalesOrder.order_date).label('month'),
        func.sum(SalesOrder.total_amount).label('revenue'),
        func.count(SalesOrder.id).label('orders')
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    revenue_by_month = [
        {
            "year": int(stat.year),
            "month": int(stat.month),
            "revenue": float(stat.revenue),
            "orders": stat.orders
        }
        for stat in monthly_stats
    ]
    
    return RevenueMetrics(
        total_revenue=float(total_revenue),
        monthly_revenue=float(monthly_revenue),
        yearly_revenue=float(yearly_revenue),
        revenue_growth=revenue_growth,
        average_order_value=average_order_value,
        revenue_by_month=revenue_by_month
    )


async def _get_inventory_metrics(db: Session, organization_id: Optional[int]) -> InventoryMetrics:
    """Get inventory metrics"""
    product_query = db.query(Product).filter(Product.deleted_at.is_(None))
    inventory_query = db.query(InventoryItem).filter(InventoryItem.deleted_at.is_(None))
    
    if organization_id:
        product_query = product_query.filter(Product.organization_id == organization_id)
        inventory_query = inventory_query.filter(InventoryItem.organization_id == organization_id)
    
    # Basic counts
    total_products = product_query.count()
    
    # Stock value
    inventory_items = inventory_query.all()
    total_stock_value = sum(
        item.total_cost for item in inventory_items 
        if item.total_cost and item.quantity_on_hand > 0
    ) or 0
    
    # Stock alerts
    low_stock_items = sum(1 for item in inventory_items if item.is_low_stock)
    out_of_stock_items = sum(1 for item in inventory_items if item.quantity_on_hand <= 0)
    expired_items = sum(1 for item in inventory_items if item.is_expired)
    near_expiry_items = sum(1 for item in inventory_items if item.is_near_expiry(30))
    
    # Top products by value
    product_values = {}
    for item in inventory_items:
        if item.total_cost and item.quantity_on_hand > 0:
            key = item.product_id
            if key not in product_values:
                product_values[key] = {
                    "product_id": item.product_id,
                    "product_code": item.product.code,
                    "product_name": item.product.name,
                    "total_value": 0,
                    "total_quantity": 0
                }
            product_values[key]["total_value"] += float(item.total_cost)
            product_values[key]["total_quantity"] += float(item.quantity_on_hand)
    
    top_products_by_value = sorted(
        product_values.values(),
        key=lambda x: x["total_value"],
        reverse=True
    )[:10]
    
    # Stock movements today
    today = date.today()
    movements_today = db.query(StockMovement).filter(
        and_(
            func.date(StockMovement.movement_date) == today,
            StockMovement.deleted_at.is_(None)
        )
    )
    
    if organization_id:
        movements_today = movements_today.filter(StockMovement.organization_id == organization_id)
    
    stock_movements_today = movements_today.count()
    
    return InventoryMetrics(
        total_products=total_products,
        total_stock_value=float(total_stock_value),
        low_stock_items=low_stock_items,
        out_of_stock_items=out_of_stock_items,
        expired_items=expired_items,
        near_expiry_items=near_expiry_items,
        top_products_by_value=top_products_by_value,
        stock_movements_today=stock_movements_today
    )


async def _get_customer_metrics(
    db: Session,
    organization_id: Optional[int],
    date_from: date,
    date_to: date
) -> CustomerMetrics:
    """Get customer metrics"""
    customer_query = db.query(Customer).filter(Customer.deleted_at.is_(None))
    if organization_id:
        customer_query = customer_query.filter(Customer.organization_id == organization_id)
    
    total_customers = customer_query.count()
    active_customers = customer_query.filter(Customer.is_active == True).count()
    
    # New customers this month
    current_month_start = date.today().replace(day=1)
    new_customers_this_month = customer_query.filter(
        Customer.created_at >= current_month_start
    ).count()
    
    # Customer growth rate (monthly)
    prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    prev_month_customers = customer_query.filter(
        Customer.created_at < current_month_start
    ).count()
    
    customer_growth_rate = 0.0
    if prev_month_customers > 0:
        customer_growth_rate = (new_customers_this_month / prev_month_customers) * 100
    
    # Top customers by revenue
    top_customers = customer_query.order_by(desc(Customer.total_spent)).limit(10).all()
    top_customers_by_revenue = [
        {
            "customer_id": customer.id,
            "customer_name": customer.name,
            "customer_code": customer.code,
            "total_spent": float(customer.total_spent),
            "total_orders": customer.total_orders
        }
        for customer in top_customers
    ]
    
    return CustomerMetrics(
        total_customers=total_customers,
        active_customers=active_customers,
        new_customers_this_month=new_customers_this_month,
        top_customers_by_revenue=top_customers_by_revenue,
        customer_growth_rate=customer_growth_rate
    )


async def _get_order_metrics(
    db: Session,
    organization_id: Optional[int],
    date_from: date,
    date_to: date
) -> OrderMetrics:
    """Get order metrics"""
    order_query = db.query(SalesOrder).filter(SalesOrder.deleted_at.is_(None))
    if organization_id:
        order_query = order_query.filter(SalesOrder.organization_id == organization_id)
    
    total_orders = order_query.count()
    
    # Orders by status
    status_counts = order_query.with_entities(
        SalesOrder.status,
        func.count(SalesOrder.id)
    ).group_by(SalesOrder.status).all()
    
    orders_by_status = {status: count for status, count in status_counts}
    
    # Individual status counts
    pending_orders = orders_by_status.get("pending", 0) + orders_by_status.get("draft", 0)
    processing_orders = orders_by_status.get("processing", 0)
    shipped_orders = orders_by_status.get("shipped", 0)
    delivered_orders = orders_by_status.get("delivered", 0)
    cancelled_orders = orders_by_status.get("cancelled", 0)
    
    # Overdue orders
    today = date.today()
    overdue_orders = order_query.filter(
        and_(
            SalesOrder.required_date < today,
            SalesOrder.status.not_in(["delivered", "cancelled", "refunded"])
        )
    ).count()
    
    # Recent orders
    recent_orders_data = order_query.order_by(desc(SalesOrder.created_at)).limit(5).all()
    recent_orders = [
        {
            "order_id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer.name if order.customer else "Unknown",
            "status": order.status,
            "total_amount": float(order.total_amount),
            "order_date": order.order_date.isoformat(),
            "created_at": order.created_at.isoformat()
        }
        for order in recent_orders_data
    ]
    
    return OrderMetrics(
        total_orders=total_orders,
        pending_orders=pending_orders,
        processing_orders=processing_orders,
        shipped_orders=shipped_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        overdue_orders=overdue_orders,
        orders_by_status=orders_by_status,
        recent_orders=recent_orders
    )


async def _get_recent_activities(
    db: Session,
    organization_id: Optional[int],
    limit: int = 20,
    activity_type: Optional[str] = None
) -> List[ActivityFeed]:
    """Get recent system activities (simplified implementation)"""
    # This is a simplified implementation
    # In a real system, you'd have a dedicated activity log table
    activities = []
    
    # Recent orders
    order_query = db.query(SalesOrder).filter(SalesOrder.deleted_at.is_(None))
    if organization_id:
        order_query = order_query.filter(SalesOrder.organization_id == organization_id)
    
    recent_orders = order_query.order_by(desc(SalesOrder.created_at)).limit(5).all()
    
    for order in recent_orders:
        activities.append(ActivityFeed(
            timestamp=order.created_at.isoformat(),
            activity_type="order_created",
            description=f"New order {order.order_number} created for {order.customer.name if order.customer else 'Unknown'}",
            user_name=None,  # Would need user lookup
            reference_id=order.id,
            reference_type="sales_order"
        ))
    
    # Recent stock movements
    movement_query = db.query(StockMovement).filter(StockMovement.deleted_at.is_(None))
    if organization_id:
        movement_query = movement_query.filter(StockMovement.organization_id == organization_id)
    
    recent_movements = movement_query.order_by(desc(StockMovement.created_at)).limit(5).all()
    
    for movement in recent_movements:
        activities.append(ActivityFeed(
            timestamp=movement.created_at.isoformat(),
            activity_type="stock_movement",
            description=f"Stock {movement.movement_type}: {movement.quantity} units of {movement.product.name}",
            user_name=movement.performed_by_user.full_name if movement.performed_by_user else None,
            reference_id=movement.id,
            reference_type="stock_movement"
        ))
    
    # Sort by timestamp and limit
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    return activities[:limit]


async def _generate_alerts(db: Session, organization_id: Optional[int]) -> List[Dict[str, Any]]:
    """Generate dashboard alerts"""
    alerts = []
    
    # Low stock alerts
    inventory_query = db.query(InventoryItem).filter(InventoryItem.deleted_at.is_(None))
    if organization_id:
        inventory_query = inventory_query.filter(InventoryItem.organization_id == organization_id)
    
    low_stock_count = inventory_query.filter(
        InventoryItem.quantity_available <= InventoryItem.minimum_level
    ).count()
    
    if low_stock_count > 0:
        alerts.append({
            "alert_type": "warning",
            "title": "Low Stock Alert",
            "message": f"{low_stock_count} products are running low on stock",
            "count": low_stock_count,
            "action_url": "/erp-inventory/inventory?low_stock_only=true",
            "priority": 1
        })
    
    # Overdue orders
    order_query = db.query(SalesOrder).filter(SalesOrder.deleted_at.is_(None))
    if organization_id:
        order_query = order_query.filter(SalesOrder.organization_id == organization_id)
    
    today = date.today()
    overdue_count = order_query.filter(
        and_(
            SalesOrder.required_date < today,
            SalesOrder.status.not_in(["delivered", "cancelled", "refunded"])
        )
    ).count()
    
    if overdue_count > 0:
        alerts.append({
            "alert_type": "error",
            "title": "Overdue Orders",
            "message": f"{overdue_count} orders are overdue for delivery",
            "count": overdue_count,
            "action_url": "/erp-sales/orders?overdue_only=true",
            "priority": 1
        })
    
    # Expired items
    expired_count = inventory_query.filter(
        InventoryItem.expiry_date < date.today()
    ).count()
    
    if expired_count > 0:
        alerts.append({
            "alert_type": "error",
            "title": "Expired Items",
            "message": f"{expired_count} inventory items have expired",
            "count": expired_count,
            "action_url": "/erp-inventory/inventory?expired_only=true",
            "priority": 2
        })
    
    return alerts