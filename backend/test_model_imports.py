#!/usr/bin/env python
"""Test model imports to identify dependency issues."""

import os

os.environ["DATABASE_URL"] = "sqlite:///test_models.db"

print("🔍 Testing Model Imports")
print("========================\n")

# Track import results
import_results = []


def test_import(module_path, description):
    """Test importing a module."""
    try:
        exec(f"import {module_path}")
        import_results.append((description, "✅", None))
        print(f"✅ {description}")
    except ImportError as e:
        import_results.append((description, "❌", str(e)))
        print(f"❌ {description}: {e}")
    except Exception as e:
        import_results.append((description, "⚠️", str(e)))
        print(f"⚠️ {description}: {e}")


# Test core imports
print("1. Testing Core Imports")
print("-----------------------")
test_import("app.core.config", "Config")
test_import("app.core.database", "Database")
test_import("app.core.security", "Security")
test_import("app.core.exceptions", "Exceptions")

# Test base models
print("\n2. Testing Base Models")
print("----------------------")
test_import("app.models.base", "Base Model")

# Test individual models
print("\n3. Testing Individual Models")
print("----------------------------")
test_import("app.models.user", "User Model")
test_import("app.models.role", "Role Model")
test_import("app.models.permission", "Permission Model")
test_import("app.models.organization", "Organization Model")
test_import("app.models.department", "Department Model")
test_import("app.models.mfa", "MFA Model")
test_import("app.models.session", "Session Model")
test_import("app.models.password_reset", "Password Reset Model")

# Test all models import
print("\n4. Testing All Models Import")
print("----------------------------")
test_import("app.models", "All Models")

# Test services
print("\n5. Testing Services")
print("-------------------")
test_import("app.services.auth", "Auth Service")
test_import("app.services.mfa_service", "MFA Service")
test_import("app.services.session_service", "Session Service")
test_import("app.services.google_auth_service", "Google Auth Service")
test_import("app.services.security_service", "Security Service")
test_import("app.services.password_reset_service", "Password Reset Service")

# Test APIs
print("\n6. Testing API Endpoints")
print("------------------------")
test_import("app.api.v1.auth", "Auth API")
test_import("app.api.v1.users", "Users API")
test_import("app.api.v1.sessions", "Sessions API")
test_import("app.api.v1.mfa", "MFA API")
test_import("app.api.v1.security", "Security API")
test_import("app.api.v1.password_reset", "Password Reset API")

# Summary
print("\n📊 Import Test Summary")
print("=====================")
success_count = sum(1 for _, status, _ in import_results if status == "✅")
failure_count = sum(1 for _, status, _ in import_results if status == "❌")
warning_count = sum(1 for _, status, _ in import_results if status == "⚠️")

print(f"✅ Success: {success_count}")
print(f"❌ Failures: {failure_count}")
print(f"⚠️ Warnings: {warning_count}")

if failure_count > 0:
    print("\n🔧 Failed Imports:")
    for desc, status, error in import_results:
        if status == "❌":
            print(f"  - {desc}: {error}")

if warning_count > 0:
    print("\n⚠️ Warning Imports:")
    for desc, status, error in import_results:
        if status == "⚠️":
            print(f"  - {desc}: {error}")

# Cleanup
import os

if os.path.exists("test_models.db"):
    os.remove("test_models.db")
