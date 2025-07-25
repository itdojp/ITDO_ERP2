"""
Minimal Product Business API Integration Tests - Issue #568
Testing database integration without full app dependencies
"""

import pytest
from decimal import Decimal
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.products_business import router as products_router
from app.core.database import get_db
from app.models.base import Base
from app.models.organization import Organization
from app.models.product import Product, ProductCategory

# Minimal test app with only business API
test_app = FastAPI()
test_app.include_router(products_router, prefix="/api/v1/business")

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


test_app.dependency_overrides[get_db] = override_get_db
client = TestClient(test_app)


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


class TestProductBusinessMinimalIntegration:
    """Minimal integration tests for product business API"""

    def test_create_product_complete_workflow(self, test_organization, test_category):
        """Test complete product creation workflow with database"""
        product_data = {
            "code": "WORKFLOW_001",
            "name": "Workflow Test Product",
            "description": "Complete workflow test",
            "standard_price": 2500.00,
            "cost_price": 1800.00,
            "selling_price": 3000.00,
            "unit": "個",
            "product_type": "product",
            "status": "active",
            "is_active": True,
            "is_sellable": True,
            "is_purchasable": True,
            "is_stock_managed": True,
            "minimum_stock_level": 10.0,
            "reorder_point": 5.0,
            "manufacturer": "Test Manufacturer",
            "brand": "Test Brand",
            "warranty_period": 12,
            "organization_id": test_organization.id,
            "category_id": test_category.id
        }
        
        # Create product
        response = client.post("/api/v1/business/products/", json=product_data)
        
        assert response.status_code == 201
        created_product = response.json()
        
        # Verify all fields are properly saved
        assert created_product["code"] == "WORKFLOW_001"
        assert created_product["name"] == "Workflow Test Product"
        assert created_product["standard_price"] == 2500.00
        assert created_product["cost_price"] == 1800.00
        assert created_product["selling_price"] == 3000.00
        assert created_product["manufacturer"] == "Test Manufacturer"
        assert created_product["brand"] == "Test Brand"
        assert created_product["warranty_period"] == 12
        assert created_product["organization_id"] == test_organization.id
        assert created_product["category_id"] == test_category.id
        
        product_id = created_product["id"]
        
        # Test retrieval
        response = client.get(f"/api/v1/business/products/{product_id}?organization_id={test_organization.id}")
        assert response.status_code == 200
        
        retrieved_product = response.json()
        assert retrieved_product["id"] == product_id
        assert retrieved_product["code"] == "WORKFLOW_001"
        
        # Test update
        update_data = {
            "name": "Updated Workflow Product",
            "standard_price": 2800.00,
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/business/products/{product_id}?organization_id={test_organization.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        updated_product = response.json()
        
        assert updated_product["name"] == "Updated Workflow Product"
        assert updated_product["standard_price"] == 2800.00
        assert updated_product["description"] == "Updated description"
        
        return product_id

    def test_duplicate_code_validation(self, test_organization):
        """Test duplicate product code validation across organization"""
        product_data = {
            "code": "DUPLICATE_001",
            "name": "First Product",
            "standard_price": 1000.00,
            "organization_id": test_organization.id
        }
        
        # First creation should succeed
        response1 = client.post("/api/v1/business/products/", json=product_data)
        assert response1.status_code == 201
        
        # Second creation with same code should fail
        product_data["name"] = "Second Product"
        response2 = client.post("/api/v1/business/products/", json=product_data)
        
        assert response2.status_code == 400
        error_detail = response2.json()["detail"]
        assert "商品コードが既に存在します" in error_detail

    def test_product_listing_with_pagination(self, test_organization, test_category):
        """Test product listing with pagination and filtering"""
        # Create multiple products for pagination testing
        products_count = 5
        created_products = []
        
        for i in range(products_count):
            product_data = {
                "code": f"PAGING_{i:03d}",
                "name": f"Paging Test Product {i+1}",
                "standard_price": 1000.00 + (i * 100),
                "organization_id": test_organization.id,
                "category_id": test_category.id,
                "is_active": i % 2 == 0  # Alternate active/inactive
            }
            
            response = client.post("/api/v1/business/products/", json=product_data)
            assert response.status_code == 201
            created_products.append(response.json())
        
        # Test listing with pagination
        response = client.get(f"/api/v1/business/products/?organization_id={test_organization.id}&skip=0&limit=3")
        assert response.status_code == 200
        
        products_page1 = response.json()
        assert len(products_page1) <= 3
        
        # Test with different page
        response = client.get(f"/api/v1/business/products/?organization_id={test_organization.id}&skip=3&limit=3")
        assert response.status_code == 200
        
        products_page2 = response.json()
        
        # Verify no overlap between pages
        page1_ids = {p["id"] for p in products_page1}
        page2_ids = {p["id"] for p in products_page2}
        assert len(page1_ids.intersection(page2_ids)) == 0
        
        # Test active filter
        response = client.get(f"/api/v1/business/products/?organization_id={test_organization.id}&is_active=true")
        assert response.status_code == 200
        
        active_products = response.json()
        assert all(product["is_active"] for product in active_products)

    def test_search_functionality_comprehensive(self, test_organization):
        """Test comprehensive search functionality"""
        # Create products with various searchable content
        search_test_products = [
            {
                "code": "SEARCH_CODE_001",
                "name": "Searchable Product Alpha",
                "description": "This product contains keyword ALPHA for testing",
                "standard_price": 1000.00,
                "organization_id": test_organization.id
            },
            {
                "code": "SEARCH_CODE_002", 
                "name": "検索可能商品ベータ",
                "description": "この商品にはキーワード BETA が含まれています",
                "standard_price": 2000.00,
                "organization_id": test_organization.id
            },
            {
                "code": "DIFFERENT_003",
                "name": "Another Product",
                "description": "This has GAMMA in description",
                "standard_price": 3000.00,
                "organization_id": test_organization.id
            }
        ]
        
        # Create all test products
        for product_data in search_test_products:
            response = client.post("/api/v1/business/products/", json=product_data)
            assert response.status_code == 201
        
        # Test search by product code
        response = client.get(f"/api/v1/business/products/search?q=SEARCH_CODE&organization_id={test_organization.id}")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 2
        assert all("SEARCH_CODE" in product["code"] for product in results)
        
        # Test search by product name (English)
        response = client.get(f"/api/v1/business/products/search?q=Alpha&organization_id={test_organization.id}")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1
        assert any("Alpha" in product["name"] for product in results)
        
        # Test search by product name (Japanese)
        response = client.get(f"/api/v1/business/products/search?q=検索可能&organization_id={test_organization.id}")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1
        assert any("検索可能" in product["name"] for product in results)
        
        # Test search in description
        response = client.get(f"/api/v1/business/products/search?q=GAMMA&organization_id={test_organization.id}")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1

    def test_category_operations_full_cycle(self, test_organization):
        """Test complete category management operations"""
        # Create parent category
        parent_category_data = {
            "code": "PARENT_CAT",
            "name": "Parent Category",
            "description": "Parent category for hierarchy testing",
            "organization_id": test_organization.id,
            "is_active": True,
            "sort_order": 100
        }
        
        response = client.post("/api/v1/business/products/categories", json=parent_category_data)
        assert response.status_code == 201
        
        parent_category = response.json()
        parent_id = parent_category["id"]
        
        # Create child category
        child_category_data = {
            "code": "CHILD_CAT",
            "name": "Child Category",
            "description": "Child category for hierarchy testing",
            "organization_id": test_organization.id,
            "parent_id": parent_id,
            "is_active": True,
            "sort_order": 110
        }
        
        response = client.post("/api/v1/business/products/categories", json=child_category_data)
        assert response.status_code == 201
        
        child_category = response.json()
        child_id = child_category["id"]
        
        assert child_category["parent_id"] == parent_id
        
        # Create product in child category
        product_data = {
            "code": "CATEGORY_PROD_001",
            "name": "Product in Child Category",
            "standard_price": 1500.00,
            "organization_id": test_organization.id,
            "category_id": child_id
        }
        
        response = client.post("/api/v1/business/products/", json=product_data)
        assert response.status_code == 201
        
        # List all categories
        response = client.get(f"/api/v1/business/products/categories?organization_id={test_organization.id}")
        assert response.status_code == 200
        
        categories = response.json()
        category_codes = [cat["code"] for cat in categories]
        assert "PARENT_CAT" in category_codes
        assert "CHILD_CAT" in category_codes
        
        # Get products by category
        response = client.get(f"/api/v1/business/products/categories/{child_id}/products?organization_id={test_organization.id}")
        assert response.status_code == 200
        
        products_in_category = response.json()
        assert len(products_in_category) >= 1
        assert all(product["category_id"] == child_id for product in products_in_category)

    def test_stock_adjustment_complete(self, test_organization):
        """Test complete stock adjustment workflow"""
        # Create stock-managed product
        product_data = {
            "code": "STOCK_FULL_001",
            "name": "Full Stock Test Product",
            "standard_price": 1000.00,
            "is_stock_managed": True,
            "minimum_stock_level": 20.0,
            "reorder_point": 10.0,
            "organization_id": test_organization.id
        }
        
        response = client.post("/api/v1/business/products/", json=product_data)
        assert response.status_code == 201
        
        product = response.json()
        product_id = product["id"]
        
        # Test positive stock adjustment (receiving inventory)
        adjustment_data = {
            "quantity": 150,
            "reason": "Initial stock receipt",
            "notes": "First stock receipt from supplier"
        }
        
        response = client.post(
            f"/api/v1/business/products/{product_id}/adjust-stock?organization_id={test_organization.id}",
            json=adjustment_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["product_id"] == product_id
        assert result["adjusted_by"] == 150
        assert result["new_stock"] == 150
        assert result["reason"] == "Initial stock receipt"
        assert result["notes"] == "First stock receipt from supplier"
        
        # Test negative stock adjustment (shipping inventory)
        adjustment_data = {
            "quantity": -30,
            "reason": "Customer order fulfillment",
            "notes": "Order #12345 shipment"
        }
        
        response = client.post(
            f"/api/v1/business/products/{product_id}/adjust-stock?organization_id={test_organization.id}",
            json=adjustment_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["adjusted_by"] == -30
        assert result["new_stock"] == 120  # 150 - 30
        
        # Test invalid stock adjustment (would result in negative stock)
        adjustment_data = {
            "quantity": -200,  # More than available
            "reason": "Large order",
            "notes": "This should fail"
        }
        
        response = client.post(
            f"/api/v1/business/products/{product_id}/adjust-stock?organization_id={test_organization.id}",
            json=adjustment_data
        )
        
        assert response.status_code == 400
        assert "在庫数が不足しています" in response.json()["detail"]

    def test_statistics_comprehensive(self, test_organization, test_category):
        """Test comprehensive statistics generation"""
        # Create diverse products for statistics
        stat_products = [
            {
                "code": "STAT_ACTIVE_001",
                "name": "Active Product",
                "standard_price": 1000.00,
                "status": "active",
                "product_type": "product",
                "is_active": True,
                "organization_id": test_organization.id,
                "category_id": test_category.id
            },
            {
                "code": "STAT_INACTIVE_001",
                "name": "Inactive Product",
                "standard_price": 2000.00,
                "status": "inactive",
                "product_type": "service",
                "is_active": False,
                "organization_id": test_organization.id,
                "category_id": test_category.id
            },
            {
                "code": "STAT_DISC_001",
                "name": "Discontinued Product",
                "standard_price": 1500.00,
                "status": "discontinued",
                "product_type": "digital",
                "is_active": False,
                "organization_id": test_organization.id,
                "category_id": test_category.id
            }
        ]
        
        # Create all products
        for product_data in stat_products:
            response = client.post("/api/v1/business/products/", json=product_data)
            assert response.status_code == 201
        
        # Get comprehensive statistics
        response = client.get(f"/api/v1/business/products/statistics?organization_id={test_organization.id}")
        assert response.status_code == 200
        
        stats = response.json()
        
        # Verify required statistics fields
        required_fields = [
            "total_products", "active_products", "inactive_products",
            "status_breakdown", "type_breakdown", "generated_at"
        ]
        
        for field in required_fields:
            assert field in stats, f"Missing required field: {field}"
        
        # Verify statistics accuracy
        assert stats["total_products"] >= 3
        assert stats["active_products"] >= 1
        assert stats["inactive_products"] >= 2
        
        # Verify breakdown details
        assert "active" in stats["status_breakdown"]
        assert "inactive" in stats["status_breakdown"]
        assert "discontinued" in stats["status_breakdown"]
        
        assert "product" in stats["type_breakdown"]
        assert "service" in stats["type_breakdown"]
        assert "digital" in stats["type_breakdown"]
        
        # Verify totals match
        total_from_breakdown = sum(stats["status_breakdown"].values())
        assert total_from_breakdown == stats["total_products"]

    def test_error_handling_comprehensive(self, test_organization):
        """Test comprehensive error handling scenarios"""
        # Test missing organization
        product_data = {
            "code": "ERROR_TEST_001",
            "name": "Error Test Product",
            "standard_price": 1000.00,
            "organization_id": 99999  # Non-existent organization
        }
        
        response = client.post("/api/v1/business/products/", json=product_data)
        assert response.status_code == 404
        assert "指定された組織が見つかりません" in response.json()["detail"]
        
        # Test invalid product type
        product_data = {
            "code": "ERROR_TEST_002",
            "name": "Error Test Product 2",
            "standard_price": 1000.00,
            "product_type": "invalid_type",
            "organization_id": test_organization.id
        }
        
        response = client.post("/api/v1/business/products/", json=product_data)
        assert response.status_code == 422  # Pydantic validation error
        
        # Test invalid status
        product_data = {
            "code": "ERROR_TEST_003",
            "name": "Error Test Product 3",
            "standard_price": 1000.00,
            "status": "invalid_status",
            "organization_id": test_organization.id
        }
        
        response = client.post("/api/v1/business/products/", json=product_data)
        assert response.status_code == 422  # Pydantic validation error
        
        # Test accessing non-existent product
        response = client.get(f"/api/v1/business/products/99999?organization_id={test_organization.id}")
        assert response.status_code == 404
        assert "商品が見つかりません" in response.json()["detail"]
        
        # Test updating non-existent product
        update_data = {"name": "Updated Name"}
        response = client.put(
            f"/api/v1/business/products/99999?organization_id={test_organization.id}",
            json=update_data
        )
        assert response.status_code == 404
        assert "商品が見つかりません" in response.json()["detail"]

    def test_performance_benchmarks(self, test_organization):
        """Test performance requirements compliance"""
        import time
        
        # Prepare test data
        product_data = {
            "code": "PERF_BENCH_001",
            "name": "Performance Benchmark Product",
            "standard_price": 1000.00,
            "organization_id": test_organization.id
        }
        
        # Test product creation performance
        start_time = time.time()
        response = client.post("/api/v1/business/products/", json=product_data)
        creation_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 201
        assert creation_time < 200, f"Product creation took {creation_time:.2f}ms, exceeds 200ms requirement"
        
        # Test product retrieval performance
        product_id = response.json()["id"]
        
        start_time = time.time()
        response = client.get(f"/api/v1/business/products/{product_id}?organization_id={test_organization.id}")
        retrieval_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert retrieval_time < 200, f"Product retrieval took {retrieval_time:.2f}ms, exceeds 200ms requirement"
        
        # Test product listing performance
        start_time = time.time()
        response = client.get(f"/api/v1/business/products/?organization_id={test_organization.id}")
        listing_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert listing_time < 200, f"Product listing took {listing_time:.2f}ms, exceeds 200ms requirement"
        
        # Test search performance
        start_time = time.time()
        response = client.get(f"/api/v1/business/products/search?q=PERF&organization_id={test_organization.id}")
        search_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert search_time < 200, f"Product search took {search_time:.2f}ms, exceeds 200ms requirement"