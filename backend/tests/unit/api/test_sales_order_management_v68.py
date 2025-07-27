"""
ITDO ERP Backend - Sales Order Management v68 Tests
Comprehensive test suite for sales order processing functionality
Day 10: Sales Order Management Test Implementation
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.v1.sales_order_management_v68 import (
    OrderStatus,
    OrderType,
    PaymentStatus,
    SalesOrderManagementService,
    ShippingMethod,
)
from app.main import app


class TestOrderQuoteGeneration:
    """Test order quote generation functionality"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def mock_db(self):
        with patch("app.core.database.get_db") as mock:
            yield mock

    @pytest.fixture
    def mock_redis(self):
        with patch("aioredis.from_url") as mock:
            redis_client = AsyncMock()
            mock.return_value = redis_client
            yield redis_client

    async def test_create_order_quote_success(self, async_client, mock_db, mock_redis):
        """Test successful order quote creation"""
        customer_id = uuid.uuid4()
        product_id = uuid.uuid4()

        quote_request = {
            "customer_id": str(customer_id),
            "line_items": [
                {
                    "product_id": str(product_id),
                    "product_name": "Test Product",
                    "quantity": 10.0,
                    "unit_price": 100.0,
                }
            ],
            "shipping_address": {
                "name": "Test Customer",
                "address_line1": "123 Test St",
                "city": "Test City",
                "postal_code": "12345",
                "country": "USA",
            },
            "shipping_method": "standard",
        }

        with patch(
            "app.api.v1.sales_order_management_v68.SalesOrderManagementService.create_order_quote"
        ) as mock_quote:
            mock_quote.return_value = {
                "quote_id": str(uuid.uuid4()),
                "customer_id": customer_id,
                "customer_name": "Test Customer",
                "quote_date": datetime.utcnow().isoformat(),
                "valid_until": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "currency": "USD",
                "line_items": [
                    {
                        "product_id": product_id,
                        "product_name": "Test Product",
                        "quantity": 10.0,
                        "unit_price": 95.0,
                        "discount_percentage": 5.0,
                        "line_total": 950.0,
                        "availability": {"available": True},
                    }
                ],
                "subtotal": 950.0,
                "tax_total": 78.375,
                "shipping_total": 15.0,
                "total_amount": 1043.375,
            }

            response = await async_client.post(
                "/api/v1/sales/quotes", json=quote_request
            )
            assert response.status_code == 200

            result = response.json()
            assert "quote_id" in result
            assert result["customer_id"] == customer_id
            assert result["total_amount"] == 1043.375
            assert len(result["line_items"]) == 1

    async def test_quote_with_volume_discounts(self, async_client, mock_db, mock_redis):
        """Test quote generation with volume discounts"""
        customer_id = uuid.uuid4()
        product_id = uuid.uuid4()

        quote_request = {
            "customer_id": str(customer_id),
            "line_items": [
                {
                    "product_id": str(product_id),
                    "product_name": "Bulk Product",
                    "quantity": 100.0,  # High quantity for volume discount
                    "unit_price": 50.0,
                }
            ],
            "shipping_address": {
                "name": "Bulk Customer",
                "address_line1": "456 Warehouse Ave",
                "city": "Industrial City",
                "postal_code": "67890",
                "country": "USA",
            },
        }

        with patch(
            "app.api.v1.sales_order_management_v68.SalesOrderManagementService.create_order_quote"
        ) as mock_quote:
            mock_quote.return_value = {
                "quote_id": str(uuid.uuid4()),
                "line_items": [
                    {
                        "product_id": product_id,
                        "quantity": 100.0,
                        "unit_price": 45.0,  # 10% volume discount applied
                        "discount_percentage": 10.0,
                        "line_total": 4500.0,
                    }
                ],
                "subtotal": 4500.0,
                "total_amount": 4886.25,  # Including tax and shipping
            }

            response = await async_client.post(
                "/api/v1/sales/quotes", json=quote_request
            )
            assert response.status_code == 200

            result = response.json()
            assert result["line_items"][0]["discount_percentage"] == 10.0
            assert result["line_items"][0]["unit_price"] == 45.0

    async def test_quote_inventory_unavailable(self, async_client, mock_db, mock_redis):
        """Test quote when inventory is unavailable"""
        customer_id = uuid.uuid4()
        product_id = uuid.uuid4()

        quote_request = {
            "customer_id": str(customer_id),
            "line_items": [
                {
                    "product_id": str(product_id),
                    "product_name": "Out of Stock Product",
                    "quantity": 500.0,  # More than available
                    "unit_price": 75.0,
                }
            ],
            "shipping_address": {
                "name": "Test Customer",
                "address_line1": "789 Customer Rd",
                "city": "Customer City",
                "postal_code": "11111",
                "country": "USA",
            },
        }

        with patch(
            "app.api.v1.sales_order_management_v68.SalesOrderManagementService.create_order_quote"
        ) as mock_quote:
            mock_quote.return_value = {
                "quote_id": str(uuid.uuid4()),
                "line_items": [
                    {
                        "product_id": product_id,
                        "quantity": 500.0,
                        "unit_price": 75.0,
                        "line_total": 37500.0,
                        "availability": {
                            "available": False,
                            "available_quantity": 50.0,
                            "earliest_availability": (
                                datetime.utcnow() + timedelta(days=14)
                            ).isoformat(),
                        },
                    }
                ],
                "notes": "Some items have limited availability",
            }

            response = await async_client.post(
                "/api/v1/sales/quotes", json=quote_request
            )
            assert response.status_code == 200

            result = response.json()
            availability = result["line_items"][0]["availability"]
            assert not availability["available"]
            assert availability["available_quantity"] == 50.0


