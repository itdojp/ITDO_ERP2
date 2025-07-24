"""
Analytics System Schemas - CC02 v31.0 Phase 2

Comprehensive Pydantic schemas for analytics system including:
- Multi-Dimensional Analytics & KPI Tracking
- Real-Time Data Processing & Aggregation
- Advanced Business Intelligence & Reporting
- Performance Metrics & Benchmarking
- Predictive Analytics & Forecasting
- Custom Dashboard & Visualization
- Data Mining & Machine Learning Integration
- Executive Analytics & Strategic Insights
- Operational Analytics & Process Optimization
- Compliance Analytics & Risk Management
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.analytics_extended import (
    AggregationType,
    AlertPriority,
    AnalyticsType,
    DashboardType,
    MetricType,
    PeriodType,
    ReportStatus,
)

# =============================================================================
# Base Schemas
# =============================================================================


class BaseAnalyticsSchema(BaseModel):
    """Base schema for analytics-related models."""

    class Config:
        from_attributes = True
        use_enum_values = True


# =============================================================================
# Data Source Schemas
# =============================================================================


class DataSourceCreateRequest(BaseAnalyticsSchema):
    """Schema for creating analytics data source."""

    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., min_length=1, max_length=200, description="Data source name")
    code: str = Field(..., min_length=1, max_length=100, description="Unique code")
    description: Optional[str] = Field(None, description="Description")
    source_type: str = Field(
        ..., description="Source type (database, api, file, stream)"
    )

    # Connection configuration
    connection_string: Optional[str] = Field(
        None, max_length=1000, description="Connection string"
    )
    connection_config: Dict[str, Any] = Field(
        default_factory=dict, description="Connection config"
    )
    authentication_config: Dict[str, Any] = Field(
        default_factory=dict, description="Auth config"
    )

    # Schema and mappings
    schema_definition: Dict[str, Any] = Field(
        default_factory=dict, description="Schema definition"
    )
    table_mappings: Dict[str, Any] = Field(
        default_factory=dict, description="Table mappings"
    )
    field_mappings: Dict[str, Any] = Field(
        default_factory=dict, description="Field mappings"
    )
    transformation_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Transformation rules"
    )

    # Sync settings
    sync_frequency: str = Field("daily", description="Sync frequency")
    sync_schedule: Optional[str] = Field(None, description="Cron schedule")
    is_realtime: bool = Field(False, description="Real-time source")

    # Validation and quality
    validation_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Validation rules"
    )
    cleansing_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Cleansing rules"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields"
    )
    created_by: str = Field(..., description="Creator user ID")

    @validator("source_type")
    def validate_source_type(cls, v) -> dict:
        """Validate source type."""
        allowed_types = ["database", "api", "file", "stream", "webhook"]
        if v not in allowed_types:
            raise ValueError(f"Source type must be one of: {', '.join(allowed_types)}")
        return v

    @validator("sync_frequency")
    def validate_sync_frequency(cls, v) -> dict:
        """Validate sync frequency."""
        allowed_frequencies = ["realtime", "hourly", "daily", "weekly", "monthly"]
        if v not in allowed_frequencies:
            raise ValueError(
                f"Sync frequency must be one of: {', '.join(allowed_frequencies)}"
            )
        return v


class DataSourceResponse(BaseAnalyticsSchema):
    """Schema for data source response."""

    id: str = Field(..., description="Data source ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Data source name")
    code: str = Field(..., description="Unique code")
    description: Optional[str] = Field(None, description="Description")
    source_type: str = Field(..., description="Source type")

    # Status and health
    is_active: bool = Field(..., description="Active status")
    is_realtime: bool = Field(..., description="Real-time source")
    health_status: str = Field(..., description="Health status")
    error_count: int = Field(..., description="Error count")
    last_error: Optional[str] = Field(None, description="Last error message")

    # Sync information
    sync_frequency: str = Field(..., description="Sync frequency")
    last_sync_at: Optional[datetime] = Field(None, description="Last sync time")
    next_sync_at: Optional[datetime] = Field(None, description="Next sync time")

    # Performance metrics
    records_processed: int = Field(..., description="Records processed")
    processing_time_avg: Optional[Decimal] = Field(
        None, description="Average processing time"
    )
    throughput_per_minute: Optional[Decimal] = Field(
        None, description="Throughput per minute"
    )
    quality_score: Optional[Decimal] = Field(None, description="Data quality score")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class DataSourceConnectionTest(BaseAnalyticsSchema):
    """Schema for data source connection test result."""

    status: str = Field(..., description="Test status")
    connection_time_ms: int = Field(0, description="Connection time in milliseconds")
    message: str = Field("", description="Test message")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional details"
    )


class DataSourceSyncResult(BaseAnalyticsSchema):
    """Schema for data source sync result."""

    status: str = Field(..., description="Sync status")
    records_processed: int = Field(0, description="Records processed")
    processing_time_seconds: float = Field(0, description="Processing time in seconds")
    metrics_updated: int = Field(0, description="Metrics updated")
    errors: List[str] = Field(default_factory=list, description="Sync errors")


# =============================================================================
# Metric Schemas
# =============================================================================


class MetricCreateRequest(BaseAnalyticsSchema):
    """Schema for creating analytics metric."""

    organization_id: str = Field(..., description="Organization ID")
    data_source_id: Optional[str] = Field(None, description="Data source ID")
    name: str = Field(..., min_length=1, max_length=200, description="Metric name")
    code: str = Field(..., min_length=1, max_length=100, description="Unique code")
    display_name: Optional[str] = Field(
        None, max_length=200, description="Display name"
    )
    description: Optional[str] = Field(None, description="Description")
    category: Optional[str] = Field(None, max_length=100, description="Category")

    # Metric configuration
    metric_type: MetricType = Field(..., description="Metric type")
    analytics_type: AnalyticsType = Field(..., description="Analytics type")
    aggregation_type: AggregationType = Field(..., description="Aggregation type")

    # Calculation definition
    calculation_formula: str = Field(..., description="Calculation formula")
    calculation_fields: List[str] = Field(
        default_factory=list, description="Calculation fields"
    )
    calculation_filters: Dict[str, Any] = Field(
        default_factory=dict, description="Calculation filters"
    )
    calculation_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Calculation parameters"
    )

    # Units and formatting
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measure")
    format_pattern: Optional[str] = Field(
        None, max_length=100, description="Format pattern"
    )
    decimal_places: int = Field(2, ge=0, le=10, description="Decimal places")
    multiplier: Decimal = Field(Decimal("1"), description="Value multiplier")

    # Targets and thresholds
    target_value: Optional[Decimal] = Field(None, description="Target value")
    min_threshold: Optional[Decimal] = Field(None, description="Minimum threshold")
    max_threshold: Optional[Decimal] = Field(None, description="Maximum threshold")
    warning_threshold: Optional[Decimal] = Field(None, description="Warning threshold")
    critical_threshold: Optional[Decimal] = Field(
        None, description="Critical threshold"
    )

    # Benchmarking
    benchmark_value: Optional[Decimal] = Field(None, description="Benchmark value")
    benchmark_source: Optional[str] = Field(
        None, max_length=200, description="Benchmark source"
    )
    industry_average: Optional[Decimal] = Field(None, description="Industry average")

    # Calculation schedule
    calculation_frequency: str = Field("daily", description="Calculation frequency")
    calculation_schedule: Optional[str] = Field(
        None, description="Calculation schedule (cron)"
    )

    # Display configuration
    chart_type: str = Field("line", description="Chart type")
    color_scheme: Optional[str] = Field(
        None, max_length=100, description="Color scheme"
    )
    display_order: int = Field(0, description="Display order")
    is_featured: bool = Field(False, description="Featured metric")

    # Access control
    access_level: str = Field("organization", description="Access level")
    allowed_roles: List[str] = Field(default_factory=list, description="Allowed roles")
    allowed_users: List[str] = Field(default_factory=list, description="Allowed users")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")

    @validator("calculation_frequency")
    def validate_calculation_frequency(cls, v) -> dict:
        """Validate calculation frequency."""
        allowed_frequencies = ["realtime", "hourly", "daily", "weekly", "monthly"]
        if v not in allowed_frequencies:
            raise ValueError(
                f"Calculation frequency must be one of: {', '.join(allowed_frequencies)}"
            )
        return v

    @validator("chart_type")
    def validate_chart_type(cls, v) -> dict:
        """Validate chart type."""
        allowed_types = [
            "line",
            "bar",
            "area",
            "pie",
            "donut",
            "gauge",
            "number",
            "table",
        ]
        if v not in allowed_types:
            raise ValueError(f"Chart type must be one of: {', '.join(allowed_types)}")
        return v


class MetricResponse(BaseAnalyticsSchema):
    """Schema for metric response."""

    id: str = Field(..., description="Metric ID")
    organization_id: str = Field(..., description="Organization ID")
    data_source_id: Optional[str] = Field(None, description="Data source ID")
    name: str = Field(..., description="Metric name")
    code: str = Field(..., description="Unique code")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Description")
    category: Optional[str] = Field(None, description="Category")

    # Metric configuration
    metric_type: MetricType = Field(..., description="Metric type")
    analytics_type: AnalyticsType = Field(..., description="Analytics type")
    aggregation_type: AggregationType = Field(..., description="Aggregation type")

    # Current values
    current_value: Optional[Decimal] = Field(None, description="Current value")
    previous_value: Optional[Decimal] = Field(None, description="Previous value")
    trend_direction: Optional[str] = Field(None, description="Trend direction")
    trend_percentage: Optional[Decimal] = Field(None, description="Trend percentage")

    # Targets and thresholds
    target_value: Optional[Decimal] = Field(None, description="Target value")
    benchmark_value: Optional[Decimal] = Field(None, description="Benchmark value")

    # Status and quality
    is_active: bool = Field(..., description="Active status")
    is_featured: bool = Field(..., description="Featured metric")
    quality_score: Optional[Decimal] = Field(None, description="Quality score")
    confidence_level: Optional[Decimal] = Field(None, description="Confidence level")

    # Display
    unit: Optional[str] = Field(None, description="Unit of measure")
    format_pattern: Optional[str] = Field(None, description="Format pattern")
    chart_type: str = Field(..., description="Chart type")

    # Calculation info
    calculation_frequency: str = Field(..., description="Calculation frequency")
    last_calculated_at: Optional[datetime] = Field(
        None, description="Last calculation time"
    )
    next_calculation_at: Optional[datetime] = Field(
        None, description="Next calculation time"
    )

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class MetricCalculationRequest(BaseAnalyticsSchema):
    """Schema for metric calculation request."""

    period_start: Optional[datetime] = Field(None, description="Period start time")
    period_end: Optional[datetime] = Field(None, description="Period end time")
    force_recalculation: bool = Field(False, description="Force recalculation")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Calculation parameters"
    )


class MetricCalculationResult(BaseAnalyticsSchema):
    """Schema for metric calculation result."""

    status: str = Field(..., description="Calculation status")
    metric_id: str = Field(..., description="Metric ID")
    value: float = Field(..., description="Calculated value")
    period_start: str = Field(..., description="Period start (ISO format)")
    period_end: str = Field(..., description="Period end (ISO format)")
    quality_score: float = Field(..., description="Quality score")
    calculation_metadata: Dict[str, Any] = Field(
        ..., description="Calculation metadata"
    )


class MetricTrendData(BaseAnalyticsSchema):
    """Schema for metric trend data point."""

    timestamp: str = Field(..., description="Data point timestamp")
    period_start: Optional[str] = Field(None, description="Period start")
    period_end: Optional[str] = Field(None, description="Period end")
    value: float = Field(..., description="Value")
    raw_value: Optional[float] = Field(None, description="Raw value")
    quality_score: Optional[float] = Field(None, description="Quality score")
    is_anomaly: bool = Field(..., description="Anomaly flag")


class MetricTrendsResponse(BaseAnalyticsSchema):
    """Schema for metric trends response."""

    metric_id: str = Field(..., description="Metric ID")
    period_type: PeriodType = Field(..., description="Period type")
    data_points: List[MetricTrendData] = Field(..., description="Trend data points")
    summary: Dict[str, Any] = Field(..., description="Trend summary statistics")


# =============================================================================
# Dashboard Schemas
# =============================================================================


class DashboardCreateRequest(BaseAnalyticsSchema):
    """Schema for creating analytics dashboard."""

    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., min_length=1, max_length=200, description="Dashboard name")
    slug: Optional[str] = Field(None, max_length=100, description="URL slug")
    description: Optional[str] = Field(None, description="Description")
    dashboard_type: DashboardType = Field(..., description="Dashboard type")

    # Layout configuration
    layout_config: Dict[str, Any] = Field(
        default_factory=dict, description="Layout configuration"
    )
    grid_config: Dict[str, Any] = Field(
        default_factory=dict, description="Grid configuration"
    )
    responsive_config: Dict[str, Any] = Field(
        default_factory=dict, description="Responsive configuration"
    )

    # Widgets
    widgets: List[Dict[str, Any]] = Field(
        default_factory=list, description="Widget definitions"
    )
    widget_positions: Dict[str, Any] = Field(
        default_factory=dict, description="Widget positions"
    )
    widget_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Widget settings"
    )

    # Filters and refresh
    global_filters: Dict[str, Any] = Field(
        default_factory=dict, description="Global filters"
    )
    default_period: str = Field("last_30_days", description="Default time period")
    auto_refresh: bool = Field(True, description="Auto refresh enabled")
    refresh_interval: int = Field(
        300, ge=30, le=3600, description="Refresh interval in seconds"
    )

    # Sharing and permissions
    is_public: bool = Field(False, description="Public dashboard")
    is_shared: bool = Field(False, description="Shared dashboard")
    access_level: str = Field("private", description="Access level")
    allowed_roles: List[str] = Field(default_factory=list, description="Allowed roles")
    allowed_users: List[str] = Field(default_factory=list, description="Allowed users")

    # Customization
    theme: str = Field("default", description="Dashboard theme")
    color_scheme: Optional[str] = Field(None, description="Color scheme")
    custom_css: Optional[str] = Field(None, description="Custom CSS")

    # Export and email
    export_formats: List[str] = Field(
        default_factory=lambda: ["pdf", "png", "excel"], description="Export formats"
    )
    email_recipients: List[str] = Field(
        default_factory=list, description="Email recipients"
    )
    email_schedule: Optional[str] = Field(None, description="Email schedule (cron)")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")

    @validator("access_level")
    def validate_access_level(cls, v) -> dict:
        """Validate access level."""
        allowed_levels = ["private", "team", "department", "organization", "public"]
        if v not in allowed_levels:
            raise ValueError(
                f"Access level must be one of: {', '.join(allowed_levels)}"
            )
        return v

    @validator("theme")
    def validate_theme(cls, v) -> dict:
        """Validate theme."""
        allowed_themes = ["default", "dark", "light", "corporate", "modern", "minimal"]
        if v not in allowed_themes:
            raise ValueError(f"Theme must be one of: {', '.join(allowed_themes)}")
        return v


class DashboardResponse(BaseAnalyticsSchema):
    """Schema for dashboard response."""

    id: str = Field(..., description="Dashboard ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Dashboard name")
    slug: str = Field(..., description="URL slug")
    description: Optional[str] = Field(None, description="Description")
    dashboard_type: DashboardType = Field(..., description="Dashboard type")

    # Configuration
    layout_config: Dict[str, Any] = Field(..., description="Layout configuration")
    widgets: List[Dict[str, Any]] = Field(..., description="Widget definitions")
    widget_positions: Dict[str, Any] = Field(..., description="Widget positions")
    global_filters: Dict[str, Any] = Field(..., description="Global filters")

    # Status and metrics
    is_active: bool = Field(..., description="Active status")
    is_public: bool = Field(..., description="Public dashboard")
    is_shared: bool = Field(..., description="Shared dashboard")
    is_featured: bool = Field(..., description="Featured dashboard")
    view_count: int = Field(..., description="View count")
    last_viewed_at: Optional[datetime] = Field(None, description="Last viewed time")

    # Sharing
    share_token: Optional[str] = Field(None, description="Share token")
    access_level: str = Field(..., description="Access level")

    # Customization
    theme: str = Field(..., description="Dashboard theme")
    auto_refresh: bool = Field(..., description="Auto refresh enabled")
    refresh_interval: int = Field(..., description="Refresh interval")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class DashboardDataRequest(BaseAnalyticsSchema):
    """Schema for dashboard data request."""

    period_start: Optional[datetime] = Field(None, description="Period start time")
    period_end: Optional[datetime] = Field(None, description="Period end time")
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Additional filters"
    )
    refresh_cache: bool = Field(False, description="Refresh cached data")


class DashboardDataResponse(BaseAnalyticsSchema):
    """Schema for dashboard data response."""

    status: str = Field(..., description="Request status")
    dashboard: Dict[str, Any] = Field(..., description="Dashboard configuration")
    widget_data: Dict[str, Any] = Field(..., description="Widget data")
    period_start: Optional[str] = Field(None, description="Period start")
    period_end: Optional[str] = Field(None, description="Period end")
    generated_at: str = Field(..., description="Data generation timestamp")
    cache_expires_at: Optional[str] = Field(None, description="Cache expiration time")


# =============================================================================
# Report Schemas
# =============================================================================


class ReportCreateRequest(BaseAnalyticsSchema):
    """Schema for creating analytics report."""

    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., min_length=1, max_length=200, description="Report name")
    title: Optional[str] = Field(None, max_length=300, description="Report title")
    description: Optional[str] = Field(None, description="Description")
    report_type: str = Field(..., description="Report type")

    # Content configuration
    metrics: List[str] = Field(default_factory=list, description="Metric IDs")
    dashboards: List[str] = Field(default_factory=list, description="Dashboard IDs")
    data_sources: List[str] = Field(default_factory=list, description="Data source IDs")

    # Parameters and filters
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Report parameters"
    )
    filters: Dict[str, Any] = Field(default_factory=dict, description="Report filters")
    period_config: Dict[str, Any] = Field(
        default_factory=dict, description="Period configuration"
    )

    # Scheduling
    is_scheduled: bool = Field(False, description="Scheduled report")
    schedule_config: Dict[str, Any] = Field(
        default_factory=dict, description="Schedule configuration"
    )
    schedule_cron: Optional[str] = Field(None, description="Cron schedule")

    # Output settings
    format: str = Field("pdf", description="Output format")
    template_id: Optional[str] = Field(None, description="Template ID")
    output_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Output settings"
    )

    # Distribution
    recipients: List[str] = Field(default_factory=list, description="Email recipients")
    delivery_method: str = Field("email", description="Delivery method")
    delivery_config: Dict[str, Any] = Field(
        default_factory=dict, description="Delivery configuration"
    )

    # Security
    is_confidential: bool = Field(False, description="Confidential report")
    access_level: str = Field("organization", description="Access level")
    allowed_roles: List[str] = Field(default_factory=list, description="Allowed roles")
    allowed_users: List[str] = Field(default_factory=list, description="Allowed users")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")

    @validator("format")
    def validate_format(cls, v) -> dict:
        """Validate output format."""
        allowed_formats = ["pdf", "excel", "csv", "html", "json", "png", "svg"]
        if v not in allowed_formats:
            raise ValueError(f"Format must be one of: {', '.join(allowed_formats)}")
        return v

    @validator("delivery_method")
    def validate_delivery_method(cls, v) -> dict:
        """Validate delivery method."""
        allowed_methods = ["email", "webhook", "ftp", "s3", "download"]
        if v not in allowed_methods:
            raise ValueError(
                f"Delivery method must be one of: {', '.join(allowed_methods)}"
            )
        return v


class ReportResponse(BaseAnalyticsSchema):
    """Schema for report response."""

    id: str = Field(..., description="Report ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Report name")
    title: Optional[str] = Field(None, description="Report title")
    description: Optional[str] = Field(None, description="Description")
    report_type: str = Field(..., description="Report type")

    # Status and scheduling
    status: ReportStatus = Field(..., description="Report status")
    is_scheduled: bool = Field(..., description="Scheduled report")
    schedule_cron: Optional[str] = Field(None, description="Cron schedule")
    next_run_at: Optional[datetime] = Field(None, description="Next run time")
    last_run_at: Optional[datetime] = Field(None, description="Last run time")

    # Statistics
    generation_count: int = Field(..., description="Generation count")
    last_generation_duration: Optional[int] = Field(
        None, description="Last generation duration (ms)"
    )
    avg_generation_time: Optional[int] = Field(
        None, description="Average generation time (ms)"
    )

    # Output
    format: str = Field(..., description="Output format")
    last_output_path: Optional[str] = Field(None, description="Last output path")
    last_output_size: Optional[int] = Field(
        None, description="Last output size (bytes)"
    )
    last_error: Optional[str] = Field(None, description="Last error message")

    # Access control
    is_confidential: bool = Field(..., description="Confidential report")
    access_level: str = Field(..., description="Access level")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class ReportGenerationRequest(BaseAnalyticsSchema):
    """Schema for report generation request."""

    execution_type: str = Field("manual", description="Execution type")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Generation parameters"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Generation filters"
    )
    period_start: Optional[date] = Field(None, description="Report period start")
    period_end: Optional[date] = Field(None, description="Report period end")
    output_format: Optional[str] = Field(None, description="Override output format")


class ReportGenerationResult(BaseAnalyticsSchema):
    """Schema for report generation result."""

    status: str = Field(..., description="Generation status")
    execution_id: str = Field(..., description="Execution ID")
    output_path: Optional[str] = Field(None, description="Output file path")
    generation_time_ms: int = Field(..., description="Generation time in milliseconds")
    records_processed: int = Field(..., description="Records processed")
    charts_generated: Optional[int] = Field(None, description="Charts generated")
    file_size_bytes: Optional[int] = Field(None, description="Output file size")


# =============================================================================
# Prediction Schemas
# =============================================================================


class PredictionCreateRequest(BaseAnalyticsSchema):
    """Schema for creating prediction model."""

    organization_id: str = Field(..., description="Organization ID")
    metric_id: Optional[str] = Field(None, description="Target metric ID")
    name: str = Field(..., min_length=1, max_length=200, description="Model name")
    description: Optional[str] = Field(None, description="Description")
    prediction_type: str = Field(..., description="Prediction type")
    model_type: str = Field(..., description="Model type")

    # Model configuration
    model_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Model parameters"
    )
    feature_columns: List[str] = Field(
        default_factory=list, description="Feature columns"
    )
    target_column: Optional[str] = Field(None, description="Target column")

    # Prediction settings
    prediction_horizon: int = Field(
        ..., ge=1, le=365, description="Prediction horizon in days"
    )
    prediction_intervals: List[float] = Field(
        default_factory=list, description="Confidence intervals"
    )
    update_frequency: str = Field("weekly", description="Model update frequency")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")

    @validator("prediction_type")
    def validate_prediction_type(cls, v) -> dict:
        """Validate prediction type."""
        allowed_types = ["forecast", "trend", "classification", "anomaly", "regression"]
        if v not in allowed_types:
            raise ValueError(
                f"Prediction type must be one of: {', '.join(allowed_types)}"
            )
        return v

    @validator("model_type")
    def validate_model_type(cls, v) -> dict:
        """Validate model type."""
        allowed_models = [
            "linear_regression",
            "arima",
            "prophet",
            "lstm",
            "random_forest",
            "xgboost",
        ]
        if v not in allowed_models:
            raise ValueError(f"Model type must be one of: {', '.join(allowed_models)}")
        return v

    @validator("update_frequency")
    def validate_update_frequency(cls, v) -> dict:
        """Validate update frequency."""
        allowed_frequencies = ["daily", "weekly", "monthly", "quarterly"]
        if v not in allowed_frequencies:
            raise ValueError(
                f"Update frequency must be one of: {', '.join(allowed_frequencies)}"
            )
        return v


class PredictionResponse(BaseAnalyticsSchema):
    """Schema for prediction model response."""

    id: str = Field(..., description="Prediction model ID")
    organization_id: str = Field(..., description="Organization ID")
    metric_id: Optional[str] = Field(None, description="Target metric ID")
    name: str = Field(..., description="Model name")
    description: Optional[str] = Field(None, description="Description")
    prediction_type: str = Field(..., description="Prediction type")
    model_type: str = Field(..., description="Model type")

    # Model performance
    accuracy_score: Optional[Decimal] = Field(None, description="Accuracy score")
    mae_score: Optional[Decimal] = Field(None, description="Mean Absolute Error")
    rmse_score: Optional[Decimal] = Field(None, description="Root Mean Square Error")
    r2_score: Optional[Decimal] = Field(None, description="R-squared score")

    # Status and training
    is_active: bool = Field(..., description="Active status")
    last_trained_at: Optional[datetime] = Field(None, description="Last training time")
    training_duration: Optional[int] = Field(
        None, description="Training duration (seconds)"
    )
    model_version: Optional[str] = Field(None, description="Model version")
    training_data_points: Optional[int] = Field(
        None, description="Training data points"
    )

    # Predictions
    prediction_horizon: int = Field(..., description="Prediction horizon (days)")
    cache_valid_until: Optional[datetime] = Field(None, description="Cache expiration")
    is_model_degraded: bool = Field(..., description="Model degradation flag")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class PredictionResult(BaseAnalyticsSchema):
    """Schema for prediction results."""

    status: str = Field(..., description="Prediction status")
    prediction_id: str = Field(..., description="Prediction model ID")
    model_type: str = Field(..., description="Model type")
    last_trained_at: Optional[str] = Field(None, description="Last training time")
    accuracy_score: Optional[float] = Field(None, description="Model accuracy")
    predictions: List[Dict[str, Any]] = Field(..., description="Prediction values")
    forecast_horizon: int = Field(..., description="Forecast horizon")
    confidence_intervals: List[float] = Field(
        default_factory=list, description="Confidence intervals"
    )
    generated_at: str = Field(..., description="Generation timestamp")


# =============================================================================
# Alert Schemas
# =============================================================================


class AlertCreateRequest(BaseAnalyticsSchema):
    """Schema for creating analytics alert."""

    organization_id: str = Field(..., description="Organization ID")
    metric_id: str = Field(..., description="Target metric ID")
    name: str = Field(..., min_length=1, max_length=200, description="Alert name")
    description: Optional[str] = Field(None, description="Description")
    alert_type: str = Field(..., description="Alert type")

    # Alert conditions
    conditions: Dict[str, Any] = Field(..., description="Alert conditions")
    threshold_config: Dict[str, Any] = Field(
        default_factory=dict, description="Threshold configuration"
    )
    comparison_config: Dict[str, Any] = Field(
        default_factory=dict, description="Comparison configuration"
    )

    # Evaluation settings
    evaluation_frequency: str = Field("hourly", description="Evaluation frequency")
    evaluation_window: str = Field("1_hour", description="Evaluation window")
    grace_period: int = Field(0, ge=0, description="Grace period in minutes")

    # Alert severity
    priority: AlertPriority = Field(AlertPriority.MEDIUM, description="Alert priority")
    severity_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Severity rules"
    )
    escalation_rules: List[Dict[str, Any]] = Field(
        default_factory=list, description="Escalation rules"
    )

    # Notification settings
    notification_channels: List[str] = Field(
        default_factory=lambda: ["email"], description="Notification channels"
    )
    notification_recipients: List[str] = Field(
        default_factory=list, description="Notification recipients"
    )
    notification_template: Optional[str] = Field(
        None, description="Notification template"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")

    @validator("alert_type")
    def validate_alert_type(cls, v) -> dict:
        """Validate alert type."""
        allowed_types = ["threshold", "anomaly", "trend", "comparison", "change"]
        if v not in allowed_types:
            raise ValueError(f"Alert type must be one of: {', '.join(allowed_types)}")
        return v

    @validator("evaluation_frequency")
    def validate_evaluation_frequency(cls, v) -> dict:
        """Validate evaluation frequency."""
        allowed_frequencies = ["realtime", "hourly", "daily", "weekly"]
        if v not in allowed_frequencies:
            raise ValueError(
                f"Evaluation frequency must be one of: {', '.join(allowed_frequencies)}"
            )
        return v

    @validator("notification_channels")
    def validate_notification_channels(cls, v) -> dict:
        """Validate notification channels."""
        allowed_channels = ["email", "sms", "slack", "teams", "webhook", "in_app"]
        for channel in v:
            if channel not in allowed_channels:
                raise ValueError(
                    f"Notification channel must be one of: {', '.join(allowed_channels)}"
                )
        return v


class AlertResponse(BaseAnalyticsSchema):
    """Schema for alert response."""

    id: str = Field(..., description="Alert ID")
    organization_id: str = Field(..., description="Organization ID")
    metric_id: str = Field(..., description="Target metric ID")
    name: str = Field(..., description="Alert name")
    description: Optional[str] = Field(None, description="Description")
    alert_type: str = Field(..., description="Alert type")

    # Status and tracking
    is_active: bool = Field(..., description="Active status")
    is_triggered: bool = Field(..., description="Currently triggered")
    trigger_count: int = Field(..., description="Total trigger count")
    last_triggered_at: Optional[datetime] = Field(None, description="Last trigger time")
    last_evaluated_at: Optional[datetime] = Field(
        None, description="Last evaluation time"
    )

    # Configuration
    priority: AlertPriority = Field(..., description="Alert priority")
    evaluation_frequency: str = Field(..., description="Evaluation frequency")
    notification_channels: List[str] = Field(..., description="Notification channels")

    # Suppression
    is_suppressed: bool = Field(..., description="Suppressed status")
    suppressed_until: Optional[datetime] = Field(None, description="Suppressed until")
    suppression_reason: Optional[str] = Field(None, description="Suppression reason")

    # Resolution
    is_resolved: bool = Field(..., description="Resolved status")
    resolved_at: Optional[datetime] = Field(None, description="Resolution time")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")

    # Performance
    false_positive_count: int = Field(..., description="False positive count")
    accuracy_rate: Optional[Decimal] = Field(None, description="Accuracy rate")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


# =============================================================================
# Insight Schemas
# =============================================================================


class InsightResponse(BaseAnalyticsSchema):
    """Schema for analytics insight response."""

    id: str = Field(..., description="Insight ID")
    organization_id: str = Field(..., description="Organization ID")
    title: str = Field(..., description="Insight title")
    summary: Optional[str] = Field(None, description="Insight summary")
    description: Optional[str] = Field(None, description="Detailed description")
    insight_type: str = Field(..., description="Insight type")

    # Related entities
    related_metrics: List[str] = Field(..., description="Related metric IDs")
    related_dashboards: List[str] = Field(..., description="Related dashboard IDs")
    affected_areas: List[str] = Field(..., description="Affected business areas")

    # Insight data
    key_findings: List[Dict[str, Any]] = Field(..., description="Key findings")
    supporting_data: Dict[str, Any] = Field(..., description="Supporting data")
    statistical_significance: Optional[Decimal] = Field(
        None, description="Statistical significance"
    )
    confidence_level: Optional[Decimal] = Field(None, description="Confidence level")

    # Recommendations
    recommendations: List[Dict[str, Any]] = Field(..., description="Recommendations")
    action_items: List[Dict[str, Any]] = Field(..., description="Action items")
    potential_impact: Optional[str] = Field(None, description="Potential impact")
    impact_estimate: Dict[str, Any] = Field(..., description="Impact estimate")

    # Prioritization
    priority_score: Optional[Decimal] = Field(None, description="Priority score")
    urgency_level: str = Field(..., description="Urgency level")
    business_value: Optional[str] = Field(None, description="Business value")

    # Status
    status: str = Field(..., description="Insight status")
    is_actionable: bool = Field(..., description="Actionable flag")
    is_automated: bool = Field(..., description="Automatically generated")

    # Validity
    valid_from: Optional[date] = Field(None, description="Valid from date")
    valid_until: Optional[date] = Field(None, description="Valid until date")
    is_expired: bool = Field(..., description="Expired flag")

    # User interaction
    user_rating: Optional[Decimal] = Field(None, description="User rating (1-5)")
    feedback_comments: Optional[str] = Field(None, description="User feedback")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class InsightGenerationRequest(BaseAnalyticsSchema):
    """Schema for insight generation request."""

    organization_id: str = Field(..., description="Organization ID")
    analytics_types: List[AnalyticsType] = Field(
        default_factory=list, description="Analytics types to analyze"
    )
    period_days: int = Field(30, ge=7, le=365, description="Analysis period in days")
    focus_areas: List[str] = Field(
        default_factory=list, description="Specific focus areas"
    )
    min_confidence: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )


# =============================================================================
# System Health Schemas
# =============================================================================


class AnalyticsSystemHealthResponse(BaseAnalyticsSchema):
    """Schema for analytics system health response."""

    status: str = Field(..., description="System status")
    database_connection: str = Field(..., description="Database connection status")
    services_available: bool = Field(..., description="Services availability")

    statistics: Dict[str, Any] = Field(..., description="System statistics")
    version: str = Field(..., description="System version")
    timestamp: str = Field(..., description="Health check timestamp")

    # Optional error info
    error: Optional[str] = Field(None, description="Error message if unhealthy")


# =============================================================================
# Bulk Operations Schemas
# =============================================================================


class BulkMetricOperationRequest(BaseAnalyticsSchema):
    """Schema for bulk metric operations."""

    metric_ids: List[str] = Field(
        ..., min_items=1, max_items=100, description="Metric IDs"
    )
    operation: str = Field(..., description="Operation type")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Operation parameters"
    )


class BulkOperationResponse(BaseAnalyticsSchema):
    """Schema for bulk operation response."""

    operation: str = Field(..., description="Operation type")
    total_requested: int = Field(..., description="Total items requested")
    successful: int = Field(..., description="Successful operations")
    failed: int = Field(..., description="Failed operations")

    # Results
    success_ids: List[str] = Field(..., description="Successful item IDs")
    errors: List[Dict[str, Any]] = Field(..., description="Error details")

    # Processing info
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    success_rate: float = Field(..., description="Success rate percentage")
