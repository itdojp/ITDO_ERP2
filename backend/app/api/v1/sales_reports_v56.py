"""
CC02 v56.0 Sales Reports API
Advanced Sales Analytics and Reporting System
1-day implementation focusing on practical business intelligence
"""

from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import asyncio
import json
from io import StringIO
import csv

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text, desc, asc, case
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field, validator

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.exceptions import ValidationError, NotFoundError
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product, ProductCategory
from app.models.user import User

router = APIRouter(prefix="/sales/reports", tags=["sales-reports-v56"])

# Enums for Report Configuration
class ReportPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class ReportType(str, Enum):
    REVENUE_SUMMARY = "revenue_summary"
    PRODUCT_PERFORMANCE = "product_performance"
    CUSTOMER_ANALYSIS = "customer_analysis"
    REGIONAL_COMPARISON = "regional_comparison"
    TREND_ANALYSIS = "trend_analysis"
    SALES_FUNNEL = "sales_funnel"

class AggregationType(str, Enum):
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"

# Request Models
class SalesReportRequest(BaseModel):
    report_type: ReportType
    period: ReportPeriod
    start_date: date
    end_date: date
    filters: Dict[str, Any] = Field(default_factory=dict)
    groupby: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=lambda: ["revenue", "quantity", "orders"])
    include_comparison: bool = Field(default=False)
    comparison_period: Optional[ReportPeriod] = None

    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v < start_date:
            raise ValueError('end_date must be after start_date')
        if start_date and (v - start_date).days > 365:
            raise ValueError('date range cannot exceed 365 days')
        return v

class SalesAnalyticsRequest(BaseModel):
    metrics: List[str] = Field(default_factory=lambda: ["revenue", "growth_rate", "conversion_rate"])
    period: ReportPeriod = ReportPeriod.MONTHLY
    date_range: int = Field(default=12, ge=1, le=36)  # months
    segments: List[str] = Field(default_factory=list)
    include_forecasting: bool = Field(default=False)

class ProductPerformanceRequest(BaseModel):
    period: ReportPeriod
    start_date: date
    end_date: date
    category_id: Optional[UUID] = None
    top_n: int = Field(default=10, ge=1, le=100)
    sort_by: str = Field(default="revenue")
    include_trends: bool = Field(default=True)

class CustomerAnalysisRequest(BaseModel):
    period: ReportPeriod
    start_date: date
    end_date: date
    segment_by: str = Field(default="value")  # value, geography, industry
    include_cohort_analysis: bool = Field(default=False)
    include_lifetime_value: bool = Field(default=True)

# Response Models
class SalesMetrics(BaseModel):
    total_revenue: Decimal
    total_orders: int
    total_quantity: int
    average_order_value: Decimal
    conversion_rate: float
    growth_rate: Optional[float] = None
    period_label: str

class ProductPerformanceItem(BaseModel):
    product_id: UUID
    product_name: str
    product_sku: str
    category_name: Optional[str] = None
    revenue: Decimal
    quantity_sold: int
    orders_count: int
    average_price: Decimal
    growth_rate: Optional[float] = None
    market_share: Optional[float] = None

class CustomerSegmentItem(BaseModel):
    segment: str
    customer_count: int
    total_revenue: Decimal
    average_revenue_per_customer: Decimal
    average_order_frequency: float
    lifetime_value: Optional[Decimal] = None

class RegionalPerformanceItem(BaseModel):
    region: str
    revenue: Decimal
    orders_count: int
    customer_count: int
    growth_rate: Optional[float] = None
    market_penetration: Optional[float] = None

class SalesReportResponse(BaseModel):
    report_id: str
    report_type: ReportType
    period: ReportPeriod
    date_range: Dict[str, date]
    metrics: SalesMetrics
    data: List[Dict[str, Any]]
    comparison_data: Optional[List[Dict[str, Any]]] = None
    generated_at: datetime
    filters_applied: Dict[str, Any]

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

