from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1 import (
    auth,
    cross_tenant_permissions,
    departments,
    multi_tenant,
    organizations,
    permission_inheritance,
    role_permission_ui,
    roles,
    tasks,
    user_profile,
    users,
    users_extended,
)
from app.core.database import get_db

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(users_extended.router)
api_router.include_router(user_profile.router, tags=["user-profile"])
api_router.include_router(organizations.router)
api_router.include_router(departments.router)
api_router.include_router(roles.router)
api_router.include_router(role_permission_ui.router, prefix="/role-permissions", tags=["role-permissions"])
api_router.include_router(permission_inheritance.router, prefix="/permission-inheritance", tags=["permission-inheritance"])
api_router.include_router(multi_tenant.router, prefix="/multi-tenant", tags=["multi-tenant"])
api_router.include_router(cross_tenant_permissions.router, prefix="/cross-tenant", tags=["cross-tenant"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])


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
