"""Error response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    detail: str = Field(..., description="Error detail message")
    code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")