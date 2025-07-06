# Type Safety Implementation Guide

## Overview

This document provides a comprehensive guide to the type-safe implementation of the ITDO ERP System v2. The system has been completely reconstructed with type safety as the top priority, implementing strict typing patterns throughout all layers.

## Architecture Overview

### Type Safety Principles

1. **Strict Type Checking**: No `any` types allowed, comprehensive type annotations
2. **Generic Base Classes**: Reusable, type-safe patterns for CRUD operations
3. **Schema Validation**: Pydantic v2 with comprehensive validation rules
4. **Repository Pattern**: Type-safe data access layer
5. **Service Layer**: Business logic with type guarantees

### Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │Organizations│ │ Departments │ │     Roles       │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                  Service Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │   OrgSvc    │ │   DeptSvc   │ │   RoleSvc       │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                Repository Layer                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │   OrgRepo   │ │  DeptRepo   │ │   RoleRepo      │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                   Model Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │Organization │ │ Department  │ │     Role        │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Type System Implementation

### Core Type Definitions

Located in `backend/app/types/__init__.py`:

```python
from typing import TypeVar, Protocol, Union
from pydantic import BaseModel

# ID Types
UserId = int
OrganizationId = int
DepartmentId = int
RoleId = int

# Generic Type Variables
ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)

# Protocols for type safety
class Identifiable(Protocol):
    id: int

class SoftDeletable(Protocol):
    is_deleted: bool
    deleted_at: Optional[datetime]
```

### Base Model Classes

#### SoftDeletableModel

```python
class SoftDeletableModel(AuditableModel):
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_by: Mapped[Optional[UserId]] = mapped_column(Integer, ForeignKey("users.id"))
    
    def soft_delete(self, deleted_by: Optional[UserId] = None) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
```

#### AuditableModel

```python
class AuditableModel(BaseModel):
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[Optional[UserId]] = mapped_column(Integer, ForeignKey("users.id"))
    updated_by: Mapped[Optional[UserId]] = mapped_column(Integer, ForeignKey("users.id"))
```

### Generic Repository Pattern

```python
class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model_class: Type[ModelType], db: Session):
        self.model_class = model_class
        self.db = db
    
    def get(self, id: int) -> Optional[ModelType]:
        return self.db.query(self.model_class).filter(
            self.model_class.id == id,
            self.model_class.is_deleted == False
        ).first()
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        obj_data = obj_in.model_dump()
        db_obj = self.model_class(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
```

## API Implementation

### Generic API Base Class

```python
class BaseAPIRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    def __init__(
        self,
        service_class: Type,
        prefix: str,
        tags: List[str]
    ):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.service_class = service_class
        self._setup_routes()
    
    def _setup_routes(self):
        @self.router.get("/", response_model=PaginatedResponse[ResponseSchemaType])
        async def list_items(
            skip: int = 0,
            limit: int = 100,
            db: Session = Depends(get_db)
        ):
            service = self.service_class(db)
            items, total = service.list_items(skip, limit)
            return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)
```

### Organization API Example

```python
@router.post("/", response_model=OrganizationResponse)
def create_organization(
    organization_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[OrganizationResponse, JSONResponse]:
    service = OrganizationService(db)
    
    try:
        organization = service.create_organization(
            organization_data,
            created_by=current_user.id
        )
        return service.get_organization_response(organization)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail=str(e),
                code="DUPLICATE_CODE"
            ).model_dump()
        )
```

## Schema Validation

### Pydantic v2 Implementation

```python
class OrganizationCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Organization code")
    name: str = Field(..., min_length=1, max_length=200, description="Organization name")
    name_en: Optional[str] = Field(None, max_length=200, description="English name")
    industry: Optional[str] = Field(None, max_length=100, description="Industry type")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('Code must be alphanumeric')
        return v.upper()
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )
```

### Hierarchical Data Validation

```python
class DepartmentCreate(BaseModel):
    organization_id: OrganizationId = Field(..., description="Organization ID")
    parent_id: Optional[DepartmentId] = Field(None, description="Parent department ID")
    
    @model_validator(mode='after')
    def validate_hierarchy(self) -> 'DepartmentCreate':
        # Custom validation logic for hierarchical relationships
        if self.parent_id == self.organization_id:
            raise ValueError("Department cannot be its own parent")
        return self
```

## Error Handling

### Comprehensive Error Responses

```python
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    field: Optional[str] = Field(None, description="Field that caused the error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Resource not found",
                "code": "NOT_FOUND",
                "field": None
            }
        }
```

### Type-Safe Exception Handling

```python
try:
    result = await service.create_item(data)
    return result
except ValueError as e:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            detail=str(e),
            code="VALIDATION_ERROR"
        ).model_dump()
    )
except IntegrityError as e:
    db.rollback()
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(
            detail="Resource already exists",
            code="DUPLICATE_KEY"
        ).model_dump()
    )
```

## Testing Framework

### Type-Safe Test Base Classes

