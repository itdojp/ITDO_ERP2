"""Add name_en field to roles table

Revision ID: 007
Revises: 006
Create Date: 2025-07-13 09:40:00.000000

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
    """Add name_en column to roles table."""
    op.add_column(
        "roles",
        sa.Column(
            "name_en",
            sa.String(length=200),
            nullable=True,
            comment="Role name in English",
        ),
    )


def downgrade() -> None:
    """Remove name_en column from roles table."""
    op.drop_column("roles", "name_en")
