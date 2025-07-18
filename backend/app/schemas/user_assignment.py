"""
User Assignment Pydantic schemas for Issue #42.
ユーザー割り当て関連Pydanticスキーマ（Issue #42）
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserAssignmentCreate(BaseModel):
    """Schema for creating user assignment."""

    user_id: int = Field(..., description="User ID to assign")
    organization_id: int = Field(..., description="Organization ID")
    department_id: Optional[int] = Field(None, description="Department ID (optional)")
    role_assignments: Optional[List[str]] = Field(None, description="List of role names to assign")
    effective_date: Optional[datetime] = Field(None, description="Effective date of assignment")
    assignment_reason: Optional[str] = Field(None, max_length=500, description="Reason for assignment")
    is_primary: bool = Field(True, description="Whether this is the primary assignment")


class UserAssignmentUpdate(BaseModel):
    """Schema for updating user assignment."""

    organization_id: Optional[int] = Field(None, description="New organization ID")
    department_id: Optional[int] = Field(None, description="New department ID")
    role_assignments: Optional[List[str]] = Field(None, description="Updated role assignments")
    effective_date: Optional[datetime] = Field(None, description="Updated effective date")
    assignment_reason: Optional[str] = Field(None, max_length=500, description="Updated assignment reason")
    is_primary: Optional[bool] = Field(None, description="Updated primary assignment status")
    is_active: Optional[bool] = Field(None, description="Assignment active status")


class UserAssignmentResponse(BaseModel):
    """Schema for user assignment response."""

    id: int
    user_id: int
    organization_id: int
    department_id: Optional[int]
    is_primary: bool
    is_active: bool
    effective_date: Optional[datetime]
    assignment_reason: Optional[str]
    assigned_by: Optional[int]
    assigned_at: datetime
    updated_by: Optional[int]
    updated_at: Optional[datetime]

    # Related data
    user_name: Optional[str] = Field(None, description="User full name")
    user_email: Optional[str] = Field(None, description="User email")
    organization_name: Optional[str] = Field(None, description="Organization name")
    organization_code: Optional[str] = Field(None, description="Organization code")
    department_name: Optional[str] = Field(None, description="Department name")
    department_code: Optional[str] = Field(None, description="Department code")
    role_names: Optional[List[str]] = Field(None, description="Assigned role names")

    class Config:
        from_attributes = True


class BulkUserAssignmentRequest(BaseModel):
    """Schema for bulk user assignment request."""

    assignments: List[UserAssignmentCreate] = Field(..., description="List of assignments to create")
    validate_before_commit: bool = Field(True, description="Validate assignments before committing")
    skip_duplicates: bool = Field(True, description="Skip duplicate assignments")
    assignment_reason: Optional[str] = Field(None, description="Common assignment reason")


class UserSummary(BaseModel):
    """Schema for user summary in assignments."""

    id: int
    full_name: str
    email: str
    is_active: bool
    employee_id: Optional[str]
    hire_date: Optional[datetime]
    job_title: Optional[str]
    current_organization_id: Optional[int]
    current_department_id: Optional[int]


class OrganizationUsersResponse(BaseModel):
    """Schema for organization users response."""

    organization_id: int
    organization_name: str
    organization_code: str
    total_users: int
    active_users: int
    inactive_users: int
    users: List[UserSummary]
    departments: Optional[List[dict]] = Field(None, description="Department breakdown")

    # Pagination
    limit: int
    offset: int
    has_more: bool


class DepartmentUsersResponse(BaseModel):
    """Schema for department users response."""

    department_id: int
    department_name: str
    department_code: str
    organization_id: int
    organization_name: str
    total_users: int
    active_users: int
    inactive_users: int
    users: List[UserSummary]
    sub_departments: Optional[List[dict]] = Field(None, description="Sub-department breakdown")

    # Pagination
    limit: int
    offset: int
    has_more: bool


class AssignmentHistory(BaseModel):
    """Schema for assignment history entry."""

    id: int
    user_id: int
    organization_id: int
    organization_name: str
    department_id: Optional[int]
    department_name: Optional[str]
    effective_date: datetime
    end_date: Optional[datetime]
    assignment_reason: Optional[str]
    assigned_by: Optional[int]
    assigned_by_name: Optional[str]
    assignment_type: str  # 'initial', 'transfer', 'promotion', 'termination'


class UserAssignmentFull(BaseModel):
    """Schema for complete user assignment information."""

    user_id: int
    user_name: str
    user_email: str
    current_assignment: Optional[UserAssignmentResponse]
    assignment_history: List[AssignmentHistory]
    total_assignments: int
    active_assignments: int


class OrganizationAssignmentStats(BaseModel):
    """Schema for organization assignment statistics."""

    organization_id: int
    organization_name: str
    total_assignments: int
    active_assignments: int
    inactive_assignments: int
    total_users: int
    active_users: int
    departments_count: int

    # Department breakdown
    department_stats: Optional[List[dict]] = Field(None, description="Per-department statistics")

    # Role distribution
    role_distribution: dict = Field(default_factory=dict, description="Users by role")

    # Trend data
    monthly_changes: dict = Field(default_factory=dict, description="Monthly assignment changes")


class DepartmentAssignmentStats(BaseModel):
    """Schema for department assignment statistics."""

    department_id: int
    department_name: str
    organization_id: int
    total_assignments: int
    active_assignments: int
    inactive_assignments: int
    total_users: int
    active_users: int

    # Capacity metrics
    headcount_limit: Optional[int]
    headcount_utilization: Optional[float] = Field(None, description="Utilization percentage")

    # Sub-department breakdown
    sub_department_stats: Optional[List[dict]] = Field(None, description="Sub-department statistics")

    # Role distribution
    role_distribution: dict = Field(default_factory=dict, description="Users by role")


class AssignmentValidationIssue(BaseModel):
    """Schema for assignment validation issues."""

    issue_type: str  # 'orphaned_user', 'invalid_department', 'circular_assignment', etc.
    severity: str    # 'error', 'warning', 'info'
    description: str
    user_id: Optional[int]
    user_name: Optional[str]
    organization_id: Optional[int]
    department_id: Optional[int]
    suggested_fix: Optional[str]
    auto_fixable: bool


class AssignmentValidationResult(BaseModel):
    """Schema for assignment validation results."""

    validation_date: datetime
    total_assignments_checked: int
    issues_found: int
    errors_count: int
    warnings_count: int
    issues: List[AssignmentValidationIssue]
    recommendations: List[str]

    # Summary by type
    issue_summary: dict = Field(default_factory=dict, description="Issues grouped by type")


class TransferRequest(BaseModel):
    """Schema for user transfer request."""

    user_id: int
    from_organization_id: Optional[int] = Field(None, description="Current organization (for validation)")
    from_department_id: Optional[int] = Field(None, description="Current department (for validation)")
    to_organization_id: Optional[int] = Field(None, description="Target organization")
    to_department_id: Optional[int] = Field(None, description="Target department")
    transfer_reason: str = Field(..., description="Reason for transfer")
    effective_date: Optional[datetime] = Field(None, description="Transfer effective date")
    maintain_roles: bool = Field(True, description="Whether to maintain current roles")
    notify_managers: bool = Field(True, description="Whether to notify managers")


class TransferResponse(BaseModel):
    """Schema for user transfer response."""

    transfer_id: int
    user_id: int
    user_name: str
    from_organization: Optional[dict] = Field(None, description="Previous organization info")
    from_department: Optional[dict] = Field(None, description="Previous department info")
    to_organization: Optional[dict] = Field(None, description="New organization info")
    to_department: Optional[dict] = Field(None, description="New department info")
    transfer_reason: str
    effective_date: datetime
    processed_by: int
    processed_at: datetime
    status: str  # 'pending', 'completed', 'cancelled'


class AssignmentSearchFilters(BaseModel):
    """Schema for assignment search filters."""

    organization_ids: Optional[List[int]] = Field(None, description="Filter by organizations")
    department_ids: Optional[List[int]] = Field(None, description="Filter by departments")
    user_ids: Optional[List[int]] = Field(None, description="Filter by users")
    role_names: Optional[List[str]] = Field(None, description="Filter by roles")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_primary: Optional[bool] = Field(None, description="Filter by primary assignment")
    date_from: Optional[datetime] = Field(None, description="Effective date from")
    date_to: Optional[datetime] = Field(None, description="Effective date to")
    assignment_types: Optional[List[str]] = Field(None, description="Filter by assignment types")


class AssignmentSearchResponse(BaseModel):
    """Schema for assignment search results."""

    assignments: List[UserAssignmentResponse]
    total_count: int
    search_filters: AssignmentSearchFilters

    # Pagination
    limit: int
    offset: int
    has_more: bool

    # Aggregations
    organization_breakdown: dict = Field(default_factory=dict)
    department_breakdown: dict = Field(default_factory=dict)
    role_breakdown: dict = Field(default_factory=dict)
