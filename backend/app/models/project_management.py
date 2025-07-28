"""プロジェクト管理システムのデータモデル"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DECIMAL

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Project(Base):
    """プロジェクトモデル"""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("projects.id"))
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    budget: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    project_type: Mapped[str] = mapped_column(String(20), default="standard")
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id")
    )
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    parent: Mapped[Optional["Project"]] = relationship(
        "Project", remote_side="Project.id", back_populates="sub_projects"
    )
    sub_projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="parent"
    )
    members: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember", back_populates="project"
    )
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project")
    milestones: Mapped[List["Milestone"]] = relationship(
        "Milestone", back_populates="project"
    )
    budget_info: Mapped[Optional["ProjectBudget"]] = relationship(
        "ProjectBudget", back_populates="project", uselist=False
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="projects"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_projects_dates"),
        CheckConstraint("budget >= 0", name="ck_projects_budget"),
        CheckConstraint(
            "status IN ('planning', 'active', 'completed', 'suspended')",
            name="ck_projects_status",
        ),
        Index("idx_projects_code", "code"),
        Index("idx_projects_parent_id", "parent_id"),
        Index("idx_projects_organization_id", "organization_id"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_dates", "start_date", "end_date"),
    )


class ProjectMember(Base):
    """プロジェクトメンバーモデル"""

    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    allocation_percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="project_memberships")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "project_id", "user_id", name="uq_project_members_project_user"
        ),
        CheckConstraint(
            "allocation_percentage >= 0 AND allocation_percentage <= 100",
            name="ck_project_members_allocation",
        ),
        CheckConstraint(
            "role IN ('project_leader', 'architect', 'dev_leader', 'developer', 'tester', 'other')",
            name="ck_project_members_role",
        ),
        Index("idx_project_members_user_id", "user_id"),
        Index("idx_project_members_dates", "start_date", "end_date"),
    )


class Task(Base):
    """タスクモデル"""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    parent_task_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tasks.id")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2))
    actual_hours: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), default=0)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="not_started")
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task", remote_side="Task.id", back_populates="sub_tasks"
    )
    sub_tasks: Mapped[List["Task"]] = relationship("Task", back_populates="parent_task")
    dependencies_as_predecessor: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.predecessor_id",
        back_populates="predecessor",
    )
    dependencies_as_successor: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.successor_id",
        back_populates="successor",
    )
    resources: Mapped[List["TaskResource"]] = relationship(
        "TaskResource", back_populates="task"
    )
    progress_history: Mapped[List["TaskProgress"]] = relationship(
        "TaskProgress", back_populates="task"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_tasks_dates"),
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="ck_tasks_progress",
        ),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed', 'on_hold')",
            name="ck_tasks_status",
        ),
        CheckConstraint(
            "priority IN ('high', 'medium', 'low')", name="ck_tasks_priority"
        ),
        Index("idx_tasks_project_id", "project_id"),
        Index("idx_tasks_parent_task_id", "parent_task_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_dates", "start_date", "end_date"),
    )


class TaskDependency(Base):
    """タスク依存関係モデル"""

    __tablename__ = "task_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    predecessor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False
    )
    successor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False
    )
    dependency_type: Mapped[str] = mapped_column(String(20), default="finish_to_start")
    lag_days: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    predecessor: Mapped["Task"] = relationship(
        "Task",
        foreign_keys=[predecessor_id],
        back_populates="dependencies_as_predecessor",
    )
    successor: Mapped["Task"] = relationship(
        "Task", foreign_keys=[successor_id], back_populates="dependencies_as_successor"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "predecessor_id", "successor_id", name="uq_task_dependencies_unique"
        ),
        CheckConstraint(
            "dependency_type IN ('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish')",
            name="ck_task_dependencies_type",
        ),
        CheckConstraint(
            "predecessor_id != successor_id", name="ck_task_dependencies_not_self"
        ),
        Index("idx_task_dependencies_successor", "successor_id"),
    )


class TaskResource(Base):
    """タスクリソース割当モデル"""

    __tablename__ = "task_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    allocation_percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(Date)
    end_date: Mapped[Optional[datetime]] = mapped_column(Date)
    planned_hours: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2))
    actual_hours: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="resources")
    user: Mapped["User"] = relationship("User", back_populates="task_assignments")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "allocation_percentage >= 0 AND allocation_percentage <= 100",
            name="ck_task_resources_allocation",
        ),
        Index("idx_task_resources_task_user", "task_id", "user_id"),
        Index("idx_task_resources_user_id", "user_id"),
        Index("idx_task_resources_dates", "start_date", "end_date"),
    )


class TaskProgress(Base):
    """タスク進捗履歴モデル"""

    __tablename__ = "task_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False
    )
    progress_percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_hours: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2))
    comment: Mapped[Optional[str]] = mapped_column(Text)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="progress_history")
    updater: Mapped["User"] = relationship("User")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="ck_task_progress_percentage",
        ),
        Index("idx_task_progress_task_id", "task_id"),
        Index("idx_task_progress_created_at", "created_at"),
    )


class Milestone(Base):
    """マイルストーンモデル"""

    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    target_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    achieved_date: Mapped[Optional[datetime]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    deliverable: Mapped[Optional[str]] = mapped_column(String(200))
    approver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="milestones")
    approver: Mapped[Optional["User"]] = relationship("User")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'achieved', 'delayed', 'cancelled')",
            name="ck_milestones_status",
        ),
        Index("idx_milestones_project_id", "project_id"),
        Index("idx_milestones_target_date", "target_date"),
        Index("idx_milestones_status", "status"),
    )


class ProjectBudget(Base):
    """プロジェクト予算モデル"""

    __tablename__ = "project_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), unique=True, nullable=False
    )
    budget_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0)
    estimated_cost: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0)
    actual_cost: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0)
    labor_cost: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0)
    outsourcing_cost: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0)
    expense_cost: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0)
    revenue: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="budget_info")

    # Constraints
    __table_args__ = (Index("idx_project_budgets_project_id", "project_id"),)


class RecurringProjectTemplate(Base):
    """繰り返しプロジェクトテンプレートモデル"""

    __tablename__ = "recurring_project_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code_prefix: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_per_instance: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0)
    recurrence_pattern: Mapped[str] = mapped_column(String(20), nullable=False)
    template_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    instances: Mapped[List["RecurringProjectInstance"]] = relationship(
        "RecurringProjectInstance", back_populates="template"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "recurrence_pattern IN ('daily', 'weekly', 'monthly', 'yearly')",
            name="ck_recurring_templates_pattern",
        ),
        CheckConstraint("duration_days > 0", name="ck_recurring_templates_duration"),
    )


class RecurringProjectInstance(Base):
    """繰り返しプロジェクトインスタンスモデル"""

    __tablename__ = "recurring_project_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recurring_project_templates.id"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), unique=True, nullable=False
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    template: Mapped["RecurringProjectTemplate"] = relationship(
        "RecurringProjectTemplate", back_populates="instances"
    )
    project: Mapped["Project"] = relationship("Project")

    # Constraints
    __table_args__ = (
        Index("idx_recurring_instances_template", "template_id"),
        Index("idx_recurring_instances_project", "project_id"),
    )
