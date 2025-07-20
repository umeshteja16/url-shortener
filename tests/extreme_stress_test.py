#!/usr/bin/env python3
"""
Redis Performance Test for Docker Setup
Tests Redis caching performance and hit/miss ratios
"""

import redis
import time
import asyncio
import aiohttp
import requests
import random
import string

class RedisPerformanceTester:
    def __init__(self, redis_url="redis://localhost:6379/0", base_url="http://localhost:5000"):
        self.redis_url = redis_url
        self.base_url = base_url
        self.redis_client = None
        
    def connect_redis(self):
        """Connect to Redis and test basic functionality"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            
            # Test connection
            ping_time = time.time()
            self.redis_client.ping()
            ping_duration = (time.time() - ping_time) * 1000
            
            print(f"✅ Redis connected successfully")
            print(f"⚡ Ping time: {ping_duration:.2f}ms")
            
            # Get Redis info
            info = self.redis_client.info()
            print(f"🔴 Redis version: {info.get('redis_version', 'Unknown')}")
            print(f"💾 Used memory: {info.get('used_memory_human', 'Unknown')}")
            print(f"🔌 Connected clients: {info.get('connected_clients', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False
    
    def test_redis_basic_performance(self):
        """Test basic Redis operations performance"""
        if not self.redis_client:
            return
        
        print("\n🔥 REDIS BASIC PERFORMANCE TEST")
        print("=" * 50)
        
        # Test SET operations
        set_times = []
        for i in range(1000):
            start = time.time()
            self.redis_client.set(f"test_key_{i}", f"test_value_{i}")
            set_times.append((time.time() - start) * 1000)
        
        avg_set_time = sum(set_times) / len(set_times)
        print(f"📊 SET Operations: {avg_set_time:.3f}ms average")
        print(f"🚀 SET Rate: {1000/avg_set_time:.0f} ops/ms")
        
        # Test GET operations
        get_times = []
        for i in range(1000):
            start = time.time()
            self.redis_client.get(f"test_key_{i}")
            get_times.append((time.time() - start) * 1000)
        
        avg_get_time = sum(get_times) / len(get_times)
        print(f"📊 GET Operations: {avg_get_time:.3f}ms average")
        print(f"🚀 GET Rate: {1000/avg_get_time:.0f} ops/ms")
        
        # Clean up test keys
        for i in range(1000):
            self.redis_client.delete(f"test_key_{i}")
        
        print(f"✅ Basic Redis performance test complete")
    
    def check_redis_cache_usage(self):
        """Check current Redis cache usage for URL shortener"""
        if not self.redis_client:
            return
        
        print("\n🔍 REDIS CACHE ANALYSIS")
        print("=" * 50)
        
        # Get all keys
        all_keys = self.redis_client.keys("*")
        url_keys = [key for key in all_keys if key.startswith("url:")]
        
        print(f"📊 Total keys in Redis: {len(all_keys)}")
        print(f"🔗 URL cache keys: {len(url_keys)}")
        
        if url_keys:
            print(f"📝 Sample URL cache keys:")
            for key in url_keys[:5]:  # Show first 5
                value = self.redis_client.get(key)
                print(f"   {key} → {value}")
            
            if len(url_keys) > 5:
                print(f"   ... and {len(url_keys) - 5} more")
        
        # Get Redis statistics
        info = self.redis_client.info()
        keyspace_hits = info.get('keyspace_hits', 0)
        keyspace_misses = info.get('keyspace_misses', 0)
        total_requests = keyspace_hits + keyspace_misses
        
        if total_requests > 0:
            hit_rate = (keyspace_hits / total_requests) * 100
            print(f"\n📈 CACHE STATISTICS:")
            print(f"   Cache Hits: {keyspace_hits:,}")
            print(f"   Cache Misses: {keyspace_misses:,}")
            print(f"   Hit Rate: {hit_rate:.1f}%")
            
            if hit_rate >= 80:
                print("✅ Excellent cache hit rate!")
            elif hit_rate >= 60:
                print("🔶 Good cache hit rate")
            elif hit_rate >= 40:
                print("⚠️  Moderate cache hit rate")
            else:
                print("❌ Low cache hit rate - needs optimization")
        else:
            print("📊 No cache statistics available yet")
    
    def create_test_urls_for_cache_test(self, count=10):
        """Create URLs specifically for cache testing"""
        print(f"\n🔧 Creating {count} URLs for cache testing...")
        
        created_urls = []
        for i in range(count):
            try:
                response = requests.post(
                    f"{self.base_url}/api/shorten",
                    json={"url": f"https://httpbin.org/status/200?cache_test={i}"},
                    timeout=10
                )
                
                if response.status_code == 201:
                    data = response.json()
                    created_urls.append(data['short_code'])
                    print(f"  ✓ Created: {data['short_code']}")
                else:
                    print(f"  ✗ Failed: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        print(f"✅ Created {len(created_urls)} URLs for cache testing")
        return created_urls
    
    async def test_cache_performance_impact(self, test_urls):
        """Test the performance impact of Redis caching"""
        if not test_urls:
            print("❌ No test URLs available")
            return
        
        print(f"\n🚀 CACHE PERFORMANCE IMPACT TEST")
        print("=" * 50)
        
        # Test 1: First time access (cache miss)
        print("🔍 Test 1: First access (cache miss expected)")
        
        cache_miss_times = []
        for url in test_urls[:5]:  # Test first 5 URLs
            start_time = time.time()
            response = requests.get(f"{self.base_url}/{url}", allow_redirects=False)
            duration = (time.time() - start_time) * 1000
            cache_miss_times.append(duration)
            print(f"   {url}: {duration:.1f}ms")
        
        avg_miss_time = sum(cache_miss_times) / len(cache_miss_times)
        print(f"📊 Average cache miss time: {avg_miss_time:.1f}ms")
        
        # Small delay
        await asyncio.sleep(1)
        
        # Test 2: Second time access (cache hit)
        print("\n🔍 Test 2: Second access (cache hit expected)")
        
        cache_hit_times = []
        for url in test_urls[:5]:  # Same URLs
            start_time = time.time()
            response = requests.get(f"{self.base_url}/{url}", allow_redirects=False)
            duration = (time.time() - start_time) * 1000
            cache_hit_times.append(duration)
            print(f"   {url}: {duration:.1f}ms")
        
        avg_hit_time = sum(cache_hit_times) / len(cache_hit_times)
        print(f"📊 Average cache hit time: {avg_hit_time:.1f}ms")
        
        # Calculate improvement
        if avg_miss_time > 0:
            improvement = ((avg_miss_time - avg_hit_time) / avg_miss_time) * 100
            speedup = avg_miss_time / avg_hit_time if avg_hit_time > 0 else 1
            
            print(f"\n🔥 CACHE PERFORMANCE RESULTS:")
            print(f"   Cache Miss: {avg_miss_time:.1f}ms")
            print(f"   Cache Hit: {avg_hit_time:.1f}ms")
            print(f"   Improvement: {improvement:.1f}% faster")
            print(f"   Speedup: {speedup:.1f}x")
            
            if improvement >= 50:
                print("✅ Excellent cache performance!")
            elif improvement >= 25:
                print("🔶 Good cache performance")
            elif improvement >= 10:
                print("⚠️  Moderate cache benefit")
            else:
                print("❌ Limited cache benefit")
    
    async def test_high_volume_cache_performance(self, test_urls):
        """Test cache performance under high volume"""
        if not test_urls:
            print("❌ No test URLs available")
            return
        
        print(f"\n🚀 HIGH VOLUME CACHE PERFORMANCE TEST")
        print("=" * 50)
        
        # Create high volume requests (mix of cached and new URLs)
        request_urls = []
        for i in range(1000):
            # 80% use existing URLs (cache hits), 20% random (cache misses)
            if random.random() < 0.8 and test_urls:
                request_urls.append(random.choice(test_urls))
            else:
                # Use a pattern that won't exist
                request_urls.append(f"nonexistent{random.randint(1000, 9999)}")
        
        print(f"🔥 Testing {len(request_urls)} requests (80% hits, 20% misses expected)")
        
        async def test_redirect(session, url):
            try:
                async with session.get(
                    f"{self.base_url}/{url}",
                    allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status in [302, 404]  # 302 = hit, 404 = miss
            except:
                return False
        
        start_time = time.time()
        
        connector = aiohttp.TCPConnector(limit=50)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [test_redirect(session, url) for url in request_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r is True)
        
        rps = successful / total_time
        avg_response_time = (total_time / len(request_urls)) * 1000
        
        print(f"📊 HIGH VOLUME RESULTS:")
        print(f"   Total Requests: {len(request_urls)}")
        print(f"   Successful: {successful}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Requests/Second: {rps:.1f}")
        print(f"   Avg Response Time: {avg_response_time:.1f}ms")
        
        return rps
    
    async def run_redis_performance_test(self):
        """Run complete Redis performance test suite"""
        print("🔴 REDIS PERFORMANCE TEST SUITE")
        print("🎯 Testing Redis caching in Docker setup")
        print("=" * 60)
        
        # Connect to Redis
        if not self.connect_redis():
            print("❌ Cannot proceed without Redis connection")
            return
        
        # Test basic Redis performance
        self.test_redis_basic_performance()
        
        # Check current cache usage
        self.check_redis_cache_usage()
        
        # Create test URLs
        test_urls = self.create_test_urls_for_cache_test(15)
        
        # Test cache performance impact
        await self.test_cache_performance_impact(test_urls)
        
        # Test high volume performance
        high_volume_rps = await self.test_high_volume_cache_performance(test_urls)
        
        # Final summary
        print("\n" + "=" * 60)
        print("🏆 REDIS PERFORMANCE SUMMARY")
        print("=" * 60)
        
        if high_volume_rps:
            print(f"🚀 High Volume Performance: {high_volume_rps:.1f} req/s")
            
            if high_volume_rps >= 400:
                print("✅ Redis is significantly boosting performance!")
            elif high_volume_rps >= 200:
                print("🔶 Redis providing good performance benefit")
            else:
                print("⚠️  Redis benefit may be limited")
        
        # Final cache statistics
        self.check_redis_cache_usage()
        
        print("=" * 60)

def main():
    print("🔴 REDIS PERFORMANCE TEST")
    print("🎯 Testing Redis caching performance in Docker")
    print("💥 Analyzing cache hit/miss ratios and speed")
    print()
    
    tester = RedisPerformanceTester()
    asyncio.run(tester.run_redis_performance_test())

if __name__ == "__main__":
    main()