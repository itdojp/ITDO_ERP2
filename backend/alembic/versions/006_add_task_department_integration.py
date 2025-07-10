"""Add department integration to tasks - CRITICAL Phase 3

Revision ID: 006
Revises: 005
Create Date: 2025-07-10 12:00:00

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add department integration to tasks table."""
    # Add department_id column
    op.add_column(
        "tasks",
        sa.Column(
            "department_id",
            sa.Integer(),
            nullable=True,
            comment="Department assignment for hierarchical task management",
        ),
    )
    
    # Add department_visibility column
    op.add_column(
        "tasks",
        sa.Column(
            "department_visibility",
            sa.String(length=50),
            nullable=False,
            server_default="department_hierarchy",
            comment="Visibility scope: personal, department, department_hierarchy, organization",
        ),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_tasks_department_id",
        "tasks",
        "departments",
        ["department_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index for performance
    op.create_index("ix_tasks_department_id", "tasks", ["department_id"])


def downgrade() -> None:
    """Remove department integration from tasks table."""
    # Drop index
    op.drop_index("ix_tasks_department_id", table_name="tasks")
    
    # Drop foreign key constraint
    op.drop_constraint("fk_tasks_department_id", "tasks", type_="foreignkey")
    
    # Drop columns
    op.drop_column("tasks", "department_visibility")
    op.drop_column("tasks", "department_id")