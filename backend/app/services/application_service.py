"""Application management service for WF-002 functionality."""

from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import Response
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.workflow import (
    Application,
    ApplicationApproval,
    ApplicationStatus,
    ApprovalStatus,
)
from app.schemas.application import (
    ApplicationApprovalCreate,
    ApplicationCreate,
    ApplicationSearchParams,
    ApplicationUpdate,
)


class ApplicationService:
    """Service layer for application management."""

    def __init__(self, db: Session):
        self.db = db

    async def create_application(
        self, application_data: ApplicationCreate
    ) -> Dict[str, Any]:
        """Create a new application."""
        application = Application(
            title=application_data.title,
            description=application_data.description,
            application_type=application_data.application_type,
            organization_id=application_data.organization_id,
            created_by=application_data.created_by,
            department_id=application_data.department_id,
            priority=application_data.priority,
            form_data=application_data.form_data,
            status=ApplicationStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)

        return {
            "id": application.id,
            "title": application.title,
            "description": application.description,
            "status": application.status.value,
            "application_type": application.application_type.value,
            "organization_id": application.organization_id,
            "created_by": application.created_by,
            "created_at": application.created_at.isoformat(),
        }

    async def get_applications(
        self,
        search_params: ApplicationSearchParams,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get list of applications with filtering and pagination."""
        query = self.db.query(Application)

        # Apply filters
        if search_params.organization_id:
            query = query.filter(
                Application.organization_id == search_params.organization_id
            )

        if search_params.status:
            query = query.filter(Application.status == search_params.status)

        if search_params.application_type:
            query = query.filter(
                Application.application_type == search_params.application_type
            )

        if search_params.created_by:
            query = query.filter(Application.created_by == search_params.created_by)

        if search_params.search:
            query = query.filter(
                or_(
                    Application.title.ilike(f"%{search_params.search}%"),
                    Application.description.ilike(f"%{search_params.search}%"),
                )
            )

        if search_params.start_date:
            query = query.filter(Application.created_at >= search_params.start_date)

        if search_params.end_date:
            query = query.filter(Application.created_at <= search_params.end_date)

        # Get total count
        total = query.count()

        # Apply pagination
        applications = query.offset(skip).limit(limit).all()

        items = []
        for app in applications:
            items.append(
                {
                    "id": app.id,
                    "title": app.title,
                    "status": app.status.value,
                    "application_type": app.application_type.value,
                    "created_by": app.created_by,
                    "created_at": app.created_at.isoformat(),
                    "priority": app.priority,
                }
            )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_user_applications(
        self,
        user_id: int,
        status: Optional[str] = None,
        application_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get applications created by specific user."""
        query = self.db.query(Application).filter(Application.created_by == user_id)

        if status:
            query = query.filter(Application.status == status)

        if application_type:
            query = query.filter(Application.application_type == application_type)

        total = query.count()
        applications = query.offset(skip).limit(limit).all()

        items = []
        for app in applications:
            items.append(
                {
                    "id": app.id,
                    "title": app.title,
                    "status": app.status.value,
                    "application_type": app.application_type.value,
                    "created_at": app.created_at.isoformat(),
                    "priority": app.priority,
                }
            )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_pending_approvals(
        self,
        approver_id: int,
        application_type: Optional[str] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get applications pending approval by specific user."""
        query = (
            self.db.query(Application)
            .join(ApplicationApproval)
            .filter(
                and_(
                    ApplicationApproval.approver_id == approver_id,
                    ApplicationApproval.status == ApprovalStatus.PENDING,
                    Application.status == ApplicationStatus.PENDING_APPROVAL,
                )
            )
        )

        if application_type:
            query = query.filter(Application.application_type == application_type)

        if priority:
            query = query.filter(Application.priority == priority)

        total = query.count()
        applications = query.offset(skip).limit(limit).all()

        items = []
        for app in applications:
            items.append(
                {
                    "id": app.id,
                    "title": app.title,
                    "status": app.status.value,
                    "application_type": app.application_type.value,
                    "created_at": app.created_at.isoformat(),
                    "priority": app.priority,
                }
            )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_application(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get application by ID."""
        application = (
            self.db.query(Application).filter(Application.id == application_id).first()
        )

        if not application:
            return None

        return {
            "id": application.id,
            "title": application.title,
            "description": application.description,
            "status": application.status.value,
            "application_type": application.application_type.value,
            "organization_id": application.organization_id,
            "created_by": application.created_by,
            "department_id": application.department_id,
            "priority": application.priority,
            "form_data": application.form_data,
            "created_at": application.created_at.isoformat(),
            "updated_at": application.updated_at.isoformat(),
            "submitted_at": application.submitted_at.isoformat()
            if application.submitted_at
            else None,
            "approved_at": application.approved_at.isoformat()
            if application.approved_at
            else None,
        }

    async def update_application(
        self, application_id: int, application_data: ApplicationUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update application."""
        application = (
            self.db.query(Application).filter(Application.id == application_id).first()
        )

        if not application:
            return None

        # Only allow updates for draft applications
        if application.status != ApplicationStatus.DRAFT:
            raise HTTPException(
                status_code=400, detail="Only draft applications can be updated"
            )

        update_data = application_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(application, field, value)

        application.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(application)

        return await self.get_application(application_id)

    async def delete_application(self, application_id: int) -> bool:
        """Delete application (soft delete)."""
        application = (
            self.db.query(Application).filter(Application.id == application_id).first()
        )

        if not application:
            return False

        # Only allow deletion for draft applications
        if application.status != ApplicationStatus.DRAFT:
            raise HTTPException(
                status_code=400, detail="Only draft applications can be deleted"
            )

        application.is_deleted = True
        application.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    async def submit_application(
        self, application_id: int, background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Submit application for approval."""
        application = (
            self.db.query(Application).filter(Application.id == application_id).first()
        )

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        if application.status != ApplicationStatus.DRAFT:
            raise HTTPException(
                status_code=400, detail="Only draft applications can be submitted"
            )

        application.status = ApplicationStatus.PENDING_APPROVAL
        application.submitted_at = datetime.utcnow()
        application.updated_at = datetime.utcnow()
        self.db.commit()

        # Add background task for notifications
        background_tasks.add_task(self._send_submission_notifications, application_id)

        return {
            "message": "Application submitted successfully",
            "application_id": application_id,
        }

    async def cancel_application(
        self, application_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel application."""
        application = (
            self.db.query(Application).filter(Application.id == application_id).first()
        )

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        if application.status in [
            ApplicationStatus.APPROVED,
            ApplicationStatus.CANCELLED,
        ]:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel approved or already cancelled application",
            )

        application.status = ApplicationStatus.CANCELLED
        application.cancelled_at = datetime.utcnow()
        application.updated_at = datetime.utcnow()
        if reason:
            application.cancellation_reason = reason

        self.db.commit()

        return {
            "message": "Application cancelled successfully",
            "application_id": application_id,
        }

    async def resubmit_application(
        self, application_id: int, background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Resubmit rejected application."""
        application = (
            self.db.query(Application).filter(Application.id == application_id).first()
        )

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        if application.status != ApplicationStatus.REJECTED:
            raise HTTPException(
                status_code=400, detail="Only rejected applications can be resubmitted"
            )

        application.status = ApplicationStatus.PENDING_APPROVAL
        application.submitted_at = datetime.utcnow()
        application.updated_at = datetime.utcnow()
        self.db.commit()

        # Add background task for notifications
        background_tasks.add_task(self._send_resubmission_notifications, application_id)

        return {
            "message": "Application resubmitted successfully",
            "application_id": application_id,
        }

    async def create_approval(
        self,
        application_id: int,
        approval_data: ApplicationApprovalCreate,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """Create approval decision for application."""
        application = (
            self.db.query(Application).filter(Application.id == application_id).first()
        )

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        approval = ApplicationApproval(
            application_id=application_id,
            approver_id=approval_data.approver_id,
            status=approval_data.status,
            comments=approval_data.comments,
            approved_at=datetime.utcnow()
            if approval_data.status == ApprovalStatus.APPROVED
            else None,
            created_at=datetime.utcnow(),
        )

        self.db.add(approval)

        # Update application status based on approval
        if approval_data.status == ApprovalStatus.APPROVED:
            application.status = ApplicationStatus.APPROVED
            application.approved_at = datetime.utcnow()
        elif approval_data.status == ApprovalStatus.REJECTED:
            application.status = ApplicationStatus.REJECTED

        application.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(approval)

        # Add background task for notifications
        background_tasks.add_task(
            self._send_approval_notifications,
            application_id,
            approval_data.status.value,
        )

        return {
            "id": approval.id,
            "application_id": approval.application_id,
            "approver_id": approval.approver_id,
            "status": approval.status.value,
            "comments": approval.comments,
            "created_at": approval.created_at.isoformat(),
        }

    async def get_application_approvals(
        self, application_id: int
    ) -> List[Dict[str, Any]]:
        """Get approval history for application."""
        approvals = (
            self.db.query(ApplicationApproval)
            .filter(ApplicationApproval.application_id == application_id)
            .order_by(ApplicationApproval.created_at.desc())
            .all()
        )

        return [
            {
                "id": approval.id,
                "approver_id": approval.approver_id,
                "status": approval.status.value,
                "comments": approval.comments,
                "created_at": approval.created_at.isoformat(),
                "approved_at": approval.approved_at.isoformat()
                if approval.approved_at
                else None,
            }
            for approval in approvals
        ]

    async def quick_approve(
        self,
        application_id: int,
        comments: Optional[str],
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """Quick approval endpoint."""
        approval_data = ApplicationApprovalCreate(
            approver_id=1,  # This should come from authentication context
            status=ApprovalStatus.APPROVED,
            comments=comments,
        )
        return await self.create_approval(
            application_id, approval_data, background_tasks
        )

    async def quick_reject(
        self,
        application_id: int,
        reason: str,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """Quick rejection endpoint."""
        approval_data = ApplicationApprovalCreate(
            approver_id=1,  # This should come from authentication context
            status=ApprovalStatus.REJECTED,
            comments=reason,
        )
        return await self.create_approval(
            application_id, approval_data, background_tasks
        )

    async def request_clarification(
        self,
        application_id: int,
        message: str,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """Request clarification on application."""
        application = (
            self.db.query(Application).filter(Application.id == application_id).first()
        )

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        application.status = ApplicationStatus.PENDING_CLARIFICATION
        application.updated_at = datetime.utcnow()
        self.db.commit()

        # Add background task for notifications
        background_tasks.add_task(
            self._send_clarification_request, application_id, message
        )

        return {"message": "Clarification requested", "application_id": application_id}

    async def bulk_approve(
        self,
        application_ids: List[int],
        comments: Optional[str],
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """Bulk approve multiple applications."""
        approved_count = 0
        failed_ids = []

        for app_id in application_ids:
            try:
                await self.quick_approve(app_id, comments, background_tasks)
                approved_count += 1
            except Exception:
                failed_ids.append(app_id)

        return {
            "approved_count": approved_count,
            "failed_ids": failed_ids,
            "total_processed": len(application_ids),
        }

    async def bulk_reject(
        self,
        application_ids: List[int],
        reason: str,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """Bulk reject multiple applications."""
        rejected_count = 0
        failed_ids = []

        for app_id in application_ids:
            try:
                await self.quick_reject(app_id, reason, background_tasks)
                rejected_count += 1
            except Exception:
                failed_ids.append(app_id)

        return {
            "rejected_count": rejected_count,
            "failed_ids": failed_ids,
            "total_processed": len(application_ids),
        }

    async def get_application_analytics(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        application_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get application analytics summary."""
        query = self.db.query(Application).filter(
            Application.organization_id == organization_id
        )

        if start_date:
            query = query.filter(Application.created_at >= start_date)
        if end_date:
            query = query.filter(Application.created_at <= end_date)
        if application_type:
            query = query.filter(Application.application_type == application_type)

        # Get status breakdown
        status_counts = (
            query.with_entities(Application.status, func.count(Application.id))
            .group_by(Application.status)
            .all()
        )

        # Get type breakdown
        type_counts = (
            query.with_entities(
                Application.application_type, func.count(Application.id)
            )
            .group_by(Application.application_type)
            .all()
        )

        # Calculate average processing time
        approved_apps = query.filter(
            Application.status == ApplicationStatus.APPROVED
        ).all()
        avg_processing_time = None
        if approved_apps:
            processing_times = [
                (app.approved_at - app.submitted_at).total_seconds() / 3600
                for app in approved_apps
                if app.approved_at and app.submitted_at
            ]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)

        return {
            "total_applications": query.count(),
            "status_breakdown": {
                status.value: count for status, count in status_counts
            },
            "type_breakdown": {
                app_type.value: count for app_type, count in type_counts
            },
            "average_processing_time_hours": avg_processing_time,
        }

    async def get_approval_performance(
        self,
        organization_id: int,
        approver_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get approval performance metrics."""
        query = (
            self.db.query(ApplicationApproval)
            .join(Application)
            .filter(Application.organization_id == organization_id)
        )

        if approver_id:
            query = query.filter(ApplicationApproval.approver_id == approver_id)
        if start_date:
            query = query.filter(ApplicationApproval.created_at >= start_date)
        if end_date:
            query = query.filter(ApplicationApproval.created_at <= end_date)

        approvals = query.all()

        # Calculate metrics
        total_approvals = len(approvals)
        approved_count = len(
            [a for a in approvals if a.status == ApprovalStatus.APPROVED]
        )
        rejected_count = len(
            [a for a in approvals if a.status == ApprovalStatus.REJECTED]
        )

        approval_rate = (
            (approved_count / total_approvals * 100) if total_approvals > 0 else 0
        )

        return {
            "total_approvals": total_approvals,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "approval_rate": approval_rate,
        }

    async def get_application_templates(
        self, application_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available application templates."""
        # This would typically come from a database table or configuration
        templates = [
            {
                "id": 1,
                "name": "Leave Request Template",
                "application_type": "LEAVE_REQUEST",
                "form_schema": {
                    "fields": [
                        {"name": "start_date", "type": "date", "required": True},
                        {"name": "end_date", "type": "date", "required": True},
                        {"name": "reason", "type": "textarea", "required": True},
                    ]
                },
            },
            {
                "id": 2,
                "name": "Expense Report Template",
                "application_type": "EXPENSE_REPORT",
                "form_schema": {
                    "fields": [
                        {"name": "amount", "type": "number", "required": True},
                        {"name": "description", "type": "text", "required": True},
                        {"name": "receipt", "type": "file", "required": True},
                    ]
                },
            },
        ]

        if application_type:
            templates = [
                t for t in templates if t["application_type"] == application_type
            ]

        return templates

    async def get_application_types(self) -> List[Dict[str, Any]]:
        """Get available application types."""
        return [
            {"code": "LEAVE_REQUEST", "name": "Leave Request"},
            {"code": "EXPENSE_REPORT", "name": "Expense Report"},
            {"code": "PURCHASE_REQUEST", "name": "Purchase Request"},
            {"code": "TRAVEL_REQUEST", "name": "Travel Request"},
            {"code": "OTHER", "name": "Other"},
        ]

    async def send_notification(
        self,
        application_id: int,
        message: str,
        recipients: List[int],
        background_tasks: BackgroundTasks,
    ) -> None:
        """Send notification about application."""
        background_tasks.add_task(
            self._send_custom_notification, application_id, message, recipients
        )

    async def send_approval_reminders(
        self, background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Send reminders for pending approvals."""
        # Get applications pending approval for more than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        pending_apps = (
            self.db.query(Application)
            .filter(
                and_(
                    Application.status == ApplicationStatus.PENDING_APPROVAL,
                    Application.submitted_at <= cutoff_time,
                )
            )
            .all()
        )

        reminder_count = len(pending_apps)

        for app in pending_apps:
            background_tasks.add_task(self._send_approval_reminder, app.id)

        return {"reminders_sent": reminder_count}

    async def export_applications_csv(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> Response:
        """Export applications to CSV."""
        query = self.db.query(Application).filter(
            Application.organization_id == organization_id
        )

        if start_date:
            query = query.filter(Application.created_at >= start_date)
        if end_date:
            query = query.filter(Application.created_at <= end_date)
        if status:
            query = query.filter(Application.status == status)

        applications = query.all()

        # Convert to DataFrame
        data = []
        for app in applications:
            data.append(
                {
                    "ID": app.id,
                    "Title": app.title,
                    "Type": app.application_type.value,
                    "Status": app.status.value,
                    "Created By": app.created_by,
                    "Created At": app.created_at.isoformat(),
                    "Priority": app.priority,
                }
            )

        df = pd.DataFrame(data)

        # Return CSV response (implementation depends on framework)
        from io import StringIO

        from fastapi.responses import Response

        output = StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=applications.csv"},
        )

    async def export_applications_excel(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> Response:
        """Export applications to Excel."""
        query = self.db.query(Application).filter(
            Application.organization_id == organization_id
        )

        if start_date:
            query = query.filter(Application.created_at >= start_date)
        if end_date:
            query = query.filter(Application.created_at <= end_date)
        if status:
            query = query.filter(Application.status == status)

        applications = query.all()

        # Convert to DataFrame
        data = []
        for app in applications:
            data.append(
                {
                    "ID": app.id,
                    "Title": app.title,
                    "Type": app.application_type.value,
                    "Status": app.status.value,
                    "Created By": app.created_by,
                    "Created At": app.created_at.isoformat(),
                    "Priority": app.priority,
                }
            )

        df = pd.DataFrame(data)

        # Return Excel response
        from io import BytesIO

        from fastapi.responses import Response

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Applications", index=False)

        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=applications.xlsx"},
        )

    # Background task methods
    async def _send_submission_notifications(self, application_id: int) -> None:
        """Send notifications when application is submitted."""
        # Implementation for sending notifications
        pass

    async def _send_resubmission_notifications(self, application_id: int) -> None:
        """Send notifications when application is resubmitted."""
        # Implementation for sending notifications
        pass

    async def _send_approval_notifications(
        self, application_id: int, status: str
    ) -> None:
        """Send notifications when application is approved/rejected."""
        # Implementation for sending notifications
        pass

    async def _send_clarification_request(
        self, application_id: int, message: str
    ) -> None:
        """Send clarification request notification."""
        # Implementation for sending notifications
        pass

    async def _send_custom_notification(
        self, application_id: int, message: str, recipients: List[int]
    ) -> None:
        """Send custom notification."""
        # Implementation for sending notifications
        pass

    async def _send_approval_reminder(self, application_id: int) -> None:
        """Send approval reminder notification."""
        # Implementation for sending notifications
        pass
