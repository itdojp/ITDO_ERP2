"""
ERP Organization Management API
Enhanced organization and department management with hierarchy support
"""

import logging
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from pydantic import BaseModel, Field, EmailStr

from app.core.dependencies import get_current_active_user, get_db
from app.core.tenant_deps import TenantDep, RequireApiAccess
from app.models.user import User
from app.models.organization import Organization
from app.models.department import Department
from app.models.employee import Employee

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/erp-organizations", tags=["ERP Organization Management"])


# Pydantic schemas
class OrganizationCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    name_kana: Optional[str] = Field(None, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    
    # Address
    postal_code: Optional[str] = Field(None, max_length=10)
    prefecture: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    
    # Business info
    business_type: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    capital: Optional[int] = None
    employee_count: Optional[int] = None
    fiscal_year_start: Optional[int] = Field(None, ge=1, le=12)
    
    # Hierarchy
    parent_id: Optional[int] = None
    
    # Additional
    description: Optional[str] = None
    is_active: bool = True


class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    name_kana: Optional[str] = Field(None, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    
    # Address
    postal_code: Optional[str] = Field(None, max_length=10)
    prefecture: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    
    # Business info
    business_type: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    capital: Optional[int] = None
    employee_count: Optional[int] = None
    fiscal_year_start: Optional[int] = Field(None, ge=1, le=12)
    
    # Additional
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    organization_id: int = Field(..., description="Organization ID")
    parent_id: Optional[int] = Field(None, description="Parent department ID")
    manager_id: Optional[int] = Field(None, description="Manager user ID")
    description: Optional[str] = None
    is_active: bool = True


class DepartmentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(BaseModel):
    id: int
    code: str
    name: str
    name_kana: Optional[str]
    name_en: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    full_address: Optional[str]
    business_type: Optional[str]
    industry: Optional[str]
    capital: Optional[int]
    employee_count: Optional[int]
    fiscal_year_start: Optional[int]
    parent_id: Optional[int]
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]
    
    # Computed fields
    subsidiary_count: int = 0
    department_count: int = 0
    user_count: int = 0
    is_parent: bool = False
    hierarchy_path: List[str] = []


class DepartmentResponse(BaseModel):
    id: int
    code: str
    name: str
    name_en: Optional[str]
    organization_id: int
    organization_name: Optional[str]
    parent_id: Optional[int]
    parent_name: Optional[str]
    manager_id: Optional[int]
    manager_name: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]
    
    # Computed fields
    user_count: int = 0
    subdepartment_count: int = 0
    hierarchy_level: int = 0


