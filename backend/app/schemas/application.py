"""Pydantic schemas for application management."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.workflow import ApplicationStatus, ApplicationType, ApprovalStatus


class ApplicationBase(BaseModel):
    """Base schema for application."""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Application title"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Application description"
    )
    application_type: ApplicationType = Field(..., description="Type of application")
    priority: str = Field(default="MEDIUM", description="Application priority")


class ApplicationCreate(ApplicationBase):
    """Schema for creating application."""

    organization_id: int = Field(..., gt=0, description="Organization ID")
    created_by: int = Field(
        ..., gt=0, description="User ID who created the application"
    )
    department_id: Optional[int] = Field(None, gt=0, description="Department ID")
    form_data: Optional[Dict[str, Any]] = Field(
        None, description="Application form data"
    )

    @field_validator("priority")
    def validate_priority(cls, v) -> dict:
        """Validate priority value."""
        valid_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v


class ApplicationUpdate(BaseModel):
    """Schema for updating application."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None)
    form_data: Optional[Dict[str, Any]] = Field(None)

    @field_validator("priority")
    def validate_priority(cls, v) -> dict:
        """Validate priority value."""
        if v is not None:
            valid_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of {valid_priorities}")
        return v


class ApplicationResponse(ApplicationBase):
    """Schema for application response."""

    id: int
    organization_id: int
    created_by: int
    department_id: Optional[int]
    status: ApplicationStatus
    form_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    is_deleted: bool = False

    class Config:
        from_attributes = True
        use_enum_values = True


class ApplicationListItem(BaseModel):
    """Schema for application list item."""

    id: int
    title: str
    status: ApplicationStatus
    application_type: ApplicationType
    created_by: int
    created_at: datetime
    priority: str

    class Config:
        from_attributes = True
        use_enum_values = True


class ApplicationListResponse(BaseModel):
    """Schema for paginated application list."""

    items: List[ApplicationListItem]
    total: int
    skip: int
    limit: int