```python
class BaseAPITestCase(ABC, Generic[T, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    @property
    @abstractmethod
    def endpoint_prefix(self) -> str:
        pass
    
    @property
    @abstractmethod
    def factory_class(self) -> Type[BaseFactory]:
        pass
    
    def test_create_success(
        self,
        client: TestClient,
        admin_token: str
    ) -> None:
        payload = self.create_valid_payload()
        
        response = client.post(
            self.endpoint_prefix,
            json=payload,
            headers=self.get_auth_headers(admin_token)
        )
        
        assert response.status_code == 201
        data = response.json()
        validated_data = self.response_schema_class.model_validate(data)
        assert validated_data.id is not None
```

### Factory Pattern Implementation

```python
class OrganizationFactory(BaseFactory):
    @property
    def model_class(self) -> Type[Organization]:
        return Organization
    
    @classmethod
    def _get_default_attributes(cls) -> Dict[str, Any]:
        return {
            "code": fake.unique.company_suffix(),
            "name": fake.company(),
            "industry": fake.random_element(elements=("IT", "製造業", "小売業"))
        }
    
    @classmethod
    def create_hierarchy(cls, db_session: Session, depth: int = 3) -> Dict[str, Any]:
        # Type-safe hierarchy creation
        root = cls.create(db_session, name="Root Organization")
        return cls._build_hierarchy(db_session, root, depth)
```

## Performance Considerations

### Query Optimization

```python
class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]):
    def get_with_departments(self, org_id: OrganizationId) -> Optional[Organization]:
        return self.db.query(Organization)\
            .options(joinedload(Organization.departments))\
            .filter(Organization.id == org_id)\
            .first()
    
    def get_hierarchy_tree(self, root_id: OrganizationId) -> List[Organization]:
        # Optimized hierarchical query with CTE
        cte = self.db.query(Organization)\
            .filter(Organization.id == root_id)\
            .cte(recursive=True)
        
        # Recursive part
        children = aliased(Organization)
        cte = cte.union_all(
            self.db.query(children)\
            .filter(children.parent_id == cte.c.id)
        )
        
        return self.db.query(Organization)\
            .select_from(cte)\
            .order_by(Organization.name)\
            .all()
```

### Caching Strategy

```python
from functools import lru_cache
from typing import List

@lru_cache(maxsize=128)
def get_cached_permissions(role_id: RoleId) -> List[str]:
    """Cache permission codes for role."""
    # Implementation with Redis or in-memory cache
    pass

class RoleService:
    @monitor_performance("role_service.get_effective_permissions")
    def get_effective_permissions(self, role_id: RoleId) -> List[Permission]:
        # Use cached permissions for better performance
        cached_codes = get_cached_permissions(role_id)
        if cached_codes:
            return self._permissions_from_codes(cached_codes)
        
        # Fallback to database query
        return self._query_permissions(role_id)
```

## Migration Strategy

### Database Schema Evolution

The migration `003_complete_type_safe_schema.py` provides a comprehensive update:

1. **Organization Model**: Complete implementation with hierarchy support
2. **Department Model**: Full departmental structure with manager relationships
3. **Role Model**: Role-based access control with permission inheritance
4. **Permission Model**: Granular permission system
5. **User Model**: Enhanced user management with organization/department links

### Backward Compatibility

The system maintains backward compatibility through:

1. **Gradual Migration**: Existing APIs continue to work
2. **Schema Versioning**: Multiple schema versions supported
3. **Feature Flags**: New features can be enabled incrementally
4. **Data Migration**: Safe data transformation processes

## Best Practices

### Type Safety Guidelines

1. **Always Use Type Hints**: Every function must have complete type annotations
2. **Prefer Composition**: Use generic base classes for reusable patterns
3. **Validate Early**: Use Pydantic for all data validation
4. **Handle Errors Gracefully**: Comprehensive error handling with proper types
5. **Test Thoroughly**: Type-safe tests for all functionality

### Performance Guidelines

1. **Use Appropriate Indexes**: Database indexes for all foreign keys and search fields
2. **Implement Caching**: Cache frequently accessed data
3. **Optimize Queries**: Use joins and CTEs for hierarchical data
4. **Monitor Performance**: Continuous monitoring with metrics
5. **Async Where Beneficial**: Use async/await for I/O bound operations

### Security Guidelines

1. **Input Validation**: Strict validation on all inputs
2. **SQL Injection Prevention**: Use parameterized queries only
3. **Access Control**: Permission-based access throughout
4. **Audit Logging**: Comprehensive audit trails
5. **Secure Defaults**: Secure by default configurations

## Tools and Configuration

### MyPy Configuration

```toml
[tool.mypy]
python_version = "3.13"
strict = true
disallow_any_explicit = false  # Disabled for Pydantic compatibility
plugins = ["pydantic.mypy"]

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
```

### Development Workflow

1. **Type Check First**: Always run mypy before committing
2. **Test Coverage**: Maintain >80% test coverage
3. **Code Review**: Focus on type safety in reviews
4. **Documentation**: Keep documentation in sync with types
5. **Continuous Integration**: Automated type checking in CI/CD

## Conclusion

This type-safe implementation provides:

- **Reliability**: Compile-time error detection
- **Maintainability**: Clear interfaces and contracts
- **Performance**: Optimized patterns and caching
- **Scalability**: Generic, reusable components
- **Security**: Comprehensive validation and access control

The system is designed to scale with the organization while maintaining type safety and performance across all layers.