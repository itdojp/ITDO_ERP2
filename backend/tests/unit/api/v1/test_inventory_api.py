"""Tests for inventory management API."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization import Organization
from app.models.inventory import Category, Product, StockMovement


class TestInventoryAPI:
    """Test inventory management API endpoints."""

    def test_create_category(self, client: TestClient, auth_headers: dict):
        """Test creating a product category."""
        category_data = {
            "name": "Electronics",
            "code": "ELEC",
            "description": "Electronic products and components",
            "is_active": True,
            "sort_order": 1
        }
        
        response = client.post(
            "/api/v1/inventory/categories",
            json=category_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["code"] == category_data["code"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_get_categories(self, client: TestClient, auth_headers: dict):
        """Test getting product categories."""
        response = client.get(
            "/api/v1/inventory/categories",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_product(self, client: TestClient, auth_headers: dict):
        """Test creating a product."""
        product_data = {
            "name": "Test Product",
            "sku": "TEST-001",
            "barcode": "1234567890123",
            "description": "A test product for inventory management",
            "unit_price": "99.99",
            "cost_price": "50.00",
            "track_quantity": True,
            "minimum_stock": 10,
            "maximum_stock": 100,
            "unit_of_measure": "each",
            "is_active": True,
            "is_serialized": False
        }
        
        response = client.post(
            "/api/v1/inventory/products",
            json=product_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == product_data["name"]
        assert data["sku"] == product_data["sku"]
        assert data["current_stock"] == 0  # Initial stock should be 0
        assert "id" in data

    def test_create_product_duplicate_sku(self, client: TestClient, auth_headers: dict):
        """Test creating a product with duplicate SKU should fail."""
        product_data = {
            "name": "Test Product 1",
            "sku": "DUPLICATE-SKU",
            "unit_price": "10.00"
        }
        
        # Create first product
        response1 = client.post(
            "/api/v1/inventory/products",
            json=product_data,
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Try to create second product with same SKU
        product_data["name"] = "Test Product 2"
        response2 = client.post(
            "/api/v1/inventory/products",
            json=product_data,
            headers=auth_headers
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_get_products(self, client: TestClient, auth_headers: dict):
        """Test getting products with filtering."""
        # Test basic get
        response = client.get(
            "/api/v1/inventory/products",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Test with search filter
        response = client.get(
            "/api/v1/inventory/products?search=test",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test with pagination
        response = client.get(
            "/api/v1/inventory/products?limit=10&offset=0",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_get_product_by_id(self, client: TestClient, auth_headers: dict, test_product: Product):
        """Test getting a specific product by ID."""
        response = client.get(
            f"/api/v1/inventory/products/{test_product.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product.id
        assert data["name"] == test_product.name
        assert data["sku"] == test_product.sku

    def test_update_product(self, client: TestClient, auth_headers: dict, test_product: Product):
        """Test updating a product."""
        update_data = {
            "name": "Updated Product Name",
            "unit_price": "199.99",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/inventory/products/{test_product.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    def test_create_stock_movement_in(self, client: TestClient, auth_headers: dict, test_product: Product):
        """Test creating an incoming stock movement."""
        movement_data = {
            "product_id": test_product.id,
            "movement_type": "in",
            "quantity": 50,
            "unit_cost": "45.00",
            "reference_number": "PO-001",
            "reason": "Purchase order receipt",
            "notes": "Initial stock receipt"
        }
        
        response = client.post(
            "/api/v1/inventory/stock-movements",
            json=movement_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == test_product.id
        assert data["movement_type"] == "in"
        assert data["quantity"] == 50
        assert data["previous_stock"] == 0
        assert data["new_stock"] == 50
        assert "total_cost" in data

    def test_create_stock_movement_out(self, client: TestClient, auth_headers: dict, test_product_with_stock: Product):
        """Test creating an outgoing stock movement."""
        movement_data = {
            "product_id": test_product_with_stock.id,
            "movement_type": "out",
            "quantity": 10,
            "reference_number": "SO-001",
            "reason": "Sales order fulfillment"
        }
        
        response = client.post(
            "/api/v1/inventory/stock-movements",
            json=movement_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["movement_type"] == "out"
        assert data["quantity"] == 10

    def test_create_stock_movement_insufficient_stock(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        test_product: Product
    ):
        """Test creating outgoing movement with insufficient stock should fail."""
        movement_data = {
            "product_id": test_product.id,
            "movement_type": "out",
            "quantity": 100  # More than available stock (0)
        }
        
        response = client.post(
            "/api/v1/inventory/stock-movements",
            json=movement_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Insufficient stock" in response.json()["detail"]

    def test_get_stock_movements(self, client: TestClient, auth_headers: dict):
        """Test getting stock movements with filtering."""
        response = client.get(
            "/api/v1/inventory/stock-movements",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Test with product filter
        response = client.get(
            "/api/v1/inventory/stock-movements?product_id=1",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_get_inventory_report(self, client: TestClient, auth_headers: dict):
        """Test getting inventory summary report."""
        response = client.get(
            "/api/v1/inventory/reports/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data
        assert "total_value" in data
        assert "low_stock_products" in data
        assert "out_of_stock_products" in data
        assert "categories_count" in data
        assert "movements_today" in data
        assert "generated_at" in data

    def test_get_low_stock_report(self, client: TestClient, auth_headers: dict):
        """Test getting low stock report."""
        response = client.get(
            "/api/v1/inventory/reports/low-stock",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Each item should have stock summary structure
        for item in data:
            assert "product_id" in item
            assert "product_name" in item
            assert "sku" in item
            assert "current_stock" in item
            assert "stock_status" in item

    def test_get_out_of_stock_report(self, client: TestClient, auth_headers: dict):
        """Test getting out of stock report."""
        response = client.get(
            "/api/v1/inventory/reports/out-of-stock",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_bulk_stock_movements(self, client: TestClient, auth_headers: dict, test_product: Product):
        """Test bulk stock movements."""
        movements_data = [
            {
                "product_id": test_product.id,
                "movement_type": "in",
                "quantity": 20,
                "reason": "Bulk movement 1"
            },
            {
                "product_id": test_product.id,
                "movement_type": "in",
                "quantity": 30,
                "reason": "Bulk movement 2"
            }
        ]
        
        response = client.post(
            "/api/v1/inventory/stock-movements/bulk",
            json=movements_data,
            headers=auth_headers
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["processed"] == 2
        assert data["successful"] >= 0
        assert "results" in data

    def test_unauthorized_access(self, client: TestClient):
        """Test that unauthorized users cannot access inventory endpoints."""
        response = client.get("/api/v1/inventory/products")
        assert response.status_code == 401

    def test_product_validation_errors(self, client: TestClient, auth_headers: dict):
        """Test product creation with validation errors."""
        # Missing required fields
        invalid_data = {
            "name": "",  # Empty name
            "sku": "",   # Empty SKU
            "unit_price": -10  # Negative price
        }
        
        response = client.post(
            "/api/v1/inventory/products",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error

    def test_category_hierarchy(self, client: TestClient, auth_headers: dict):
        """Test category parent-child relationships."""
        # Create parent category
        parent_data = {
            "name": "Parent Category",
            "code": "PARENT"
        }
        
        response = client.post(
            "/api/v1/inventory/categories",
            json=parent_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        parent_id = response.json()["id"]
        
        # Create child category
        child_data = {
            "name": "Child Category",
            "code": "CHILD",
            "parent_id": parent_id
        }
        
        response = client.post(
            "/api/v1/inventory/categories",
            json=child_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        child = response.json()
        assert child["parent_id"] == parent_id


# Test fixtures
@pytest.fixture
def test_product(db_session: Session, test_organization: Organization) -> Product:
    """Create a test product."""
    product = Product(
        name="Test Product",
        sku="TEST-PRODUCT-001",
        description="A test product",
        unit_price=Decimal("99.99"),
        cost_price=Decimal("50.00"),
        current_stock=0,
        minimum_stock=5,
        maximum_stock=100,
        organization_id=test_organization.id,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def test_product_with_stock(db_session: Session, test_organization: Organization) -> Product:
    """Create a test product with initial stock."""
    product = Product(
        name="Stocked Product",
        sku="STOCKED-001",
        description="A product with stock",
        unit_price=Decimal("25.00"),
        current_stock=50,
        minimum_stock=10,
        organization_id=test_organization.id,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def test_category(db_session: Session, test_organization: Organization) -> Category:
    """Create a test category."""
    category = Category(
        name="Test Category",
        code="TEST-CAT",
        description="A test category",
        organization_id=test_organization.id,
        is_active=True,
        sort_order=1
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category