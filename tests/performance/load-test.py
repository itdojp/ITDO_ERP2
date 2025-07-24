"""負荷テストスイート"""
import asyncio
import time
from typing import List
import httpx
import statistics

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []

    async def single_request(self, client: httpx.AsyncClient, endpoint: str):
        """単一リクエスト実行"""
        start = time.time()
        try:
            response = await client.get(f"{self.base_url}{endpoint}")
            duration = time.time() - start
            return {
                "endpoint": endpoint,
                "status": response.status_code,
                "duration": duration,
                "success": 200 <= response.status_code < 300
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "status": 0,
                "duration": time.time() - start,
                "success": False,
                "error": str(e)
            }

    async def load_test(self, endpoint: str, concurrent: int = 10, requests: int = 100):
        """負荷テスト実行"""
        async with httpx.AsyncClient() as client:
            tasks = []
            for _ in range(requests):
                task = self.single_request(client, endpoint)
                tasks.append(task)

                # 同時実行数を制限
                if len(tasks) >= concurrent:
                    results = await asyncio.gather(*tasks)
                    self.results.extend(results)
                    tasks = []

            # 残りのタスク実行
            if tasks:
                results = await asyncio.gather(*tasks)
                self.results.extend(results)

    def analyze_results(self):
        """結果分析"""
        if not self.results:
            return {}

        durations = [r["duration"] for r in self.results if r["success"]]
        success_count = sum(1 for r in self.results if r["success"])

        return {
            "total_requests": len(self.results),
            "success_count": success_count,
            "success_rate": success_count / len(self.results) * 100,
            "avg_duration": statistics.mean(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "p95_duration": statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else 0,
            "p99_duration": statistics.quantiles(durations, n=100)[98] if len(durations) > 100 else 0
        }

    def print_results(self, results):
        """結果出力"""
        print("\n🔬 Load Test Results:")
        print(f"   Total Requests: {results['total_requests']}")
        print(f"   Success Rate: {results['success_rate']:.1f}%")
        print(f"   Avg Duration: {results['avg_duration']:.3f}s")
        print(f"   P95 Duration: {results['p95_duration']:.3f}s")
        print(f"   P99 Duration: {results['p99_duration']:.3f}s")

async def main():
    """メイン実行"""
    tester = LoadTester()

    # 各エンドポイントをテスト
    endpoints = ["/health", "/api/v1/users", "/api/v1/organizations"]

    print("🚀 Starting load tests...")
    
    for endpoint in endpoints:
        print(f"\n📊 Testing {endpoint}...")
        tester.results.clear()  # Reset results for each endpoint
        await tester.load_test(endpoint, concurrent=20, requests=200)
        
        results = tester.analyze_results()
        tester.print_results(results)

    print("\n✅ Load tests completed!")

if __name__ == "__main__":
    asyncio.run(main())