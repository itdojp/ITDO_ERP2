"""Initial migration.

Revision ID: 001
Revises: 
Create Date: 2024-01-01 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Initial migration - creates base schema."""
    pass


def downgrade() -> None:
    """Downgrade not supported for initial migration."""
    pass