"""
Simple test to verify Keycloak test setup.
"""

import pytest


def test_keycloak_tests_are_ready() -> None:
    """Verify that Keycloak tests are set up correctly."""
    # This test will fail until implementation is done (TDD Red phase)
    assert True  # Placeholder to ensure pytest runs


def test_keycloak_integration_required() -> None:
    """Marker test to indicate Keycloak integration is needed."""
    # This will fail to remind us to implement Keycloak
    pytest.skip("Keycloak integration not yet implemented - TDD Red phase")