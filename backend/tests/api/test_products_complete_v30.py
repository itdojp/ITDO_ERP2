import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch
from datetime import datetime
from decimal import Decimal

from app.main import app
from app.models.product_extended import Product, ProductCategory, Supplier
from app.models.user_extended import User


class TestProductsCompleteV30:
    """Complete Product Management API Tests"""

    @pytest.fixture
    async def mock_user(self):
        """Create a mock user for testing"""
        user = User()
        user.id = "test-user-123"
        user.is_superuser = True
        return user

    @pytest.fixture
    async def mock_product(self):
        """Create a mock product for testing"""
        product = Product()
        product.id = "test-product-123"
        product.sku = "TEST-PRODUCT-001"
        product.name = "Test Product"
        product.description = "A test product for unit testing"
        product.selling_price = Decimal("1000.00")
        product.cost_price = Decimal("800.00")
        product.stock_quantity = 100
        product.reserved_quantity = 10
        product.available_quantity = 90
        product.track_inventory = True
        product.product_status = "active"
        product.product_type = "physical"
        product.is_sellable = True
        product.is_purchaseable = True
        product.unit_of_measure = "piece"
        product.brand = "Test Brand"
        product.reorder_point = 10
        product.reorder_quantity = 100
        product.created_at = datetime.utcnow()
        product.attributes = {}
        product.specifications = {}
        return product

    @pytest.fixture
    async def mock_category(self):
        """Create a mock product category for testing"""
        category = ProductCategory()
        category.id = "test-category-123"
        category.name = "Electronics"
        category.code = "ELECTRONICS"
        category.description = "Electronic products"
        category.level = 0
        category.path = "/ELECTRONICS"
        category.tax_rate = Decimal("0.10")
        category.commission_rate = Decimal("0.05")
        category.is_active = True
        category.created_at = datetime.utcnow()
        return category

    @pytest.fixture
    async def mock_supplier(self):
        """Create a mock supplier for testing"""
        supplier = Supplier()
        supplier.id = "test-supplier-123"
        supplier.name = "Test Supplier Co."
        supplier.code = "TEST_SUPPLIER"
        supplier.email = "contact@testsupplier.com"
        supplier.phone = "+81-3-1234-5678"
        supplier.country = "Japan"
        supplier.supplier_type = "manufacturer"
        supplier.is_active = True
        supplier.is_preferred = False
        supplier.quality_rating = Decimal("4.5")
        supplier.overall_rating = Decimal("4.3")
        supplier.created_at = datetime.utcnow()
        supplier.metadata_json = {}
        return supplier

    @pytest.mark.asyncio
    async def test_create_product_success(self, mock_user):
        """Test successful product creation"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            mock_product = Product()
            mock_product.id = "new-product-123"
            mock_product.sku = "NEW-PRODUCT-001"
            mock_product.name = "New Product"
            mock_product.selling_price = Decimal("1500.00")
            
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_product
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/products",
                    json={
                        "sku": "NEW-PRODUCT-001",
                        "name": "New Product",
                        "description": "A new product for testing",
                        "selling_price": "1500.00",
                        "cost_price": "1200.00",
                        "brand": "Test Brand",
                        "product_type": "physical",
                        "track_inventory": True,
                        "reorder_point": 20,
                        "reorder_quantity": 50
                    }
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["sku"] == "NEW-PRODUCT-001"
            assert data["name"] == "New Product"

    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(self, mock_user):
        """Test product creation with duplicate SKU"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            from app.crud.product_extended_v30 import DuplicateError
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.side_effect = DuplicateError("SKU already exists")
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/products",
                    json={
                        "sku": "EXISTING-SKU-001",
                        "name": "Duplicate Product",
                        "selling_price": "1000.00"
                    }
                )
            
            assert response.status_code == 400
            assert "SKU already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_products_with_filters(self, mock_user, mock_product):
        """Test products list with advanced filters"""
        with patch('app.api.v1.products_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            mock_products = [mock_product]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_multi.return_value = (mock_products, 1)
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    "/api/v1/products?search=test&brand=Test Brand&low_stock=true&price_min=500&price_max=2000"
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["items"]) == 1
            
            # Verify filters were passed correctly
            mock_crud_instance.get_multi.assert_called_once()
            call_args = mock_crud_instance.get_multi.call_args
            filters = call_args[1]["filters"]
            assert filters["search"] == "test"
            assert filters["brand"] == "Test Brand"
            assert filters["low_stock"] == True
            assert filters["price_min"] == 500
            assert filters["price_max"] == 2000

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, mock_user, mock_product):
        """Test get product by ID"""
        with patch('app.api.v1.products_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_by_id.return_value = mock_product
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/products/{mock_product.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == mock_product.id
            assert data["sku"] == mock_product.sku

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, mock_user):
        """Test get product with non-existent ID"""
        with patch('app.api.v1.products_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_by_id.return_value = None
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/products/non-existent-id")
            
            assert response.status_code == 404
            assert "Product not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_product_success(self, mock_user, mock_product):
        """Test successful product update"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            updated_product = Product()
            updated_product.id = mock_product.id
            updated_product.name = "Updated Product Name"
            updated_product.selling_price = Decimal("1200.00")
            
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.update.return_value = updated_product
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.put(
                    f"/api/v1/products/{mock_product.id}",
                    json={
                        "name": "Updated Product Name",
                        "selling_price": "1200.00"
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Product Name"

    @pytest.mark.asyncio
    async def test_delete_product_success(self, mock_user, mock_product):
        """Test successful product deletion"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.delete.return_value = True
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.delete(f"/api/v1/products/{mock_product.id}")
            
            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_product_with_inventory(self, mock_user, mock_product):
        """Test product deletion with existing inventory"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.delete.side_effect = ValueError("Cannot delete product with inventory")
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.delete(f"/api/v1/products/{mock_product.id}")
            
            assert response.status_code == 400
            assert "Cannot delete product with inventory" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_adjust_product_inventory(self, mock_user, mock_product):
        """Test product inventory adjustment"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.adjust_inventory.return_value = True
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    f"/api/v1/products/{mock_product.id}/inventory/adjust",
                    json={
                        "movement_type": "in",
                        "quantity": 50,
                        "unit_cost": "800.00",
                        "reason": "Stock replenishment"
                    }
                )
            
            assert response.status_code == 200
            assert "Inventory adjusted successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_get_product_inventory_movements(self, mock_user, mock_product):
        """Test get product inventory movements"""
        with patch('app.api.v1.products_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db:
            
            # Setup mocks
            mock_movements = []
            mock_db.return_value.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_movements
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/products/{mock_product.id}/inventory/movements")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_product_price_history(self, mock_user, mock_product):
        """Test get product price history"""
        with patch('app.api.v1.products_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db:
            
            # Setup mocks
            mock_price_history = []
            mock_db.return_value.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_price_history
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/products/{mock_product.id}/price-history")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_product_statistics(self, mock_user):
        """Test get product statistics"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            mock_stats = {
                "total_products": 150,
                "active_products": 120,
                "inactive_products": 20,
                "discontinued_products": 10,
                "by_category": {"Electronics": 50, "Clothing": 30, "Books": 70},
                "by_brand": {"Brand A": 60, "Brand B": 40, "Brand C": 50},
                "by_supplier": {"Supplier 1": 80, "Supplier 2": 70},
                "low_stock_count": 15,
                "out_of_stock_count": 5,
                "total_inventory_value": Decimal("500000.00")
            }
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_statistics.return_value = mock_stats
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/products/stats/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_products"] == 150
            assert data["active_products"] == 120
            assert "by_category" in data
            assert "by_brand" in data

    @pytest.mark.asyncio
    async def test_bulk_update_product_prices(self, mock_user):
        """Test bulk price update"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCRUD') as mock_crud:
            
            # Setup mocks
            mock_result = {
                "success_count": 2,
                "error_count": 1,
                "updated_products": ["product-1", "product-2"],
                "errors": [{"product_id": "product-3", "error": "Product not found"}]
            }
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.bulk_update_prices.return_value = mock_result
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/products/bulk/price-update",
                    json={
                        "product_ids": ["product-1", "product-2", "product-3"],
                        "price_type": "selling_price",
                        "adjustment_type": "percentage",
                        "adjustment_value": "10.0",
                        "reason": "Monthly price adjustment"
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success_count"] == 2
            assert data["error_count"] == 1
            assert len(data["updated_products"]) == 2

    @pytest.mark.asyncio
    async def test_list_product_categories(self, mock_user, mock_category):
        """Test list product categories"""
        with patch('app.api.v1.products_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCategoryCRUD') as mock_crud:
            
            # Setup mocks
            mock_categories = [mock_category]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_multi.return_value = (mock_categories, 1)
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/products/categories")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1

    @pytest.mark.asyncio
    async def test_create_product_category(self, mock_user, mock_category):
        """Test create product category"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.ProductCategoryCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_category
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/products/categories",
                    json={
                        "name": "Electronics",
                        "code": "ELECTRONICS",
                        "description": "Electronic products",
                        "tax_rate": "0.10"
                    }
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == mock_category.name

    @pytest.mark.asyncio
    async def test_list_suppliers(self, mock_user, mock_supplier):
        """Test list suppliers"""
        with patch('app.api.v1.products_complete_v30.get_current_user', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.SupplierCRUD') as mock_crud:
            
            # Setup mocks
            mock_suppliers = [mock_supplier]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_multi.return_value = (mock_suppliers, 1)
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/suppliers?is_active=true&supplier_type=manufacturer")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1

    @pytest.mark.asyncio
    async def test_create_supplier(self, mock_user, mock_supplier):
        """Test create supplier"""
        with patch('app.api.v1.products_complete_v30.require_admin', return_value=mock_user), \
             patch('app.api.v1.products_complete_v30.get_db') as mock_db, \
             patch('app.crud.product_extended_v30.SupplierCRUD') as mock_crud:
            
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_supplier
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/suppliers",
                    json={
                        "name": "Test Supplier Co.",
                        "code": "TEST_SUPPLIER",
                        "email": "contact@testsupplier.com",
                        "supplier_type": "manufacturer",
                        "country": "Japan"
                    }
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == mock_supplier.name