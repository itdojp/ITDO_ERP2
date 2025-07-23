"""
Analytics System Models - CC02 v31.0 Phase 2

Comprehensive analytics system with:
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

import uuid
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class AnalyticsType(str, Enum):
    """Analytics type enumeration."""

    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"
    SALES = "sales"
    MARKETING = "marketing"
    HR = "hr"
    PROJECT = "project"
    INVENTORY = "inventory"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    PREDICTIVE = "predictive"
    EXECUTIVE = "executive"


class MetricType(str, Enum):
    """Metric type enumeration."""

    KPI = "kpi"
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TREND = "trend"
    RATIO = "ratio"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    DURATION = "duration"


class AggregationType(str, Enum):
    """Aggregation type enumeration."""

    SUM = "sum"
    COUNT = "count"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    DISTINCT = "distinct"
    VARIANCE = "variance"
    STDDEV = "stddev"


class PeriodType(str, Enum):
    """Period type enumeration."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


class DashboardType(str, Enum):
    """Dashboard type enumeration."""

    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    ANALYTICAL = "analytical"
    TACTICAL = "tactical"
    STRATEGIC = "strategic"
    COMPLIANCE = "compliance"
    PERSONAL = "personal"
    TEAM = "team"
    DEPARTMENTAL = "departmental"
    ORGANIZATIONAL = "organizational"


class ReportStatus(str, Enum):
    """Report status enumeration."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class AlertPriority(str, Enum):
    """Alert priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalyticsDataSource(Base):
    """Analytics Data Source - Configuration for data collection sources."""

    __tablename__ = "analytics_data_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Source identification
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    source_type = Column(String(100), nullable=False)  # database, api, file, stream

    # Connection configuration
    connection_string = Column(String(1000))
    connection_config = Column(JSON, default={})
    authentication_config = Column(JSON, default={})

    # Data schema
    schema_definition = Column(JSON, default={})
    table_mappings = Column(JSON, default={})
    field_mappings = Column(JSON, default={})
    transformation_rules = Column(JSON, default={})

    # Sync configuration
    sync_frequency = Column(
        String(50), default="daily"
    )  # realtime, hourly, daily, weekly
    sync_schedule = Column(String(100))  # cron expression
    last_sync_at = Column(DateTime)
    next_sync_at = Column(DateTime)

    # Data quality
    validation_rules = Column(JSON, default={})
    cleansing_rules = Column(JSON, default={})
    quality_score = Column(Numeric(5, 2))

    # Status and monitoring
    is_active = Column(Boolean, default=True)
    is_realtime = Column(Boolean, default=False)
    health_status = Column(String(50), default="healthy")
    error_count = Column(Integer, default=0)
    last_error = Column(Text)

    # Performance metrics
    records_processed = Column(Integer, default=0)
    processing_time_avg = Column(Numeric(8, 2))
    throughput_per_minute = Column(Numeric(10, 2))

    # Metadata
    tags = Column(JSON, default=[])
    analytics_metadata = Column(JSON, default={})
    custom_fields = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")
    metrics = relationship("AnalyticsMetric", back_populates="data_source")


class AnalyticsMetric(Base):
    """Analytics Metric - Individual metric definitions and calculations."""

    __tablename__ = "analytics_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    data_source_id = Column(String, ForeignKey("analytics_data_sources.id"))

    # Metric identification
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, index=True)
    display_name = Column(String(200))
    description = Column(Text)
    category = Column(String(100))

    # Metric configuration
    metric_type = Column(SQLEnum(MetricType), nullable=False)
    analytics_type = Column(SQLEnum(AnalyticsType), nullable=False)
    aggregation_type = Column(SQLEnum(AggregationType), nullable=False)

    # Calculation definition
    calculation_formula = Column(Text, nullable=False)
    calculation_fields = Column(JSON, default=[])
    calculation_filters = Column(JSON, default={})
    calculation_parameters = Column(JSON, default={})

    # Units and formatting
    unit = Column(String(50))
    format_pattern = Column(String(100))
    decimal_places = Column(Integer, default=2)
    multiplier = Column(Numeric(10, 4), default=1)

    # Targets and thresholds
    target_value = Column(Numeric(15, 4))
    min_threshold = Column(Numeric(15, 4))
    max_threshold = Column(Numeric(15, 4))
    warning_threshold = Column(Numeric(15, 4))
    critical_threshold = Column(Numeric(15, 4))

    # Benchmarking
    benchmark_value = Column(Numeric(15, 4))
    benchmark_source = Column(String(200))
    industry_average = Column(Numeric(15, 4))

    # Calculation schedule
    calculation_frequency = Column(String(50), default="daily")
    calculation_schedule = Column(String(100))
    last_calculated_at = Column(DateTime)
    next_calculation_at = Column(DateTime)

    # Current values
    current_value = Column(Numeric(15, 4))
    previous_value = Column(Numeric(15, 4))
    trend_direction = Column(String(20))  # up, down, stable
    trend_percentage = Column(Numeric(5, 2))

    # Status and quality
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    quality_score = Column(Numeric(5, 2))
    confidence_level = Column(Numeric(5, 2))

    # Display configuration
    chart_type = Column(String(50), default="line")
    color_scheme = Column(String(100))
    display_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)

    # Permissions
    access_level = Column(
        String(50), default="organization"
    )  # public, organization, department, team, private
    allowed_roles = Column(JSON, default=[])
    allowed_users = Column(JSON, default=[])

    # Metadata
    tags = Column(JSON, default=[])
    analytics_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    data_source = relationship("AnalyticsDataSource", back_populates="metrics")
    creator = relationship("User")
    data_points = relationship("AnalyticsDataPoint", back_populates="metric")
    alerts = relationship("AnalyticsAlert", back_populates="metric")


