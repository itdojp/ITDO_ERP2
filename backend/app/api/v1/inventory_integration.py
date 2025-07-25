"""
Inventory Integration API for CC02 v62.0
Comprehensive inventory management endpoints with real-time tracking, auto-ordering, analytics, shipping integration, and warehouse management
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user
from app.core.database import get_async_session
from app.core.exceptions import BusinessLogicError, ValidationError
from app.models.inventory_integration import (
    AutoOrder,
    AutoOrderRule,
    InventoryAnalytics,
    InventoryPrediction,
    PredictionModel,
    RealtimeInventoryAlert,
    ShippingInventorySync,
)
from app.models.user import User
from app.schemas.inventory_integration import (
    AutoOrder as AutoOrderSchema,
    AutoOrderCreate,
    AutoOrderRule as AutoOrderRuleSchema,
    AutoOrderRuleCreate,
    AutoOrderRuleUpdate,
    BulkInventoryUpdate,
    BulkOperationResult,
    InventoryAnalytics as InventoryAnalyticsSchema,
    InventoryDashboardStats,
    InventorySearchFilters,
    PaginatedResponse,
    ProductAnalyticsSummary,
    RealtimeAlert,
    RealtimeAlertCreate,
    RealtimeInventorySnapshot,
    RealtimeInventoryUpdate,
    ShippingInventorySync as ShippingInventorySyncSchema,
    ShippingInventorySyncCreate,
    WarehousePerformanceMetrics,
    WebSocketMessage,
)
from app.services.inventory_integration_service import (
    AutoOrderingService,
    InventoryAnalyticsService,
    RealtimeInventoryTrackingService,
    ShippingInventoryIntegrationService,
)

router = APIRouter(prefix="/inventory-integration", tags=["Inventory Integration"])
security = HTTPBearer()


# WebSocket connection manager
class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception:
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)


websocket_manager = WebSocketManager()


# Real-time inventory tracking endpoints
@router.websocket("/realtime/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """WebSocket endpoint for real-time inventory updates."""
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Process incoming messages if needed
            await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)


@router.get("/realtime/snapshot/{product_id}/{warehouse_id}", response_model=RealtimeInventorySnapshot)
async def get_realtime_inventory_snapshot(
    product_id: int,
    warehouse_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> RealtimeInventorySnapshot:
    """Get current real-time inventory snapshot for a product in a warehouse."""
    service = RealtimeInventoryTrackingService(db)
    return await service.get_realtime_snapshot(product_id, warehouse_id, current_user.organization_id)


@router.post("/realtime/update", response_model=RealtimeInventorySnapshot)
async def process_realtime_inventory_update(
    update: RealtimeInventoryUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> RealtimeInventorySnapshot:
    """Process a real-time inventory update."""
    service = RealtimeInventoryTrackingService(db)
    
    # Update user_id if not provided
    if not update.user_id:
        update.user_id = current_user.id
    
    snapshot = await service.process_realtime_update(update, current_user.organization_id)
    
    # Broadcast update via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast,
        {
            "type": "inventory_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": snapshot.model_dump()
        }
    )
    
    return snapshot


@router.post("/realtime/bulk-update", response_model=BulkOperationResult)
async def process_bulk_inventory_updates(
    bulk_update: BulkInventoryUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> BulkOperationResult:
    """Process multiple inventory updates in bulk."""
    service = RealtimeInventoryTrackingService(db)
    start_time = datetime.utcnow()
    
    successful_items = 0
    failed_items = 0
    errors = []
    
    for i, update in enumerate(bulk_update.updates):
        try:
            if not update.user_id:
                update.user_id = current_user.id
            
            await service.process_realtime_update(update, current_user.organization_id)
            successful_items += 1
            
        except Exception as e:
            failed_items += 1
            errors.append({
                "index": i,
                "update": update.model_dump(),
                "error": str(e)
            })
    
    end_time = datetime.utcnow()
    processing_time = (end_time - start_time).total_seconds()
    
    result = BulkOperationResult(
        total_items=len(bulk_update.updates),
        successful_items=successful_items,
        failed_items=failed_items,
        errors=errors,
        batch_id=bulk_update.batch_id,
        processing_time_seconds=processing_time
    )
    
    return result


@router.get("/realtime/alerts", response_model=list[RealtimeAlert])
async def get_realtime_alerts(
    active_only: bool = Query(True, description="Return only active alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> list[RealtimeAlert]:
    """Get real-time inventory alerts."""
    query = select(RealtimeInventoryAlert).where(
        and_(
            RealtimeInventoryAlert.organization_id == current_user.organization_id,
            RealtimeInventoryAlert.deleted_at.is_(None)
        )
    ).order_by(desc(RealtimeInventoryAlert.created_at))
    
    if active_only:
        query = query.where(RealtimeInventoryAlert.is_active == True)
    
    if severity:
        query = query.where(RealtimeInventoryAlert.severity == severity)
    
    if alert_type:
        query = query.where(RealtimeInventoryAlert.alert_type == alert_type)
    
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [RealtimeAlert.model_validate(alert) for alert in alerts]


@router.put("/realtime/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, str]:
    """Acknowledge a real-time alert."""
    query = select(RealtimeInventoryAlert).where(
        and_(
            RealtimeInventoryAlert.id == alert_id,
            RealtimeInventoryAlert.organization_id == current_user.organization_id,
            RealtimeInventoryAlert.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledge(current_user.id)
    await db.commit()
    
    return {"message": "Alert acknowledged successfully"}


# Auto-ordering system endpoints
@router.post("/auto-ordering/rules", response_model=AutoOrderRuleSchema, status_code=201)
async def create_auto_order_rule(
    rule_data: AutoOrderRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> AutoOrderRuleSchema:
    """Create a new auto order rule."""
    service = AutoOrderingService(db)
    try:
        rule = await service.create_auto_order_rule(rule_data, current_user.organization_id, current_user.id)
        return AutoOrderRuleSchema.model_validate(rule)
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/auto-ordering/rules", response_model=list[AutoOrderRuleSchema])
async def get_auto_order_rules(
    product_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> list[AutoOrderRuleSchema]:
    """Get auto order rules."""
    query = select(AutoOrderRule).where(
        and_(
            AutoOrderRule.organization_id == current_user.organization_id,
            AutoOrderRule.deleted_at.is_(None)
        )
    ).order_by(desc(AutoOrderRule.created_at))
    
    if product_id:
        query = query.where(AutoOrderRule.product_id == product_id)
    
    if warehouse_id:
        query = query.where(AutoOrderRule.warehouse_id == warehouse_id)
    
    if is_active is not None:
        query = query.where(AutoOrderRule.is_active == is_active)
    
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return [AutoOrderRuleSchema.model_validate(rule) for rule in rules]


@router.put("/auto-ordering/rules/{rule_id}", response_model=AutoOrderRuleSchema)
async def update_auto_order_rule(
    rule_id: int,
    rule_update: AutoOrderRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> AutoOrderRuleSchema:
    """Update an auto order rule."""
    query = select(AutoOrderRule).where(
        and_(
            AutoOrderRule.id == rule_id,
            AutoOrderRule.organization_id == current_user.organization_id,
            AutoOrderRule.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Auto order rule not found")
    
    # Update fields
    update_data = rule_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    rule.updated_by = current_user.id
    rule.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(rule)
    
    return AutoOrderRuleSchema.model_validate(rule)


@router.post("/auto-ordering/check-and-process", response_model=list[AutoOrderSchema])
async def check_and_process_auto_orders(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> list[AutoOrderSchema]:
    """Check all auto order rules and create orders where needed."""
    service = AutoOrderingService(db)
    
    try:
        orders = await service.check_and_process_auto_orders(current_user.organization_id)
        
        # Send notifications for created orders
        if orders:
            background_tasks.add_task(
                websocket_manager.broadcast,
                {
                    "type": "auto_orders_created",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {"orders_count": len(orders)}
                }
            )
        
        return [AutoOrderSchema.model_validate(order) for order in orders]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing auto orders: {str(e)}")


@router.get("/auto-ordering/orders", response_model=list[AutoOrderSchema])
async def get_auto_orders(
    status: Optional[str] = Query(None),
    product_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> list[AutoOrderSchema]:
    """Get auto orders."""
    query = select(AutoOrder).where(
        and_(
            AutoOrder.organization_id == current_user.organization_id,
            AutoOrder.deleted_at.is_(None)
        )
    ).order_by(desc(AutoOrder.created_at))
    
    if status:
        query = query.where(AutoOrder.status == status)
    
    if product_id:
        query = query.where(AutoOrder.product_id == product_id)
    
    if warehouse_id:
        query = query.where(AutoOrder.warehouse_id == warehouse_id)
    
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return [AutoOrderSchema.model_validate(order) for order in orders]


@router.put("/auto-ordering/orders/{order_id}/approve", response_model=AutoOrderSchema)
async def approve_auto_order(
    order_id: int,
    approval_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> AutoOrderSchema:
    """Approve an auto order."""
    service = AutoOrderingService(db)
    
    try:
        order = await service.approve_auto_order(order_id, current_user.id, approval_notes)
        return AutoOrderSchema.model_validate(order)
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# Inventory analytics endpoints
@router.post("/analytics/generate/{product_id}/{warehouse_id}", response_model=InventoryAnalyticsSchema)
async def generate_inventory_analytics(
    product_id: int,
    warehouse_id: int,
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> InventoryAnalyticsSchema:
    """Generate comprehensive inventory analytics for a product/warehouse."""
    service = InventoryAnalyticsService(db)
    
    try:
        analytics = await service.generate_analytics(
            product_id, warehouse_id, current_user.organization_id, period_days
        )
        return InventoryAnalyticsSchema.model_validate(analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")


@router.get("/analytics", response_model=list[InventoryAnalyticsSchema])
async def get_inventory_analytics(
    product_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> list[InventoryAnalyticsSchema]:
    """Get inventory analytics records."""
    query = select(InventoryAnalytics).where(
        and_(
            InventoryAnalytics.organization_id == current_user.organization_id,
            InventoryAnalytics.deleted_at.is_(None)
        )
    ).order_by(desc(InventoryAnalytics.period_end))
    
    if product_id:
        query = query.where(InventoryAnalytics.product_id == product_id)
    
    if warehouse_id:
        query = query.where(InventoryAnalytics.warehouse_id == warehouse_id)
    
    if start_date:
        query = query.where(InventoryAnalytics.period_start >= start_date)
    
    if end_date:
        query = query.where(InventoryAnalytics.period_end <= end_date)
    
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    analytics = result.scalars().all()
    
    return [InventoryAnalyticsSchema.model_validate(item) for item in analytics]


# Shipping integration endpoints
@router.post("/shipping/sync", response_model=ShippingInventorySyncSchema, status_code=201)
async def create_shipping_sync(
    sync_data: ShippingInventorySyncCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ShippingInventorySyncSchema:
    """Create a new shipping inventory sync record."""
    service = ShippingInventoryIntegrationService(db)
    
    try:
        sync_record = await service.create_shipping_sync(sync_data, current_user.organization_id)
        return ShippingInventorySyncSchema.model_validate(sync_record)
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/shipping/sync/{sync_id}/status", response_model=ShippingInventorySyncSchema)
async def update_shipment_status(
    sync_id: str,
    new_status: str,
    tracking_events: Optional[list[dict[str, Any]]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> ShippingInventorySyncSchema:
    """Update shipment status and sync inventory."""
    service = ShippingInventoryIntegrationService(db)
    
    try:
        sync_record = await service.update_shipment_status(
            sync_id, new_status, tracking_events, current_user.organization_id
        )
        return ShippingInventorySyncSchema.model_validate(sync_record)
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating shipment status: {str(e)}")


@router.post("/shipping/sync-all", response_model=dict[str, int])
async def sync_all_pending_shipments(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, int]:
    """Synchronize all pending shipments with external systems."""
    service = ShippingInventoryIntegrationService(db)
    
    try:
        result = await service.sync_all_pending_shipments(current_user.organization_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing shipments: {str(e)}")


@router.get("/shipping/sync", response_model=list[ShippingInventorySyncSchema])
async def get_shipping_syncs(
    shipment_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sync_status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> list[ShippingInventorySyncSchema]:
    """Get shipping inventory sync records."""
    query = select(ShippingInventorySync).where(
        and_(
            ShippingInventorySync.organization_id == current_user.organization_id,
            ShippingInventorySync.deleted_at.is_(None)
        )
    ).order_by(desc(ShippingInventorySync.last_sync_at))
    
    if shipment_id:
        query = query.where(ShippingInventorySync.shipment_id == shipment_id)
    
    if status:
        query = query.where(ShippingInventorySync.status == status)
    
    if sync_status:
        query = query.where(ShippingInventorySync.sync_status == sync_status)
    
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    syncs = result.scalars().all()
    
    return [ShippingInventorySyncSchema.model_validate(sync) for sync in syncs]


# Dashboard and reporting endpoints
@router.get("/dashboard/stats", response_model=InventoryDashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> InventoryDashboardStats:
    """Get inventory dashboard statistics."""
    from app.models.inventory import InventoryItem, Warehouse
    from app.models.product import Product
    
    # Total products query
    products_query = select(func.count(Product.id.distinct())).where(
        and_(
            Product.organization_id == current_user.organization_id,
            Product.deleted_at.is_(None)
        )
    )
    products_result = await db.execute(products_query)
    total_products = products_result.scalar() or 0
    
    # Total warehouses query
    warehouses_query = select(func.count(Warehouse.id)).where(
        and_(
            Warehouse.organization_id == current_user.organization_id,
            Warehouse.deleted_at.is_(None)
        )
    )
    warehouses_result = await db.execute(warehouses_query)
    total_warehouses = warehouses_result.scalar() or 0
    
    # Total stock value query
    stock_value_query = select(func.sum(InventoryItem.total_cost)).where(
        and_(
            InventoryItem.organization_id == current_user.organization_id,
            InventoryItem.deleted_at.is_(None),
            InventoryItem.total_cost.is_not(None)
        )
    )
    stock_value_result = await db.execute(stock_value_query)
    total_stock_value = stock_value_result.scalar() or 0
    
    # Low stock items query
    low_stock_query = select(func.count(InventoryItem.id)).where(
        and_(
            InventoryItem.organization_id == current_user.organization_id,
            InventoryItem.deleted_at.is_(None),
            InventoryItem.quantity_available <= InventoryItem.minimum_level,
            InventoryItem.minimum_level.is_not(None),
            InventoryItem.minimum_level > 0
        )
    )
    low_stock_result = await db.execute(low_stock_query)
    low_stock_items = low_stock_result.scalar() or 0
    
    # Out of stock items query
    out_of_stock_query = select(func.count(InventoryItem.id)).where(
        and_(
            InventoryItem.organization_id == current_user.organization_id,
            InventoryItem.deleted_at.is_(None),
            InventoryItem.quantity_available <= 0
        )
    )
    out_of_stock_result = await db.execute(out_of_stock_query)
    out_of_stock_items = out_of_stock_result.scalar() or 0
    
    # Active alerts query
    alerts_query = select(func.count(RealtimeInventoryAlert.id)).where(
        and_(
            RealtimeInventoryAlert.organization_id == current_user.organization_id,
            RealtimeInventoryAlert.is_active == True,
            RealtimeInventoryAlert.deleted_at.is_(None)
        )
    )
    alerts_result = await db.execute(alerts_query)
    active_alerts = alerts_result.scalar() or 0
    
    # Pending orders query
    pending_orders_query = select(func.count(AutoOrder.id)).where(
        and_(
            AutoOrder.organization_id == current_user.organization_id,
            AutoOrder.status.in_(['pending', 'approved', 'placed']),
            AutoOrder.deleted_at.is_(None)
        )
    )
    pending_orders_result = await db.execute(pending_orders_query)
    pending_orders = pending_orders_result.scalar() or 0
    
    return InventoryDashboardStats(
        total_products=total_products,
        total_warehouses=total_warehouses,
        total_stock_value=total_stock_value,
        low_stock_items=low_stock_items,
        out_of_stock_items=out_of_stock_items,
        overstock_items=0,  # TODO: Implement overstock calculation
        pending_orders=pending_orders,
        active_alerts=active_alerts
    )


# Background task endpoints
@router.post("/tasks/generate-analytics-batch")
async def generate_analytics_batch(
    background_tasks: BackgroundTasks,
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, str]:
    """Generate analytics for all products in all warehouses (background task)."""
    
    async def batch_analytics_task():
        """Background task to generate analytics."""
        from app.models.inventory import InventoryItem
        
        service = InventoryAnalyticsService(db)
        
        # Get all unique product/warehouse combinations
        query = select(
            InventoryItem.product_id,
            InventoryItem.warehouse_id
        ).where(
            and_(
                InventoryItem.organization_id == current_user.organization_id,
                InventoryItem.deleted_at.is_(None)
            )
        ).distinct()
        
        result = await db.execute(query)
        combinations = result.all()
        
        for product_id, warehouse_id in combinations:
            try:
                await service.generate_analytics(
                    product_id, warehouse_id, current_user.organization_id, period_days
                )
                await asyncio.sleep(0.1)  # Prevent overwhelming the system
            except Exception as e:
                print(f"Error generating analytics for product {product_id}, warehouse {warehouse_id}: {e}")
    
    background_tasks.add_task(batch_analytics_task)
    
    return {"message": "Batch analytics generation started"}


# Warehouse management endpoints
@router.get("/warehouse/{warehouse_id}/performance", response_model=WarehousePerformanceMetrics)
async def get_warehouse_performance_metrics(
    warehouse_id: int,
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> WarehousePerformanceMetrics:
    """Get comprehensive performance metrics for a warehouse."""
    from app.services.warehouse_management_service import WarehouseOptimizationService
    
    service = WarehouseOptimizationService(db)
    
    try:
        metrics = await service.get_warehouse_performance_metrics(
            warehouse_id, current_user.organization_id, period_days
        )
        return metrics
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting warehouse metrics: {str(e)}")


@router.post("/warehouse/{warehouse_id}/optimize-layout")
async def optimize_warehouse_layout(
    warehouse_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, Any]:
    """Optimize warehouse layout based on product velocity and characteristics."""
    from app.services.warehouse_management_service import WarehouseOptimizationService
    
    service = WarehouseOptimizationService(db)
    
    try:
        optimization = await service.optimize_warehouse_layout(warehouse_id, current_user.organization_id)
        return optimization
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing warehouse layout: {str(e)}")


@router.post("/warehouse/{warehouse_id}/optimize-picking")
async def generate_picking_optimization(
    warehouse_id: int,
    order_ids: list[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, Any]:
    """Generate optimized picking routes for given orders."""
    from app.services.warehouse_management_service import WarehouseOptimizationService
    
    service = WarehouseOptimizationService(db)
    
    try:
        optimization = await service.generate_picking_optimization(
            warehouse_id, current_user.organization_id, order_ids
        )
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating picking optimization: {str(e)}")


@router.get("/warehouse/{warehouse_id}/optimal-stock-levels")
async def calculate_optimal_stock_levels(
    warehouse_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, Any]:
    """Calculate optimal stock levels for all products in warehouse."""
    from app.services.warehouse_management_service import WarehouseOptimizationService
    
    service = WarehouseOptimizationService(db)
    
    try:
        optimization = await service.calculate_optimal_stock_levels(warehouse_id, current_user.organization_id)
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating optimal stock levels: {str(e)}")


@router.get("/warehouse/{warehouse_id}/capacity-report")
async def generate_warehouse_capacity_report(
    warehouse_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, Any]:
    """Generate comprehensive warehouse capacity and utilization report."""
    from app.services.warehouse_management_service import WarehouseOptimizationService
    
    service = WarehouseOptimizationService(db)
    
    try:
        report = await service.generate_warehouse_capacity_report(warehouse_id, current_user.organization_id)
        return report
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating capacity report: {str(e)}")


@router.get("/warehouse/multi-location/transfer-optimization")
async def optimize_inventory_transfers(
    source_warehouse_id: int = Query(..., description="Source warehouse ID"),
    target_warehouse_id: int = Query(..., description="Target warehouse ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, Any]:
    """Optimize inventory transfers between warehouses."""
    from app.models.inventory import InventoryItem
    
    # Get inventory items from both warehouses
    source_query = select(InventoryItem).where(
        and_(
            InventoryItem.warehouse_id == source_warehouse_id,
            InventoryItem.organization_id == current_user.organization_id,
            InventoryItem.quantity_available > 0,
            InventoryItem.deleted_at.is_(None)
        )
    )
    source_result = await db.execute(source_query)
    source_items = {item.product_id: item for item in source_result.scalars().all()}
    
    target_query = select(InventoryItem).where(
        and_(
            InventoryItem.warehouse_id == target_warehouse_id,
            InventoryItem.organization_id == current_user.organization_id,
            InventoryItem.deleted_at.is_(None)
        )
    )
    target_result = await db.execute(target_query)
    target_items = {item.product_id: item for item in target_result.scalars().all()}
    
    # Find optimization opportunities
    transfer_recommendations = []
    
    for product_id, source_item in source_items.items():
        target_item = target_items.get(product_id)
        
        if target_item:
            # Check if target warehouse is low/out of stock
            if target_item.is_low_stock and source_item.quantity_available > source_item.minimum_level:
                excess_quantity = source_item.quantity_available - (source_item.minimum_level or 0)
                needed_quantity = (target_item.minimum_level or 0) - target_item.quantity_available
                
                if excess_quantity > 0 and needed_quantity > 0:
                    transfer_quantity = min(excess_quantity, needed_quantity)
                    
                    transfer_recommendations.append({
                        "product_id": product_id,
                        "source_warehouse_id": source_warehouse_id,
                        "target_warehouse_id": target_warehouse_id,
                        "recommended_quantity": float(transfer_quantity),
                        "source_current_stock": float(source_item.quantity_available),
                        "target_current_stock": float(target_item.quantity_available),
                        "priority": "high" if target_item.quantity_available <= 0 else "medium",
                        "estimated_cost_savings": float(transfer_quantity * (source_item.average_cost or 0) * Decimal("0.1"))
                    })
    
    return {
        "source_warehouse_id": source_warehouse_id,
        "target_warehouse_id": target_warehouse_id,
        "analysis_date": datetime.utcnow().isoformat(),
        "total_recommendations": len(transfer_recommendations),
        "transfer_recommendations": transfer_recommendations[:20],  # Limit response size
        "estimated_total_savings": sum(rec["estimated_cost_savings"] for rec in transfer_recommendations),
        "implementation_notes": [
            "Verify product compatibility between warehouses",
            "Consider transportation costs in final decision",
            "Schedule transfers during low-activity periods"
        ]
    }


# Health check endpoint
@router.get("/health")
async def inventory_integration_health() -> dict[str, str]:
    """Health check for inventory integration system."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "CC02 v62.0",
        "system": "Inventory Integration API"
    }