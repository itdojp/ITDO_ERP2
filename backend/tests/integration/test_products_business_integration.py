"""
Product Business API Integration Tests - Issue #568
Testing database integration and business logic
"""

import pytest
import asyncio
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.organization import Organization
from app.models.product import Product, ProductCategory

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Setup test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_organization():
    """Create test organization"""
    db = TestingSessionLocal()
    try:
        org = Organization(
            name="Test Organization",
            code="TEST_ORG",
            is_active=True
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org
    finally:
        db.close()


@pytest.fixture
def test_category(test_organization):
    """Create test category"""
    db = TestingSessionLocal()
    try:
        category = ProductCategory(
            code="TEST_CAT",
            name="Test Category",
            organization_id=test_organization.id,
            is_active=True
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    finally:
        db.close()


class TestProductBusinessIntegration:
    """Integration tests for product business API"""

    def test_create_product_with_database(self, test_organization, test_category):
        """Test product creation with actual database"""
        product_data = {
            "code": "TEST_PROD_001",
            "name": "Integration Test Product",
            "description": "Created via integration test",
            "standard_price": 1500.00,
            "cost_price": 1000.00,
            "selling_price": 1800.00,
            "unit": "個",
            "product_type": "product",
            "status": "active",
            "is_active": True,
            "is_sellable": True,
            "is_purchasable": True,
            "organization_id": test_organization.id,
            "category_id": test_category.id
        }
        
        response = client.post("/api/v1/business/products/", json=product_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["code"] == "TEST_PROD_001"
        assert data["name"] == "Integration Test Product"
        assert data["standard_price"] == 1500.00
        assert data["organization_id"] == test_organization.id
        assert data["category_id"] == test_category.id
        assert "id" in data
        assert "created_at" in data

    def test_duplicate_product_code_error(self, test_organization):
        """Test duplicate product code validation"""
        product_data = {
            "code": "DUPLICATE_TEST",
            "name": "First Product",
            "standard_price": 1000.00,
            "organization_id": test_organization.id
        }
        
        # Create first product
        response1 = client.post("/api/v1/business/products/", json=product_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        product_data["name"] = "Second Product"
        response2 = client.post("/api/v1/business/products/", json=product_data)
        
        assert response2.status_code == 400
        assert "商品コードが既に存在します" in response2.json()["detail"]

    def test_list_products_with_filters(self, test_organization, test_category):
        """Test product listing with various filters"""
        # Create multiple test products
        products_data = [
            {
                "code": "FILTER_TEST_001",
                "name": "Active Product 1",
                "standard_price": 1000.00,
                "organization_id": test_organization.id,
                "category_id": test_category.id,
                "is_active": True,
                "status": "active"
            },
            {
                "code": "FILTER_TEST_002", 
                "name": "Inactive Product 2",
                "standard_price": 2000.00,
                "organization_id": test_organization.id,
                "category_id": test_category.id,
                "is_active": False,
                "status": "inactive"
            }
        ]
        
        # Create products
        for product_data in products_data:
            response = client.post("/api/v1/business/products/", json=product_data)
            assert response.status_code == 201
        
        # Test filter by active status
        response = client.get(f"/api/v1/business/products/?organization_id={test_organization.id}&is_active=true")
        assert response.status_code == 200
        
        active_products = response.json()
        assert len(active_products) >= 1
        assert all(product["is_active"] for product in active_products)
        
        # Test filter by category
        response = client.get(f"/api/v1/business/products/?organization_id={test_organization.id}&category_id={test_category.id}")
        assert response.status_code == 200
        
        category_products = response.json()
        assert all(product["category_id"] == test_category.id for product in category_products)

    def test_product_search_functionality(self, test_organization):
        """Test product search functionality"""
        # Create searchable products
        search_products = [
            {
                "code": "SEARCH_001",
                "name": "検索テスト商品1",
                "description": "これは検索のためのテスト商品です",
                "standard_price": 1000.00,
                "organization_id": test_organization.id
            },
            {
                "code": "SEARCH_002",
                "name": "Search Test Product 2",
                "description": "This is a test product for searching",
                "standard_price": 2000.00,
                "organization_id": test_organization.id
            }
        ]
        
        # Create products
        for product_data in search_products:
            response = client.post("/api/v1/business/products/", json=product_data)
            assert response.status_code == 201
        
        # Test search by name (Japanese)
        response = client.get(f"/api/v1/business/products/search?q=検索&organization_id={test_organization.id}")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1
        assert any("検索" in product["name"] for product in results)
        
        # Test search by code
        response = client.get(f"/api/v1/business/products/search?q=SEARCH_001&organization_id={test_organization.id}")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1
        assert any(product["code"] == "SEARCH_001" for product in results)

    def test_product_update_with_price_history(self, test_organization):
        """Test product update and price history tracking"""
        # Create product
        product_data = {
            "code": "UPDATE_TEST",
            "name": "Update Test Product",
            "standard_price": 1000.00,
            "organization_id": test_organization.id
        }
        
        create_response = client.post("/api/v1/business/products/", json=product_data)
        assert create_response.status_code == 201
        
        product = create_response.json()
        product_id = product["id"]
        
        # Update product with new price
        update_data = {
            "name": "Updated Test Product",
            "standard_price": 1500.00,
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/business/products/{product_id}?organization_id={test_organization.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        updated_product = response.json()
        
        assert updated_product["name"] == "Updated Test Product"
        assert updated_product["standard_price"] == 1500.00
        assert updated_product["description"] == "Updated description"
        assert updated_product["updated_at"] != product["updated_at"]

    def test_product_category_management(self, test_organization):
        """Test product category CRUD operations"""
        # Create category
        category_data = {
            "code": "INTEGRATION_CAT",
            "name": "Integration Test Category",
            "description": "Category for integration testing",
            "organization_id": test_organization.id,
            "is_active": True,
            "sort_order": 10
        }
        
        response = client.post("/api/v1/business/products/categories", json=category_data)
        assert response.status_code == 201
        
        category = response.json()
        assert category["code"] == "INTEGRATION_CAT"
        assert category["name"] == "Integration Test Category"
        assert category["organization_id"] == test_organization.id
        assert category["sort_order"] == 10
        
        # List categories
        response = client.get(f"/api/v1/business/products/categories?organization_id={test_organization.id}")
        assert response.status_code == 200
        
        categories = response.json()
        assert len(categories) >= 1
        assert any(cat["code"] == "INTEGRATION_CAT" for cat in categories)
        
        # Get products by category (should be empty initially)
        response = client.get(f"/api/v1/business/products/categories/{category['id']}/products?organization_id={test_organization.id}")
        assert response.status_code == 200
        
        products_in_category = response.json()
        assert isinstance(products_in_category, list)

    def test_stock_adjustment_functionality(self, test_organization):
        """Test stock adjustment features"""
        # Create product with stock management
        product_data = {
            "code": "STOCK_TEST",
            "name": "Stock Test Product",
            "standard_price": 1000.00,
            "is_stock_managed": True,
            "organization_id": test_organization.id
        }
        
        create_response = client.post("/api/v1/business/products/", json=product_data)
        assert create_response.status_code == 201
        
        product = create_response.json()
        product_id = product["id"]
        
        # Test stock adjustment
        adjustment_data = {
            "quantity": 100,
            "reason": "Initial stock",
            "notes": "Integration test stock adjustment"
        }
        
        response = client.post(
            f"/api/v1/business/products/{product_id}/adjust-stock?organization_id={test_organization.id}",
            json=adjustment_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["product_id"] == product_id
        assert result["adjusted_by"] == 100
        assert result["new_stock"] == 100  # Assuming initial stock was 0
        assert result["reason"] == "Initial stock"

    def test_product_statistics(self, test_organization, test_category):
        """Test product statistics API"""
        # Create various products for statistics
        test_products = [
            {
                "code": "STAT_ACTIVE_001",
                "name": "Active Product 1",
                "standard_price": 1000.00,
                "status": "active",
                "product_type": "product",
                "is_active": True,
                "organization_id": test_organization.id,
                "category_id": test_category.id
            },
            {
                "code": "STAT_INACTIVE_001",
                "name": "Inactive Product 1", 
                "standard_price": 2000.00,
                "status": "inactive",
                "product_type": "service",
                "is_active": False,
                "organization_id": test_organization.id,
                "category_id": test_category.id
            }
        ]
        
        # Create products
        for product_data in test_products:
            response = client.post("/api/v1/business/products/", json=product_data)
            assert response.status_code == 201
        
        # Get statistics
        response = client.get(f"/api/v1/business/products/statistics?organization_id={test_organization.id}")
        assert response.status_code == 200
        
        stats = response.json()
        
        assert "total_products" in stats
        assert "active_products" in stats
        assert "inactive_products" in stats
        assert "status_breakdown" in stats
        assert "type_breakdown" in stats
        assert "generated_at" in stats
        
        assert stats["total_products"] >= 2
        assert stats["active_products"] >= 1
        assert stats["inactive_products"] >= 1

    def test_product_deletion(self, test_organization):
        """Test product soft deletion"""
        # Create product
        product_data = {
            "code": "DELETE_TEST",
            "name": "Delete Test Product",
            "standard_price": 1000.00,
            "status": "inactive",  # Must be inactive to delete
            "organization_id": test_organization.id
        }
        
        create_response = client.post("/api/v1/business/products/", json=product_data)
        assert create_response.status_code == 201
        
        product = create_response.json()
        product_id = product["id"]
        
        # Delete product
        response = client.delete(f"/api/v1/business/products/{product_id}?organization_id={test_organization.id}")
        assert response.status_code == 204
        
        # Verify product is not accessible
        response = client.get(f"/api/v1/business/products/{product_id}?organization_id={test_organization.id}")
        assert response.status_code == 404

    def test_performance_requirements(self, test_organization):
        """Test API performance requirements (<200ms)"""
        import time
        
        # Test product creation performance
        product_data = {
            "code": "PERF_TEST_001",
            "name": "Performance Test Product",
            "standard_price": 1000.00,
            "organization_id": test_organization.id
        }
        
        start_time = time.time()
        response = client.post("/api/v1/business/products/", json=product_data)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 201
        assert response_time_ms < 200, f"Product creation took {response_time_ms}ms, exceeds 200ms requirement"
        
        # Test product listing performance
        start_time = time.time()
        response = client.get(f"/api/v1/business/products/?organization_id={test_organization.id}")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time_ms < 200, f"Product listing took {response_time_ms}ms, exceeds 200ms requirement"