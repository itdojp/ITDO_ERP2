"""
CC02 v53.0 Reporting and Analytics Schemas - Issue #568
10-Day ERP Business API Implementation Sprint - Day 9-10 Phase 1
Comprehensive Business Intelligence and Reporting API Schemas
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ReportType(str, Enum):
    """Report type enumeration"""
    SALES = "sales"
    INVENTORY = "inventory"
    PRODUCT = "product"
    CUSTOMER = "customer"
    FINANCIAL = "financial"
    CRM = "crm"
    OPERATIONAL = "operational"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report output format enumeration"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    CHART = "chart"
    DASHBOARD = "dashboard"


class ReportStatus(str, Enum):
    """Report generation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportFrequency(str, Enum):
    """Report scheduling frequency"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ChartType(str, Enum):
    """Chart visualization types"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    TABLE = "table"


class TimeRange(str, Enum):
    """Time range options for reports"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    LAST_QUARTER = "last_quarter"
    THIS_YEAR = "this_year"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class MetricAggregation(str, Enum):
    """Metric aggregation methods"""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    VARIANCE = "variance"
    STANDARD_DEVIATION = "std_dev"
    PERCENTAGE = "percentage"
    RATIO = "ratio"


# Report Configuration Schemas

class ReportFilter(BaseModel):
    """Schema for report filters"""
    field: str = Field(..., min_length=1, max_length=100)
    operator: str = Field(..., pattern="^(eq|ne|gt|gte|lt|lte|in|not_in|like|between)$")
    value: Union[str, int, float, List[str], Dict[str, Any]]
    label: Optional[str] = Field(None, max_length=100)


class ReportSort(BaseModel):
    """Schema for report sorting"""
    field: str = Field(..., min_length=1, max_length=100)
    direction: str = Field(default="asc", pattern="^(asc|desc)$")
    priority: int = Field(default=1, ge=1, le=10)


class ReportGrouping(BaseModel):
    """Schema for report data grouping"""
    field: str = Field(..., min_length=1, max_length=100)
    level: int = Field(default=1, ge=1, le=5)
    aggregation: MetricAggregation = Field(default=MetricAggregation.COUNT)
    label: Optional[str] = Field(None, max_length=100)


class ChartConfiguration(BaseModel):
    """Schema for chart configuration"""
    chart_type: ChartType
    title: str = Field(..., min_length=1, max_length=200)
    x_axis: str = Field(..., min_length=1, max_length=100)
    y_axis: str = Field(..., min_length=1, max_length=100)
    color_scheme: Optional[str] = Field(None, max_length=50)
    show_legend: bool = Field(default=True)
    show_labels: bool = Field(default=True)
    width: Optional[int] = Field(None, ge=100, le=2000)
    height: Optional[int] = Field(None, ge=100, le=1500)
    custom_options: Dict[str, Any] = Field(default_factory=dict)


class ReportCreate(BaseModel):
    """Schema for creating report"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    report_type: ReportType
    format: ReportFormat = Field(default=ReportFormat.JSON)
    
    # Time range
    time_range: TimeRange = Field(default=TimeRange.THIS_MONTH)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Data configuration
    data_source: str = Field(..., min_length=1, max_length=100)
    filters: List[ReportFilter] = Field(default_factory=list)
    sorting: List[ReportSort] = Field(default_factory=list)
    grouping: List[ReportGrouping] = Field(default_factory=list)
    
    # Output configuration
    columns: Optional[List[str]] = Field(None, max_length=50)
    max_rows: Optional[int] = Field(None, ge=1, le=100000)
    include_summary: bool = Field(default=True)
    include_charts: bool = Field(default=False)
    chart_config: Optional[ChartConfiguration] = None
    
    # Metadata
    tags: List[str] = Field(default_factory=list, max_length=10)
    category: Optional[str] = Field(None, max_length=100)
    owner: Optional[str] = None
    is_public: bool = Field(default=False)
    
    # Scheduling
    is_scheduled: bool = Field(default=False)
    frequency: Optional[ReportFrequency] = None
    schedule_time: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    recipients: List[str] = Field(default_factory=list, max_length=20)
    
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        if v and 'start_date' in info.data and info.data['start_date']:
            start_date = info.data['start_date']
            if v < start_date:
                raise ValueError('end_date cannot be before start_date')
        return v


