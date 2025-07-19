"""File metadata model for secure file storage tracking."""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class FileMetadata(Base):
    """Model for tracking uploaded file metadata."""

    __tablename__ = "file_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # File identification
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # File properties
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 hash

    # Classification
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Ownership and organization
    uploaded_by: Mapped[int] = mapped_column(Integer, nullable=False)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Additional metadata
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default={}
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Security and validation
    virus_scan_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    virus_scan_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Download tracking
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_downloaded_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        """String representation of FileMetadata."""
        return (
            f"<FileMetadata(id={self.id}, filename='{self.original_filename}', "
            f"size={self.file_size})>"
        )

    @property
    def is_image(self) -> bool:
        """Check if file is an image."""
        return self.mime_type.startswith("image/")

    @property
    def is_document(self) -> bool:
        """Check if file is a document."""
        document_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument",
            "text/plain",
            "text/csv",
        ]
        return any(self.mime_type.startswith(doc_type) for doc_type in document_types)

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return round(self.file_size / (1024 * 1024), 2)

    def increment_download_count(self, downloaded_by: Optional[int] = None) -> None:
        """Increment download count and update last download info."""
        self.download_count += 1
        self.last_downloaded_at = datetime.utcnow()
        if downloaded_by:
            self.last_downloaded_by = downloaded_by
