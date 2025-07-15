"""Type definitions for the application."""

from typing import NewType

# ID types for type safety
UserId = NewType("UserId", int)
OrganizationId = NewType("OrganizationId", int)
DepartmentId = NewType("DepartmentId", int)
RoleId = NewType("RoleId", int)
PermissionId = NewType("PermissionId", int)
ProjectId = NewType("ProjectId", int)
TaskId = NewType("TaskId", int)
