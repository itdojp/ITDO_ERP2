"""Data export/import API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.data_export import (
    BulkExportRequest,
    BulkExportResponse,
    DataPreviewRequest,
    DataPreviewResponse,
    ExportJobCreate,
    ExportJobResponse,
    ExportListResponse,
    ExportProgressResponse,
    ExportStatisticsResponse,
    ExportTemplateResponse,
    ImportJobCreate,
    ImportJobResponse,
    ImportValidationResponse,
)
from app.services.data_export import DataExportService

router = APIRouter()


@router.post("/export", response_model=ExportJobResponse)
async def create_export_job(
    export_data: ExportJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportJobResponse:
    """Create a new export job."""
    service = DataExportService(db)
    
    # Set organization if not specified
    if not export_data.organization_id:
        export_data.organization_id = current_user.organization_id
    
    # Check permissions for cross-organization access
    if (
        export_data.organization_id != current_user.organization_id
        and not current_user.is_superuser
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await service.create_export_job(
            export_data=export_data,
            created_by=current_user.id,
            background_tasks=background_tasks,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportJobResponse:
    """Get export job by ID."""
    service = DataExportService(db)
    
    job = await service.get_export_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    # TODO: Add permission check based on job ownership/organization
    
    return job


@router.get("/export/{job_id}/progress", response_model=ExportProgressResponse)
async def get_export_progress(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportProgressResponse:
    """Get export job progress."""
    service = DataExportService(db)
    
    progress = await service.get_export_progress(job_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    return progress


@router.get("/export/{job_id}/download")
async def download_export(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Download completed export file."""
    service = DataExportService(db)
    
    result = await service.download_export(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Export file not found or not ready")
    
    content, filename, mime_type = result
    
    return StreamingResponse(
        iter([content]),
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(content)),
        },
    )


@router.get("/export", response_model=ExportListResponse)
async def list_export_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    entity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportListResponse:
    """List export jobs with filtering."""
    # This is a placeholder implementation
    # In practice, this would query the database with filters
    
    return ExportListResponse(
        jobs=[],
        total=0,
        skip=skip,
        limit=limit,
    )


