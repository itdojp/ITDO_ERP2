"""Basic department schemas for user management."""

from pydantic import BaseModel


class DepartmentBasic(BaseModel):
    """Basic department info for nested responses."""
    
    id: int
    code: str
    name: str
    
    class Config:
        from_attributes = True