# Type Error Fix Guide

## Quick Start: Critical Fixes

### Step 1: Create Missing Permission Models

Create `app/models/permission.py`:
```python
"""Permission model for RBAC system."""
from typing import TYPE_CHECKING, List
from sqlalchemy import String, ForeignKey, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.role import Role

# Association table for Role-Permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class Permission(Base, TimestampMixin):
    """Permission model."""
    
    __tablename__ = "permissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    category: Mapped[str] = mapped_column(String(50))
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        secondary=role_permissions,
        back_populates="permissions"
    )


class RolePermission(Base):
    """Role-Permission association with additional fields."""
    
    __tablename__ = "role_permission_details"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"))
    granted_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    granted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
```

### Step 2: Update Role Model

Add to `app/models/role.py`:
```python
# Add these attributes to the Role class:
organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
parent_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
full_path: Mapped[str] = mapped_column(String(500), default="")
depth: Mapped[int] = mapped_column(default=0)

# Add relationship
permissions: Mapped[List["Permission"]] = relationship(
    secondary=role_permissions,
    back_populates="roles"
)

# Update UserRole model to add:
valid_to: Mapped[datetime | None] = mapped_column(nullable=True)
```

### Step 3: Create Missing Schemas

Create `app/schemas/permission.py`:
```python
"""Permission schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class PermissionBasic(BaseModel):
    """Basic permission information."""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: str
    
    model_config = ConfigDict(from_attributes=True)


class RoleSummary(BaseModel):
    """Role summary information."""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    user_count: int = 0
    organization_id: int
    
    model_config = ConfigDict(from_attributes=True)


class RoleWithPermissions(BaseModel):
    """Role with permissions list."""
    id: int
    code: str
    name: str
    permissions: List[PermissionBasic] = []
    
    model_config = ConfigDict(from_attributes=True)


class UserRoleAssignment(BaseModel):
    """User role assignment request."""
    user_id: int
    role_id: int
    organization_id: int
    department_id: Optional[int] = None
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_to: Optional[datetime] = None
```

### Step 4: Fix Service Imports

Update `app/services/role.py`:
```python
# Add these imports
from app.models.permission import Permission, RolePermission
from app.schemas.permission import (
    PermissionBasic,
    RoleSummary,
    RoleWithPermissions,
    UserRoleAssignment
)
```

### Step 5: Fix Department Model

Update `app/models/department.py`:
```python
# Change this relationship name:
children: Mapped[List["Department"]] = relationship(
    back_populates="parent",
    cascade="all, delete-orphan"
)

# Update the property that references it:
@property
def has_sub_departments(self) -> bool:
    """Check if department has sub-departments."""
    return len(self.children) > 0

def get_all_sub_departments(self) -> List["Department"]:
    """Get all sub-departments recursively."""
    sub_depts = []
    for child in self.children:
        sub_depts.append(child)
        sub_depts.extend(child.get_all_sub_departments())
    return sub_depts
```

### Step 6: Install Type Stubs

```bash
cd backend
uv add --dev types-psutil
```

### Step 7: Add Type Ignore for Monitoring (Temporary)

Update `app/core/monitoring.py`:
```python
# Add at the top of the file
# type: ignore[import-not-found]
# TODO: Add type stubs for monitoring libraries

import structlog  # type: ignore[import-not-found]
from prometheus_client import Counter, Histogram, Gauge, generate_latest  # type: ignore[import-not-found]
from opentelemetry import trace  # type: ignore[import-not-found]
# ... etc for other monitoring imports
```

## Verification Commands

After making changes:

```bash
# Check if error count decreased
uv run mypy --strict app/services/role.py 2>&1 | grep -c "error:"

# Run specific file checks
uv run mypy --strict app/models/permission.py
uv run mypy --strict app/schemas/permission.py

# Run tests to ensure functionality
uv run pytest tests/unit/services/test_role_service.py -v
```

## Migration Script

After creating models, generate migration:

```bash
cd backend
uv run alembic revision --autogenerate -m "Add Permission and RolePermission models"
uv run alembic upgrade head
```

## Expected Results

After implementing these fixes:
- Role service errors: 46 → ~10
- Total errors: 132 → ~70
- Critical blockers: Resolved
- RBAC functionality: Restored

## Next Steps

1. Implement the fixes in order
2. Run type checking after each step
3. Create unit tests for new models
4. Update API documentation
5. Test role assignment workflows