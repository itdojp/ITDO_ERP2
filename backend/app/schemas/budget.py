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
    
    name: str = Field(..., max_length=200, description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    expense_category_id: int = Field(..., description="Expense category ID")
    budgeted_amount: Decimal = Field(..., description="Budgeted amount")


class BudgetItemCreate(BudgetItemBase):
    """Schema for creating budget items."""
    pass


class BudgetItemUpdate(BaseModel):
    """Schema for updating budget items."""
    
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    expense_category_id: Optional[int] = Field(None)
    budgeted_amount: Optional[Decimal] = Field(None)


class BudgetItemResponse(BudgetItemBase, BaseResponse):
    """Schema for budget item responses."""
    
    id: int
    budget_id: int
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    
    # Relationships
    expense_category: Optional[ExpenseCategoryResponse] = None
    
    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    """Base schema for budgets."""
    
    code: str = Field(..., max_length=50, description="Budget code")
    name: str = Field(..., max_length=200, description="Budget name")
    description: Optional[str] = Field(None, description="Budget description")
    budget_type: str = Field(..., description="Budget type")
    fiscal_year: int = Field(..., description="Fiscal year")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    total_amount: Decimal = Field(..., description="Total amount")
    project_id: Optional[int] = Field(None, description="Project ID")
    department_id: Optional[int] = Field(None, description="Department ID")
    alert_threshold: Decimal = Field(Decimal("80.00"), description="Alert threshold")
    is_alert_enabled: bool = Field(True, description="Alert enabled")

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


class BudgetCreate(BudgetBase):
    """Schema for creating budgets."""
    
    budget_items: List[BudgetItemCreate] = Field(default_factory=list, description="Budget items")


class BudgetUpdate(BaseModel):
    """Schema for updating budgets."""
    
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    budget_type: Optional[str] = Field(None)
    fiscal_year: Optional[int] = Field(None)
    start_date: Optional[date] = Field(None)
    end_date: Optional[date] = Field(None)
    total_amount: Optional[Decimal] = Field(None)
    project_id: Optional[int] = Field(None)
    department_id: Optional[int] = Field(None)
    alert_threshold: Optional[Decimal] = Field(None)
    is_alert_enabled: Optional[bool] = Field(None)


class BudgetResponse(BudgetBase, BaseResponse):
    """Schema for budget responses."""
    
    id: int
    organization_id: int
    status: str
    approved_amount: Optional[Decimal]
    actual_amount: Decimal
    remaining_amount: Decimal
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    
    # Computed properties
    utilization_percentage: Decimal
    is_over_budget: bool
    is_alert_threshold_exceeded: bool
    
    # Relationships
    budget_items: List[BudgetItemResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class BudgetStatusUpdate(BaseModel):
    """Schema for updating budget status."""
    
    action: str = Field(..., description="Action: submit, approve, reject, activate, close")
    comments: Optional[str] = Field(None, description="Status change comments")

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['submit', 'approve', 'reject', 'activate', 'close']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class BudgetListResponse(BaseModel):
    """Schema for budget list responses."""
    
    items: List[BudgetResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class BudgetSummary(BaseModel):
    """Schema for budget summary analytics."""
    
    total_budgets: int
    total_budget_amount: Decimal
    total_actual_amount: Decimal
    total_variance_amount: Decimal
    variance_percentage: Decimal
    over_budget_count: int
    alert_threshold_exceeded_count: int