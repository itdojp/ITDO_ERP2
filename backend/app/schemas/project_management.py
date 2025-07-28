"""プロジェクト管理システムのスキーマ定義"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Project Schemas


class ProjectBase(BaseModel):
    """プロジェクト基本スキーマ"""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    start_date: date
    end_date: date
    budget: Decimal = Field(default=Decimal("0"), ge=0)
    status: str = Field(default="planning")
    project_type: str = Field(default="standard")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ["planning", "active", "completed", "suspended"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

    @field_validator("project_type")
    @classmethod
    def validate_project_type(cls, v: str) -> str:
        valid_types = ["standard", "recurring"]
        if v not in valid_types:
            raise ValueError(f"Project type must be one of {valid_types}")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("End date must be after or equal to start date")
        return v


class ProjectCreate(ProjectBase):
    """プロジェクト作成スキーマ"""

    pass


class ProjectUpdate(BaseModel):
    """プロジェクト更新スキーマ"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_statuses = ["planning", "active", "completed", "suspended"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class ProjectSummary(BaseModel):
    """プロジェクトサマリースキーマ"""

    id: int
    code: str
    name: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(ProjectBase):
    """プロジェクトレスポンススキーマ"""

    id: int
    parent_project: Optional[ProjectSummary] = None
    sub_projects: List[ProjectSummary] = []
    progress_percentage: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    """プロジェクト詳細レスポンススキーマ"""

    members: List["ProjectMemberResponse"] = []
    task_count: int = 0
    milestone_count: int = 0
    budget_info: Optional["BudgetSummary"] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """プロジェクト一覧レスポンススキーマ"""

    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int


# Project Member Schemas


class ProjectMemberBase(BaseModel):
    """プロジェクトメンバー基本スキーマ"""

    user_id: int
    role: str
    allocation_percentage: int = Field(..., ge=0, le=100)
    start_date: date
    end_date: Optional[date] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = [
            "project_leader",
            "architect",
            "dev_leader",
            "developer",
            "tester",
            "other",
        ]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}")
        return v


class ProjectMemberCreate(ProjectMemberBase):
    """プロジェクトメンバー作成スキーマ"""

    pass


class ProjectMemberResponse(ProjectMemberBase):
    """プロジェクトメンバーレスポンススキーマ"""

    id: int
    user: "UserSummary"
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberListResponse(BaseModel):
    """プロジェクトメンバー一覧レスポンススキーマ"""

    items: List[ProjectMemberResponse]
    total: int


# Task Schemas


class TaskBase(BaseModel):
    """タスク基本スキーマ"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    parent_task_id: Optional[int] = None
    start_date: date
    end_date: date
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    priority: str = Field(default="medium")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        valid_priorities = ["high", "medium", "low"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v


class TaskCreate(TaskBase):
    """タスク作成スキーマ"""

    pass


class TaskUpdate(BaseModel):
    """タスク更新スキーマ"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    priority: Optional[str] = None
    status: Optional[str] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)


