#!/usr/bin/env python3
"""
CC02 v33.0 パフォーマンスベンチマーク最適化ツール - Infinite Loop Cycle 2
Performance Benchmark Optimizer for API Response Time Analysis
"""

import asyncio
import aiohttp
import time
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import concurrent.futures
import psutil
import threading
from collections import defaultdict


@dataclass
class BenchmarkResult:
    """ベンチマーク結果データクラス"""
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    response_size_bytes: int
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: datetime
    error: Optional[str] = None


@dataclass
class EndpointMetrics:
    """エンドポイント メトリクス"""
    endpoint: str
    method: str
    total_requests: int
    success_count: int
    failure_count: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput_rps: float
    error_rate: float
    avg_memory_usage: float
    avg_cpu_usage: float


class PerformanceBenchmarkOptimizer:
    """パフォーマンスベンチマーク最適化ツール"""
    
    def __init__(self, project_root: Path, base_url: str = "http://localhost:8000"):
        self.project_root = project_root
        self.base_url = base_url
        self.output_path = project_root / "scripts" / "performance_reports"
        self.output_path.mkdir(exist_ok=True)
        
        # Benchmark configuration
        self.config = {
            "concurrent_users": [1, 5, 10, 20, 50],
            "test_duration_seconds": 30,
            "warmup_requests": 10,
            "request_timeout": 30,
            "memory_threshold_mb": 512,
            "cpu_threshold_percent": 80,
            "response_time_threshold_ms": 1000
        }
        
        # Test endpoints to benchmark
        self.test_endpoints = [
            {"path": "/api/v1/health", "method": "GET"},
            {"path": "/api/v1/users", "method": "GET"},
            {"path": "/api/v1/organizations", "method": "GET"},
            {"path": "/api/v1/projects", "method": "GET"},
            {"path": "/api/v1/tasks", "method": "GET"},
            {"path": "/api/v1/expenses", "method": "GET"},
            {"path": "/docs", "method": "GET"},
        ]
        
        # System monitoring
        self.system_metrics = []
        self.monitoring_active = False
        
    def start_system_monitoring(self):
        """システムモニタリング開始"""
        self.monitoring_active = True
        
        def monitor():
            while self.monitoring_active:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                
                self.system_metrics.append({
                    "timestamp": datetime.now(),
                    "cpu_percent": cpu_percent,
                    "memory_used_mb": memory_info.used / (1024 * 1024),
                    "memory_percent": memory_info.percent
                })
                
                time.sleep(1)
        
        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.start()
    
    def stop_system_monitoring(self):
        """システムモニタリング停止"""
        self.monitoring_active = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
    
    async def benchmark_endpoint(self, session: aiohttp.ClientSession, endpoint: Dict[str, str], 
                                user_count: int, duration_seconds: int) -> List[BenchmarkResult]:
        """個別エンドポイントのベンチマーク"""
        url = f"{self.base_url}{endpoint['path']}"
        method = endpoint['method'].upper()
        results = []
        
        print(f"  📊 Benchmarking {method} {endpoint['path']} with {user_count} users...")
        
        # Warmup requests
        for _ in range(self.config["warmup_requests"]):
            try:
                async with session.request(method, url) as response:
                    await response.read()
            except:
                pass
        
        # Actual benchmark
        start_time = time.time()
        tasks = []
        
        async def make_request():
            request_start = time.time()
            cpu_before = psutil.cpu_percent()
            memory_before = psutil.virtual_memory().used / (1024 * 1024)
            
            try:
                async with session.request(method, url, timeout=aiohttp.ClientTimeout(total=self.config["request_timeout"])) as response:
                    content = await response.read()
                    
                    request_end = time.time()
                    response_time_ms = (request_end - request_start) * 1000
                    
                    cpu_after = psutil.cpu_percent()
                    memory_after = psutil.virtual_memory().used / (1024 * 1024)
                    
                    result = BenchmarkResult(
                        endpoint=endpoint['path'],
                        method=method,
                        response_time_ms=response_time_ms,
                        status_code=response.status,
                        response_size_bytes=len(content),
                        memory_usage_mb=memory_after - memory_before,
                        cpu_usage_percent=cpu_after - cpu_before,
                        timestamp=datetime.now()
                    )
                    results.append(result)
                    
            except asyncio.TimeoutError:
                result = BenchmarkResult(
                    endpoint=endpoint['path'],
                    method=method,
                    response_time_ms=self.config["request_timeout"] * 1000,
                    status_code=408,
                    response_size_bytes=0,
                    memory_usage_mb=0,
                    cpu_usage_percent=0,
                    timestamp=datetime.now(),
                    error="Timeout"
                )
                results.append(result)
            except Exception as e:
                result = BenchmarkResult(
                    endpoint=endpoint['path'],
                    method=method,
                    response_time_ms=0,
                    status_code=500,
                    response_size_bytes=0,
                    memory_usage_mb=0,
                    cpu_usage_percent=0,
                    timestamp=datetime.now(),
                    error=str(e)
                )
                results.append(result)
        
        # Create concurrent requests
        while time.time() - start_time < duration_seconds:
            batch_tasks = [make_request() for _ in range(user_count)]
            tasks.extend(batch_tasks)
            await asyncio.gather(*batch_tasks)
            await asyncio.sleep(0.1)  # Small delay between batches
        
        return results
    
    def calculate_endpoint_metrics(self, results: List[BenchmarkResult]) -> EndpointMetrics:
        """エンドポイントメトリクスを計算"""
        if not results:
            return None
        
        # Filter successful requests for response time calculations
        successful_results = [r for r in results if r.status_code == 200 and r.error is None]
        response_times = [r.response_time_ms for r in successful_results]
        
        if not response_times:
            response_times = [0]
        
        total_requests = len(results)
        success_count = len(successful_results)
        failure_count = total_requests - success_count
        
        # Calculate percentiles
        response_times.sort()
        p50 = response_times[int(len(response_times) * 0.5)] if response_times else 0
        p95 = response_times[int(len(response_times) * 0.95)] if response_times else 0
        p99 = response_times[int(len(response_times) * 0.99)] if response_times else 0
        
        # Calculate time span for throughput
        if results:
            time_span = (results[-1].timestamp - results[0].timestamp).total_seconds()
            throughput_rps = success_count / max(time_span, 1)
        else:
            throughput_rps = 0
        
        metrics = EndpointMetrics(
            endpoint=results[0].endpoint,
            method=results[0].method,
            total_requests=total_requests,
            success_count=success_count,
            failure_count=failure_count,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p50_response_time=p50,
            p95_response_time=p95,
            p99_response_time=p99,
            throughput_rps=throughput_rps,
            error_rate=(failure_count / total_requests * 100) if total_requests > 0 else 0,
            avg_memory_usage=statistics.mean([r.memory_usage_mb for r in results]) if results else 0,
            avg_cpu_usage=statistics.mean([r.cpu_usage_percent for r in results]) if results else 0
        )
        
        return metrics
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """包括的パフォーマンスベンチマークを実行"""
        print("🚀 CC02 v33.0 Performance Benchmark Optimization")
        print("=" * 60)
        
        self.start_system_monitoring()
        
        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "configuration": self.config,
            "endpoint_metrics": {},
            "load_test_results": {},
            "system_metrics": [],
            "performance_issues": [],
            "optimization_recommendations": []
        }
        
        try:
            # Test different load levels
            for user_count in self.config["concurrent_users"]:
                print(f"\n🔄 Running load test with {user_count} concurrent users...")
                
                connector = aiohttp.TCPConnector(limit=user_count * 2)
                timeout = aiohttp.ClientTimeout(total=self.config["request_timeout"])
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    load_results = {}
                    
                    for endpoint in self.test_endpoints:
                        endpoint_results = await self.benchmark_endpoint(
                            session, endpoint, user_count, self.config["test_duration_seconds"]
                        )
                        
                        metrics = self.calculate_endpoint_metrics(endpoint_results)
                        if metrics:
                            endpoint_key = f"{endpoint['method']} {endpoint['path']}"
                            load_results[endpoint_key] = asdict(metrics)
                    
                    benchmark_results["load_test_results"][f"{user_count}_users"] = load_results
            
            # Analyze results and generate insights
            benchmark_results["endpoint_metrics"] = self._aggregate_endpoint_metrics(benchmark_results["load_test_results"])
            benchmark_results["performance_issues"] = self._identify_performance_issues(benchmark_results["endpoint_metrics"])
            benchmark_results["optimization_recommendations"] = self._generate_optimization_recommendations(benchmark_results)
            
        finally:
            self.stop_system_monitoring()
            benchmark_results["system_metrics"] = [
                {
                    "timestamp": m["timestamp"].isoformat(),
                    "cpu_percent": m["cpu_percent"],
                    "memory_used_mb": m["memory_used_mb"],
                    "memory_percent": m["memory_percent"]
                } for m in self.system_metrics[-100:]  # Keep last 100 samples
            ]
        
        # Save comprehensive report
        report_file = self.output_path / f"performance_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Benchmark complete! Report saved to: {report_file}")
        
        # Print summary
        self._print_benchmark_summary(benchmark_results)
        
        return benchmark_results
    
    def _aggregate_endpoint_metrics(self, load_test_results: Dict[str, Any]) -> Dict[str, Any]:
        """エンドポイントメトリクスを集約"""
        aggregated = defaultdict(lambda: {
            "response_times": [],
            "throughput_values": [],
            "error_rates": [],
            "memory_usage": [],
            "cpu_usage": []
        })
        
        for user_count, endpoints in load_test_results.items():
            for endpoint, metrics in endpoints.items():
                aggregated[endpoint]["response_times"].append(metrics["avg_response_time"])
                aggregated[endpoint]["throughput_values"].append(metrics["throughput_rps"])
                aggregated[endpoint]["error_rates"].append(metrics["error_rate"])
                aggregated[endpoint]["memory_usage"].append(metrics["avg_memory_usage"])
                aggregated[endpoint]["cpu_usage"].append(metrics["avg_cpu_usage"])
        
        # Calculate aggregated statistics
        final_metrics = {}
        for endpoint, data in aggregated.items():
            final_metrics[endpoint] = {
                "avg_response_time": statistics.mean(data["response_times"]) if data["response_times"] else 0,
                "max_response_time": max(data["response_times"]) if data["response_times"] else 0,
                "avg_throughput": statistics.mean(data["throughput_values"]) if data["throughput_values"] else 0,
                "max_throughput": max(data["throughput_values"]) if data["throughput_values"] else 0,
                "avg_error_rate": statistics.mean(data["error_rates"]) if data["error_rates"] else 0,
                "max_error_rate": max(data["error_rates"]) if data["error_rates"] else 0,
                "avg_memory_usage": statistics.mean(data["memory_usage"]) if data["memory_usage"] else 0,
                "avg_cpu_usage": statistics.mean(data["cpu_usage"]) if data["cpu_usage"] else 0
            }
        
        return final_metrics
    
    def _identify_performance_issues(self, endpoint_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """パフォーマンス問題を特定"""
        issues = []
        
        for endpoint, metrics in endpoint_metrics.items():
            # Slow response times
            if metrics["max_response_time"] > self.config["response_time_threshold_ms"]:
                issues.append({
                    "type": "slow_response",
                    "endpoint": endpoint,
                    "severity": "high" if metrics["max_response_time"] > 2000 else "medium",
                    "value": metrics["max_response_time"],
                    "threshold": self.config["response_time_threshold_ms"],
                    "description": f"Response time {metrics['max_response_time']:.1f}ms exceeds threshold {self.config['response_time_threshold_ms']}ms"
                })
            
            # High error rates
            if metrics["max_error_rate"] > 5:  # 5% error rate threshold
                issues.append({
                    "type": "high_error_rate",
                    "endpoint": endpoint,
                    "severity": "high" if metrics["max_error_rate"] > 10 else "medium",
                    "value": metrics["max_error_rate"],
                    "threshold": 5,
                    "description": f"Error rate {metrics['max_error_rate']:.1f}% exceeds acceptable threshold"
                })
            
            # Low throughput
            if metrics["max_throughput"] < 10:  # Less than 10 RPS
                issues.append({
                    "type": "low_throughput",
                    "endpoint": endpoint,
                    "severity": "medium",
                    "value": metrics["max_throughput"],
                    "threshold": 10,
                    "description": f"Low throughput {metrics['max_throughput']:.1f} RPS indicates scalability issues"
                })
            
            # High memory usage
            if metrics["avg_memory_usage"] > self.config["memory_threshold_mb"]:
                issues.append({
                    "type": "high_memory_usage",
                    "endpoint": endpoint,
                    "severity": "medium",
                    "value": metrics["avg_memory_usage"],
                    "threshold": self.config["memory_threshold_mb"],
                    "description": f"High memory usage {metrics['avg_memory_usage']:.1f}MB may indicate memory leaks"
                })
        
        return issues
    
    def _generate_optimization_recommendations(self, benchmark_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """最適化推奨事項を生成"""
        recommendations = []
        
        issues = benchmark_results["performance_issues"]
        
        # Group issues by type
        issue_counts = defaultdict(int)
        for issue in issues:
            issue_counts[issue["type"]] += 1
        
        # Response time optimization
        if issue_counts["slow_response"] > 0:
            recommendations.append({
                "category": "response_time_optimization",
                "priority": "high",
                "issue_count": issue_counts["slow_response"],
                "recommendation": "Optimize slow endpoints with database query optimization and caching",
                "implementation": [
                    "Add database indexes for frequently queried columns",
                    "Implement Redis caching for read-heavy endpoints",
                    "Use database connection pooling",
                    "Optimize SQLAlchemy queries with eager loading"
                ],
                "expected_impact": "20-50% reduction in response times"
            })
        
        # Error rate optimization
        if issue_counts["high_error_rate"] > 0:
            recommendations.append({
                "category": "error_handling_improvement",
                "priority": "high",
                "issue_count": issue_counts["high_error_rate"],
                "recommendation": "Improve error handling and request validation",
                "implementation": [
                    "Add comprehensive input validation",
                    "Implement circuit breakers for external dependencies",
                    "Add proper exception handling with logging",
                    "Implement request retry mechanisms"
                ],
                "expected_impact": "Reduce error rates to <1%"
            })
        
        # Throughput optimization
        if issue_counts["low_throughput"] > 0:
            recommendations.append({
                "category": "scalability_improvement",
                "priority": "medium",
                "issue_count": issue_counts["low_throughput"],
                "recommendation": "Improve application scalability and throughput",
                "implementation": [
                    "Implement async/await patterns for I/O operations",
                    "Add request rate limiting and throttling",
                    "Optimize database connection management",
                    "Consider horizontal scaling with load balancers"
                ],
                "expected_impact": "2-5x improvement in throughput capacity"
            })
        
        # Memory optimization
        if issue_counts["high_memory_usage"] > 0:
            recommendations.append({
                "category": "memory_optimization",
                "priority": "medium",
                "issue_count": issue_counts["high_memory_usage"],
                "recommendation": "Optimize memory usage and prevent memory leaks",
                "implementation": [
                    "Profile memory usage with tools like memory_profiler",
                    "Implement proper object lifecycle management",
                    "Add memory monitoring and alerting",
                    "Optimize large object handling and serialization"
                ],
                "expected_impact": "30-60% reduction in memory footprint"
            })
        
        # General performance recommendations
        recommendations.extend([
            {
                "category": "monitoring_implementation",
                "priority": "high",
                "recommendation": "Implement comprehensive performance monitoring",
                "implementation": [
                    "Add APM (Application Performance Monitoring) tools",
                    "Implement custom metrics collection",
                    "Set up performance alerting thresholds",
                    "Create performance dashboards"
                ],
                "expected_impact": "Enable proactive performance issue detection"
            },
            {
                "category": "load_testing_automation",
                "priority": "medium",
                "recommendation": "Automate regular performance testing",
                "implementation": [
                    "Integrate performance tests into CI/CD pipeline",
                    "Set up scheduled performance regression testing",
                    "Create performance test data management",
                    "Implement performance budgets and gates"
                ],
                "expected_impact": "Prevent performance regressions in production"
            }
        ])
        
        return recommendations
    
    def _print_benchmark_summary(self, results: Dict[str, Any]):
        """ベンチマーク結果サマリーを出力"""
        print("\n" + "=" * 60)
        print("📊 Performance Benchmark Summary")
        print("=" * 60)
        
        # Overall statistics
        total_issues = len(results["performance_issues"])
        high_severity_issues = len([i for i in results["performance_issues"] if i["severity"] == "high"])
        
        print(f"Total endpoints tested: {len(results['endpoint_metrics'])}")
        print(f"Performance issues found: {total_issues}")
        print(f"High severity issues: {high_severity_issues}")
        
        # Top slow endpoints
        print("\n🐌 Slowest Endpoints:")
        endpoint_times = [(endpoint, metrics["max_response_time"]) 
                         for endpoint, metrics in results["endpoint_metrics"].items()]
        endpoint_times.sort(key=lambda x: x[1], reverse=True)
        
        for i, (endpoint, response_time) in enumerate(endpoint_times[:5], 1):
            print(f"  {i}. {endpoint}: {response_time:.1f}ms")
        
        # Error rates
        print("\n❌ Endpoints with Errors:")
        error_endpoints = [(endpoint, metrics["max_error_rate"]) 
                          for endpoint, metrics in results["endpoint_metrics"].items() 
                          if metrics["max_error_rate"] > 0]
        error_endpoints.sort(key=lambda x: x[1], reverse=True)
        
        for i, (endpoint, error_rate) in enumerate(error_endpoints[:3], 1):
            print(f"  {i}. {endpoint}: {error_rate:.1f}% error rate")
        
        # Top recommendations
        print("\n🎯 Top Recommendations:")
        for i, rec in enumerate(results["optimization_recommendations"][:3], 1):
            print(f"  {i}. {rec['category']}: {rec['recommendation']}")
        
        print("\n📈 Next Steps:")
        print("  1. Address high severity performance issues")
        print("  2. Implement caching for slow endpoints")
        print("  3. Add database indexes for query optimization")
        print("  4. Set up continuous performance monitoring")
        print("  5. Integrate performance tests into CI/CD pipeline")


async def main():
    """メイン実行関数"""
    project_root = Path.cwd()
    
    optimizer = PerformanceBenchmarkOptimizer(project_root)
    results = await optimizer.run_comprehensive_benchmark()
    
    return results


if __name__ == "__main__":
    asyncio.run(main())