"""Fix role_permissions table - add id column

Revision ID: 006_fix_role_permissions_id
Revises: 005_add_task_management_tables
Create Date: 2025-01-14

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_fix_role_permissions_id"
down_revision: Union[str, None] = "005_add_task_management_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing primary key constraint
    op.drop_constraint("role_permissions_pkey", "role_permissions", type_="primary")
    
    # Add id column with auto-increment
    op.add_column(
        "role_permissions",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
            autoincrement=True,
            comment="Primary key"
        )
    )
    
    # Create sequence for the id column (PostgreSQL specific)
    op.execute("CREATE SEQUENCE role_permissions_id_seq")
    op.execute("ALTER TABLE role_permissions ALTER COLUMN id SET DEFAULT nextval('role_permissions_id_seq')")
    
    # Populate existing rows with sequential ids
    op.execute("UPDATE role_permissions SET id = nextval('role_permissions_id_seq')")
    
    # Set the id column as primary key
    op.create_primary_key("role_permissions_pkey", "role_permissions", ["id"])
    
    # Add created_at and updated_at columns to match BaseModel
    op.add_column(
        "role_permissions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Creation timestamp"
        )
    )
    
    op.add_column(
        "role_permissions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Update timestamp"
        )
    )
    
    # Update existing rows to have current timestamp
    op.execute("UPDATE role_permissions SET created_at = granted_at WHERE created_at IS NULL")
    op.execute("UPDATE role_permissions SET updated_at = granted_at WHERE updated_at IS NULL")


def downgrade() -> None:
    # Drop the id primary key
    op.drop_constraint("role_permissions_pkey", "role_permissions", type_="primary")
    
    # Drop the columns
    op.drop_column("role_permissions", "updated_at")
    op.drop_column("role_permissions", "created_at")
    op.drop_column("role_permissions", "id")
    
    # Drop the sequence
    op.execute("DROP SEQUENCE IF EXISTS role_permissions_id_seq")
    
    # Recreate the composite primary key
    op.create_primary_key("role_permissions_pkey", "role_permissions", ["role_id", "permission_id"])