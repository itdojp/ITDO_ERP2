#!/usr/bin/env python
"""Fix duplicate model definitions."""

import os
import shutil
from datetime import datetime

print("🔧 Fixing Duplicate Model Definitions")
print("=====================================\n")

# Backup directory
backup_dir = f"model_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)

# Files to handle
duplicates = [
    ("app/models/user_session.py", "Old UserSession model"),
    ("app/models/user_extended.py", "Check for UserSession"),
]

print(f"📁 Creating backup in: {backup_dir}")

for file_path, description in duplicates:
    if os.path.exists(file_path):
        backup_path = os.path.join(backup_dir, os.path.basename(file_path))
        shutil.copy2(file_path, backup_path)
        print(f"✅ Backed up: {file_path} -> {backup_path}")

# Check which UserSession to keep
print("\n📊 Analyzing UserSession implementations...")

# Read both files
with open("app/models/session.py", "r") as f:
    session_content = f.read()
    session_lines = len(session_content.splitlines())
    has_session_config = "SessionConfiguration" in session_content
    has_session_activity = "SessionActivity" in session_content

with open("app/models/user_session.py", "r") as f:
    user_session_content = f.read()
    user_session_lines = len(user_session_content.splitlines())

print("\n  app/models/session.py:")
print(f"    - Lines: {session_lines}")
print(f"    - Has SessionConfiguration: {has_session_config}")
print(f"    - Has SessionActivity: {has_session_activity}")

print("\n  app/models/user_session.py:")
print(f"    - Lines: {user_session_lines}")

# Check imports
print("\n🔍 Checking imports...")
import subprocess

result = subprocess.run(
    ["grep", "-r", "from app.models.user_session import", "app/"],
    capture_output=True,
    text=True,
)

if result.stdout:
    print("  Files importing from user_session.py:")
    for line in result.stdout.strip().split("\n"):
        print(f"    - {line.split(':')[0]}")

result = subprocess.run(
    ["grep", "-r", "from app.models.session import", "app/"],
    capture_output=True,
    text=True,
)

if result.stdout:
    print("\n  Files importing from session.py:")
    for line in result.stdout.strip().split("\n"):
        print(f"    - {line.split(':')[0]}")

print("\n📋 Recommendation:")
print("  - Keep app/models/session.py (newer, more complete)")
print("  - Remove app/models/user_session.py (duplicate)")
print("  - Update imports to use session.py")

print("\n✅ Backup complete. Manual intervention needed to:")
print("  1. Remove app/models/user_session.py")
print("  2. Update imports from 'user_session' to 'session'")
print("  3. Verify UserSession is properly exported from __init__.py")