class OrganizationListResponse(BaseModel):
    organizations: List[OrganizationResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class DepartmentListResponse(BaseModel):
    departments: List[DepartmentResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class OrganizationHierarchyResponse(BaseModel):
    id: int
    code: str
    name: str
    parent_id: Optional[int]
    level: int
    children: List["OrganizationHierarchyResponse"] = []


class DepartmentHierarchyResponse(BaseModel):
    id: int
    code: str
    name: str
    parent_id: Optional[int]
    level: int
    user_count: int
    children: List["DepartmentHierarchyResponse"] = []


# Fix forward reference
OrganizationHierarchyResponse.model_rebuild()
DepartmentHierarchyResponse.model_rebuild()


# Organization Management Endpoints
@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    org_request: OrganizationCreateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Create a new organization"""
    try:
        # Check if organization code already exists
        existing_org = db.query(Organization).filter(Organization.code == org_request.code).first()
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization with this code already exists"
            )
        
        # Validate parent organization if provided
        if org_request.parent_id:
            parent = db.query(Organization).filter(Organization.id == org_request.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent organization not found"
                )
        
        # Create organization
        org_data = org_request.dict()
        org_data["created_by"] = current_user.id
        
        organization = Organization(**org_data)
        db.add(organization)
        db.commit()
        db.refresh(organization)
        
        # Get computed fields
        hierarchy_path = [org.name for org in organization.get_hierarchy_path()]
        
        logger.info(f"Organization created: {organization.id} by {current_user.id}")
        
        return OrganizationResponse(
            id=organization.id,
            code=organization.code,
            name=organization.name,
            name_kana=organization.name_kana,
            name_en=organization.name_en,
            phone=organization.phone,
            email=organization.email,
            website=organization.website,
            full_address=organization.full_address,
            business_type=organization.business_type,
            industry=organization.industry,
            capital=organization.capital,
            employee_count=organization.employee_count,
            fiscal_year_start=organization.fiscal_year_start,
            parent_id=organization.parent_id,
            description=organization.description,
            is_active=organization.is_active,
            created_at=organization.created_at.isoformat(),
            updated_at=organization.updated_at.isoformat() if organization.updated_at else None,
            subsidiary_count=len(organization.subsidiaries),
            department_count=organization.departments.count(),
            user_count=0,  # Would need complex query to count users
            is_parent=organization.is_parent,
            hierarchy_path=hierarchy_path
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Organization creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )


@router.get("/organizations", response_model=OrganizationListResponse)
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    parent_id: Optional[int] = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """List organizations with filtering and pagination"""
    try:
        query = db.query(Organization).filter(Organization.deleted_at.is_(None))
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Organization.name.ilike(search_term),
                    Organization.code.ilike(search_term),
                    Organization.name_en.ilike(search_term),
                    Organization.email.ilike(search_term)
                )
            )
        
        if industry:
            query = query.filter(Organization.industry == industry)
        
        if is_active is not None:
            query = query.filter(Organization.is_active == is_active)
        
        if parent_id is not None:
            query = query.filter(Organization.parent_id == parent_id)
        
        # Apply sorting
        sort_column = getattr(Organization, sort_by, Organization.name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        total_count = query.count()
        organizations = query.offset(skip).limit(limit).all()
        
        # Prepare response
        org_responses = []
        for org in organizations:
            hierarchy_path = [o.name for o in org.get_hierarchy_path()]
            
            org_responses.append(OrganizationResponse(
                id=org.id,
                code=org.code,
                name=org.name,
                name_kana=org.name_kana,
                name_en=org.name_en,
                phone=org.phone,
                email=org.email,
                website=org.website,
                full_address=org.full_address,
                business_type=org.business_type,
                industry=org.industry,
                capital=org.capital,
                employee_count=org.employee_count,
                fiscal_year_start=org.fiscal_year_start,
                parent_id=org.parent_id,
                description=org.description,
                is_active=org.is_active,
                created_at=org.created_at.isoformat(),
                updated_at=org.updated_at.isoformat() if org.updated_at else None,
                subsidiary_count=len(org.subsidiaries),
                department_count=org.departments.count(),
                user_count=0,  # Would need complex query
                is_parent=org.is_parent,
                hierarchy_path=hierarchy_path
            ))
        
        return OrganizationListResponse(
            organizations=org_responses,
            total_count=total_count,
            page=(skip // limit) + 1,
            limit=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0
        )
    
    except Exception as e:
        logger.error(f"Failed to list organizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organizations"
        )


@router.get("/organizations/hierarchy", response_model=List[OrganizationHierarchyResponse])
async def get_organization_hierarchy(
    root_id: Optional[int] = Query(None, description="Root organization ID"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get organization hierarchy tree"""
    try:
        def build_hierarchy(parent_id: Optional[int], level: int = 0) -> List[OrganizationHierarchyResponse]:
            query = db.query(Organization).filter(
                and_(
                    Organization.deleted_at.is_(None),
                    Organization.parent_id == parent_id,
                    Organization.is_active == True
                )
            ).order_by(Organization.name)
            
            orgs = query.all()
            result = []
            
            for org in orgs:
                children = build_hierarchy(org.id, level + 1)
                result.append(OrganizationHierarchyResponse(
                    id=org.id,
                    code=org.code,
                    name=org.name,
                    parent_id=org.parent_id,
                    level=level,
                    children=children
                ))
            
            return result
        
        if root_id:
            # Start from specific organization
            root_org = db.query(Organization).filter(Organization.id == root_id).first()
            if not root_org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Root organization not found"
                )
            
            children = build_hierarchy(root_id, 1)
            return [OrganizationHierarchyResponse(
                id=root_org.id,
                code=root_org.code,
                name=root_org.name,
                parent_id=root_org.parent_id,
                level=0,
                children=children
            )]
        else:
            # Start from top level (no parent)
            return build_hierarchy(None, 0)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization hierarchy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization hierarchy"
        )