class AnalyticsDataPoint(Base):
    """Analytics Data Point - Time-series data points for metrics."""

    __tablename__ = "analytics_data_points"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    metric_id = Column(String, ForeignKey("analytics_metrics.id"), nullable=False)

    # Data point identification
    timestamp = Column(DateTime, nullable=False, index=True)
    period_type = Column(SQLEnum(PeriodType), nullable=False)
    period_start = Column(DateTime)
    period_end = Column(DateTime)

    # Values
    value = Column(Numeric(15, 4), nullable=False)
    raw_value = Column(Numeric(15, 4))
    calculated_value = Column(Numeric(15, 4))

    # Statistical data
    count = Column(Integer)
    sum_value = Column(Numeric(15, 4))
    avg_value = Column(Numeric(15, 4))
    min_value = Column(Numeric(15, 4))
    max_value = Column(Numeric(15, 4))
    median_value = Column(Numeric(15, 4))
    std_deviation = Column(Numeric(15, 4))

    # Dimensions
    dimensions = Column(JSON, default={})  # Additional grouping dimensions
    filters_applied = Column(JSON, default={})

    # Data quality
    quality_score = Column(Numeric(5, 2))
    is_estimated = Column(Boolean, default=False)
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Numeric(5, 2))

    # Metadata
    source_query = Column(Text)
    calculation_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    metric = relationship("AnalyticsMetric", back_populates="data_points")


class AnalyticsDashboard(Base):
    """Analytics Dashboard - Configurable dashboard for metric visualization."""

    __tablename__ = "analytics_dashboards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Dashboard identification
    name = Column(String(200), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    dashboard_type = Column(SQLEnum(DashboardType), nullable=False)

    # Layout configuration
    layout_config = Column(JSON, default={})
    grid_config = Column(JSON, default={})
    responsive_config = Column(JSON, default={})

    # Widgets configuration
    widgets = Column(JSON, default=[])
    widget_positions = Column(JSON, default={})
    widget_settings = Column(JSON, default={})

    # Filters and parameters
    global_filters = Column(JSON, default={})
    default_period = Column(String(50), default="last_30_days")
    auto_refresh = Column(Boolean, default=True)
    refresh_interval = Column(Integer, default=300)  # seconds

    # Sharing and permissions
    is_public = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=False)
    share_token = Column(String(200))
    access_level = Column(String(50), default="private")
    allowed_roles = Column(JSON, default=[])
    allowed_users = Column(JSON, default=[])

    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime)

    # Customization
    theme = Column(String(100), default="default")
    color_scheme = Column(String(100))
    custom_css = Column(Text)

    # Export configuration
    export_formats = Column(JSON, default=["pdf", "png", "excel"])
    email_recipients = Column(JSON, default=[])
    email_schedule = Column(String(100))

    # Metadata
    tags = Column(JSON, default=[])
    analytics_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


