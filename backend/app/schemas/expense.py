"""Expense management schemas for Phase 4 financial management API."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class ExpenseBase(BaseModel):
    """Base schema for expenses."""

    title: str = Field(..., max_length=200, description="Expense title")
    description: Optional[str] = Field(None, description="Expense description")
    expense_category_id: int = Field(..., description="Expense category ID")
    project_id: Optional[int] = Field(None, description="Project ID")
    expense_date: date = Field(..., description="Expense date")
    amount: Decimal = Field(..., gt=0, description="Expense amount")
    currency: str = Field("JPY", max_length=3, description="Currency code")
    payment_method: str = Field(..., description="Payment method")
    receipt_number: Optional[str] = Field(
        None, max_length=100, description="Receipt number"
    )
    vendor_name: Optional[str] = Field(None, max_length=200, description="Vendor name")

    @field_validator("payment_method")
    def validate_payment_method(cls, v) -> dict:
        allowed_methods = ["cash", "credit_card", "bank_transfer", "check", "other"]
        if v not in allowed_methods:
            raise ValueError(
                f"Payment method must be one of: {', '.join(allowed_methods)}"
            )
        return v


class ExpenseCreate(ExpenseBase):
    """Schema for creating expenses."""

    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating expenses."""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    expense_category_id: Optional[int] = Field(None)
    project_id: Optional[int] = Field(None)
    expense_date: Optional[date] = Field(None)
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    payment_method: Optional[str] = Field(None)
    receipt_number: Optional[str] = Field(None, max_length=100)
    vendor_name: Optional[str] = Field(None, max_length=200)


class ExpenseResponse(ExpenseBase, BaseResponse):
    """Schema for expense responses."""

    id: int
    expense_number: str
    organization_id: int
    employee_id: int
    status: str
    receipt_url: Optional[str]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejected_reason: Optional[str]
    paid_at: Optional[datetime]
    paid_by: Optional[int]

    # Computed properties
    is_pending_approval: bool
    is_approved: bool
    is_paid: bool

    class Config:
        from_attributes = True


class ExpenseApprovalFlowBase(BaseModel):
    """Base schema for expense approval flows."""

    approver_id: int = Field(..., description="Approver user ID")
    approval_level: int = Field(..., description="Approval level")
    is_required: bool = Field(True, description="Required approval")
    comments: Optional[str] = Field(None, description="Approval comments")


class ExpenseApprovalFlowCreate(ExpenseApprovalFlowBase):
    """Schema for creating expense approval flows."""

    pass


class ExpenseApprovalFlowResponse(ExpenseApprovalFlowBase, BaseResponse):
    """Schema for expense approval flow responses."""

    id: int
    expense_id: int
    approved_at: Optional[datetime]
    is_approved: bool

    class Config:
        from_attributes = True


class ExpenseApprovalAction(BaseModel):
    """Schema for expense approval actions."""

    action: str = Field(..., description="Action: approve, reject")
    comments: Optional[str] = Field(None, description="Approval comments")

    @field_validator("action")
    def validate_action(cls, v) -> dict:
        allowed_actions = ["approve", "reject"]
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v


class ExpenseSubmission(BaseModel):
    """Schema for expense submission."""

    comments: Optional[str] = Field(None, description="Submission comments")


class ExpenseListResponse(BaseModel):
    """Schema for expense list responses."""

    items: List[ExpenseResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class ExpenseSearch(BaseModel):
    """Schema for expense search filters."""

    employee_id: Optional[int] = Field(None, description="Employee ID filter")
    project_id: Optional[int] = Field(None, description="Project ID filter")
    expense_category_id: Optional[int] = Field(None, description="Category ID filter")
    status: Optional[str] = Field(None, description="Status filter")
    date_from: Optional[date] = Field(None, description="Date from filter")
    date_to: Optional[date] = Field(None, description="Date to filter")
    amount_min: Optional[Decimal] = Field(None, description="Minimum amount filter")
    amount_max: Optional[Decimal] = Field(None, description="Maximum amount filter")
    search_text: Optional[str] = Field(
        None, description="Text search in title/description"
    )


class ExpenseSummary(BaseModel):
    """Schema for expense summary analytics."""

    total_expenses: int
    total_amount: Decimal
    pending_approval_count: int
    pending_approval_amount: Decimal
    approved_count: int
    approved_amount: Decimal
    rejected_count: int
    rejected_amount: Decimal
    paid_count: int
    paid_amount: Decimal

    # Category breakdown
    by_category: List[dict] = Field(
        default_factory=list, description="Amount by category"
    )
    by_month: List[dict] = Field(default_factory=list, description="Amount by month")
    by_employee: List[dict] = Field(
        default_factory=list, description="Amount by employee"
    )


class ReceiptUpload(BaseModel):
    """Schema for receipt upload."""

    file_name: str = Field(..., description="Original file name")
    content_type: str = Field(..., description="File content type")
    file_size: int = Field(..., description="File size in bytes")


class ReceiptUploadResponse(BaseModel):
    """Schema for receipt upload response."""

    receipt_url: str = Field(..., description="Receipt file URL")
    upload_id: str = Field(..., description="Upload identifier")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
