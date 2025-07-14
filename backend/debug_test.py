#!/usr/bin/env python3
"""Debug script to test user creation and token validation."""

import os
import sys

# Add the backend directory to sys.path
sys.path.insert(0, '/home/work/ITDO_ERP2/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import User
from app.core.security import create_access_token
from app.services.auth import AuthService
from tests.factories.user import UserFactory

# Use the same database URL as tests
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Test user creation and token validation
with SessionLocal() as db_session:
    try:
        # Create a test user
        print("Creating test user...")
        test_user = UserFactory.create_with_password(
            db_session,
            password="TestPassword123!",
            email="debug_test@example.com",
            full_name="Debug Test User",
        )
        print(f"Created user: ID={test_user.id}, Email={test_user.email}")
        
        # Create token
        print("Creating token...")
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email, "is_superuser": False}
        )
        print(f"Token created: {token[:50]}...")
        
        # Test token validation
        print("Validating token...")
        retrieved_user = AuthService.get_current_user(db_session, token)
        if retrieved_user:
            print(f"Token validation successful: User ID={retrieved_user.id}")
        else:
            print("Token validation failed: User not found")
            
        # Check if user exists in database
        print("Direct database lookup...")
        user_from_db = db_session.query(User).filter(User.id == test_user.id).first()
        if user_from_db:
            print(f"User found in DB: ID={user_from_db.id}, Active={user_from_db.is_active}")
        else:
            print("User not found in database")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_session.rollback()  # Clean up