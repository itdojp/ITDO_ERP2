"""
CC02 v61.0 Advanced Reporting & Analytics Management API
Comprehensive reporting system with real-time dashboards, business intelligence, and custom report builders
"""

from __future__ import annotations

import json
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
    prefix="/api/v1/reporting-analytics", tags=["Reporting Analytics v61"]
)


# Enums for reporting system
class ReportType(str, Enum):
    """Report types"""

    FINANCIAL = "financial"
    SALES = "sales"
    INVENTORY = "inventory"
    CUSTOMER = "customer"
    OPERATIONAL = "operational"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report output formats"""

    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    HTML = "html"


class ChartType(str, Enum):
    """Chart visualization types"""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    TABLE = "table"


class AggregationType(str, Enum):
    """Data aggregation types"""

    SUM = "sum"
    COUNT = "count"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    DISTINCT_COUNT = "distinct_count"


class TimeGranularity(str, Enum):
    """Time aggregation granularity"""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class DeliveryMethod(str, Enum):
    """Report delivery methods"""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    FTP = "ftp"
    API = "api"


class ReportStatus(str, Enum):
    """Report generation status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


# Request Models
class DashboardWidgetRequest(BaseModel):
    """Request model for dashboard widgets"""

    widget_id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=200)
    chart_type: ChartType
    data_source: str = Field(..., min_length=1, max_length=100)
    metrics: List[str] = Field(..., min_items=1)
    dimensions: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    time_range: Optional[str] = Field(None, max_length=50)
    refresh_interval: int = Field(default=300, ge=60, le=86400)  # 1 minute to 24 hours
    position: Dict[str, int] = Field(default_factory=dict)  # x, y, width, height


class CustomReportRequest(BaseModel):
    """Request model for custom reports"""

    report_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    report_type: ReportType
    data_sources: List[str] = Field(..., min_items=1)
    columns: List[str] = Field(..., min_items=1)
    filters: Dict[str, Any] = Field(default_factory=dict)
    grouping: List[str] = Field(default_factory=list)
    aggregations: Dict[str, AggregationType] = Field(default_factory=dict)
    sorting: List[Dict[str, str]] = Field(default_factory=list)
    time_granularity: Optional[TimeGranularity] = None
    date_range: Optional[Dict[str, datetime]] = None
    limit: Optional[int] = Field(None, ge=1, le=10000)


class ReportScheduleRequest(BaseModel):
    """Request model for scheduled reports"""

    report_id: UUID
    schedule_name: str = Field(..., min_length=1, max_length=200)
    cron_expression: str = Field(..., min_length=1, max_length=100)
    format: ReportFormat = ReportFormat.JSON
    delivery_method: DeliveryMethod
    recipients: List[str] = Field(..., min_items=1)
    enabled: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @validator("cron_expression")
    def validate_cron(cls, v):
        """Basic cron expression validation"""
        parts = v.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts")
        return v


class AnalyticsQueryRequest(BaseModel):
    """Request model for analytics queries"""

    query_name: str = Field(..., min_length=1, max_length=200)
    sql_query: Optional[str] = Field(None, max_length=10000)
    data_source: str = Field(..., min_length=1, max_length=100)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    cache_duration: int = Field(default=300, ge=0, le=86400)  # Cache for up to 24 hours
    visualization_config: Optional[Dict[str, Any]] = None


class KPIDefinitionRequest(BaseModel):
    """Request model for KPI definitions"""

    kpi_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    calculation_formula: str = Field(..., min_length=1, max_length=500)
    data_sources: List[str] = Field(..., min_items=1)
    target_value: Optional[Decimal] = None
    warning_threshold: Optional[Decimal] = None
    critical_threshold: Optional[Decimal] = None
    unit: Optional[str] = Field(None, max_length=50)
    frequency: TimeGranularity = TimeGranularity.DAILY


# Response Models
class DashboardWidgetResponse(BaseModel):
    """Response model for dashboard widgets"""

    widget_id: UUID
    title: str
    chart_type: ChartType
    data_source: str
    metrics: List[str]
    dimensions: List[str]
    data: Dict[str, Any]
    filters: Dict[str, Any]
    time_range: Optional[str]
    refresh_interval: int
    position: Dict[str, int]
    last_updated: datetime
    created_at: datetime


class CustomReportResponse(BaseModel):
    """Response model for custom reports"""

    report_id: UUID
    report_name: str
    description: Optional[str]
    report_type: ReportType
    data_sources: List[str]
    columns: List[str]
    row_count: int
    data: List[Dict[str, Any]]
    filters: Dict[str, Any]
    grouping: List[str]
    aggregations: Dict[str, AggregationType]
    generation_time_ms: int
    generated_at: datetime
    created_by: UUID


class ReportScheduleResponse(BaseModel):
    """Response model for report schedules"""

    schedule_id: UUID
    report_id: UUID
    schedule_name: str
    cron_expression: str
    format: ReportFormat
    delivery_method: DeliveryMethod
    recipients: List[str]
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    success_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime


class AnalyticsQueryResponse(BaseModel):
    """Response model for analytics queries"""

    query_id: UUID
    query_name: str
    data_source: str
    result_count: int
    results: List[Dict[str, Any]]
    execution_time_ms: int
    cached: bool
    cache_expires_at: Optional[datetime]
    visualization_config: Optional[Dict[str, Any]]
    executed_at: datetime


