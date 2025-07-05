"""Basic role schemas for user management."""

from pydantic import BaseModel


class RoleBasic(BaseModel):
    """Basic role info for nested responses."""
    
    id: int
    code: str
    name: str
    
    class Config:
        from_attributes = True