class AnalyticsReport(Base):
    """Analytics Report - Automated and scheduled analytics reports."""

    __tablename__ = "analytics_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Report identification
    name = Column(String(200), nullable=False)
    title = Column(String(300))
    description = Column(Text)
    report_type = Column(String(100), nullable=False)

    # Report configuration
    metrics = Column(JSON, default=[])
    dashboards = Column(JSON, default=[])
    data_sources = Column(JSON, default=[])

    # Report parameters
    parameters = Column(JSON, default={})
    filters = Column(JSON, default={})
    period_config = Column(JSON, default={})

    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_config = Column(JSON, default={})
    schedule_cron = Column(String(100))
    next_run_at = Column(DateTime)
    last_run_at = Column(DateTime)

    # Generation settings
    format = Column(String(50), default="pdf")
    template_id = Column(String)
    output_settings = Column(JSON, default={})

    # Distribution
    recipients = Column(JSON, default=[])
    delivery_method = Column(String(50), default="email")
    delivery_config = Column(JSON, default={})

    # Status and tracking
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.DRAFT)
    generation_count = Column(Integer, default=0)
    last_generation_duration = Column(Integer)  # milliseconds
    avg_generation_time = Column(Integer)

    # Results
    last_output_path = Column(String(1000))
    last_output_size = Column(Integer)
    last_error = Column(Text)

    # Access control
    is_confidential = Column(Boolean, default=False)
    access_level = Column(String(50), default="organization")
    allowed_roles = Column(JSON, default=[])
    allowed_users = Column(JSON, default=[])

    # Metadata
    tags = Column(JSON, default=[])
    analytics_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")
    executions = relationship("AnalyticsReportExecution", back_populates="report")


class AnalyticsReportExecution(Base):
    """Analytics Report Execution - Individual report generation instances."""

    __tablename__ = "analytics_report_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    report_id = Column(String, ForeignKey("analytics_reports.id"), nullable=False)

    # Execution details
    execution_type = Column(String(50), nullable=False)  # scheduled, manual, triggered
    triggered_by = Column(String, ForeignKey("users.id"))

    # Status and timing
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.SCHEDULED)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # Parameters used
    parameters = Column(JSON, default={})
    filters = Column(JSON, default={})
    period_start = Column(Date)
    period_end = Column(Date)

    # Output details
    output_format = Column(String(50))
    output_path = Column(String(1000))
    output_size_bytes = Column(Integer)

    # Processing details
    records_processed = Column(Integer)
    metrics_calculated = Column(Integer)
    charts_generated = Column(Integer)

    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)

    # Performance metrics
    query_time_ms = Column(Integer)
    processing_time_ms = Column(Integer)
    rendering_time_ms = Column(Integer)

    # Distribution
    recipients_notified = Column(JSON, default=[])
    notification_status = Column(JSON, default={})

    # Metadata
    execution_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    report = relationship("AnalyticsReport", back_populates="executions")
    triggered_by_user = relationship("User")


class AnalyticsAlert(Base):
    """Analytics Alert - Threshold-based alerts and notifications."""

    __tablename__ = "analytics_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    metric_id = Column(String, ForeignKey("analytics_metrics.id"), nullable=False)

    # Alert identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    alert_type = Column(
        String(100), nullable=False
    )  # threshold, anomaly, trend, comparison

    # Alert conditions
    conditions = Column(JSON, nullable=False)
    threshold_config = Column(JSON, default={})
    comparison_config = Column(JSON, default={})

    # Evaluation settings
    evaluation_frequency = Column(String(50), default="hourly")
    evaluation_window = Column(String(50), default="1_hour")
    grace_period = Column(Integer, default=0)  # minutes

    # Alert severity
    priority = Column(SQLEnum(AlertPriority), default=AlertPriority.MEDIUM)
    severity_rules = Column(JSON, default={})
    escalation_rules = Column(JSON, default=[])

    # Notification settings
    notification_channels = Column(JSON, default=["email"])
    notification_recipients = Column(JSON, default=[])
    notification_template = Column(Text)

    # Status and tracking
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    trigger_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)
    last_evaluated_at = Column(DateTime)

    # Suppression
    is_suppressed = Column(Boolean, default=False)
    suppressed_until = Column(DateTime)
    suppression_reason = Column(String(500))

    # Alert resolution
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String, ForeignKey("users.id"))
    resolution_notes = Column(Text)

    # Performance
    false_positive_count = Column(Integer, default=0)
    accuracy_rate = Column(Numeric(5, 2))

    # Metadata
    tags = Column(JSON, default=[])
    alert_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    metric = relationship("AnalyticsMetric", back_populates="alerts")
    creator = relationship("User", foreign_keys=[created_by])
    resolver = relationship("User", foreign_keys=[resolved_by])


