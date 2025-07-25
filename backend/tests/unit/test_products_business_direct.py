"""
Direct Product Business API Tests - TDD verification for Issue #568
Testing the business API directly without main app
"""

import pytest
import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Direct import of our business API
from app.api.v1.products_business import router as products_router

# Create minimal test app
test_app = FastAPI()
test_app.include_router(products_router, prefix="/api/v1/business")

client = TestClient(test_app)


def test_products_endpoint_accessible():
    """Test that the products business API is accessible"""
    # Test GET endpoint - should return 422 for missing required params
    response = client.get("/api/v1/business/products/")
    assert response.status_code == 422  # Missing organization_id
    

def test_product_creation_validation():
    """Test product creation validation - should require proper data"""
    # Test with empty data - should return validation error
    response = client.post("/api/v1/business/products/", json={})
    assert response.status_code == 422
    
    # Check validation error details
    error_data = response.json()
    assert "detail" in error_data
    assert any("code" in str(error) for error in error_data["detail"])
    assert any("name" in str(error) for error in error_data["detail"])
    assert any("organization_id" in str(error) for error in error_data["detail"])


def test_product_categories_endpoint():
    """Test product categories endpoint"""
    # Test categories endpoint
    response = client.get("/api/v1/business/products/categories")
    assert response.status_code == 422  # Missing organization_id
    
    # Test category creation validation
    response = client.post("/api/v1/business/products/categories", json={})
    assert response.status_code == 422


def test_product_search_endpoint():
    """Test product search endpoint"""
    # Test search without required params
    response = client.get("/api/v1/business/products/search")
    assert response.status_code == 422  # Missing q and organization_id
    

def test_product_statistics_endpoint():
    """Test product statistics endpoint"""
    # Test statistics without organization_id
    response = client.get("/api/v1/business/products/statistics")
    assert response.status_code == 422  # Missing organization_id


def test_product_schema_validation():
    """Test comprehensive product schema validation"""
    # Test with partial valid data to check required fields
    partial_data = {
        "code": "TEST001",
        "name": "Test Product"
        # Missing organization_id and other required fields
    }
    
    response = client.post("/api/v1/business/products/", json=partial_data)
    assert response.status_code == 422
    
    error_data = response.json()
    assert "organization_id" in str(error_data)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])