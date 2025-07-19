"""Schemas for data export and import operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExportJobCreate(BaseModel):
    """Request schema for creating export job."""

    entity_type: str = Field(..., description="Type of entity to export")
    format: str = Field(..., description="Export format (csv, excel, pdf, json)")
    filters: Optional[Dict[str, Any]] = Field(
        default={}, description="Filters to apply"
    )
    columns: Optional[List[str]] = Field(default=[], description="Columns to include")
    organization_id: Optional[int] = Field(None, description="Organization ID filter")
    configuration: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional configuration"
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ExportJobResponse(BaseModel):
    """Response schema for export job."""

    id: int
    entity_type: str
    format: str
    status: str
    progress_percentage: int
    rows_processed: int
    total_rows: int
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ExportProgressResponse(BaseModel):
    """Response schema for export progress."""

    job_id: int
    status: str
    progress_percentage: int
    rows_processed: int
    total_rows: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ExportListResponse(BaseModel):
    """Response schema for export job listing."""

    jobs: List[ExportJobResponse]
    total: int
    skip: int
    limit: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ImportJobCreate(BaseModel):
    """Request schema for creating import job."""

    entity_type: str = Field(..., description="Type of entity to import")
    source_format: str = Field(..., description="Source file format")
    mapping_configuration: Optional[Dict[str, Any]] = Field(
        default={}, description="Column mapping"
    )
    validation_rules: Optional[Dict[str, Any]] = Field(
        default={}, description="Validation rules"
    )
    organization_id: Optional[int] = Field(None, description="Organization ID")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ImportJobResponse(BaseModel):
    """Response schema for import job."""

    id: int
    entity_type: str
    status: str
    total_rows: int
    processed_rows: int
    error_rows: int
    created_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ImportValidationResponse(BaseModel):
    """Response schema for import validation."""

    valid: bool
    total_rows: int
    valid_rows: int
    errors: List[str]
    error: Optional[str] = None
    sample_data: Optional[List[Dict[str, Any]]] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ExportTemplateResponse(BaseModel):
    """Response schema for export templates."""

    entity_type: str
    name: str
    description: str
    supported_formats: List[str]
    default_columns: List[str]
    available_filters: List[Dict[str, Any]]

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class BulkExportRequest(BaseModel):
    """Request schema for bulk export operations."""

    entity_types: List[str] = Field(..., description="List of entity types to export")
    format: str = Field(..., description="Export format for all entities")
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Common filters")
    organization_id: Optional[int] = Field(None, description="Organization ID filter")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class BulkExportResponse(BaseModel):
    """Response schema for bulk export operations."""

    job_ids: List[int]
    total_jobs: int
    archive_job_id: Optional[int] = None
    message: str

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ExportStatisticsResponse(BaseModel):
    """Response schema for export statistics."""

    total_exports: int
    exports_by_format: Dict[str, int]
    exports_by_entity: Dict[str, int]
    recent_exports: List[ExportJobResponse]
    average_export_time: float
    largest_export_size: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class DataPreviewRequest(BaseModel):
    """Request schema for data preview before export."""

    entity_type: str = Field(..., description="Entity type to preview")
    filters: Optional[Dict[str, Any]] = Field(
        default={}, description="Filters to apply"
    )
    limit: int = Field(default=10, description="Number of rows to preview")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class DataPreviewResponse(BaseModel):
    """Response schema for data preview."""

    entity_type: str
    total_rows: int
    preview_rows: int
    columns: List[str]
    sample_data: List[Dict[str, Any]]
    filters_applied: Dict[str, Any]

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ScheduledExportCreate(BaseModel):
    """Request schema for scheduled export."""

    name: str = Field(..., description="Name of the scheduled export")
    entity_type: str = Field(..., description="Entity type to export")
    format: str = Field(..., description="Export format")
    schedule_expression: str = Field(..., description="Cron expression for schedule")
    filters: Optional[Dict[str, Any]] = Field(
        default={}, description="Filters to apply"
    )
    columns: Optional[List[str]] = Field(default=[], description="Columns to include")
    email_recipients: Optional[List[str]] = Field(
        default=[], description="Email recipients"
    )
    is_active: bool = Field(default=True, description="Whether schedule is active")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ScheduledExportResponse(BaseModel):
    """Response schema for scheduled export."""

    id: int
    name: str
    entity_type: str
    format: str
    schedule_expression: str
    is_active: bool
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    created_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True
