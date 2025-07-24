#!/usr/bin/env python3
"""
CC02 v33.0 パフォーマンステストフレームワーク
Performance Testing Framework for API Quality Assurance
"""

import asyncio
import time
import statistics
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import json
import requests
from dataclasses import dataclass, asdict
import threading
import queue
import psutil
import sys


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    endpoint: str
    method: str
    response_times: List[float]
    status_codes: List[int]
    errors: List[str]
    throughput: float  # requests per second
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    success_rate: float
    memory_usage: Dict[str, float]
    cpu_usage: float
    test_duration: float
    timestamp: str


class PerformanceTestFramework:
    """API パフォーマンステスト自動化フレームワーク"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[PerformanceMetrics] = []
        self.session = requests.Session()
        self.default_headers = {"Content-Type": "application/json"}
        
    def single_request_test(self, endpoint: str, method: str = "GET", 
                          data: Optional[Dict] = None, headers: Optional[Dict] = None,
                          timeout: float = 30.0) -> Dict[str, Any]:
        """単一リクエストのパフォーマンステスト"""
        
        full_url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers, **(headers or {})}
        
        # Memory before request
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        try:
            if method.upper() == "GET":
                response = self.session.get(full_url, headers=request_headers, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(full_url, json=data, headers=request_headers, timeout=timeout)
            elif method.upper() == "PUT":
                response = self.session.put(full_url, json=data, headers=request_headers, timeout=timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(full_url, headers=request_headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            end_time = time.time()
            
            # Memory after request
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                "success": True,
                "response_time": end_time - start_time,
                "status_code": response.status_code,
                "response_size": len(response.content),
                "memory_used": memory_after - memory_before,
                "error": None
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "response_time": end_time - start_time,
                "status_code": 0,
                "response_size": 0,
                "memory_used": 0,
                "error": str(e)
            }
    
    def load_test(self, endpoint: str, method: str = "GET", 
                  concurrent_users: int = 10, duration_seconds: int = 60,
                  data: Optional[Dict] = None, headers: Optional[Dict] = None) -> PerformanceMetrics:
        """負荷テスト実行"""
        
        print(f"🚀 Starting load test: {method} {endpoint}")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Duration: {duration_seconds}s")
        
        results_queue = queue.Queue()
        
        def worker():
            """ワーカー関数 - 継続的にリクエストを送信"""
            end_time = time.time() + duration_seconds
            
            while time.time() < end_time:
                result = self.single_request_test(endpoint, method, data, headers)
                results_queue.put(result)
                
                # Small delay to prevent overwhelming
                time.sleep(0.01)
        
        # Monitor system resources
        cpu_percentages = []
        memory_stats = []
        
        def monitor_resources():
            """システムリソースモニタリング"""
            end_time = time.time() + duration_seconds
            
            while time.time() < end_time:
                cpu_percentages.append(psutil.cpu_percent(interval=1))
                memory_stats.append(psutil.virtual_memory().percent)
        
        # Start resource monitoring
        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.start()
        
        # Start worker threads
        start_time = time.time()
        threads = []
        
        for _ in range(concurrent_users):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        monitor_thread.join()
        actual_duration = time.time() - start_time
        
        # Collect results
        response_times = []
        status_codes = []
        errors = []
        
        while not results_queue.empty():
            result = results_queue.get()
            response_times.append(result["response_time"])
            status_codes.append(result["status_code"])
            
            if result["error"]:
                errors.append(result["error"])
        
        # Calculate metrics
        total_requests = len(response_times)
        successful_requests = len([sc for sc in status_codes if 200 <= sc < 400])
        
        metrics = PerformanceMetrics(
            endpoint=endpoint,
            method=method,
            response_times=response_times,
            status_codes=status_codes,
            errors=errors,
            throughput=total_requests / actual_duration,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            median_response_time=statistics.median(response_times) if response_times else 0,
            p95_response_time=self._percentile(response_times, 95) if response_times else 0,
            p99_response_time=self._percentile(response_times, 99) if response_times else 0,
            success_rate=(successful_requests / total_requests * 100) if total_requests > 0 else 0,
            memory_usage={
                "avg_memory_percent": statistics.mean(memory_stats) if memory_stats else 0,
                "max_memory_percent": max(memory_stats) if memory_stats else 0
            },
            cpu_usage=statistics.mean(cpu_percentages) if cpu_percentages else 0,
            test_duration=actual_duration,
            timestamp=datetime.now().isoformat()
        )
        
        self.results.append(metrics)
        return metrics
    
    def stress_test(self, endpoint: str, method: str = "GET",
                   start_users: int = 1, max_users: int = 100, step: int = 10,
                   step_duration: int = 30, data: Optional[Dict] = None) -> List[PerformanceMetrics]:
        """ストレステスト - 徐々にユーザー数を増加"""
        
        print(f"🔥 Starting stress test: {method} {endpoint}")
        print(f"   Users: {start_users} -> {max_users} (step: {step})")
        
        stress_results = []
        
        for users in range(start_users, max_users + 1, step):
            print(f"   Testing with {users} concurrent users...")
            
            metrics = self.load_test(
                endpoint=endpoint,
                method=method,
                concurrent_users=users,
                duration_seconds=step_duration,
                data=data
            )
            
            stress_results.append(metrics)
            
            # Check if system is under too much stress
            if metrics.success_rate < 50:  # Less than 50% success rate
                print(f"⚠️  High failure rate detected at {users} users. Stopping stress test.")
                break
            
            # Brief pause between steps
            time.sleep(2)
        
        return stress_results
    
    def spike_test(self, endpoint: str, method: str = "GET",
                   normal_users: int = 10, spike_users: int = 100,
                   normal_duration: int = 30, spike_duration: int = 10,
                   data: Optional[Dict] = None) -> Dict[str, PerformanceMetrics]:
        """スパイクテスト - 突然の負荷増加をテスト"""
        
        print(f"⚡ Starting spike test: {method} {endpoint}")
        print(f"   Normal load: {normal_users} users for {normal_duration}s")
        print(f"   Spike load: {spike_users} users for {spike_duration}s")
        
        # Normal load
        print("   Phase 1: Normal load...")
        normal_metrics = self.load_test(
            endpoint=endpoint,
            method=method,
            concurrent_users=normal_users,
            duration_seconds=normal_duration,
            data=data
        )
        
        # Brief pause
        time.sleep(2)
        
        # Spike load
        print("   Phase 2: Spike load...")
        spike_metrics = self.load_test(
            endpoint=endpoint,
            method=method,
            concurrent_users=spike_users,
            duration_seconds=spike_duration,
            data=data
        )
        
        return {
            "normal": normal_metrics,
            "spike": spike_metrics
        }
    
    def endurance_test(self, endpoint: str, method: str = "GET",
                      concurrent_users: int = 10, duration_hours: float = 1,
                      data: Optional[Dict] = None) -> PerformanceMetrics:
        """耐久テスト - 長時間の安定性テスト"""
        
        duration_seconds = int(duration_hours * 3600)
        
        print(f"⏱️  Starting endurance test: {method} {endpoint}")
        print(f"   Duration: {duration_hours} hours ({duration_seconds}s)")
        print(f"   Concurrent users: {concurrent_users}")
        
        return self.load_test(
            endpoint=endpoint,
            method=method,
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            data=data
        )
    
    def api_discovery_performance_test(self) -> List[PerformanceMetrics]:
        """APIエンドポイントを自動発見してパフォーマンステスト実行"""
        
        # Common API endpoints to test
        test_endpoints = [
            {"endpoint": "/health", "method": "GET"},
            {"endpoint": "/api/v1/users", "method": "GET"},
            {"endpoint": "/api/v1/organizations", "method": "GET"},
            {"endpoint": "/api/v1/products", "method": "GET"},
            {"endpoint": "/api/v1/orders", "method": "GET"},
            {"endpoint": "/docs", "method": "GET"},  # OpenAPI docs
        ]
        
        results = []
        
        for test_config in test_endpoints:
            try:
                print(f"Testing {test_config['method']} {test_config['endpoint']}")
                
                # Quick load test for each endpoint
                metrics = self.load_test(
                    endpoint=test_config["endpoint"],
                    method=test_config["method"],
                    concurrent_users=5,
                    duration_seconds=10
                )
                
                results.append(metrics)
                
            except Exception as e:
                print(f"⚠️  Failed to test {test_config['endpoint']}: {e}")
        
        return results
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """パーセンタイル計算"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def generate_performance_report(self, output_file: Path):
        """パフォーマンステストレポートを生成"""
        
        if not self.results:
            print("No performance test results to report")
            return
        
        report = {
            "summary": {
                "total_tests": len(self.results),
                "test_timestamp": datetime.now().isoformat(),
                "overall_metrics": self._calculate_overall_metrics()
            },
            "detailed_results": [asdict(result) for result in self.results],
            "performance_analysis": self._analyze_performance(),
            "recommendations": self._generate_recommendations()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Performance report saved: {output_file}")
        return report
    
    def _calculate_overall_metrics(self) -> Dict[str, Any]:
        """全体的なメトリクスを計算"""
        
        all_response_times = []
        all_throughputs = []
        all_success_rates = []
        
        for result in self.results:
            all_response_times.extend(result.response_times)
            all_throughputs.append(result.throughput)
            all_success_rates.append(result.success_rate)
        
        return {
            "avg_response_time": statistics.mean(all_response_times) if all_response_times else 0,
            "avg_throughput": statistics.mean(all_throughputs) if all_throughputs else 0,
            "avg_success_rate": statistics.mean(all_success_rates) if all_success_rates else 0,
            "total_requests": len(all_response_times)
        }
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """パフォーマンス分析"""
        
        analysis = {
            "slow_endpoints": [],
            "high_error_endpoints": [],
            "performance_trends": {},
            "bottlenecks": []
        }
        
        for result in self.results:
            # Identify slow endpoints (> 1 second average)
            if result.avg_response_time > 1.0:
                analysis["slow_endpoints"].append({
                    "endpoint": result.endpoint,
                    "avg_response_time": result.avg_response_time,
                    "p95_response_time": result.p95_response_time
                })
            
            # Identify high error rate endpoints (< 95% success)
            if result.success_rate < 95:
                analysis["high_error_endpoints"].append({
                    "endpoint": result.endpoint,
                    "success_rate": result.success_rate,
                    "errors": result.errors[:5]  # First 5 errors
                })
        
        return analysis
    
    def _generate_recommendations(self) -> List[str]:
        """改善推奨事項を生成"""
        
        recommendations = []
        
        # Check average response time
        avg_response_times = [r.avg_response_time for r in self.results]
        if avg_response_times and statistics.mean(avg_response_times) > 0.5:
            recommendations.append("Response times are high - consider caching, database optimization, or CDN")
        
        # Check success rates
        success_rates = [r.success_rate for r in self.results]
        if success_rates and statistics.mean(success_rates) < 95:
            recommendations.append("Success rates are low - investigate error handling and system stability")
        
        # Check memory usage
        memory_usages = [r.memory_usage.get("max_memory_percent", 0) for r in self.results]
        if memory_usages and max(memory_usages) > 80:
            recommendations.append("High memory usage detected - consider memory optimization and garbage collection")
        
        # General recommendations
        recommendations.extend([
            "Implement API rate limiting to prevent abuse",
            "Add performance monitoring and alerting",
            "Consider load balancing for high-traffic endpoints",
            "Optimize database queries and add proper indexing",
            "Implement response compression for large payloads"
        ])
        
        return recommendations


def main():
    """メイン実行関数"""
    
    print("⚡ CC02 v33.0 Performance Test Framework")
    print("=" * 50)
    
    # Check if backend is running
    framework = PerformanceTestFramework()
    
    try:
        health_check = framework.single_request_test("/health")
        if not health_check["success"]:
            print("⚠️  Backend server not responding. Please start the backend first:")
            print("   cd backend && uv run uvicorn app.main:app --reload")
            return
    except:
        print("⚠️  Cannot connect to backend. Please start the backend first:")
        print("   cd backend && uv run uvicorn app.main:app --reload")
        return
    
    print("✅ Backend server is running")
    
    # Run automatic API discovery and testing
    print("\n🔍 Running API discovery performance tests...")
    results = framework.api_discovery_performance_test()
    
    print(f"\n📊 Completed {len(results)} performance tests")
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path(f"performance_report_{timestamp}.json")
    
    framework.generate_performance_report(report_file)
    
    # Print summary
    print("\n" + "=" * 50)
    print("🎯 Performance Test Summary:")
    
    for result in results:
        status = "✅" if result.success_rate > 95 else "⚠️" if result.success_rate > 80 else "❌"
        print(f"{status} {result.method} {result.endpoint}")
        print(f"   Response time: {result.avg_response_time:.3f}s (p95: {result.p95_response_time:.3f}s)")
        print(f"   Throughput: {result.throughput:.1f} req/s")
        print(f"   Success rate: {result.success_rate:.1f}%")
    
    print(f"\n📋 Full report: {report_file}")


if __name__ == "__main__":
    main()