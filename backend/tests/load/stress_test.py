import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import json

class StressTest:
    """Advanced stress testing for API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
        
    async def make_request(self, session: aiohttp.ClientSession, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a single HTTP request and measure performance."""
        start_time = time.time()
        
        try:
            async with session.request(method, f"{self.base_url}{endpoint}", **kwargs) as response:
                end_time = time.time()
                response_text = await response.text()
                
                return {
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "response_size": len(response_text),
                    "success": 200 <= response.status < 400,
                    "timestamp": start_time
                }
        except Exception as e:
            end_time = time.time()
            return {
                "method": method,
                "endpoint": endpoint,
                "status_code": 0,
                "response_time": end_time - start_time,
                "response_size": 0,
                "success": False,
                "error": str(e),
                "timestamp": start_time
            }
    
    async def run_concurrent_requests(self, concurrent_users: int, requests_per_user: int, endpoint: str = "/api/v1/health"):
        """Run concurrent requests to simulate load."""
        print(f"🚀 Starting stress test: {concurrent_users} users, {requests_per_user} requests each")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for user in range(concurrent_users):
                for req in range(requests_per_user):
                    task = self.make_request(session, "GET", endpoint)
                    tasks.append(task)
            
            # Execute all requests concurrently
            results = await asyncio.gather(*tasks)
            self.results.extend(results)
        
        return self.analyze_results()
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and generate statistics."""
        if not self.results:
            return {"error": "No results to analyze"}
        
        # Filter successful requests
        successful = [r for r in self.results if r["success"]]
        failed = [r for r in self.results if not r["success"]]
        
        response_times = [r["response_time"] for r in successful]
        
        if not response_times:
            return {"error": "No successful requests"}
        
        analysis = {
            "total_requests": len(self.results),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / len(self.results) * 100,
            "response_time_stats": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": self._percentile(response_times, 95),
                "p99": self._percentile(response_times, 99)
            },
            "throughput": len(successful) / max(response_times) if response_times else 0,
            "status_code_distribution": self._count_status_codes(),
            "errors": [r.get("error") for r in failed if "error" in r]
        }
        
        return analysis
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of response times."""
        data_sorted = sorted(data)
        index = int(len(data_sorted) * percentile / 100)
        return data_sorted[min(index, len(data_sorted) - 1)]
    
    def _count_status_codes(self) -> Dict[int, int]:
        """Count occurrences of each status code."""
        status_counts = {}
        for result in self.results:
            code = result["status_code"]
            status_counts[code] = status_counts.get(code, 0) + 1
        return status_counts
    
    def print_report(self, analysis: Dict[str, Any]):
        """Print detailed test report."""
        print("\n" + "="*50)
        print("🧪 STRESS TEST RESULTS")
        print("="*50)
        
        print(f"📊 Total Requests: {analysis['total_requests']}")
        print(f"✅ Successful: {analysis['successful_requests']}")
        print(f"❌ Failed: {analysis['failed_requests']}")
        print(f"📈 Success Rate: {analysis['success_rate']:.2f}%")
        
        rt_stats = analysis["response_time_stats"]
        print(f"\n⏱️  Response Time Statistics (seconds):")
        print(f"   Min: {rt_stats['min']:.4f}")
        print(f"   Max: {rt_stats['max']:.4f}")
        print(f"   Mean: {rt_stats['mean']:.4f}")
        print(f"   Median: {rt_stats['median']:.4f}")
        print(f"   95th percentile: {rt_stats['p95']:.4f}")
        print(f"   99th percentile: {rt_stats['p99']:.4f}")
        
        print(f"\n🚀 Throughput: {analysis['throughput']:.2f} requests/second")
        
        print(f"\n📋 Status Code Distribution:")
        for code, count in analysis["status_code_distribution"].items():
            print(f"   {code}: {count} requests")
        
        if analysis.get("errors"):
            print(f"\n❗ Errors encountered:")
            for error in set(analysis["errors"]):
                print(f"   - {error}")

async def main():
    """Run comprehensive stress tests."""
    stress_test = StressTest()
    
    # Test scenarios
    scenarios = [
        {"users": 10, "requests": 10, "name": "Light Load"},
        {"users": 50, "requests": 20, "name": "Medium Load"},
        {"users": 100, "requests": 10, "name": "High Concurrency"},
    ]
    
    for scenario in scenarios:
        print(f"\n🎯 Running scenario: {scenario['name']}")
        stress_test.results.clear()  # Reset results
        
        analysis = await stress_test.run_concurrent_requests(
            concurrent_users=scenario["users"],
            requests_per_user=scenario["requests"]
        )
        
        stress_test.print_report(analysis)
        
        # Brief pause between scenarios
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())