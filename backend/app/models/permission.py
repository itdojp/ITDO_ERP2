"""Permission model for RBAC system."""

from typing import Optional

from sqlalchemy import Boolean, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Permission(BaseModel):
    """Permission model representing a specific action or access right."""

    __tablename__ = "permissions"

    # Unique permission code (e.g., "user.create", "project.view")
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique permission code",
    )

    # Human-readable name
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Permission display name"
    )

    # Detailed description
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Permission description"
    )

    # Category for grouping (e.g., "user", "project", "admin")
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Permission category"
    )

    # Whether this permission is active
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether permission is active"
    )

    # System permission that cannot be modified
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this is a system permission",
    )

    # Relationships - simplified to avoid complex RolePermission model
    # For now, permissions are managed directly in Role.permissions JSON field

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("code", name="uq_permissions_code"),
        Index("ix_permissions_category_active", "category", "is_active"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Permission(code='{self.code}', name='{self.name}', "
            f"category='{self.category}')>"
        )

    @property
    def full_code(self) -> str:
        """Get full permission code with category."""
        return f"{self.category}.{self.code}"

    def is_admin_permission(self) -> bool:
        """Check if this is an admin permission."""
        return self.category == "admin" or self.code.startswith("admin.")


# Predefined system permissions
SYSTEM_PERMISSIONS = [
    # User management
    {
        "code": "user.view",
        "name": "View Users",
        "category": "user",
        "description": "View user information",
    },
    {
        "code": "user.create",
        "name": "Create Users",
        "category": "user",
        "description": "Create new users",
    },
    {
        "code": "user.edit",
        "name": "Edit Users",
        "category": "user",
        "description": "Edit user information",
    },
    {
        "code": "user.delete",
        "name": "Delete Users",
        "category": "user",
        "description": "Delete users",
    },
    # Role management
    {
        "code": "role.view",
        "name": "View Roles",
        "category": "role",
        "description": "View role information",
    },
    {
        "code": "role.create",
        "name": "Create Roles",
        "category": "role",
        "description": "Create new roles",
    },
    {
        "code": "role.edit",
        "name": "Edit Roles",
        "category": "role",
        "description": "Edit role information",
    },
    {
        "code": "role.delete",
        "name": "Delete Roles",
        "category": "role",
        "description": "Delete roles",
    },
    {
        "code": "role.assign",
        "name": "Assign Roles",
        "category": "role",
        "description": "Assign roles to users",
    },
    # Organization management
    {
        "code": "org.view",
        "name": "View Organizations",
        "category": "organization",
        "description": "View organization information",
    },
    {
        "code": "org.create",
        "name": "Create Organizations",
        "category": "organization",
        "description": "Create new organizations",
    },
    {
        "code": "org.edit",
        "name": "Edit Organizations",
        "category": "organization",
        "description": "Edit organization information",
    },
    {
        "code": "org.delete",
        "name": "Delete Organizations",
        "category": "organization",
        "description": "Delete organizations",
    },
    # Department management
    {
        "code": "dept.view",
        "name": "View Departments",
        "category": "department",
        "description": "View department information",
    },
    {
        "code": "dept.create",
        "name": "Create Departments",
        "category": "department",
        "description": "Create new departments",
    },
    {
        "code": "dept.edit",
        "name": "Edit Departments",
        "category": "department",
        "description": "Edit department information",
    },
    {
        "code": "dept.delete",
        "name": "Delete Departments",
        "category": "department",
        "description": "Delete departments",
    },
    # Project management
    {
        "code": "project.view",
        "name": "View Projects",
        "category": "project",
        "description": "View project information",
    },
    {
        "code": "project.create",
        "name": "Create Projects",
        "category": "project",
        "description": "Create new projects",
    },
    {
        "code": "project.edit",
        "name": "Edit Projects",
        "category": "project",
        "description": "Edit project information",
    },
    {
        "code": "project.delete",
        "name": "Delete Projects",
        "category": "project",
        "description": "Delete projects",
    },
    # Task management
    {
        "code": "task.view",
        "name": "View Tasks",
        "category": "task",
        "description": "View task information",
    },
    {
        "code": "task.create",
        "name": "Create Tasks",
        "category": "task",
        "description": "Create new tasks",
    },
    {
        "code": "task.edit",
        "name": "Edit Tasks",
        "category": "task",
        "description": "Edit task information",
    },
    {
        "code": "task.delete",
        "name": "Delete Tasks",
        "category": "task",
        "description": "Delete tasks",
    },
    # Admin permissions
    {
        "code": "admin.all",
        "name": "Full Admin Access",
        "category": "admin",
        "description": "Full system administration access",
    },
    {
        "code": "admin.audit",
        "name": "View Audit Logs",
        "category": "admin",
        "description": "View system audit logs",
    },
    {
        "code": "admin.settings",
        "name": "Manage Settings",
        "category": "admin",
        "description": "Manage system settings",
    },
]
