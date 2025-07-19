"""File upload API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.file_upload import (
    FileDeleteResponse,
    FileIntegrityResponse,
    FileListResponse,
    FileMetadataResponse,
    FileStatisticsResponse,
    FileUploadResponse,
)
from app.services.file_upload import FileUploadService

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(default="general"),
    description: Optional[str] = Form(default=None),
    organization_id: Optional[int] = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileUploadResponse:
    """Upload a file with metadata."""
    service = FileUploadService(db)
    
    # Parse metadata if provided
    metadata: Dict[str, Any] = {
        "uploaded_via": "api",
        "user_agent": "file_upload_api",
    }
    
    try:
        result = await service.upload_file(
            file=file,
            uploaded_by=current_user.id,
            organization_id=organization_id or current_user.organization_id,
            category=category,
            description=description,
            metadata=metadata,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files", response_model=FileListResponse)
async def list_files(
    organization_id: Optional[int] = None,
    category: Optional[str] = None,
    uploaded_by: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileListResponse:
    """List files with filtering."""
    service = FileUploadService(db)
    
    # Use current user's organization if not specified
    org_filter = organization_id or current_user.organization_id
    
    files = await service.list_files(
        organization_id=org_filter,
        category=category,
        uploaded_by=uploaded_by,
        skip=skip,
        limit=limit,
    )
    
    return FileListResponse(
        files=files,
        total=len(files),  # TODO: Implement proper count query
        skip=skip,
        limit=limit,
    )


@router.get("/files/{file_id}", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileMetadataResponse:
    """Get file metadata by ID."""
    service = FileUploadService(db)
    
    file_metadata = await service.get_file_metadata(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check access permissions (basic implementation)
    if (
        file_metadata.organization_id != current_user.organization_id
        and not current_user.is_superuser
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return file_metadata


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Download file content."""
    service = FileUploadService(db)
    
    # Check file metadata and permissions
    file_metadata = await service.get_file_metadata(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check access permissions
    if (
        file_metadata.organization_id != current_user.organization_id
        and not current_user.is_superuser
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get file content
    result = await service.get_file_content(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File content not found")
    
    content, filename, mime_type = result
    
    # TODO: Update download tracking
    
    return StreamingResponse(
        iter([content]),
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(content)),
        },
    )


@router.delete("/files/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileDeleteResponse:
    """Delete a file (soft delete)."""
    service = FileUploadService(db)
    
    # Check file metadata and permissions
    file_metadata = await service.get_file_metadata(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions (only uploader or admin can delete)
    if (
        file_metadata.uploaded_by != current_user.id
        and not current_user.is_superuser
        and not current_user.has_permission("file.delete")
    ):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        result = await service.delete_file(file_id, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics", response_model=FileStatisticsResponse)
async def get_file_statistics(
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileStatisticsResponse:
    """Get file upload statistics."""
    service = FileUploadService(db)
    
    # Use current user's organization if not specified
    org_filter = organization_id or current_user.organization_id
    
    # Check permissions for cross-organization access
    if organization_id and organization_id != current_user.organization_id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
    
    stats = await service.get_file_statistics(org_filter)
    
    return FileStatisticsResponse(**stats)


@router.get("/files/{file_id}/integrity", response_model=FileIntegrityResponse)
async def check_file_integrity(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileIntegrityResponse:
    """Check file integrity by validating hash."""
    service = FileUploadService(db)
    
    # Check file metadata and permissions
    file_metadata = await service.get_file_metadata(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check access permissions
    if (
        file_metadata.organization_id != current_user.organization_id
        and not current_user.is_superuser
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await service.validate_file_integrity(file_id)
    
    return FileIntegrityResponse(**result)


@router.post("/files/{file_id}/scan")
async def scan_file_for_viruses(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Scan file for viruses (placeholder endpoint)."""
    service = FileUploadService(db)
    
    # Check file metadata and permissions
    file_metadata = await service.get_file_metadata(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions (admin only for virus scanning)
    if not current_user.is_superuser and not current_user.has_permission("file.scan"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Placeholder implementation
    return {
        "file_id": file_id,
        "scan_status": "clean",
        "scanner": "placeholder",
        "scan_time": "2024-01-01T00:00:00Z",
        "message": "Virus scanning integration not yet implemented",
    }


@router.get("/categories")
async def get_file_categories(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, str]]:
    """Get available file categories."""
    return [
        {"id": "general", "name": "General Files", "description": "General purpose files"},
        {"id": "image", "name": "Images", "description": "Image files (JPEG, PNG, GIF, WebP)"},
        {"id": "document", "name": "Documents", "description": "Documents (PDF, Word, Excel, CSV)"},
        {"id": "archive", "name": "Archives", "description": "Archive files (ZIP, RAR, 7Z)"},
        {"id": "profile", "name": "Profile", "description": "User profile related files"},
        {"id": "attachment", "name": "Attachments", "description": "Email and message attachments"},
    ]


@router.get("/health")
async def file_service_health() -> Dict[str, Any]:
    """Check file service health status."""
    return {
        "status": "healthy",
        "service": "file_upload",
        "version": "1.0.0",
        "features": [
            "secure_upload",
            "metadata_tracking",
            "file_validation",
            "integrity_checking",
            "category_management",
        ],
    }