class AnalyticsPrediction(Base):
    """Analytics Prediction - Predictive analytics and forecasting."""

    __tablename__ = "analytics_predictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    metric_id = Column(String, ForeignKey("analytics_metrics.id"))

    # Prediction identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    prediction_type = Column(
        String(100), nullable=False
    )  # forecast, trend, classification, anomaly

    # Model configuration
    model_type = Column(
        String(100), nullable=False
    )  # linear_regression, arima, neural_network, etc.
    model_parameters = Column(JSON, default={})
    feature_columns = Column(JSON, default=[])
    target_column = Column(String(200))

    # Training data
    training_period_start = Column(Date)
    training_period_end = Column(Date)
    training_data_points = Column(Integer)

    # Prediction settings
    prediction_horizon = Column(Integer, nullable=False)  # days
    prediction_intervals = Column(JSON, default=[])  # confidence intervals
    update_frequency = Column(String(50), default="weekly")

    # Model performance
    accuracy_score = Column(Numeric(5, 4))
    mae_score = Column(Numeric(10, 4))  # Mean Absolute Error
    rmse_score = Column(Numeric(10, 4))  # Root Mean Square Error
    r2_score = Column(Numeric(5, 4))  # R-squared

    # Model status
    is_active = Column(Boolean, default=True)
    last_trained_at = Column(DateTime)
    training_duration = Column(Integer)  # seconds
    model_version = Column(String(50))

    # Predictions cache
    cached_predictions = Column(JSON, default=[])
    cache_valid_until = Column(DateTime)

    # Validation and monitoring
    validation_results = Column(JSON, default={})
    drift_detection = Column(JSON, default={})
    is_model_degraded = Column(Boolean, default=False)

    # Metadata
    tags = Column(JSON, default=[])
    model_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    metric = relationship("AnalyticsMetric")
    creator = relationship("User")


class AnalyticsInsight(Base):
    """Analytics Insight - AI-generated insights and recommendations."""

    __tablename__ = "analytics_insights"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Insight identification
    title = Column(String(300), nullable=False)
    summary = Column(String(1000))
    description = Column(Text)
    insight_type = Column(String(100), nullable=False)

    # Related entities
    related_metrics = Column(JSON, default=[])
    related_dashboards = Column(JSON, default=[])
    affected_areas = Column(JSON, default=[])

    # Insight data
    key_findings = Column(JSON, default=[])
    supporting_data = Column(JSON, default={})
    statistical_significance = Column(Numeric(5, 4))
    confidence_level = Column(Numeric(5, 2))

    # Recommendations
    recommendations = Column(JSON, default=[])
    action_items = Column(JSON, default=[])
    potential_impact = Column(String(100))
    impact_estimate = Column(JSON, default={})

    # Prioritization
    priority_score = Column(Numeric(5, 2))
    urgency_level = Column(String(50), default="medium")
    business_value = Column(String(100))

    # Status and tracking
    status = Column(String(50), default="new")  # new, reviewed, actioned, dismissed
    is_actionable = Column(Boolean, default=True)
    is_automated = Column(Boolean, default=True)

    # User interaction
    viewed_by = Column(JSON, default=[])
    acknowledged_by = Column(JSON, default=[])
    dismissed_by = Column(String, ForeignKey("users.id"))
    dismissal_reason = Column(String(500))

    # Feedback and learning
    user_rating = Column(Numeric(3, 1))  # 1-5 scale
    feedback_comments = Column(Text)
    false_positive = Column(Boolean, default=False)

    # Generation metadata
    generation_model = Column(String(100))
    generation_version = Column(String(50))
    generation_parameters = Column(JSON, default={})

    # Validity
    valid_from = Column(Date)
    valid_until = Column(Date)
    is_expired = Column(Boolean, default=False)

    # Metadata
    tags = Column(JSON, default=[])
    insight_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    dismissed_by_user = relationship("User")


class AnalyticsAuditLog(Base):
    """Analytics Audit Log - Comprehensive audit trail for analytics operations."""

    __tablename__ = "analytics_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Action details
    action_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String, nullable=False)

    # User and session
    user_id = Column(String, ForeignKey("users.id"))
    session_id = Column(String(200))
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Changes
    old_values = Column(JSON)
    new_values = Column(JSON)
    changes_summary = Column(String(1000))

    # Context
    context_data = Column(JSON, default={})
    related_entities = Column(JSON, default=[])

    # Impact assessment
    impact_level = Column(String(50))  # low, medium, high, critical
    affected_users = Column(JSON, default=[])
    data_sensitivity = Column(String(50))

    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")
