"""Add task management tables

Revision ID: 005
Revises: 004
Create Date: 2025-07-09 03:15:00

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="pending"
        ),
        sa.Column(
            "priority", sa.String(length=20), nullable=False, server_default="medium"
        ),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("parent_task_id", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_hours", sa.Float(), nullable=True),
        sa.Column("actual_hours", sa.Float(), nullable=True),
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
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_task_id"],
            ["tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tasks_assignee_id"), "tasks", ["assignee_id"], unique=False
    )
    op.create_index(op.f("ix_tasks_project_id"), "tasks", ["project_id"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)


def downgrade() -> None:
    # Drop tasks table
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_project_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_assignee_id"), table_name="tasks")
    op.drop_table("tasks")
