import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    employee_id: Optional[str] = None

    @validator("username")
    def username_valid(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username must contain only letters, numbers, hyphens and underscores"
            )
        return v

    @validator("phone_number")
    def phone_valid(cls, v):
        if v and not re.match(r"^\+?1?\d{9,15}$", v):
            raise ValueError("Invalid phone number format")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    confirm_password: str

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

    @validator("password")
    def password_strength(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None
    metadata_json: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login_at: Optional[datetime]
    roles: List[str] = []

    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[UserResponse]


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Dict[str, Any] = {}


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True


class UserActivityResponse(BaseModel):
    id: str
    action: str
    resource: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    new_users_this_month: int
    departments: Dict[str, int]
    roles: Dict[str, int]
