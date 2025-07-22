"""
ERP User Management API
Enhanced user management with comprehensive CRUD, search, filtering, and pagination
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
from app.models.role import Role, UserRole
from app.models.organization import Organization
from app.models.department import Department
from app.models.employee import Employee
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/erp-users", tags=["ERP User Management"])


# Pydantic schemas
class UserCreateRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=8, max_length=100)
    department_id: Optional[int] = None
    is_active: bool = Field(True)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    department_id: Optional[int] = None
    is_active: Optional[bool] = None
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    profile_image_url: Optional[str] = Field(None, max_length=500)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, max_length=100)


class RoleAssignmentRequest(BaseModel):
    role_id: int = Field(..., description="Role ID to assign")
    organization_id: int = Field(..., description="Organization ID")
    department_id: Optional[int] = Field(None, description="Department ID (optional)")
    expires_at: Optional[datetime] = Field(None, description="Role expiration date")


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    profile_image_url: Optional[str]
    is_active: bool
    is_superuser: bool
    department_id: Optional[int]
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    last_login_at: Optional[str]
    password_changed_at: Optional[str]
    created_at: str
    updated_at: Optional[str]
    
    # Computed fields
    department_name: Optional[str] = None
    role_count: int = 0
    organization_count: int = 0
    is_online: bool = False


class UserDetailResponse(UserResponse):
    password_must_change: bool
    failed_login_attempts: int
    locked_until: Optional[str]
    roles: List[Dict[str, Any]] = []
    organizations: List[Dict[str, Any]] = []
    employee_profile: Optional[Dict[str, Any]] = None


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    online_users: int
    users_by_department: Dict[str, int]
    recent_registrations: int


# User Management Endpoints
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_request: UserCreateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Create a new user"""
    try:
        # Check if user email already exists
        existing_user = db.query(User).filter(User.email == user_request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Validate department exists if provided
        if user_request.department_id:
            department = db.query(Department).filter(Department.id == user_request.department_id).first()
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Department not found"
                )
        
        # Create user
        user = User.create(
            db=db,
            email=user_request.email,
            password=user_request.password,
            full_name=user_request.full_name,
            phone=user_request.phone,
            is_active=user_request.is_active
        )
        
        # Update additional fields
        user.department_id = user_request.department_id
        user.bio = user_request.bio
        user.location = user_request.location
        user.website = user_request.website
        user.created_by = current_user.id
        
        db.commit()
        db.refresh(user)
        
        # Get department name
        department_name = None
        if user.department_id:
            department = db.query(Department).filter(Department.id == user.department_id).first()
            department_name = department.name if department else None
        
        logger.info(f"User created: {user.id} by {current_user.id}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            profile_image_url=user.profile_image_url,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            department_id=user.department_id,
            bio=user.bio,
            location=user.location,
            website=user.website,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            password_changed_at=user.password_changed_at.isoformat() if user.password_changed_at else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            department_name=department_name,
            role_count=len(user.user_roles),
            organization_count=len(user.get_organizations()),
            is_online=user.is_online()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search term for name, email"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_superuser: Optional[bool] = Query(None, description="Filter by superuser status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """List users with advanced filtering and pagination"""
    try:
        query = db.query(User).filter(User.deleted_at.is_(None))
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.phone.ilike(search_term)
                )
            )
        
        if department_id is not None:
            query = query.filter(User.department_id == department_id)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_superuser is not None:
            query = query.filter(User.is_superuser == is_superuser)
        
        # Apply sorting
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        # Prepare response
        user_responses = []
        for user in users:
            # Get department name
            department_name = None
            if user.department_id:
                department = db.query(Department).filter(Department.id == user.department_id).first()
                department_name = department.name if department else None
            
            user_responses.append(UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                phone=user.phone,
                profile_image_url=user.profile_image_url,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                department_id=user.department_id,
                bio=user.bio,
                location=user.location,
                website=user.website,
                last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
                password_changed_at=user.password_changed_at.isoformat() if user.password_changed_at else None,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat() if user.updated_at else None,
                department_name=department_name,
                role_count=len(user.user_roles),
                organization_count=len(user.get_organizations()),
                is_online=user.is_online()
            ))
        
        return UserListResponse(
            users=user_responses,
            total_count=total_count,
            page=(skip // limit) + 1,
            limit=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0
        )
    
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get detailed user information"""
    try:
        user = db.query(User).filter(
            and_(User.id == user_id, User.deleted_at.is_(None))
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if current user can access this user's details
        if not current_user.can_access_user(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get department name
        department_name = None
        if user.department_id:
            department = db.query(Department).filter(Department.id == user.department_id).first()
            department_name = department.name if department else None
        
        # Get roles information
        roles = []
        for user_role in user.user_roles:
            if user_role.is_valid:
                roles.append({
                    "id": user_role.role.id,
                    "code": user_role.role.code,
                    "name": user_role.role.name,
                    "organization_id": user_role.organization_id,
                    "organization_name": user_role.organization.name if user_role.organization else None,
                    "department_id": user_role.department_id,
                    "department_name": user_role.department.name if user_role.department else None,
                    "assigned_at": user_role.assigned_at.isoformat(),
                    "expires_at": user_role.expires_at.isoformat() if user_role.expires_at else None,
                    "is_primary": user_role.is_primary
                })
        
        # Get organizations
        organizations = []
        for org in user.get_organizations():
            organizations.append({
                "id": org.id,
                "code": org.code,
                "name": org.name,
                "is_active": org.is_active
            })
        
        # Get employee profile if exists
        employee_profile = None
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        if employee:
            employee_profile = {
                "employee_number": employee.employee_number,
                "position": employee.position,
                "job_title": employee.job_title,
                "employment_type": employee.employment_type,
                "hire_date": employee.hire_date.isoformat() if employee.hire_date else None,
                "manager_id": employee.manager_id
            }
        
        return UserDetailResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            profile_image_url=user.profile_image_url,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            department_id=user.department_id,
            bio=user.bio,
            location=user.location,
            website=user.website,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            password_changed_at=user.password_changed_at.isoformat() if user.password_changed_at else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            password_must_change=user.password_must_change,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until.isoformat() if user.locked_until else None,
            department_name=department_name,
            role_count=len(user.user_roles),
            organization_count=len(user.get_organizations()),
            is_online=user.is_online(),
            roles=roles,
            organizations=organizations,
            employee_profile=employee_profile
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details"
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_request: UserUpdateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Update user information"""
    try:
        user = db.query(User).filter(
            and_(User.id == user_id, User.deleted_at.is_(None))
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check permissions
        if not current_user.can_access_user(user) and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Validate department if provided
        if user_request.department_id:
            department = db.query(Department).filter(Department.id == user_request.department_id).first()
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Department not found"
                )
        
        # Update user fields
        update_data = user_request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_by = current_user.id
        user.updated_at = datetime.now(UTC)
        
        db.commit()
        db.refresh(user)
        
        # Get department name
        department_name = None
        if user.department_id:
            department = db.query(Department).filter(Department.id == user.department_id).first()
            department_name = department.name if department else None
        
        logger.info(f"User updated: {user.id} by {current_user.id}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            profile_image_url=user.profile_image_url,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            department_id=user.department_id,
            bio=user.bio,
            location=user.location,
            website=user.website,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            password_changed_at=user.password_changed_at.isoformat() if user.password_changed_at else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            department_name=department_name,
            role_count=len(user.user_roles),
            organization_count=len(user.get_organizations()),
            is_online=user.is_online()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Soft delete a user"""
    try:
        user = db.query(User).filter(
            and_(User.id == user_id, User.deleted_at.is_(None))
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check permissions
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can delete users"
            )
        
        # Prevent self-deletion
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete yourself"
            )
        
        # Soft delete user
        user.soft_delete(deleted_by=current_user.id)
        db.commit()
        
        logger.info(f"User deleted: {user.id} by {current_user.id}")
        
        return {"message": "User deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.post("/users/{user_id}/change-password")
async def change_password(
    user_id: int,
    password_request: PasswordChangeRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Change user password"""
    try:
        user = db.query(User).filter(
            and_(User.id == user_id, User.deleted_at.is_(None))
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check permissions (users can only change their own password unless admin)
        if user.id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Change password
        user.change_password(
            db=db,
            current_password=password_request.current_password,
            new_password=password_request.new_password
        )
        
        logger.info(f"Password changed: {user.id}")
        
        return {"message": "Password changed successfully"}
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/users/{user_id}/assign-role")
async def assign_role(
    user_id: int,
    role_request: RoleAssignmentRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Assign role to user"""
    try:
        user = db.query(User).filter(
            and_(User.id == user_id, User.deleted_at.is_(None))
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        role = db.query(Role).filter(Role.id == role_request.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        organization = db.query(Organization).filter(Organization.id == role_request.organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Check if role assignment already exists
        existing_assignment = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_request.role_id,
                UserRole.organization_id == role_request.organization_id,
                UserRole.department_id == role_request.department_id
            )
        ).first()
        
        if existing_assignment and existing_assignment.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role already assigned to user in this context"
            )
        
        # Assign role
        user_role = role.assign_to_user(
            user=user,
            assigned_by=current_user.id,
            expires_at=role_request.expires_at
        )
        user_role.organization_id = role_request.organization_id
        user_role.department_id = role_request.department_id
        
        db.add(user_role)
        db.commit()
        
        logger.info(f"Role assigned: {role.code} to user {user.id} by {current_user.id}")
        
        return {"message": f"Role '{role.name}' assigned successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role"
        )


@router.get("/statistics", response_model=UserStatsResponse)
async def get_user_statistics(
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get user statistics"""
    try:
        from datetime import datetime, timedelta
        
        # Basic counts
        total_users = db.query(User).filter(User.deleted_at.is_(None)).count()
        active_users = db.query(User).filter(
            and_(User.deleted_at.is_(None), User.is_active == True)
        ).count()
        inactive_users = total_users - active_users
        
        # Online users (active within last 15 minutes)
        online_threshold = datetime.now(UTC) - timedelta(minutes=15)
        online_users = db.query(User).filter(
            and_(
                User.deleted_at.is_(None),
                User.is_active == True,
                User.last_login_at > online_threshold
            )
        ).count()
        
        # Recent registrations (last 30 days)
        recent_threshold = datetime.now(UTC) - timedelta(days=30)
        recent_registrations = db.query(User).filter(
            and_(
                User.deleted_at.is_(None),
                User.created_at > recent_threshold
            )
        ).count()
        
        # Users by department
        users_by_dept = db.query(
            Department.name.label('department_name'),
            func.count(User.id).label('user_count')
        ).join(
            User, User.department_id == Department.id
        ).filter(
            User.deleted_at.is_(None)
        ).group_by(Department.name).all()
        
        users_by_department = {dept.department_name: dept.user_count for dept in users_by_dept}
        
        return UserStatsResponse(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            online_users=online_users,
            recent_registrations=recent_registrations,
            users_by_department=users_by_department
        )
    
    except Exception as e:
        logger.error(f"Failed to get user statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )