import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from app.main import app
from app.schemas.purchasing_complete_v30 import (
    SupplierCreate, SupplierUpdate, PurchaseRequestCreate, PurchaseRequestItemCreate,
    PurchaseOrderCreate, PurchaseOrderItemCreate, PurchaseReceiptCreate, PurchaseReceiptItemCreate,
    SupplierProductCreate
)

client = TestClient(app)

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_current_user():
    return {"sub": str(uuid.uuid4()), "username": "testuser"}

class TestSupplierAPI:
    def test_create_supplier(self, mock_db, mock_current_user):
        """サプライヤー作成テスト"""
        supplier_data = SupplierCreate(
            supplier_code="SUP001",
            name="テストサプライヤー",
            company_name="テスト会社",
            email="supplier@example.com",
            phone="03-1234-5678",
            supplier_type="vendor",
            supplier_category="raw_materials",
            priority_level="high"
        )
        
        mock_supplier = Mock()
        mock_supplier.id = str(uuid.uuid4())
        mock_supplier.supplier_code = supplier_data.supplier_code
        mock_supplier.name = supplier_data.name
        mock_supplier.created_at = datetime.utcnow()
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.SupplierCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_supplier
            
            response = client.post("/api/v1/purchasing/suppliers", json=supplier_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once()

    def test_get_supplier(self, mock_db, mock_current_user):
        """サプライヤー詳細取得テスト"""
        supplier_id = str(uuid.uuid4())
        
        mock_supplier = Mock()
        mock_supplier.id = supplier_id
        mock_supplier.name = "テストサプライヤー"
        mock_supplier.supplier_code = "SUP001"
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.SupplierCRUD") as mock_crud:
            
            mock_crud.return_value.get_by_id.return_value = mock_supplier
            
            response = client.get(f"/api/v1/purchasing/suppliers/{supplier_id}")
            
            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(supplier_id)

    def test_list_suppliers(self, mock_db, mock_current_user):
        """サプライヤー一覧取得テスト"""
        mock_suppliers = [Mock() for _ in range(5)]
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.SupplierCRUD") as mock_crud:
            
            mock_crud.return_value.get_multi.return_value = (mock_suppliers, 5)
            
            response = client.get("/api/v1/purchasing/suppliers?page=1&per_page=20")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 5
            assert data["page"] == 1

    def test_update_supplier(self, mock_db, mock_current_user):
        """サプライヤー情報更新テスト"""
        supplier_id = str(uuid.uuid4())
        update_data = SupplierUpdate(name="更新後サプライヤー名", is_approved=True)
        
        mock_supplier = Mock()
        mock_supplier.id = supplier_id
        mock_supplier.name = update_data.name
        mock_supplier.is_approved = update_data.is_approved
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.SupplierCRUD") as mock_crud:
            
            mock_crud.return_value.update.return_value = mock_supplier
            
            response = client.put(
                f"/api/v1/purchasing/suppliers/{supplier_id}",
                json=update_data.dict(exclude_unset=True)
            )
            
            assert response.status_code == 200
            mock_crud.return_value.update.assert_called_once()

class TestPurchaseRequestAPI:
    def test_create_purchase_request(self, mock_db, mock_current_user):
        """購買リクエスト作成テスト"""
        request_data = PurchaseRequestCreate(
            supplier_id=str(uuid.uuid4()),
            priority="high",
            estimated_total=Decimal("10000"),
            justification="緊急調達",
            items=[
                PurchaseRequestItemCreate(
                    product_name="テスト商品",
                    quantity=Decimal("10"),
                    estimated_unit_price=Decimal("1000.00")
                )
            ]
        )
        
        mock_request = Mock()
        mock_request.id = str(uuid.uuid4())
        mock_request.request_number = "PR-202401-0001"
        mock_request.estimated_total = Decimal("10000.00")
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseRequestCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_request
            
            response = client.post("/api/v1/purchasing/requests", json=request_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(request_data, mock_current_user["sub"])

    def test_get_purchase_request(self, mock_db, mock_current_user):
        """購買リクエスト詳細取得テスト"""
        request_id = str(uuid.uuid4())
        
        mock_request = Mock()
        mock_request.id = request_id
        mock_request.request_number = "PR-202401-0001"
        mock_request.status = "submitted"
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseRequestCRUD") as mock_crud:
            
            mock_crud.return_value.get_by_id.return_value = mock_request
            
            response = client.get(f"/api/v1/purchasing/requests/{request_id}")
            
            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(request_id)

    def test_approve_purchase_request(self, mock_db, mock_current_user):
        """購買リクエスト承認テスト"""
        request_id = str(uuid.uuid4())
        approved_budget = Decimal("15000.00")
        
        mock_request = Mock()
        mock_request.id = request_id
        mock_request.approval_status = "approved"
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseRequestCRUD") as mock_crud:
            
            mock_crud.return_value.approve_request.return_value = mock_request
            
            response = client.post(f"/api/v1/purchasing/requests/{request_id}/approve?approved_budget={approved_budget}")
            
            assert response.status_code == 200
            mock_crud.return_value.approve_request.assert_called_once_with(request_id, mock_current_user["sub"], approved_budget)

    def test_reject_purchase_request(self, mock_db, mock_current_user):
        """購買リクエスト却下テスト"""
        request_id = str(uuid.uuid4())
        rejection_reason = "予算不足"
        
        mock_request = Mock()
        mock_request.id = request_id
        mock_request.approval_status = "rejected"
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseRequestCRUD") as mock_crud:
            
            mock_crud.return_value.reject_request.return_value = mock_request
            
            response = client.post(f"/api/v1/purchasing/requests/{request_id}/reject?rejection_reason={rejection_reason}")
            
            assert response.status_code == 200
            mock_crud.return_value.reject_request.assert_called_once_with(request_id, mock_current_user["sub"], rejection_reason)

class TestPurchaseOrderAPI:
    def test_create_purchase_order(self, mock_db, mock_current_user):
        """購買注文作成テスト"""
        order_data = PurchaseOrderCreate(
            supplier_id=str(uuid.uuid4()),
            required_delivery_date=datetime.utcnow() + timedelta(days=7),
            payment_terms="net_30",
            items=[
                PurchaseOrderItemCreate(
                    product_name="テスト商品",
                    quantity=Decimal("10"),
                    unit_price=Decimal("1000.00")
                )
            ]
        )
        
        mock_order = Mock()
        mock_order.id = str(uuid.uuid4())
        mock_order.po_number = "PO-202401-0001"
        mock_order.total_amount = Decimal("10000.00")
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseOrderCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_order
            
            response = client.post("/api/v1/purchasing/orders", json=order_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(order_data, mock_current_user["sub"])

    def test_get_purchase_order(self, mock_db, mock_current_user):
        """購買注文詳細取得テスト"""
        order_id = str(uuid.uuid4())
        
        mock_order = Mock()
        mock_order.id = order_id
        mock_order.po_number = "PO-202401-0001"
        mock_order.status = "sent"
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseOrderCRUD") as mock_crud:
            
            mock_crud.return_value.get_by_id.return_value = mock_order
            
            response = client.get(f"/api/v1/purchasing/orders/{order_id}")
            
            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(order_id)

    def test_list_purchase_orders(self, mock_db, mock_current_user):
        """購買注文一覧取得テスト"""
        mock_orders = [Mock() for _ in range(10)]
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseOrderCRUD") as mock_crud:
            
            mock_crud.return_value.get_multi.return_value = (mock_orders, 10)
            
            response = client.get("/api/v1/purchasing/orders?page=1&per_page=20")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 10
            assert data["page"] == 1

    def test_acknowledge_purchase_order(self, mock_db, mock_current_user):
        """購買注文確認テスト"""
        order_id = str(uuid.uuid4())
        
        mock_order = Mock()
        mock_order.id = order_id
        mock_order.status = "acknowledged"
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseOrderCRUD") as mock_crud:
            
            mock_crud.return_value.acknowledge_order.return_value = mock_order
            
            response = client.post(f"/api/v1/purchasing/orders/{order_id}/acknowledge")
            
            assert response.status_code == 200
            mock_crud.return_value.acknowledge_order.assert_called_once_with(order_id)

class TestPurchaseReceiptAPI:
    def test_create_purchase_receipt(self, mock_db, mock_current_user):
        """購買受領記録作成テスト"""
        receipt_data = PurchaseReceiptCreate(
            purchase_order_id=str(uuid.uuid4()),
            delivery_note_number="DN123456",
            carrier="ヤマト運輸",
            items=[
                PurchaseReceiptItemCreate(
                    purchase_order_item_id=str(uuid.uuid4()),
                    product_id=str(uuid.uuid4()),
                    received_quantity=Decimal("10"),
                    accepted_quantity=Decimal("10"),
                    quality_status="passed"
                )
            ]
        )
        
        mock_receipt = Mock()
        mock_receipt.id = str(uuid.uuid4())
        mock_receipt.receipt_number = "RC-202401-0001"
        mock_receipt.status = "received"
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseReceiptCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_receipt
            
            response = client.post("/api/v1/purchasing/receipts", json=receipt_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(receipt_data, mock_current_user["sub"])

    def test_get_purchase_receipt(self, mock_db, mock_current_user):
        """購買受領記録詳細取得テスト"""
        receipt_id = str(uuid.uuid4())
        
        mock_receipt = Mock()
        mock_receipt.id = receipt_id
        mock_receipt.receipt_number = "RC-202401-0001"
        mock_receipt.status = "received"
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseReceiptCRUD") as mock_crud:
            
            mock_crud.return_value.get_by_id.return_value = mock_receipt
            
            response = client.get(f"/api/v1/purchasing/receipts/{receipt_id}")
            
            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(receipt_id)

class TestSupplierProductAPI:
    def test_create_supplier_product(self, mock_db, mock_current_user):
        """サプライヤー商品関連作成テスト"""
        supplier_product_data = SupplierProductCreate(
            supplier_id=str(uuid.uuid4()),
            product_id=str(uuid.uuid4()),
            unit_price=Decimal("1000.00"),
            supplier_product_code="SP001",
            minimum_order_quantity=Decimal("5"),
            lead_time_days=7
        )
        
        mock_supplier_product = Mock()
        mock_supplier_product.id = str(uuid.uuid4())
        mock_supplier_product.unit_price = supplier_product_data.unit_price
        mock_supplier_product.lead_time_days = supplier_product_data.lead_time_days
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.SupplierProductCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_supplier_product
            
            response = client.post("/api/v1/purchasing/supplier-products", json=supplier_product_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(supplier_product_data)

class TestAnalyticsAPI:
    def test_get_purchase_analytics(self, mock_db, mock_current_user):
        """購買分析データ取得テスト"""
        date_from = datetime.utcnow() - timedelta(days=30)
        date_to = datetime.utcnow()
        
        mock_analytics = {
            "period_start": date_from,
            "period_end": date_to,
            "total_spend": Decimal("100000.00"),
            "orders_count": 50,
            "suppliers_count": 10,
            "avg_order_value": Decimal("2000.00"),
            "cost_savings": Decimal("5000.00"),
            "on_time_delivery_rate": Decimal("95.0"),
            "quality_rejection_rate": Decimal("2.0"),
            "daily_breakdown": [],
            "supplier_performance": []
        }
        
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.purchasing_complete_v30.PurchaseOrderCRUD") as mock_crud:
            
            mock_crud.return_value.get_purchase_analytics.return_value = mock_analytics
            
            response = client.get(
                f"/api/v1/purchasing/analytics?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}"
            )
            
            assert response.status_code == 200
            mock_crud.return_value.get_purchase_analytics.assert_called_once()

    def test_get_purchase_stats(self, mock_db, mock_current_user):
        """購買統計取得テスト"""
        with patch("app.api.v1.purchasing_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.purchasing_complete_v30.get_current_user", return_value=mock_current_user):
            
            mock_db.query.return_value.count.return_value = 50
            mock_db.query.return_value.filter.return_value.count.return_value = 40
            mock_db.query.return_value.scalar.return_value = Decimal("200000.00")
            mock_db.query.return_value.group_by.return_value.all.return_value = [("sent", 30), ("acknowledged", 20)]
            mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = [("vendor", Decimal("150000.00"))]
            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/v1/purchasing/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_suppliers" in data
            assert "total_purchase_orders" in data
            assert "total_purchases" in data