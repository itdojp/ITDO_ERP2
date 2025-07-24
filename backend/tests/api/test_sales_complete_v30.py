import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.sales_complete_v30 import (
    CustomerCreate,
    CustomerUpdate,
    PaymentCreate,
    QuoteCreate,
    QuoteItemCreate,
    SalesOrderCreate,
    SalesOrderItemCreate,
    ShipmentCreate,
    ShipmentItemCreate,
)

client = TestClient(app)


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def mock_current_user():
    return {"sub": str(uuid.uuid4()), "username": "testuser"}


class TestCustomerAPI:
    def test_create_customer(self, mock_db, mock_current_user):
        """顧客作成テスト"""
        customer_data = CustomerCreate(
            customer_code="CUST001",
            name="テスト顧客",
            company_name="テスト会社",
            email="test@example.com",
            phone="090-1234-5678",
            customer_type="business",
            customer_group="premium",
            priority_level="high",
        )

        mock_customer = Mock()
        mock_customer.id = str(uuid.uuid4())
        mock_customer.customer_code = customer_data.customer_code
        mock_customer.name = customer_data.name
        mock_customer.created_at = datetime.utcnow()

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.CustomerCRUD") as mock_crud,
        ):
            mock_crud.return_value.create.return_value = mock_customer

            response = client.post("/api/v1/sales/customers", json=customer_data.dict())

            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once()

    def test_get_customer(self, mock_db, mock_current_user):
        """顧客詳細取得テスト"""
        customer_id = str(uuid.uuid4())

        mock_customer = Mock()
        mock_customer.id = customer_id
        mock_customer.name = "テスト顧客"
        mock_customer.customer_code = "CUST001"

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.CustomerCRUD") as mock_crud,
        ):
            mock_crud.return_value.get_by_id.return_value = mock_customer

            response = client.get(f"/api/v1/sales/customers/{customer_id}")

            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(customer_id)

    def test_get_customer_not_found(self, mock_db, mock_current_user):
        """顧客が見つからない場合のテスト"""
        customer_id = str(uuid.uuid4())

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.CustomerCRUD") as mock_crud,
        ):
            mock_crud.return_value.get_by_id.return_value = None

            response = client.get(f"/api/v1/sales/customers/{customer_id}")

            assert response.status_code == 404

    def test_list_customers(self, mock_db, mock_current_user):
        """顧客一覧取得テスト"""
        mock_customers = [Mock() for _ in range(5)]

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.CustomerCRUD") as mock_crud,
        ):
            mock_crud.return_value.get_multi.return_value = (mock_customers, 5)

            response = client.get("/api/v1/sales/customers?page=1&per_page=20")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 5
            assert data["page"] == 1
            assert data["per_page"] == 20

    def test_update_customer(self, mock_db, mock_current_user):
        """顧客情報更新テスト"""
        customer_id = str(uuid.uuid4())
        update_data = CustomerUpdate(name="更新後顧客名", is_vip=True)

        mock_customer = Mock()
        mock_customer.id = customer_id
        mock_customer.name = update_data.name
        mock_customer.is_vip = update_data.is_vip

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.CustomerCRUD") as mock_crud,
        ):
            mock_crud.return_value.update.return_value = mock_customer

            response = client.put(
                f"/api/v1/sales/customers/{customer_id}",
                json=update_data.dict(exclude_unset=True),
            )

            assert response.status_code == 200
            mock_crud.return_value.update.assert_called_once()


