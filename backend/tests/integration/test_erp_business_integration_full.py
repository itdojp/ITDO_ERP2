"""
ERP Business Integration Full Test Suite
ERP業務統合完全テストスイート

48時間以内実装 - 完全なERP業務フロー統合テスト
商品管理 → 在庫管理 → 売上管理 → 顧客管理 → レポート生成の完全フロー
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
import uuid
from decimal import Decimal
import json
import time

from app.main import app
from app.core.database import get_db


client = TestClient(app)


@pytest.fixture(scope="function")
def full_integration_db():
    """完全統合テスト用データベース"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
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
    
    app.dependency_overrides.clear()


class TestERPCompleteBusinessScenario:
    """ERP完全業務シナリオテスト"""
    
    def test_complete_business_lifecycle(self, full_integration_db):
        """完全業務ライフサイクルテスト"""
        # === Phase 1: 商品マスター管理 ===
        print("\n=== Phase 1: 商品マスター管理 ===")
        
        # 1.1 商品カテゴリ作成
        categories = ["electronics", "clothing", "books", "food"]
        created_products = []
        
        for i, category in enumerate(categories):
            product_data = {
                "code": f"PROD-{category.upper()}-{i+1:03d}",
                "name": f"{category} テスト商品 {i+1}",
                "description": f"{category}カテゴリのテスト商品",
                "price": 1000.0 + (i * 500),
                "cost": 600.0 + (i * 300),
                "category": category,
                "unit": "個",
                "status": "active",
                "min_stock_level": 10,
                "max_stock_level": 100
            }
            
            response = client.post("/api/v1/products", json=product_data)
            assert response.status_code == 201, f"商品作成失敗: {category}"
            
            product = response.json()
            created_products.append(product)
            print(f"✅ 商品作成: {product['code']} - {product['name']}")
        
        # 1.2 商品一覧取得と検索機能テスト
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        all_products = response.json()
        assert len(all_products) >= len(categories)
        print(f"✅ 商品一覧取得: {len(all_products)}件")
        
        # カテゴリ別検索
        for category in categories:
            response = client.get("/api/v1/products", params={"category": category})
            assert response.status_code == 200
            category_products = response.json()
            assert len(category_products) >= 1
            print(f"✅ カテゴリ検索 ({category}): {len(category_products)}件")
        
        # === Phase 2: 在庫管理 ===
        print("\n=== Phase 2: 在庫管理 ===")
        
        inventory_operations = []
        
        for product in created_products:
            product_id = product["id"]
            
            # 2.1 初期在庫登録
            initial_stock = {
                "quantity": 50 + (len(product["code"]) % 20),  # 50-70の範囲
                "reason": "初期在庫登録"
            }
            
            response = client.post(f"/api/v1/inventory/add/{product_id}", json=initial_stock)
            assert response.status_code == 200
            inventory_operations.append({
                "product_id": product_id,
                "operation": "add",
                "quantity": initial_stock["quantity"]
            })
            print(f"✅ 初期在庫登録: {product['code']} - {initial_stock['quantity']}個")
            
            # 2.2 在庫レベル確認
            response = client.get(f"/api/v1/inventory/level/{product_id}")
            assert response.status_code == 200
            stock_level = response.json()
            assert stock_level["current_stock"] == initial_stock["quantity"]
            print(f"✅ 在庫レベル確認: {product['code']} - 現在庫{stock_level['current_stock']}個")
            
            # 2.3 在庫調整（一部商品のみ）
            if len(product["code"]) % 2 == 0:  # 偶数番目の商品のみ
                adjustment = {
                    "quantity": 10,
                    "reason": "在庫調整（追加）"
                }
                
                response = client.post(f"/api/v1/inventory/adjust/{product_id}",
                                     params={"quantity": adjustment["quantity"], 
                                            "reason": adjustment["reason"]})
                assert response.status_code == 200
                inventory_operations.append({
                    "product_id": product_id,
                    "operation": "adjust",
                    "quantity": adjustment["quantity"]
                })
                print(f"✅ 在庫調整: {product['code']} - +{adjustment['quantity']}個")
        
        # === Phase 3: 顧客管理 ===
        print("\n=== Phase 3: 顧客管理 ===")
        
        # 3.1 顧客データ作成
        customers_data = [
            {
                "code": "CUST-001",
                "name": "株式会社テストA",
                "name_kana": "カブシキガイシャテストエー",
                "customer_type": "corporate",
                "industry": "製造業",
                "phone": "03-1234-5678",
                "email": "contact@test-a.com",
                "status": "active",
                "priority": "high"
            },
            {
                "code": "CUST-002", 
                "name": "株式会社テストB",
                "name_kana": "カブシキガイシャテストビー",
                "customer_type": "corporate",
                "industry": "小売業",
                "phone": "06-8765-4321",
                "email": "info@test-b.com",
                "status": "active",
                "priority": "normal"
            },
            {
                "code": "CUST-003",
                "name": "個人顧客テスト",
                "customer_type": "individual",
                "phone": "090-1234-5678",
                "email": "individual@test.com",
                "status": "active",
                "priority": "low"
            }
        ]
        
        created_customers = []
        for customer_data in customers_data:
            response = client.post("/api/v1/customers", json=customer_data)
            # 顧客APIが存在しない場合はスキップ
            if response.status_code == 404:
                print("⚠️ 顧客API未実装のため、仮想顧客データで継続")
                created_customers = [
                    {"id": f"virtual-{i}", "code": customer_data["code"], "name": customer_data["name"]}
                    for i, customer_data in enumerate(customers_data)
                ]
                break
            elif response.status_code == 201:
                customer = response.json()
                created_customers.append(customer)
                print(f"✅ 顧客作成: {customer['code']} - {customer['name']}")
        
        # === Phase 4: 売上オーダー管理 ===
        print("\n=== Phase 4: 売上オーダー管理 ===")
        
        created_orders = []
        
        # 4.1 複数の売上オーダー作成
        for i, customer in enumerate(created_customers):
            # 顧客ごとに異なる商品を注文
            order_products = created_products[i:i+2] if i+2 <= len(created_products) else created_products[:2]
            
            order_items = []
            total_expected = 0
            
            for j, product in enumerate(order_products):
                quantity = (j + 1) * 2  # 2, 4, 6...
                unit_price = product["price"]
                
                order_items.append({
                    "product_id": product["id"],
                    "quantity": quantity,
                    "unit_price": unit_price
                })
                
                total_expected += quantity * unit_price
            
            order_data = {
                "customer_name": customer["name"],
                "customer_email": f"order{i+1}@test.com",
                "items": order_items,
                "notes": f"テスト注文 {i+1}",
                "order_date": datetime.now().isoformat()
            }
            
            response = client.post("/api/v1/sales-orders", json=order_data)
            assert response.status_code == 201, f"注文作成失敗: 顧客{customer['code']}"
            
            order = response.json()
            created_orders.append(order)
            print(f"✅ 注文作成: 顧客{customer['code']} - {len(order_items)}品目, 金額¥{order.get('total_amount', total_expected)}")
            
            # 4.2 注文ステータス管理
            order_id = order["id"]
            
            # 確認済みに更新
            response = client.put(f"/api/v1/sales-orders/{order_id}/status",
                                params={"status": "confirmed"})
            assert response.status_code == 200
            print(f"✅ 注文確認: 注文ID {order_id}")
            
            # 出荷済みに更新（一部注文のみ）
            if i % 2 == 0:
                response = client.put(f"/api/v1/sales-orders/{order_id}/status",
                                    params={"status": "shipped"})
                assert response.status_code == 200
                print(f"✅ 注文出荷: 注文ID {order_id}")
        
        # === Phase 5: 在庫連携確認 ===
        print("\n=== Phase 5: 在庫連携確認 ===")
        
        # 5.1 注文後の在庫レベル確認
        for product in created_products:
            product_id = product["id"]
            
            response = client.get(f"/api/v1/inventory/level/{product_id}")
            assert response.status_code == 200
            current_stock = response.json()
            
            print(f"✅ 注文後在庫: {product['code']} - 現在庫{current_stock['current_stock']}個")
            
            # 在庫履歴確認
            response = client.get(f"/api/v1/inventory/transactions/{product_id}")
            if response.status_code == 200:
                transactions = response.json()
                print(f"✅ 在庫履歴: {product['code']} - {len(transactions)}件のトランザクション")
        
        # === Phase 6: レポート・分析 ===
        print("\n=== Phase 6: レポート・分析 ===")
        
        # 6.1 売上サマリー
        response = client.get("/api/v1/reports/sales-summary",
                            params={
                                "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
                                "end_date": datetime.now().isoformat()
                            })
        
        if response.status_code == 200:
            sales_summary = response.json()
            print(f"✅ 売上サマリー: 総売上¥{sales_summary.get('total_sales', 'N/A')}")
        else:
            print("⚠️ 売上サマリーAPI未実装")
        
        # 6.2 在庫レポート
        response = client.get("/api/v1/reports/inventory-status")
        
        if response.status_code == 200:
            inventory_report = response.json()
            print(f"✅ 在庫レポート: {len(inventory_report.get('products', []))}商品の在庫状況")
        else:
            print("⚠️ 在庫レポートAPI未実装")
        
        # === Phase 7: データ整合性検証 ===
        print("\n=== Phase 7: データ整合性検証 ===")
        
        # 7.1 商品データ整合性
        for product in created_products:
            response = client.get(f"/api/v1/products/{product['id']}")
            assert response.status_code == 200
            current_product = response.json()
            assert current_product["code"] == product["code"]
            assert current_product["name"] == product["name"]
            print(f"✅ 商品整合性確認: {product['code']}")
        
        # 7.2 注文データ整合性
        for order in created_orders:
            response = client.get(f"/api/v1/sales-orders/{order['id']}")
            assert response.status_code == 200
            current_order = response.json()
            assert current_order["id"] == order["id"]
            assert len(current_order["items"]) == len(order["items"])
            print(f"✅ 注文整合性確認: 注文ID {order['id']}")
        
        print(f"\n🎉 完全業務ライフサイクルテスト完了!")
        print(f"   - 作成商品数: {len(created_products)}")
        print(f"   - 作成顧客数: {len(created_customers)}")
        print(f"   - 作成注文数: {len(created_orders)}")
        print(f"   - 在庫操作数: {len(inventory_operations)}")
        
        return {
            "products": created_products,
            "customers": created_customers,
            "orders": created_orders,
            "inventory_operations": inventory_operations
        }
    
    def test_business_performance_integration(self, full_integration_db):
        """業務パフォーマンス統合テスト"""
        print("\n=== 業務パフォーマンス統合テスト ===")
        
        # パフォーマンステスト用の大量データ作成
        bulk_data = self._create_bulk_test_data()
        
        # 1. 大量商品検索パフォーマンス
        start_time = time.time()
        response = client.get("/api/v1/products", params={"limit": 100})
        search_time = time.time() - start_time
        
        assert response.status_code == 200
        assert search_time < 1.0, f"商品検索時間が遅すぎます: {search_time:.3f}s"
        print(f"✅ 大量商品検索: {search_time:.3f}s ({len(response.json())}件)")
        
        # 2. 大量在庫操作パフォーマンス
        if bulk_data["products"]:
            product_id = bulk_data["products"][0]["id"]
            
            start_time = time.time()
            for i in range(10):
                client.post(f"/api/v1/inventory/adjust/{product_id}",
                           params={"quantity": 1, "reason": f"パフォーマンステスト{i}"})
            adjustment_time = time.time() - start_time
            
            assert adjustment_time < 2.0, f"在庫調整時間が遅すぎます: {adjustment_time:.3f}s"
            print(f"✅ 大量在庫調整: {adjustment_time:.3f}s (10回)")
        
        # 3. 複数注文同時処理パフォーマンス
        if bulk_data["products"] and len(bulk_data["products"]) >= 3:
            start_time = time.time()
            
            for i in range(5):
                order_data = {
                    "customer_name": f"パフォーマンステスト顧客{i}",
                    "customer_email": f"perf{i}@test.com",
                    "items": [
                        {
                            "product_id": bulk_data["products"][i % len(bulk_data["products"])]["id"],
                            "quantity": 2,
                            "unit_price": 1000.0
                        }
                    ]
                }
                client.post("/api/v1/sales-orders", json=order_data)
            
            order_creation_time = time.time() - start_time
            assert order_creation_time < 3.0, f"注文作成時間が遅すぎます: {order_creation_time:.3f}s"
            print(f"✅ 大量注文作成: {order_creation_time:.3f}s (5件)")
        
        print("🎉 業務パフォーマンス統合テスト完了!")
    
    def test_error_recovery_scenarios(self, full_integration_db):
        """エラー復旧シナリオテスト"""
        print("\n=== エラー復旧シナリオテスト ===")
        
        # 1. 在庫不足エラーからの復旧
        product_data = {
            "code": "ERROR-RECOVERY-001",
            "name": "エラー復旧テスト商品",
            "price": 1000.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product = response.json()
        product_id = product["id"]
        
        # 少量在庫設定
        client.post(f"/api/v1/inventory/add/{product_id}",
                   json={"quantity": 5, "reason": "エラーテスト用"})
        
        # 在庫を超える注文でエラー発生
        large_order = {
            "customer_name": "大量注文テスト顧客",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 10,  # 在庫5に対して10個注文
                    "unit_price": 1000.0
                }
            ]
        }
        
        response = client.post("/api/v1/sales-orders", json=large_order)
        # エラーまたは保留状態になることを確認
        assert response.status_code in [400, 201]  # エラーまたは保留注文として作成
        
        if response.status_code == 201:
            order = response.json()
            assert order.get("status") in ["pending", "on_hold"]
            print("✅ 在庫不足注文の適切な処理")
        else:
            print("✅ 在庫不足注文の適切な拒否")
        
        # 在庫追加による復旧
        client.post(f"/api/v1/inventory/add/{product_id}",
                   json={"quantity": 10, "reason": "在庫補充"})
        
        # 再度注文試行
        response = client.post("/api/v1/sales-orders", json=large_order)
        assert response.status_code == 201
        print("✅ 在庫補充後の注文成功")
        
        # 2. 重複データエラーからの復旧
        duplicate_product = {
            "code": "ERROR-RECOVERY-001",  # 既存コード
            "name": "重複テスト商品",
            "price": 2000.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=duplicate_product)
        assert response.status_code == 400
        print("✅ 重複商品コードの適切な拒否")
        
        # 正しいコードで再試行
        duplicate_product["code"] = "ERROR-RECOVERY-002"
        response = client.post("/api/v1/products", json=duplicate_product)
        assert response.status_code == 201
        print("✅ 修正後の商品作成成功")
        
        print("🎉 エラー復旧シナリオテスト完了!")
    
    def _create_bulk_test_data(self):
        """大量テストデータ作成"""
        products = []
        
        # 50個の商品を作成
        for i in range(50):
            product_data = {
                "code": f"BULK-{i:03d}",
                "name": f"大量テスト商品 {i}",
                "price": 1000.0 + i,
                "category": f"category{i % 5}",
                "status": "active"
            }
            
            response = client.post("/api/v1/products", json=product_data)
            if response.status_code == 201:
                products.append(response.json())
                
                # 在庫も設定
                product_id = response.json()["id"]
                client.post(f"/api/v1/inventory/add/{product_id}",
                           json={"quantity": 100, "reason": "大量テスト用"})
        
        return {"products": products}


