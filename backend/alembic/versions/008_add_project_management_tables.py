"""Add project management tables

Revision ID: 008_project_management
Revises: 007_add_authentication_models
Create Date: 2025-07-28

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "008_project_management"
down_revision = "007_add_authentication_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("budget", sa.DECIMAL(15, 2), nullable=True, default=0),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("project_type", sa.String(20), nullable=True, default="standard"),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.CheckConstraint("end_date >= start_date", name="ck_projects_dates"),
        sa.CheckConstraint("budget >= 0", name="ck_projects_budget"),
        sa.CheckConstraint(
            "status IN ('planning', 'active', 'completed', 'suspended')",
            name="ck_projects_status",
        ),
    )
    op.create_index("idx_projects_code", "projects", ["code"])
    op.create_index("idx_projects_parent_id", "projects", ["parent_id"])
    op.create_index("idx_projects_organization_id", "projects", ["organization_id"])
    op.create_index("idx_projects_status", "projects", ["status"])
    op.create_index("idx_projects_dates", "projects", ["start_date", "end_date"])

    # Create project_members table
    op.create_table(
        "project_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("allocation_percentage", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "user_id", name="uq_project_members_project_user"
        ),
        sa.CheckConstraint(
            "allocation_percentage >= 0 AND allocation_percentage <= 100",
            name="ck_project_members_allocation",
        ),
        sa.CheckConstraint(
            "role IN ('project_leader', 'architect', 'dev_leader', 'developer', 'tester', 'other')",
            name="ck_project_members_role",
        ),
    )
    op.create_index("idx_project_members_user_id", "project_members", ["user_id"])
    op.create_index(
        "idx_project_members_dates", "project_members", ["start_date", "end_date"]
    )

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("parent_task_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("estimated_hours", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("actual_hours", sa.DECIMAL(8, 2), nullable=True, default=0),
        sa.Column("progress_percentage", sa.Integer(), nullable=True, default=0),
        sa.Column("status", sa.String(20), nullable=True, default="not_started"),
        sa.Column("priority", sa.String(10), nullable=True, default="medium"),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_task_id"],
            ["tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("end_date >= start_date", name="ck_tasks_dates"),
        sa.CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="ck_tasks_progress",
        ),
        sa.CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed', 'on_hold')",
            name="ck_tasks_status",
        ),
        sa.CheckConstraint(
            "priority IN ('high', 'medium', 'low')", name="ck_tasks_priority"
        ),
    )
    op.create_index("idx_tasks_project_id", "tasks", ["project_id"])
    op.create_index("idx_tasks_parent_task_id", "tasks", ["parent_task_id"])
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_index("idx_tasks_dates", "tasks", ["start_date", "end_date"])

    # Create task_dependencies table
    op.create_table(
        "task_dependencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("predecessor_id", sa.Integer(), nullable=False),
        sa.Column("successor_id", sa.Integer(), nullable=False),
        sa.Column(
            "dependency_type", sa.String(20), nullable=True, default="finish_to_start"
        ),
        sa.Column("lag_days", sa.Integer(), nullable=True, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_id"],
            ["tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["successor_id"],
            ["tasks.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "predecessor_id", "successor_id", name="uq_task_dependencies_unique"
        ),
        sa.CheckConstraint(
            "dependency_type IN ('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish')",
            name="ck_task_dependencies_type",
        ),
        sa.CheckConstraint(
            "predecessor_id != successor_id", name="ck_task_dependencies_not_self"
        ),
    )
    op.create_index(
        "idx_task_dependencies_successor", "task_dependencies", ["successor_id"]
    )

    # Create task_resources table
    op.create_table(
        "task_resources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("allocation_percentage", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("planned_hours", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("actual_hours", sa.DECIMAL(8, 2), nullable=True, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "allocation_percentage >= 0 AND allocation_percentage <= 100",
            name="ck_task_resources_allocation",
        ),
    )
    op.create_index(
        "idx_task_resources_task_user", "task_resources", ["task_id", "user_id"]
    )
    op.create_index("idx_task_resources_user_id", "task_resources", ["user_id"])
    op.create_index(
        "idx_task_resources_dates", "task_resources", ["start_date", "end_date"]
    )

    # Create task_progress table
    op.create_table(
        "task_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("progress_percentage", sa.Integer(), nullable=False),
        sa.Column("actual_hours", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="ck_task_progress_percentage",
        ),
    )
    op.create_index("idx_task_progress_task_id", "task_progress", ["task_id"])
    op.create_index("idx_task_progress_created_at", "task_progress", ["created_at"])

    # Create milestones table
    op.create_table(
        "milestones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("achieved_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True, default="pending"),
        sa.Column("deliverable", sa.String(200), nullable=True),
        sa.Column("approver_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["approver_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('pending', 'achieved', 'delayed', 'cancelled')",
            name="ck_milestones_status",
        ),
    )
    op.create_index("idx_milestones_project_id", "milestones", ["project_id"])
    op.create_index("idx_milestones_target_date", "milestones", ["target_date"])
    op.create_index("idx_milestones_status", "milestones", ["status"])

    # Create project_budgets table
    op.create_table(
        "project_budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("budget_amount", sa.DECIMAL(15, 2), nullable=True, default=0),
        sa.Column("estimated_cost", sa.DECIMAL(15, 2), nullable=True, default=0),
        sa.Column("actual_cost", sa.DECIMAL(15, 2), nullable=True, default=0),
        sa.Column("labor_cost", sa.DECIMAL(15, 2), nullable=True, default=0),
        sa.Column("outsourcing_cost", sa.DECIMAL(15, 2), nullable=True, default=0),
        sa.Column("expense_cost", sa.DECIMAL(15, 2), nullable=True, default=0),
        sa.Column("revenue", sa.DECIMAL(15, 2), nullable=True, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index("idx_project_budgets_project_id", "project_budgets", ["project_id"])

    # Create recurring_project_templates table
    op.create_table(
        "recurring_project_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code_prefix", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("budget_per_instance", sa.DECIMAL(15, 2), nullable=True, default=0),
        sa.Column("recurrence_pattern", sa.String(20), nullable=False),
        sa.Column(
            "template_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "recurrence_pattern IN ('daily', 'weekly', 'monthly', 'yearly')",
            name="ck_recurring_templates_pattern",
        ),
        sa.CheckConstraint("duration_days > 0", name="ck_recurring_templates_duration"),
    )

    # Create recurring_project_instances table
    op.create_table(
        "recurring_project_instances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["recurring_project_templates.id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index(
        "idx_recurring_instances_template",
        "recurring_project_instances",
        ["template_id"],
    )
    op.create_index(
        "idx_recurring_instances_project", "recurring_project_instances", ["project_id"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        "idx_recurring_instances_project", table_name="recurring_project_instances"
    )
    op.drop_index(
        "idx_recurring_instances_template", table_name="recurring_project_instances"
    )
    op.drop_index("idx_project_budgets_project_id", table_name="project_budgets")
    op.drop_index("idx_milestones_status", table_name="milestones")
    op.drop_index("idx_milestones_target_date", table_name="milestones")
    op.drop_index("idx_milestones_project_id", table_name="milestones")
    op.drop_index("idx_task_progress_created_at", table_name="task_progress")
    op.drop_index("idx_task_progress_task_id", table_name="task_progress")
    op.drop_index("idx_task_resources_dates", table_name="task_resources")
    op.drop_index("idx_task_resources_user_id", table_name="task_resources")
    op.drop_index("idx_task_resources_task_user", table_name="task_resources")
    op.drop_index("idx_task_dependencies_successor", table_name="task_dependencies")
    op.drop_index("idx_tasks_dates", table_name="tasks")
    op.drop_index("idx_tasks_status", table_name="tasks")
    op.drop_index("idx_tasks_parent_task_id", table_name="tasks")
    op.drop_index("idx_tasks_project_id", table_name="tasks")
    op.drop_index("idx_project_members_dates", table_name="project_members")
    op.drop_index("idx_project_members_user_id", table_name="project_members")
    op.drop_index("idx_projects_dates", table_name="projects")
    op.drop_index("idx_projects_status", table_name="projects")
    op.drop_index("idx_projects_organization_id", table_name="projects")
    op.drop_index("idx_projects_parent_id", table_name="projects")
    op.drop_index("idx_projects_code", table_name="projects")

    # Drop tables
    op.drop_table("recurring_project_instances")
    op.drop_table("recurring_project_templates")
    op.drop_table("project_budgets")
    op.drop_table("milestones")
    op.drop_table("task_progress")
    op.drop_table("task_resources")
    op.drop_table("task_dependencies")
    op.drop_table("tasks")
    op.drop_table("project_members")
    op.drop_table("projects")
