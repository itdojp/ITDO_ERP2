"""Budget management schemas for Phase 4 financial management API."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.schemas.base import BaseResponse


class ExpenseCategoryBase(BaseModel):
    """Base schema for expense categories."""
    
    code: str = Field(..., max_length=50, description="Category code")
    name: str = Field(..., max_length=200, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    is_active: bool = Field(True, description="Active status")
    requires_receipt: bool = Field(True, description="Receipt required")
    approval_required: bool = Field(True, description="Approval required")
    approval_limit: Optional[Decimal] = Field(None, description="Approval limit")


class ExpenseCategoryCreate(ExpenseCategoryBase):
    """Schema for creating expense categories."""
    pass


class ExpenseCategoryUpdate(BaseModel):
    """Schema for updating expense categories."""
    
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    parent_id: Optional[int] = Field(None)
    is_active: Optional[bool] = Field(None)
    requires_receipt: Optional[bool] = Field(None)
    approval_required: Optional[bool] = Field(None)
    approval_limit: Optional[Decimal] = Field(None)


class ExpenseCategoryResponse(ExpenseCategoryBase, BaseResponse):
    """Schema for expense category responses."""
    
    id: int
    organization_id: int
    
    class Config:
        from_attributes = True


class BudgetItemBase(BaseModel):
    """Base schema for budget items."""

    name: str = Field(..., max_length=200, description="Budget item name")
    description: Optional[str] = Field(None, description="Budget item description")
    expense_category_id: int = Field(..., description="Expense category ID")
    quantity: Decimal = Field(Decimal("1.000"), ge=0, description="Quantity")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    unit_price: Decimal = Field(Decimal("0.00"), ge=0, description="Unit price")
    budgeted_amount: Decimal = Field(..., ge=0, description="Budgeted amount")
    sort_order: int = Field(0, description="Sort order")
    monthly_breakdown: Optional[str] = Field(None, description="Monthly breakdown (JSON)")


class BudgetItemCreate(BudgetItemBase):
    """Schema for creating budget items."""
    pass


class BudgetItemUpdate(BaseModel):
    """Schema for updating budget items."""

    name: Optional[str] = Field(None, max_length=200, description="Budget item name")
    description: Optional[str] = Field(None, description="Budget item description")
    expense_category_id: Optional[int] = Field(None, description="Expense category ID")
    quantity: Optional[Decimal] = Field(None, ge=0, description="Quantity")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Unit price")
    budgeted_amount: Optional[Decimal] = Field(None, ge=0, description="Budgeted amount")
    sort_order: Optional[int] = Field(None, description="Sort order")
    monthly_breakdown: Optional[str] = Field(None, description="Monthly breakdown (JSON)")


class BudgetItemResponse(BudgetItemBase, BaseResponse):
    """Schema for budget item responses."""

    id: int
    budget_id: int
    actual_amount: Decimal
    committed_amount: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    remaining_amount: Decimal
    utilization_percentage: Decimal
    is_over_budget: bool

    # Relationships
    expense_category: Optional[ExpenseCategoryResponse] = Field(None, description="Expense category details")

    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    """Base schema for budgets."""

    code: str = Field(..., max_length=50, description="Budget code")
    name: str = Field(..., max_length=200, description="Budget name")
    description: Optional[str] = Field(None, description="Budget description")
    budget_type: str = Field(..., description="Budget type: project/department/annual/quarterly/monthly")
    fiscal_year: int = Field(..., ge=2000, le=2100, description="Fiscal year")
    budget_period: str = Field("annual", description="Budget period: annual/quarterly/monthly")
    start_date: date = Field(..., description="Budget start date")
    end_date: date = Field(..., description="Budget end date")
    total_amount: Decimal = Field(..., ge=0, description="Total budget amount")
    currency: str = Field("JPY", max_length=3, description="Currency code")
    alert_threshold: Decimal = Field(Decimal("80.00"), ge=0, le=100, description="Alert threshold percentage")
    is_alert_enabled: bool = Field(True, description="Whether alerts are enabled")

    # Optional foreign keys
    project_id: Optional[int] = Field(None, description="Project ID for project budgets")
    department_id: Optional[int] = Field(None, description="Department ID for department budgets")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('budget_type')
    def validate_budget_type(cls, v):
        allowed_types = ['project', 'department', 'annual', 'quarterly', 'monthly']
        if v not in allowed_types:
            raise ValueError(f'Budget type must be one of: {", ".join(allowed_types)}')
        return v

    @validator('budget_period')
    def validate_budget_period(cls, v):
        allowed_periods = ['annual', 'quarterly', 'monthly']
        if v not in allowed_periods:
            raise ValueError(f'Budget period must be one of: {", ".join(allowed_periods)}')
        return v


class BudgetCreate(BudgetBase):
    """Schema for creating budgets."""

    budget_items: List[BudgetItemCreate] = Field(default_factory=list, description="Budget items")


class BudgetUpdate(BaseModel):
    """Schema for updating budgets."""

    code: Optional[str] = Field(None, max_length=50, description="Budget code")
    name: Optional[str] = Field(None, max_length=200, description="Budget name")
    description: Optional[str] = Field(None, description="Budget description")
    budget_type: Optional[str] = Field(None, description="Budget type")
    fiscal_year: Optional[int] = Field(None, ge=2000, le=2100, description="Fiscal year")
    budget_period: Optional[str] = Field(None, description="Budget period")
    start_date: Optional[date] = Field(None, description="Budget start date")
    end_date: Optional[date] = Field(None, description="Budget end date")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total budget amount")
    currency: Optional[str] = Field(None, max_length=3, description="Currency code")
    alert_threshold: Optional[Decimal] = Field(None, ge=0, le=100, description="Alert threshold percentage")
    is_alert_enabled: Optional[bool] = Field(None, description="Whether alerts are enabled")
    project_id: Optional[int] = Field(None, description="Project ID")
    department_id: Optional[int] = Field(None, description="Department ID")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class BudgetResponse(BudgetBase, BaseResponse):
    """Schema for budget responses."""

    id: int
    organization_id: int
    status: str
    approval_level: int
    approved_amount: Optional[Decimal]
    actual_amount: Decimal
    committed_amount: Decimal
    remaining_amount: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    submitted_at: Optional[datetime]

    # Computed properties
    utilization_percentage: Decimal
    available_amount: Decimal
    is_over_budget: bool
    is_alert_threshold_exceeded: bool
    is_active: bool
    is_editable: bool
    days_remaining: int
    progress_percentage: Decimal

    # Relationships
    organization: Optional[dict] = Field(None, description="Organization details")
    project: Optional[dict] = Field(None, description="Project details")
    department: Optional[dict] = Field(None, description="Department details")
    approved_by_user: Optional[dict] = Field(None, description="Approver details")
    budget_items: List[BudgetItemResponse] = Field(default_factory=list, description="Budget items")

    class Config:
        from_attributes = True


class BudgetStatusUpdate(BaseModel):
    """Schema for updating budget status."""

    action: str = Field(..., description="Action to perform: submit/approve/reject/activate/close")
    comments: Optional[str] = Field(None, description="Comments for the action")

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['submit', 'approve', 'reject', 'activate', 'close']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class BudgetVarianceReport(BaseModel):
    """Schema for budget variance reports."""

    budget_id: int
    budget_name: str
    budget_code: str
    fiscal_year: int
    total_budget: Decimal
    total_actual: Decimal
    total_variance: Decimal
    total_variance_percentage: Decimal

    # Item-level variances
    item_variances: List[dict] = Field(default_factory=list, description="Item-level variance details")

    # Summary by category
    category_summary: List[dict] = Field(default_factory=list, description="Variance summary by category")

    class Config:
        from_attributes = True


class BudgetUtilizationReport(BaseModel):
    """Schema for budget utilization reports."""

    budget_id: int
    budget_name: str
    budget_code: str
    fiscal_year: int
    total_budget: Decimal
    total_actual: Decimal
    total_committed: Decimal
    total_available: Decimal
    utilization_percentage: Decimal

    # Time-based utilization
    monthly_utilization: List[dict] = Field(default_factory=list, description="Monthly utilization")

    # Category-based utilization
    category_utilization: List[dict] = Field(default_factory=list, description="Category utilization")

    class Config:
        from_attributes = True


class BudgetAlertSettings(BaseModel):
    """Schema for budget alert settings."""

    threshold_percentage: Decimal = Field(..., ge=0, le=100, description="Alert threshold percentage")
    is_enabled: bool = Field(True, description="Whether alerts are enabled")
    notification_emails: List[str] = Field(default_factory=list, description="Email addresses for notifications")

    @validator('notification_emails')
    def validate_emails(cls, v):
        # Basic email validation
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in v:
            if not re.match(email_regex, email):
                raise ValueError(f'Invalid email format: {email}')
        return v


class BudgetListResponse(BaseModel):
    """Schema for budget list responses."""

    items: List[BudgetResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

    class Config:
        from_attributes = True


class BudgetSummary(BaseModel):
    """Schema for budget summary."""

    total_budgets: int
    total_budget_amount: Decimal
    total_actual_amount: Decimal
    total_variance_amount: Decimal
    total_variance_percentage: Decimal

    # Status breakdown
    status_breakdown: dict = Field(default_factory=dict, description="Budget count by status")

    # Type breakdown
    type_breakdown: dict = Field(default_factory=dict, description="Budget count by type")

    # Alert information
    over_budget_count: int
    alert_threshold_exceeded_count: int

    class Config:
        from_attributes = True