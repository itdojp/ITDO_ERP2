"""
ERP Load Testing Suite
ERP負荷テストスイート

48時間以内実装 - 大規模負荷テスト
- 長時間負荷テスト
- メモリリークテスト
- データベース負荷テスト
- システム限界テスト
"""
import pytest
import time
import threading
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from typing import List, Dict, Any
import statistics
import json
from datetime import datetime, timedelta

from app.main import app
from app.core.database import get_db


client = TestClient(app)

# 負荷テスト設定
LOAD_TEST_CONFIG = {
    "long_duration_minutes": 5,        # 長時間テスト（本番では60分）
    "max_concurrent_users": 200,       # 最大同時ユーザー
    "ramp_up_seconds": 30,            # ランプアップ時間
    "sustained_load_minutes": 2,       # 持続負荷時間
    "memory_leak_threshold_mb": 100,   # メモリリーク閾値
    "database_connection_limit": 50,   # DB接続上限
}


@pytest.fixture(scope="function")
def load_test_db():
    """負荷テスト用データベース"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base
    
    # より高性能な設定
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        connect_args={
            "check_same_thread": False,
            "timeout": 60,
            "cached_statements": 100
        }
    )
    
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine
    )
    
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


class SystemResourceMonitor:
    """システムリソース監視"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "memory_rss_mb": [],
            "active_threads": [],
            "timestamps": []
        }
        self.monitor_thread = None
        self.process = psutil.Process()
    
    def start_monitoring(self):
        """監視開始"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """監視停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """監視ループ"""
        while self.monitoring:
            try:
                # CPU使用率
                cpu_percent = self.process.cpu_percent()
                
                # メモリ使用量
                memory_info = self.process.memory_info()
                memory_percent = self.process.memory_percent()
                memory_rss_mb = memory_info.rss / 1024 / 1024
                
                # スレッド数
                thread_count = self.process.num_threads()
                
                self.metrics["cpu_usage"].append(cpu_percent)
                self.metrics["memory_usage"].append(memory_percent)
                self.metrics["memory_rss_mb"].append(memory_rss_mb)
                self.metrics["active_threads"].append(thread_count)
                self.metrics["timestamps"].append(time.time())
                
            except Exception:
                pass  # 監視エラーは無視
            
            time.sleep(1.0)  # 1秒間隔
    
    def get_peak_metrics(self) -> Dict[str, float]:
        """ピーク値取得"""
        if not self.metrics["timestamps"]:
            return {}
        
        return {
            "peak_cpu_percent": max(self.metrics["cpu_usage"], default=0),
            "peak_memory_percent": max(self.metrics["memory_usage"], default=0),
            "peak_memory_rss_mb": max(self.metrics["memory_rss_mb"], default=0),
            "peak_threads": max(self.metrics["active_threads"], default=0),
            "avg_cpu_percent": statistics.mean(self.metrics["cpu_usage"]) if self.metrics["cpu_usage"] else 0,
            "avg_memory_rss_mb": statistics.mean(self.metrics["memory_rss_mb"]) if self.metrics["memory_rss_mb"] else 0,
            "monitoring_duration": self.metrics["timestamps"][-1] - self.metrics["timestamps"][0] if len(self.metrics["timestamps"]) > 1 else 0
        }
    
    def detect_memory_leak(self) -> Dict[str, Any]:
        """メモリリーク検出"""
        if len(self.metrics["memory_rss_mb"]) < 10:
            return {"detected": False, "reason": "データ不足"}
        
        # 最初と最後の10%のデータで比較
        start_samples = int(len(self.metrics["memory_rss_mb"]) * 0.1)
        end_samples = int(len(self.metrics["memory_rss_mb"]) * 0.1)
        
        start_avg = statistics.mean(self.metrics["memory_rss_mb"][:start_samples])
        end_avg = statistics.mean(self.metrics["memory_rss_mb"][-end_samples:])
        
        memory_increase_mb = end_avg - start_avg
        increase_percent = (memory_increase_mb / start_avg) * 100 if start_avg > 0 else 0
        
        is_leak = (
            memory_increase_mb > LOAD_TEST_CONFIG["memory_leak_threshold_mb"] and
            increase_percent > 20  # 20%以上の増加
        )
        
        return {
            "detected": is_leak,
            "memory_increase_mb": memory_increase_mb,
            "increase_percent": increase_percent,
            "start_memory_mb": start_avg,
            "end_memory_mb": end_avg
        }


