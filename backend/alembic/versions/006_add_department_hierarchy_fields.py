"""Add department hierarchy fields

Revision ID: 006
Revises: 005
Create Date: 2025-07-09 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add hierarchical structure fields to departments table."""
    # Add path field for materialized path pattern
    op.add_column(
        "departments",
        sa.Column(
            "path",
            sa.String(500),
            nullable=True,
            comment="Materialized path for hierarchical queries",
        ),
    )
    
    # Add depth field for efficient level queries
    op.add_column(
        "departments",
        sa.Column(
            "depth",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Depth in hierarchy (0 for root)",
        ),
    )
    
    # Create indexes for efficient queries
    op.create_index(
        "ix_departments_path",
        "departments",
        ["path"],
        unique=False,
    )
    op.create_index(
        "ix_departments_depth",
        "departments",
        ["depth"],
        unique=False,
    )
    op.create_index(
        "ix_departments_parent_id_display_order",
        "departments",
        ["parent_id", "display_order"],
        unique=False,
    )
    
    # Update existing departments to set path and depth
    connection = op.get_bind()
    
    # First, set path and depth for root departments
    connection.execute(
        sa.text("""
            UPDATE departments 
            SET path = CAST(id AS VARCHAR), depth = 0 
            WHERE parent_id IS NULL
        """)
    )
    
    # Then update child departments iteratively
    # This is a simplified approach - in production you might want a more sophisticated migration
    for level in range(1, 10):  # Support up to 10 levels
        result = connection.execute(
            sa.text(f"""
                UPDATE departments d
                SET 
                    path = p.path || '.' || CAST(d.id AS VARCHAR),
                    depth = {level}
                FROM departments p
                WHERE d.parent_id = p.id 
                    AND p.depth = {level - 1}
                    AND d.depth = 0
            """)
        )
        if result.rowcount == 0:
            break  # No more levels to process
    
    # Make path NOT NULL after populating
    op.alter_column(
        "departments",
        "path",
        existing_type=sa.String(500),
        nullable=False,
    )


def downgrade() -> None:
    """Remove hierarchical structure fields from departments table."""
    # Drop indexes
    op.drop_index("ix_departments_parent_id_display_order", table_name="departments")
    op.drop_index("ix_departments_depth", table_name="departments")
    op.drop_index("ix_departments_path", table_name="departments")
    
    # Drop columns
    op.drop_column("departments", "depth")
    op.drop_column("departments", "path")