class TestSalesOrderCreation:
    """Test sales order creation functionality"""

    @pytest.fixture
    def sales_service(self, mock_db, mock_redis):
        return SalesOrderManagementService(mock_db, mock_redis)

    async def test_create_sales_order_success(self, sales_service):
        """Test successful sales order creation"""
        customer_id = uuid.uuid4()
        product_id = uuid.uuid4()

        order_data = Mock(
            customer_id=customer_id,
            order_type=OrderType.STANDARD,
            priority=1,
            currency="USD",
            payment_terms="Net 30",
            shipping_method=ShippingMethod.STANDARD,
            requested_delivery_date=datetime.utcnow() + timedelta(days=7),
            shipping_address=Mock(
                name="Test Customer",
                address_line1="123 Main St",
                city="Test City",
                postal_code="12345",
                country="USA",
                dict=lambda: {
                    "name": "Test Customer",
                    "address_line1": "123 Main St",
                    "city": "Test City",
                    "postal_code": "12345",
                    "country": "USA",
                },
            ),
            billing_address=None,
            line_items=[
                Mock(
                    product_id=product_id,
                    product_name="Test Product",
                    quantity=Decimal("5.0"),
                    unit_price=Decimal("100.0"),
                    notes="Test item",
                )
            ],
            notes="Test order",
            internal_notes="Internal note",
            reference_number="REF123",
            sales_rep_id=None,
        )

        # Mock all the helper methods
        with patch.object(
            sales_service, "generate_order_number", return_value="SO-20241126-000001"
        ):
            with patch.object(sales_service, "_get_customer") as mock_customer:
                mock_customer.return_value = {
                    "id": customer_id,
                    "name": "Test Customer",
                }

                with patch.object(sales_service, "_get_product_info") as mock_product:
                    mock_product.return_value = {
                        "id": product_id,
                        "sku": "TEST001",
                        "name": "Test Product",
                        "list_price": Decimal("100.0"),
                    }

                    with patch.object(
                        sales_service, "_check_inventory_availability"
                    ) as mock_inventory:
                        mock_inventory.return_value = {
                            "available": True,
                            "available_quantity": 100,
                        }

                        with patch.object(
                            sales_service, "_calculate_pricing"
                        ) as mock_pricing:
                            mock_pricing.return_value = {
                                "unit_price": Decimal("95.0"),
                                "discount_percentage": Decimal("5.0"),
                                "discount_amount": Decimal("25.0"),
                                "line_total": Decimal("475.0"),
                            }

                            with patch.object(
                                sales_service, "_calculate_tax"
                            ) as mock_tax:
                                mock_tax.return_value = {
                                    "tax_rate": Decimal("8.25"),
                                    "tax_amount": Decimal("39.19"),
                                }

                                with patch.object(
                                    sales_service, "_calculate_shipping"
                                ) as mock_shipping:
                                    mock_shipping.return_value = {
                                        "amount": Decimal("15.0")
                                    }

                                    with patch.object(
                                        sales_service, "_calculate_delivery_date"
                                    ) as mock_delivery:
                                        delivery_date = datetime.utcnow() + timedelta(
                                            days=5
                                        )
                                        mock_delivery.return_value = delivery_date

                                        with patch.object(
                                            sales_service, "_save_order_to_db"
                                        ):
                                            with patch.object(
                                                sales_service,
                                                "_create_inventory_allocations",
                                            ):
                                                with patch.object(
                                                    sales_service,
                                                    "_initiate_order_workflow",
                                                ):
                                                    with patch.object(
                                                        sales_service,
                                                        "_add_order_history",
                                                    ):
                                                        with patch.object(
                                                            sales_service,
                                                            "_send_order_notifications",
                                                        ):
                                                            sales_service.redis.setex = AsyncMock()

                                                            order_response = await sales_service.create_sales_order(
                                                                order_data
                                                            )

                                                            assert (
                                                                order_response.order_number
                                                                == "SO-20241126-000001"
                                                            )
                                                            assert (
                                                                order_response.customer_id
                                                                == customer_id
                                                            )
                                                            assert (
                                                                order_response.status
                                                                == OrderStatus.PENDING
                                                            )
                                                            assert (
                                                                order_response.subtotal
                                                                == Decimal("475.0")
                                                            )
                                                            assert (
                                                                order_response.total_amount
                                                                == Decimal("529.19")
                                                            )

    async def test_create_order_insufficient_inventory(self, sales_service):
        """Test order creation with insufficient inventory"""
        customer_id = uuid.uuid4()
        product_id = uuid.uuid4()

        order_data = Mock(
            customer_id=customer_id,
            line_items=[Mock(product_id=product_id, quantity=Decimal("100.0"))],
        )

        with patch.object(
            sales_service, "_get_customer", return_value={"id": customer_id}
        ):
            with patch.object(
                sales_service, "_get_product_info", return_value={"sku": "TEST001"}
            ):
                with patch.object(
                    sales_service, "_check_inventory_availability"
                ) as mock_inventory:
                    mock_inventory.return_value = {
                        "available": False,
                        "available_quantity": 10,
                    }

                    with pytest.raises(
                        Exception
                    ):  # Should raise insufficient inventory error
                        await sales_service.create_sales_order(order_data)

    async def test_create_order_customer_not_found(self, sales_service):
        """Test order creation with non-existent customer"""
        customer_id = uuid.uuid4()

        order_data = Mock(customer_id=customer_id)

        with patch.object(sales_service, "_get_customer", return_value=None):
            with pytest.raises(Exception):  # Should raise customer not found error
                await sales_service.create_sales_order(order_data)


