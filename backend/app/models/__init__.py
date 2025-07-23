"""Database models package."""

from app.models.analytics import (
    Dashboard,
    DashboardWidget,
    DataSource,
    Report,
    ReportExecution,
    ReportWidget,
)
from app.models.audit import AuditLog
from app.models.budget import Budget, BudgetItem
from app.models.cross_tenant_permissions import (
    CrossTenantAuditLog,
    CrossTenantPermissionRule,
)
from app.models.customer import Customer, CustomerActivity, CustomerContact, Opportunity
from app.models.department import Department

# Phase 4-7 Models
from app.models.expense import Expense, ExpenseApprovalFlow
from app.models.expense_category import ExpenseCategory

# CC02 v31.0 Phase 2 - Finance Management Models
from app.models.finance_extended import (
    Account,
    Budget as FinanceBudget,
    BudgetLine,
    CostCenter,
    FinanceAuditLog,
    FinancialPeriod,
    FinancialReport,
    JournalEntry,
    JournalEntryLine,
    TaxConfiguration,
)

# CC02 v31.0 Phase 2 - HR Management Models
from app.models.hr_extended import (
    Employee,
    EmployeeBenefit,
    HRAnalytics,
    JobPosting,
    LeaveRequest,
    OnboardingRecord,
    PayrollRecord,
    PerformanceReview,
    Position,
    TrainingRecord,
)

# CC02 v31.0 Phase 2 - Project Management Models
from app.models.project_extended import (
    ProjectDeliverable,
    ProjectExtended,
    ProjectIssue,
    ProjectMilestoneExtended,
    ProjectPortfolio,
    ProjectResource,
    ProjectRisk,
    ProjectTemplate,
    TaskComment,
    TaskDependencyExtended,
    TaskExtended,
    TimeEntry,
)

# CC02 v31.0 Phase 2 - CRM Management Models
from app.models.crm_extended import (
    CampaignExtended,
    ContactExtended,
    CRMActivity,
    CRMAnalytics,
    CustomerExtended,
    LeadExtended,
    OpportunityExtended,
    SupportTicket,
)

# CC02 v31.0 Phase 2 - Document Management Models
from app.models.document_extended import (
    DocumentActivity,
    DocumentAnalytics,
    DocumentApproval,
    DocumentComment,
    DocumentExtended,
    DocumentFolder,
    DocumentFolderPermission,
    DocumentShare,
    DocumentSignature,
    DocumentTemplate,
    DocumentWorkflow,
)
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
from app.models.workflow import (
    Workflow,
    WorkflowConnection,
    WorkflowInstance,
    WorkflowNode,
    WorkflowTask,
)

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
    # Phase 4-7 Models
    "Budget",
    "BudgetItem",
    "ExpenseCategory",
    "Expense",
    "ExpenseApprovalFlow",
    "Customer",
    "CustomerContact",
    "Opportunity",
    "CustomerActivity",
    "Workflow",
    "WorkflowNode",
    "WorkflowConnection",
    "WorkflowInstance",
    "WorkflowTask",
    "Report",
    "ReportWidget",
    "Dashboard",
    "DashboardWidget",
    "ReportExecution",
    "DataSource",
    # CC02 v31.0 Phase 2 - Finance Management Models
    "Account",
    "FinanceBudget",
    "BudgetLine",
    "CostCenter",
    "FinanceAuditLog",
    "FinancialPeriod", 
    "FinancialReport",
    "JournalEntry",
    "JournalEntryLine",
    "TaxConfiguration",
    # CC02 v31.0 Phase 2 - HR Management Models
    "Employee",
    "EmployeeBenefit",
    "HRAnalytics",
    "JobPosting",
    "LeaveRequest",
    "OnboardingRecord",
    "PayrollRecord",
    "PerformanceReview",
    "Position",
    "TrainingRecord",
    # CC02 v31.0 Phase 2 - Project Management Models
    "ProjectDeliverable",
    "ProjectExtended",
    "ProjectIssue",
    "ProjectMilestoneExtended",
    "ProjectPortfolio",
    "ProjectResource",
    "ProjectRisk",
    "ProjectTemplate",
    "TaskComment",
    "TaskDependencyExtended",
    "TaskExtended",
    "TimeEntry",
    # CC02 v31.0 Phase 2 - CRM Management Models
    "CampaignExtended",
    "ContactExtended",
    "CRMActivity",
    "CRMAnalytics",
    "CustomerExtended",
    "LeadExtended",
    "OpportunityExtended",
    "SupportTicket",
    # CC02 v31.0 Phase 2 - Document Management Models
    "DocumentActivity",
    "DocumentAnalytics",
    "DocumentApproval",
    "DocumentComment",
    "DocumentExtended",
    "DocumentFolder",
    "DocumentFolderPermission",
    "DocumentShare",
    "DocumentSignature",
    "DocumentTemplate",
    "DocumentWorkflow",
]