class TestSalesOrderAPI:
    def test_create_sales_order(self, mock_db, mock_current_user):
        """販売注文作成テスト"""
        order_data = SalesOrderCreate(
            customer_id=str(uuid.uuid4()),
            priority="high",
            payment_terms="net_30",
            items=[
                SalesOrderItemCreate(
                    product_id=str(uuid.uuid4()),
                    quantity=Decimal("10"),
                    unit_price=Decimal("100.00"),
                )
            ],
        )

        mock_order = Mock()
        mock_order.id = str(uuid.uuid4())
        mock_order.order_number = "SO-202401-0001"
        mock_order.total_amount = Decimal("1000.00")

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.SalesOrderCRUD") as mock_crud,
        ):
            mock_crud.return_value.create.return_value = mock_order

            response = client.post("/api/v1/sales/orders", json=order_data.dict())

            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(
                order_data, mock_current_user["sub"]
            )

    def test_get_sales_order(self, mock_db, mock_current_user):
        """販売注文詳細取得テスト"""
        order_id = str(uuid.uuid4())

        mock_order = Mock()
        mock_order.id = order_id
        mock_order.order_number = "SO-202401-0001"
        mock_order.status = "confirmed"

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.SalesOrderCRUD") as mock_crud,
        ):
            mock_crud.return_value.get_by_id.return_value = mock_order

            response = client.get(f"/api/v1/sales/orders/{order_id}")

            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(order_id)

    def test_list_sales_orders(self, mock_db, mock_current_user):
        """販売注文一覧取得テスト"""
        mock_orders = [Mock() for _ in range(10)]

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.SalesOrderCRUD") as mock_crud,
        ):
            mock_crud.return_value.get_multi.return_value = (mock_orders, 10)

            response = client.get("/api/v1/sales/orders?page=1&per_page=20")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 10
            assert data["page"] == 1

    def test_confirm_sales_order(self, mock_db, mock_current_user):
        """販売注文確定テスト"""
        order_id = str(uuid.uuid4())

        mock_order = Mock()
        mock_order.id = order_id
        mock_order.status = "confirmed"

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.SalesOrderCRUD") as mock_crud,
        ):
            mock_crud.return_value.confirm_order.return_value = mock_order

            response = client.post(f"/api/v1/sales/orders/{order_id}/confirm")

            assert response.status_code == 200
            mock_crud.return_value.confirm_order.assert_called_once_with(order_id)


class TestQuoteAPI:
    def test_create_quote(self, mock_db, mock_current_user):
        """見積作成テスト"""
        quote_data = QuoteCreate(
            customer_id=str(uuid.uuid4()),
            valid_until=datetime.utcnow() + timedelta(days=30),
            win_probability=Decimal("75"),
            items=[
                QuoteItemCreate(
                    product_id=str(uuid.uuid4()),
                    quantity=Decimal("5"),
                    unit_price=Decimal("200.00"),
                )
            ],
        )

        mock_quote = Mock()
        mock_quote.id = str(uuid.uuid4())
        mock_quote.quote_number = "QT-202401-0001"
        mock_quote.total_amount = Decimal("1000.00")

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.QuoteCRUD") as mock_crud,
        ):
            mock_crud.return_value.create.return_value = mock_quote

            response = client.post("/api/v1/sales/quotes", json=quote_data.dict())

            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(
                quote_data, mock_current_user["sub"]
            )

    def test_get_quote(self, mock_db, mock_current_user):
        """見積詳細取得テスト"""
        quote_id = str(uuid.uuid4())

        mock_quote = Mock()
        mock_quote.id = quote_id
        mock_quote.quote_number = "QT-202401-0001"
        mock_quote.status = "sent"

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.QuoteCRUD") as mock_crud,
        ):
            mock_crud.return_value.get_by_id.return_value = mock_quote

            response = client.get(f"/api/v1/sales/quotes/{quote_id}")

            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(quote_id)


class TestInvoiceAPI:
    def test_create_invoice_from_order(self, mock_db, mock_current_user):
        """注文から請求書作成テスト"""
        order_id = str(uuid.uuid4())

        mock_invoice = Mock()
        mock_invoice.id = str(uuid.uuid4())
        mock_invoice.invoice_number = "INV-202401-0001"
        mock_invoice.total_amount = Decimal("1000.00")

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.InvoiceCRUD") as mock_crud,
        ):
            mock_crud.return_value.create_from_order.return_value = mock_invoice

            response = client.post(f"/api/v1/sales/invoices/from-order/{order_id}")

            assert response.status_code == 201
            mock_crud.return_value.create_from_order.assert_called_once_with(order_id)

    def test_get_invoice(self, mock_db, mock_current_user):
        """請求書詳細取得テスト"""
        invoice_id = str(uuid.uuid4())

        mock_invoice = Mock()
        mock_invoice.id = invoice_id
        mock_invoice.invoice_number = "INV-202401-0001"
        mock_invoice.status = "sent"

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.InvoiceCRUD") as mock_crud,
        ):
            mock_crud.return_value.get_by_id.return_value = mock_invoice

            response = client.get(f"/api/v1/sales/invoices/{invoice_id}")

            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(invoice_id)