# Department Management Endpoints
@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    dept_request: DepartmentCreateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Create a new department"""
    try:
        # Check if department code already exists within organization
        existing_dept = db.query(Department).filter(
            and_(
                Department.code == dept_request.code,
                Department.organization_id == dept_request.organization_id
            )
        ).first()
        
        if existing_dept:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Department with this code already exists in the organization"
            )
        
        # Validate organization exists
        organization = db.query(Organization).filter(Organization.id == dept_request.organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Validate parent department if provided
        if dept_request.parent_id:
            parent_dept = db.query(Department).filter(
                and_(
                    Department.id == dept_request.parent_id,
                    Department.organization_id == dept_request.organization_id
                )
            ).first()
            
            if not parent_dept:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent department not found in the same organization"
                )
        
        # Validate manager if provided
        if dept_request.manager_id:
            manager = db.query(User).filter(User.id == dept_request.manager_id).first()
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Manager user not found"
                )
        
        # Create department
        dept_data = dept_request.dict()
        dept_data["created_by"] = current_user.id
        
        department = Department(**dept_data)
        db.add(department)
        db.commit()
        db.refresh(department)
        
        # Get related data for response
        organization_name = organization.name
        parent_name = None
        manager_name = None
        
        if department.parent_id:
            parent = db.query(Department).filter(Department.id == department.parent_id).first()
            parent_name = parent.name if parent else None
        
        if department.manager_id:
            manager = db.query(User).filter(User.id == department.manager_id).first()
            manager_name = manager.full_name if manager else None
        
        logger.info(f"Department created: {department.id} by {current_user.id}")
        
        return DepartmentResponse(
            id=department.id,
            code=department.code,
            name=department.name,
            name_en=department.name_en,
            organization_id=department.organization_id,
            organization_name=organization_name,
            parent_id=department.parent_id,
            parent_name=parent_name,
            manager_id=department.manager_id,
            manager_name=manager_name,
            description=department.description,
            is_active=department.is_active,
            created_at=department.created_at.isoformat(),
            updated_at=department.updated_at.isoformat() if department.updated_at else None,
            user_count=0,  # Would need query to count users
            subdepartment_count=len(department.children),
            hierarchy_level=0  # Would need calculation
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Department creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create department"
        )


@router.get("/departments", response_model=DepartmentListResponse)
async def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    parent_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """List departments with filtering and pagination"""
    try:
        query = db.query(Department).filter(Department.deleted_at.is_(None))
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Department.name.ilike(search_term),
                    Department.code.ilike(search_term),
                    Department.name_en.ilike(search_term)
                )
            )
        
        if organization_id is not None:
            query = query.filter(Department.organization_id == organization_id)
        
        if parent_id is not None:
            query = query.filter(Department.parent_id == parent_id)
        
        if is_active is not None:
            query = query.filter(Department.is_active == is_active)
        
        # Apply sorting
        sort_column = getattr(Department, sort_by, Department.name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        total_count = query.count()
        departments = query.offset(skip).limit(limit).all()
        
        # Prepare response with related data
        dept_responses = []
        for dept in departments:
            # Get organization name
            organization_name = dept.organization.name if dept.organization else None
            
            # Get parent name
            parent_name = None
            if dept.parent_id:
                parent = db.query(Department).filter(Department.id == dept.parent_id).first()
                parent_name = parent.name if parent else None
            
            # Get manager name
            manager_name = None
            if dept.manager_id:
                manager = db.query(User).filter(User.id == dept.manager_id).first()
                manager_name = manager.full_name if manager else None
            
            # Count users in department
            user_count = db.query(User).filter(User.department_id == dept.id).count()
            
            dept_responses.append(DepartmentResponse(
                id=dept.id,
                code=dept.code,
                name=dept.name,
                name_en=dept.name_en,
                organization_id=dept.organization_id,
                organization_name=organization_name,
                parent_id=dept.parent_id,
                parent_name=parent_name,
                manager_id=dept.manager_id,
                manager_name=manager_name,
                description=dept.description,
                is_active=dept.is_active,
                created_at=dept.created_at.isoformat(),
                updated_at=dept.updated_at.isoformat() if dept.updated_at else None,
                user_count=user_count,
                subdepartment_count=len(dept.children),
                hierarchy_level=0  # Would need calculation
            ))
        
        return DepartmentListResponse(
            departments=dept_responses,
            total_count=total_count,
            page=(skip // limit) + 1,
            limit=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0
        )
    
    except Exception as e:
        logger.error(f"Failed to list departments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve departments"
        )


@router.get("/departments/hierarchy", response_model=List[DepartmentHierarchyResponse])
async def get_department_hierarchy(
    organization_id: int = Query(..., description="Organization ID"),
    root_id: Optional[int] = Query(None, description="Root department ID"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get department hierarchy tree for an organization"""
    try:
        def build_dept_hierarchy(parent_id: Optional[int], level: int = 0) -> List[DepartmentHierarchyResponse]:
            query = db.query(Department).filter(
                and_(
                    Department.deleted_at.is_(None),
                    Department.organization_id == organization_id,
                    Department.parent_id == parent_id,
                    Department.is_active == True
                )
            ).order_by(Department.name)
            
            depts = query.all()
            result = []
            
            for dept in depts:
                user_count = db.query(User).filter(User.department_id == dept.id).count()
                children = build_dept_hierarchy(dept.id, level + 1)
                
                result.append(DepartmentHierarchyResponse(
                    id=dept.id,
                    code=dept.code,
                    name=dept.name,
                    parent_id=dept.parent_id,
                    level=level,
                    user_count=user_count,
                    children=children
                ))
            
            return result
        
        if root_id:
            # Start from specific department
            root_dept = db.query(Department).filter(
                and_(
                    Department.id == root_id,
                    Department.organization_id == organization_id
                )
            ).first()
            
            if not root_dept:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Root department not found"
                )
            
            user_count = db.query(User).filter(User.department_id == root_dept.id).count()
            children = build_dept_hierarchy(root_id, 1)
            
            return [DepartmentHierarchyResponse(
                id=root_dept.id,
                code=root_dept.code,
                name=root_dept.name,
                parent_id=root_dept.parent_id,
                level=0,
                user_count=user_count,
                children=children
            )]
        else:
            # Start from top level (no parent) within organization
            return build_dept_hierarchy(None, 0)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get department hierarchy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve department hierarchy"
        )