"""API error handlers."""

from datetime import datetime

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.schemas.error import ErrorResponse


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "code": "VALIDATION_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """Handle database integrity errors."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(
            detail="Database integrity error",
            code="DATABASE_ERROR",
            timestamp=datetime.utcnow(),
        ).model_dump(),
    )