class TestERPLongDurationLoad:
    """ERP長時間負荷テスト"""
    
    def test_sustained_load_performance(self, load_test_db):
        """持続負荷パフォーマンステスト"""
        print(f"\n=== {LOAD_TEST_CONFIG['sustained_load_minutes']}分間持続負荷テスト ===")
        
        # テストデータ準備
        test_products = self._prepare_load_test_data()
        
        # システムリソース監視開始
        resource_monitor = SystemResourceMonitor()
        resource_monitor.start_monitoring()
        
        # 持続負荷実行
        duration_seconds = LOAD_TEST_CONFIG['sustained_load_minutes'] * 60
        concurrent_users = 50  # 持続可能なユーザー数
        
        def sustained_user_simulation(user_id: int) -> Dict[str, Any]:
            """持続負荷ユーザーシミュレーション"""
            end_time = time.time() + duration_seconds
            operations = 0
            errors = 0
            response_times = []
            
            while time.time() < end_time:
                # 多様な操作パターン
                operation_weights = [0.5, 0.2, 0.2, 0.1]  # 検索, 詳細, 在庫, 注文
                operation_type = ["search", "detail", "inventory", "order"][
                    self._weighted_choice(operation_weights)
                ]
                
                start_time = time.time()
                try:
                    success = self._execute_operation(operation_type, test_products, user_id)
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    
                    if not success:
                        errors += 1
                    
                    operations += 1
                    
                except Exception:
                    errors += 1
                    response_times.append(0)
                
                # ユーザー行動間隔（リアルなペース）
                time.sleep(0.5 + (user_id % 10) * 0.1)  # 0.5-1.4秒間隔
            
            return {
                "user_id": user_id,
                "operations": operations,
                "errors": errors,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0
            }
        
        print(f"🚀 {concurrent_users}ユーザーでの{duration_seconds}秒間持続負荷開始")
        start_time = time.time()
        
        # 並行実行
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(sustained_user_simulation, user_id)
                for user_id in range(concurrent_users)
            ]
            
            user_results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    user_results.append(result)
                except Exception as e:
                    user_results.append({
                        "user_id": -1,
                        "operations": 0,
                        "errors": 1,
                        "error": str(e)
                    })
        
        # 監視停止
        resource_monitor.stop_monitoring()
        total_duration = time.time() - start_time
        
        # 結果分析
        total_operations = sum(r["operations"] for r in user_results)
        total_errors = sum(r["errors"] for r in user_results)
        error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0
        throughput = total_operations / total_duration
        
        avg_response_times = [r["avg_response_time"] for r in user_results if r["avg_response_time"] > 0]
        overall_avg_response = statistics.mean(avg_response_times) if avg_response_times else 0
        
        # リソース使用量確認
        resource_metrics = resource_monitor.get_peak_metrics()
        memory_leak_analysis = resource_monitor.detect_memory_leak()
        
        # 性能要件検証
        assert error_rate < 2.0, f"エラー率が高すぎます: {error_rate:.2f}% > 2%"
        assert overall_avg_response < 1.0, f"平均応答時間が遅すぎます: {overall_avg_response:.3f}s > 1s"
        assert resource_metrics["peak_memory_rss_mb"] < 500, f"メモリ使用量が多すぎます: {resource_metrics['peak_memory_rss_mb']:.1f}MB"
        assert not memory_leak_analysis["detected"], f"メモリリークが検出されました: +{memory_leak_analysis['memory_increase_mb']:.1f}MB"
        
        print(f"✅ 持続負荷テスト結果:")
        print(f"   実行時間: {total_duration:.1f}秒")
        print(f"   総操作数: {total_operations}")
        print(f"   エラー率: {error_rate:.2f}%")
        print(f"   スループット: {throughput:.1f} ops/sec")
        print(f"   平均応答時間: {overall_avg_response:.3f}秒")
        print(f"   ピークメモリ: {resource_metrics['peak_memory_rss_mb']:.1f}MB")
        print(f"   ピークCPU: {resource_metrics['peak_cpu_percent']:.1f}%")
        print(f"   メモリリーク: {'検出' if memory_leak_analysis['detected'] else '未検出'}")
    
    def test_ramp_up_load_testing(self, load_test_db):
        """ランプアップ負荷テスト"""
        print(f"\n=== ランプアップ負荷テスト ===")
        
        test_products = self._prepare_load_test_data()
        resource_monitor = SystemResourceMonitor()
        resource_monitor.start_monitoring()
        
        max_users = LOAD_TEST_CONFIG["max_concurrent_users"]
        ramp_up_duration = LOAD_TEST_CONFIG["ramp_up_seconds"]
        
        # 段階的にユーザー数を増加
        user_increments = [10, 25, 50, 100, 150, 200]
        phase_results = []
        
        for phase, target_users in enumerate(user_increments):
            if target_users > max_users:
                break
                
            print(f"📈 Phase {phase + 1}: {target_users}ユーザー負荷")
            
            # 各フェーズでの負荷実行
            phase_start = time.time()
            
            def ramp_user_simulation(user_id: int) -> Dict[str, Any]:
                """ランプアップ段階のユーザーシミュレーション"""
                operations = 0
                errors = 0
                
                # 10秒間の負荷
                end_time = time.time() + 10
                while time.time() < end_time:
                    try:
                        success = self._execute_operation("search", test_products, user_id)
                        if not success:
                            errors += 1
                        operations += 1
                        time.sleep(0.1)  # 高頻度操作
                    except Exception:
                        errors += 1
                
                return {
                    "user_id": user_id,
                    "operations": operations,
                    "errors": errors
                }
            
            # 並行実行
            with ThreadPoolExecutor(max_workers=target_users) as executor:
                futures = [
                    executor.submit(ramp_user_simulation, user_id)
                    for user_id in range(target_users)
                ]
                
                results = [f.result() for f in as_completed(futures)]
            
            phase_duration = time.time() - phase_start
            phase_operations = sum(r["operations"] for r in results)
            phase_errors = sum(r["errors"] for r in results)
            phase_error_rate = (phase_errors / phase_operations * 100) if phase_operations > 0 else 0
            phase_throughput = phase_operations / phase_duration
            
            phase_results.append({
                "users": target_users,
                "operations": phase_operations,
                "error_rate": phase_error_rate,
                "throughput": phase_throughput,
                "duration": phase_duration
            })
            
            print(f"   操作数: {phase_operations}, エラー率: {phase_error_rate:.2f}%, スループット: {phase_throughput:.1f} ops/sec")
            
            # 段階間の休憩
            time.sleep(2)
        
        resource_monitor.stop_monitoring()
        resource_metrics = resource_monitor.get_peak_metrics()
        
        # スケーラビリティ分析
        throughput_degradation = self._analyze_scalability(phase_results)
        
        print(f"✅ ランプアップテスト結果:")
        print(f"   最大ユーザー数: {max([p['users'] for p in phase_results])}")
        print(f"   ピーク スループット: {max([p['throughput'] for p in phase_results]):.1f} ops/sec")
        print(f"   スケーラビリティ効率: {throughput_degradation:.1f}% (低い方が良い)")
        print(f"   リソース使用量 - メモリ: {resource_metrics['peak_memory_rss_mb']:.1f}MB, CPU: {resource_metrics['peak_cpu_percent']:.1f}%")
        
        # スケーラビリティ要件確認
        assert throughput_degradation < 50, f"スケーラビリティ低下が大きすぎます: {throughput_degradation:.1f}%"
    
    def _prepare_load_test_data(self) -> List[Dict[str, Any]]:
        """負荷テスト用データ準備"""
        products = []
        
        for i in range(200):  # 200商品
            product_data = {
                "code": f"LOAD-{i:04d}",
                "name": f"負荷テスト商品 {i}",
                "price": 1000.0 + i,
                "category": f"load_category_{i % 20}",
                "status": "active"
            }
            
            try:
                response = client.post("/api/v1/products", json=product_data)
                if response.status_code == 201:
                    product = response.json()
                    products.append(product)
                    
                    # 在庫設定
                    client.post(f"/api/v1/inventory/add/{product['id']}", 
                               json={"quantity": 1000, "reason": "負荷テスト用"})
            except Exception:
                pass
        
        return products
    
    def _execute_operation(self, operation_type: str, test_products: List[Dict], user_id: int) -> bool:
        """操作実行"""
        try:
            if operation_type == "search":
                response = client.get("/api/v1/products", 
                                    params={"limit": 20, "search": f"負荷{user_id % 100}"})
                return response.status_code == 200
                
            elif operation_type == "detail" and test_products:
                product = test_products[user_id % len(test_products)]
                response = client.get(f"/api/v1/products/{product['id']}")
                return response.status_code == 200
                
            elif operation_type == "inventory" and test_products:
                product = test_products[user_id % len(test_products)]
                response = client.get(f"/api/v1/inventory/level/{product['id']}")
                return response.status_code == 200
                
            elif operation_type == "order" and test_products:
                product = test_products[user_id % len(test_products)]
                order_data = {
                    "customer_name": f"負荷テストユーザー{user_id}",
                    "customer_email": f"load{user_id}@test.com",
                    "items": [
                        {
                            "product_id": product["id"],
                            "quantity": 1,
                            "unit_price": product["price"]
                        }
                    ]
                }
                response = client.post("/api/v1/sales-orders", json=order_data)
                return response.status_code == 201
                
        except Exception:
            return False
        
        return False
    
    def _weighted_choice(self, weights: List[float]) -> int:
        """重み付き選択"""
        import random
        r = random.random()
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return i
        return len(weights) - 1
    
    def _analyze_scalability(self, phase_results: List[Dict]) -> float:
        """スケーラビリティ分析"""
        if len(phase_results) < 2:
            return 0
        
        # 最初と最後のフェーズでスループット効率を比較
        first_phase = phase_results[0]
        last_phase = phase_results[-1]
        
        # ユーザーあたりのスループット
        first_throughput_per_user = first_phase["throughput"] / first_phase["users"]
        last_throughput_per_user = last_phase["throughput"] / last_phase["users"]
        
        # 効率低下率（パーセント）
        efficiency_degradation = ((first_throughput_per_user - last_throughput_per_user) / first_throughput_per_user) * 100
        
        return max(0, efficiency_degradation)