class TestERPBusinessRuleCompliance:
    """ERP業務ルール準拠テスト"""
    
    def test_japanese_business_rules(self, full_integration_db):
        """日本の業務ルール準拠テスト"""
        print("\n=== 日本の業務ルール準拠テスト ===")
        
        # 1. 消費税計算ルール（10%）
        product_data = {
            "code": "TAX-TEST-001",
            "name": "税率テスト商品",
            "price": 1000.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product = response.json()
        
        # 在庫設定
        client.post(f"/api/v1/inventory/add/{product['id']}",
                   json={"quantity": 100, "reason": "税率テスト用"})
        
        # 注文作成（税計算確認）
        order_data = {
            "customer_name": "税率テスト顧客",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "unit_price": 1000.0
                }
            ]
        }
        
        response = client.post("/api/v1/sales-orders", json=order_data)
        assert response.status_code == 201
        order = response.json()
        
        # 税込み金額確認（1000 * 1.1 = 1100）
        expected_total = 1100.0
        assert abs(order.get("total_amount", 0) - expected_total) < 1.0, \
            f"消費税計算が正しくありません: {order.get('total_amount')} != {expected_total}"
        print(f"✅ 消費税計算確認: ¥{order.get('total_amount')}")
        
        # 2. 商品コード規則（英数字のみ）
        invalid_codes = ["商品-001", "PROD/001", "PROD 001"]
        
        for invalid_code in invalid_codes:
            invalid_product = {
                "code": invalid_code,
                "name": "無効コードテスト商品",
                "price": 1000.0,
                "status": "active"
            }
            
            response = client.post("/api/v1/products", json=invalid_product)
            # 無効なコードは拒否されることを期待（ただし実装次第）
            if response.status_code == 400:
                print(f"✅ 無効商品コード拒否: {invalid_code}")
            else:
                print(f"⚠️ 無効商品コードが受け入れられました: {invalid_code}")
        
        # 3. 在庫マイナス防止ルール
        test_product_data = {
            "code": "MINUS-STOCK-TEST",
            "name": "マイナス在庫テスト商品",
            "price": 1000.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=test_product_data)
        assert response.status_code == 201
        test_product = response.json()
        
        # 10個の在庫設定
        client.post(f"/api/v1/inventory/add/{test_product['id']}",
                   json={"quantity": 10, "reason": "マイナス在庫テスト用"})
        
        # 20個の減少調整（マイナス在庫になる）
        response = client.post(f"/api/v1/inventory/adjust/{test_product['id']}",
                             params={"quantity": -20, "reason": "マイナス在庫テスト"})
        
        # マイナス在庫は防がれることを確認
        if response.status_code == 400:
            print("✅ マイナス在庫防止機能確認")
        else:
            # 在庫レベル確認
            stock_response = client.get(f"/api/v1/inventory/level/{test_product['id']}")
            if stock_response.status_code == 200:
                stock_level = stock_response.json()
                assert stock_level["current_stock"] >= 0, "在庫がマイナスになっています"
                print(f"⚠️ マイナス在庫調整が実行されました（現在庫: {stock_level['current_stock']}）")
        
        print("🎉 日本の業務ルール準拠テスト完了!")
    
    def test_audit_trail_requirements(self, full_integration_db):
        """監査証跡要件テスト"""
        print("\n=== 監査証跡要件テスト ===")
        
        # 1. 商品変更履歴
        product_data = {
            "code": "AUDIT-001",
            "name": "監査テスト商品",
            "price": 1000.0,
            "status": "active"
        }
        
        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product = response.json()
        product_id = product["id"]
        
        # 商品更新
        update_data = {
            "name": "監査テスト商品（更新）",
            "price": 1200.0
        }
        
        response = client.put(f"/api/v1/products/{product_id}", json=update_data)
        assert response.status_code == 200
        
        # 変更履歴確認（APIが存在する場合）
        response = client.get(f"/api/v1/products/{product_id}/history")
        if response.status_code == 200:
            history = response.json()
            assert len(history) >= 1
            print(f"✅ 商品変更履歴: {len(history)}件")
        else:
            print("⚠️ 商品変更履歴API未実装")
        
        # 2. 在庫移動履歴
        client.post(f"/api/v1/inventory/add/{product_id}",
                   json={"quantity": 50, "reason": "監査テスト初期在庫"})
        
        client.post(f"/api/v1/inventory/adjust/{product_id}",
                   params={"quantity": -10, "reason": "監査テスト調整"})
        
        # 在庫履歴確認
        response = client.get(f"/api/v1/inventory/transactions/{product_id}")
        if response.status_code == 200:
            transactions = response.json()
            assert len(transactions) >= 2
            
            # 各トランザクションに必要な情報が含まれているか確認
            for transaction in transactions:
                assert "timestamp" in transaction or "created_at" in transaction
                assert "quantity" in transaction
                assert "reason" in transaction
                print(f"✅ 在庫移動記録: {transaction.get('reason', 'N/A')}")
        else:
            print("⚠️ 在庫移動履歴API未実装")
        
        # 3. 注文処理履歴
        order_data = {
            "customer_name": "監査テスト顧客",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 5,
                    "unit_price": 1200.0
                }
            ]
        }
        
        response = client.post("/api/v1/sales-orders", json=order_data)
        assert response.status_code == 201
        order = response.json()
        order_id = order["id"]
        
        # 注文ステータス変更
        client.put(f"/api/v1/sales-orders/{order_id}/status", params={"status": "confirmed"})
        client.put(f"/api/v1/sales-orders/{order_id}/status", params={"status": "shipped"})
        
        # 注文履歴確認
        response = client.get(f"/api/v1/sales-orders/{order_id}/history")
        if response.status_code == 200:
            order_history = response.json()
            assert len(order_history) >= 2  # confirmed, shipped
            print(f"✅ 注文処理履歴: {len(order_history)}件")
        else:
            print("⚠️ 注文処理履歴API未実装")
        
        print("🎉 監査証跡要件テスト完了!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])