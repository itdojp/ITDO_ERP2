"""Error response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str = Field(..., description="Error detail message")
    code: str = Field(..., description="Error code")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )

    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime) -> str:
        """Serialize timestamp as ISO format string."""
        return timestamp.isoformat()
