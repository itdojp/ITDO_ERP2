"""Add department integration to tasks

Revision ID: 007
Revises: 005
Create Date: 2025-07-09 22:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add department integration fields to tasks table."""
    # Add department_id foreign key column
    op.add_column(
        "tasks",
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id"),
            nullable=True,
        ),
    )

    # Add visibility_scope column
    op.add_column(
        "tasks",
        sa.Column(
            "visibility_scope",
            sa.String(50),
            nullable=False,
            server_default="personal",
        ),
    )

    # Create index on department_id for efficient queries
    op.create_index("ix_tasks_department_id", "tasks", ["department_id"])

    # Create index on visibility_scope for efficient filtering
    op.create_index("ix_tasks_visibility_scope", "tasks", ["visibility_scope"])


def downgrade() -> None:
    """Remove department integration fields from tasks table."""
    # Drop indexes first
    op.drop_index("ix_tasks_visibility_scope", table_name="tasks")
    op.drop_index("ix_tasks_department_id", table_name="tasks")

    # Drop columns
    op.drop_column("tasks", "visibility_scope")
    op.drop_column("tasks", "department_id")
