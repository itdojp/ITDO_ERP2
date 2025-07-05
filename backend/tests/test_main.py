"""Test main application functionality."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "ITDO ERP System API"}


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ping_endpoint():
    """Test the ping endpoint."""
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}


@pytest.mark.asyncio
async def test_openapi_docs():
    """Test that OpenAPI docs are accessible."""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]