class ReportUpdate(BaseModel):
    """Schema for updating report"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    format: Optional[ReportFormat] = None
    time_range: Optional[TimeRange] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    filters: Optional[List[ReportFilter]] = None
    sorting: Optional[List[ReportSort]] = None
    grouping: Optional[List[ReportGrouping]] = None
    columns: Optional[List[str]] = None
    max_rows: Optional[int] = Field(None, ge=1, le=100000)
    include_summary: Optional[bool] = None
    include_charts: Optional[bool] = None
    chart_config: Optional[ChartConfiguration] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=100)
    is_public: Optional[bool] = None
    is_scheduled: Optional[bool] = None
    frequency: Optional[ReportFrequency] = None
    schedule_time: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    recipients: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """Schema for report API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: Optional[str] = None
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus = ReportStatus.PENDING
    
    # Time configuration
    time_range: TimeRange
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Data configuration
    data_source: str
    filters: List[ReportFilter] = Field(default_factory=list)
    sorting: List[ReportSort] = Field(default_factory=list)
    grouping: List[ReportGrouping] = Field(default_factory=list)
    
    # Output configuration
    columns: Optional[List[str]] = None
    max_rows: Optional[int] = None
    include_summary: bool = True
    include_charts: bool = False
    chart_config: Optional[ChartConfiguration] = None
    
    # Results
    row_count: int = 0
    file_size_bytes: Optional[int] = None
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    
    # Processing metrics
    generation_time_ms: Optional[float] = None
    last_generated: Optional[datetime] = None
    cache_expires: Optional[datetime] = None
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    owner: Optional[str] = None
    owner_name: Optional[str] = None
    is_public: bool = False
    view_count: int = 0
    download_count: int = 0
    
    # Scheduling
    is_scheduled: bool = False
    frequency: Optional[ReportFrequency] = None
    schedule_time: Optional[str] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    recipients: List[str] = Field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = Field(default_factory=list)
    
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Analytics and Dashboard Schemas

class DashboardWidget(BaseModel):
    """Schema for dashboard widgets"""
    id: str
    type: str = Field(..., pattern="^(chart|metric|table|kpi|text)$")
    title: str = Field(..., min_length=1, max_length=200)
    position: Dict[str, int] = Field(..., description="x, y, width, height")
    
    # Data configuration
    data_source: str
    query: Optional[str] = None
    filters: List[ReportFilter] = Field(default_factory=list)
    refresh_interval: int = Field(default=300, ge=30, le=3600)  # seconds
    
    # Visualization
    chart_config: Optional[ChartConfiguration] = None
    format_options: Dict[str, Any] = Field(default_factory=dict)
    
    # Interactivity
    clickable: bool = Field(default=False)
    drill_down_enabled: bool = Field(default=False)
    export_enabled: bool = Field(default=True)
    
    custom_config: Dict[str, Any] = Field(default_factory=dict)


class DashboardCreate(BaseModel):
    """Schema for creating dashboard"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    
    # Layout
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    theme: str = Field(default="default", max_length=50)
    
    # Widgets
    widgets: List[DashboardWidget] = Field(default_factory=list, max_length=20)
    
    # Access control
    is_public: bool = Field(default=False)
    shared_with: List[str] = Field(default_factory=list, max_length=50)
    
    # Auto-refresh
    auto_refresh: bool = Field(default=True)
    refresh_interval: int = Field(default=300, ge=60, le=3600)
    
    tags: List[str] = Field(default_factory=list, max_length=10)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    """Schema for dashboard API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    
    # Layout
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    theme: str = "default"
    
    # Widgets
    widgets: List[DashboardWidget] = Field(default_factory=list)
    widget_count: int = 0
    
    # Access control
    is_public: bool = False
    shared_with: List[str] = Field(default_factory=list)
    owner: Optional[str] = None
    owner_name: Optional[str] = None
    
    # Auto-refresh
    auto_refresh: bool = True
    refresh_interval: int = 300
    last_refreshed: Optional[datetime] = None
    
    # Usage metrics
    view_count: int = 0
    last_viewed: Optional[datetime] = None
    favorite_count: int = 0
    
    # Status
    is_active: bool = True
    health_status: str = "healthy"
    error_count: int = 0
    
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Analytics Data Schemas

class AnalyticsMetric(BaseModel):
    """Schema for analytics metrics"""
    name: str = Field(..., min_length=1, max_length=100)
    value: Union[int, float, Decimal]
    format_type: str = Field(default="number", pattern="^(number|currency|percentage|duration)$")
    trend: Optional[str] = Field(None, pattern="^(up|down|stable)$")
    trend_percentage: Optional[Decimal] = Field(None, decimal_places=2)
    benchmark: Optional[Union[int, float, Decimal]] = None
    target: Optional[Union[int, float, Decimal]] = None
    unit: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=500)


