"""Basic organization schemas for user management."""

from pydantic import BaseModel


class OrganizationBasic(BaseModel):
    """Basic organization info for nested responses."""

    id: int
    code: str
    name: str

    class Config:
        from_attributes = True
