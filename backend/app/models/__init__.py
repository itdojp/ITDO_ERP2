"""Database models package."""

from app.models.audit import AuditLog
from app.models.cross_tenant_permissions import (
    CrossTenantAuditLog,
    CrossTenantPermissionRule,
)
from app.models.customer import Customer, CustomerActivity, CustomerContact, Opportunity
from app.models.department import Department
from app.models.organization import Organization
from app.models.password_history import PasswordHistory
from app.models.permission import Permission
from app.models.permission_inheritance import (
    InheritanceAuditLog,
    InheritanceConflictResolution,
    PermissionDependency,
    RoleInheritanceRule,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_milestone import ProjectMilestone
from app.models.role import Role, RolePermission, UserRole
from app.models.task import Task, TaskDependency, TaskHistory
from app.models.user import User
from app.models.user_activity_log import UserActivityLog
from app.models.user_organization import (
    OrganizationInvitation,
    UserOrganization,
    UserTransferRequest,
)
from app.models.user_preferences import UserPreferences
from app.models.user_privacy import UserPrivacySettings
from app.models.user_session import UserSession

__all__ = [
    "User",
    "Organization",
    "Department",
    "Role",
    "UserRole",
    "RolePermission",
    "Permission",
    "PermissionDependency",
    "RoleInheritanceRule",
    "InheritanceConflictResolution",
    "InheritanceAuditLog",
    "PasswordHistory",
    "UserSession",
    "UserActivityLog",
    "UserPreferences",
    "UserPrivacySettings",
    "UserOrganization",
    "OrganizationInvitation",
    "UserTransferRequest",
    "CrossTenantPermissionRule",
    "CrossTenantAuditLog",
    "AuditLog",
    "Project",
    "ProjectMember",
    "ProjectMilestone",
    "Task",
    "TaskDependency",
    "TaskHistory",
    # Phase 5: CRM
    "Customer",
    "CustomerContact",
    "Opportunity",
    "CustomerActivity",
]
