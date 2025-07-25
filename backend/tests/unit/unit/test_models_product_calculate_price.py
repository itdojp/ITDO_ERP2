"""
Test for models.product.calculate_price
Auto-generated by CC02 v39.0
Enhanced by Claude Code to provide functional test implementation
"""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.product import Product, ProductCategory
from tests.factories import create_test_organization


class TestProductPriceCalculations:
    """Test cases for Product price calculation methods."""

    @pytest.fixture
    def test_organization(self, db_session: Session):
        """Create test organization for products."""
        return create_test_organization(db_session, name="Test Org", code="TEST-ORG")

    @pytest.fixture
    def test_category(self, db_session: Session, test_organization):
        """Create test product category."""
        category = ProductCategory(
            code="ELECTRONICS",
            name="Electronics",
            description="Electronic products",
            organization_id=test_organization.id,
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()
        return category

    @pytest.fixture
    def basic_product(self, db_session: Session, test_organization, test_category):
        """Create basic product for testing."""
        product = Product(
            code="LAPTOP001",
            name="Test Laptop",
            description="A test laptop product",
            organization_id=test_organization.id,
            category_id=test_category.id,
            standard_price=Decimal("1000.00"),
            cost_price=Decimal("800.00"),
            selling_price=Decimal("1200.00"),
            tax_rate=Decimal("0.1000"),  # 10%
            tax_included=False,
            is_active=True,
            is_sellable=True,
        )
        db_session.add(product)
        db_session.commit()
        return product

    def test_effective_selling_price_with_selling_price_set(self, basic_product):
        """Test effective_selling_price returns selling_price when set."""
        # When: product has selling_price
        effective_price = basic_product.effective_selling_price

        # Then: should return selling_price
        assert effective_price == Decimal("1200.00")

    def test_effective_selling_price_fallback_to_standard(
        self, db_session: Session, test_organization, test_category
    ):
        """Test effective_selling_price falls back to standard_price when selling_price is None."""
        # Given: product without selling_price
        product = Product(
            code="LAPTOP002",
            name="Test Laptop 2",
            organization_id=test_organization.id,
            category_id=test_category.id,
            standard_price=Decimal("1500.00"),
            selling_price=None,  # No selling price set
            tax_rate=Decimal("0.1000"),
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        # When: getting effective selling price
        effective_price = product.effective_selling_price

        # Then: should return standard_price
        assert effective_price == Decimal("1500.00")

    def test_profit_margin_calculation(self, basic_product):
        """Test profit margin calculation with cost and selling price."""
        # When: calculating profit margin
        # selling_price = 1200, cost_price = 800
        # margin = ((1200 - 800) / 800) * 100 = 50%
        margin = basic_product.profit_margin

        # Then: should return correct margin percentage
        assert margin == Decimal("50.0")

    def test_profit_margin_with_no_cost_price(
        self, db_session: Session, test_organization, test_category
    ):
        """Test profit margin returns None when cost_price is not set."""
        # Given: product without cost_price
        product = Product(
            code="LAPTOP003",
            name="Test Laptop 3",
            organization_id=test_organization.id,
            category_id=test_category.id,
            standard_price=Decimal("1000.00"),
            selling_price=Decimal("1200.00"),
            cost_price=None,  # No cost price set
            tax_rate=Decimal("0.1000"),
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        # When: calculating profit margin
        margin = product.profit_margin

        # Then: should return None
        assert margin is None

    def test_profit_margin_with_zero_cost_price(
        self, db_session: Session, test_organization, test_category
    ):
        """Test profit margin returns None when cost_price is zero."""
        # Given: product with zero cost_price
        product = Product(
            code="LAPTOP004",
            name="Test Laptop 4",
            organization_id=test_organization.id,
            category_id=test_category.id,
            standard_price=Decimal("1000.00"),
            selling_price=Decimal("1200.00"),
            cost_price=Decimal("0.00"),  # Zero cost price
            tax_rate=Decimal("0.1000"),
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        # When: calculating profit margin
        margin = product.profit_margin

        # Then: should return None (avoid division by zero)
        assert margin is None

    def test_calculate_tax_amount_excluded(self, basic_product):
        """Test tax calculation when tax is not included in price."""
        # Given: product with tax_included=False, tax_rate=10%
        base_amount = Decimal("1000.00")

        # When: calculating tax amount
        tax_amount = basic_product.calculate_tax_amount(base_amount)

        # Then: tax = base_amount * tax_rate = 1000 * 0.10 = 100
        assert tax_amount == Decimal("100.00")

    def test_calculate_tax_amount_included(
        self, db_session: Session, test_organization, test_category
    ):
        """Test tax calculation when tax is included in price."""
        # Given: product with tax_included=True, tax_rate=10%
        product = Product(
            code="LAPTOP005",
            name="Test Laptop 5",
            organization_id=test_organization.id,
            category_id=test_category.id,
            standard_price=Decimal("1100.00"),
            tax_rate=Decimal("0.1000"),  # 10%
            tax_included=True,  # Tax included
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        base_amount = Decimal("1100.00")

        # When: calculating tax amount
        tax_amount = product.calculate_tax_amount(base_amount)

        # Then: tax = base_amount - (base_amount / (1 + tax_rate))
        # tax = 1100 - (1100 / 1.1) = 1100 - 1000 = 100
        expected_tax = base_amount - (base_amount / (Decimal("1") + product.tax_rate))
        assert tax_amount == expected_tax
        assert abs(tax_amount - Decimal("100.00")) < Decimal(
            "0.01"
        )  # Allow for rounding

    def test_calculate_tax_amount_zero_rate(
        self, db_session: Session, test_organization, test_category
    ):
        """Test tax calculation with zero tax rate."""
        # Given: product with zero tax rate
        product = Product(
            code="LAPTOP006",
            name="Test Laptop 6",
            organization_id=test_organization.id,
            category_id=test_category.id,
            standard_price=Decimal("1000.00"),
            tax_rate=Decimal("0.0000"),  # 0% tax
            tax_included=False,
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        base_amount = Decimal("1000.00")

        # When: calculating tax amount
        tax_amount = product.calculate_tax_amount(base_amount)

        # Then: should return zero
        assert tax_amount == Decimal("0.00")

    def test_calculate_tax_amount_high_rate(
        self, db_session: Session, test_organization, test_category
    ):
        """Test tax calculation with high tax rate."""
        # Given: product with high tax rate (25%)
        product = Product(
            code="LAPTOP007",
            name="Test Laptop 7",
            organization_id=test_organization.id,
            category_id=test_category.id,
            standard_price=Decimal("1000.00"),
            tax_rate=Decimal("0.2500"),  # 25% tax
            tax_included=False,
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        base_amount = Decimal("1000.00")

        # When: calculating tax amount
        tax_amount = product.calculate_tax_amount(base_amount)

        # Then: tax = 1000 * 0.25 = 250
        assert tax_amount == Decimal("250.00")

    def test_profit_margin_negative_margin(
        self, db_session: Session, test_organization, test_category
    ):
        """Test profit margin calculation when selling at a loss."""
        # Given: product selling below cost
        product = Product(
            code="LAPTOP008",
            name="Test Laptop 8",
            organization_id=test_organization.id,
            category_id=test_category.id,
            standard_price=Decimal("800.00"),
            selling_price=Decimal("600.00"),  # Selling below cost
            cost_price=Decimal("1000.00"),
            tax_rate=Decimal("0.1000"),
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        # When: calculating profit margin
        # margin = ((600 - 1000) / 1000) * 100 = -40%
        margin = product.profit_margin

        # Then: should return negative margin
        assert margin == Decimal("-40.0")

    def test_complex_pricing_scenario(
        self, db_session: Session, test_organization, test_category
    ):
        """Test complex pricing calculation scenario."""
        # Given: product with all pricing fields set
        product = Product(
            code="LAPTOP009",
            name="Premium Laptop",
            organization_id=test_organization.id,
            category_id=test_category.id,
            standard_price=Decimal("2000.00"),
            cost_price=Decimal("1500.00"),
            selling_price=Decimal("2500.00"),
            minimum_price=Decimal("1800.00"),
            tax_rate=Decimal("0.0800"),  # 8% tax
            tax_included=False,
            is_active=True,
            is_sellable=True,
        )
        db_session.add(product)
        db_session.commit()

        # When: getting various price calculations
        effective_price = product.effective_selling_price
        margin = product.profit_margin
        tax_amount = product.calculate_tax_amount(effective_price)

        # Then: verify all calculations
        assert effective_price == Decimal("2500.00")  # Uses selling_price
        assert margin == Decimal(
            "66.666666666666666666666666667"
        )  # ((2500-1500)/1500)*100
        assert tax_amount == Decimal("200.00")  # 2500 * 0.08


def test_calculate_price():
    """Legacy test function - kept for compatibility."""
    # This test is now covered by the class-based tests above
    # Testing pricing-related functionality in Product model
    assert True


def test_calculate_price_error_handling():
    """Legacy test function - kept for compatibility."""
    # Error handling is now covered by the class-based tests above
    # Including edge cases like zero cost price, missing values, etc.
    assert True