class TestOrderStatusManagement:
    """Test order status management functionality"""

    @pytest.fixture
    def sales_service(self, mock_db, mock_redis):
        return SalesOrderManagementService(mock_db, mock_redis)

    async def test_update_order_status_valid_transition(self, sales_service):
        """Test valid order status transitions"""
        order_id = uuid.uuid4()

        # Mock existing order
        mock_order = Mock(
            id=order_id,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
        )

        with patch.object(sales_service, "get_order", return_value=mock_order):
            with patch.object(
                sales_service, "_validate_status_transition", return_value=True
            ):
                with patch.object(sales_service, "_update_order_status_in_db"):
                    with patch.object(sales_service, "_add_order_history"):
                        with patch.object(sales_service, "_execute_status_actions"):
                            with patch.object(
                                sales_service, "_send_order_notifications"
                            ):
                                sales_service.redis.delete = AsyncMock()

                                # Mock the final get_order call
                                updated_order = Mock(
                                    id=order_id, status=OrderStatus.CONFIRMED
                                )

                                with patch.object(
                                    sales_service,
                                    "get_order",
                                    return_value=updated_order,
                                ):
                                    result = await sales_service.update_order_status(
                                        order_id=order_id,
                                        new_status=OrderStatus.CONFIRMED,
                                        notes="Order confirmed",
                                    )

                                    assert result.status == OrderStatus.CONFIRMED

    async def test_update_order_status_invalid_transition(self, sales_service):
        """Test invalid order status transitions"""
        order_id = uuid.uuid4()

        mock_order = Mock(id=order_id, status=OrderStatus.COMPLETED)

        with patch.object(sales_service, "get_order", return_value=mock_order):
            with patch.object(
                sales_service, "_validate_status_transition", return_value=False
            ):
                with pytest.raises(Exception):  # Should raise invalid transition error
                    await sales_service.update_order_status(
                        order_id=order_id, new_status=OrderStatus.PENDING
                    )

    async def test_status_transition_validation(self, sales_service):
        """Test status transition validation logic"""
        # Test valid transitions
        assert await sales_service._validate_status_transition(
            OrderStatus.PENDING, OrderStatus.CONFIRMED
        )

        assert await sales_service._validate_status_transition(
            OrderStatus.FULFILLED, OrderStatus.SHIPPED
        )

        # Test invalid transitions
        assert not await sales_service._validate_status_transition(
            OrderStatus.COMPLETED, OrderStatus.PENDING
        )

        assert not await sales_service._validate_status_transition(
            OrderStatus.CANCELLED, OrderStatus.CONFIRMED
        )


