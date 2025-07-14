#!/usr/bin/env python3
"""Debug script to replicate the exact user lookup process."""

import os
import sys

# Add the backend directory to sys.path
sys.path.insert(0, '/home/work/ITDO_ERP2/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import User
from app.core.security import create_access_token, verify_token
from app.services.auth import AuthService
from tests.factories.user import UserFactory
from app.core.exceptions import ExpiredTokenError, InvalidTokenError

# Use the same database URL as tests
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Test the exact same process as in the failing test
with SessionLocal() as db_session:
    try:
        # Create connection and begin transaction (same as test fixture)
        connection = engine.connect()
        transaction = connection.begin()
        
        # Create session bound to the transaction (same as test fixture)
        test_session = sessionmaker(autocommit=False, autoflush=True, bind=connection)()
        
        # Create a test user in this transaction
        print("Creating test user...")
        test_user = UserFactory.create_with_password(
            test_session,
            password="TestPassword123!",
            email="debug_lookup@example.com",
            full_name="Debug Lookup User",
        )
        print(f"Created user: ID={test_user.id}, Email={test_user.email}")
        
        # Flush to make sure user is in the transaction
        test_session.flush()
        print("User flushed to transaction")
        
        # Create token
        print("Creating token...")
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email, "is_superuser": False}
        )
        print(f"Token created for user ID: {test_user.id}")
        
        # Now simulate the exact AuthService.get_current_user process
        print("\\nSimulating AuthService.get_current_user...")
        
        # Step 1: Verify token
        try:
            payload = verify_token(token)
            print(f"Token verified, payload: {payload}")
        except (ExpiredTokenError, InvalidTokenError) as e:
            print(f"Token verification failed: {e}")
            raise
            
        # Step 2: Check token type
        if payload.get("type") != "access":
            print(f"Wrong token type: {payload.get('type')}")
            raise ValueError("Invalid token type")
            
        # Step 3: Get user ID
        user_id = payload.get("sub")
        if not user_id:
            print("No user ID in token")
            raise ValueError("No user ID")
        print(f"Token user ID: {user_id} (type: {type(user_id)})")
        
        # Step 4: Query user from SAME session
        print("Querying user from same session...")
        user_from_same_session = test_session.query(User).filter(User.id == int(user_id)).first()
        if user_from_same_session:
            print(f"User found in same session: ID={user_from_same_session.id}, Active={user_from_same_session.is_active}")
        else:
            print("User NOT found in same session")
            
        # Step 5: Query user from DIFFERENT session (this is what AuthService does)
        print("Querying user from different session...")
        user_from_different_session = db_session.query(User).filter(User.id == int(user_id)).first()
        if user_from_different_session:
            print(f"User found in different session: ID={user_from_different_session.id}, Active={user_from_different_session.is_active}")
        else:
            print("User NOT found in different session")
            
        # Step 6: Use AuthService with same session
        print("Using AuthService with same session...")
        auth_user_same = AuthService.get_current_user(test_session, token)
        if auth_user_same:
            print(f"AuthService found user with same session: ID={auth_user_same.id}")
        else:
            print("AuthService did NOT find user with same session")
            
        # Step 7: Use AuthService with different session  
        print("Using AuthService with different session...")
        auth_user_different = AuthService.get_current_user(db_session, token)
        if auth_user_different:
            print(f"AuthService found user with different session: ID={auth_user_different.id}")
        else:
            print("AuthService did NOT find user with different session")
            
        # The problem is likely here - the user exists in test_session transaction
        # but not in db_session which has no transaction/autocommit
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test_session.close()
        transaction.rollback()
        connection.close()
        db_session.rollback()