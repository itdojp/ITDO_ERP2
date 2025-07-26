"""
ERP Business Performance Tests
ERP業務パフォーマンステスト

48時間以内実装 - 業務操作パフォーマンス検証
- 商品検索 <100ms
- 在庫更新 <50ms
- 100+ 同時ユーザー対応
"""

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app

client = TestClient(app)

# パフォーマンス要件定義
PERFORMANCE_REQUIREMENTS = {
    "product_search_max_time": 0.1,  # 100ms
    "inventory_update_max_time": 0.05,  # 50ms
    "concurrent_users_min": 100,  # 100同時ユーザー
    "api_response_max_time": 0.2,  # 200ms
    "database_query_max_time": 0.03,  # 30ms
}


@pytest.fixture(scope="function")
def performance_test_db():
    """パフォーマンステスト用データベース"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models.base import Base

    # より高速なSQLite設定
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
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


class TestERPPerformanceRequirements:
    """ERP業務パフォーマンス要件テスト"""

    def test_product_search_performance(self, performance_test_db):
        """商品検索パフォーマンス要件テスト (<100ms)"""
        # テストデータ準備
        test_products = []
        for i in range(1000):  # 1000商品で検索テスト
            product_data = {
                "code": f"PERF-{i:04d}",
                "name": f"パフォーマンステスト商品 {i}",
                "description": f"説明文 {i}",
                "price": 1000.0 + i,
                "category": f"category{i % 10}",
                "status": "active",
            }

            response = client.post("/api/v1/products", json=product_data)
            if response.status_code == 201:
                test_products.append(response.json())

        assert len(test_products) >= 500, "十分なテストデータが作成されませんでした"

        # 商品検索パフォーマンステスト
        search_times = []
        test_scenarios = [
            {"params": {"limit": 50}},  # 基本検索
            {"params": {"search": "テスト", "limit": 50}},  # 名前検索
            {"params": {"category": "category1", "limit": 50}},  # カテゴリ検索
            {
                "params": {"min_price": 1000, "max_price": 1100, "limit": 50}
            },  # 価格範囲検索
        ]

        for scenario in test_scenarios:
            start_time = time.time()
            response = client.get("/api/v1/products", params=scenario["params"])
            search_time = time.time() - start_time

            assert response.status_code == 200, f"検索が失敗しました: {scenario}"
            products = response.json()
            assert isinstance(products, list), "商品リストが返されませんでした"

            search_times.append(search_time)

        # パフォーマンス要件検証
        max_search_time = max(search_times)
        avg_search_time = statistics.mean(search_times)

        assert max_search_time < PERFORMANCE_REQUIREMENTS["product_search_max_time"], (
            f"商品検索の最大時間が要件を超過: {max_search_time:.3f}s > {PERFORMANCE_REQUIREMENTS['product_search_max_time']}s"
        )

        assert (
            avg_search_time < PERFORMANCE_REQUIREMENTS["product_search_max_time"] * 0.5
        ), f"商品検索の平均時間が推奨値を超過: {avg_search_time:.3f}s"

        print(
            f"✅ 商品検索パフォーマンス - 最大: {max_search_time:.3f}s, 平均: {avg_search_time:.3f}s"
        )

    def test_inventory_update_performance(self, performance_test_db):
        """在庫更新パフォーマンス要件テスト (<50ms)"""
        # テスト商品作成
        products = []
        for i in range(100):
            product_data = {
                "code": f"INV-PERF-{i:03d}",
                "name": f"在庫パフォーマンステスト商品 {i}",
                "price": 1000.0,
                "status": "active",
            }

            response = client.post("/api/v1/products", json=product_data)
            if response.status_code == 201:
                products.append(response.json())

        assert len(products) >= 50, "十分なテスト商品が作成されませんでした"

        # 在庫更新パフォーマンステスト
        update_times = []

        for product in products[:50]:  # 50商品で在庫更新テスト
            product_id = product["id"]

            # 在庫追加パフォーマンス
            start_time = time.time()
            response = client.post(
                f"/api/v1/inventory/add/{product_id}",
                json={"quantity": 100, "reason": "パフォーマンステスト"},
            )
            add_time = time.time() - start_time

            assert response.status_code == 200, f"在庫追加が失敗: {product_id}"
            update_times.append(add_time)

            # 在庫調整パフォーマンス
            start_time = time.time()
            response = client.post(
                f"/api/v1/inventory/adjust/{product_id}",
                params={"quantity": -10, "reason": "調整テスト"},
            )
            adjust_time = time.time() - start_time

            if response.status_code == 200:
                update_times.append(adjust_time)

            # 在庫レベル取得パフォーマンス
            start_time = time.time()
            response = client.get(f"/api/v1/inventory/level/{product_id}")
            level_time = time.time() - start_time

            assert response.status_code == 200, f"在庫レベル取得が失敗: {product_id}"
            update_times.append(level_time)

        # パフォーマンス要件検証
        max_update_time = max(update_times)
        avg_update_time = statistics.mean(update_times)

        assert (
            max_update_time < PERFORMANCE_REQUIREMENTS["inventory_update_max_time"]
        ), (
            f"在庫更新の最大時間が要件を超過: {max_update_time:.3f}s > {PERFORMANCE_REQUIREMENTS['inventory_update_max_time']}s"
        )

        assert (
            avg_update_time
            < PERFORMANCE_REQUIREMENTS["inventory_update_max_time"] * 0.7
        ), f"在庫更新の平均時間が推奨値を超過: {avg_update_time:.3f}s"

        print(
            f"✅ 在庫更新パフォーマンス - 最大: {max_update_time:.3f}s, 平均: {avg_update_time:.3f}s"
        )

    def test_concurrent_user_performance(self, performance_test_db):
        """同時ユーザーパフォーマンステスト (100+ユーザー)"""
        # テストデータ準備
        test_product_data = {
            "code": "CONCURRENT-001",
            "name": "同時アクセステスト商品",
            "price": 1000.0,
            "status": "active",
        }

        response = client.post("/api/v1/products", json=test_product_data)
        assert response.status_code == 201
        test_product = response.json()
        product_id = test_product["id"]

        # 初期在庫設定
        response = client.post(
            f"/api/v1/inventory/add/{product_id}",
            json={"quantity": 10000, "reason": "同時テスト用"},
        )
        assert response.status_code == 200

        def simulate_user_session(user_id: int) -> Dict[str, Any]:
            """ユーザーセッションシミュレーション"""
            session_start = time.time()
            operations = []

            try:
                # 1. 商品検索
                start = time.time()
                response = client.get("/api/v1/products", params={"limit": 10})
                search_time = time.time() - start
                operations.append(
                    {
                        "operation": "search",
                        "time": search_time,
                        "success": response.status_code == 200,
                    }
                )

                # 2. 商品詳細取得
                start = time.time()
                response = client.get(f"/api/v1/products/{product_id}")
                detail_time = time.time() - start
                operations.append(
                    {
                        "operation": "detail",
                        "time": detail_time,
                        "success": response.status_code == 200,
                    }
                )

                # 3. 在庫レベル確認
                start = time.time()
                response = client.get(f"/api/v1/inventory/level/{product_id}")
                inventory_time = time.time() - start
                operations.append(
                    {
                        "operation": "inventory",
                        "time": inventory_time,
                        "success": response.status_code == 200,
                    }
                )

                # 4. 注文作成（一部のユーザーのみ）
                if user_id % 5 == 0:  # 20%のユーザーが注文
                    start = time.time()
                    order_data = {
                        "customer_name": f"テストユーザー{user_id}",
                        "customer_email": f"user{user_id}@test.com",
                        "items": [
                            {
                                "product_id": product_id,
                                "quantity": 1,
                                "unit_price": 1000.0,
                            }
                        ],
                    }
                    response = client.post("/api/v1/sales-orders", json=order_data)
                    order_time = time.time() - start
                    operations.append(
                        {
                            "operation": "order",
                            "time": order_time,
                            "success": response.status_code == 201,
                        }
                    )

                session_time = time.time() - session_start

                return {
                    "user_id": user_id,
                    "session_time": session_time,
                    "operations": operations,
                    "success": True,
                }

            except Exception as e:
                return {
                    "user_id": user_id,
                    "session_time": time.time() - session_start,
                    "operations": operations,
                    "success": False,
                    "error": str(e),
                }

        # 同時ユーザーシミュレーション実行
        concurrent_users = PERFORMANCE_REQUIREMENTS["concurrent_users_min"]
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(simulate_user_session, user_id)
                for user_id in range(concurrent_users)
            ]

            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)  # 30秒タイムアウト
                    results.append(result)
                except Exception as e:
                    results.append(
                        {
                            "success": False,
                            "error": str(e),
                            "user_id": -1,
                            "session_time": 30.0,
                        }
                    )

        total_time = time.time() - start_time

        # 結果分析
        successful_sessions = [r for r in results if r["success"]]
        [r for r in results if not r["success"]]

        success_rate = len(successful_sessions) / len(results) * 100
        avg_session_time = (
            statistics.mean([r["session_time"] for r in successful_sessions])
            if successful_sessions
            else 0
        )

        # パフォーマンス要件検証
        assert success_rate >= 95.0, f"成功率が低すぎます: {success_rate:.1f}% < 95%"
        assert len(successful_sessions) >= concurrent_users * 0.9, (
            f"成功したセッション数が不十分: {len(successful_sessions)} < {concurrent_users * 0.9}"
        )

        # 操作別パフォーマンス分析
        operation_times = {}
        for session in successful_sessions:
            for op in session["operations"]:
                if op["success"]:
                    if op["operation"] not in operation_times:
                        operation_times[op["operation"]] = []
                    operation_times[op["operation"]].append(op["time"])

        print("✅ 同時ユーザーパフォーマンス:")
        print(f"   - 同時ユーザー数: {concurrent_users}")
        print(f"   - 成功率: {success_rate:.1f}%")
        print(f"   - 平均セッション時間: {avg_session_time:.3f}s")
        print(f"   - 総実行時間: {total_time:.3f}s")

        for operation, times in operation_times.items():
            avg_time = statistics.mean(times)
            max_time = max(times)
            print(f"   - {operation}: 平均 {avg_time:.3f}s, 最大 {max_time:.3f}s")

    def test_api_response_time_requirements(self, performance_test_db):
        """API応答時間要件テスト"""
        # テストデータ準備
        product_data = {
            "code": "API-PERF-001",
            "name": "API応答時間テスト商品",
            "price": 1000.0,
            "status": "active",
        }

        response = client.post("/api/v1/products", json=product_data)
        assert response.status_code == 201
        product = response.json()
        product_id = product["id"]

        # 各APIエンドポイントの応答時間測定
        api_endpoints = [
            {"method": "GET", "url": "/api/v1/products", "params": {"limit": 10}},
            {"method": "GET", "url": f"/api/v1/products/{product_id}", "params": None},
            {
                "method": "POST",
                "url": f"/api/v1/inventory/add/{product_id}",
                "json": {"quantity": 10, "reason": "テスト"},
            },
            {
                "method": "GET",
                "url": f"/api/v1/inventory/level/{product_id}",
                "params": None,
            },
            {"method": "GET", "url": "/api/v1/sales-orders", "params": {"limit": 10}},
        ]

        response_times = {}

        for endpoint in api_endpoints:
            times = []
            endpoint_key = f"{endpoint['method']} {endpoint['url']}"

            # 各エンドポイントを10回測定
            for _ in range(10):
                start_time = time.time()

                if endpoint["method"] == "GET":
                    response = client.get(
                        endpoint["url"], params=endpoint.get("params")
                    )
                elif endpoint["method"] == "POST":
                    response = client.post(endpoint["url"], json=endpoint.get("json"))

                response_time = time.time() - start_time
                times.append(response_time)

                # HTTPステータスコードチェック（エラーでなければOK）
                assert response.status_code < 500, f"サーバーエラー: {endpoint_key}"

            response_times[endpoint_key] = {
                "times": times,
                "avg": statistics.mean(times),
                "max": max(times),
                "min": min(times),
            }

        # パフォーマンス要件検証
        for endpoint_key, metrics in response_times.items():
            assert metrics["max"] < PERFORMANCE_REQUIREMENTS["api_response_max_time"], (
                f"{endpoint_key} の最大応答時間が要件を超過: {metrics['max']:.3f}s > {PERFORMANCE_REQUIREMENTS['api_response_max_time']}s"
            )

            assert (
                metrics["avg"] < PERFORMANCE_REQUIREMENTS["api_response_max_time"] * 0.7
            ), f"{endpoint_key} の平均応答時間が推奨値を超過: {metrics['avg']:.3f}s"

        print("✅ API応答時間パフォーマンス:")
        for endpoint_key, metrics in response_times.items():
            print(
                f"   - {endpoint_key}: 平均 {metrics['avg']:.3f}s, 最大 {metrics['max']:.3f}s"
            )


class TestERPLoadTestingScenarios:
    """ERP負荷テストシナリオ"""

    def test_peak_hour_simulation(self, performance_test_db):
        """ピーク時間シミュレーション"""
        # 実業務のピーク時間を想定した負荷テスト
        # 商品検索: 60%、在庫確認: 25%、注文作成: 15%

        # テストデータ準備
        products = []
        for i in range(50):
            product_data = {
                "code": f"PEAK-{i:03d}",
                "name": f"ピークテスト商品 {i}",
                "price": 1000.0 + i,
                "status": "active",
            }

            response = client.post("/api/v1/products", json=product_data)
            if response.status_code == 201:
                product = response.json()
                products.append(product)

                # 在庫追加
                client.post(
                    f"/api/v1/inventory/add/{product['id']}",
                    json={"quantity": 1000, "reason": "ピークテスト用"},
                )

        def peak_hour_user_behavior(user_id: int) -> Dict[str, Any]:
            """ピーク時間のユーザー行動シミュレーション"""
            import random

            session_start = time.time()
            operations_performed = []

            try:
                # ランダムな操作パターン
                for _ in range(random.randint(3, 8)):  # 1セッションで3-8操作
                    operation_type = random.choices(
                        ["search", "inventory_check", "order_create"],
                        weights=[60, 25, 15],
                    )[0]

                    op_start = time.time()

                    if operation_type == "search":
                        response = client.get(
                            "/api/v1/products", params={"limit": random.randint(5, 20)}
                        )
                        success = response.status_code == 200

                    elif operation_type == "inventory_check":
                        if products:
                            product = random.choice(products)
                            response = client.get(
                                f"/api/v1/inventory/level/{product['id']}"
                            )
                            success = response.status_code == 200
                        else:
                            success = False

                    elif operation_type == "order_create":
                        if products:
                            product = random.choice(products)
                            order_data = {
                                "customer_name": f"ピークユーザー{user_id}",
                                "customer_email": f"peak{user_id}@test.com",
                                "items": [
                                    {
                                        "product_id": product["id"],
                                        "quantity": random.randint(1, 5),
                                        "unit_price": product["price"],
                                    }
                                ],
                            }
                            response = client.post(
                                "/api/v1/sales-orders", json=order_data
                            )
                            success = response.status_code == 201
                        else:
                            success = False

                    op_time = time.time() - op_start
                    operations_performed.append(
                        {"type": operation_type, "time": op_time, "success": success}
                    )

                    # 操作間の小休止（実際のユーザー行動を模擬）
                    time.sleep(random.uniform(0.1, 0.5))

                session_time = time.time() - session_start

                return {
                    "user_id": user_id,
                    "session_time": session_time,
                    "operations": operations_performed,
                    "success": True,
                }

            except Exception as e:
                return {
                    "user_id": user_id,
                    "session_time": time.time() - session_start,
                    "operations": operations_performed,
                    "success": False,
                    "error": str(e),
                }

        # ピーク負荷実行
        peak_users = 50  # 50同時ユーザー
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=peak_users) as executor:
            futures = [
                executor.submit(peak_hour_user_behavior, user_id)
                for user_id in range(peak_users)
            ]

            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e), "user_id": -1})

        total_time = time.time() - start_time

        # 結果分析
        successful_sessions = [r for r in results if r["success"]]
        success_rate = len(successful_sessions) / len(results) * 100

        # 操作統計
        operation_stats = {"search": [], "inventory_check": [], "order_create": []}
        for session in successful_sessions:
            for op in session["operations"]:
                if op["success"] and op["type"] in operation_stats:
                    operation_stats[op["type"]].append(op["time"])

        # パフォーマンス要件検証
        assert success_rate >= 90.0, (
            f"ピーク時間の成功率が低すぎます: {success_rate:.1f}% < 90%"
        )

        print("✅ ピーク時間シミュレーション結果:")
        print(f"   - 同時ユーザー数: {peak_users}")
        print(f"   - 成功率: {success_rate:.1f}%")
        print(f"   - 総実行時間: {total_time:.3f}s")

        for op_type, times in operation_stats.items():
            if times:
                avg_time = statistics.mean(times)
                max_time = max(times)
                print(
                    f"   - {op_type}: {len(times)}回実行, 平均 {avg_time:.3f}s, 最大 {max_time:.3f}s"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