class AnalyticsDataPoint(BaseModel):
    """Schema for analytics data points"""
    timestamp: datetime
    value: Union[int, float, Decimal]
    label: Optional[str] = None
    category: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsQuery(BaseModel):
    """Schema for analytics queries"""
    metric_name: str = Field(..., min_length=1, max_length=100)
    aggregation: MetricAggregation = MetricAggregation.SUM
    time_range: TimeRange = TimeRange.THIS_MONTH
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    group_by: Optional[str] = Field(None, max_length=100)
    filters: List[ReportFilter] = Field(default_factory=list)
    limit: Optional[int] = Field(None, ge=1, le=10000)


class AnalyticsResult(BaseModel):
    """Schema for analytics query results"""
    query: AnalyticsQuery
    metrics: List[AnalyticsMetric] = Field(default_factory=list)
    data_points: List[AnalyticsDataPoint] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    total_records: int = 0
    query_time_ms: float
    cache_hit: bool = False
    generated_at: datetime = Field(default_factory=datetime.now)


# Business Intelligence Schemas

class KPIDefinition(BaseModel):
    """Schema for KPI definitions"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(..., min_length=1, max_length=100)
    
    # Calculation
    formula: str = Field(..., min_length=1, max_length=1000)
    data_sources: List[str] = Field(..., min_length=1, max_length=10)
    calculation_method: MetricAggregation = MetricAggregation.SUM
    
    # Targets and thresholds
    target_value: Optional[Decimal] = Field(None, decimal_places=2)
    warning_threshold: Optional[Decimal] = Field(None, decimal_places=2)
    critical_threshold: Optional[Decimal] = Field(None, decimal_places=2)
    
    # Display
    format_type: str = Field(default="number", pattern="^(number|currency|percentage|duration)$")
    unit: Optional[str] = Field(None, max_length=20)
    decimal_places: int = Field(default=2, ge=0, le=6)
    
    # Update frequency
    update_frequency: str = Field(default="daily", pattern="^(hourly|daily|weekly|monthly)$")
    last_calculated: Optional[datetime] = None
    
    # Access control
    is_active: bool = Field(default=True)
    owner: Optional[str] = None
    viewers: List[str] = Field(default_factory=list)
    
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class KPIValue(BaseModel):
    """Schema for KPI values"""
    kpi_id: str
    kpi_name: str
    value: Decimal = Field(..., decimal_places=6)
    formatted_value: str
    
    # Performance indicators
    target_value: Optional[Decimal] = Field(None, decimal_places=2)
    variance: Optional[Decimal] = Field(None, decimal_places=2)
    variance_percentage: Optional[Decimal] = Field(None, decimal_places=2)
    status: str = Field(default="normal", pattern="^(excellent|good|normal|warning|critical)$")
    
    # Trends
    previous_value: Optional[Decimal] = Field(None, decimal_places=6)
    trend: Optional[str] = Field(None, pattern="^(up|down|stable)$")
    trend_percentage: Optional[Decimal] = Field(None, decimal_places=2)
    
    # Context
    period_start: date
    period_end: date
    calculation_time: datetime = Field(default_factory=datetime.now)
    data_quality: str = Field(default="high", pattern="^(high|medium|low)$")
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Business Intelligence Dashboard

class BIDashboard(BaseModel):
    """Schema for Business Intelligence Dashboard"""
    overview_metrics: List[AnalyticsMetric] = Field(default_factory=list)
    kpi_summary: List[KPIValue] = Field(default_factory=list)
    
    # Sales Analytics
    sales_performance: Dict[str, Any] = Field(default_factory=dict)
    revenue_trends: List[AnalyticsDataPoint] = Field(default_factory=list)
    top_products: List[Dict[str, Any]] = Field(default_factory=list)
    customer_insights: Dict[str, Any] = Field(default_factory=dict)
    
    # Inventory Analytics
    inventory_health: Dict[str, Any] = Field(default_factory=dict)
    stock_levels: List[Dict[str, Any]] = Field(default_factory=list)
    turnover_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # CRM Analytics
    lead_pipeline: Dict[str, Any] = Field(default_factory=dict)
    conversion_funnel: List[Dict[str, Any]] = Field(default_factory=list)
    customer_lifecycle: Dict[str, Any] = Field(default_factory=dict)
    
    # Financial Analytics
    financial_summary: Dict[str, Any] = Field(default_factory=dict)
    profit_margins: List[AnalyticsDataPoint] = Field(default_factory=list)
    cost_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Operational Analytics
    operational_efficiency: Dict[str, Any] = Field(default_factory=dict)
    process_metrics: List[AnalyticsMetric] = Field(default_factory=list)
    quality_indicators: Dict[str, Any] = Field(default_factory=dict)
    
    # Alerts and recommendations
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    dashboard_health: str = "healthy"
    last_updated: datetime = Field(default_factory=datetime.now)
    data_freshness: Dict[str, datetime] = Field(default_factory=dict)
    generation_time_ms: float


# List Response Schemas

class ReportListResponse(BaseModel):
    """Schema for paginated report list responses"""
    items: List[ReportResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class DashboardListResponse(BaseModel):
    """Schema for paginated dashboard list responses"""
    items: List[DashboardResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class KPIListResponse(BaseModel):
    """Schema for paginated KPI list responses"""
    items: List[KPIDefinition]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# Report Execution Schemas

class ReportExecution(BaseModel):
    """Schema for report execution tracking"""
    id: str
    report_id: str
    report_name: str
    status: ReportStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    # Results
    row_count: int = 0
    file_size_bytes: Optional[int] = None
    output_format: ReportFormat
    file_path: Optional[str] = None
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Context
    requested_by: Optional[str] = None
    execution_mode: str = Field(default="manual", pattern="^(manual|scheduled|api)$")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Resource usage
    memory_usage_mb: Optional[float] = None
    cpu_time_ms: Optional[float] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BulkReportOperation(BaseModel):
    """Schema for bulk report operations"""
    operation_type: str = Field(..., pattern="^(generate|delete|update|export)$")
    report_ids: List[str] = Field(..., min_length=1, max_length=100)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    notify_on_completion: bool = Field(default=False)
    recipients: List[str] = Field(default_factory=list)


class BulkReportResult(BaseModel):
    """Schema for bulk report operation results"""
    operation_id: str
    operation_type: str
    total_reports: int
    successful_count: int = 0
    failed_count: int = 0
    
    # Results
    successful_reports: List[str] = Field(default_factory=list)
    failed_reports: List[Dict[str, str]] = Field(default_factory=list)  # id, error
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    
    status: str = Field(default="in_progress", pattern="^(in_progress|completed|failed|cancelled)$")


# Export and Integration Schemas

class ReportExport(BaseModel):
    """Schema for report export configuration"""
    report_id: str
    format: ReportFormat
    include_charts: bool = Field(default=True)
    include_metadata: bool = Field(default=False)
    compression: bool = Field(default=False)
    
    # Delivery options
    delivery_method: str = Field(default="download", pattern="^(download|email|ftp|s3|webhook)$")
    delivery_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Security
    password_protect: bool = Field(default=False)
    expiry_hours: Optional[int] = Field(None, ge=1, le=168)  # Max 1 week
    
    custom_options: Dict[str, Any] = Field(default_factory=dict)


# Error and Health Schemas

class ReportingError(BaseModel):
    """Reporting-specific error response"""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    report_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ReportingHealth(BaseModel):
    """Schema for reporting system health"""
    status: str = "healthy"
    service: str = "Reporting and Analytics API v53.0"
    
    # Component health
    report_engine: str = "operational"
    data_sources: Dict[str, str] = Field(default_factory=dict)
    chart_renderer: str = "operational"
    export_service: str = "operational"
    
    # Statistics
    total_reports: int = 0
    active_dashboards: int = 0
    scheduled_reports: int = 0
    pending_executions: int = 0
    
    # Performance metrics
    average_generation_time_ms: Optional[float] = None
    cache_hit_rate: Optional[float] = None
    error_rate: Optional[float] = None
    
    # Resource usage
    memory_usage_mb: Optional[float] = None
    disk_usage_gb: Optional[float] = None
    
    timestamp: datetime = Field(default_factory=datetime.now)
    uptime_seconds: Optional[int] = None


# API Response Wrappers

class ReportingAPIResponse(BaseModel):
    """Reporting-specific API response wrapper"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Union[
        ReportResponse,
        DashboardResponse,
        AnalyticsResult,
        BIDashboard,
        ReportListResponse,
        DashboardListResponse,
        KPIListResponse,
        ReportExecution,
        BulkReportResult,
        ReportingHealth
    ]] = None
    errors: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None