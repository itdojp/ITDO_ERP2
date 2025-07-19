"""File upload service for secure file handling with validation."""

import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file_metadata import FileMetadata
from app.schemas.file_upload import (
    FileUploadResponse,
    FileMetadataResponse,
    FileDeleteResponse,
)


class FileUploadService:
    """Service for secure file upload and management operations."""

    # Allowed file types and their MIME types
    ALLOWED_MIME_TYPES = {
        "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
        "document": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain",
            "text/csv",
        ],
        "archive": ["application/zip", "application/x-rar-compressed", "application/x-7z-compressed"],
    }

    # Maximum file sizes by category (in bytes)
    MAX_FILE_SIZES = {
        "image": 10 * 1024 * 1024,      # 10MB
        "document": 50 * 1024 * 1024,   # 50MB
        "archive": 100 * 1024 * 1024,   # 100MB
    }

    def __init__(self, db: Session):
        """Initialize file upload service."""
        self.db = db
        self.upload_dir = Path(getattr(settings, "UPLOAD_DIRECTORY", "uploads"))
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file: UploadFile,
        uploaded_by: int,
        organization_id: Optional[int] = None,
        category: str = "general",
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileUploadResponse:
        """Upload a file with validation and metadata storage."""
        # Validate file
        await self._validate_file(file)

        # Generate unique filename
        file_extension = Path(file.filename or "").suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Determine file category
        file_category = self._determine_file_category(file.content_type or "")
        
        # Create storage path
        storage_path = self._create_storage_path(file_category, unique_filename)
        
        # Calculate file hash while reading
        file_hash = await self._save_file_with_hash(file, storage_path)
        
        # Create file metadata record
        file_metadata = FileMetadata(
            original_filename=file.filename or "unknown",
            stored_filename=unique_filename,
            file_path=str(storage_path),
            file_size=file.size or 0,
            mime_type=file.content_type or "application/octet-stream",
            file_hash=file_hash,
            category=category,
            description=description,
            uploaded_by=uploaded_by,
            organization_id=organization_id,
            extra_metadata=metadata or {},
            is_active=True,
        )

        self.db.add(file_metadata)
        self.db.commit()
        self.db.refresh(file_metadata)

        return FileUploadResponse(
            id=file_metadata.id,
            filename=file_metadata.original_filename,
            stored_filename=file_metadata.stored_filename,
            file_size=file_metadata.file_size,
            mime_type=file_metadata.mime_type,
            file_hash=file_metadata.file_hash,
            category=file_metadata.category,
            upload_url=f"/api/v1/files/{file_metadata.id}",
            created_at=file_metadata.created_at,
        )

    async def get_file_metadata(self, file_id: int) -> Optional[FileMetadataResponse]:
        """Get file metadata by ID."""
        file_metadata = (
            self.db.query(FileMetadata)
            .filter(FileMetadata.id == file_id, FileMetadata.is_active)
            .first()
        )

        if not file_metadata:
            return None

        return FileMetadataResponse(
            id=file_metadata.id,
            original_filename=file_metadata.original_filename,
            stored_filename=file_metadata.stored_filename,
            file_size=file_metadata.file_size,
            mime_type=file_metadata.mime_type,
            file_hash=file_metadata.file_hash,
            category=file_metadata.category,
            description=file_metadata.description,
            uploaded_by=file_metadata.uploaded_by,
            organization_id=file_metadata.organization_id,
            metadata=file_metadata.extra_metadata,
            download_url=f"/api/v1/files/{file_metadata.id}/download",
            created_at=file_metadata.created_at,
            updated_at=file_metadata.updated_at,
        )

    async def get_file_content(self, file_id: int) -> Optional[tuple[bytes, str, str]]:
        """Get file content for download."""
        file_metadata = (
            self.db.query(FileMetadata)
            .filter(FileMetadata.id == file_id, FileMetadata.is_active)
            .first()
        )

        if not file_metadata:
            return None

        file_path = Path(file_metadata.file_path)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            return (
                content,
                file_metadata.original_filename,
                file_metadata.mime_type,
            )
        except Exception:
            return None

    async def delete_file(self, file_id: int, deleted_by: int) -> FileDeleteResponse:
        """Soft delete a file."""
        file_metadata = (
            self.db.query(FileMetadata)
            .filter(FileMetadata.id == file_id, FileMetadata.is_active)
            .first()
        )

        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")

        # Soft delete in database
        file_metadata.is_active = False
        file_metadata.deleted_at = datetime.utcnow()
        file_metadata.deleted_by = deleted_by
        
        self.db.commit()

        return FileDeleteResponse(
            id=file_id,
            message="File deleted successfully",
            deleted_at=file_metadata.deleted_at,
        )

    async def list_files(
        self,
        organization_id: Optional[int] = None,
        category: Optional[str] = None,
        uploaded_by: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FileMetadataResponse]:
        """List files with filtering."""
        query = self.db.query(FileMetadata).filter(FileMetadata.is_active)

        if organization_id:
            query = query.filter(FileMetadata.organization_id == organization_id)

        if category:
            query = query.filter(FileMetadata.category == category)

        if uploaded_by:
            query = query.filter(FileMetadata.uploaded_by == uploaded_by)

        files = query.offset(skip).limit(limit).all()

        return [
            FileMetadataResponse(
                id=f.id,
                original_filename=f.original_filename,
                stored_filename=f.stored_filename,
                file_size=f.file_size,
                mime_type=f.mime_type,
                file_hash=f.file_hash,
                category=f.category,
                description=f.description,
                uploaded_by=f.uploaded_by,
                organization_id=f.organization_id,
                metadata=f.extra_metadata,
                download_url=f"/api/v1/files/{f.id}/download",
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            for f in files
        ]

    async def get_file_statistics(
        self, organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get file upload statistics."""
        query = self.db.query(FileMetadata).filter(FileMetadata.is_active)

        if organization_id:
            query = query.filter(FileMetadata.organization_id == organization_id)

        files = query.all()

        total_files = len(files)
        total_size = sum(f.file_size for f in files)
        
        # Calculate statistics by category
        category_stats = {}
        for f in files:
            if f.category not in category_stats:
                category_stats[f.category] = {"count": 0, "size": 0}
            category_stats[f.category]["count"] += 1
            category_stats[f.category]["size"] += f.file_size

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "category_breakdown": category_stats,
            "average_file_size": total_size // total_files if total_files > 0 else 0,
        }

    async def validate_file_integrity(self, file_id: int) -> Dict[str, Any]:
        """Validate file integrity by checking hash."""
        file_metadata = (
            self.db.query(FileMetadata)
            .filter(FileMetadata.id == file_id, FileMetadata.is_active)
            .first()
        )

        if not file_metadata:
            return {"valid": False, "error": "File not found"}

        file_path = Path(file_metadata.file_path)
        if not file_path.exists():
            return {"valid": False, "error": "File does not exist on disk"}

        try:
            # Calculate current hash
            current_hash = self._calculate_file_hash(file_path)
            
            # Compare with stored hash
            is_valid = current_hash == file_metadata.file_hash
            
            return {
                "valid": is_valid,
                "stored_hash": file_metadata.file_hash,
                "current_hash": current_hash,
                "file_path": str(file_path),
            }
        except Exception as e:
            return {"valid": False, "error": f"Hash calculation failed: {str(e)}"}

    # Private methods

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        # Check file size
        if file.size and file.size > max(self.MAX_FILE_SIZES.values()):
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {max(self.MAX_FILE_SIZES.values()) // (1024*1024)}MB"
            )

        # Check MIME type
        if file.content_type:
            file_category = self._determine_file_category(file.content_type)
            if file_category == "unknown":
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{file.content_type}' is not allowed"
                )

            # Check size limit for specific category
            max_size = self.MAX_FILE_SIZES.get(file_category, self.MAX_FILE_SIZES["document"])
            if file.size and file.size > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large for {file_category}. Maximum size is {max_size // (1024*1024)}MB"
                )

        # Check filename for security
        if any(char in file.filename for char in ["../", "..\\", "/", "\\"]):
            raise HTTPException(
                status_code=400,
                detail="Invalid filename - path traversal not allowed"
            )

    def _determine_file_category(self, mime_type: str) -> str:
        """Determine file category from MIME type."""
        for category, mime_types in self.ALLOWED_MIME_TYPES.items():
            if mime_type in mime_types:
                return category
        return "unknown"

    def _create_storage_path(self, category: str, filename: str) -> Path:
        """Create storage path for file."""
        # Create category subdirectory
        category_dir = self.upload_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Create date-based subdirectory
        date_dir = category_dir / datetime.utcnow().strftime("%Y/%m/%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        return date_dir / filename

    async def _save_file_with_hash(self, file: UploadFile, storage_path: Path) -> str:
        """Save file and calculate hash simultaneously."""
        hash_sha256 = hashlib.sha256()
        
        with open(storage_path, "wb") as f:
            # Reset file pointer
            await file.seek(0)
            
            # Read and write in chunks while calculating hash
            while chunk := await file.read(8192):  # 8KB chunks
                hash_sha256.update(chunk)
                f.write(chunk)
        
        return hash_sha256.hexdigest()

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()

    # Virus scanning integration point (placeholder)
    async def _scan_file_for_viruses(self, file_path: Path) -> Dict[str, Any]:
        """Scan file for viruses (integration point for external scanner)."""
        # Placeholder for virus scanning integration
        # In production, integrate with ClamAV, VirusTotal, or similar
        return {
            "clean": True,
            "scanner": "placeholder",
            "scan_time": datetime.utcnow().isoformat(),
        }

    # S3-compatible storage support (placeholder)
    async def _upload_to_s3(self, file_path: Path, s3_key: str) -> str:
        """Upload file to S3-compatible storage (placeholder)."""
        # Placeholder for S3 integration
        # In production, integrate with boto3 or similar
        return f"s3://bucket/{s3_key}"