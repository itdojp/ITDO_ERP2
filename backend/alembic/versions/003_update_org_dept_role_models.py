"""Update organization, department, and role models

Revision ID: 003
Revises: 002
Create Date: 2025-01-06

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update organization, department, and role models with new fields."""

    # Add new fields to organizations table
    op.add_column(
        "organizations", sa.Column("name_kana", sa.String(200), nullable=True)
    )
    op.add_column("organizations", sa.Column("name_en", sa.String(200), nullable=True))
    op.add_column("organizations", sa.Column("phone", sa.String(20), nullable=True))
    op.add_column("organizations", sa.Column("fax", sa.String(20), nullable=True))
    op.add_column("organizations", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("organizations", sa.Column("website", sa.String(255), nullable=True))
    op.add_column(
        "organizations", sa.Column("postal_code", sa.String(10), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("prefecture", sa.String(50), nullable=True)
    )
    op.add_column("organizations", sa.Column("city", sa.String(100), nullable=True))
    op.add_column(
        "organizations", sa.Column("address_line1", sa.String(255), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("address_line2", sa.String(255), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("business_type", sa.String(100), nullable=True)
    )
    op.add_column("organizations", sa.Column("industry", sa.String(100), nullable=True))
    op.add_column("organizations", sa.Column("capital", sa.Integer(), nullable=True))
    op.add_column(
        "organizations", sa.Column("employee_count", sa.Integer(), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("fiscal_year_end", sa.String(5), nullable=True)
    )
    op.add_column("organizations", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.add_column("organizations", sa.Column("settings", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("logo_url", sa.String(255), nullable=True))
    op.add_column(
        "organizations", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("organizations", sa.Column("deleted_by", sa.Integer(), nullable=True))
    op.add_column(
        "organizations",
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column("organizations", sa.Column("created_by", sa.Integer(), nullable=True))
    op.add_column("organizations", sa.Column("updated_by", sa.Integer(), nullable=True))

    # Add foreign keys for organizations
    op.create_foreign_key(
        "fk_organizations_parent", "organizations", "organizations", ["parent_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_organizations_deleted_by", "organizations", "users", ["deleted_by"], ["id"]
    )
    op.create_foreign_key(
        "fk_organizations_created_by", "organizations", "users", ["created_by"], ["id"]
    )
    op.create_foreign_key(
        "fk_organizations_updated_by", "organizations", "users", ["updated_by"], ["id"]
    )

    # Add indexes for organizations
    op.create_index("ix_organizations_code", "organizations", ["code"], unique=True)
    op.create_index("ix_organizations_parent_id", "organizations", ["parent_id"])
    op.create_index("ix_organizations_is_active", "organizations", ["is_active"])
    op.create_index("ix_organizations_is_deleted", "organizations", ["is_deleted"])

    # Create departments table
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_kana", sa.String(200), nullable=True),
        sa.Column("name_en", sa.String(200), nullable=True),
        sa.Column("short_name", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("manager_id", sa.Integer(), nullable=True),
        sa.Column("department_type", sa.String(50), nullable=True),
        sa.Column("cost_center_code", sa.String(50), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0"),
        sa.Column("headcount_limit", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["deleted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_departments_org_code"),
    )

    # Add indexes for departments
    op.create_index("ix_departments_organization_id", "departments", ["organization_id"])
    op.create_index("ix_departments_parent_id", "departments", ["parent_id"])
    op.create_index("ix_departments_manager_id", "departments", ["manager_id"])
    op.create_index("ix_departments_is_active", "departments", ["is_active"])
    op.create_index("ix_departments_is_deleted", "departments", ["is_deleted"])
    op.create_index("ix_departments_display_order", "departments", ["display_order"])

    # Create permissions table
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_system", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )

    # Add indexes for permissions
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)
    op.create_index("ix_permissions_category", "permissions", ["category"])
    op.create_index(
        "ix_permissions_category_active", "permissions", ["category", "is_active"]
    )

    # Create roles table
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("role_type", sa.String(50), server_default="custom"),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("permissions", JSON(), server_default="{}"),
        sa.Column("is_system", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("display_order", sa.Integer(), server_default="0"),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["deleted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    # Add indexes for roles
    op.create_index("ix_roles_code", "roles", ["code"], unique=True)
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])
    op.create_index("ix_roles_parent_id", "roles", ["parent_id"])
    op.create_index("ix_roles_role_type", "roles", ["role_type"])
    op.create_index("ix_roles_is_active", "roles", ["is_active"])
    op.create_index("ix_roles_is_deleted", "roles", ["is_deleted"])
    op.create_index("ix_roles_is_system", "roles", ["is_system"])

    # Create role_permissions table
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("granted_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )

    # Add indexes for role_permissions
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index(
        "ix_role_permissions_permission_id", "role_permissions", ["permission_id"]
    )

    # Create user_roles table
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("assigned_by", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("valid_from", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_primary", sa.Boolean(), server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approval_status", sa.String(50), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add indexes for user_roles
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index("ix_user_roles_organization_id", "user_roles", ["organization_id"])
    op.create_index("ix_user_roles_department_id", "user_roles", ["department_id"])
    op.create_index("ix_user_roles_is_active", "user_roles", ["is_active"])
    op.create_index("ix_user_roles_is_primary", "user_roles", ["is_primary"])
    op.create_index("ix_user_roles_expires_at", "user_roles", ["expires_at"])

    # Add department_id to users table
    op.add_column("users", sa.Column("department_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_department", "users", "departments", ["department_id"], ["id"]
    )
    op.create_index("ix_users_department_id", "users", ["department_id"])


def downgrade() -> None:
    """Remove organization, department, and role model updates."""

    # Drop department_id from users
    op.drop_constraint("fk_users_department", "users", type_="foreignkey")
    op.drop_index("ix_users_department_id", "users")
    op.drop_column("users", "department_id")

    # Drop user_roles table
    op.drop_table("user_roles")

    # Drop role_permissions table
    op.drop_table("role_permissions")

    # Drop roles table
    op.drop_table("roles")

    # Drop permissions table
    op.drop_table("permissions")

    # Drop departments table
    op.drop_table("departments")

    # Drop foreign keys and indexes for organizations
    op.drop_constraint("fk_organizations_parent", "organizations", type_="foreignkey")
    op.drop_constraint(
        "fk_organizations_deleted_by", "organizations", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_organizations_created_by", "organizations", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_organizations_updated_by", "organizations", type_="foreignkey"
    )
    op.drop_index("ix_organizations_code", "organizations")
    op.drop_index("ix_organizations_parent_id", "organizations")
    op.drop_index("ix_organizations_is_active", "organizations")
    op.drop_index("ix_organizations_is_deleted", "organizations")

    # Remove columns from organizations
    op.drop_column("organizations", "updated_by")
    op.drop_column("organizations", "created_by")
    op.drop_column("organizations", "is_deleted")
    op.drop_column("organizations", "deleted_by")
    op.drop_column("organizations", "deleted_at")
    op.drop_column("organizations", "logo_url")
    op.drop_column("organizations", "description")
    op.drop_column("organizations", "settings")
    op.drop_column("organizations", "parent_id")
    op.drop_column("organizations", "fiscal_year_end")
    op.drop_column("organizations", "employee_count")
    op.drop_column("organizations", "capital")
    op.drop_column("organizations", "industry")
    op.drop_column("organizations", "business_type")
    op.drop_column("organizations", "address_line2")
    op.drop_column("organizations", "address_line1")
    op.drop_column("organizations", "city")
    op.drop_column("organizations", "prefecture")
    op.drop_column("organizations", "postal_code")
    op.drop_column("organizations", "website")
    op.drop_column("organizations", "email")
    op.drop_column("organizations", "fax")
    op.drop_column("organizations", "phone")
    op.drop_column("organizations", "name_en")
    op.drop_column("organizations", "name_kana")