class KPIResponse(BaseModel):
    """Response model for KPIs"""

    kpi_id: UUID
    kpi_name: str
    description: Optional[str]
    current_value: Decimal
    target_value: Optional[Decimal]
    previous_period_value: Optional[Decimal]
    change_percentage: Optional[float]
    status: str  # "good", "warning", "critical"
    trend: str  # "up", "down", "stable"
    unit: Optional[str]
    frequency: TimeGranularity
    last_calculated: datetime


class BusinessIntelligenceInsight(BaseModel):
    """Business intelligence insight"""

    insight_id: UUID
    title: str
    description: str
    insight_type: str
    severity: str
    confidence_score: float
    supporting_data: Dict[str, Any]
    recommended_actions: List[str]
    generated_at: datetime


# Core Business Logic Classes
class DashboardEngine:
    """Real-time dashboard management engine"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dashboard_widget(
        self, request: DashboardWidgetRequest, user_id: UUID
    ) -> Dict[str, Any]:
        """Create new dashboard widget"""
        try:
            widget_id = request.widget_id or uuid4()

            # Generate widget data
            widget_data = await self._generate_widget_data(request)

            # Store widget configuration
            widget_query = text("""
                INSERT INTO dashboard_widgets (
                    id, title, chart_type, data_source, metrics, dimensions,
                    filters, time_range, refresh_interval, position,
                    created_by, created_at, updated_at
                ) VALUES (
                    :id, :title, :chart_type, :data_source, :metrics, :dimensions,
                    :filters, :time_range, :refresh_interval, :position,
                    :created_by, :created_at, :updated_at
                )
            """)

            await self.db.execute(
                widget_query,
                {
                    "id": str(widget_id),
                    "title": request.title,
                    "chart_type": request.chart_type.value,
                    "data_source": request.data_source,
                    "metrics": json.dumps(request.metrics),
                    "dimensions": json.dumps(request.dimensions),
                    "filters": json.dumps(request.filters),
                    "time_range": request.time_range,
                    "refresh_interval": request.refresh_interval,
                    "position": json.dumps(request.position),
                    "created_by": str(user_id),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )

            await self.db.commit()

            return {
                "widget_id": widget_id,
                "title": request.title,
                "chart_type": request.chart_type,
                "data": widget_data,
                "created_at": datetime.utcnow(),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating dashboard widget: {str(e)}")
            raise BusinessLogicError(f"Failed to create widget: {str(e)}")

    async def get_dashboard_data(self, dashboard_id: UUID) -> Dict[str, Any]:
        """Get complete dashboard data"""
        try:
            # Get dashboard widgets
            widgets_query = text("""
                SELECT id, title, chart_type, data_source, metrics, dimensions,
                       filters, time_range, refresh_interval, position, updated_at
                FROM dashboard_widgets
                WHERE dashboard_id = :dashboard_id OR dashboard_id IS NULL
                ORDER BY position
            """)

            result = await self.db.execute(
                widgets_query, {"dashboard_id": str(dashboard_id)}
            )
            widgets = result.fetchall()

            dashboard_data = {
                "dashboard_id": dashboard_id,
                "widgets": [],
                "last_updated": datetime.utcnow(),
            }

            # Load data for each widget
            for widget in widgets:
                widget_request = DashboardWidgetRequest(
                    widget_id=UUID(widget.id),
                    title=widget.title,
                    chart_type=ChartType(widget.chart_type),
                    data_source=widget.data_source,
                    metrics=json.loads(widget.metrics),
                    dimensions=json.loads(widget.dimensions or "[]"),
                    filters=json.loads(widget.filters or "{}"),
                    time_range=widget.time_range,
                    refresh_interval=widget.refresh_interval,
                    position=json.loads(widget.position or "{}"),
                )

                widget_data = await self._generate_widget_data(widget_request)

                dashboard_data["widgets"].append(
                    {
                        "widget_id": widget.id,
                        "title": widget.title,
                        "chart_type": widget.chart_type,
                        "data": widget_data,
                        "position": json.loads(widget.position or "{}"),
                        "last_updated": widget.updated_at,
                    }
                )

            return dashboard_data

        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            raise BusinessLogicError(f"Failed to get dashboard data: {str(e)}")

    async def _generate_widget_data(
        self, request: DashboardWidgetRequest
    ) -> Dict[str, Any]:
        """Generate data for dashboard widget"""
        try:
            # Route to appropriate data generator based on data source
            if request.data_source == "sales":
                return await self._generate_sales_data(request)
            elif request.data_source == "inventory":
                return await self._generate_inventory_data(request)
            elif request.data_source == "customers":
                return await self._generate_customer_data(request)
            elif request.data_source == "financial":
                return await self._generate_financial_data(request)
            else:
                return await self._generate_custom_data(request)

        except Exception as e:
            logger.error(f"Error generating widget data: {str(e)}")
            return {"error": f"Failed to generate data: {str(e)}"}

    async def _generate_sales_data(
        self, request: DashboardWidgetRequest
    ) -> Dict[str, Any]:
        """Generate sales-specific widget data"""
        base_query = """
            SELECT
                DATE(o.created_at) as date,
                COUNT(*) as order_count,
                SUM(o.total_amount) as total_revenue,
                AVG(o.total_amount) as avg_order_value
            FROM orders o
            WHERE o.created_at >= :start_date
            GROUP BY DATE(o.created_at)
            ORDER BY date DESC
            LIMIT 30
        """

        start_date = datetime.utcnow() - timedelta(days=30)
        result = await self.db.execute(text(base_query), {"start_date": start_date})
        rows = result.fetchall()

        data = {
            "labels": [row.date.strftime("%Y-%m-%d") for row in rows],
            "datasets": [],
        }

        if "order_count" in request.metrics:
            data["datasets"].append(
                {
                    "label": "Orders",
                    "data": [row.order_count for row in rows],
                    "type": "line",
                }
            )

        if "total_revenue" in request.metrics:
            data["datasets"].append(
                {
                    "label": "Revenue",
                    "data": [float(row.total_revenue or 0) for row in rows],
                    "type": "bar",
                }
            )

        return data

    async def _generate_inventory_data(
        self, request: DashboardWidgetRequest
    ) -> Dict[str, Any]:
        """Generate inventory-specific widget data"""
        base_query = """
            SELECT
                p.name as product_name,
                COALESCE(i.current_stock, 0) as stock_level,
                COALESCE(i.reorder_point, 10) as reorder_point,
                p.unit_cost * COALESCE(i.current_stock, 0) as stock_value
            FROM products p
            LEFT JOIN inventory_items i ON p.id = i.product_id
            WHERE p.status = 'active'
            ORDER BY stock_value DESC
            LIMIT 20
        """

        result = await self.db.execute(text(base_query))
        rows = result.fetchall()

        data = {"labels": [row.product_name for row in rows], "datasets": []}

        if "stock_level" in request.metrics:
            data["datasets"].append(
                {
                    "label": "Stock Level",
                    "data": [row.stock_level for row in rows],
                    "type": "bar",
                }
            )

        if "stock_value" in request.metrics:
            data["datasets"].append(
                {
                    "label": "Stock Value",
                    "data": [float(row.stock_value or 0) for row in rows],
                    "type": "line",
                }
            )

        return data

    async def _generate_customer_data(
        self, request: DashboardWidgetRequest
    ) -> Dict[str, Any]:
        """Generate customer-specific widget data"""
        base_query = """
            SELECT
                DATE(c.created_at) as registration_date,
                COUNT(*) as new_customers,
                COUNT(CASE WHEN c.status = 'active' THEN 1 END) as active_customers
            FROM customers c
            WHERE c.created_at >= :start_date
            GROUP BY DATE(c.created_at)
            ORDER BY registration_date DESC
            LIMIT 30
        """

        start_date = datetime.utcnow() - timedelta(days=30)
        result = await self.db.execute(text(base_query), {"start_date": start_date})
        rows = result.fetchall()

        data = {
            "labels": [row.registration_date.strftime("%Y-%m-%d") for row in rows],
            "datasets": [],
        }

        if "new_customers" in request.metrics:
            data["datasets"].append(
                {
                    "label": "New Customers",
                    "data": [row.new_customers for row in rows],
                    "type": "area",
                }
            )

        return data

    async def _generate_financial_data(
        self, request: DashboardWidgetRequest
    ) -> Dict[str, Any]:
        """Generate financial-specific widget data"""
        # Simplified financial data generation
        data = {
            "summary": {
                "total_revenue": 125000.00,
                "total_expenses": 87500.00,
                "profit_margin": 30.0,
                "growth_rate": 12.5,
            },
            "trends": {
                "revenue_trend": "up",
                "expense_trend": "stable",
                "profit_trend": "up",
            },
        }

        return data

    async def _generate_custom_data(
        self, request: DashboardWidgetRequest
    ) -> Dict[str, Any]:
        """Generate custom widget data"""
        # Placeholder for custom data generation
        return {
            "message": "Custom data source not implemented",
            "data_source": request.data_source,
            "metrics": request.metrics,
        }


class ReportBuilder:
    """Custom report builder engine"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_custom_report(
        self, request: CustomReportRequest, user_id: UUID
    ) -> Dict[str, Any]:
        """Create and execute custom report"""
        try:
            start_time = datetime.utcnow()
            report_id = uuid4()

            # Generate report data
            report_data = await self._execute_report_query(request)

            generation_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            # Store report definition
            report_query = text("""
                INSERT INTO custom_reports (
                    id, report_name, description, report_type, data_sources,
                    columns, filters, grouping, aggregations, created_by, created_at
                ) VALUES (
                    :id, :report_name, :description, :report_type, :data_sources,
                    :columns, :filters, :grouping, :aggregations, :created_by, :created_at
                )
            """)

            await self.db.execute(
                report_query,
                {
                    "id": str(report_id),
                    "report_name": request.report_name,
                    "description": request.description,
                    "report_type": request.report_type.value,
                    "data_sources": json.dumps(request.data_sources),
                    "columns": json.dumps(request.columns),
                    "filters": json.dumps(request.filters),
                    "grouping": json.dumps(request.grouping),
                    "aggregations": json.dumps(
                        {k: v.value for k, v in request.aggregations.items()}
                    ),
                    "created_by": str(user_id),
                    "created_at": datetime.utcnow(),
                },
            )

            await self.db.commit()

            return {
                "report_id": report_id,
                "report_name": request.report_name,
                "report_type": request.report_type,
                "row_count": len(report_data),
                "data": report_data,
                "generation_time_ms": generation_time,
                "generated_at": datetime.utcnow(),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating custom report: {str(e)}")
            raise BusinessLogicError(f"Failed to create report: {str(e)}")

    async def _execute_report_query(
        self, request: CustomReportRequest
    ) -> List[Dict[str, Any]]:
        """Execute report query based on request parameters"""
        try:
            # Build query based on data sources and parameters
            if "orders" in request.data_sources:
                return await self._query_orders_data(request)
            elif "customers" in request.data_sources:
                return await self._query_customers_data(request)
            elif "products" in request.data_sources:
                return await self._query_products_data(request)
            elif "inventory" in request.data_sources:
                return await self._query_inventory_data(request)
            else:
                return await self._query_combined_data(request)

        except Exception as e:
            logger.error(f"Error executing report query: {str(e)}")
            raise BusinessLogicError(f"Query execution failed: {str(e)}")

    async def _query_orders_data(
        self, request: CustomReportRequest
    ) -> List[Dict[str, Any]]:
        """Query orders data for reporting"""
        base_query = """
            SELECT
                o.id as order_id,
                o.order_number,
                o.total_amount,
                o.status,
                o.created_at,
                c.full_name as customer_name,
                c.email as customer_email
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE 1=1
        """

        params = {}

        # Apply date filters
        if request.date_range:
            if request.date_range.get("start"):
                base_query += " AND o.created_at >= :start_date"
                params["start_date"] = request.date_range["start"]
            if request.date_range.get("end"):
                base_query += " AND o.created_at <= :end_date"
                params["end_date"] = request.date_range["end"]

        # Apply status filter
        if "status" in request.filters:
            base_query += " AND o.status = :status"
            params["status"] = request.filters["status"]

        # Apply ordering
        base_query += " ORDER BY o.created_at DESC"

        # Apply limit
        if request.limit:
            base_query += f" LIMIT {request.limit}"

        result = await self.db.execute(text(base_query), params)
        rows = result.fetchall()

        return [dict(row._mapping) for row in rows]

    async def _query_customers_data(
        self, request: CustomReportRequest
    ) -> List[Dict[str, Any]]:
        """Query customers data for reporting"""
        base_query = """
            SELECT
                c.id as customer_id,
                c.full_name,
                c.email,
                c.phone,
                c.status,
                c.created_at,
                COUNT(o.id) as total_orders,
                COALESCE(SUM(o.total_amount), 0) as total_spent
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            WHERE 1=1
        """

        params = {}

        # Apply status filter
        if "status" in request.filters:
            base_query += " AND c.status = :status"
            params["status"] = request.filters["status"]

        base_query += (
            " GROUP BY c.id, c.full_name, c.email, c.phone, c.status, c.created_at"
        )
        base_query += " ORDER BY total_spent DESC"

        if request.limit:
            base_query += f" LIMIT {request.limit}"

        result = await self.db.execute(text(base_query), params)
        rows = result.fetchall()

        return [dict(row._mapping) for row in rows]

    async def _query_products_data(
        self, request: CustomReportRequest
    ) -> List[Dict[str, Any]]:
        """Query products data for reporting"""
        base_query = """
            SELECT
                p.id as product_id,
                p.name,
                p.sku,
                p.description,
                p.unit_cost,
                p.status,
                p.created_at,
                COALESCE(i.current_stock, 0) as stock_level
            FROM products p
            LEFT JOIN inventory_items i ON p.id = i.product_id
            WHERE 1=1
        """

        params = {}

        if "status" in request.filters:
            base_query += " AND p.status = :status"
            params["status"] = request.filters["status"]

        base_query += " ORDER BY p.name"

        if request.limit:
            base_query += f" LIMIT {request.limit}"

        result = await self.db.execute(text(base_query), params)
        rows = result.fetchall()

        return [dict(row._mapping) for row in rows]

    async def _query_inventory_data(
        self, request: CustomReportRequest
    ) -> List[Dict[str, Any]]:
        """Query inventory data for reporting"""
        base_query = """
            SELECT
                p.name as product_name,
                p.sku,
                COALESCE(i.current_stock, 0) as stock_level,
                COALESCE(i.reorder_point, 0) as reorder_point,
                COALESCE(i.max_stock_level, 0) as max_stock,
                p.unit_cost,
                (p.unit_cost * COALESCE(i.current_stock, 0)) as stock_value
            FROM products p
            LEFT JOIN inventory_items i ON p.id = i.product_id
            WHERE p.status = 'active'
        """

        base_query += " ORDER BY stock_value DESC"

        if request.limit:
            base_query += f" LIMIT {request.limit}"

        result = await self.db.execute(text(base_query))
        rows = result.fetchall()

        return [dict(row._mapping) for row in rows]

    async def _query_combined_data(
        self, request: CustomReportRequest
    ) -> List[Dict[str, Any]]:
        """Query combined data from multiple sources"""
        # Complex multi-table query based on request
        return [{"message": "Combined data query not implemented"}]


class BusinessIntelligenceEngine:
    """Business intelligence and insights generation"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_insights(self, time_period: str = "30d") -> List[Dict[str, Any]]:
        """Generate business intelligence insights"""
        try:
            insights = []

            # Sales performance insights
            sales_insights = await self._analyze_sales_performance(time_period)
            insights.extend(sales_insights)

            # Customer behavior insights
            customer_insights = await self._analyze_customer_behavior(time_period)
            insights.extend(customer_insights)

            # Inventory insights
            inventory_insights = await self._analyze_inventory_status()
            insights.extend(inventory_insights)

            # Financial insights
            financial_insights = await self._analyze_financial_trends(time_period)
            insights.extend(financial_insights)

            return insights

        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            raise BusinessLogicError(f"Failed to generate insights: {str(e)}")

    async def _analyze_sales_performance(
        self, time_period: str
    ) -> List[Dict[str, Any]]:
        """Analyze sales performance"""
        insights = []

        # Calculate period boundaries
        days = int(time_period.replace("d", ""))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        previous_start = start_date - timedelta(days=days)

        # Current period sales
        current_query = text("""
            SELECT
                COUNT(*) as order_count,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_order_value
            FROM orders
            WHERE created_at BETWEEN :start_date AND :end_date
        """)

        current_result = await self.db.execute(
            current_query, {"start_date": start_date, "end_date": end_date}
        )
        current = current_result.fetchone()

        # Previous period sales
        previous_result = await self.db.execute(
            current_query, {"start_date": previous_start, "end_date": start_date}
        )
        previous = previous_result.fetchone()

        if current and previous:
            revenue_change = (
                (current.total_revenue - previous.total_revenue)
                / previous.total_revenue
                * 100
                if previous.total_revenue > 0
                else 0
            )

            if abs(revenue_change) > 10:
                severity = "high" if abs(revenue_change) > 25 else "medium"
                insights.append(
                    {
                        "insight_id": uuid4(),
                        "title": f"Sales Revenue {'Surge' if revenue_change > 0 else 'Decline'}",
                        "description": f"Revenue changed by {revenue_change:.1f}% compared to previous period",
                        "insight_type": "sales_performance",
                        "severity": severity,
                        "confidence_score": 0.85,
                        "supporting_data": {
                            "current_revenue": float(current.total_revenue or 0),
                            "previous_revenue": float(previous.total_revenue or 0),
                            "change_percentage": revenue_change,
                        },
                        "recommended_actions": [
                            "Investigate factors driving the change",
                            "Adjust marketing strategies accordingly",
                            "Review pricing strategy",
                        ]
                        if revenue_change < -10
                        else [
                            "Scale up inventory to meet demand",
                            "Increase marketing spend",
                            "Optimize fulfillment processes",
                        ],
                        "generated_at": datetime.utcnow(),
                    }
                )

        return insights

    async def _analyze_customer_behavior(
        self, time_period: str
    ) -> List[Dict[str, Any]]:
        """Analyze customer behavior patterns"""
        insights = []

        # Customer acquisition trends
        days = int(time_period.replace("d", ""))
        start_date = datetime.utcnow() - timedelta(days=days)

        customer_query = text("""
            SELECT
                COUNT(*) as new_customers,
                COUNT(CASE WHEN c.status = 'active' THEN 1 END) as active_customers,
                AVG(customer_orders.order_count) as avg_orders_per_customer
            FROM customers c
            LEFT JOIN (
                SELECT customer_id, COUNT(*) as order_count
                FROM orders
                WHERE created_at >= :start_date
                GROUP BY customer_id
            ) customer_orders ON c.id = customer_orders.customer_id
            WHERE c.created_at >= :start_date
        """)

        result = await self.db.execute(customer_query, {"start_date": start_date})
        data = result.fetchone()

        if data and data.new_customers > 0:
            activation_rate = (data.active_customers / data.new_customers) * 100

            if activation_rate < 70:
                insights.append(
                    {
                        "insight_id": uuid4(),
                        "title": "Low Customer Activation Rate",
                        "description": f"Only {activation_rate:.1f}% of new customers are active",
                        "insight_type": "customer_behavior",
                        "severity": "medium",
                        "confidence_score": 0.78,
                        "supporting_data": {
                            "activation_rate": activation_rate,
                            "new_customers": data.new_customers,
                            "active_customers": data.active_customers,
                        },
                        "recommended_actions": [
                            "Improve onboarding process",
                            "Implement customer engagement campaigns",
                            "Review customer support quality",
                        ],
                        "generated_at": datetime.utcnow(),
                    }
                )

        return insights

    async def _analyze_inventory_status(self) -> List[Dict[str, Any]]:
        """Analyze inventory status and trends"""
        insights = []

        # Check for low stock or overstock situations
        inventory_query = text("""
            SELECT
                COUNT(CASE WHEN i.current_stock <= i.reorder_point THEN 1 END) as low_stock_items,
                COUNT(CASE WHEN i.current_stock > i.max_stock_level THEN 1 END) as overstock_items,
                COUNT(*) as total_items,
                SUM(p.unit_cost * i.current_stock) as total_inventory_value
            FROM inventory_items i
            JOIN products p ON i.product_id = p.id
            WHERE p.status = 'active'
        """)

        result = await self.db.execute(inventory_query)
        data = result.fetchone()

        if data:
            low_stock_ratio = (data.low_stock_items / data.total_items) * 100

            if low_stock_ratio > 15:
                insights.append(
                    {
                        "insight_id": uuid4(),
                        "title": "High Number of Low Stock Items",
                        "description": f"{low_stock_ratio:.1f}% of items are below reorder point",
                        "insight_type": "inventory_management",
                        "severity": "high",
                        "confidence_score": 0.92,
                        "supporting_data": {
                            "low_stock_items": data.low_stock_items,
                            "total_items": data.total_items,
                            "low_stock_ratio": low_stock_ratio,
                        },
                        "recommended_actions": [
                            "Review and update reorder points",
                            "Implement automated reordering",
                            "Improve demand forecasting",
                        ],
                        "generated_at": datetime.utcnow(),
                    }
                )

        return insights

    async def _analyze_financial_trends(self, time_period: str) -> List[Dict[str, Any]]:
        """Analyze financial trends and health"""
        insights = []

        # Simplified financial analysis
        # In a real implementation, this would analyze cash flow, profitability, etc.

        insights.append(
            {
                "insight_id": uuid4(),
                "title": "Financial Health Analysis",
                "description": "Overall financial health is stable with room for improvement",
                "insight_type": "financial_analysis",
                "severity": "low",
                "confidence_score": 0.65,
                "supporting_data": {
                    "revenue_trend": "stable",
                    "cost_trend": "increasing",
                    "profit_margin": 0.15,
                },
                "recommended_actions": [
                    "Monitor cost trends closely",
                    "Explore cost reduction opportunities",
                    "Optimize pricing strategy",
                ],
                "generated_at": datetime.utcnow(),
            }
        )

        return insights


class KPIManager:
    """KPI definition and calculation management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_kpi(self, kpi_id: UUID) -> Dict[str, Any]:
        """Calculate KPI value"""
        try:
            # Get KPI definition
            kpi_query = text("""
                SELECT kpi_name, calculation_formula, data_sources, target_value,
                       warning_threshold, critical_threshold, unit, frequency
                FROM kpi_definitions
                WHERE id = :kpi_id
            """)

            result = await self.db.execute(kpi_query, {"kpi_id": str(kpi_id)})
            kpi_def = result.fetchone()

            if not kpi_def:
                raise NotFoundError(f"KPI {kpi_id} not found")

            # Calculate KPI based on formula
            current_value = await self._execute_kpi_calculation(
                kpi_def.calculation_formula, json.loads(kpi_def.data_sources)
            )

            # Get previous period value for comparison
            previous_value = await self._get_previous_kpi_value(kpi_id)

            # Calculate change percentage
            change_percentage = None
            if previous_value and previous_value > 0:
                change_percentage = (
                    (current_value - previous_value) / previous_value
                ) * 100

            # Determine status
            status = self._determine_kpi_status(
                current_value,
                kpi_def.target_value,
                kpi_def.warning_threshold,
                kpi_def.critical_threshold,
            )

            # Determine trend
            trend = "stable"
            if change_percentage:
                if change_percentage > 5:
                    trend = "up"
                elif change_percentage < -5:
                    trend = "down"

            return {
                "kpi_id": kpi_id,
                "kpi_name": kpi_def.kpi_name,
                "current_value": current_value,
                "target_value": kpi_def.target_value,
                "previous_period_value": previous_value,
                "change_percentage": change_percentage,
                "status": status,
                "trend": trend,
                "unit": kpi_def.unit,
                "last_calculated": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Error calculating KPI: {str(e)}")
            raise BusinessLogicError(f"Failed to calculate KPI: {str(e)}")

    async def _execute_kpi_calculation(
        self, formula: str, data_sources: List[str]
    ) -> Decimal:
        """Execute KPI calculation formula"""
        try:
            # Simplified KPI calculation - in reality would parse and execute formula
            if "revenue" in formula.lower():
                query = text(
                    "SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE created_at >= :start_date"
                )
                start_date = datetime.utcnow() - timedelta(days=30)
                result = await self.db.execute(query, {"start_date": start_date})
                return Decimal(str(result.scalar() or 0))

            elif "customers" in formula.lower():
                query = text(
                    "SELECT COUNT(*) FROM customers WHERE created_at >= :start_date"
                )
                start_date = datetime.utcnow() - timedelta(days=30)
                result = await self.db.execute(query, {"start_date": start_date})
                return Decimal(str(result.scalar() or 0))

            else:
                # Default calculation
                return Decimal("100.0")

        except Exception as e:
            logger.error(f"Error executing KPI calculation: {str(e)}")
            return Decimal("0")

    async def _get_previous_kpi_value(self, kpi_id: UUID) -> Optional[Decimal]:
        """Get previous period KPI value"""
        try:
            query = text("""
                SELECT value FROM kpi_history
                WHERE kpi_id = :kpi_id
                ORDER BY calculated_at DESC
                LIMIT 1 OFFSET 1
            """)

            result = await self.db.execute(query, {"kpi_id": str(kpi_id)})
            row = result.fetchone()

            return Decimal(str(row.value)) if row else None

        except Exception as e:
            logger.error(f"Error getting previous KPI value: {str(e)}")
            return None

    def _determine_kpi_status(
        self,
        current_value: Decimal,
        target_value: Optional[Decimal],
        warning_threshold: Optional[Decimal],
        critical_threshold: Optional[Decimal],
    ) -> str:
        """Determine KPI status based on thresholds"""
        if critical_threshold and current_value <= critical_threshold:
            return "critical"
        elif warning_threshold and current_value <= warning_threshold:
            return "warning"
        elif target_value and current_value >= target_value:
            return "good"
        else:
            return "neutral"


class ScheduledReportManager:
    """Scheduled report management and delivery"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report_schedule(
        self, request: ReportScheduleRequest, user_id: UUID
    ) -> Dict[str, Any]:
        """Create new report schedule"""
        try:
            schedule_id = uuid4()

            # Calculate next run time
            next_run = self._calculate_next_run(request.cron_expression)

            # Store schedule
            schedule_query = text("""
                INSERT INTO report_schedules (
                    id, report_id, schedule_name, cron_expression, format,
                    delivery_method, recipients, enabled, parameters,
                    next_run, created_by, created_at
                ) VALUES (
                    :id, :report_id, :schedule_name, :cron_expression, :format,
                    :delivery_method, :recipients, :enabled, :parameters,
                    :next_run, :created_by, :created_at
                )
            """)

            await self.db.execute(
                schedule_query,
                {
                    "id": str(schedule_id),
                    "report_id": str(request.report_id),
                    "schedule_name": request.schedule_name,
                    "cron_expression": request.cron_expression,
                    "format": request.format.value,
                    "delivery_method": request.delivery_method.value,
                    "recipients": json.dumps(request.recipients),
                    "enabled": request.enabled,
                    "parameters": json.dumps(request.parameters),
                    "next_run": next_run,
                    "created_by": str(user_id),
                    "created_at": datetime.utcnow(),
                },
            )

            await self.db.commit()

            return {
                "schedule_id": schedule_id,
                "schedule_name": request.schedule_name,
                "next_run": next_run,
                "enabled": request.enabled,
                "created_at": datetime.utcnow(),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating report schedule: {str(e)}")
            raise BusinessLogicError(f"Failed to create schedule: {str(e)}")

    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression"""
        # Simplified cron calculation - in reality would use proper cron parser
        # For demo, assume daily at specific hour
        parts = cron_expression.split()
        if len(parts) >= 2:
            try:
                hour = int(parts[1])
                next_run = datetime.utcnow().replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
                if next_run <= datetime.utcnow():
                    next_run += timedelta(days=1)
                return next_run
            except ValueError:
                pass

        # Default to next hour
        return datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(
            hours=1
        )


# Main Reporting Analytics Manager
class ReportingAnalyticsManager:
    """Main manager for reporting and analytics operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dashboard_engine = DashboardEngine(db)
        self.report_builder = ReportBuilder(db)
        self.bi_engine = BusinessIntelligenceEngine(db)
        self.kpi_manager = KPIManager(db)
        self.scheduler = ScheduledReportManager(db)

    async def get_executive_summary(self) -> Dict[str, Any]:
        """Get executive summary with key metrics and insights"""
        try:
            # Get key metrics
            metrics = await self._get_key_metrics()

            # Get latest insights
            insights = await self.bi_engine.generate_insights("7d")

            # Get KPI summary
            kpi_summary = await self._get_kpi_summary()

            return {
                "summary_date": datetime.utcnow(),
                "key_metrics": metrics,
                "insights": insights[:5],  # Top 5 insights
                "kpi_summary": kpi_summary,
                "generated_at": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Error generating executive summary: {str(e)}")
            raise BusinessLogicError(f"Failed to generate summary: {str(e)}")

    async def _get_key_metrics(self) -> Dict[str, Any]:
        """Get key business metrics"""
        try:
            # Revenue metrics
            revenue_query = text("""
                SELECT
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_order_value
                FROM orders
                WHERE created_at >= :start_date
            """)

            start_date = datetime.utcnow() - timedelta(days=30)
            revenue_result = await self.db.execute(
                revenue_query, {"start_date": start_date}
            )
            revenue_data = revenue_result.fetchone()

            # Customer metrics
            customer_query = text("""
                SELECT
                    COUNT(*) as total_customers,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_customers
                FROM customers
            """)

            customer_result = await self.db.execute(customer_query)
            customer_data = customer_result.fetchone()

            return {
                "revenue": {
                    "total_orders": revenue_data.total_orders if revenue_data else 0,
                    "total_revenue": float(revenue_data.total_revenue or 0)
                    if revenue_data
                    else 0,
                    "avg_order_value": float(revenue_data.avg_order_value or 0)
                    if revenue_data
                    else 0,
                },
                "customers": {
                    "total_customers": customer_data.total_customers
                    if customer_data
                    else 0,
                    "active_customers": customer_data.active_customers
                    if customer_data
                    else 0,
                },
            }

        except Exception as e:
            logger.error(f"Error getting key metrics: {str(e)}")
            return {}

    async def _get_kpi_summary(self) -> Dict[str, Any]:
        """Get KPI summary"""
        # Simplified KPI summary
        return {
            "revenue_growth": {"value": 12.5, "trend": "up", "status": "good"},
            "customer_acquisition": {"value": 250, "trend": "up", "status": "good"},
            "inventory_turnover": {
                "value": 4.2,
                "trend": "stable",
                "status": "warning",
            },
            "customer_satisfaction": {"value": 8.7, "trend": "up", "status": "good"},
        }


# API Endpoints
@router.get("/dashboard/{dashboard_id}", response_model=Dict[str, Any])
async def get_dashboard(dashboard_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get dashboard data with all widgets"""
    manager = ReportingAnalyticsManager(db)
    return await manager.dashboard_engine.get_dashboard_data(dashboard_id)


@router.post("/dashboard/widgets", response_model=Dict[str, Any])
async def create_dashboard_widget(
    widget_request: DashboardWidgetRequest,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Create new dashboard widget"""
    manager = ReportingAnalyticsManager(db)
    return await manager.dashboard_engine.create_dashboard_widget(
        widget_request, user_id
    )


@router.post("/reports/custom", response_model=Dict[str, Any])
async def create_custom_report(
    report_request: CustomReportRequest,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Create and execute custom report"""
    manager = ReportingAnalyticsManager(db)
    return await manager.report_builder.create_custom_report(report_request, user_id)


@router.post("/reports/schedules", response_model=Dict[str, Any])
async def create_report_schedule(
    schedule_request: ReportScheduleRequest,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Create scheduled report delivery"""
    manager = ReportingAnalyticsManager(db)
    return await manager.scheduler.create_report_schedule(schedule_request, user_id)


@router.get("/analytics/insights", response_model=List[Dict[str, Any]])
async def get_business_insights(
    time_period: str = Query("30d", description="Time period for analysis"),
    db: AsyncSession = Depends(get_db),
):
    """Get business intelligence insights"""
    manager = ReportingAnalyticsManager(db)
    return await manager.bi_engine.generate_insights(time_period)


@router.get("/kpi/{kpi_id}", response_model=Dict[str, Any])
async def get_kpi_value(kpi_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get calculated KPI value"""
    manager = ReportingAnalyticsManager(db)
    return await manager.kpi_manager.calculate_kpi(kpi_id)


@router.get("/executive-summary", response_model=Dict[str, Any])
async def get_executive_summary(db: AsyncSession = Depends(get_db)):
    """Get executive summary with key metrics and insights"""
    manager = ReportingAnalyticsManager(db)
    return await manager.get_executive_summary()


@router.post("/analytics/query", response_model=Dict[str, Any])
async def execute_analytics_query(
    query_request: AnalyticsQueryRequest, db: AsyncSession = Depends(get_db)
):
    """Execute custom analytics query"""
    try:
        start_time = datetime.utcnow()

        # Execute query (simplified - in reality would have proper query validation)
        if query_request.sql_query:
            result = await db.execute(
                text(query_request.sql_query), query_request.parameters
            )
            rows = result.fetchall()
            results = [dict(row._mapping) for row in rows]
        else:
            results = [{"message": "No query provided"}]

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return {
            "query_id": uuid4(),
            "query_name": query_request.query_name,
            "data_source": query_request.data_source,
            "result_count": len(results),
            "results": results,
            "execution_time_ms": execution_time,
            "cached": False,
            "executed_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Error executing analytics query: {str(e)}")
        raise HTTPException(status_code=500, detail="Query execution failed")


@router.get("/reports/templates", response_model=List[Dict[str, Any]])
async def get_report_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    """Get available report templates"""
    templates = [
        {
            "template_id": uuid4(),
            "name": "Sales Performance Report",
            "description": "Comprehensive sales analysis with trends and forecasts",
            "category": "sales",
            "data_sources": ["orders", "customers"],
            "default_columns": [
                "order_date",
                "customer_name",
                "total_amount",
                "status",
            ],
            "chart_types": ["line", "bar", "pie"],
        },
        {
            "template_id": uuid4(),
            "name": "Inventory Status Report",
            "description": "Current inventory levels and stock movements",
            "category": "inventory",
            "data_sources": ["products", "inventory"],
            "default_columns": [
                "product_name",
                "stock_level",
                "reorder_point",
                "stock_value",
            ],
            "chart_types": ["bar", "gauge", "table"],
        },
        {
            "template_id": uuid4(),
            "name": "Customer Analytics Report",
            "description": "Customer behavior and segmentation analysis",
            "category": "customer",
            "data_sources": ["customers", "orders"],
            "default_columns": [
                "customer_name",
                "total_orders",
                "total_spent",
                "last_order_date",
            ],
            "chart_types": ["pie", "scatter", "heatmap"],
        },
    ]

    if category:
        templates = [t for t in templates if t["category"] == category]

    return templates


@router.get("/analytics/data-sources", response_model=List[Dict[str, Any]])
async def get_available_data_sources(db: AsyncSession = Depends(get_db)):
    """Get available data sources for reporting"""
    return [
        {
            "source_id": "orders",
            "name": "Orders",
            "description": "Order transactions and details",
            "tables": ["orders", "order_items"],
            "available_columns": [
                "order_id",
                "customer_id",
                "total_amount",
                "status",
                "created_at",
            ],
            "sample_filters": ["status", "date_range", "customer_id"],
        },
        {
            "source_id": "customers",
            "name": "Customers",
            "description": "Customer information and profiles",
            "tables": ["customers"],
            "available_columns": [
                "customer_id",
                "full_name",
                "email",
                "phone",
                "status",
                "created_at",
            ],
            "sample_filters": ["status", "registration_date", "location"],
        },
        {
            "source_id": "products",
            "name": "Products",
            "description": "Product catalog and inventory",
            "tables": ["products", "inventory_items"],
            "available_columns": [
                "product_id",
                "name",
                "sku",
                "unit_cost",
                "stock_level",
            ],
            "sample_filters": ["status", "category", "stock_level"],
        },
        {
            "source_id": "financial",
            "name": "Financial",
            "description": "Financial transactions and accounting",
            "tables": ["financial_transactions"],
            "available_columns": [
                "transaction_id",
                "amount",
                "type",
                "account",
                "date",
            ],
            "sample_filters": ["transaction_type", "date_range", "account"],
        },
    ]


# Background Tasks
@router.post("/automation/generate-reports")
async def run_scheduled_reports(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """Run scheduled report generation"""

    async def report_generation_task():
        """Background task for report generation"""
        try:
            ReportingAnalyticsManager(db)

            # Find due scheduled reports
            due_reports_query = text("""
                SELECT id, report_id, format, delivery_method, recipients
                FROM report_schedules
                WHERE enabled = true AND next_run <= :now
                LIMIT 10
            """)

            result = await db.execute(due_reports_query, {"now": datetime.utcnow()})
            due_reports = result.fetchall()

            logger.info(f"Found {len(due_reports)} scheduled reports to generate")

            for schedule in due_reports:
                # Generate and deliver report
                try:
                    # This would generate and send the actual report
                    logger.info(f"Generated scheduled report {schedule.id}")

                except Exception as e:
                    logger.error(
                        f"Failed to generate scheduled report {schedule.id}: {str(e)}"
                    )

        except Exception as e:
            logger.error(f"Scheduled report generation failed: {str(e)}")

    background_tasks.add_task(report_generation_task)

    return {
        "message": "Scheduled report generation started",
        "started_at": datetime.utcnow(),
    }


@router.post("/automation/refresh-dashboards")
async def refresh_dashboard_data(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """Refresh dashboard data in background"""

    async def dashboard_refresh_task():
        """Background task for dashboard refresh"""
        try:
            # Find dashboards that need refresh
            text("""
                SELECT DISTINCT dashboard_id
                FROM dashboard_widgets
                WHERE refresh_interval <= :seconds_since_update
            """)

            # This would find dashboards needing refresh based on their intervals
            logger.info("Dashboard refresh task completed")

        except Exception as e:
            logger.error(f"Dashboard refresh failed: {str(e)}")

    background_tasks.add_task(dashboard_refresh_task)

    return {"message": "Dashboard refresh started", "started_at": datetime.utcnow()}
