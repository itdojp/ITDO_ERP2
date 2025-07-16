"""Application management API endpoints for WF-002 functionality."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.application import (
    ApplicationApprovalCreate,
    ApplicationApprovalResponse,
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationSearchParams,
    ApplicationUpdate,
)
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application_data: ApplicationCreate, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new application."""
    service = ApplicationService(db)
    application = await service.create_application(application_data)
    return application


@router.get("/", response_model=ApplicationListResponse)
async def get_applications(
    search_params: ApplicationSearchParams = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get list of applications with filtering and pagination."""
    service = ApplicationService(db)
    result = await service.get_applications(
        search_params=search_params, skip=skip, limit=limit
    )
    return result


@router.get("/my-applications", response_model=ApplicationListResponse)
async def get_my_applications(
    user_id: int,
    status: Optional[str] = Query(None),
    application_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get applications created by current user."""
    service = ApplicationService(db)
    result = await service.get_user_applications(
        user_id=user_id,
        status=status,
        application_type=application_type,
        skip=skip,
        limit=limit,
    )
    return result


@router.get("/pending-approvals", response_model=ApplicationListResponse)
async def get_pending_approvals(
    approver_id: int,
    application_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get applications pending approval by current user."""
    service = ApplicationService(db)
    result = await service.get_pending_approvals(
        approver_id=approver_id,
        application_type=application_type,
        priority=priority,
        skip=skip,
        limit=limit,
    )
    return result


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get application by ID."""
    service = ApplicationService(db)
    application = await service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    application_data: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Update application."""
    service = ApplicationService(db)
    application = await service.update_application(application_id, application_data)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.delete("/{application_id}")
async def delete_application(
    application_id: int, db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Delete application (soft delete)."""
    service = ApplicationService(db)
    success = await service.delete_application(application_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application deleted successfully"}


# Application Status Management
@router.post("/{application_id}/submit")
async def submit_application(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Submit application for approval."""
    service = ApplicationService(db)
    result = await service.submit_application(
        application_id=application_id, background_tasks=background_tasks
    )
    return result


@router.post("/{application_id}/cancel")
async def cancel_application(
    application_id: int, reason: Optional[str] = None, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Cancel application."""
    service = ApplicationService(db)
    result = await service.cancel_application(application_id, reason)
    return result


@router.post("/{application_id}/resubmit")
async def resubmit_application(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Resubmit rejected application."""
    service = ApplicationService(db)
    result = await service.resubmit_application(
        application_id=application_id, background_tasks=background_tasks
    )
    return result


# Approval Management
@router.post("/{application_id}/approvals", response_model=ApplicationApprovalResponse)
async def create_approval(
    application_id: int,
    approval_data: ApplicationApprovalCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create approval decision for application."""
    service = ApplicationService(db)
    approval = await service.create_approval(
        application_id=application_id,
        approval_data=approval_data,
        background_tasks=background_tasks,
    )
    return approval


@router.get(
    "/{application_id}/approvals", response_model=List[ApplicationApprovalResponse]
)
async def get_application_approvals(
    application_id: int, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get approval history for application."""
    service = ApplicationService(db)
    approvals = await service.get_application_approvals(application_id)
    return approvals


@router.post("/{application_id}/approve")
async def approve_application(
    application_id: int,
    comments: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Approve application (quick approval endpoint)."""
    service = ApplicationService(db)
    result = await service.quick_approve(
        application_id=application_id,
        comments=comments,
        background_tasks=background_tasks,
    )
    return result


@router.post("/{application_id}/reject")
async def reject_application(
    application_id: int,
    reason: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Reject application."""
    service = ApplicationService(db)
    result = await service.quick_reject(
        application_id=application_id, reason=reason, background_tasks=background_tasks
    )
    return result


@router.post("/{application_id}/request-clarification")
async def request_clarification(
    application_id: int,
    message: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Request clarification on application."""
    service = ApplicationService(db)
    result = await service.request_clarification(
        application_id=application_id,
        message=message,
        background_tasks=background_tasks,
    )
    return result


# Bulk Operations
@router.post("/bulk-approve")
async def bulk_approve_applications(
    application_ids: List[int],
    comments: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Bulk approve multiple applications."""
    service = ApplicationService(db)
    result = await service.bulk_approve(
        application_ids=application_ids,
        comments=comments,
        background_tasks=background_tasks,
    )
    return result


@router.post("/bulk-reject")
async def bulk_reject_applications(
    application_ids: List[int],
    reason: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Bulk reject multiple applications."""
    service = ApplicationService(db)
    result = await service.bulk_reject(
        application_ids=application_ids,
        reason=reason,
        background_tasks=background_tasks,
    )
    return result


# Application Analytics
@router.get("/analytics/summary")
async def get_application_analytics(
    organization_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    application_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get application analytics summary."""
    service = ApplicationService(db)
    analytics = await service.get_application_analytics(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        application_type=application_type,
    )
    return analytics


@router.get("/analytics/performance")
async def get_approval_performance(
    organization_id: int,
    approver_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get approval performance metrics."""
    service = ApplicationService(db)
    performance = await service.get_approval_performance(
        organization_id=organization_id,
        approver_id=approver_id,
        start_date=start_date,
        end_date=end_date,
    )
    return performance


# Application Templates
@router.get("/templates/")
async def get_application_templates(
    application_type: Optional[str] = Query(None), db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get available application templates."""
    service = ApplicationService(db)
    templates = await service.get_application_templates(application_type)
    return templates


@router.get("/types/")
async def get_application_types(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get available application types."""
    service = ApplicationService(db)
    types = await service.get_application_types()
    return types


# Notifications and Reminders
@router.post("/{application_id}/notify")
async def send_notification(
    application_id: int,
    message: str,
    recipients: List[int],
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Send notification about application."""
    service = ApplicationService(db)
    await service.send_notification(
        application_id=application_id,
        message=message,
        recipients=recipients,
        background_tasks=background_tasks,
    )
    return {"message": "Notification sent successfully"}


@router.post("/send-reminders")
async def send_approval_reminders(
    background_tasks: BackgroundTasks = BackgroundTasks(), db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Send reminders for pending approvals."""
    service = ApplicationService(db)
    result = await service.send_approval_reminders(background_tasks)
    return result


# Export and Reporting
@router.get("/export/csv")
async def export_applications_csv(
    organization_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export applications to CSV."""
    service = ApplicationService(db)
    csv_response = await service.export_applications_csv(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )
    return csv_response


@router.get("/export/excel")
async def export_applications_excel(
    organization_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export applications to Excel."""
    service = ApplicationService(db)
    excel_response = await service.export_applications_excel(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )
    return excel_response
