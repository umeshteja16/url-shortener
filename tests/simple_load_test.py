#!/usr/bin/env python3
"""
Simple Load Testing Script for URL Shortener
Quick and easy performance testing
"""

import requests
import time
import threading
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed

class SimpleLoadTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.created_urls = []
        self.results = {
            'creation_times': [],
            'redirect_times': [],
            'errors': []
        }
    
    def generate_test_url(self):
        """Generate a random test URL"""
        random_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return f"https://example.com/test/{random_path}"
    
    def create_short_url(self):
        """Create a single short URL and measure time"""
        test_url = self.generate_test_url()
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/api/shorten",
                json={"url": test_url},
                timeout=10
            )
            end_time = time.time()
            
            if response.status_code == 201:
                data = response.json()
                self.created_urls.append(data['short_code'])
                self.results['creation_times'].append(end_time - start_time)
                return True, end_time - start_time
            else:
                self.results['errors'].append(f"Creation failed: HTTP {response.status_code}")
                return False, end_time - start_time
                
        except Exception as e:
            end_time = time.time()
            self.results['errors'].append(f"Creation error: {str(e)}")
            return False, end_time - start_time
    
    def test_redirect(self, short_code):
        """Test URL redirection and measure time"""
        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/{short_code}",
                allow_redirects=False,
                timeout=10
            )
            end_time = time.time()
            
            if response.status_code == 302:
                self.results['redirect_times'].append(end_time - start_time)
                return True, end_time - start_time
            else:
                self.results['errors'].append(f"Redirect failed: HTTP {response.status_code}")
                return False, end_time - start_time
                
        except Exception as e:
            end_time = time.time()
            self.results['errors'].append(f"Redirect error: {str(e)}")
            return False, end_time - start_time
    
    def load_test_creation(self, num_requests=50, num_threads=5):
        """Load test URL creation"""
        print(f"🔧 Load Testing URL Creation: {num_requests} requests with {num_threads} threads")
        
        successful = 0
        failed = 0
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(self.create_short_url) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                success, duration = future.result()
                if success:
                    successful += 1
                else:
                    failed += 1
        
        total_time = time.time() - start_time
        
        print(f"✅ Creation Results:")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Successful: {successful}/{num_requests} ({successful/num_requests*100:.1f}%)")
        print(f"   Failed: {failed}")
        print(f"   Requests/Second: {successful/total_time:.1f}")
        
        if self.results['creation_times']:
            avg_time = sum(self.results['creation_times']) / len(self.results['creation_times'])
            print(f"   Average Response Time: {avg_time*1000:.1f}ms")
        
        return successful / total_time
    
    def load_test_redirection(self, num_requests=200, num_threads=20):
        """Load test URL redirection"""
        if not self.created_urls:
            print("❌ No URLs available for redirection test. Run creation test first.")
            return 0
        
        print(f"🔄 Load Testing URL Redirection: {num_requests} requests with {num_threads} threads")
        
        # Create list of short codes to test (cycling through available ones)
        test_codes = [self.created_urls[i % len(self.created_urls)] for i in range(num_requests)]
        
        successful = 0
        failed = 0
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(self.test_redirect, code) for code in test_codes]
            
            for future in as_completed(futures):
                success, duration = future.result()
                if success:
                    successful += 1
                else:
                    failed += 1
        
        total_time = time.time() - start_time
        
        print(f"✅ Redirection Results:")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Successful: {successful}/{num_requests} ({successful/num_requests*100:.1f}%)")
        print(f"   Failed: {failed}")
        print(f"   Requests/Second: {successful/total_time:.1f}")
        
        if self.results['redirect_times']:
            avg_time = sum(self.results['redirect_times']) / len(self.results['redirect_times'])
            print(f"   Average Response Time: {avg_time*1000:.1f}ms")
        
        return successful / total_time
    
    def quick_health_check(self):
        """Quick health check"""
        print("🏥 Health Check...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is healthy")
                return True
            else:
                print(f"❌ Health check failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def run_quick_test(self):
        """Run a quick performance test"""
        print("🚀 Quick Performance Test")
        print("=" * 50)
        
        # Health check
        if not self.quick_health_check():
            return
        
        print()
        
        # Test URL creation
        creation_rps = self.load_test_creation(num_requests=25, num_threads=3)
        
        print()
        
        # Test URL redirection
        redirect_rps = self.load_test_redirection(num_requests=100, num_threads=10)
        
        print()
        print("=" * 50)
        print("📊 Performance Summary:")
        print(f"   URL Creation: {creation_rps:.1f} requests/second")
        print(f"   URL Redirection: {redirect_rps:.1f} requests/second")
        
        # Compare with targets
        print("\n🎯 Target Performance:")
        print("   URL Creation: >40 req/s")
        print("   URL Redirection: >8000 req/s")
        
        print("\n📈 Performance Status:")
        creation_status = "✅ PASS" if creation_rps >= 40 else "⚠️ BELOW TARGET"
        redirect_status = "✅ PASS" if redirect_rps >= 8000 else "⚠️ BELOW TARGET"
        
        print(f"   Creation: {creation_status}")
        print(f"   Redirection: {redirect_status}")
        
        if self.results['errors']:
            print(f"\n⚠️ Errors encountered: {len(self.results['errors'])}")
            for error in self.results['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(self.results['errors']) > 5:
                print(f"   ... and {len(self.results['errors']) - 5} more")
    
    def run_stress_test(self):
        """Run a more intensive stress test"""
        print("💪 Stress Test")
        print("=" * 50)
        
        if not self.quick_health_check():
            return
        
        print()
        
        # Stress test URL creation
        print("🔧 Stress Testing URL Creation...")
        creation_rps = self.load_test_creation(num_requests=100, num_threads=10)
        
        print()
        
        # Stress test URL redirection
        print("🔄 Stress Testing URL Redirection...")
        redirect_rps = self.load_test_redirection(num_requests=1000, num_threads=50)
        
        print()
        print("=" * 50)
        print("💪 Stress Test Summary:")
        print(f"   URL Creation: {creation_rps:.1f} requests/second")
        print(f"   URL Redirection: {redirect_rps:.1f} requests/second")
        
        if self.results['errors']:
            error_rate = len(self.results['errors']) / (len(self.results['creation_times']) + len(self.results['redirect_times'])) * 100
            print(f"   Error Rate: {error_rate:.2f}%")

def main():
    """Main function with simple CLI"""
    print("URL Shortener - Simple Load Tester")
    print("=" * 40)
    
    base_url = input("Enter base URL (default: http://localhost:5000): ").strip()
    if not base_url:
        base_url = "http://localhost:5000"
    
    print("\nChoose test type:")
    print("1. Quick Test (light load)")
    print("2. Stress Test (heavy load)")
    print("3. Custom Test")
    
    choice = input("Enter choice (1-3): ").strip()
    
    tester = SimpleLoadTester(base_url)
    
    if choice == "1":
        tester.run_quick_test()
    elif choice == "2":
        tester.run_stress_test()
    elif choice == "3":
        create_requests = int(input("Number of creation requests (default: 50): ") or 50)
        create_threads = int(input("Creation threads (default: 5): ") or 5)
        redirect_requests = int(input("Number of redirection requests (default: 200): ") or 200)
        redirect_threads = int(input("Redirection threads (default: 20): ") or 20)
        
        print(f"\n🔧 Custom Test: {create_requests} creates, {redirect_requests} redirects")
        print("=" * 50)
        
        if not tester.quick_health_check():
            return
        
        creation_rps = tester.load_test_creation(create_requests, create_threads)
        redirect_rps = tester.load_test_redirection(redirect_requests, redirect_threads)
        
        print(f"\n📊 Custom Test Results:")
        print(f"   Creation: {creation_rps:.1f} req/s")
        print(f"   Redirection: {redirect_rps:.1f} req/s")
    else:
        print("Invalid choice. Running quick test...")
        tester.run_quick_test()

if __name__ == "__main__":
    main()