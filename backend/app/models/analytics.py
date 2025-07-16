"""Analytics and reporting models for Phase 7 analysis functionality."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional, Any

from sqlalchemy import Boolean, DateTime, Integer, JSON, Numeric, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class ReportType(str, Enum):
    """Report type enumeration."""
    STANDARD = "standard"
    CUSTOM = "custom"
    DASHBOARD = "dashboard"
    SCHEDULED = "scheduled"


class ReportStatus(str, Enum):
    """Report status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ReportFrequency(str, Enum):
    """Report frequency enumeration."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ChartType(str, Enum):
    """Chart type enumeration."""
    LINE = "line"
    BAR = "bar"
    COLUMN = "column"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    TABLE = "table"
    GAUGE = "gauge"
    KPI = "kpi"


class DataSourceType(str, Enum):
    """Data source type enumeration."""
    DATABASE = "database"
    API = "api"
    FILE = "file"
    CALCULATION = "calculation"


class Report(SoftDeletableModel):
    """Report definition model."""

    __tablename__ = "reports"

    # Basic fields
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Report name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Report description"
    )
    report_type: Mapped[ReportType] = mapped_column(
        String(50), nullable=False, comment="Report type"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )
    created_by: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="Creator user ID"
    )

    # Report configuration
    status: Mapped[ReportStatus] = mapped_column(
        String(50), default=ReportStatus.DRAFT, comment="Report status"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Public visibility flag"
    )
    
    # Report definition
    query_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Query configuration (JSON)"
    )
    visualization_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Visualization configuration (JSON)"
    )
    parameters_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Parameters schema (JSON)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Active status"
    )

    # Scheduling
    is_scheduled: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Scheduled report flag"
    )
    schedule_frequency: Mapped[Optional[ReportFrequency]] = mapped_column(
        String(50), nullable=True, comment="Schedule frequency"
    )
    schedule_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Schedule configuration (JSON)"
    )
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Next scheduled run"
    )

    # Performance optimization
    cache_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Cache duration in minutes"
    )
    last_cached_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last cache timestamp"
    )

    # Metadata
    tags: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Report tags (comma-separated)"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Report category"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")
    created_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], lazy="select"
    )
    widgets: Mapped[List["ReportWidget"]] = relationship(
        "ReportWidget", back_populates="report", cascade="all, delete-orphan"
    )
    executions: Mapped[List["ReportExecution"]] = relationship(
        "ReportExecution", back_populates="report", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.report_type})"


class ReportWidget(SoftDeletableModel):
    """Report widget model for dashboard components."""

    __tablename__ = "report_widgets"

    # Foreign keys
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id"), nullable=False, comment="Report ID"
    )

    # Widget identification
    widget_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Unique widget ID within report"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Widget name"
    )
    chart_type: Mapped[ChartType] = mapped_column(
        String(50), nullable=False, comment="Chart type"
    )

    # Layout
    position_x: Mapped[int] = mapped_column(
        Integer, default=0, comment="X position in grid"
    )
    position_y: Mapped[int] = mapped_column(
        Integer, default=0, comment="Y position in grid"
    )
    width: Mapped[int] = mapped_column(
        Integer, default=4, comment="Widget width in grid units"
    )
    height: Mapped[int] = mapped_column(
        Integer, default=3, comment="Widget height in grid units"
    )

    # Data configuration
    data_source: Mapped[DataSourceType] = mapped_column(
        String(50), nullable=False, comment="Data source type"
    )
    query_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Query configuration (JSON)"
    )
    chart_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Chart configuration (JSON)"
    )

    # Display settings
    title: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Widget title"
    )
    show_legend: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Show legend flag"
    )
    show_title: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Show title flag"
    )

    # Interactivity
    is_drilldown_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Drilldown enabled flag"
    )
    drilldown_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Drilldown configuration (JSON)"
    )

    # Relationships
    report: Mapped["Report"] = relationship("Report", back_populates="widgets")

    def __str__(self) -> str:
        return f"{self.name} ({self.chart_type})"


class Dashboard(SoftDeletableModel):
    """Dashboard model for customizable analytics dashboards."""

    __tablename__ = "dashboards"

    # Basic fields
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Dashboard name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Dashboard description"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )
    created_by: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="Creator user ID"
    )

    # Dashboard settings
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Default dashboard flag"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Public visibility flag"
    )
    auto_refresh_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Auto-refresh interval in minutes"
    )

    # Layout configuration
    layout_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Layout configuration (JSON)"
    )
    filter_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Global filter configuration (JSON)"
    )

    # Metadata
    tags: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Dashboard tags (comma-separated)"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")
    created_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], lazy="select"
    )
    widgets: Mapped[List["DashboardWidget"]] = relationship(
        "DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return self.name


class DashboardWidget(SoftDeletableModel):
    """Dashboard widget model."""

    __tablename__ = "dashboard_widgets"

    # Foreign keys
    dashboard_id: Mapped[int] = mapped_column(
        ForeignKey("dashboards.id"), nullable=False, comment="Dashboard ID"
    )
    report_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("reports.id"), nullable=True, comment="Source report ID"
    )

    # Widget configuration
    widget_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Widget type"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Widget title"
    )

    # Layout
    position_x: Mapped[int] = mapped_column(
        Integer, default=0, comment="X position in grid"
    )
    position_y: Mapped[int] = mapped_column(
        Integer, default=0, comment="Y position in grid"
    )
    width: Mapped[int] = mapped_column(
        Integer, default=4, comment="Widget width in grid units"
    )
    height: Mapped[int] = mapped_column(
        Integer, default=3, comment="Widget height in grid units"
    )

    # Configuration
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Widget configuration (JSON)"
    )

    # Relationships
    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="widgets")
    report: Mapped[Optional["Report"]] = relationship("Report", lazy="select")

    def __str__(self) -> str:
        return f"{self.title} on {self.dashboard.name}"


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportExecution(SoftDeletableModel):
    """Report execution model for tracking report runs."""

    __tablename__ = "report_executions"

    # Foreign keys
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id"), nullable=False, comment="Report ID"
    )
    executed_by: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="User who executed (null for scheduled)"
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )

    # Execution details
    execution_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Execution type (manual, scheduled, api)"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Execution status (running, completed, failed)"
    )
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Execution start time"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Execution completion time"
    )
    duration_seconds: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 3), nullable=True, comment="Execution duration in seconds"
    )

    # Results
    row_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Number of result rows"
    )
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Execution result data (JSON)"
    )
    output_format: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Output format (pdf, excel, csv, json)"
    )
    output_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Output file URL"
    )
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error message if failed"
    )
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Detailed error information (JSON)"
    )

    # Parameters
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Execution parameters (JSON)"
    )
    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Applied filters (JSON)"
    )

    # Relationships
    report: Mapped["Report"] = relationship("Report", back_populates="executions")
    executed_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[executed_by], lazy="select"
    )
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")

    @property
    def is_completed(self) -> bool:
        """Check if execution is completed."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == "failed"

    @property
    def is_running(self) -> bool:
        """Check if execution is still running."""
        return self.status == "running"

    def __str__(self) -> str:
        return f"{self.report.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ReportSchedule(SoftDeletableModel):
    """Report schedule model for automated report execution."""

    __tablename__ = "report_schedules"

    # Foreign keys
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id"), nullable=False, comment="Report ID"
    )
    created_by: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="Creator user ID"
    )

    # Schedule configuration
    cron_expression: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Cron expression for scheduling"
    )
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Default parameters for execution (JSON)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Active schedule flag"
    )

    # Schedule tracking
    next_run: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Next scheduled run"
    )
    last_run: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last execution time"
    )
    run_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total execution count"
    )

    # Relationships
    report: Mapped["Report"] = relationship("Report", lazy="select")
    created_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], lazy="select"
    )

    def __str__(self) -> str:
        return f"Schedule for {self.report.name}"