class TestPaymentAPI:
    def test_record_payment(self, mock_db, mock_current_user):
        """支払記録作成テスト"""
        payment_data = PaymentCreate(
            invoice_id=str(uuid.uuid4()),
            amount=Decimal("500.00"),
            payment_method="credit_card",
            reference_number="REF123",
        )

        mock_payment = Mock()
        mock_payment.id = str(uuid.uuid4())
        mock_payment.amount = payment_data.amount
        mock_payment.status = "completed"

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.PaymentCRUD") as mock_crud,
        ):
            mock_crud.return_value.create.return_value = mock_payment

            response = client.post("/api/v1/sales/payments", json=payment_data.dict())

            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(payment_data)


class TestShipmentAPI:
    def test_create_shipment(self, mock_db, mock_current_user):
        """出荷記録作成テスト"""
        shipment_data = ShipmentCreate(
            sales_order_id=str(uuid.uuid4()),
            carrier="ヤマト運輸",
            shipping_method="宅急便",
            estimated_delivery_date=datetime.utcnow() + timedelta(days=3),
            delivery_city="東京都渋谷区",
            items=[
                ShipmentItemCreate(
                    sales_order_item_id=str(uuid.uuid4()),
                    product_id=str(uuid.uuid4()),
                    quantity_shipped=Decimal("10"),
                )
            ],
        )

        mock_shipment = Mock()
        mock_shipment.id = str(uuid.uuid4())
        mock_shipment.shipment_number = "SH-202401-0001"
        mock_shipment.status = "pending"

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.ShipmentCRUD") as mock_crud,
        ):
            mock_crud.return_value.create.return_value = mock_shipment

            response = client.post("/api/v1/sales/shipments", json=shipment_data.dict())

            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(shipment_data)


class TestAnalyticsAPI:
    def test_get_sales_analytics(self, mock_db, mock_current_user):
        """売上分析データ取得テスト"""
        date_from = datetime.utcnow() - timedelta(days=30)
        date_to = datetime.utcnow()

        mock_analytics = {
            "period_start": date_from,
            "period_end": date_to,
            "revenue": Decimal("50000.00"),
            "orders_count": 25,
            "customers_count": 15,
            "avg_order_value": Decimal("2000.00"),
            "conversion_rate": Decimal("0"),
            "growth_rate": Decimal("0"),
            "daily_breakdown": [],
        }

        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
            patch("app.api.v1.sales_complete_v30.SalesOrderCRUD") as mock_crud,
        ):
            mock_crud.return_value.get_sales_analytics.return_value = mock_analytics

            response = client.get(
                f"/api/v1/sales/analytics?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}"
            )

            assert response.status_code == 200
            mock_crud.return_value.get_sales_analytics.assert_called_once()

    def test_get_sales_stats(self, mock_db, mock_current_user):
        """売上統計取得テスト"""
        with (
            patch("app.api.v1.sales_complete_v30.get_db", return_value=mock_db),
            patch(
                "app.api.v1.sales_complete_v30.get_current_user",
                return_value=mock_current_user,
            ),
        ):
            mock_db.query.return_value.count.return_value = 100
            mock_db.query.return_value.filter.return_value.count.return_value = 80
            mock_db.query.return_value.scalar.return_value = Decimal("100000.00")
            mock_db.query.return_value.group_by.return_value.all.return_value = [
                ("confirmed", 50),
                ("shipped", 30),
            ]
            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

            response = client.get("/api/v1/sales/stats")

            assert response.status_code == 200
            data = response.json()
            assert "total_customers" in data
            assert "total_orders" in data
            assert "total_sales" in data
