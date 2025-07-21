from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError

from app.api.errors import integrity_error_handler, validation_exception_handler
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.monitoring import (
    MonitoringMiddleware,
    setup_health_checks,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ITDO ERP System v2 - Modern ERP with GraphQL, Inventory Management, and Advanced Features",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization operations",
        },
        {
            "name": "Users",
            "description": "User management operations",
        },
        {
            "name": "Organizations",
            "description": "Organization and department management",
        },
        {
            "name": "GraphQL",
            "description": "GraphQL API endpoint with flexible querying",
        },
        {
            "name": "Inventory",
            "description": "Inventory and stock management operations",
        },
        {
            "name": "Orders",
            "description": "Order processing and management",
        },
        {
            "name": "Security",
            "description": "Security audit and monitoring features",
        },
        {
            "name": "Analytics",
            "description": "Reports and analytics endpoints",
        },
    ]
)

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

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