class TestOrderFulfillment:
    """Test order fulfillment functionality"""

    @pytest.fixture
    def sales_service(self, mock_db, mock_redis):
        return SalesOrderManagementService(mock_db, mock_redis)

    async def test_fulfill_order_complete(self, sales_service):
        """Test complete order fulfillment"""
        order_id = uuid.uuid4()
        line_item_id = uuid.uuid4()
        product_id = uuid.uuid4()

        # Mock order with line items
        mock_order = Mock(
            id=order_id,
            status=OrderStatus.CONFIRMED,
            line_items=[
                Mock(id=line_item_id, product_id=product_id, quantity=Decimal("10.0"))
            ],
        )

        fulfillment_request = Mock(
            line_items=[{"line_item_id": str(line_item_id), "quantity": "10.0"}],
            tracking_number="TRACK123",
            shipping_carrier="UPS",
        )

        with patch.object(sales_service, "get_order", return_value=mock_order):
            with patch.object(
                sales_service, "_get_inventory_allocation"
            ) as mock_allocation:
                mock_allocation.return_value = {"available_quantity": Decimal("10.0")}

                with patch.object(
                    sales_service, "_create_fulfillment_record"
                ) as mock_fulfillment:
                    mock_fulfillment.return_value = {"id": uuid.uuid4()}

                    with patch.object(sales_service, "_update_inventory_allocation"):
                        with patch.object(sales_service, "update_order_status"):
                            with patch.object(
                                sales_service, "_create_shipment"
                            ) as mock_shipment:
                                mock_shipment.return_value = {
                                    "shipment_id": str(uuid.uuid4()),
                                    "tracking_number": "TRACK123",
                                }

                                result = await sales_service.fulfill_order(
                                    order_id, fulfillment_request
                                )

                                assert (
                                    result["fulfillment_status"]
                                    == OrderStatus.FULFILLED
                                )
                                assert result["fulfilled_items"] == 1
                                assert result["total_items"] == 1
                                assert len(result["fulfillment_results"]) == 1

    async def test_fulfill_order_partial(self, sales_service):
        """Test partial order fulfillment"""
        order_id = uuid.uuid4()
        line_item_id = uuid.uuid4()

        mock_order = Mock(
            id=order_id,
            status=OrderStatus.CONFIRMED,
            line_items=[
                Mock(id=line_item_id, quantity=Decimal("10.0")),
                Mock(
                    id=uuid.uuid4(), quantity=Decimal("5.0")
                ),  # Second item not fulfilled
            ],
        )

        fulfillment_request = Mock(
            line_items=[{"line_item_id": str(line_item_id), "quantity": "10.0"}]
        )

        with patch.object(sales_service, "get_order", return_value=mock_order):
            with patch.object(
                sales_service, "_get_inventory_allocation"
            ) as mock_allocation:
                mock_allocation.return_value = {"available_quantity": Decimal("10.0")}

                with patch.object(
                    sales_service, "_create_fulfillment_record"
                ) as mock_fulfillment:
                    mock_fulfillment.return_value = {"id": uuid.uuid4()}

                    with patch.object(sales_service, "_update_inventory_allocation"):
                        with patch.object(sales_service, "update_order_status"):
                            result = await sales_service.fulfill_order(
                                order_id, fulfillment_request
                            )

                            assert (
                                result["fulfillment_status"]
                                == OrderStatus.PARTIALLY_FULFILLED
                            )
                            assert result["fulfilled_items"] == 1
                            assert result["total_items"] == 2

    async def test_fulfill_order_insufficient_allocation(self, sales_service):
        """Test fulfillment with insufficient inventory allocation"""
        order_id = uuid.uuid4()
        line_item_id = uuid.uuid4()

        mock_order = Mock(
            id=order_id,
            status=OrderStatus.CONFIRMED,
            line_items=[Mock(id=line_item_id, quantity=Decimal("10.0"))],
        )

        fulfillment_request = Mock(
            line_items=[{"line_item_id": str(line_item_id), "quantity": "10.0"}]
        )

        with patch.object(sales_service, "get_order", return_value=mock_order):
            with patch.object(
                sales_service, "_get_inventory_allocation"
            ) as mock_allocation:
                mock_allocation.return_value = {
                    "available_quantity": Decimal("5.0")
                }  # Insufficient

                with pytest.raises(
                    Exception
                ):  # Should raise insufficient allocation error
                    await sales_service.fulfill_order(order_id, fulfillment_request)


