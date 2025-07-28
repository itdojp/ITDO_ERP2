"""
ITDO ERP v2 API Router Integration
"""

from fastapi import APIRouter

from app.api.v1 import auth, health, project_management, session, users

# Simple integration for v25
api_router = APIRouter()

# Include routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(session.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(
    project_management.router, prefix="/projects", tags=["project-management"]
)


# APIバージョン情報
@api_router.get("/version")
async def get_api_version() -> None:
    return {
        "version": "2.0.0",
        "name": "ITDO ERP API v25",
        "status": "active",
        "endpoints": [
            "/health",
            "/auth",
            "/users",
            "/sessions",
            "/projects",
            "/products",
            "/inventory",
            "/sales",
            "/reports",
            "/permissions",
            "/organizations",
        ],
    }
