from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1 import (  # permission_inheritance,  # Temporarily disabled due to syntax errors; role_permission_ui,  # Temporarily disabled due to syntax errors
    applications,
    audit,
    audit_logs,
    auth,
    budgets,
    cross_tenant_permissions,
    # crm_v31,  # CC02 v31.0 Phase 2 - CRM Management API - Temporarily disabled
    customer_activities,
    customers,
    departments,
    document_v31,  # CC02 v31.0 Phase 2 - Document Management API
    expense_categories,
    expenses,
    finance_v31,  # CC02 v31.0 Phase 2 - Finance Management API
    financial_reports,
    health,
    health_simple,  # v19.0 practical health check
    hr_v31,  # CC02 v31.0 Phase 2 - HR Management API
    inventory_basic,  # ERP v17.0 basic inventory
    multi_tenant,
    opportunities,
    organizations,
    organizations_basic,  # ERP v17.0 basic organizations
    organizations_simple,  # v19.0 practical organizations
    permission_management,
    pm_automation,
    products_basic,  # ERP v17.0 basic products
    products_simple,  # v19.0 practical products
    project_v31,  # CC02 v31.0 Phase 2 - Project Management API
    reports,
    roles,
    tasks,
    user_preferences,
    user_privacy,
    user_profile,
    users,
    users_basic,  # ERP v17.0 basic users
    users_extended,
    users_simple,  # v19.0 practical users
    workflows,
)
from app.api.v1.endpoints.monitoring.performance import router as performance_router

# New CC02 v35.0 API modules
from app.api.v1.endpoints.security.audit import router as security_audit_router
from app.core.database import get_db

api_router = APIRouter()

# Include routers
api_router.include_router(health.router)
api_router.include_router(
    health_simple.router, prefix="/simple", tags=["health-simple"]
)  # v19.0 practical
api_router.include_router(auth.router)
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(users.router)
api_router.include_router(users_basic.router)  # ERP v17.0 basic user API
api_router.include_router(users_extended.router)
api_router.include_router(
    users_simple.router, prefix="/simple", tags=["users-simple"]
)  # v19.0 practical
api_router.include_router(user_profile.router, tags=["user-profile"])
api_router.include_router(organizations.router)
api_router.include_router(
    organizations_basic.router
)  # ERP v17.0 basic organization API
api_router.include_router(
    organizations_simple.router, prefix="/simple", tags=["organizations-simple"]
)  # v19.0 practical
api_router.include_router(products_basic.router)  # ERP v17.0 basic product API
api_router.include_router(
    products_simple.router, prefix="/simple", tags=["products-simple"]
)  # v19.0 practical
api_router.include_router(inventory_basic.router)  # ERP v17.0 basic inventory API
api_router.include_router(departments.router)
api_router.include_router(roles.router)
api_router.include_router(permission_management.router)
api_router.include_router(audit_logs.router)
# api_router.include_router(
#     role_permission_ui.router, prefix="/role-permissions", tags=["role-permissions"]
# )
# api_router.include_router(
#     permission_inheritance.router,
#     prefix="/permission-inheritance",
#     tags=["permission-inheritance"],
# )
api_router.include_router(
    multi_tenant.router, prefix="/multi-tenant", tags=["multi-tenant"]
)
api_router.include_router(
    cross_tenant_permissions.router, prefix="/cross-tenant", tags=["cross-tenant"]
)
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(
    user_preferences.router, prefix="/users/preferences", tags=["user-preferences"]
)
api_router.include_router(
    user_privacy.router, prefix="/users/privacy", tags=["user-privacy"]
)
api_router.include_router(pm_automation.router)
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])

# Phase 6-7 Advanced Features (Issue #155)
api_router.include_router(budgets.router, prefix="/budgets", tags=["financial"])
api_router.include_router(customers.router, prefix="/customers", tags=["crm"])
api_router.include_router(
    customer_activities.router, prefix="/customer-activities", tags=["crm"]
)
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["crm"])
api_router.include_router(
    expense_categories.router, prefix="/expense-categories", tags=["financial"]
)
api_router.include_router(expenses.router, prefix="/expenses", tags=["financial"])
api_router.include_router(
    financial_reports.router, prefix="/financial-reports", tags=["financial"]
)
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflow"])
api_router.include_router(
    applications.router, prefix="/applications", tags=["workflow"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["analytics"])

# CC02 v35.0 - Security and Monitoring APIs
api_router.include_router(
    security_audit_router, prefix="/security/audit", tags=["security"]
)
api_router.include_router(
    performance_router, prefix="/monitoring/performance", tags=["monitoring"]
)

# CC02 v31.0 Phase 2 - Finance Management API
api_router.include_router(finance_v31.router, prefix="/finance", tags=["finance-v31"])

# CC02 v31.0 Phase 2 - HR Management API
api_router.include_router(hr_v31.router, prefix="/hr", tags=["hr-v31"])

# CC02 v31.0 Phase 2 - Project Management API
api_router.include_router(project_v31.router, prefix="/project", tags=["project-v31"])

# CC02 v31.0 Phase 2 - Document Management API
api_router.include_router(
    document_v31.router, prefix="/documents", tags=["document-v31"]
)

# CC02 v31.0 Phase 2 - Notification System API
from app.api.v1 import notification_v31

api_router.include_router(
    notification_v31.router, prefix="/notifications", tags=["notification-v31"]
)

# CC02 v31.0 Phase 2 - Analytics API
from app.api.v1 import analytics_v31

api_router.include_router(
    analytics_v31.router, prefix="/analytics", tags=["analytics-v31"]
)

# CC02 v31.0 Phase 2 - Integration API
from app.api.v1 import integration_v31

api_router.include_router(
    integration_v31.router, prefix="/integration", tags=["integration-v31"]
)

# CC02 v31.0 Phase 2 - Workflow API
from app.api.v1 import workflow_v31

api_router.include_router(
    workflow_v31.router, prefix="/workflow", tags=["workflow-v31"]
)

# CC02 v31.0 Phase 2 - Audit Log API
from app.api.v1 import audit_v31

api_router.include_router(audit_v31.router, prefix="/audit", tags=["audit-v31"])


@api_router.get("/ping")
async def ping() -> dict[str, str]:
    return {"message": "pong"}


@api_router.get("/db-test")
async def db_test(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        result = db.execute(text("SELECT 1 as test")).fetchone()
        return {"status": "success", "result": str(result[0]) if result else "None"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
