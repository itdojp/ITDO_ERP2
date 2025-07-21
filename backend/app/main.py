from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError

from app.api.errors import integrity_error_handler, validation_exception_handler
from app.api.v1.router import api_router
from app.api.v2.router import api_router_v2
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.monitoring import (
    MonitoringMiddleware,
    setup_health_checks,
)
from app.core.versioning import (
    VersionValidationMiddleware,
    DeprecationWarningMiddleware,
    version_manager,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

# Add API versioning middleware
app.add_middleware(VersionValidationMiddleware, version_manager=version_manager)
app.add_middleware(DeprecationWarningMiddleware, version_manager=version_manager)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(IntegrityError, integrity_error_handler)  # type: ignore[arg-type]

# APIルーターの登録
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router_v2, prefix="/api/v2")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize health checks and monitoring on startup."""
    setup_health_checks(app, SessionLocal, None)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "ITDO ERP System API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check for legacy compatibility."""
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint."""
    from app.core.monitoring import get_metrics

    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain")


@app.get("/api/v2/docs", include_in_schema=False)
async def get_v2_docs():
    """Custom documentation endpoint for API v2."""
    from fastapi.openapi.docs import get_swagger_ui_html
    
    return get_swagger_ui_html(
        openapi_url="/api/v2/openapi.json",
        title=f"{settings.PROJECT_NAME} - API v2 Documentation",
    )


@app.get("/api/v2/openapi.json", include_in_schema=False)
async def get_v2_openapi():
    """Custom OpenAPI schema endpoint for API v2."""
    from fastapi.openapi.utils import get_openapi
    
    if not hasattr(app, "_v2_openapi_schema"):
        app._v2_openapi_schema = get_openapi(
            title=f"{settings.PROJECT_NAME} - API v2",
            version="2.0.0",
            description="Enhanced ITDO ERP API with improved features",
            routes=api_router_v2.routes,
        )
    return app._v2_openapi_schema


@app.get("/api/versions")
async def get_api_versions():
    """Get information about all available API versions."""
    return {
        "supported_versions": version_manager.supported_versions,
        "default_version": version_manager.default_version,
        "versions": {
            "v1": {
                "description": "ITDO ERP API Version 1 - Initial release",
                "docs_url": "/api/v1/docs",
                "openapi_url": "/api/v1/openapi.json",
                "deprecated": version_manager.is_deprecated("v1"),
                "deprecation_info": version_manager.get_deprecation_info("v1")
            },
            "v2": {
                "description": "ITDO ERP API Version 2 - Enhanced features and performance",
                "docs_url": "/api/v2/docs",
                "openapi_url": "/api/v2/openapi.json",
                "deprecated": version_manager.is_deprecated("v2"),
                "deprecation_info": version_manager.get_deprecation_info("v2")
            }
        }
    }
