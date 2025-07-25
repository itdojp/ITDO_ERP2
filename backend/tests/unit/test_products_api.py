"""
Product Management API Tests - TDD Implementation for Issue #568
CC02 v53.0 - ERPビジネスAPI実装スプリント

Test Coverage:
- Product CRUD operations
- Product validation
- Category management  
- Stock management
- Price management
- Product search and filtering
- Error handling
- Performance requirements (<200ms)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import Dict, Any

from app.main import app
from app.models.product import Product, ProductCategory, ProductStatus, ProductType
from app.models.organization import Organization


class TestProductsAPI:
    """Commercial-grade Product Management API Tests"""

    @pytest.mark.asyncio
    async def test_create_product_success(self):
        """Test successful product creation - Required by Issue #568"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            product_data = {
                "code": "PRD001", 
                "name": "テスト商品",
                "description": "商品の説明",
                "standard_price": 1000.00,
                "cost_price": 800.00,
                "selling_price": 1200.00,
                "unit": "個",
                "product_type": "product",
                "status": "active",
                "is_active": True,
                "is_sellable": True,
                "is_purchasable": True,
                "organization_id": 1,
                "category_id": 1
            }
            
            response = await client.post("/api/v1/products", json=product_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["code"] == "PRD001"
            assert data["name"] == "テスト商品"
            assert data["standard_price"] == 1000.00
            assert data["status"] == "active"
            assert "id" in data
            assert "created_at" in data
            assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_product_duplicate_code_error(self):
        """Test product creation with duplicate code"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            product_data = {
                "code": "PRD001",
                "name": "テスト商品1",
                "standard_price": 1000.00,
                "organization_id": 1
            }
            
            # First creation should succeed
            response1 = await client.post("/api/v1/products", json=product_data)
            assert response1.status_code == 201
            
            # Second creation with same code should fail
            product_data["name"] = "テスト商品2"
            response2 = await client.post("/api/v1/products", json=product_data)
            assert response2.status_code == 400
            assert "商品コードが既に存在します" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_product_validation_error(self):
        """Test product creation with invalid data"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            invalid_data = {
                "code": "",  # Empty code
                "name": "",  # Empty name
                "standard_price": -100,  # Negative price
                "organization_id": "invalid"  # Invalid organization_id
            }
            
            response = await client.post("/api/v1/products", json=invalid_data)
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_products_success(self):
        """Test product listing with pagination"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create test products first
            for i in range(5):
                product_data = {
                    "code": f"PRD00{i+1}",
                    "name": f"テスト商品{i+1}",
                    "standard_price": 1000.00 + i*100,
                    "organization_id": 1
                }
                await client.post("/api/v1/products", json=product_data)
            
            # Test listing
            response = await client.get("/api/v1/products?skip=0&limit=3")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 3
            
            for product in data:
                assert "id" in product
                assert "code" in product
                assert "name" in product
                assert "standard_price" in product

    @pytest.mark.asyncio
    async def test_list_products_with_filters(self):
        """Test product listing with category and status filters"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test with category filter
            response = await client.get("/api/v1/products?category_id=1&is_active=true")
            assert response.status_code == 200
            
            data = response.json()
            for product in data:
                assert product.get("category_id") == 1
                assert product.get("is_active") is True

    @pytest.mark.asyncio
    async def test_get_product_by_id_success(self):
        """Test retrieving product by ID"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a product first
            product_data = {
                "code": "PRD001",
                "name": "テスト商品",
                "standard_price": 1000.00,
                "organization_id": 1
            }
            
            create_response = await client.post("/api/v1/products", json=product_data)
            created_product = create_response.json()
            product_id = created_product["id"]
            
            # Get the product
            response = await client.get(f"/api/v1/products/{product_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == product_id
            assert data["code"] == "PRD001"
            assert data["name"] == "テスト商品"

    @pytest.mark.asyncio
    async def test_get_product_not_found(self):
        """Test retrieving non-existent product"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/products/99999")
            assert response.status_code == 404
            assert "商品が見つかりません" in response.json()["detail"]

    @pytest.mark.asyncio 
    async def test_update_product_success(self):
        """Test successful product update"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a product first
            product_data = {
                "code": "PRD001",
                "name": "テスト商品",
                "standard_price": 1000.00,
                "organization_id": 1
            }
            
            create_response = await client.post("/api/v1/products", json=product_data)
            created_product = create_response.json()
            product_id = created_product["id"]
            
            # Update the product
            update_data = {
                "name": "更新されたテスト商品",
                "standard_price": 1500.00,
                "description": "更新された説明"
            }
            
            response = await client.put(f"/api/v1/products/{product_id}", json=update_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["name"] == "更新されたテスト商品"
            assert data["standard_price"] == 1500.00
            assert data["description"] == "更新された説明"
            assert data["updated_at"] != created_product["updated_at"]

    @pytest.mark.asyncio
    async def test_delete_product_success(self):
        """Test successful product deletion (soft delete)"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a product first
            product_data = {
                "code": "PRD001",
                "name": "テスト商品",
                "standard_price": 1000.00,
                "organization_id": 1
            }
            
            create_response = await client.post("/api/v1/products", json=product_data)
            created_product = create_response.json()
            product_id = created_product["id"]
            
            # Delete the product
            response = await client.delete(f"/api/v1/products/{product_id}")
            assert response.status_code == 204
            
            # Verify product is soft deleted
            get_response = await client.get(f"/api/v1/products/{product_id}")
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_search_products_by_code(self):
        """Test product search by code"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a product
            product_data = {
                "code": "PRD001",
                "name": "テスト商品",
                "standard_price": 1000.00,
                "organization_id": 1
            }
            
            await client.post("/api/v1/products", json=product_data)
            
            # Search by code
            response = await client.get("/api/v1/products/search?q=PRD001")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) >= 1
            assert any(product["code"] == "PRD001" for product in data)

    @pytest.mark.asyncio
    async def test_search_products_by_name(self):
        """Test product search by name"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Search by name
            response = await client.get("/api/v1/products/search?q=テスト")
            assert response.status_code == 200
            
            data = response.json()
            for product in data:
                assert "テスト" in product["name"] or "テスト" in product.get("description", "")

    @pytest.mark.asyncio
    async def test_adjust_stock_success(self):
        """Test stock adjustment functionality"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a product with stock management
            product_data = {
                "code": "PRD001",
                "name": "在庫管理商品",
                "standard_price": 1000.00,
                "is_stock_managed": True,
                "current_stock": 100,
                "organization_id": 1
            }
            
            create_response = await client.post("/api/v1/products", json=product_data)
            created_product = create_response.json()
            product_id = created_product["id"]
            
            # Adjust stock
            adjustment_data = {
                "quantity": 50,
                "reason": "入庫",
                "notes": "テスト在庫調整"
            }
            
            response = await client.post(f"/api/v1/products/{product_id}/adjust-stock", json=adjustment_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["new_stock"] == 150
            assert data["adjusted_by"] == 50

    @pytest.mark.asyncio
    async def test_adjust_stock_insufficient_error(self):
        """Test stock adjustment with insufficient stock"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a product with limited stock
            product_data = {
                "code": "PRD001",
                "name": "在庫管理商品",
                "standard_price": 1000.00,
                "is_stock_managed": True,
                "current_stock": 10,
                "organization_id": 1
            }
            
            create_response = await client.post("/api/v1/products", json=product_data)
            created_product = create_response.json()
            product_id = created_product["id"]
            
            # Try to reduce stock beyond available amount
            adjustment_data = {
                "quantity": -20,  # More than available
                "reason": "出庫"
            }
            
            response = await client.post(f"/api/v1/products/{product_id}/adjust-stock", json=adjustment_data)
            assert response.status_code == 400
            assert "在庫数が不足しています" in response.json()["detail"]


