"""Add permission models

Revision ID: 004_add_permission_models
Revises: 003_complete_type_safe_schema
Create Date: 2025-01-07

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create permissions table
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "code", sa.String(100), nullable=False, comment="Unique permission code"
        ),
        sa.Column(
            "name", sa.String(200), nullable=False, comment="Permission display name"
        ),
        sa.Column(
            "description", sa.Text(), nullable=True, comment="Permission description"
        ),
        sa.Column(
            "category", sa.String(50), nullable=False, comment="Permission category"
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether permission is active",
        ),
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether this is a system permission",
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])
    op.create_index(
        "ix_permissions_category_active", "permissions", ["category", "is_active"]
    )

    # Create role_permissions association table
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False, comment="Role ID"),
        sa.Column(
            "permission_id", sa.Integer(), nullable=False, comment="Permission ID"
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="When permission was granted",
        ),
        sa.Column(
            "granted_by",
            sa.Integer(),
            nullable=True,
            comment="User who granted the permission",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )
    op.create_index(
        "ix_role_permissions_permission_id", "role_permissions", ["permission_id"]
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])

    # Add missing columns to roles table
    op.add_column(
        "roles",
        sa.Column(
            "organization_id",
            sa.Integer(),
            nullable=True,
            comment="Organization ID if role is organization-specific",
        ),
    )
    op.add_column(
        "roles",
        sa.Column(
            "full_path",
            sa.String(500),
            nullable=False,
            server_default="/",
            comment="Full path in hierarchy (e.g., /1/2/3)",
        ),
    )
    op.add_column(
        "roles",
        sa.Column(
            "depth",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Depth in hierarchy (0 for root)",
        ),
    )

    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])
    op.create_foreign_key(
        "fk_roles_organization_id",
        "roles",
        "organizations",
        ["organization_id"],
        ["id"],
    )

    # Add valid_to column to user_roles table
    op.add_column(
        "user_roles",
        sa.Column(
            "valid_to",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the role validity ends (deprecated, use expires_at)",
        ),
    )


def downgrade() -> None:
    # Remove columns from user_roles
    op.drop_column("user_roles", "valid_to")

    # Remove columns and constraints from roles
    op.drop_constraint("fk_roles_organization_id", "roles", type_="foreignkey")
    op.drop_index("ix_roles_organization_id", table_name="roles")
    op.drop_column("roles", "depth")
    op.drop_column("roles", "full_path")
    op.drop_column("roles", "organization_id")

    # Drop tables
    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index("ix_permissions_category_active", table_name="permissions")
    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")
