"""
Simple Product API Tests - TDD verification for Issue #568
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Basic health check test"""
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}


def test_products_endpoint_exists():
    """Test that products business endpoint is accessible"""
    # This should return 422 for missing required params, not 404
    response = client.post("/api/v1/business/products/")
    assert response.status_code in [400, 422]  # Not 404, which means endpoint exists


def test_product_categories_endpoint_exists():
    """Test that product categories endpoint is accessible"""
    # This should return 422 for missing required params, not 404  
    response = client.post("/api/v1/business/products/categories")
    assert response.status_code in [400, 422]  # Not 404, which means endpoint exists