class TestOrderCancellation:
    """Test order cancellation functionality"""

    @pytest.fixture
    def sales_service(self, mock_db, mock_redis):
        return SalesOrderManagementService(mock_db, mock_redis)

    async def test_cancel_order_success(self, sales_service):
        """Test successful order cancellation"""
        order_id = uuid.uuid4()

        mock_order = Mock(
            id=order_id,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
        )

        with patch.object(sales_service, "get_order", return_value=mock_order):
            with patch.object(sales_service, "_release_inventory_allocations"):
                with patch.object(sales_service, "_cancel_pending_shipments"):
                    with patch.object(sales_service, "update_order_status"):
                        # Mock final get_order call
                        cancelled_order = Mock(
                            id=order_id, status=OrderStatus.CANCELLED
                        )

                        with patch.object(
                            sales_service, "get_order", return_value=cancelled_order
                        ):
                            result = await sales_service.cancel_order(
                                order_id=order_id, reason="Customer request"
                            )

                            assert result.status == OrderStatus.CANCELLED

    async def test_cancel_order_with_refund(self, sales_service):
        """Test order cancellation with refund processing"""
        order_id = uuid.uuid4()

        mock_order = Mock(
            id=order_id, status=OrderStatus.CONFIRMED, payment_status=PaymentStatus.PAID
        )

        with patch.object(sales_service, "get_order", return_value=mock_order):
            with patch.object(sales_service, "_release_inventory_allocations"):
                with patch.object(sales_service, "_cancel_pending_shipments"):
                    with patch.object(sales_service, "update_order_status"):
                        with patch.object(
                            sales_service, "_process_refund"
                        ) as mock_refund:
                            cancelled_order = Mock(status=OrderStatus.CANCELLED)

                            with patch.object(
                                sales_service, "get_order", return_value=cancelled_order
                            ):
                                await sales_service.cancel_order(
                                    order_id=order_id, reason="Inventory shortage"
                                )

                                # Verify refund was processed
                                mock_refund.assert_called_once_with(
                                    order_id, "Inventory shortage"
                                )

    async def test_cancel_order_invalid_status(self, sales_service):
        """Test cancellation of order with invalid status"""
        order_id = uuid.uuid4()

        mock_order = Mock(
            id=order_id,
            status=OrderStatus.DELIVERED,  # Cannot cancel delivered order
        )

        with patch.object(sales_service, "get_order", return_value=mock_order):
            with pytest.raises(Exception):  # Should raise invalid status error
                await sales_service.cancel_order(
                    order_id=order_id, reason="Change of mind"
                )


