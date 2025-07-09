"""Add inherit_permissions field to departments

Revision ID: 007
Revises: 006
Create Date: 2024-07-09 18:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add inherit_permissions field to departments."""
    # Add the inherit_permissions field with default True
    op.add_column(
        "departments",
        sa.Column(
            "inherit_permissions",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Whether to inherit permissions from parent departments",
        ),
    )


def downgrade() -> None:
    """Remove inherit_permissions field from departments."""
    op.drop_column("departments", "inherit_permissions")