class Chart(SoftDeletableModel):
    """Chart model for report visualization components."""

    __tablename__ = "charts"

    # Foreign keys
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id"), nullable=False, comment="Report ID"
    )
    dashboard_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("dashboards.id"), nullable=True, comment="Dashboard ID (if part of dashboard)"
    )

    # Chart identification
    chart_type: Mapped[ChartType] = mapped_column(
        String(50), nullable=False, comment="Chart type"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Chart title"
    )

    # Layout
    position_x: Mapped[int] = mapped_column(
        Integer, default=0, comment="X position in grid"
    )
    position_y: Mapped[int] = mapped_column(
        Integer, default=0, comment="Y position in grid"
    )
    width: Mapped[int] = mapped_column(
        Integer, default=400, comment="Chart width in pixels"
    )
    height: Mapped[int] = mapped_column(
        Integer, default=300, comment="Chart height in pixels"
    )

    # Configuration
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Chart configuration (JSON)"
    )
    data_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Data binding configuration (JSON)"
    )

    # Relationships
    report: Mapped["Report"] = relationship("Report", lazy="select")
    dashboard: Mapped[Optional["Dashboard"]] = relationship("Dashboard", lazy="select")

    def __str__(self) -> str:
        return f"{self.title} ({self.chart_type})"


class DataSource(SoftDeletableModel):
    """Data source model for analytics data connections."""

    __tablename__ = "data_sources"

    # Basic fields
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Data source name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Data source description"
    )
    source_type: Mapped[DataSourceType] = mapped_column(
        String(50), nullable=False, comment="Data source type"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )

    # Connection details
    connection_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Connection configuration (JSON)"
    )
    credentials: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Encrypted credentials (JSON)"
    )

    # Settings
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Active status"
    )
    refresh_frequency_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Data refresh frequency in minutes"
    )
    last_refreshed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last refresh timestamp"
    )

    # Schema information
    schema_definition: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Schema definition (JSON)"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")

    def __str__(self) -> str:
        return f"{self.name} ({self.source_type})"