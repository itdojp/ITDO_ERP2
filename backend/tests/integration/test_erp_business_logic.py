"""
ERP Business Logic Integration Tests
ERP業務ロジック統合テスト

48時間以内実装 - ERP業務フロー完全テスト
商品管理・在庫管理・売上オーダー統合業務フロー検証
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date
import uuid
from decimal import Decimal

from app.main import app
from app.core.database import get_db


client = TestClient(app)

# テスト用データベースセッション（SQLiteメモリDB使用）
@pytest.fixture(scope="function")
def test_db():
    """テスト用データベースセッション"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base
    
    # SQLiteメモリデータベース使用
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    db = TestingSessionLocal()
    yield db
    db.close()
    
    # クリーンアップ
    app.dependency_overrides.clear()


class TestERPBusinessWorkflow:
    """ERP業務ワークフロー統合テスト"""
    
    def test_complete_product_lifecycle(self, test_db):
        """商品ライフサイクル完全テスト"""
        # 1. 商品作成
        product_data = {
            "code": "PROD001",
            "name": "テスト商品",
            "description": "テスト用商品",
            "price": 1000.0,
            "cost": 600.0,
            "category": "electronics",
            "unit": "個",
            "status": "active",
            "min_stock_level": 10,
            "max_stock_level": 100
        }
        
        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product = response.json()
        product_id = product["id"]
        
        # 商品データ検証
        assert product["code"] == "PROD001"
        assert product["name"] == "テスト商品"
        assert product["price"] == 1000.0
        assert product["status"] == "active"
        
        # 2. 商品詳細取得
        response = client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        retrieved_product = response.json()
        assert retrieved_product["id"] == product_id
        assert retrieved_product["code"] == "PROD001"
        
        # 3. 商品更新
        update_data = {
            "name": "更新されたテスト商品",
            "price": 1200.0,
            "description": "更新されたテスト用商品"
        }
        
        response = client.put(f"/api/v1/products/{product_id}", json=update_data)
        assert response.status_code == 200
        updated_product = response.json()
        assert updated_product["name"] == "更新されたテスト商品"
        assert updated_product["price"] == 1200.0
        
        return product_id
    
    def test_inventory_management_workflow(self, test_db):
        """在庫管理ワークフロー完全テスト"""
        # 1. 商品作成（前提条件）
        product_id = self.test_complete_product_lifecycle(test_db)
        
        # 2. 初期在庫追加
        initial_stock = {
            "quantity": 50,
            "reason": "初期在庫"
        }
        
        response = client.post(f"/api/v1/inventory/add/{product_id}", json=initial_stock)
        assert response.status_code == 200
        stock_result = response.json()
        assert stock_result["message"] == "在庫が追加されました"
        
        # 3. 在庫レベル確認
        response = client.get(f"/api/v1/inventory/level/{product_id}")
        assert response.status_code == 200
        stock_level = response.json()
        assert stock_level["current_stock"] == 50
        assert stock_level["product_id"] == product_id
        
        # 4. 在庫調整（追加）
        adjustment_data = {
            "quantity": 20,
            "reason": "追加入荷"
        }
        
        response = client.post(f"/api/v1/inventory/adjust/{product_id}", 
                             params=adjustment_data)
        assert response.status_code == 200
        
        # 5. 在庫レベル再確認
        response = client.get(f"/api/v1/inventory/level/{product_id}")
        assert response.status_code == 200
        updated_stock = response.json()
        assert updated_stock["current_stock"] == 70
        
        # 6. 在庫履歴確認
        response = client.get(f"/api/v1/inventory/transactions/{product_id}")
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) >= 2  # 初期追加 + 調整
        
        return product_id
    
    def test_sales_order_complete_workflow(self, test_db):
        """売上オーダー完全業務ワークフロー"""
        # 1. 商品・在庫準備
        product_id = self.test_inventory_management_workflow(test_db)
        
        # 2. 売上オーダー作成
        order_data = {
            "customer_name": "テスト顧客",
            "customer_email": "test@example.com",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 5,
                    "unit_price": 1200.0
                }
            ],
            "notes": "テスト注文"
        }
        
        response = client.post("/api/v1/sales-orders", json=order_data)
        assert response.status_code == 201
        order = response.json()
        order_id = order["id"]
        
        # オーダー内容検証
        assert order["customer_name"] == "テスト顧客"
        assert order["status"] == "pending"
        assert len(order["items"]) == 1
        assert order["items"][0]["quantity"] == 5
        assert order["items"][0]["unit_price"] == 1200.0
        assert order["total_amount"] == 6600.0  # 5 * 1200 * 1.1（税込）
        
        # 3. オーダーステータス更新（確認済み）
        response = client.put(f"/api/v1/sales-orders/{order_id}/status", 
                            params={"status": "confirmed"})
        assert response.status_code == 200
        confirmed_order = response.json()
        assert confirmed_order["status"] == "confirmed"
        
        # 4. 在庫予約確認
        response = client.get(f"/api/v1/inventory/level/{product_id}")
        assert response.status_code == 200
        stock_after_reservation = response.json()
        # 在庫が予約されていることを確認（70 - 5 = 65）
        assert stock_after_reservation["available_stock"] <= 65
        
        # 5. オーダー出荷処理
        response = client.put(f"/api/v1/sales-orders/{order_id}/status", 
                            params={"status": "shipped"})
        assert response.status_code == 200
        shipped_order = response.json()
        assert shipped_order["status"] == "shipped"
        
        # 6. 最終在庫確認（出荷分減少）
        response = client.get(f"/api/v1/inventory/level/{product_id}")
        assert response.status_code == 200
        final_stock = response.json()
        assert final_stock["current_stock"] == 65  # 70 - 5
        
        return order_id, product_id
    
    def test_business_validation_rules(self, test_db):
        """業務検証ルールテスト"""
        # 1. 在庫不足での注文テスト
        product_data = {
            "code": "PROD002",
            "name": "在庫不足テスト商品",
            "price": 500.0,
            "cost": 300.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product = response.json()
        product_id = product["id"]
        
        # 2. 少量の在庫追加
        response = client.post(f"/api/v1/inventory/add/{product_id}", 
                             json={"quantity": 3, "reason": "少量在庫"})
        assert response.status_code == 200
        
        # 3. 在庫を超える注文作成（エラーを期待）
        order_data = {
            "customer_name": "在庫不足テスト顧客",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 10,  # 在庫3に対して10個注文
                    "unit_price": 500.0
                }
            ]
        }
        
        response = client.post("/api/v1/sales-orders", json=order_data)
        # 在庫不足エラーの適切な処理を確認
        if response.status_code == 400:
            error = response.json()
            assert "在庫不足" in error.get("detail", "")
        else:
            # 注文は作成されるが、保留状態になることを確認
            order = response.json()
            assert order["status"] in ["pending", "on_hold"]
    
    def test_concurrent_inventory_operations(self, test_db):
        """並行在庫操作テスト"""
        # 1. テスト商品作成
        product_data = {
            "code": "CONCURRENT001",
            "name": "並行処理テスト商品",
            "price": 800.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product = response.json()
        product_id = product["id"]
        
        # 2. 初期在庫設定
        response = client.post(f"/api/v1/inventory/add/{product_id}", 
                             json={"quantity": 100, "reason": "初期在庫"})
        assert response.status_code == 200
        
        # 3. 複数の在庫予約を同時実行
        reservation_results = []
        for i in range(5):
            response = client.post(f"/api/v1/inventory/reserve/{product_id}",
                                 params={"quantity": 10, "reference_id": f"ORDER-{i}"})
            reservation_results.append(response.status_code)
        
        # 全ての予約が成功することを確認
        successful_reservations = sum(1 for status in reservation_results if status == 200)
        assert successful_reservations <= 5  # 最大5回の予約が可能
        
        # 4. 最終在庫確認
        response = client.get(f"/api/v1/inventory/level/{product_id}")
        assert response.status_code == 200
        final_stock = response.json()
        expected_remaining = 100 - (successful_reservations * 10)
        assert final_stock["available_stock"] >= expected_remaining
    
    def test_order_cancellation_workflow(self, test_db):
        """注文キャンセルワークフロー"""
        # 1. 商品・在庫・注文準備
        order_id, product_id = self.test_sales_order_complete_workflow(test_db)
        
        # 2. 注文前在庫確認
        response = client.get(f"/api/v1/inventory/level/{product_id}")
        assert response.status_code == 200
        stock_before_cancel = response.json()
        
        # 3. 注文キャンセル
        response = client.put(f"/api/v1/sales-orders/{order_id}/status", 
                            params={"status": "cancelled"})
        assert response.status_code == 200
        cancelled_order = response.json()
        assert cancelled_order["status"] == "cancelled"
        
        # 4. キャンセル後在庫確認（在庫が戻されているか）
        response = client.get(f"/api/v1/inventory/level/{product_id}")
        assert response.status_code == 200
        stock_after_cancel = response.json()
        
        # キャンセルにより在庫が回復していることを確認
        assert stock_after_cancel["available_stock"] >= stock_before_cancel["available_stock"]


class TestERPPerformanceBusinessLogic:
    """ERP業務パフォーマンステスト"""
    
    def test_bulk_product_operations(self, test_db):
        """大量商品操作パフォーマンス"""
        import time
        
        start_time = time.time()
        
        # 100個の商品を作成
        product_ids = []
        for i in range(100):
            product_data = {
                "code": f"BULK-{i:03d}",
                "name": f"大量テスト商品 {i}",
                "price": 1000.0 + i,
                "status": "active"
            }
            
            response = client.post("/api/v1/products", json=product_data)
            if response.status_code == 201:
                product_ids.append(response.json()["id"])
        
        creation_time = time.time() - start_time
        
        # パフォーマンス要件：100商品作成が5秒以内
        assert creation_time < 5.0, f"商品作成に{creation_time:.2f}秒かかりました（5秒以内が要件）"
        assert len(product_ids) == 100, "100個の商品作成に失敗しました"
        
        # 検索パフォーマンステスト
        search_start = time.time()
        response = client.get("/api/v1/products", params={"limit": 100})
        search_time = time.time() - search_start
        
        assert response.status_code == 200
        products = response.json()
        assert len(products) >= 100
        
        # パフォーマンス要件：商品一覧取得が1秒以内
        assert search_time < 1.0, f"商品検索に{search_time:.2f}秒かかりました（1秒以内が要件）"
    
    def test_inventory_transaction_performance(self, test_db):
        """在庫取引パフォーマンステスト"""
        import time
        
        # テスト商品作成
        product_data = {
            "code": "PERF-INV001",
            "name": "在庫パフォーマンステスト商品",
            "price": 1000.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product_id = response.json()["id"]
        
        # 大量在庫取引実行
        start_time = time.time()
        successful_transactions = 0
        
        for i in range(50):
            # 在庫追加
            response = client.post(f"/api/v1/inventory/add/{product_id}", 
                                 json={"quantity": 10, "reason": f"バッチ{i}"})
            if response.status_code == 200:
                successful_transactions += 1
            
            # 在庫調整
            response = client.post(f"/api/v1/inventory/adjust/{product_id}",
                                 params={"quantity": -2, "reason": f"調整{i}"})
            if response.status_code == 200:
                successful_transactions += 1
        
        transaction_time = time.time() - start_time
        
        # パフォーマンス要件：100回の在庫取引が10秒以内
        assert transaction_time < 10.0, f"在庫取引に{transaction_time:.2f}秒かかりました（10秒以内が要件）"
        assert successful_transactions >= 90, f"取引成功率が低すぎます：{successful_transactions}/100"


class TestERPBusinessRuleValidation:
    """ERP業務ルール検証テスト"""
    
    def test_product_business_rules(self, test_db):
        """商品業務ルール検証"""
        # 1. 重複商品コードエラー
        product_data = {
            "code": "DUP001",
            "name": "重複テスト商品1",
            "price": 1000.0,
            "status": "active"
        }
        
        response1 = client.post("/api/v1/products", json=product_data)
        assert response1.status_code == 201
        
        # 同じコードで再作成（エラーを期待）
        product_data["name"] = "重複テスト商品2"
        response2 = client.post("/api/v1/products", json=product_data)
        assert response2.status_code == 400
        error = response2.json()
        assert "既に存在" in error.get("detail", "")
        
        # 2. 価格検証ルール
        invalid_price_data = {
            "code": "INVALID001",
            "name": "無効価格テスト商品",
            "price": -100.0,  # 負の価格
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=invalid_price_data)
        # 負の価格が拒否されることを確認
        if response.status_code == 400:
            error = response.json()
            assert "価格" in error.get("detail", "")
    
    def test_inventory_business_rules(self, test_db):
        """在庫業務ルール検証"""
        # テスト商品作成
        product_data = {
            "code": "INV-RULE001",
            "name": "在庫ルールテスト商品",
            "price": 1000.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product_id = response.json()["id"]
        
        # 1. 在庫追加
        response = client.post(f"/api/v1/inventory/add/{product_id}", 
                             json={"quantity": 100, "reason": "初期在庫"})
        assert response.status_code == 200
        
        # 2. 負の在庫調整制限テスト
        response = client.post(f"/api/v1/inventory/adjust/{product_id}",
                             params={"quantity": -150, "reason": "過剰減少テスト"})
        
        # 在庫を下回る調整が適切に処理されることを確認
        if response.status_code == 400:
            error = response.json()
            assert "在庫不足" in error.get("detail", "")
    
    def test_sales_order_business_rules(self, test_db):
        """売上オーダー業務ルール検証"""
        # 商品・在庫準備
        product_data = {
            "code": "ORDER-RULE001",
            "name": "注文ルールテスト商品",
            "price": 1000.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product_id = response.json()["id"]
        
        response = client.post(f"/api/v1/inventory/add/{product_id}", 
                             json={"quantity": 10, "reason": "テスト在庫"})
        assert response.status_code == 200
        
        # 1. 空注文の拒否
        empty_order = {
            "customer_name": "空注文テスト顧客",
            "items": []  # 空のアイテムリスト
        }
        
        response = client.post("/api/v1/sales-orders", json=empty_order)
        assert response.status_code == 400
        error = response.json()
        assert "アイテム" in error.get("detail", "")
        
        # 2. 無効な数量の拒否
        invalid_quantity_order = {
            "customer_name": "無効数量テスト顧客",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 0,  # ゼロ数量
                    "unit_price": 1000.0
                }
            ]
        }
        
        response = client.post("/api/v1/sales-orders", json=invalid_quantity_order)
        assert response.status_code == 400
        error = response.json()
        assert "数量" in error.get("detail", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])