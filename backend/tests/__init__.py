"""Test package for ITDO ERP System."""

import os

# Force SQLite for all tests by setting environment variable before any imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
