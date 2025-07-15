"""Add department hierarchy fields

Revision ID: 006
Revises: 005
Create Date: 2025-01-09

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add path and depth fields to departments table."""
    # Add path column
    op.add_column(
        "departments",
        sa.Column(
            "path",
            sa.String(length=500),
            nullable=True,
            comment="Materialized path for efficient hierarchy queries",
        ),
    )

    # Add depth column
    op.add_column(
        "departments",
        sa.Column(
            "depth",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Depth level in hierarchy (0 for root departments)",
        ),
    )

    # Create indexes for efficient queries
    op.create_index("ix_departments_path", "departments", ["path"])
    op.create_index("ix_departments_depth", "departments", ["depth"])


def downgrade() -> None:
    """Remove hierarchy fields."""
    # Drop indexes
    op.drop_index("ix_departments_path", table_name="departments")
    op.drop_index("ix_departments_depth", table_name="departments")

    # Drop columns
    op.drop_column("departments", "path")
    op.drop_column("departments", "depth")