class ApplicationSearchParams(BaseModel):
    """Schema for application search parameters."""

    organization_id: Optional[int] = Field(None, gt=0)
    status: Optional[ApplicationStatus] = None
    application_type: Optional[ApplicationType] = None
    created_by: Optional[int] = Field(None, gt=0)
    department_id: Optional[int] = Field(None, gt=0)
    priority: Optional[str] = None
    search: Optional[str] = Field(
        None, max_length=200, description="Search in title and description"
    )
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("priority")
    def validate_priority(cls, v) -> dict:
        """Validate priority value."""
        if v is not None:
            valid_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of {valid_priorities}")
        return v

    @field_validator("end_date")
    def validate_end_date(cls, v, values) -> dict:
        """Validate end_date is after start_date."""
        if (
            v is not None
            and "start_date" in values
            and values["start_date"] is not None
        ):
            if v <= values["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v


# Application Approval Schemas
class ApplicationApprovalBase(BaseModel):
    """Base schema for application approval."""

    status: ApprovalStatus = Field(..., description="Approval status")
    comments: Optional[str] = Field(
        None, max_length=1000, description="Approval comments"
    )


class ApplicationApprovalCreate(ApplicationApprovalBase):
    """Schema for creating application approval."""

    approver_id: int = Field(..., gt=0, description="Approver user ID")


class ApplicationApprovalUpdate(BaseModel):
    """Schema for updating application approval."""

    status: Optional[ApprovalStatus] = None
    comments: Optional[str] = Field(None, max_length=1000)


class ApplicationApprovalResponse(ApplicationApprovalBase):
    """Schema for application approval response."""

    id: int
    application_id: int
    approver_id: int
    created_at: datetime
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True
        use_enum_values = True


# Bulk Operations Schemas
class BulkApprovalRequest(BaseModel):
    """Schema for bulk approval request."""

    application_ids: List[int] = Field(..., min_items=1, max_items=100)
    comments: Optional[str] = Field(None, max_length=1000)

    @field_validator("application_ids")
    def validate_application_ids(cls, v) -> dict:
        """Validate application IDs are positive integers."""
        for app_id in v:
            if app_id <= 0:
                raise ValueError("All application IDs must be positive integers")
        return v


class BulkRejectionRequest(BaseModel):
    """Schema for bulk rejection request."""

    application_ids: List[int] = Field(..., min_items=1, max_items=100)
    reason: str = Field(
        ..., min_length=1, max_length=1000, description="Rejection reason"
    )

    @field_validator("application_ids")
    def validate_application_ids(cls, v) -> dict:
        """Validate application IDs are positive integers."""
        for app_id in v:
            if app_id <= 0:
                raise ValueError("All application IDs must be positive integers")
        return v


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response."""

    processed_count: int
    failed_ids: List[int]
    total_requested: int
    success_rate: float

    @field_validator("success_rate")
    def calculate_success_rate(cls, v) -> float:
        """Calculate success rate."""
        return round(v, 2) if v else 0.0


# Analytics Schemas
class ApplicationAnalyticsResponse(BaseModel):
    """Schema for application analytics response."""

    total_applications: int
    status_breakdown: Dict[str, int]
    type_breakdown: Dict[str, int]
    average_processing_time_hours: Optional[float]
    period_summary: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "total_applications": 150,
                "status_breakdown": {
                    "DRAFT": 20,
                    "PENDING_APPROVAL": 30,
                    "APPROVED": 80,
                    "REJECTED": 15,
                    "CANCELLED": 5,
                },
                "type_breakdown": {
                    "LEAVE_REQUEST": 60,
                    "EXPENSE_REPORT": 40,
                    "PURCHASE_REQUEST": 30,
                    "OTHER": 20,
                },
                "average_processing_time_hours": 24.5,
                "period_summary": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                },
            }
        }


class ApprovalPerformanceResponse(BaseModel):
    """Schema for approval performance metrics."""

    total_approvals: int
    approved_count: int
    rejected_count: int
    pending_count: int
    approval_rate: float
    average_response_time_hours: Optional[float]
    approver_metrics: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "total_approvals": 100,
                "approved_count": 75,
                "rejected_count": 20,
                "pending_count": 5,
                "approval_rate": 75.0,
                "average_response_time_hours": 18.5,
                "approver_metrics": [
                    {
                        "approver_id": 1,
                        "approver_name": "John Doe",
                        "total_processed": 30,
                        "approval_rate": 80.0,
                    }
                ],
            }
        }


# Template Schemas
class ApplicationFormField(BaseModel):
    """Schema for application form field."""

    name: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., description="Field type (text, number, date, etc.)")
    required: bool = Field(default=False)
    validation: Optional[Dict[str, Any]] = Field(
        None, description="Field validation rules"
    )
    options: Optional[List[str]] = Field(None, description="Options for select fields")

    @field_validator("type")
    def validate_field_type(cls, v) -> dict:
        """Validate field type."""
        valid_types = [
            "text",
            "textarea",
            "number",
            "email",
            "date",
            "datetime",
            "select",
            "multiselect",
            "checkbox",
            "radio",
            "file",
        ]
        if v not in valid_types:
            raise ValueError(f"Field type must be one of {valid_types}")
        return v


class ApplicationTemplate(BaseModel):
    """Schema for application template."""

    id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    application_type: ApplicationType
    form_schema: List[ApplicationFormField]
    is_active: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class ApplicationTemplateCreate(BaseModel):
    """Schema for creating application template."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    application_type: ApplicationType
    form_schema: List[ApplicationFormField]
    organization_id: int = Field(..., gt=0)


class ApplicationTemplateUpdate(BaseModel):
    """Schema for updating application template."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    form_schema: Optional[List[ApplicationFormField]] = None
    is_active: Optional[bool] = None


# Notification Schemas
class NotificationRequest(BaseModel):
    """Schema for sending notifications."""

    message: str = Field(..., min_length=1, max_length=1000)
    recipients: List[int] = Field(..., min_items=1, max_items=50)
    notification_type: str = Field(default="INFO")

    @field_validator("recipients")
    def validate_recipients(cls, v) -> dict:
        """Validate recipient IDs are positive integers."""
        for recipient_id in v:
            if recipient_id <= 0:
                raise ValueError("All recipient IDs must be positive integers")
        return v

    @field_validator("notification_type")
    def validate_notification_type(cls, v) -> dict:
        """Validate notification type."""
        valid_types = ["INFO", "WARNING", "SUCCESS", "ERROR"]
        if v not in valid_types:
            raise ValueError(f"Notification type must be one of {valid_types}")
        return v


class ClarificationRequest(BaseModel):
    """Schema for clarification request."""

    message: str = Field(
        ..., min_length=1, max_length=1000, description="Clarification message"
    )
    priority: str = Field(default="MEDIUM", description="Urgency of clarification")

    @field_validator("priority")
    def validate_priority(cls, v) -> dict:
        """Validate priority value."""
        valid_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v


# Export Schemas
class ExportRequest(BaseModel):
    """Schema for export request."""

    format: str = Field(..., description="Export format (csv, excel, pdf)")
    organization_id: int = Field(..., gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[ApplicationStatus] = None
    application_type: Optional[ApplicationType] = None
    include_details: bool = Field(
        default=False, description="Include detailed information"
    )

    @field_validator("format")
    def validate_format(cls, v) -> dict:
        """Validate export format."""
        valid_formats = ["csv", "excel", "pdf"]
        if v not in valid_formats:
            raise ValueError(f"Format must be one of {valid_formats}")
        return v

    @field_validator("end_date")
    def validate_end_date(cls, v, values) -> dict:
        """Validate end_date is after start_date."""
        if (
            v is not None
            and "start_date" in values
            and values["start_date"] is not None
        ):
            if v <= values["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v


# Status and Type Response Schemas
class ApplicationTypeResponse(BaseModel):
    """Schema for application type response."""

    code: str
    name: str
    description: Optional[str]
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "code": "LEAVE_REQUEST",
                "name": "Leave Request",
                "description": "Request for time off from work",
                "is_active": True,
            }
        }


class ApplicationStatusResponse(BaseModel):
    """Schema for application status response."""

    code: str
    name: str
    description: Optional[str]
    is_terminal: bool = Field(description="Whether this is a final status")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "APPROVED",
                "name": "Approved",
                "description": "Application has been approved",
                "is_terminal": True,
            }
        }