class TestProductCategoryAPI:
    """Product Category Management API Tests"""
    
    @pytest.mark.asyncio
    async def test_create_category_success(self):
        """Test successful category creation"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            category_data = {
                "code": "CAT001",
                "name": "テストカテゴリ",
                "description": "カテゴリの説明",
                "organization_id": 1,
                "is_active": True
            }
            
            response = await client.post("/api/v1/products/categories", json=category_data)
            assert response.status_code == 201
            
            data = response.json()
            assert data["code"] == "CAT001"
            assert data["name"] == "テストカテゴリ"
            assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_categories_success(self):
        """Test category listing"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/products/categories")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_products_by_category(self):
        """Test retrieving products by category"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create category first
            category_data = {
                "code": "CAT001",
                "name": "テストカテゴリ",
                "organization_id": 1
            }
            
            cat_response = await client.post("/api/v1/products/categories", json=category_data)
            category = cat_response.json()
            category_id = category["id"]
            
            # Create product in category
            product_data = {
                "code": "PRD001",
                "name": "カテゴリ商品",
                "standard_price": 1000.00,
                "category_id": category_id,
                "organization_id": 1
            }
            
            await client.post("/api/v1/products", json=product_data)
            
            # Get products by category
            response = await client.get(f"/api/v1/products/categories/{category_id}/products")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) >= 1
            assert all(product["category_id"] == category_id for product in data)


class TestProductPerformance:
    """Performance tests - Must meet <200ms requirement from Issue #568"""
    
    @pytest.mark.asyncio
    async def test_product_creation_performance(self):
        """Test product creation response time < 200ms"""
        import time
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            product_data = {
                "code": "PERF001",
                "name": "パフォーマンステスト商品",
                "standard_price": 1000.00,
                "organization_id": 1
            }
            
            start_time = time.time()
            response = await client.post("/api/v1/products", json=product_data) 
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 201
            assert response_time_ms < 200, f"Response time {response_time_ms}ms exceeds 200ms requirement"

    @pytest.mark.asyncio
    async def test_product_listing_performance(self):
        """Test product listing response time < 200ms"""
        import time
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()
            response = await client.get("/api/v1/products?limit=100")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time_ms < 200, f"Response time {response_time_ms}ms exceeds 200ms requirement"

    @pytest.mark.asyncio 
    async def test_product_search_performance(self):
        """Test product search response time < 200ms"""
        import time
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()
            response = await client.get("/api/v1/products/search?q=テスト")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200  
            assert response_time_ms < 200, f"Response time {response_time_ms}ms exceeds 200ms requirement"