@router.post("/export/bulk", response_model=BulkExportResponse)
async def create_bulk_export(
    bulk_request: BulkExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BulkExportResponse:
    """Create multiple export jobs for different entity types."""
    service = DataExportService(db)
    
    job_ids = []
    
    for entity_type in bulk_request.entity_types:
        export_data = ExportJobCreate(
            entity_type=entity_type,
            format=bulk_request.format,
            filters=bulk_request.filters,
            organization_id=bulk_request.organization_id or current_user.organization_id,
        )
        
        try:
            job = await service.create_export_job(
                export_data=export_data,
                created_by=current_user.id,
                background_tasks=background_tasks,
            )
            job_ids.append(job.id)
        except Exception:
            # Continue with other exports even if one fails
            continue
    
    return BulkExportResponse(
        job_ids=job_ids,
        total_jobs=len(job_ids),
        message=f"Created {len(job_ids)} export jobs",
    )


@router.post("/preview", response_model=DataPreviewResponse)
async def preview_export_data(
    preview_request: DataPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataPreviewResponse:
    """Preview data before export."""
    # This is a placeholder implementation
    # In practice, this would query the actual data
    
    return DataPreviewResponse(
        entity_type=preview_request.entity_type,
        total_rows=100,
        preview_rows=10,
        columns=["id", "name", "created_at"],
        sample_data=[
            {"id": 1, "name": "Sample 1", "created_at": "2024-01-01T00:00:00Z"},
            {"id": 2, "name": "Sample 2", "created_at": "2024-01-02T00:00:00Z"},
        ],
        filters_applied=preview_request.filters or {},
    )


@router.get("/templates", response_model=List[ExportTemplateResponse])
async def get_export_templates(
    current_user: User = Depends(get_current_user),
) -> List[ExportTemplateResponse]:
    """Get available export templates."""
    templates = [
        ExportTemplateResponse(
            entity_type="users",
            name="User Export",
            description="Export user data with basic information",
            supported_formats=["csv", "excel", "pdf"],
            default_columns=["id", "email", "first_name", "last_name", "created_at"],
            available_filters=[
                {"field": "is_active", "type": "boolean", "description": "Active users only"},
                {"field": "organization_id", "type": "integer", "description": "Filter by organization"},
            ],
        ),
        ExportTemplateResponse(
            entity_type="organizations",
            name="Organization Export",
            description="Export organization data",
            supported_formats=["csv", "excel", "json"],
            default_columns=["id", "name", "code", "created_at"],
            available_filters=[
                {"field": "is_active", "type": "boolean", "description": "Active organizations only"},
            ],
        ),
        ExportTemplateResponse(
            entity_type="roles",
            name="Role Export",
            description="Export role and permission data",
            supported_formats=["csv", "excel"],
            default_columns=["id", "code", "name", "role_type", "is_system"],
            available_filters=[
                {"field": "role_type", "type": "string", "description": "Filter by role type"},
                {"field": "is_active", "type": "boolean", "description": "Active roles only"},
            ],
        ),
    ]
    
    return templates


@router.get("/statistics", response_model=ExportStatisticsResponse)
async def get_export_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportStatisticsResponse:
    """Get export statistics."""
    # This is a placeholder implementation
    return ExportStatisticsResponse(
        total_exports=150,
        exports_by_format={"csv": 80, "excel": 50, "pdf": 15, "json": 5},
        exports_by_entity={"users": 60, "organizations": 40, "roles": 30, "others": 20},
        recent_exports=[],
        average_export_time=45.5,
        largest_export_size=1024000,
    )


# Import endpoints

@router.post("/import/validate", response_model=ImportValidationResponse)
async def validate_import_file(
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportValidationResponse:
    """Validate import file before processing."""
    service = DataExportService(db)
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Determine file format from filename
    file_extension = file.filename.split(".")[-1].lower()
    format_map = {"csv": "csv", "xlsx": "excel", "xls": "excel", "json": "json"}
    
    file_format = format_map.get(file_extension)
    if not file_format:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    # Read file content
    content = await file.read()
    
    try:
        result = await service.validate_import_data(
            entity_type=entity_type,
            file_content=content,
            file_format=file_format,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import", response_model=ImportJobResponse)
async def create_import_job(
    import_data: ImportJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportJobResponse:
    """Create a new import job."""
    service = DataExportService(db)
    
    try:
        result = await service.import_data(
            import_data=import_data,
            created_by=current_user.id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/formats")
async def get_supported_formats() -> Dict[str, Any]:
    """Get supported export/import formats."""
    return {
        "export_formats": [
            {
                "format": "csv",
                "name": "CSV",
                "description": "Comma-separated values",
                "mime_type": "text/csv",
                "supports_large_datasets": True,
            },
            {
                "format": "excel",
                "name": "Excel",
                "description": "Microsoft Excel spreadsheet",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "supports_large_datasets": True,
            },
            {
                "format": "pdf",
                "name": "PDF",
                "description": "Portable Document Format (limited rows)",
                "mime_type": "application/pdf",
                "supports_large_datasets": False,
                "max_rows": 50,
            },
            {
                "format": "json",
                "name": "JSON",
                "description": "JavaScript Object Notation",
                "mime_type": "application/json",
                "supports_large_datasets": True,
            },
        ],
        "import_formats": [
            {
                "format": "csv",
                "name": "CSV",
                "description": "Comma-separated values",
                "mime_type": "text/csv",
            },
            {
                "format": "excel",
                "name": "Excel",
                "description": "Microsoft Excel spreadsheet",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
            {
                "format": "json",
                "name": "JSON",
                "description": "JavaScript Object Notation",
                "mime_type": "application/json",
            },
        ],
    }


@router.get("/health")
async def export_service_health() -> Dict[str, Any]:
    """Check export service health status."""
    return {
        "status": "healthy",
        "service": "data_export",
        "version": "1.0.0",
        "features": [
            "csv_export",
            "excel_export",
            "pdf_export",
            "json_export",
            "bulk_export",
            "background_processing",
            "data_validation",
            "import_support",
        ],
    }