"""
Basic user CRUD operations for ERP v17.0
Simplified CRUD focusing on essential ERP functionality
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserERPResponse
from app.core.exceptions import BusinessLogicError


def create_user(db: Session, user_data: UserCreate, created_by: Optional[int] = None) -> User:
    """Create a new user with basic validation."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise BusinessLogicError("User with this email already exists")
    
    # Create user using model method
    user = User.create(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        is_active=user_data.is_active
    )
    
    # Set created_by if provided
    if created_by:
        user.created_by = created_by
        db.add(user)
        db.flush()
    
    db.commit()
    db.refresh(user)
    
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(
        and_(
            User.id == user_id,
            User.deleted_at.is_(None)
        )
    ).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(
        and_(
            User.email == email,
            User.deleted_at.is_(None)
        )
    ).first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    organization_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "full_name",
    sort_order: str = "asc"
) -> tuple[List[User], int]:
    """Get users with filtering and pagination."""
    query = db.query(User).filter(User.deleted_at.is_(None))
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    
    # Organization filter (if user has organization relationship)
    if organization_id:
        # This would need actual organization relationship
        # For now, filter by users who have an organization_id
        query = query.filter(User.organization_id == organization_id)
    
    # Active status filter
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Sorting
    sort_column = getattr(User, sort_by, User.full_name)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Count for pagination
    total = query.count()
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return users, total


def update_user(
    db: Session,
    user_id: int,
    user_data: UserUpdate,
    updated_by: Optional[int] = None
) -> Optional[User]:
    """Update user information."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    # Update fields
    update_dict = user_data.dict(exclude_unset=True)
    if updated_by:
        update_dict['updated_by'] = updated_by
    
    user.update(db, **update_dict)
    db.commit()
    db.refresh(user)
    
    return user


def deactivate_user(
    db: Session,
    user_id: int,
    deactivated_by: Optional[int] = None
) -> Optional[User]:
    """Deactivate user (soft delete)."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.is_active = False
    if deactivated_by:
        user.updated_by = deactivated_by
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def get_active_users_count(db: Session, organization_id: Optional[int] = None) -> int:
    """Get count of active users."""
    query = db.query(User).filter(
        and_(
            User.deleted_at.is_(None),
            User.is_active == True
        )
    )
    
    if organization_id:
        query = query.filter(User.organization_id == organization_id)
    
    return query.count()


def get_user_statistics(db: Session) -> Dict[str, Any]:
    """Get basic user statistics."""
    total_users = db.query(User).filter(User.deleted_at.is_(None)).count()
    active_users = db.query(User).filter(
        and_(
            User.deleted_at.is_(None),
            User.is_active == True
        )
    ).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "activation_rate": (active_users / total_users * 100) if total_users > 0 else 0
    }


def convert_to_erp_response(user: User) -> UserERPResponse:
    """Convert User model to ERP response schema."""
    return UserERPResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        display_name=user.get_full_display_name(),
        is_active=user.is_active,
        organization_id=user.organization_id,
        department_id=user.department_id,
        is_erp_user=user.is_erp_user(),
        created_at=user.created_at,
        last_login_at=user.last_login_at
    )