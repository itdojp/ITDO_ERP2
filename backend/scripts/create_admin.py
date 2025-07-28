#!/usr/bin/env python3
"""
Create admin user script for ITDO ERP v2
"""

import argparse
import getpass
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.base import Base
from app.models.user import User


def create_admin_user(email: str, password: str, name: str) -> None:
    """Create an admin user in the database."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"Error: User with email {email} already exists")
            return

        # Create admin user
        admin_user = User(
            email=email,
            username=email.split("@")[0],  # Use email prefix as username
            hashed_password=get_password_hash(password),
            full_name=name,
            is_active=True,
            is_superuser=True,
            is_verified=True,
            mfa_enabled=False,  # Can be enabled later through UI
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("Successfully created admin user:")
        print(f"  ID: {admin_user.id}")
        print(f"  Email: {admin_user.email}")
        print(f"  Username: {admin_user.username}")
        print(f"  Name: {admin_user.full_name}")
        print(f"  Superuser: {admin_user.is_superuser}")
        print()
        print("The user can now log in with the provided credentials.")
        print("For security, it's recommended to enable MFA after first login.")

    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create an admin user for ITDO ERP v2")
    parser.add_argument(
        "--email",
        type=str,
        required=True,
        help="Admin user email address",
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Admin user password (will prompt if not provided)",
    )
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Admin user full name",
    )

    args = parser.parse_args()

    # Get password if not provided
    password = args.password
    if not password:
        password = getpass.getpass("Enter admin password: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if password != confirm_password:
            print("Error: Passwords do not match")
            sys.exit(1)

    # Validate password length
    if len(password) < 8:
        print("Error: Password must be at least 8 characters long")
        sys.exit(1)

    # Create the admin user
    try:
        create_admin_user(args.email, password, args.name)
    except Exception as e:
        print(f"Failed to create admin user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
