"""Report schemas for Phase 7 analytics functionality."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReportBase(BaseModel):
    """Base report schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(..., min_length=1, max_length=100)
    query_config: Dict[str, Any] = Field(
        ..., description="Query configuration for data extraction"
    )
    visualization_config: Optional[Dict[str, Any]] = Field(
        None, description="Chart and visualization settings"
    )
    parameters_schema: Optional[Dict[str, Any]] = Field(
        None, description="Parameters schema for dynamic reports"
    )
    is_active: bool = Field(default=True)
    is_public: bool = Field(default=False)


class ReportCreate(ReportBase):
    """Schema for creating a new report."""

    organization_id: int = Field(..., gt=0)
    created_by: int = Field(..., gt=0)


class ReportUpdate(BaseModel):
    """Schema for updating a report."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    query_config: Optional[Dict[str, Any]] = None
    visualization_config: Optional[Dict[str, Any]] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class ReportResponse(ReportBase):
    """Schema for report response."""

    id: int
    organization_id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportExecutionBase(BaseModel):
    """Base report execution schema."""

    parameters: Dict[str, Any] = Field(default_factory=dict)


class ReportExecutionCreate(ReportExecutionBase):
    """Schema for creating a report execution."""

    report_id: int = Field(..., gt=0)


class ReportExecutionResponse(ReportExecutionBase):
    """Schema for report execution response."""

    id: int
    report_id: int
    status: str
    organization_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    row_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportDataResponse(BaseModel):
    """Schema for report data response."""

    format: str
    data: dict[str, Any] | list[Any] | str | bytes
    execution_id: int
    generated_at: str


class ReportTaskUpdate(BaseModel):
    """Schema for updating a report task."""

    status: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None


class ReportTaskResponse(BaseModel):
    """Schema for report task response."""

    id: int
    report_id: int
    name: str
    description: Optional[str] = None
    status: str
    assigned_to: Optional[int] = None
    assigned_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_config: Optional[Dict[str, Any]] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChartBase(BaseModel):
    """Base chart schema."""

    chart_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    config: Dict[str, Any] = Field(default_factory=dict)
    position_x: int = Field(default=0)
    position_y: int = Field(default=0)
    width: int = Field(default=400, gt=0)
    height: int = Field(default=300, gt=0)


class ChartCreate(ChartBase):
    """Schema for creating a chart."""

    report_id: int = Field(..., gt=0)


class ChartUpdate(BaseModel):
    """Schema for updating a chart."""

    chart_type: Optional[str] = Field(None, min_length=1, max_length=50)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[Dict[str, Any]] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)


class ChartResponse(ChartBase):
    """Schema for chart response."""

    id: int
    report_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DashboardBase(BaseModel):
    """Base dashboard schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = Field(default=False)
    refresh_interval: int = Field(default=300, ge=30)  # seconds


class DashboardCreate(DashboardBase):
    """Schema for creating a dashboard."""

    organization_id: int = Field(..., gt=0)
    created_by: int = Field(..., gt=0)


class DashboardUpdate(BaseModel):
    """Schema for updating a dashboard."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    layout_config: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    refresh_interval: Optional[int] = Field(None, ge=30)


class DashboardResponse(DashboardBase):
    """Schema for dashboard response."""

    id: int
    organization_id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportTemplateResponse(BaseModel):
    """Schema for report template response."""

    id: str
    name: str
    category: str
    description: str
    parameters: List[str]
    query_template: Optional[str] = None
    visualization_template: Optional[Dict[str, Any]] = None


class ReportCategoryResponse(BaseModel):
    """Schema for report category response."""

    id: str
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None


class ReportScheduleBase(BaseModel):
    """Base report schedule schema."""

    cron_expression: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)


class ReportScheduleCreate(ReportScheduleBase):
    """Schema for creating a report schedule."""

    report_id: int = Field(..., gt=0)
    created_by: int = Field(..., gt=0)


class ReportScheduleUpdate(BaseModel):
    """Schema for updating a report schedule."""

    cron_expression: Optional[str] = Field(None, min_length=1)
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ReportScheduleResponse(ReportScheduleBase):
    """Schema for report schedule response."""

    id: int
    report_id: int
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportAnalyticsResponse(BaseModel):
    """Schema for report analytics response."""

    report_id: int
    total_executions: int
    successful_executions: int
    success_rate: float
    average_execution_time_seconds: float
    status_breakdown: Dict[str, int]
    usage_trend: List[Dict[str, Any]]


class SystemPerformanceResponse(BaseModel):
    """Schema for system performance response."""

    system_status: str
    total_reports: int
    active_reports: int
    executions_24h: int
    success_rate_24h: float
    average_execution_time: float
    peak_usage_hours: List[int]


class RealtimeDataResponse(BaseModel):
    """Schema for real-time data response."""

    status: str
    data: Optional[Any] = None
    execution_id: Optional[int] = None
    last_updated: Optional[str] = None
    age_minutes: Optional[float] = None
    is_fresh: Optional[bool] = None
    refresh_interval: Optional[int] = None
    message: Optional[str] = None