# Core Analytics Service
class SalesAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_revenue_summary(
        self, 
        start_date: date, 
        end_date: date,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive revenue summary report"""
        
        # Base query for orders in date range
        base_query = select(
            func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue'),
            func.count(func.distinct(Order.id)).label('total_orders'),
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.avg(Order.total_amount).label('average_order_value')
        ).select_from(
            Order.__table__.join(OrderItem.__table__)
        ).where(
            and_(
                Order.order_date >= start_date,
                Order.order_date <= end_date,
                Order.status.in_(['completed', 'shipped', 'delivered'])
            )
        )

        # Apply additional filters
        if filters:
            if 'customer_ids' in filters:
                base_query = base_query.where(Order.customer_id.in_(filters['customer_ids']))
            if 'product_categories' in filters:
                base_query = base_query.join(Product).where(
                    Product.category_id.in_(filters['product_categories'])
                )

        result = await self.db.execute(base_query)
        summary = result.first()

        # Calculate conversion rate (simplified)
        total_sessions = 1000  # Would get from analytics service
        conversion_rate = (summary.total_orders / total_sessions * 100) if total_sessions > 0 else 0

        return {
            'total_revenue': summary.total_revenue or Decimal('0'),
            'total_orders': summary.total_orders or 0,
            'total_quantity': summary.total_quantity or 0,
            'average_order_value': summary.average_order_value or Decimal('0'),
            'conversion_rate': round(conversion_rate, 2)
        }

    async def get_product_performance(
        self,
        start_date: date,
        end_date: date,
        top_n: int = 10,
        sort_by: str = "revenue"
    ) -> List[ProductPerformanceItem]:
        """Get top performing products by various metrics"""
        
        query = select(
            Product.id,
            Product.name,
            Product.sku,
            ProductCategory.name.label('category_name'),
            func.sum(OrderItem.price * OrderItem.quantity).label('revenue'),
            func.sum(OrderItem.quantity).label('quantity_sold'),
            func.count(func.distinct(Order.id)).label('orders_count'),
            func.avg(OrderItem.price).label('average_price')
        ).select_from(
            Product.__table__
            .join(OrderItem.__table__)
            .join(Order.__table__)
            .outerjoin(ProductCategory.__table__)
        ).where(
            and_(
                Order.order_date >= start_date,
                Order.order_date <= end_date,
                Order.status.in_(['completed', 'shipped', 'delivered'])
            )
        ).group_by(
            Product.id, Product.name, Product.sku, ProductCategory.name
        )

        # Apply sorting
        if sort_by == "revenue":
            query = query.order_by(desc('revenue'))
        elif sort_by == "quantity":
            query = query.order_by(desc('quantity_sold'))
        elif sort_by == "orders":
            query = query.order_by(desc('orders_count'))

        query = query.limit(top_n)
        
        result = await self.db.execute(query)
        products = result.all()

        return [
            ProductPerformanceItem(
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                category_name=product.category_name,
                revenue=product.revenue or Decimal('0'),
                quantity_sold=product.quantity_sold or 0,
                orders_count=product.orders_count or 0,
                average_price=product.average_price or Decimal('0')
            )
            for product in products
        ]

    async def get_customer_analysis(
        self,
        start_date: date,
        end_date: date,
        segment_by: str = "value"
    ) -> List[CustomerSegmentItem]:
        """Analyze customer segments and behavior"""
        
        if segment_by == "value":
            # Segment customers by spending levels
            query = select(
                case(
                    (func.sum(Order.total_amount) >= 10000, 'High Value'),
                    (func.sum(Order.total_amount) >= 5000, 'Medium Value'),
                    (func.sum(Order.total_amount) >= 1000, 'Regular'),
                    else_='Low Value'
                ).label('segment'),
                func.count(func.distinct(Customer.id)).label('customer_count'),
                func.sum(Order.total_amount).label('total_revenue'),
                func.avg(Order.total_amount).label('avg_order_value'),
                func.count(Order.id).label('total_orders')
            ).select_from(
                Customer.__table__.join(Order.__table__)
            ).where(
                and_(
                    Order.order_date >= start_date,
                    Order.order_date <= end_date,
                    Order.status.in_(['completed', 'shipped', 'delivered'])
                )
            ).group_by('segment')

        result = await self.db.execute(query)
        segments = result.all()

        return [
            CustomerSegmentItem(
                segment=segment.segment,
                customer_count=segment.customer_count,
                total_revenue=segment.total_revenue or Decimal('0'),
                average_revenue_per_customer=segment.total_revenue / segment.customer_count if segment.customer_count > 0 else Decimal('0'),
                average_order_frequency=segment.total_orders / segment.customer_count if segment.customer_count > 0 else 0.0
            )
            for segment in segments
        ]

    async def get_trend_analysis(
        self,
        start_date: date,
        end_date: date,
        period: ReportPeriod = ReportPeriod.MONTHLY
    ) -> List[Dict[str, Any]]:
        """Generate trend analysis over time periods"""
        
        # Determine date truncation based on period
        if period == ReportPeriod.DAILY:
            date_trunc = func.date(Order.order_date)
        elif period == ReportPeriod.WEEKLY:
            date_trunc = func.date_trunc('week', Order.order_date)
        elif period == ReportPeriod.MONTHLY:
            date_trunc = func.date_trunc('month', Order.order_date)
        elif period == ReportPeriod.QUARTERLY:
            date_trunc = func.date_trunc('quarter', Order.order_date)
        else:  # YEARLY
            date_trunc = func.date_trunc('year', Order.order_date)

        query = select(
            date_trunc.label('period_start'),
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('orders_count'),
            func.avg(Order.total_amount).label('avg_order_value')
        ).where(
            and_(
                Order.order_date >= start_date,
                Order.order_date <= end_date,
                Order.status.in_(['completed', 'shipped', 'delivered'])
            )
        ).group_by('period_start').order_by('period_start')

        result = await self.db.execute(query)
        trends = result.all()

        # Calculate growth rates
        trend_data = []
        prev_revenue = None
        
        for trend in trends:
            growth_rate = None
            if prev_revenue and prev_revenue > 0:
                growth_rate = ((trend.revenue - prev_revenue) / prev_revenue * 100)
            
            trend_data.append({
                'period': trend.period_start.isoformat() if hasattr(trend.period_start, 'isoformat') else str(trend.period_start),
                'revenue': float(trend.revenue or 0),
                'orders_count': trend.orders_count or 0,
                'avg_order_value': float(trend.avg_order_value or 0),
                'growth_rate': round(growth_rate, 2) if growth_rate is not None else None
            })
            
            prev_revenue = trend.revenue

        return trend_data

# API Endpoints
@router.post("/generate", response_model=SalesReportResponse)
async def generate_sales_report(
    request: SalesReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate comprehensive sales report based on specified parameters"""
    
    analytics_service = SalesAnalyticsService(db)
    report_id = f"sales_report_{uuid4().hex[:8]}"
    
    try:
        # Generate base metrics
        metrics_data = await analytics_service.generate_revenue_summary(
            request.start_date, 
            request.end_date, 
            request.filters
        )
        
        metrics = SalesMetrics(
            total_revenue=metrics_data['total_revenue'],
            total_orders=metrics_data['total_orders'],
            total_quantity=metrics_data['total_quantity'],
            average_order_value=metrics_data['average_order_value'],
            conversion_rate=metrics_data['conversion_rate'],
            period_label=f"{request.start_date} to {request.end_date}"
        )
        
        # Generate specific report data based on type
        report_data = []
        comparison_data = None
        
        if request.report_type == ReportType.REVENUE_SUMMARY:
            report_data = await analytics_service.get_trend_analysis(
                request.start_date, request.end_date, request.period
            )
            
        elif request.report_type == ReportType.PRODUCT_PERFORMANCE:
            products = await analytics_service.get_product_performance(
                request.start_date, request.end_date
            )
            report_data = [product.dict() for product in products]
            
        elif request.report_type == ReportType.CUSTOMER_ANALYSIS:
            customers = await analytics_service.get_customer_analysis(
                request.start_date, request.end_date
            )
            report_data = [customer.dict() for customer in customers]
            
        elif request.report_type == ReportType.TREND_ANALYSIS:
            report_data = await analytics_service.get_trend_analysis(
                request.start_date, request.end_date, request.period
            )
        
        # Generate comparison data if requested
        if request.include_comparison and request.comparison_period:
            # Calculate comparison period dates
            period_diff = request.end_date - request.start_date
            comp_end_date = request.start_date - timedelta(days=1)
            comp_start_date = comp_end_date - period_diff
            
            if request.report_type == ReportType.REVENUE_SUMMARY:
                comparison_data = await analytics_service.get_trend_analysis(
                    comp_start_date, comp_end_date, request.period
                )
        
        return SalesReportResponse(
            report_id=report_id,
            report_type=request.report_type,
            period=request.period,
            date_range={
                "start_date": request.start_date,
                "end_date": request.end_date
            },
            metrics=metrics,
            data=report_data,
            comparison_data=comparison_data,
            generated_at=datetime.utcnow(),
            filters_applied=request.filters
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sales report: {str(e)}"
        )

@router.get("/product-performance", response_model=List[ProductPerformanceItem])
async def get_product_performance_report(
    start_date: date = Query(..., description="Start date for the report"),
    end_date: date = Query(..., description="End date for the report"),
    top_n: int = Query(10, ge=1, le=100, description="Number of top products to return"),
    sort_by: str = Query("revenue", description="Sort by: revenue, quantity, orders"),
    category_id: Optional[UUID] = Query(None, description="Filter by product category"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get top performing products with detailed metrics"""
    
    analytics_service = SalesAnalyticsService(db)
    
    try:
        products = await analytics_service.get_product_performance(
            start_date=start_date,
            end_date=end_date,
            top_n=top_n,
            sort_by=sort_by
        )
        
        return products
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate product performance report: {str(e)}"
        )

@router.get("/customer-analysis", response_model=List[CustomerSegmentItem])
async def get_customer_analysis_report(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    segment_by: str = Query("value", description="Segment by: value, geography, industry"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze customer segments and purchasing behavior"""
    
    analytics_service = SalesAnalyticsService(db)
    
    try:
        segments = await analytics_service.get_customer_analysis(
            start_date=start_date,
            end_date=end_date,
            segment_by=segment_by
        )
        
        return segments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate customer analysis: {str(e)}"
        )

@router.get("/trend-analysis")
async def get_sales_trend_analysis(
    start_date: date = Query(..., description="Start date for trend analysis"),
    end_date: date = Query(..., description="End date for trend analysis"),
    period: ReportPeriod = Query(ReportPeriod.MONTHLY, description="Aggregation period"),
    include_forecast: bool = Query(False, description="Include sales forecasting"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate detailed sales trend analysis with growth rates"""
    
    analytics_service = SalesAnalyticsService(db)
    
    try:
        trends = await analytics_service.get_trend_analysis(
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        
        # Add forecasting if requested
        forecast_data = None
        if include_forecast and len(trends) >= 3:
            # Simple linear forecasting based on trend
            recent_trends = trends[-3:]
            avg_growth = sum(t.get('growth_rate', 0) or 0 for t in recent_trends) / 3
            
            last_revenue = trends[-1]['revenue']
            forecast_periods = 3
            
            forecast_data = []
            for i in range(1, forecast_periods + 1):
                forecast_revenue = last_revenue * (1 + avg_growth/100) ** i
                forecast_data.append({
                    'period': f"Forecast +{i}",
                    'forecasted_revenue': round(forecast_revenue, 2),
                    'confidence': max(0.5, 0.9 - i * 0.1)  # Decreasing confidence
                })
        
        return {
            "trends": trends,
            "forecast": forecast_data,
            "summary": {
                "total_periods": len(trends),
                "average_growth_rate": round(sum(t.get('growth_rate', 0) or 0 for t in trends if t.get('growth_rate')) / len([t for t in trends if t.get('growth_rate')]), 2) if trends else 0,
                "best_period": max(trends, key=lambda x: x['revenue'])['period'] if trends else None,
                "total_revenue": sum(t['revenue'] for t in trends)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trend analysis: {str(e)}"
        )

@router.get("/export/{report_id}")
async def export_report(
    report_id: str = Path(..., description="Report ID to export"),
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export sales report in specified format"""
    
    # For demonstration, generate sample data
    # In production, would retrieve stored report data
    sample_data = [
        {
            "period": "2024-01",
            "revenue": 125000.50,
            "orders": 145,
            "avg_order_value": 862.07,
            "growth_rate": 12.5
        },
        {
            "period": "2024-02", 
            "revenue": 138750.25,
            "orders": 162,
            "avg_order_value": 857.72,
            "growth_rate": 11.0
        }
    ]
    
    if format == ExportFormat.CSV:
        # Generate CSV
        output = StringIO()
        if sample_data:
            writer = csv.DictWriter(output, fieldnames=sample_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_data)
        
        csv_content = output.getvalue()
        output.close()
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sales_report_{report_id}.csv"}
        )
    
    elif format == ExportFormat.JSON:
        json_content = json.dumps(sample_data, indent=2, default=str)
        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=sales_report_{report_id}.json"}
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export format {format} not yet supported"
        )

@router.get("/dashboard-summary")
async def get_sales_dashboard_summary(
    period: ReportPeriod = Query(ReportPeriod.MONTHLY, description="Summary period"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sales dashboard summary with key metrics and trends"""
    
    analytics_service = SalesAnalyticsService(db)
    end_date = date.today()
    
    # Calculate start date based on period
    if period == ReportPeriod.DAILY:
        start_date = end_date - timedelta(days=30)
    elif period == ReportPeriod.WEEKLY:
        start_date = end_date - timedelta(weeks=12)
    elif period == ReportPeriod.MONTHLY:
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=90)
    
    try:
        # Get current period metrics
        current_metrics = await analytics_service.generate_revenue_summary(
            start_date, end_date
        )
        
        # Get previous period for comparison
        period_length = end_date - start_date
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - period_length
        
        previous_metrics = await analytics_service.generate_revenue_summary(
            prev_start_date, prev_end_date
        )
        
        # Calculate changes
        revenue_change = 0
        orders_change = 0
        
        if previous_metrics['total_revenue'] > 0:
            revenue_change = ((current_metrics['total_revenue'] - previous_metrics['total_revenue']) / previous_metrics['total_revenue'] * 100)
        
        if previous_metrics['total_orders'] > 0:
            orders_change = ((current_metrics['total_orders'] - previous_metrics['total_orders']) / previous_metrics['total_orders'] * 100)
        
        # Get top products
        top_products = await analytics_service.get_product_performance(
            start_date, end_date, top_n=5
        )
        
        return {
            "current_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "metrics": current_metrics
            },
            "period_comparison": {
                "revenue_change_percent": round(revenue_change, 2),
                "orders_change_percent": round(orders_change, 2)
            },
            "top_products": [
                {
                    "name": product.product_name,
                    "revenue": float(product.revenue),
                    "units_sold": product.quantity_sold
                }
                for product in top_products[:5]
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard summary: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for sales reports API"""
    return {
        "status": "healthy",
        "service": "sales-reports-v56",
        "version": "1.0.0",
        "features": [
            "revenue_summary",
            "product_performance", 
            "customer_analysis",
            "trend_analysis",
            "csv_export",
            "dashboard_summary"
        ],
        "checked_at": datetime.utcnow().isoformat()
    }