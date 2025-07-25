from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1 import (
    audit,
    auth,
    cross_tenant_permissions,
    departments,
    health,
    multi_tenant,
    organizations,
    payment_processing,
    permission_inheritance,
    pm_automation,
    role_permission_ui,
    roles,
    tasks,
    user_preferences,
    user_privacy,
    user_profile,
    users,
    users_extended,
)

# New CC02 v35.0 API modules
from app.core.database import get_db

api_router = APIRouter()

# Include routers
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(users.router)
api_router.include_router(users_basic.router)  # ERP v17.0 basic user API
api_router.include_router(users_extended.router)
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
api_router.include_router(
    role_permission_ui.router, prefix="/role-permissions", tags=["role-permissions"]
)
api_router.include_router(
    permission_inheritance.router,
    prefix="/permission-inheritance",
    tags=["permission-inheritance"],
)
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
# CC02 v60.0 - Payment Processing API
api_router.include_router(payment_processing.router)


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
