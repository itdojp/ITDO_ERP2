"""Role schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """Base role schema."""

    code: str = Field(..., min_length=1, max_length=50, description="ロールコード")
    name: str = Field(..., min_length=1, max_length=255, description="ロール名")
    description: Optional[str] = Field(None, description="説明")
    permissions: List[str] = Field(default_factory=list, description="権限リスト")


class RoleCreate(RoleBase):
    """Role creation schema."""

    pass


class RoleUpdate(BaseModel):
    """Role update schema."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="ロール名"
    )
    description: Optional[str] = Field(None, description="説明")
    permissions: Optional[List[str]] = Field(None, description="権限リスト")


class RoleResponse(RoleBase):
    """Role response schema."""

    id: int
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, role):
        """Custom method to convert from ORM model."""
        # Convert permissions dict to list
        permissions = []
        if role.permissions:
            permissions = [perm for perm, granted in role.permissions.items() if granted]
        
        data = {
            "id": role.id,
            "code": role.code,
            "name": role.name,
            "description": role.description,
            "permissions": permissions,
            "is_system": role.is_system,
            "is_active": role.is_active,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "created_by": role.created_by,
            "updated_by": role.updated_by,
        }
        return cls(**data)


class UserRoleBase(BaseModel):
    """Base user role schema."""

    user_id: int = Field(..., description="ユーザーID")
    role_id: int = Field(..., description="ロールID")
    organization_id: int = Field(..., description="組織ID")
    department_id: Optional[int] = Field(None, description="部門ID")
    expires_at: Optional[datetime] = Field(None, description="有効期限")


class UserRoleCreate(UserRoleBase):
    """User role creation schema."""

    pass


class UserRoleResponse(UserRoleBase):
    """User role response schema."""

    id: int
    assigned_by: Optional[int] = None
    assigned_at: datetime

    class Config:
        from_attributes = True


class RoleList(BaseModel):
    """Role list response schema."""

    items: List[RoleResponse]
    total: int
    page: int = 1
    limit: int = 10

    class Config:
        from_attributes = True