class TaskResponse(TaskBase):
    """タスクレスポンススキーマ"""

    id: int
    project_id: int
    status: str = "not_started"
    progress_percentage: int = 0
    actual_hours: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskDetailResponse(TaskResponse):
    """タスク詳細レスポンススキーマ"""

    sub_tasks: List[TaskResponse] = []
    dependencies: List["TaskDependency"] = []
    resources: List["ResourceAssignmentResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class TaskNode(TaskResponse):
    """タスクノード（階層構造）スキーマ"""

    children: List["TaskNode"] = []

    model_config = ConfigDict(from_attributes=True)


class TaskTreeResponse(BaseModel):
    """タスクツリーレスポンススキーマ"""

    tasks: List[TaskNode]


# Task Dependency Schemas


class TaskDependencyCreate(BaseModel):
    """タスク依存関係作成スキーマ"""

    predecessor_id: int
    dependency_type: str = Field(default="finish_to_start")
    lag_days: int = Field(default=0)

    @field_validator("dependency_type")
    @classmethod
    def validate_dependency_type(cls, v: str) -> str:
        valid_types = [
            "finish_to_start",
            "start_to_start",
            "finish_to_finish",
            "start_to_finish",
        ]
        if v not in valid_types:
            raise ValueError(f"Dependency type must be one of {valid_types}")
        return v


class TaskDependency(TaskDependencyCreate):
    """タスク依存関係スキーマ"""

    id: int
    successor_id: int

    model_config = ConfigDict(from_attributes=True)


# Resource Assignment Schemas


class ResourceAssignment(BaseModel):
    """リソース割当スキーマ"""

    resource_id: int
    allocation_percentage: int = Field(..., ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_hours: Optional[Decimal] = Field(None, ge=0)


class ResourceAssignmentResponse(ResourceAssignment):
    """リソース割当レスポンススキーマ"""

    id: int
    resource: "UserSummary"
    actual_hours: Decimal = Decimal("0")

    model_config = ConfigDict(from_attributes=True)


# Milestone Schemas


class MilestoneCreate(BaseModel):
    """マイルストーン作成スキーマ"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    target_date: date
    deliverable: Optional[str] = Field(None, max_length=200)
    approver_id: Optional[int] = None


class MilestoneResponse(MilestoneCreate):
    """マイルストーンレスポンススキーマ"""

    id: int
    status: str = "pending"
    achieved_date: Optional[date] = None
    approver: Optional["UserSummary"] = None

    model_config = ConfigDict(from_attributes=True)


class MilestoneListResponse(BaseModel):
    """マイルストーン一覧レスポンススキーマ"""

    items: List[MilestoneResponse]
    total: int


# Progress Update Schemas


class ProgressUpdate(BaseModel):
    """進捗更新スキーマ"""

    progress_percentage: int = Field(..., ge=0, le=100)
    actual_hours: Decimal = Field(..., ge=0)
    comment: Optional[str] = Field(None, max_length=500)


# Budget Schemas


class BudgetUpdate(BaseModel):
    """予算更新スキーマ"""

    estimated_cost: Optional[Decimal] = Field(None, ge=0)
    actual_cost: Optional[Decimal] = Field(None, ge=0)
    labor_cost: Optional[Decimal] = Field(None, ge=0)
    outsourcing_cost: Optional[Decimal] = Field(None, ge=0)
    expense_cost: Optional[Decimal] = Field(None, ge=0)


class CostItem(BaseModel):
    """コスト項目スキーマ"""

    planned: Decimal
    actual: Decimal
    variance: Decimal

    model_config = ConfigDict(from_attributes=True)


class BudgetResponse(BaseModel):
    """予算レスポンススキーマ"""

    budget_amount: Decimal
    estimated_cost: Decimal
    actual_cost: Decimal
    cost_breakdown: Dict[str, CostItem]
    consumption_rate: float
    forecast_at_completion: Decimal
    variance: Decimal
    revenue: Decimal
    profit: Decimal
    profit_rate: float

    model_config = ConfigDict(from_attributes=True)


class BudgetSummary(BaseModel):
    """予算サマリースキーマ"""

    budget: Decimal
    actual_cost: Decimal
    consumption_rate: float

    model_config = ConfigDict(from_attributes=True)


# Gantt Chart Schemas


class GanttTask(BaseModel):
    """ガントチャートタスクスキーマ"""

    id: int
    name: str
    start_date: date
    end_date: date
    progress: int
    level: int
    is_milestone: bool
    resources: List[str]

    model_config = ConfigDict(from_attributes=True)


class GanttDependency(BaseModel):
    """ガントチャート依存関係スキーマ"""

    source: int
    target: int
    type: str

    model_config = ConfigDict(from_attributes=True)


class GanttChartResponse(BaseModel):
    """ガントチャートレスポンススキーマ"""

    tasks: List[GanttTask]
    dependencies: List[GanttDependency]
    critical_path: List[int]


# Resource Management Schemas


class ResourceInfo(BaseModel):
    """リソース情報スキーマ"""

    id: int
    name: str
    email: str
    skills: List[str]
    max_allocation: int
    current_allocation: int

    model_config = ConfigDict(from_attributes=True)


class ResourceListResponse(BaseModel):
    """リソース一覧レスポンススキーマ"""

    items: List[ResourceInfo]
    total: int


class UtilizationDetail(BaseModel):
    """稼働率詳細スキーマ"""

    date: date
    utilization_percentage: int
    allocated_hours: Decimal

    model_config = ConfigDict(from_attributes=True)


class UtilizationResponse(BaseModel):
    """稼働率レスポンススキーマ"""

    resource_id: int
    period: Dict[str, date]
    daily_utilization: List[UtilizationDetail]
    average_utilization: float
    peak_utilization: int
    overallocated_days: int


# Report Schemas


class ProgressReportResponse(BaseModel):
    """進捗レポートレスポンススキーマ"""

    project: ProjectSummary
    report_date: date
    overall_progress: float
    milestone_status: Dict[str, int]
    task_status: Dict[str, int]
    budget_status: BudgetSummary
    risks: List[Dict[str, str]]


# Recurring Project Schemas


class RecurringProjectCreate(BaseModel):
    """繰り返しプロジェクト作成スキーマ"""

    template: ProjectCreate
    recurrence_pattern: str
    recurrence_count: int = Field(..., ge=1, le=60)
    start_date: date

    @field_validator("recurrence_pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        valid_patterns = ["daily", "weekly", "monthly", "yearly"]
        if v not in valid_patterns:
            raise ValueError(f"Recurrence pattern must be one of {valid_patterns}")
        return v


class RecurringProjectResponse(BaseModel):
    """繰り返しプロジェクトレスポンススキーマ"""

    master_project: ProjectResponse
    generated_projects: List[ProjectResponse]
    total_budget: Decimal


# User Summary Schema


class UserSummary(BaseModel):
    """ユーザーサマリースキーマ"""

    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


# Error Schema


class Error(BaseModel):
    """エラースキーマ"""

    code: str
    message: str
    details: Optional[Dict] = None
