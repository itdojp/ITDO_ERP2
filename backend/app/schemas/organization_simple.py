from typing import Optional

from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    """Organization creation schema - v19.0 practical"""
    name: str
    code: str
    description: Optional[str] = None

class OrganizationResponse(BaseModel):
    """Organization response schema - v19.0 practical"""
    id: str
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        orm_mode = True  # type: ignore[misc] - practical approach

class OrganizationUpdate(BaseModel):
    """Organization update schema - v19.0 practical"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
