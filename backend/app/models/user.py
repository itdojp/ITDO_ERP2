"""User model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.security import hash_password, verify_password


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @classmethod
    def create(
        cls,
        db: Session,
        *,
        email: str,
        password: str,
        full_name: str,
        is_active: bool = True,
        is_superuser: bool = False
    ) -> "User":
        """Create a new user."""
        # Hash the password
        hashed_password = hash_password(password)
        
        # Create user instance
        user = cls(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser
        )
        
        # Add to database
        db.add(user)
        db.flush()
        
        return user
    
    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional["User"]:
        """Get user by email."""
        return db.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def authenticate(cls, db: Session, email: str, password: str) -> Optional["User"]:
        """Authenticate user by email and password."""
        # Get user by email
        user = cls.get_by_email(db, email)
        if not user:
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def update(self, db: Session, **kwargs) -> None:
        """Update user attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                # Hash password if updating
                if key == "password":
                    value = hash_password(value)
                    key = "hashed_password"
                setattr(self, key, value)
        
        db.add(self)
        db.flush()