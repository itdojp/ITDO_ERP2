"""Complete type-safe schema implementation.

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create comprehensive type-safe ERP schema."""

    # Update organizations table to full implementation
    op.drop_table("organizations")
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("business_type", sa.String(50), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(10), nullable=True),
        sa.Column("prefecture", sa.String(50), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("address_line1", sa.String(200), nullable=True),
        sa.Column("address_line2", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("fax", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("tax_number", sa.String(50), nullable=True),
        sa.Column("registration_number", sa.String(50), nullable=True),
        sa.Column("capital", sa.BigInteger(), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("fiscal_year_start", sa.String(5), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("settings", sa.JSON(), server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false"),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["organizations.id"], name="fk_organizations_parent"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_organizations_created_by"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.id"], name="fk_organizations_updated_by"
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name="fk_organizations_deleted_by"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_code", "organizations", ["code"], unique=True)
    op.create_index("ix_organizations_name", "organizations", ["name"])
    op.create_index("ix_organizations_parent_id", "organizations", ["parent_id"])
    op.create_index("ix_organizations_is_active", "organizations", ["is_active"])
    op.create_index("ix_organizations_is_deleted", "organizations", ["is_deleted"])

    # Create departments table
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("manager_id", sa.Integer(), nullable=True),
        sa.Column("department_type", sa.String(50), nullable=True),
        sa.Column("cost_center", sa.String(50), nullable=True),
        sa.Column("budget", sa.BigInteger(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_departments_organization",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["departments.id"], name="fk_departments_parent"
        ),
        sa.ForeignKeyConstraint(
            ["manager_id"], ["users.id"], name="fk_departments_manager"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_departments_created_by"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.id"], name="fk_departments_updated_by"
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name="fk_departments_deleted_by"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_departments_code_org",
        "departments",
        ["code", "organization_id"],
        unique=True,
    )
    op.create_index("ix_departments_name", "departments", ["name"])
    op.create_index(
        "ix_departments_organization_id", "departments", ["organization_id"]
    )
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
        sa.Column("is_system", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)
    op.create_index("ix_permissions_category", "permissions", ["category"])
    op.create_index("ix_permissions_is_system", "permissions", ["is_system"])

    # Create roles table
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("role_type", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("can_be_assigned", sa.Boolean(), server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], name="fk_roles_organization"
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["roles.id"], name="fk_roles_parent"),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_roles_created_by"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.id"], name="fk_roles_updated_by"
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name="fk_roles_deleted_by"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_roles_name_org", "roles", ["name", "organization_id"], unique=True
    )
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])
    op.create_index("ix_roles_parent_id", "roles", ["parent_id"])
    op.create_index("ix_roles_role_type", "roles", ["role_type"])
    op.create_index("ix_roles_is_active", "roles", ["is_active"])
    op.create_index("ix_roles_is_deleted", "roles", ["is_deleted"])

    # Create role_permissions table
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("granted_by", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_role_permissions_role",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permissions.id"], name="fk_role_permissions_permission"
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"], ["users.id"], name="fk_role_permissions_granted_by"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_role_permissions_role_perm",
        "role_permissions",
        ["role_id", "permission_id"],
        unique=True,
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index(
        "ix_role_permissions_permission_id", "role_permissions", ["permission_id"]
    )
    op.create_index("ix_role_permissions_is_active", "role_permissions", ["is_active"])

    # Create user_roles table
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column(
            "valid_from", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("assigned_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_roles_user", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_user_roles_role"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], name="fk_user_roles_organization"
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by"], ["users.id"], name="fk_user_roles_assigned_by"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_roles_user_role", "user_roles", ["user_id", "role_id"], unique=True
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index("ix_user_roles_organization_id", "user_roles", ["organization_id"])
    op.create_index("ix_user_roles_is_active", "user_roles", ["is_active"])
    op.create_index(
        "ix_user_roles_valid_period", "user_roles", ["valid_from", "valid_to"]
    )

    # Update users table with additional fields
    op.add_column("users", sa.Column("employee_code", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("department_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("updated_by", sa.Integer(), nullable=True))
    op.add_column(
        "users", sa.Column("is_deleted", sa.Boolean(), server_default="false")
    )

    # Create foreign keys for new user fields
    op.create_foreign_key(
        "fk_users_department", "users", "departments", ["department_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_users_organization", "users", "organizations", ["organization_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_users_updated_by", "users", "users", ["updated_by"], ["id"]
    )

    # Create indexes for new user fields
    op.create_index("ix_users_employee_code", "users", ["employee_code"], unique=True)
    op.create_index("ix_users_department_id", "users", ["department_id"])
    op.create_index("ix_users_organization_id", "users", ["organization_id"])
    op.create_index("ix_users_is_deleted", "users", ["is_deleted"])

    # Insert standard permissions
    permissions_data = [
        # Users permissions
        ("users.create", "Create Users", "Create new user accounts", "users"),
        ("users.read", "Read Users", "View user information", "users"),
        ("users.update", "Update Users", "Modify user information", "users"),
        ("users.delete", "Delete Users", "Delete user accounts", "users"),
        ("users.search", "Search Users", "Search and filter users", "users"),
        # Organizations permissions
        (
            "organizations.create",
            "Create Organizations",
            "Create new organizations",
            "organizations",
        ),
        (
            "organizations.read",
            "Read Organizations",
            "View organization information",
            "organizations",
        ),
        (
            "organizations.update",
            "Update Organizations",
            "Modify organization information",
            "organizations",
        ),
        (
            "organizations.delete",
            "Delete Organizations",
            "Delete organizations",
            "organizations",
        ),
        (
            "organizations.manage",
            "Manage Organizations",
            "Full organization management",
            "organizations",
        ),
        (
            "organizations.activate",
            "Activate Organizations",
            "Activate organizations",
            "organizations",
        ),
        (
            "organizations.deactivate",
            "Deactivate Organizations",
            "Deactivate organizations",
            "organizations",
        ),
        # Departments permissions
        (
            "departments.create",
            "Create Departments",
            "Create new departments",
            "departments",
        ),
        (
            "departments.read",
            "Read Departments",
            "View department information",
            "departments",
        ),
        (
            "departments.update",
            "Update Departments",
            "Modify department information",
            "departments",
        ),
        (
            "departments.delete",
            "Delete Departments",
            "Delete departments",
            "departments",
        ),
        (
            "departments.reorder",
            "Reorder Departments",
            "Change department display order",
            "departments",
        ),
        # Roles permissions
        ("roles.create", "Create Roles", "Create new roles", "roles"),
        ("roles.read", "Read Roles", "View role information", "roles"),
        ("roles.update", "Update Roles", "Modify role information", "roles"),
        ("roles.delete", "Delete Roles", "Delete roles", "roles"),
        ("roles.assign", "Assign Roles", "Assign roles to users", "roles"),
        ("roles.unassign", "Unassign Roles", "Remove roles from users", "roles"),
        (
            "roles.update_permissions",
            "Update Role Permissions",
            "Modify role permissions",
            "roles",
        ),
        # System permissions
        (
            "system.admin",
            "System Administration",
            "Full system administration",
            "system",
        ),
        (
            "system.config",
            "System Configuration",
            "Modify system configuration",
            "system",
        ),
        ("system.logs", "System Logs", "View system logs", "system"),
        ("system.backup", "System Backup", "Perform system backups", "system"),
        # Reports permissions
        ("reports.view", "View Reports", "View system reports", "reports"),
        (
            "reports.export",
            "Export Reports",
            "Export reports to various formats",
            "reports",
        ),
        (
            "reports.schedule",
            "Schedule Reports",
            "Schedule automated reports",
            "reports",
        ),
    ]

    # Insert permissions
    permissions_table = sa.table(
        "permissions",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("category", sa.String),
        sa.column("is_system", sa.Boolean),
    )

    for code, name, description, category in permissions_data:
        is_system = category == "system"
        op.execute(
            permissions_table.insert().values(
                code=code,
                name=name,
                description=description,
                category=category,
                is_system=is_system,
            )
        )


def downgrade() -> None:
    """Drop comprehensive type-safe ERP schema."""

    # Drop tables in reverse order of creation
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
    op.drop_table("departments")

    # Drop foreign keys from users table
    op.drop_constraint("fk_users_is_deleted", "users", type_="foreignkey")
    op.drop_constraint("fk_users_organization_id", "users", type_="foreignkey")
    op.drop_constraint("fk_users_department_id", "users", type_="foreignkey")
    op.drop_constraint("fk_users_updated_by", "users", type_="foreignkey")

    # Drop new columns from users table
    op.drop_column("users", "is_deleted")
    op.drop_column("users", "updated_by")
    op.drop_column("users", "organization_id")
    op.drop_column("users", "department_id")
    op.drop_column("users", "employee_code")

    # Recreate simple organizations table
    op.drop_table("organizations")
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_code", "organizations", ["code"], unique=True)
