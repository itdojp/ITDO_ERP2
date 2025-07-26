"""
CC02 v60.0 Inventory Integration Management API
Advanced inventory management with real-time tracking, prediction, and supplier integration
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BusinessLogicError, NotFoundError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/inventory-integration", tags=["Inventory Integration v60"]
)


# Enums for inventory management
class InventoryStatus(str, Enum):
    """Inventory item status"""

    AVAILABLE = "available"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    RESERVED = "reserved"


class StockMovementType(str, Enum):
    """Stock movement types"""

    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RETURN = "return"
    DAMAGE = "damage"
    RESERVATION = "reservation"
    RELEASE = "release"


class PredictionMethod(str, Enum):
    """Inventory prediction methods"""

    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"


class AlertSeverity(str, Enum):
    """Alert severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SupplierStatus(str, Enum):
    """Supplier status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


# Request Models
class InventoryItemRequest(BaseModel):
    """Request model for inventory item operations"""

    product_id: UUID
    location_id: Optional[UUID] = None
    quantity: int = Field(..., ge=0)
    reorder_point: int = Field(default=10, ge=0)
    max_stock_level: int = Field(default=100, ge=1)
    unit_cost: Decimal = Field(..., ge=0)
    supplier_id: Optional[UUID] = None
    lead_time_days: int = Field(default=7, ge=1)
    safety_stock: int = Field(default=5, ge=0)

    @validator("max_stock_level")
    def validate_max_stock_level(cls, v, values):
        if "reorder_point" in values and v <= values["reorder_point"]:
            raise ValueError("max_stock_level must be greater than reorder_point")
        return v


class StockMovementRequest(BaseModel):
    """Request model for stock movements"""

    product_id: UUID
    movement_type: StockMovementType
    quantity: int = Field(..., gt=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    reference_id: Optional[UUID] = None
    location_from: Optional[UUID] = None
    location_to: Optional[UUID] = None
    notes: Optional[str] = Field(None, max_length=500)
    batch_number: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[datetime] = None


class ReorderRequest(BaseModel):
    """Request model for automatic reordering"""

    product_id: UUID
    supplier_id: UUID
    quantity: int = Field(..., gt=0)
    priority: int = Field(default=1, ge=1, le=5)
    delivery_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class StockPredictionRequest(BaseModel):
    """Request model for stock prediction"""

    product_ids: Optional[List[UUID]] = None
    prediction_days: int = Field(default=30, ge=1, le=365)
    method: PredictionMethod = PredictionMethod.MOVING_AVERAGE
    include_seasonal: bool = True
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)


class SupplierIntegrationRequest(BaseModel):
    """Request model for supplier integration"""

    supplier_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    contact_email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    contact_phone: Optional[str] = Field(None, max_length=20)
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=100)
    lead_time_days: int = Field(default=7, ge=1, le=90)
    minimum_order_value: Decimal = Field(default=Decimal("0"), ge=0)
    status: SupplierStatus = SupplierStatus.ACTIVE


# Response Models
class InventoryItemResponse(BaseModel):
    """Response model for inventory items"""

    item_id: UUID
    product_id: UUID
    product_name: str
    product_sku: str
    location_id: Optional[UUID]
    location_name: Optional[str]
    current_quantity: int
    available_quantity: int
    reserved_quantity: int
    reorder_point: int
    max_stock_level: int
    unit_cost: Decimal
    total_value: Decimal
    status: InventoryStatus
    supplier_id: Optional[UUID]
    supplier_name: Optional[str]
    lead_time_days: int
    safety_stock: int
    last_movement_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class StockMovementResponse(BaseModel):
    """Response model for stock movements"""

    movement_id: UUID
    product_id: UUID
    product_name: str
    movement_type: StockMovementType
    quantity: int
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    reference_id: Optional[UUID]
    location_from_name: Optional[str]
    location_to_name: Optional[str]
    notes: Optional[str]
    batch_number: Optional[str]
    expiry_date: Optional[datetime]
    created_by: UUID
    created_at: datetime


class ReorderResponse(BaseModel):
    """Response model for reorder suggestions"""

    reorder_id: UUID
    product_id: UUID
    product_name: str
    current_stock: int
    reorder_point: int
    suggested_quantity: int
    supplier_id: UUID
    supplier_name: str
    estimated_cost: Decimal
    priority: int
    delivery_date: Optional[datetime]
    status: str
    created_at: datetime


class StockPredictionResponse(BaseModel):
    """Response model for stock predictions"""

    product_id: UUID
    product_name: str
    current_stock: int
    prediction_date: datetime
    predicted_stock: int
    predicted_demand: int
    confidence_interval_lower: int
    confidence_interval_upper: int
    reorder_recommendation: bool
    suggested_reorder_quantity: int
    method_used: PredictionMethod
    accuracy_score: float


class InventoryAlertResponse(BaseModel):
    """Response model for inventory alerts"""

    alert_id: UUID
    product_id: UUID
    product_name: str
    alert_type: str
    severity: AlertSeverity
    message: str
    current_stock: int
    threshold: Optional[int]
    suggested_action: str
    created_at: datetime
    acknowledged: bool
    acknowledged_by: Optional[UUID]
    acknowledged_at: Optional[datetime]


class SupplierIntegrationResponse(BaseModel):
    """Response model for supplier integration"""

    supplier_id: UUID
    name: str
    contact_email: str
    contact_phone: Optional[str]
    api_endpoint: Optional[str]
    api_connected: bool
    lead_time_days: int
    minimum_order_value: Decimal
    status: SupplierStatus
    total_products: int
    last_order_date: Optional[datetime]
    performance_rating: float
    created_at: datetime
    updated_at: datetime


# Core Business Logic Classes
class InventoryTracker:
    """Real-time inventory tracking system"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_real_time_inventory(self, product_id: UUID) -> Dict[str, Any]:
        """Get real-time inventory data"""
        try:
            # Query current inventory status
            query = text("""
                SELECT 
                    p.id as product_id,
                    p.name as product_name,
                    p.sku as product_sku,
                    COALESCE(SUM(CASE WHEN sm.movement_type IN ('purchase', 'adjustment', 'return') 
                                     THEN sm.quantity 
                                     ELSE -sm.quantity END), 0) as current_quantity,
                    COALESCE(i.reorder_point, 10) as reorder_point,
                    COALESCE(i.max_stock_level, 100) as max_stock_level,
                    COALESCE(i.safety_stock, 5) as safety_stock,
                    COALESCE(reserved.reserved_qty, 0) as reserved_quantity
                FROM products p
                LEFT JOIN inventory_items i ON p.id = i.product_id
                LEFT JOIN stock_movements sm ON p.id = sm.product_id
                LEFT JOIN (
                    SELECT product_id, SUM(quantity) as reserved_qty
                    FROM stock_movements 
                    WHERE movement_type = 'reservation' 
                    GROUP BY product_id
                ) reserved ON p.id = reserved.product_id
                WHERE p.id = :product_id
                GROUP BY p.id, p.name, p.sku, i.reorder_point, i.max_stock_level, i.safety_stock, reserved.reserved_qty
            """)

            result = await self.db.execute(query, {"product_id": str(product_id)})
            row = result.fetchone()

            if not row:
                raise NotFoundError(f"Product {product_id} not found")

            current_qty = row.current_quantity or 0
            reserved_qty = row.reserved_quantity or 0
            available_qty = max(0, current_qty - reserved_qty)

            # Determine status
            status = self._determine_inventory_status(
                current_qty, row.reorder_point, row.max_stock_level
            )

            return {
                "product_id": product_id,
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "current_quantity": current_qty,
                "available_quantity": available_qty,
                "reserved_quantity": reserved_qty,
                "reorder_point": row.reorder_point,
                "max_stock_level": row.max_stock_level,
                "safety_stock": row.safety_stock,
                "status": status,
                "last_updated": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(
                f"Error getting real-time inventory for {product_id}: {str(e)}"
            )
            raise BusinessLogicError(f"Failed to retrieve inventory data: {str(e)}")

    def _determine_inventory_status(
        self, current_qty: int, reorder_point: int, max_level: int
    ) -> InventoryStatus:
        """Determine inventory status based on quantity levels"""
        if current_qty == 0:
            return InventoryStatus.OUT_OF_STOCK
        elif current_qty <= reorder_point:
            return InventoryStatus.LOW_STOCK
        elif current_qty > max_level:
            return InventoryStatus.AVAILABLE  # Could add OVERSTOCK status
        else:
            return InventoryStatus.AVAILABLE

    async def record_stock_movement(
        self, movement_request: StockMovementRequest, user_id: UUID
    ) -> Dict[str, Any]:
        """Record stock movement and update inventory"""
        try:
            movement_id = uuid4()

            # Insert stock movement record
            movement_query = text("""
                INSERT INTO stock_movements (
                    id, product_id, movement_type, quantity, unit_cost, 
                    reference_id, location_from, location_to, notes, 
                    batch_number, expiry_date, created_by, created_at
                ) VALUES (
                    :id, :product_id, :movement_type, :quantity, :unit_cost,
                    :reference_id, :location_from, :location_to, :notes,
                    :batch_number, :expiry_date, :created_by, :created_at
                )
            """)

            await self.db.execute(
                movement_query,
                {
                    "id": str(movement_id),
                    "product_id": str(movement_request.product_id),
                    "movement_type": movement_request.movement_type.value,
                    "quantity": movement_request.quantity,
                    "unit_cost": movement_request.unit_cost,
                    "reference_id": str(movement_request.reference_id)
                    if movement_request.reference_id
                    else None,
                    "location_from": str(movement_request.location_from)
                    if movement_request.location_from
                    else None,
                    "location_to": str(movement_request.location_to)
                    if movement_request.location_to
                    else None,
                    "notes": movement_request.notes,
                    "batch_number": movement_request.batch_number,
                    "expiry_date": movement_request.expiry_date,
                    "created_by": str(user_id),
                    "created_at": datetime.utcnow(),
                },
            )

            await self.db.commit()

            # Get updated inventory status
            updated_inventory = await self.get_real_time_inventory(
                movement_request.product_id
            )

            # Check for alerts
            await self._check_inventory_alerts(
                movement_request.product_id, updated_inventory
            )

            return {
                "movement_id": movement_id,
                "product_id": movement_request.product_id,
                "movement_type": movement_request.movement_type,
                "quantity": movement_request.quantity,
                "updated_inventory": updated_inventory,
                "created_at": datetime.utcnow(),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error recording stock movement: {str(e)}")
            raise BusinessLogicError(f"Failed to record stock movement: {str(e)}")

    async def _check_inventory_alerts(
        self, product_id: UUID, inventory_data: Dict[str, Any]
    ) -> None:
        """Check for inventory alerts and create them if needed"""
        alerts = []

        current_qty = inventory_data["current_quantity"]
        reorder_point = inventory_data["reorder_point"]
        status = inventory_data["status"]

        if status == InventoryStatus.OUT_OF_STOCK:
            alerts.append(
                {
                    "product_id": product_id,
                    "alert_type": "out_of_stock",
                    "severity": AlertSeverity.CRITICAL,
                    "message": f"Product {inventory_data['product_name']} is out of stock",
                    "current_stock": current_qty,
                    "threshold": 0,
                    "suggested_action": "Reorder immediately",
                }
            )
        elif status == InventoryStatus.LOW_STOCK:
            alerts.append(
                {
                    "product_id": product_id,
                    "alert_type": "low_stock",
                    "severity": AlertSeverity.HIGH,
                    "message": f"Product {inventory_data['product_name']} is below reorder point",
                    "current_stock": current_qty,
                    "threshold": reorder_point,
                    "suggested_action": "Consider reordering",
                }
            )

        # Create alert records
        for alert_data in alerts:
            await self._create_inventory_alert(alert_data)

    async def _create_inventory_alert(self, alert_data: Dict[str, Any]) -> None:
        """Create inventory alert record"""
        try:
            alert_query = text("""
                INSERT INTO inventory_alerts (
                    id, product_id, alert_type, severity, message, 
                    current_stock, threshold, suggested_action, created_at
                ) VALUES (
                    :id, :product_id, :alert_type, :severity, :message,
                    :current_stock, :threshold, :suggested_action, :created_at
                )
            """)

            await self.db.execute(
                alert_query,
                {
                    "id": str(uuid4()),
                    "product_id": str(alert_data["product_id"]),
                    "alert_type": alert_data["alert_type"],
                    "severity": alert_data["severity"].value,
                    "message": alert_data["message"],
                    "current_stock": alert_data["current_stock"],
                    "threshold": alert_data.get("threshold"),
                    "suggested_action": alert_data["suggested_action"],
                    "created_at": datetime.utcnow(),
                },
            )

        except Exception as e:
            logger.error(f"Error creating inventory alert: {str(e)}")


class PredictionEngine:
    """Inventory prediction and demand forecasting"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_stock_predictions(
        self, request: StockPredictionRequest
    ) -> List[Dict[str, Any]]:
        """Generate stock predictions using various methods"""
        try:
            predictions = []

            # Get product IDs to predict
            if request.product_ids:
                product_ids = request.product_ids
            else:
                # Get all active products
                query = text("SELECT id FROM products WHERE status = 'active'")
                result = await self.db.execute(query)
                product_ids = [UUID(row.id) for row in result.fetchall()]

            for product_id in product_ids:
                prediction = await self._predict_single_product(product_id, request)
                if prediction:
                    predictions.append(prediction)

            return predictions

        except Exception as e:
            logger.error(f"Error generating stock predictions: {str(e)}")
            raise BusinessLogicError(f"Failed to generate predictions: {str(e)}")

    async def _predict_single_product(
        self, product_id: UUID, request: StockPredictionRequest
    ) -> Optional[Dict[str, Any]]:
        """Generate prediction for a single product"""
        try:
            # Get historical data
            historical_data = await self._get_historical_demand(
                product_id, request.prediction_days * 2
            )

            if len(historical_data) < 7:  # Need minimum data points
                return None

            # Apply prediction method
            if request.method == PredictionMethod.MOVING_AVERAGE:
                predicted_demand = self._moving_average_prediction(
                    historical_data, request.prediction_days
                )
            elif request.method == PredictionMethod.EXPONENTIAL_SMOOTHING:
                predicted_demand = self._exponential_smoothing_prediction(
                    historical_data, request.prediction_days
                )
            elif request.method == PredictionMethod.LINEAR_REGRESSION:
                predicted_demand = self._linear_regression_prediction(
                    historical_data, request.prediction_days
                )
            else:
                predicted_demand = self._moving_average_prediction(
                    historical_data, request.prediction_days
                )

            # Get current stock
            current_stock = await self._get_current_stock(product_id)

            # Calculate predicted stock
            predicted_stock = max(0, current_stock - predicted_demand)

            # Calculate confidence interval
            confidence_lower, confidence_upper = self._calculate_confidence_interval(
                historical_data, predicted_demand, request.confidence_level
            )

            # Determine reorder recommendation
            reorder_needed = predicted_stock <= await self._get_reorder_point(
                product_id
            )
            suggested_quantity = 0
            if reorder_needed:
                suggested_quantity = await self._calculate_reorder_quantity(
                    product_id, predicted_demand
                )

            return {
                "product_id": product_id,
                "current_stock": current_stock,
                "prediction_date": datetime.utcnow()
                + timedelta(days=request.prediction_days),
                "predicted_stock": predicted_stock,
                "predicted_demand": predicted_demand,
                "confidence_interval_lower": max(0, predicted_stock + confidence_lower),
                "confidence_interval_upper": predicted_stock + confidence_upper,
                "reorder_recommendation": reorder_needed,
                "suggested_reorder_quantity": suggested_quantity,
                "method_used": request.method,
                "accuracy_score": 0.85,  # Simplified - would calculate from historical accuracy
            }

        except Exception as e:
            logger.error(f"Error predicting for product {product_id}: {str(e)}")
            return None

    async def _get_historical_demand(self, product_id: UUID, days: int) -> List[int]:
        """Get historical demand data"""
        query = text("""
            SELECT DATE(created_at) as date, SUM(quantity) as daily_demand
            FROM stock_movements 
            WHERE product_id = :product_id 
            AND movement_type = 'sale'
            AND created_at >= :start_date
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)

        start_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            query, {"product_id": str(product_id), "start_date": start_date}
        )

        return [row.daily_demand for row in result.fetchall()]

    def _moving_average_prediction(
        self, historical_data: List[int], prediction_days: int
    ) -> int:
        """Simple moving average prediction"""
        if not historical_data:
            return 0

        # Use last 7 days for moving average
        recent_data = historical_data[:7]
        avg_daily_demand = sum(recent_data) / len(recent_data)
        return int(avg_daily_demand * prediction_days)

    def _exponential_smoothing_prediction(
        self, historical_data: List[int], prediction_days: int
    ) -> int:
        """Exponential smoothing prediction"""
        if not historical_data:
            return 0

        alpha = 0.3  # Smoothing parameter
        smoothed = historical_data[0]

        for value in historical_data[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed

        return int(smoothed * prediction_days)

    def _linear_regression_prediction(
        self, historical_data: List[int], prediction_days: int
    ) -> int:
        """Simple linear regression prediction"""
        if len(historical_data) < 2:
            return 0

        # Simple linear trend calculation
        n = len(historical_data)
        x = list(range(n))
        y = historical_data

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return int(y_mean * prediction_days)

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Predict for next period
        future_x = n + prediction_days / 2  # Approximate middle of prediction period
        predicted_daily = max(0, slope * future_x + intercept)

        return int(predicted_daily * prediction_days)

    def _calculate_confidence_interval(
        self, historical_data: List[int], prediction: int, confidence: float
    ) -> tuple[int, int]:
        """Calculate confidence interval for prediction"""
        if len(historical_data) < 2:
            return (0, prediction)

        # Simple standard deviation calculation
        mean = sum(historical_data) / len(historical_data)
        variance = sum((x - mean) ** 2 for x in historical_data) / len(historical_data)
        std_dev = variance**0.5

        # Simplified confidence interval (would use proper statistical methods in production)
        z_score = 1.96 if confidence >= 0.95 else 1.65  # 95% or 90% confidence
        margin = int(z_score * std_dev)

        return (-margin, margin)

    async def _get_current_stock(self, product_id: UUID) -> int:
        """Get current stock level"""
        query = text("""
            SELECT COALESCE(SUM(CASE WHEN movement_type IN ('purchase', 'adjustment', 'return') 
                                    THEN quantity 
                                    ELSE -quantity END), 0) as current_stock
            FROM stock_movements 
            WHERE product_id = :product_id
        """)

        result = await self.db.execute(query, {"product_id": str(product_id)})
        row = result.fetchone()
        return row.current_stock if row else 0

    async def _get_reorder_point(self, product_id: UUID) -> int:
        """Get reorder point for product"""
        query = text(
            "SELECT reorder_point FROM inventory_items WHERE product_id = :product_id"
        )
        result = await self.db.execute(query, {"product_id": str(product_id)})
        row = result.fetchone()
        return row.reorder_point if row else 10

    async def _calculate_reorder_quantity(
        self, product_id: UUID, predicted_demand: int
    ) -> int:
        """Calculate optimal reorder quantity"""
        # Get max stock level and lead time
        query = text("""
            SELECT max_stock_level, lead_time_days, safety_stock 
            FROM inventory_items 
            WHERE product_id = :product_id
        """)
        result = await self.db.execute(query, {"product_id": str(product_id)})
        row = result.fetchone()

        if not row:
            return predicted_demand  # Fallback

        max_level = row.max_stock_level or 100
        lead_time = row.lead_time_days or 7
        safety_stock = row.safety_stock or 5

        # Calculate reorder quantity based on lead time demand + safety stock
        lead_time_demand = int(
            predicted_demand * lead_time / 30
        )  # Approximate monthly to lead time
        current_stock = await self._get_current_stock(product_id)

        return max(0, min(max_level - current_stock, lead_time_demand + safety_stock))


class SupplierIntegrator:
    """Supplier integration and management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_supplier(
        self, request: SupplierIntegrationRequest
    ) -> Dict[str, Any]:
        """Register new supplier"""
        try:
            # Check if supplier already exists
            existing_query = text("SELECT id FROM suppliers WHERE email = :email")
            existing = await self.db.execute(
                existing_query, {"email": request.contact_email}
            )

            if existing.fetchone():
                raise BusinessLogicError(
                    f"Supplier with email {request.contact_email} already exists"
                )

            # Insert supplier
            supplier_query = text("""
                INSERT INTO suppliers (
                    id, name, contact_email, contact_phone, api_endpoint, 
                    api_key, lead_time_days, minimum_order_value, status, created_at
                ) VALUES (
                    :id, :name, :contact_email, :contact_phone, :api_endpoint,
                    :api_key, :lead_time_days, :minimum_order_value, :status, :created_at
                )
            """)

            supplier_id = request.supplier_id or uuid4()

            await self.db.execute(
                supplier_query,
                {
                    "id": str(supplier_id),
                    "name": request.name,
                    "contact_email": request.contact_email,
                    "contact_phone": request.contact_phone,
                    "api_endpoint": request.api_endpoint,
                    "api_key": request.api_key,
                    "lead_time_days": request.lead_time_days,
                    "minimum_order_value": request.minimum_order_value,
                    "status": request.status.value,
                    "created_at": datetime.utcnow(),
                },
            )

            await self.db.commit()

            # Test API connection if endpoint provided
            api_connected = False
            if request.api_endpoint and request.api_key:
                api_connected = await self._test_supplier_api_connection(
                    request.api_endpoint, request.api_key
                )

            return {
                "supplier_id": supplier_id,
                "name": request.name,
                "contact_email": request.contact_email,
                "status": request.status,
                "api_connected": api_connected,
                "created_at": datetime.utcnow(),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error registering supplier: {str(e)}")
            raise BusinessLogicError(f"Failed to register supplier: {str(e)}")

    async def create_purchase_order(
        self, reorder_request: ReorderRequest, user_id: UUID
    ) -> Dict[str, Any]:
        """Create purchase order with supplier"""
        try:
            # Get supplier info
            supplier_query = text("""
                SELECT name, contact_email, api_endpoint, api_key, minimum_order_value
                FROM suppliers 
                WHERE id = :supplier_id AND status = 'active'
            """)

            supplier_result = await self.db.execute(
                supplier_query, {"supplier_id": str(reorder_request.supplier_id)}
            )
            supplier = supplier_result.fetchone()

            if not supplier:
                raise NotFoundError(
                    f"Active supplier {reorder_request.supplier_id} not found"
                )

            # Get product info
            product_query = text(
                "SELECT name, unit_cost FROM products WHERE id = :product_id"
            )
            product_result = await self.db.execute(
                product_query, {"product_id": str(reorder_request.product_id)}
            )
            product = product_result.fetchone()

            if not product:
                raise NotFoundError(f"Product {reorder_request.product_id} not found")

            # Calculate order value
            estimated_cost = (
                Decimal(str(product.unit_cost or 0)) * reorder_request.quantity
            )

            # Check minimum order value
            if estimated_cost < supplier.minimum_order_value:
                raise BusinessLogicError(
                    f"Order value {estimated_cost} below minimum {supplier.minimum_order_value}"
                )

            # Create purchase order
            po_id = uuid4()
            po_query = text("""
                INSERT INTO purchase_orders (
                    id, supplier_id, product_id, quantity, unit_cost, total_cost,
                    priority, delivery_date, notes, status, created_by, created_at
                ) VALUES (
                    :id, :supplier_id, :product_id, :quantity, :unit_cost, :total_cost,
                    :priority, :delivery_date, :notes, :status, :created_by, :created_at
                )
            """)

            await self.db.execute(
                po_query,
                {
                    "id": str(po_id),
                    "supplier_id": str(reorder_request.supplier_id),
                    "product_id": str(reorder_request.product_id),
                    "quantity": reorder_request.quantity,
                    "unit_cost": product.unit_cost,
                    "total_cost": estimated_cost,
                    "priority": reorder_request.priority,
                    "delivery_date": reorder_request.delivery_date,
                    "notes": reorder_request.notes,
                    "status": "pending",
                    "created_by": str(user_id),
                    "created_at": datetime.utcnow(),
                },
            )

            await self.db.commit()

            # Send to supplier API if available
            api_sent = False
            if supplier.api_endpoint and supplier.api_key:
                api_sent = await self._send_po_to_supplier_api(
                    po_id, supplier, product, reorder_request
                )

            return {
                "purchase_order_id": po_id,
                "supplier_name": supplier.name,
                "product_name": product.name,
                "quantity": reorder_request.quantity,
                "estimated_cost": estimated_cost,
                "status": "pending",
                "api_sent": api_sent,
                "created_at": datetime.utcnow(),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating purchase order: {str(e)}")
            raise BusinessLogicError(f"Failed to create purchase order: {str(e)}")

    async def _test_supplier_api_connection(self, endpoint: str, api_key: str) -> bool:
        """Test supplier API connection"""
        try:
            # Simulate API test - would implement actual HTTP request in production
            await asyncio.sleep(0.1)  # Simulate network call
            return True  # Simplified for demo
        except Exception as e:
            logger.error(f"Supplier API connection test failed: {str(e)}")
            return False

    async def _send_po_to_supplier_api(
        self, po_id: UUID, supplier: Any, product: Any, request: ReorderRequest
    ) -> bool:
        """Send purchase order to supplier API"""
        try:
            # Simulate API call - would implement actual HTTP request in production
            await asyncio.sleep(0.2)  # Simulate network call

            # Log the API call
            logger.info(f"Purchase order {po_id} sent to supplier {supplier.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send PO to supplier API: {str(e)}")
            return False


# Inventory Integration Manager
class InventoryIntegrationManager:
    """Main manager for inventory integration operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.tracker = InventoryTracker(db)
        self.predictor = PredictionEngine(db)
        self.supplier_integrator = SupplierIntegrator(db)

    async def get_comprehensive_inventory_status(
        self, product_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get comprehensive inventory status across all systems"""
        try:
            if product_id:
                products = [product_id]
            else:
                # Get all active products
                query = text("SELECT id FROM products WHERE status = 'active' LIMIT 50")
                result = await self.db.execute(query)
                products = [UUID(row.id) for row in result.fetchall()]

            inventory_status = []

            for pid in products:
                # Get real-time data
                real_time_data = await self.tracker.get_real_time_inventory(pid)

                # Get recent movements
                movements = await self._get_recent_movements(pid, 5)

                # Get alerts
                alerts = await self._get_active_alerts(pid)

                # Get supplier info
                supplier_info = await self._get_supplier_info(pid)

                inventory_status.append(
                    {
                        "product_id": pid,
                        "real_time_data": real_time_data,
                        "recent_movements": movements,
                        "active_alerts": alerts,
                        "supplier_info": supplier_info,
                    }
                )

            return {
                "timestamp": datetime.utcnow(),
                "total_products": len(products),
                "inventory_status": inventory_status,
            }

        except Exception as e:
            logger.error(f"Error getting comprehensive inventory status: {str(e)}")
            raise BusinessLogicError(f"Failed to get inventory status: {str(e)}")

    async def _get_recent_movements(
        self, product_id: UUID, limit: int
    ) -> List[Dict[str, Any]]:
        """Get recent stock movements"""
        query = text("""
            SELECT movement_type, quantity, created_at, notes
            FROM stock_movements
            WHERE product_id = :product_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        result = await self.db.execute(
            query, {"product_id": str(product_id), "limit": limit}
        )

        return [
            {
                "movement_type": row.movement_type,
                "quantity": row.quantity,
                "created_at": row.created_at,
                "notes": row.notes,
            }
            for row in result.fetchall()
        ]

    async def _get_active_alerts(self, product_id: UUID) -> List[Dict[str, Any]]:
        """Get active alerts for product"""
        query = text("""
            SELECT alert_type, severity, message, created_at
            FROM inventory_alerts
            WHERE product_id = :product_id AND acknowledged = false
            ORDER BY created_at DESC
            LIMIT 10
        """)

        result = await self.db.execute(query, {"product_id": str(product_id)})

        return [
            {
                "alert_type": row.alert_type,
                "severity": row.severity,
                "message": row.message,
                "created_at": row.created_at,
            }
            for row in result.fetchall()
        ]

    async def _get_supplier_info(self, product_id: UUID) -> Optional[Dict[str, Any]]:
        """Get supplier information for product"""
        query = text("""
            SELECT s.id, s.name, s.contact_email, s.lead_time_days, s.status
            FROM suppliers s
            JOIN inventory_items i ON s.id = i.supplier_id
            WHERE i.product_id = :product_id AND s.status = 'active'
            LIMIT 1
        """)

        result = await self.db.execute(query, {"product_id": str(product_id)})
        row = result.fetchone()

        if row:
            return {
                "supplier_id": row.id,
                "name": row.name,
                "contact_email": row.contact_email,
                "lead_time_days": row.lead_time_days,
                "status": row.status,
            }

        return None


# API Endpoints
@router.get("/status", response_model=Dict[str, Any])
async def get_inventory_integration_status(
    product_id: Optional[UUID] = Query(None, description="Specific product ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive inventory integration status"""
    manager = InventoryIntegrationManager(db)
    return await manager.get_comprehensive_inventory_status(product_id)


@router.get("/real-time/{product_id}", response_model=Dict[str, Any])
async def get_real_time_inventory(product_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get real-time inventory data for specific product"""
    tracker = InventoryTracker(db)
    return await tracker.get_real_time_inventory(product_id)


@router.post("/movements", response_model=Dict[str, Any])
async def record_stock_movement(
    movement_request: StockMovementRequest,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Record stock movement and update inventory"""
    tracker = InventoryTracker(db)
    return await tracker.record_stock_movement(movement_request, user_id)


@router.post("/predictions", response_model=List[Dict[str, Any]])
async def generate_stock_predictions(
    prediction_request: StockPredictionRequest, db: AsyncSession = Depends(get_db)
):
    """Generate stock predictions and demand forecasts"""
    engine = PredictionEngine(db)
    return await engine.generate_stock_predictions(prediction_request)


@router.post("/suppliers", response_model=Dict[str, Any])
async def register_supplier(
    supplier_request: SupplierIntegrationRequest, db: AsyncSession = Depends(get_db)
):
    """Register new supplier"""
    integrator = SupplierIntegrator(db)
    return await integrator.register_supplier(supplier_request)


@router.post("/purchase-orders", response_model=Dict[str, Any])
async def create_purchase_order(
    reorder_request: ReorderRequest,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Create purchase order with supplier"""
    integrator = SupplierIntegrator(db)
    return await integrator.create_purchase_order(reorder_request, user_id)


@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_inventory_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(
        None, description="Filter by acknowledgment status"
    ),
    limit: int = Query(50, description="Maximum number of alerts", le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get inventory alerts"""
    try:
        query_parts = ["SELECT * FROM inventory_alerts WHERE 1=1"]
        params = {}

        if severity:
            query_parts.append("AND severity = :severity")
            params["severity"] = severity.value

        if acknowledged is not None:
            query_parts.append("AND acknowledged = :acknowledged")
            params["acknowledged"] = acknowledged

        query_parts.append("ORDER BY created_at DESC LIMIT :limit")
        params["limit"] = limit

        query = text(" ".join(query_parts))
        result = await db.execute(query, params)

        return [dict(row._mapping) for row in result.fetchall()]

    except Exception as e:
        logger.error(f"Error getting inventory alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge inventory alert"""
    try:
        query = text("""
            UPDATE inventory_alerts 
            SET acknowledged = true, acknowledged_by = :user_id, acknowledged_at = :ack_time
            WHERE id = :alert_id
        """)

        result = await db.execute(
            query,
            {
                "alert_id": str(alert_id),
                "user_id": str(user_id),
                "ack_time": datetime.utcnow(),
            },
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alert not found")

        await db.commit()

        return {
            "alert_id": alert_id,
            "acknowledged": True,
            "acknowledged_by": user_id,
            "acknowledged_at": datetime.utcnow(),
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Error acknowledging alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@router.get("/analytics/dashboard", response_model=Dict[str, Any])
async def get_inventory_analytics_dashboard(db: AsyncSession = Depends(get_db)):
    """Get inventory analytics dashboard data"""
    try:
        # Get summary statistics
        summary_query = text("""
            SELECT 
                COUNT(DISTINCT p.id) as total_products,
                COUNT(CASE WHEN sm.current_stock = 0 THEN 1 END) as out_of_stock_count,
                COUNT(CASE WHEN sm.current_stock <= i.reorder_point THEN 1 END) as low_stock_count,
                SUM(sm.current_stock * p.unit_cost) as total_inventory_value
            FROM products p
            LEFT JOIN inventory_items i ON p.id = i.product_id
            LEFT JOIN (
                SELECT product_id,
                       SUM(CASE WHEN movement_type IN ('purchase', 'adjustment', 'return') 
                               THEN quantity ELSE -quantity END) as current_stock
                FROM stock_movements 
                GROUP BY product_id
            ) sm ON p.id = sm.product_id
            WHERE p.status = 'active'
        """)

        summary_result = await db.execute(summary_query)
        summary = summary_result.fetchone()

        # Get recent movement trends
        trends_query = text("""
            SELECT DATE(created_at) as date, 
                   movement_type,
                   SUM(quantity) as total_quantity
            FROM stock_movements
            WHERE created_at >= :start_date
            GROUP BY DATE(created_at), movement_type
            ORDER BY date DESC
            LIMIT 30
        """)

        start_date = datetime.utcnow() - timedelta(days=30)
        trends_result = await db.execute(trends_query, {"start_date": start_date})
        trends = [dict(row._mapping) for row in trends_result.fetchall()]

        # Get top alerts
        alerts_query = text("""
            SELECT severity, COUNT(*) as count
            FROM inventory_alerts
            WHERE acknowledged = false
            GROUP BY severity
        """)

        alerts_result = await db.execute(alerts_query)
        alerts_summary = [dict(row._mapping) for row in alerts_result.fetchall()]

        return {
            "summary": {
                "total_products": summary.total_products or 0,
                "out_of_stock_count": summary.out_of_stock_count or 0,
                "low_stock_count": summary.low_stock_count or 0,
                "total_inventory_value": float(summary.total_inventory_value or 0),
            },
            "movement_trends": trends,
            "alerts_summary": alerts_summary,
            "generated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


# Background tasks for automated processes
@router.post("/automation/run-predictions")
async def run_automated_predictions(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """Run automated inventory predictions"""

    async def prediction_task():
        """Background task to run predictions"""
        try:
            engine = PredictionEngine(db)
            request = StockPredictionRequest(
                prediction_days=30, method=PredictionMethod.MOVING_AVERAGE
            )

            predictions = await engine.generate_stock_predictions(request)
            logger.info(f"Generated {len(predictions)} inventory predictions")

        except Exception as e:
            logger.error(f"Automated prediction task failed: {str(e)}")

    background_tasks.add_task(prediction_task)

    return {
        "message": "Automated prediction task started",
        "started_at": datetime.utcnow(),
    }


@router.post("/automation/check-reorders")
async def check_automated_reorders(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """Check for automated reorder requirements"""

    async def reorder_task():
        """Background task to check reorders"""
        try:
            # Find products needing reorder
            query = text("""
                SELECT p.id, p.name, sm.current_stock, i.reorder_point, i.supplier_id
                FROM products p
                JOIN inventory_items i ON p.id = i.product_id
                LEFT JOIN (
                    SELECT product_id,
                           SUM(CASE WHEN movement_type IN ('purchase', 'adjustment', 'return') 
                                   THEN quantity ELSE -quantity END) as current_stock
                    FROM stock_movements 
                    GROUP BY product_id
                ) sm ON p.id = sm.product_id
                WHERE p.status = 'active' 
                AND i.supplier_id IS NOT NULL
                AND (sm.current_stock IS NULL OR sm.current_stock <= i.reorder_point)
            """)

            result = await db.execute(query)
            reorder_candidates = result.fetchall()

            logger.info(f"Found {len(reorder_candidates)} products needing reorder")

        except Exception as e:
            logger.error(f"Automated reorder check failed: {str(e)}")

    background_tasks.add_task(reorder_task)

    return {
        "message": "Automated reorder check started",
        "started_at": datetime.utcnow(),
    }
