"""Schemas for file upload and management."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response schema for file upload."""

    id: int
    filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    file_hash: str
    category: str
    upload_url: str
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class FileMetadataResponse(BaseModel):
    """Response schema for file metadata."""

    id: int
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    file_hash: str
    category: str
    description: Optional[str] = None
    uploaded_by: int
    organization_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    download_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class FileDeleteResponse(BaseModel):
    """Response schema for file deletion."""

    id: int
    message: str
    deleted_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class FileUploadRequest(BaseModel):
    """Request schema for file upload metadata."""

    category: str = Field(default="general", description="File category")
    description: Optional[str] = Field(None, description="File description")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )
    organization_id: Optional[int] = Field(None, description="Organization ID")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class FileListResponse(BaseModel):
    """Response schema for file listing."""

    files: list[FileMetadataResponse]
    total: int
    skip: int
    limit: int

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class FileStatisticsResponse(BaseModel):
    """Response schema for file statistics."""

    total_files: int
    total_size_bytes: int
    total_size_mb: float
    category_breakdown: Dict[str, Dict[str, int]]
    average_file_size: int

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class FileIntegrityResponse(BaseModel):
    """Response schema for file integrity check."""

    valid: bool
    stored_hash: Optional[str] = None
    current_hash: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class FileSearchRequest(BaseModel):
    """Request schema for file search."""

    filename: Optional[str] = Field(None, description="Search by filename")
    category: Optional[str] = Field(None, description="Filter by category")
    mime_type: Optional[str] = Field(None, description="Filter by MIME type")
    uploaded_by: Optional[int] = Field(None, description="Filter by uploader")
    organization_id: Optional[int] = Field(None, description="Filter by organization")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    min_size: Optional[int] = Field(None, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, description="Maximum file size in bytes")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class FileAccessLogResponse(BaseModel):
    """Response schema for file access log."""

    file_id: int
    download_count: int
    last_downloaded_at: Optional[datetime] = None
    last_downloaded_by: Optional[int] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True