"""Export job model for tracking export operations."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class ExportStatus(str, Enum):
    """Export job status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportJob(Base):
    """Model for tracking export job operations."""

    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Export configuration
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # csv, excel, pdf, json
    filters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    columns: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=[])
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    
    # Job status and progress
    status: Mapped[ExportStatus] = mapped_column(String(20), nullable=False, default=ExportStatus.PENDING)
    progress_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rows_processed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # File output
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Ownership and organization
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Download tracking
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """String representation of ExportJob."""
        return f"<ExportJob(id={self.id}, entity='{self.entity_type}', format='{self.format}', status='{self.status}')>"

    @property
    def is_complete(self) -> bool:
        """Check if export job is complete."""
        return self.status == ExportStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if export job failed."""
        return self.status == ExportStatus.FAILED

    @property
    def is_running(self) -> bool:
        """Check if export job is currently running."""
        return self.status == ExportStatus.RUNNING

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def increment_download_count(self) -> None:
        """Increment download count and update last download time."""
        self.download_count += 1
        self.last_downloaded_at = datetime.utcnow()


class ImportStatus(str, Enum):
    """Import job status enumeration."""
    PENDING = "pending"
    VALIDATING = "validating"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportJob(Base):
    """Model for tracking import job operations."""

    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Import configuration
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_format: Mapped[str] = mapped_column(String(20), nullable=False)  # csv, excel, json
    source_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mapping_configuration: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    validation_rules: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    
    # Job status and progress
    status: Mapped[ImportStatus] = mapped_column(String(30), nullable=False, default=ImportStatus.PENDING)
    progress_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processed_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validation_errors: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=[])
    
    # Results
    results_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    
    # Ownership and organization
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """String representation of ImportJob."""
        return f"<ImportJob(id={self.id}, entity='{self.entity_type}', format='{self.source_format}', status='{self.status}')>"

    @property
    def is_complete(self) -> bool:
        """Check if import job is complete."""
        return self.status in [ImportStatus.COMPLETED, ImportStatus.COMPLETED_WITH_ERRORS]

    @property
    def is_failed(self) -> bool:
        """Check if import job failed."""
        return self.status == ImportStatus.FAILED

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if not self.total_rows or self.total_rows == 0:
            return 0.0
        
        success_count = self.success_rows or 0
        return (success_count / self.total_rows) * 100