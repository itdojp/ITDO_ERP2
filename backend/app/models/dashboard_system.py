"""Dashboard and reporting system models for CC02 v63.0 - Day 8: Advanced Dashboard & Report System."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DashboardType(str, Enum):
    """Dashboard type enumeration."""
    
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    SALES = "sales"
    INVENTORY = "inventory"
    SHIPPING = "shipping"
    ANALYTICS = "analytics"
    CUSTOM = "custom"


class WidgetType(str, Enum):
    """Widget type enumeration."""
    
    KPI_CARD = "kpi_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    TABLE = "table"
    GAUGE = "gauge"
    PROGRESS_BAR = "progress_bar"
    MAP = "map"
    CUSTOM = "custom"


class DataSourceType(str, Enum):
    """Data source type enumeration."""
    
    DATABASE = "database"
    API = "api"
    FILE = "file"
    REAL_TIME = "real_time"
    CALCULATED = "calculated"
    EXTERNAL = "external"


class RefreshInterval(str, Enum):
    """Refresh interval enumeration."""
    
    REAL_TIME = "real_time"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_6 = "6h"
    HOUR_12 = "12h"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MANUAL = "manual"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReportFormat(str, Enum):
    """Report format enumeration."""
    
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ReportStatus(str, Enum):
    """Report generation status."""
    
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AdvancedDashboard(Base):
    """Advanced dashboard configuration."""
    
    __tablename__ = "advanced_dashboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dashboard_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Dashboard Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    dashboard_type: Mapped[DashboardType] = mapped_column(String(50), nullable=False, index=True)
    
    # Access Control
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    shared_with: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    permissions: Mapped[Optional[Dict[str, List[str]]]] = mapped_column(JSON, default=dict)
    
    # Layout Configuration
    layout_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    grid_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    theme_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Behavior Settings
    auto_refresh: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    refresh_interval: Mapped[RefreshInterval] = mapped_column(String(20), default=RefreshInterval.MINUTE_5, nullable=False)
    real_time_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Filtering & Interactivity
    global_filters: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    drill_down_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cross_filtering: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Performance
    cache_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cache_duration_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    lazy_loading: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Mobile & Responsive
    mobile_layout: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    responsive_breakpoints: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON, default=dict)
    
    # Analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    avg_load_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Versioning
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    version_history: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    
    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    dashboard_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    widgets: Mapped[List["DashboardWidget"]] = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")
    reports: Mapped[List["CustomReport"]] = relationship("CustomReport", back_populates="dashboard")


class DashboardWidget(Base):
    """Dashboard widget configuration."""
    
    __tablename__ = "dashboard_widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    widget_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    dashboard_id: Mapped[int] = mapped_column(Integer, ForeignKey("advanced_dashboards.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Widget Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    widget_type: Mapped[WidgetType] = mapped_column(String(50), nullable=False)
    
    # Layout Position
    position_x: Mapped[int] = mapped_column(Integer, nullable=False)
    position_y: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    z_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Data Configuration
    data_source_id: Mapped[int] = mapped_column(Integer, ForeignKey("data_sources.id"), nullable=False)
    query_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    aggregation_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Visualization Settings
    chart_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    color_scheme: Mapped[Optional[str]] = mapped_column(String(50))
    custom_colors: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Interactivity
    clickable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    drill_down_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    filter_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Refresh & Performance
    auto_refresh: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    refresh_interval: Mapped[RefreshInterval] = mapped_column(String(20), default=RefreshInterval.MINUTE_5, nullable=False)
    cache_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Thresholds & Alerts
    alert_thresholds: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, default=dict)
    alert_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Performance Metrics
    avg_load_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    widget_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    dashboard: Mapped["AdvancedDashboard"] = relationship("AdvancedDashboard", back_populates="widgets")
    data_source: Mapped["DataSource"] = relationship("DataSource", back_populates="widgets")


class DataSource(Base):
    """Data source configuration for widgets and reports."""
    
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Source Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    source_type: Mapped[DataSourceType] = mapped_column(String(50), nullable=False)
    
    # Connection Configuration
    connection_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    authentication_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Query Configuration
    base_query: Mapped[Optional[str]] = mapped_column(Text)
    query_templates: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, default=dict)
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Schema Information
    schema_definition: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    available_fields: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    field_types: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, default=dict)
    
    # Performance
    cache_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cache_duration_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    connection_timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    query_timeout_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    
    # Health Monitoring
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime)
    health_check_interval_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Usage Metrics
    query_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_query_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    source_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    widgets: Mapped[List["DashboardWidget"]] = relationship("DashboardWidget", back_populates="data_source")
    reports: Mapped[List["CustomReport"]] = relationship("CustomReport", back_populates="data_source")


class CustomReport(Base):
    """Custom report configuration and generation."""
    
    __tablename__ = "custom_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Report Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Data Configuration
    dashboard_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("advanced_dashboards.id"))
    data_source_id: Mapped[int] = mapped_column(Integer, ForeignKey("data_sources.id"), nullable=False)
    query_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Report Layout
    template_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    sections: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    styling_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Parameters & Filters
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    default_filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Generation Settings
    supported_formats: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    default_format: Mapped[ReportFormat] = mapped_column(String(20), default=ReportFormat.PDF, nullable=False)
    page_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Scheduling
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schedule_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Distribution
    recipients: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    distribution_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Access Control
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    shared_with: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Performance
    avg_generation_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    max_generation_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    
    # Usage Statistics
    generation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    report_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    dashboard: Mapped[Optional["AdvancedDashboard"]] = relationship("AdvancedDashboard", back_populates="reports")
    data_source: Mapped["DataSource"] = relationship("DataSource", back_populates="reports")
    executions: Mapped[List["ReportExecution"]] = relationship("ReportExecution", back_populates="report", cascade="all, delete-orphan")


class ReportExecution(Base):
    """Report execution tracking."""
    
    __tablename__ = "report_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    report_id: Mapped[int] = mapped_column(Integer, ForeignKey("custom_reports.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Execution Details
    status: Mapped[ReportStatus] = mapped_column(String(20), default=ReportStatus.PENDING, nullable=False, index=True)
    format: Mapped[ReportFormat] = mapped_column(String(20), nullable=False)
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    generation_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Results
    file_path: Mapped[Optional[str]] = mapped_column(String(1000))
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    download_url: Mapped[Optional[str]] = mapped_column(String(1000))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # User Context
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Distribution
    distributed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    distribution_log: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    
    # Metadata
    execution_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    report: Mapped["CustomReport"] = relationship("CustomReport", back_populates="executions")


class KPIDefinition(Base):
    """KPI definition and configuration."""
    
    __tablename__ = "kpi_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kpi_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # KPI Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Calculation Configuration
    calculation_method: Mapped[str] = mapped_column(String(100), nullable=False)  # formula, aggregation, custom
    formula: Mapped[Optional[str]] = mapped_column(Text)
    data_sources: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    calculation_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Target & Thresholds
    target_value: Mapped[Optional[float]] = mapped_column(Float)
    warning_threshold: Mapped[Optional[float]] = mapped_column(Float)
    critical_threshold: Mapped[Optional[float]] = mapped_column(Float)
    threshold_direction: Mapped[str] = mapped_column(String(20), default="higher_is_better", nullable=False)
    
    # Frequency & Timing
    calculation_frequency: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)
    aggregation_period: Mapped[str] = mapped_column(String(20), default="day", nullable=False)
    historical_periods: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    
    # Alert Configuration
    alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    alert_recipients: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    escalation_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Visualization
    preferred_chart_type: Mapped[Optional[str]] = mapped_column(String(50))
    color_scheme: Mapped[Optional[str]] = mapped_column(String(50))
    display_format: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Business Context
    business_owner: Mapped[Optional[str]] = mapped_column(String(255))
    stakeholders: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    related_kpis: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    kpi_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    values: Mapped[List["KPIValue"]] = relationship("KPIValue", back_populates="kpi_definition", cascade="all, delete-orphan")
    alerts: Mapped[List["KPIAlert"]] = relationship("KPIAlert", back_populates="kpi_definition", cascade="all, delete-orphan")


class KPIValue(Base):
    """KPI calculated values over time."""
    
    __tablename__ = "kpi_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kpi_id: Mapped[int] = mapped_column(Integer, ForeignKey("kpi_definitions.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Value Details
    measurement_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Values
    value: Mapped[float] = mapped_column(Float, nullable=False)
    target_value: Mapped[Optional[float]] = mapped_column(Float)
    previous_value: Mapped[Optional[float]] = mapped_column(Float)
    change_amount: Mapped[Optional[float]] = mapped_column(Float)
    change_percentage: Mapped[Optional[float]] = mapped_column(Float)
    
    # Performance Indicators
    vs_target: Mapped[Optional[float]] = mapped_column(Float)  # Percentage vs target
    performance_status: Mapped[Optional[str]] = mapped_column(String(20))  # excellent, good, warning, critical
    trend_direction: Mapped[Optional[str]] = mapped_column(String(20))  # up, down, stable
    
    # Calculation Context
    calculation_method_used: Mapped[str] = mapped_column(String(100), nullable=False)
    data_points_count: Mapped[Optional[int]] = mapped_column(Integer)
    calculation_confidence: Mapped[Optional[float]] = mapped_column(Float)
    
    # Quality & Validation
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estimation_method: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Metadata
    calculation_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    kpi_definition: Mapped["KPIDefinition"] = relationship("KPIDefinition", back_populates="values")


class KPIAlert(Base):
    """KPI-based alerts and notifications."""
    
    __tablename__ = "kpi_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    kpi_id: Mapped[int] = mapped_column(Integer, ForeignKey("kpi_definitions.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Alert Details
    severity: Mapped[AlertSeverity] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Trigger Context
    trigger_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_type: Mapped[str] = mapped_column(String(20), nullable=False)  # above, below, equal
    measurement_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Alert Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(255))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Resolution
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(255))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Escalation
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    max_escalation_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Notification
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_channels: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    recipients_notified: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Actions
    suggested_actions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    automated_actions: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    actions_taken: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    
    # Metadata
    alert_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    kpi_definition: Mapped["KPIDefinition"] = relationship("KPIDefinition", back_populates="alerts")


class BusinessIntelligence(Base):
    """Business intelligence insights and recommendations."""
    
    __tablename__ = "business_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    insight_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Insight Details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)  # trend, anomaly, pattern, forecast
    
    # Analysis Context
    data_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    analysis_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Insight Details
    key_findings: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    statistical_significance: Mapped[Optional[float]] = mapped_column(Float)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    
    # Impact Assessment
    business_impact: Mapped[str] = mapped_column(String(20), nullable=False)  # high, medium, low
    financial_impact: Mapped[Optional[float]] = mapped_column(Float)
    affected_areas: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    
    # Recommendations
    recommendations: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    priority_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    implementation_difficulty: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    estimated_roi: Mapped[Optional[float]] = mapped_column(Float)
    
    # Supporting Data
    supporting_metrics: Mapped[List[str]] = mapped_column(JSON, default=list)
    related_kpis: Mapped[List[str]] = mapped_column(JSON, default=list)
    data_sources_used: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    
    # Visualization
    chart_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    visualization_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Follow-up
    requires_action: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    action_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255))
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, archived, resolved
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Engagement
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    insight_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    generated_by: Mapped[str] = mapped_column(String(100), default="system", nullable=False)  # system, user, ai
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)