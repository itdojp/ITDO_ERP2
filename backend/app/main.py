from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from app.api.v1.router import api_router
from app.core.config import settings
from app.api.errors import validation_exception_handler, integrity_error_handler

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)

# APIルーターの登録
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "ITDO ERP System API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
