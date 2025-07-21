from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1 import (
    advanced_api_security,
    advanced_graphql,
    advanced_search,
    api_versioning,
    applications,
    audit,
    audit_logs,
    auth,
    budgets,
    business_intelligence,
    cache_management,
    comprehensive_audit,
    comprehensive_security_audit,
    cross_tenant_permissions,
    customer_activities,
    customer_import_export,
    customers,
    data_pipeline,
    departments,
    distributed_cache,
    enhanced_security_monitoring,
    event_api,
    expense_categories,
    expenses,
    financial_reports,
    graphql,
    health,
    inventory,
    microservices_management,
    multi_tenant,
    multi_tenant_performance,
    notifications,
    opportunities,
    organizations,
    password_security,
    # permission_inheritance,  # Temporarily disabled due to syntax errors
    permission_management,
    pm_automation,
    reports,
    # role_permission_ui,  # Temporarily disabled due to syntax errors
    roles,
    sales_analytics,
    security_compliance,
    tasks,
    user_preferences,
    user_privacy,
    user_profile,
    users,
    users_extended,
    websocket_api,
    workflow_automation,
    workflows,
)
from app.core.database import get_db

api_router = APIRouter()

# Include routers
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(users.router)
api_router.include_router(users_extended.router)
api_router.include_router(user_profile.router, tags=["user-profile"])
api_router.include_router(organizations.router)
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
api_router.include_router(
    password_security.router, prefix="/password-security", tags=["security", "password"]
)
api_router.include_router(
    enhanced_security_monitoring.router, prefix="/security-monitoring", tags=["security", "monitoring"]
)
api_router.include_router(
    comprehensive_security_audit.router, prefix="/api/v1", tags=["security", "audit"]
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
api_router.include_router(
    sales_analytics.router, prefix="/sales-analytics", tags=["crm", "analytics"]
)
api_router.include_router(
    customer_import_export.router,
    prefix="/customer-import-export",
    tags=["crm", "data-management"]
)

# GraphQL API endpoint
api_router.include_router(
    graphql.graphql_app, 
    prefix="/graphql", 
    tags=["graphql", "api"]
)

# Inventory Management API
api_router.include_router(
    inventory.router, 
    tags=["inventory", "stock-management"]
)

# Notification System API
api_router.include_router(
    notifications.router, 
    prefix="/notifications",
    tags=["notifications", "communication"]
)

# API Versioning System
api_router.include_router(
    api_versioning.router,
    prefix="/api-versioning",
    tags=["versioning", "management"]
)

# Comprehensive Audit System
api_router.include_router(
    comprehensive_audit.router,
    prefix="/comprehensive-audit",
    tags=["audit", "compliance", "security"]
)

# Microservices Management
api_router.include_router(
    microservices_management.router,
    prefix="/microservices",
    tags=["microservices", "service-discovery", "gateway"]
)

# Advanced Cache Management
api_router.include_router(
    cache_management.router,
    prefix="/cache",
    tags=["cache", "performance", "multi-level"]
)

# Multi-Tenant Performance Optimization
api_router.include_router(
    multi_tenant_performance.router,
    prefix="/performance",
    tags=["performance", "multi-tenant", "optimization"]
)

# Business Intelligence & Analytics
api_router.include_router(
    business_intelligence.router,
    prefix="/bi",
    tags=["business-intelligence", "analytics", "reporting"]
)

# Data Pipeline & ETL Processing
api_router.include_router(
    data_pipeline.router,
    prefix="/data-pipeline",
    tags=["data-pipeline", "etl", "data-processing"]
)

# Enterprise Security & Compliance
api_router.include_router(
    security_compliance.router,
    prefix="/security",
    tags=["security", "compliance", "enterprise"]
)

# Workflow Automation & Integration
api_router.include_router(
    workflow_automation.router,
    prefix="/workflow-automation",
    tags=["workflow", "automation", "integration"]
)

# Advanced API Security & Protection
api_router.include_router(
    advanced_api_security.router,
    prefix="/api-security",
    tags=["api-security", "protection", "rate-limiting"]
)

# Advanced GraphQL Features
api_router.include_router(
    advanced_graphql.router,
    prefix="/advanced-graphql",
    tags=["graphql", "advanced", "federation", "analytics"]
)

# Advanced Search & Indexing
api_router.include_router(
    advanced_search.router,
    prefix="/advanced-search",
    tags=["search", "indexing", "full-text", "analytics"]
)

# Distributed Cache Management
api_router.include_router(
    distributed_cache.router,
    prefix="/distributed-cache",
    tags=["cache", "distributed", "performance"]
)

# Real-time WebSocket API
api_router.include_router(
    websocket_api.router,
    prefix="/websocket",
    tags=["websocket", "real-time", "messaging"]
)

# Event-Driven Architecture
api_router.include_router(
    event_api.router,
    prefix="/events",
    tags=["events", "event-driven", "architecture"]
)


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