class TestERPMemoryLeakDetection:
    """ERPメモリリーク検出テスト"""
    
    def test_memory_leak_detection(self, load_test_db):
        """メモリリーク検出テスト"""
        print("\n=== メモリリーク検出テスト ===")
        
        # ガベージコレクション実行
        gc.collect()
        
        resource_monitor = SystemResourceMonitor()
        resource_monitor.start_monitoring()
        
        # 大量のオブジェクト作成・削除を繰り返す
        for cycle in range(10):  # 10サイクル
            print(f"  サイクル {cycle + 1}/10 実行中...")
            
            # 大量の商品作成
            created_products = []
            for i in range(50):
                product_data = {
                    "code": f"MEMLEAK-{cycle}-{i:03d}",
                    "name": f"メモリテスト商品 {cycle}-{i}",
                    "price": 1000.0,
                    "status": "active"
                }
                
                response = client.post("/api/v1/products", json=product_data)
                if response.status_code == 201:
                    created_products.append(response.json())
            
            # 在庫操作（メモリ使用量増加）
            for product in created_products:
                client.post(f"/api/v1/inventory/add/{product['id']}", 
                           json={"quantity": 100, "reason": f"メモリテスト{cycle}"})
                client.get(f"/api/v1/inventory/level/{product['id']}")
            
            # 商品検索（キャッシュなどでメモリ使用）
            for i in range(20):
                client.get("/api/v1/products", params={"limit": 100})
            
            # 意図的にガベージコレクション実行
            gc.collect()
            
            # サイクル間の待機
            time.sleep(1)
        
        resource_monitor.stop_monitoring()
        
        # メモリリーク分析
        memory_leak_analysis = resource_monitor.detect_memory_leak()
        resource_metrics = resource_monitor.get_peak_metrics()
        
        print(f"✅ メモリリーク検出結果:")
        print(f"   メモリリーク: {'検出' if memory_leak_analysis['detected'] else '未検出'}")
        print(f"   メモリ増加量: {memory_leak_analysis['memory_increase_mb']:.1f}MB")
        print(f"   増加率: {memory_leak_analysis['increase_percent']:.1f}%")
        print(f"   開始時メモリ: {memory_leak_analysis['start_memory_mb']:.1f}MB")
        print(f"   終了時メモリ: {memory_leak_analysis['end_memory_mb']:.1f}MB")
        print(f"   ピークメモリ: {resource_metrics['peak_memory_rss_mb']:.1f}MB")
        
        # メモリリーク要件検証
        assert not memory_leak_analysis["detected"], \
            f"メモリリークが検出されました: +{memory_leak_analysis['memory_increase_mb']:.1f}MB ({memory_leak_analysis['increase_percent']:.1f}%増加)"
        
        assert resource_metrics["peak_memory_rss_mb"] < 1000, \
            f"ピークメモリ使用量が多すぎます: {resource_metrics['peak_memory_rss_mb']:.1f}MB > 1000MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])