import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database_simple import get_db
from app.models.user_simple import User
from app.schemas.user_simple import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new user - v19.0 practical approach"""
    # Check if user exists
    if db.query(User).filter(User.email == user.email).first():  # type: ignore[misc]
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.username == user.username).first():  # type: ignore[misc]
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    db_user = User(
        id=str(uuid.uuid4()),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
    )
    db.add(db_user)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    db.refresh(db_user)  # type: ignore[misc]
    return db_user  # type: ignore[return-value]


@router.get("/users", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> Any:
    """List users - v19.0 practical approach"""
    users = db.query(User).offset(skip).limit(limit).all()  # type: ignore[misc]
    return users  # type: ignore[return-value]


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)) -> Any:
    """Get user by ID - v19.0 practical approach"""
    user = db.query(User).filter(User.id == user_id).first()  # type: ignore[misc]
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user  # type: ignore[return-value]

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_update: UserUpdate, db: Session = Depends(get_db)) -> Any:
    """Update user - v19.0 practical approach"""
    user = db.query(User).filter(User.id == user_id).first()  # type: ignore[misc]
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    update_data = user_update.dict(exclude_unset=True)  # type: ignore[misc]
    for field, value in update_data.items():
        setattr(user, field, value)  # type: ignore[misc]

    db.add(user)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    db.refresh(user)  # type: ignore[misc]
    return user  # type: ignore[return-value]


@router.delete("/users/{user_id}")
def deactivate_user(user_id: str, db: Session = Depends(get_db)) -> Any:
    """Deactivate user - v19.0 practical approach"""
    user = db.query(User).filter(User.id == user_id).first()  # type: ignore[misc]
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False  # type: ignore[misc]
    db.add(user)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    return {"message": "User deactivated successfully"}  # type: ignore[return-value]