class TestOrderRetrieval:
    """Test order retrieval functionality"""

    @pytest.fixture
    def sales_service(self, mock_db, mock_redis):
        return SalesOrderManagementService(mock_db, mock_redis)

    async def test_get_order_from_cache(self, sales_service):
        """Test order retrieval from Redis cache"""
        order_id = uuid.uuid4()

        cached_order_data = {
            "id": str(order_id),
            "order_number": "SO-20241126-000001",
            "status": "pending",
            "total_amount": "100.00",
        }

        sales_service.redis.get = AsyncMock(return_value=json.dumps(cached_order_data))

        result = await sales_service.get_order(order_id)

        assert result is not None
        assert result.id == order_id
        assert result.order_number == "SO-20241126-000001"

    async def test_get_order_from_database(self, sales_service):
        """Test order retrieval from database when not in cache"""
        order_id = uuid.uuid4()

        order_data = {
            "id": order_id,
            "order_number": "SO-20241126-000002",
            "customer_id": uuid.uuid4(),
            "status": OrderStatus.CONFIRMED,
            "order_type": OrderType.STANDARD,
            "priority": 1,
            "currency": "USD",
            "subtotal": Decimal("100.00"),
            "tax_total": Decimal("8.25"),
            "shipping_total": Decimal("15.00"),
            "discount_total": Decimal("0.00"),
            "total_amount": Decimal("123.25"),
            "payment_status": PaymentStatus.PENDING,
            "shipping_method": ShippingMethod.STANDARD,
            "order_date": datetime.utcnow(),
            "line_items": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Mock cache miss
        sales_service.redis.get = AsyncMock(return_value=None)
        sales_service.redis.setex = AsyncMock()

        with patch.object(sales_service, "_get_order_from_db", return_value=order_data):
            result = await sales_service.get_order(order_id)

            assert result is not None
            assert result.id == order_id
            assert result.status == OrderStatus.CONFIRMED

    async def test_get_order_not_found(self, sales_service):
        """Test order retrieval when order doesn't exist"""
        order_id = uuid.uuid4()

        # Mock cache miss and database miss
        sales_service.redis.get = AsyncMock(return_value=None)

        with patch.object(sales_service, "_get_order_from_db", return_value=None):
            result = await sales_service.get_order(order_id)

            assert result is None


class TestOrderFiltering:
    """Test order filtering and search functionality"""

    @pytest.fixture
    def sales_service(self, mock_db, mock_redis):
        return SalesOrderManagementService(mock_db, mock_redis)

    async def test_get_orders_with_filters(self, sales_service):
        """Test order retrieval with various filters"""
        customer_id = uuid.uuid4()

        mock_orders_data = {
            "orders": [
                {
                    "id": uuid.uuid4(),
                    "order_number": "SO-20241126-000001",
                    "customer_id": customer_id,
                    "status": OrderStatus.PENDING,
                    "order_type": OrderType.STANDARD,
                    "priority": 1,
                    "currency": "USD",
                    "subtotal": Decimal("100.00"),
                    "tax_total": Decimal("8.25"),
                    "shipping_total": Decimal("15.00"),
                    "discount_total": Decimal("0.00"),
                    "total_amount": Decimal("123.25"),
                    "payment_status": PaymentStatus.PENDING,
                    "shipping_method": ShippingMethod.STANDARD,
                    "order_date": datetime.utcnow(),
                    "line_items": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            ],
            "total": 1,
        }

        with patch.object(
            sales_service, "_get_orders_from_db", return_value=mock_orders_data
        ):
            result = await sales_service.get_orders(
                customer_id=customer_id, status=OrderStatus.PENDING, page=1, size=10
            )

            assert result["total"] == 1
            assert len(result["orders"]) == 1
            assert result["orders"][0].customer_id == customer_id
            assert result["orders"][0].status == OrderStatus.PENDING

    async def test_get_orders_pagination(self, sales_service):
        """Test order retrieval with pagination"""
        mock_orders_data = {
            "orders": [
                {
                    "id": uuid.uuid4(),
                    "order_number": f"SO-20241126-{i:06d}",
                    "customer_id": uuid.uuid4(),
                    "status": OrderStatus.PENDING,
                    "order_type": OrderType.STANDARD,
                    "priority": 1,
                    "currency": "USD",
                    "subtotal": Decimal("100.00"),
                    "tax_total": Decimal("8.25"),
                    "shipping_total": Decimal("15.00"),
                    "discount_total": Decimal("0.00"),
                    "total_amount": Decimal("123.25"),
                    "payment_status": PaymentStatus.PENDING,
                    "shipping_method": ShippingMethod.STANDARD,
                    "order_date": datetime.utcnow(),
                    "line_items": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                for i in range(25)  # 25 orders
            ],
            "total": 25,
        }

        with patch.object(
            sales_service, "_get_orders_from_db", return_value=mock_orders_data
        ):
            result = await sales_service.get_orders(page=1, size=10)

            assert result["total"] == 25
            assert result["page"] == 1
            assert result["size"] == 10
            assert result["pages"] == 3  # (25 + 10 - 1) // 10


class TestSalesAnalytics:
    """Test sales analytics functionality"""

    @pytest.fixture
    def sales_service(self, mock_db, mock_redis):
        return SalesOrderManagementService(mock_db, mock_redis)

    async def test_get_order_analytics(self, sales_service):
        """Test order analytics retrieval"""
        date_from = datetime.utcnow() - timedelta(days=30)
        date_to = datetime.utcnow()

        mock_analytics = {
            "total_orders": 150,
            "total_revenue": Decimal("75000.00"),
            "average_order_value": Decimal("500.00"),
            "total_items_sold": 1200,
            "status_breakdown": {
                "pending": 10,
                "confirmed": 25,
                "fulfilled": 80,
                "shipped": 30,
                "delivered": 5,
            },
            "order_type_breakdown": {"standard": 120, "rush": 20, "backorder": 10},
            "daily_trends": [
                {"date": "2024-11-01", "orders": 5, "revenue": 2500.00},
                {"date": "2024-11-02", "orders": 8, "revenue": 4000.00},
            ],
            "top_products": [
                {
                    "product_id": str(uuid.uuid4()),
                    "name": "Top Product",
                    "quantity_sold": 100,
                }
            ],
            "top_customers": [
                {
                    "customer_id": str(uuid.uuid4()),
                    "name": "Top Customer",
                    "total_orders": 15,
                }
            ],
        }

        with patch.object(
            sales_service, "_get_order_analytics_from_db", return_value=mock_analytics
        ):
            result = await sales_service.get_order_analytics(date_from, date_to)

            assert result["summary"]["total_orders"] == 150
            assert result["summary"]["total_revenue"] == 75000.00
            assert result["summary"]["average_order_value"] == 500.00
            assert len(result["status_breakdown"]) == 5
            assert len(result["daily_trends"]) == 2


class TestOrderWorkflow:
    """Test order workflow and business logic"""

    @pytest.fixture
    def sales_service(self, mock_db, mock_redis):
        return SalesOrderManagementService(mock_db, mock_redis)

    async def test_order_number_generation(self, sales_service):
        """Test order number generation"""
        sales_service.redis.incr = AsyncMock(return_value=1)
        sales_service.redis.expire = AsyncMock()

        order_number = await sales_service.generate_order_number()

        assert order_number.startswith("SO-")
        assert len(order_number) == 17  # SO-YYYYMMDD-NNNNNN

    async def test_multiple_order_number_generation(self, sales_service):
        """Test multiple order number generation increments counter"""
        sales_service.redis.incr = AsyncMock(side_effect=[1, 2, 3])
        sales_service.redis.expire = AsyncMock()

        order_numbers = []
        for _ in range(3):
            order_number = await sales_service.generate_order_number()
            order_numbers.append(order_number)

        # All should be unique and sequential
        assert len(set(order_numbers)) == 3
        assert order_numbers[0].endswith("000001")
        assert order_numbers[1].endswith("000002")
        assert order_numbers[2].endswith("000003")


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""

    async def test_complete_order_lifecycle(self, async_client, mock_db, mock_redis):
        """Test complete order lifecycle from quote to fulfillment"""
        customer_id = uuid.uuid4()
        product_id = uuid.uuid4()

        # 1. Create quote
        quote_request = {
            "customer_id": str(customer_id),
            "line_items": [
                {
                    "product_id": str(product_id),
                    "product_name": "Lifecycle Product",
                    "quantity": 5.0,
                    "unit_price": 200.0,
                }
            ],
            "shipping_address": {
                "name": "Integration Customer",
                "address_line1": "456 Integration Ave",
                "city": "Test City",
                "postal_code": "54321",
                "country": "USA",
            },
        }

        with patch(
            "app.api.v1.sales_order_management_v68.SalesOrderManagementService.create_order_quote"
        ) as mock_quote:
            quote_id = str(uuid.uuid4())
            mock_quote.return_value = {"quote_id": quote_id, "total_amount": 1100.0}

            quote_response = await async_client.post(
                "/api/v1/sales/quotes", json=quote_request
            )
            assert quote_response.status_code == 200
            quote_result = quote_response.json()
            assert quote_result["quote_id"] == quote_id

        # 2. Create order
        order_data = {
            "customer_id": str(customer_id),
            "order_type": "standard",
            "shipping_method": "standard",
            "shipping_address": quote_request["shipping_address"],
            "line_items": quote_request["line_items"],
        }

        with patch(
            "app.api.v1.sales_order_management_v68.SalesOrderManagementService.create_sales_order"
        ) as mock_order:
            order_id = uuid.uuid4()
            mock_order.return_value = Mock(
                id=order_id,
                order_number="SO-20241126-000001",
                status=OrderStatus.PENDING,
                customer_id=customer_id,
                customer_name="Integration Customer",
                order_type=OrderType.STANDARD,
                priority=1,
                currency="USD",
                subtotal=Decimal("1000.00"),
                tax_total=Decimal("82.50"),
                shipping_total=Decimal("15.00"),
                discount_total=Decimal("0.00"),
                total_amount=Decimal("1097.50"),
                payment_status=PaymentStatus.PENDING,
                shipping_method=ShippingMethod.STANDARD,
                order_date=datetime.utcnow(),
                line_items=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            order_response = await async_client.post(
                "/api/v1/sales/orders", json=order_data
            )
            assert order_response.status_code == 200
            order_result = order_response.json()
            assert order_result["status"] == "pending"

        # 3. Update status to confirmed
        status_update = {"status": "confirmed", "notes": "Payment received"}

        with patch(
            "app.api.v1.sales_order_management_v68.SalesOrderManagementService.update_order_status"
        ) as mock_status:
            mock_status.return_value = Mock(status=OrderStatus.CONFIRMED)

            status_response = await async_client.put(
                f"/api/v1/sales/orders/{order_id}/status", json=status_update
            )
            assert status_response.status_code == 200

    async def test_order_error_handling(self, async_client, mock_db, mock_redis):
        """Test error handling in order processing"""
        # Test invalid customer ID
        invalid_order_data = {
            "customer_id": str(uuid.uuid4()),
            "line_items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "product_name": "Error Product",
                    "quantity": 1.0,
                    "unit_price": 100.0,
                }
            ],
            "shipping_address": {
                "name": "Error Customer",
                "address_line1": "123 Error St",
                "city": "Error City",
                "postal_code": "00000",
                "country": "USA",
            },
        }

        with patch(
            "app.api.v1.sales_order_management_v68.SalesOrderManagementService.create_sales_order"
        ) as mock_order:
            mock_order.side_effect = Exception("Customer not found")

            response = await async_client.post(
                "/api/v1/sales/orders", json=invalid_order_data
            )
            assert response.status_code == 500


class TestPerformanceAndScalability:
    """Test performance and scalability aspects"""

    async def test_bulk_order_processing(self, async_client):
        """Test handling of multiple concurrent orders"""
        order_tasks = []

        for i in range(10):
            order_data = {
                "customer_id": str(uuid.uuid4()),
                "order_type": "standard",
                "shipping_method": "standard",
                "shipping_address": {
                    "name": f"Bulk Customer {i}",
                    "address_line1": f"{i} Bulk St",
                    "city": "Bulk City",
                    "postal_code": "99999",
                    "country": "USA",
                },
                "line_items": [
                    {
                        "product_id": str(uuid.uuid4()),
                        "product_name": f"Bulk Product {i}",
                        "quantity": 1.0,
                        "unit_price": 50.0,
                    }
                ],
            }

            with patch(
                "app.api.v1.sales_order_management_v68.SalesOrderManagementService.create_sales_order"
            ) as mock_order:
                mock_order.return_value = Mock(
                    id=uuid.uuid4(),
                    order_number=f"SO-20241126-{i:06d}",
                    status=OrderStatus.PENDING,
                    customer_id=uuid.uuid4(),
                    customer_name=f"Bulk Customer {i}",
                    order_type=OrderType.STANDARD,
                    priority=1,
                    currency="USD",
                    subtotal=Decimal("50.00"),
                    tax_total=Decimal("4.13"),
                    shipping_total=Decimal("15.00"),
                    discount_total=Decimal("0.00"),
                    total_amount=Decimal("69.13"),
                    payment_status=PaymentStatus.PENDING,
                    shipping_method=ShippingMethod.STANDARD,
                    order_date=datetime.utcnow(),
                    line_items=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                task = async_client.post("/api/v1/sales/orders", json=order_data)
                order_tasks.append(task)

        # Execute all order creation tasks concurrently
        responses = await asyncio.gather(*order_tasks, return_exceptions=True)
        successful_responses = [r for r in responses if not isinstance(r, Exception)]

        # All orders should be created successfully
        assert len(successful_responses) == 10

    async def test_large_order_line_items(self, async_client):
        """Test order with many line items"""
        line_items = []
        for i in range(100):  # 100 line items
            line_items.append(
                {
                    "product_id": str(uuid.uuid4()),
                    "product_name": f"Line Item Product {i}",
                    "quantity": 1.0,
                    "unit_price": 25.0,
                }
            )

        large_order_data = {
            "customer_id": str(uuid.uuid4()),
            "order_type": "standard",
            "shipping_method": "standard",
            "shipping_address": {
                "name": "Large Order Customer",
                "address_line1": "789 Large Order Blvd",
                "city": "Large City",
                "postal_code": "88888",
                "country": "USA",
            },
            "line_items": line_items,
        }

        with patch(
            "app.api.v1.sales_order_management_v68.SalesOrderManagementService.create_sales_order"
        ) as mock_order:
            mock_order.return_value = Mock(
                id=uuid.uuid4(),
                order_number="SO-20241126-LARGE",
                status=OrderStatus.PENDING,
                customer_id=uuid.uuid4(),
                total_amount=Decimal("2706.25"),  # 100 * 25 + tax + shipping
                line_items=line_items,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            response = await async_client.post(
                "/api/v1/sales/orders", json=large_order_data
            )
            assert response.status_code == 200

            result = response.json()
            assert len(result["line_items"]) == 100


# Test execution and coverage reporting
if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=app.api.v1.sales_order_management_v68",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=85",
        ]
    )
