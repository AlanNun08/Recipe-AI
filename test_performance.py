#!/usr/bin/env python3
"""
Performance Tests
Tests API response times, concurrent usage, and system performance
"""

import asyncio
import httpx
import time
import statistics
from datetime import datetime

class TestPerformance:
    def __init__(self):
        self.backend_url = "http://localhost:8001/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def measure_endpoint_performance(self, endpoint, method="GET", data=None, name="Endpoint"):
        """Measure response time for an endpoint"""
        try:
            start_time = time.time()
            
            if method == "GET":
                response = await self.client.get(f"{self.backend_url}/{endpoint}")
            else:
                response = await self.client.post(f"{self.backend_url}/{endpoint}", json=data)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                return response_time, True
            else:
                self.log(f"❌ {name} returned status {response.status_code}", "ERROR")  
                return response_time, False
                
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            self.log(f"❌ {name} error: {str(e)}", "ERROR")
            return response_time, False
    
    async def test_recipe_history_performance(self):
        """Test recipe history endpoint performance"""
        self.log("=== Testing Recipe History Performance ===")
        
        endpoint = f"recipes/history/{self.demo_user_id}"
        response_times = []
        successful_requests = 0
        
        # Run 10 requests to measure consistency
        for i in range(10):
            response_time, success = await self.measure_endpoint_performance(
                endpoint, name="Recipe History"
            )
            response_times.append(response_time)
            if success:
                successful_requests += 1
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        if successful_requests == 0:
            self.log("❌ No successful requests for performance test", "ERROR")
            return False
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        self.log(f"Recipe History Performance:")
        self.log(f"  Average: {avg_time:.2f}ms")
        self.log(f"  Min: {min_time:.2f}ms")
        self.log(f"  Max: {max_time:.2f}ms")
        self.log(f"  Success Rate: {successful_requests}/10")
        
        # Performance thresholds
        if avg_time > 2000:  # 2 seconds
            self.log(f"⚠️  Recipe history is slow (avg: {avg_time:.2f}ms)", "WARNING")
        else:
            self.log(f"✅ Recipe history performance acceptable")
        
        return successful_requests >= 8  # At least 80% success rate
    
    async def test_recipe_generation_performance(self):
        """Test recipe generation endpoint performance"""
        self.log("=== Testing Recipe Generation Performance ===")
        
        recipe_data = {
            "user_id": self.demo_user_id,
            "cuisine_type": "Italian",
            "recipe_category": "cuisine",
            "meal_type": "dinner",
            "servings": 4,
            "difficulty": "medium",
            "dietary_preferences": []
        }
        
        response_times = []
        successful_requests = 0
        
        # Run 5 recipe generation requests (slower endpoint)
        for i in range(5):
            response_time, success = await self.measure_endpoint_performance(
                "recipes/generate", method="POST", data=recipe_data, name="Recipe Generation"
            )
            response_times.append(response_time)
            if success:
                successful_requests += 1
            
            # Longer delay between generation requests
            await asyncio.sleep(0.5)
        
        if successful_requests == 0:
            self.log("❌ No successful recipe generations", "ERROR")
            return False
        
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        self.log(f"Recipe Generation Performance:")
        self.log(f"  Average: {avg_time:.2f}ms")
        self.log(f"  Min: {min_time:.2f}ms")
        self.log(f"  Max: {max_time:.2f}ms")
        self.log(f"  Success Rate: {successful_requests}/5")
        
        # More lenient threshold for generation (AI processing)
        if avg_time > 5000:  # 5 seconds
            self.log(f"⚠️  Recipe generation is slow (avg: {avg_time:.2f}ms)", "WARNING")
        else:
            self.log(f"✅ Recipe generation performance acceptable")
        
        return successful_requests >= 4  # At least 80% success rate
    
    async def test_recipe_detail_performance(self):
        """Test recipe detail endpoint performance"""
        self.log("=== Testing Recipe Detail Performance ===")
        
        # Get a recipe ID to test
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log("❌ Could not get recipe for detail performance test", "ERROR")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])
            
            if not recipes:
                self.log("❌ No recipes available for detail performance test", "ERROR")
                return False
            
            test_recipe_id = recipes[0].get("id")
            
        except Exception as e:
            self.log(f"❌ Error getting recipe for detail test: {str(e)}", "ERROR")
            return False
        
        response_times = []
        successful_requests = 0
        
        # Run 10 detail requests
        for i in range(10):
            response_time, success = await self.measure_endpoint_performance(
                f"recipes/{test_recipe_id}/detail", name="Recipe Detail"
            )
            response_times.append(response_time)
            if success:
                successful_requests += 1
            
            await asyncio.sleep(0.1)
        
        if successful_requests == 0:
            self.log("❌ No successful recipe detail requests", "ERROR")
            return False
        
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        self.log(f"Recipe Detail Performance:")
        self.log(f"  Average: {avg_time:.2f}ms")
        self.log(f"  Min: {min_time:.2f}ms")
        self.log(f"  Max: {max_time:.2f}ms")
        self.log(f"  Success Rate: {successful_requests}/10")
        
        if avg_time > 1500:  # 1.5 seconds
            self.log(f"⚠️  Recipe detail is slow (avg: {avg_time:.2f}ms)", "WARNING")
        else:
            self.log(f"✅ Recipe detail performance acceptable")
        
        return successful_requests >= 8
    
    async def test_concurrent_requests(self):
        """Test system behavior under concurrent load"""
        self.log("=== Testing Concurrent Request Handling ===")
        
        async def make_request(request_id):
            """Make a single concurrent request"""
            try:
                start_time = time.time()
                response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                success = response.status_code == 200
                
                return request_id, response_time, success
                
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                return request_id, response_time, False
        
        # Create 20 concurrent requests
        concurrent_requests = 20
        self.log(f"Launching {concurrent_requests} concurrent requests...")
        
        start_time = time.time()
        tasks = [make_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        # Analyze results
        successful_requests = sum(1 for _, _, success in results if success)
        response_times = [rt for _, rt, success in results if success]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = 0
            max_response_time = 0
        
        self.log(f"Concurrent Request Results:")
        self.log(f"  Total Time: {total_time:.2f}ms")
        self.log(f"  Successful: {successful_requests}/{concurrent_requests}")
        self.log(f"  Success Rate: {(successful_requests/concurrent_requests)*100:.1f}%")
        self.log(f"  Avg Response Time: {avg_response_time:.2f}ms")
        self.log(f"  Max Response Time: {max_response_time:.2f}ms")
        
        # Performance criteria
        success_rate = successful_requests / concurrent_requests
        
        if success_rate >= 0.9 and avg_response_time < 3000:
            self.log("✅ Concurrent request handling acceptable")
            return True
        else:
            self.log("⚠️  Concurrent request handling needs improvement", "WARNING")
            return success_rate >= 0.7  # At least 70% success rate
    
    async def test_memory_usage_stability(self):
        """Test that repeated requests don't cause memory issues"""
        self.log("=== Testing Memory Usage Stability ===")
        
        # Make 50 sequential requests to test for memory leaks
        request_count = 50
        failed_requests = 0
        response_times = []
        
        self.log(f"Making {request_count} sequential requests...")
        
        for i in range(request_count):
            try:
                start_time = time.time()
                response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)
                
                if response.status_code != 200:
                    failed_requests += 1
                
                # Log progress every 10 requests
                if (i + 1) % 10 == 0:
                    self.log(f"  Completed {i + 1}/{request_count} requests")
                
                # Small delay to prevent overwhelming the server
                await asyncio.sleep(0.05)
                
            except Exception as e:
                failed_requests += 1
        
        # Analyze stability
        if len(response_times) >= 40:  # At least 80% successful
            # Check if response times are increasing (potential memory leak)
            first_half = response_times[:len(response_times)//2]
            second_half = response_times[len(response_times)//2:]
            
            avg_first_half = statistics.mean(first_half)
            avg_second_half = statistics.mean(second_half)
            
            performance_degradation = avg_second_half / avg_first_half if avg_first_half > 0 else 1
            
            self.log(f"Memory Stability Results:")
            self.log(f"  Failed Requests: {failed_requests}/{request_count}")
            self.log(f"  First Half Avg: {avg_first_half:.2f}ms")
            self.log(f"  Second Half Avg: {avg_second_half:.2f}ms")
            self.log(f"  Performance Ratio: {performance_degradation:.2f}")
            
            if performance_degradation < 1.5 and failed_requests < 5:
                self.log("✅ Memory usage stability acceptable")
                return True
            else:
                self.log("⚠️  Potential memory or performance issues detected", "WARNING")
                return False
        else:
            self.log("❌ Too many failed requests for stability test", "ERROR")
            return False
    
    async def run_all_tests(self):
        """Run all performance tests"""
        self.log("🚀 Starting Performance Tests")
        self.log("=" * 50)
        
        tests = [
            ("Recipe History Performance", self.test_recipe_history_performance),
            ("Recipe Generation Performance", self.test_recipe_generation_performance),
            ("Recipe Detail Performance", self.test_recipe_detail_performance),
            ("Concurrent Requests", self.test_concurrent_requests),
            ("Memory Stability", self.test_memory_usage_stability)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running {test_name} test...")
            try:
                result = await test_func()
                if result:
                    passed += 1
                    self.log(f"✅ {test_name} test PASSED")
                else:
                    self.log(f"❌ {test_name} test FAILED")
            except Exception as e:
                self.log(f"❌ {test_name} test ERROR: {str(e)}", "ERROR")
        
        self.log("=" * 50)
        self.log(f"🎯 Performance Tests Complete: {passed}/{total} passed")
        
        if passed == total:
            self.log("🎉 All performance tests PASSED!")
            return True
        else:
            self.log(f"❌ {total - passed} test(s) FAILED")
            return False

async def main():
    tester = TestPerformance()
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Performance tests completed successfully!")
    else:
        print("\n❌ Performance tests failed!")
        exit(1)