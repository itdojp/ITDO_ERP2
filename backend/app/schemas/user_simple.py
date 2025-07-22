from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    """User creation schema - v19.0 practical"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    """User response schema - v19.0 practical"""
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool

    class Config:
        orm_mode = True  # type: ignore[misc] - practical approach

class UserUpdate(BaseModel):
    """User update schema - v19.0 practical"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None