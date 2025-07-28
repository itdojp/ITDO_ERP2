"""Database models package."""

from app.models.analytics import (
    Dashboard,
    DashboardWidget,
    DataSource,
    Report,
    ReportExecution,
    ReportWidget,
)

# CC02 v31.0 Phase 2 - Analytics System Models
from app.models.analytics_extended import (
    AnalyticsAlert,
    AnalyticsAuditLog,
    AnalyticsDashboard,
    AnalyticsDataPoint,
    AnalyticsDataSource,
    AnalyticsInsight,
    AnalyticsMetric,
    AnalyticsPrediction,
    AnalyticsReport,
    AnalyticsReportExecution,
)
from app.models.audit import AuditLog
from app.models.cross_tenant_permissions import (
    CrossTenantAuditLog,
    CrossTenantPermissionRule,
)
from app.models.department import Department

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

# Phase 4-7 Models
from app.models.expense import Expense, ExpenseApprovalFlow
from app.models.expense_category import ExpenseCategory

# CC02 v31.0 Phase 2 - Finance Management Models
from app.models.finance_extended import (
    Account,
    BudgetLine,
    CostCenter,
    FinanceAuditLog,
    FinancialPeriod,
    FinancialReport,
    JournalEntry,
    JournalEntryLine,
    TaxConfiguration,
)
from app.models.finance_extended import Budget as FinanceBudget

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

# CC02 v31.0 Phase 2 - Integration System Models
from app.models.integration_extended import (
    DataMapping,
    DataTransformation,
    ExternalSystem,
    IntegrationAuditLog,
    IntegrationConnector,
    IntegrationExecution,
    IntegrationMessage,
    WebhookEndpoint,
    WebhookRequest,
)
from app.models.mfa import MFABackupCode, MFAChallenge, MFADevice

# CC02 v31.0 Phase 2 - Notification System Models
from app.models.notification_extended import (
    NotificationAnalytics,
    NotificationDelivery,
    NotificationEvent,
    NotificationExtended,
    NotificationInteraction,
    NotificationPreference,
    NotificationQueue,
    NotificationRule,
    NotificationSubscription,
    NotificationTemplate,
)
from app.models.organization import Organization
from app.models.password_history import PasswordHistory

# CC02 v60.0 - Payment Processing Models
from app.models.payment_processing import (
    PaymentAnalytics,
    PaymentMethod,
    PaymentMethodInfo,
    PaymentProcessingLog,
    PaymentProvider,
    PaymentProviderConfig,
    PaymentRefund,
    PaymentStatus,
    PaymentTransaction,
    RefundReason,
)
from app.models.permission import Permission
from app.models.permission_inheritance import (
    InheritanceAuditLog,
    InheritanceConflictResolution,
    PermissionDependency,
    RoleInheritanceRule,
)
from app.models.project import Project

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

# Project Management Models (Issue #646)
from app.models.project_management import (
    Milestone,
    ProjectBudget,
    RecurringProjectInstance,
    RecurringProjectTemplate,
    TaskProgress,
    TaskResource,
)
from app.models.project_management import (
    Project as ProjectManagement,
)
from app.models.project_management import (
    ProjectMember as ProjectManagementMember,
)
from app.models.project_management import (
    Task as ProjectTask,
)
from app.models.project_management import (
    TaskDependency as ProjectTaskDependency,
)
from app.models.project_member import ProjectMember
from app.models.project_milestone import ProjectMilestone
from app.models.role import Role, RolePermission, UserRole
from app.models.session import SessionActivity, SessionConfiguration, UserSession
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
from app.models.workflow import (
    Workflow,
    WorkflowConnection,
    WorkflowInstance,
    WorkflowNode,
    WorkflowTask,
)

# CC02 v31.0 Phase 2 - Workflow System Models
from app.models.workflow_extended import (
    WorkflowActivity,
    WorkflowAnalytics,
    WorkflowAttachment,
    WorkflowAuditLog,
    WorkflowComment,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowStep,
    WorkflowTask,
    WorkflowTemplate,
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
    "MFADevice",
    "MFABackupCode",
    "MFAChallenge",
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
    # CC02 v31.0 Phase 2 - Notification System Models
    "NotificationExtended",
    "NotificationTemplate",
    "NotificationDelivery",
    "NotificationPreference",
    "NotificationSubscription",
    "NotificationInteraction",
    "NotificationEvent",
    "NotificationRule",
    "NotificationQueue",
    "NotificationAnalytics",
    # CC02 v31.0 Phase 2 - Analytics System Models
    "AnalyticsDataSource",
    "AnalyticsMetric",
    "AnalyticsDataPoint",
    "AnalyticsDashboard",
    "AnalyticsReport",
    "AnalyticsReportExecution",
    "AnalyticsAlert",
    "AnalyticsPrediction",
    "AnalyticsInsight",
    "AnalyticsAuditLog",
    # CC02 v31.0 Phase 2 - Integration System Models
    "ExternalSystem",
    "IntegrationConnector",
    "DataMapping",
    "DataTransformation",
    "IntegrationExecution",
    "WebhookEndpoint",
    "WebhookRequest",
    "IntegrationMessage",
    "IntegrationAuditLog",
    # CC02 v31.0 Phase 2 - Workflow System Models
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowInstance",
    "WorkflowTask",
    "WorkflowActivity",
    "WorkflowComment",
    "WorkflowAttachment",
    "WorkflowTemplate",
    "WorkflowAnalytics",
    "WorkflowAuditLog",
    # CC02 v31.0 Phase 2 - Audit Log System Models
    "AuditLogEntry",
    "AuditRule",
    "AuditAlert",
    "AuditReport",
    "AuditSession",
    "AuditDataRetention",
    "AuditCompliance",
    "AuditConfiguration",
    "AuditMetrics",
    # CC02 v60.0 - Payment Processing Models
    "PaymentTransaction",
    "PaymentMethodInfo",
    "PaymentRefund",
    "PaymentProcessingLog",
    "PaymentProviderConfig",
    "PaymentAnalytics",
    "PaymentStatus",
    "PaymentMethod",
    "PaymentProvider",
    "RefundReason",
    # Project Management Models (Issue #646)
    "ProjectManagement",
    "ProjectManagementMember",
    "ProjectTask",
    "ProjectTaskDependency",
    "TaskProgress",
    "TaskResource",
    "Milestone",
    "ProjectBudget",
    "RecurringProjectTemplate",
    "RecurringProjectInstance",
]