class TestProductValidation:
    """Advanced validation tests for business rules"""
    
    @pytest.mark.asyncio
    async def test_price_validation(self):
        """Test price validation rules"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test negative prices
            invalid_data = {
                "code": "PRD001",
                "name": "テスト商品",
                "standard_price": -100.00,
                "organization_id": 1
            }
            
            response = await client.post("/api/v1/products", json=invalid_data)
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_product_status_validation(self):
        """Test product status validation"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            invalid_data = {
                "code": "PRD001", 
                "name": "テスト商品",
                "standard_price": 1000.00,
                "status": "invalid_status",  # Invalid status
                "organization_id": 1
            }
            
            response = await client.post("/api/v1/products", json=invalid_data)
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_product_type_validation(self):
        """Test product type validation"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            invalid_data = {
                "code": "PRD001",
                "name": "テスト商品", 
                "standard_price": 1000.00,
                "product_type": "invalid_type",  # Invalid type
                "organization_id": 1
            }
            
            response = await client.post("/api/v1/products", json=invalid_data)
            assert response.status_code == 422


class TestProductAuthentication:
    """Authentication and authorization tests"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self):
        """Test API access without authentication"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Remove authorization headers
            response = await client.get("/api/v1/products")
            # Should require authentication 
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_insufficient_permissions(self):
        """Test API access with insufficient permissions"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock user with read-only permissions trying to create
            headers = {"Authorization": "Bearer read_only_token"}
            
            product_data = {
                "code": "PRD001",
                "name": "テスト商品",
                "standard_price": 1000.00,
                "organization_id": 1
            }
            
            response = await client.post("/api/v1/products", json=product_data, headers=headers)
            assert response.status_code in [401, 403]


@pytest.fixture
async def sample_products():
    """Fixture to create sample products for testing"""
    products = []
    for i in range(3):
        product_data = {
            "code": f"TEST{i:03d}",
            "name": f"サンプル商品{i+1}",
            "standard_price": 1000.00 + i*500,
            "organization_id": 1
        }
        products.append(product_data)
    return products


@pytest.fixture  
async def sample_category():
    """Fixture to create sample category for testing"""
    return {
        "code": "TESTCAT",
        "name": "テストカテゴリ",
        "organization_id": 1,
        "is_active": True
    }