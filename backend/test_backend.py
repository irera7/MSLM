"""
Quick test script to verify backend functionality.
Run this after starting the backend server.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8078"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    print_section("Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_root():
    print_section("Root Endpoint")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_models():
    print_section("Models API")
    
    # List models
    response = requests.get(f"{BASE_URL}/api/models")
    print(f"List Models Status: {response.status_code}")
    models = response.json()
    print(f"Models Count: {len(models)}")
    
    return response.status_code == 200

def test_monitoring():
    print_section("Monitoring API")
    
    # System info
    response = requests.get(f"{BASE_URL}/api/monitoring/system")
    print(f"System Info Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Platform: {data.get('platform')}")
        print(f"CPU Cores: {data.get('cpu_count')}")
        print(f"RAM: {data.get('ram_total_gb'):.2f} GB")
        print(f"GPU Available: {data.get('gpu_available')}")
    
    # Current metrics
    response = requests.get(f"{BASE_URL}/api/monitoring/metrics")
    print(f"\nCurrent Metrics Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"CPU Usage: {data.get('cpu', {}).get('percent'):.1f}%")
        print(f"RAM Usage: {data.get('ram', {}).get('percent'):.1f}%")
    
    return True

def test_functions():
    print_section("Functions API")
    
    # List functions
    response = requests.get(f"{BASE_URL}/api/functions/")
    print(f"List Functions Status: {response.status_code}")
    if response.status_code == 200:
        functions = response.json()
        print(f"Available Functions: {len(functions.get('functions', []))}")
        for func in functions.get('functions', []):
            print(f"  - {func['name']}: {func['description']}")
    
    # Test calculator
    print("\nTesting Calculator Function:")
    response = requests.post(
        f"{BASE_URL}/api/functions/execute",
        json={"name": "calculator", "arguments": {"expression": "2 + 2"}}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Result: {result}")
    
    return True

def test_cache():
    print_section("Cache API")
    
    response = requests.get(f"{BASE_URL}/api/cache/stats")
    print(f"Cache Stats Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"Hits: {stats.get('hits', 0)}")
        print(f"Misses: {stats.get('misses', 0)}")
        print(f"Size: {stats.get('size', 0)}")
        print(f"Max Size: {stats.get('max_size', 0)}")
    
    return True

def test_huggingface():
    print_section("HuggingFace API")
    
    # Search
    response = requests.get(
        f"{BASE_URL}/api/huggingface/search",
        params={"query": "llama", "limit": 5}
    )
    print(f"Search Status: {response.status_code}")
    if response.status_code == 200:
        results = response.json()
        print(f"Found Models: {len(results.get('models', []))}")
    
    return True

def test_rag():
    print_section("RAG API")
    
    # Check status
    response = requests.get(f"{BASE_URL}/api/rag/status")
    print(f"RAG Status: {response.status_code}")
    if response.status_code == 200:
        status = response.json()
        print(f"Available: {status.get('available')}")
        if not status.get('available'):
            print(f"Message: {status.get('message')}")
    
    # List collections
    response = requests.get(f"{BASE_URL}/api/rag/collections")
    print(f"Collections Status: {response.status_code}")
    if response.status_code == 200:
        collections = response.json()
        print(f"Collections Count: {len(collections.get('collections', []))}")
    
    return True

def test_batch():
    print_section("Batch API")
    
    response = requests.get(f"{BASE_URL}/api/batch/jobs")
    print(f"Batch Jobs Status: {response.status_code}")
    if response.status_code == 200:
        jobs = response.json()
        print(f"Jobs Count: {len(jobs.get('jobs', []))}")
    
    return True

def test_api_keys():
    print_section("API Keys API")
    
    response = requests.get(f"{BASE_URL}/api/keys/")
    print(f"List Keys Status: {response.status_code}")
    if response.status_code == 200:
        keys = response.json()
        print(f"Keys Count: {keys.get('count', 0)}")
    
    return True

def test_openai_api():
    print_section("OpenAI-Compatible API")
    
    response = requests.get(f"{BASE_URL}/v1/models")
    print(f"List Models Status: {response.status_code}")
    if response.status_code == 200:
        models = response.json()
        print(f"Models Available: {len(models.get('data', []))}")
    
    return True

def main():
    print("\n" + "🚀 " + "="*55)
    print("    LM Studio Clone - Backend Test Suite")
    print("="*60 + "\n")
    print(f"Testing backend at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("Models API", test_models),
        ("Monitoring API", test_monitoring),
        ("Functions API", test_functions),
        ("Cache API", test_cache),
        ("HuggingFace API", test_huggingface),
        ("RAG API", test_rag),
        ("Batch API", test_batch),
        ("API Keys API", test_api_keys),
        ("OpenAI API", test_openai_api),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {str(e)}")
            results[name] = False
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")

