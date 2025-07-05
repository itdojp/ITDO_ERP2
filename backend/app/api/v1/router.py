from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.api.v1 import auth, users, auth_keycloak, admin, manager

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(auth_keycloak.router, prefix="/auth/keycloak", tags=["keycloak"])
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(manager.router)


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
