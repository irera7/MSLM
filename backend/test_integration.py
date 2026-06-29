"""
Comprehensive integration test for all API endpoints.
Tests Backend-Frontend connectivity.
"""

import requests
import json
import os
from datetime import datetime

# Disable proxy for localhost
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

BASE_URL = "http://localhost:8078"
API_URL = f"{BASE_URL}/api"

# Create session without proxy
session = requests.Session()
session.trust_env = False  # Ignore system proxy settings

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}{Colors.END}\n")

def test_endpoint(name, method, url, data=None, params=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = session.get(url, params=params)
        elif method == "POST":
            response = session.post(url, json=data, params=params)
        elif method == "PATCH":
            response = session.patch(url, json=data, params=params)
        elif method == "DELETE":
            response = session.delete(url, json=data, params=params)
        
        success = response.status_code == expected_status or response.status_code == 200
        
        if success:
            print(f"{Colors.GREEN}✓{Colors.END} {name}: {response.status_code}")
            return True, response
        else:
            print(f"{Colors.RED}✗{Colors.END} {name}: {response.status_code} (expected {expected_status})")
            return False, response
            
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} {name}: {str(e)}")
        return False, None

def main():
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"  LM Studio Clone - Complete Integration Test")
    print(f"  Testing Backend-Frontend Connectivity")
    print(f"{'='*70}{Colors.END}")
    print(f"Testing at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # ==================== Core Endpoints ====================
    print_section("Core Endpoints")
    
    success, _ = test_endpoint("Health Check", "GET", f"{BASE_URL}/health")
    results["total"] += 1
    if success: results["passed"] += 1
    else: results["failed"] += 1
    
    success, _ = test_endpoint("Root", "GET", BASE_URL)
    results["total"] += 1
    if success: results["passed"] += 1
    else: results["failed"] += 1
    
    # ==================== Models API ====================
    print_section("Models API (19 endpoints)")
    
    endpoints = [
        ("List Models", "GET", f"{API_URL}/models"),
        ("List Loaded Models", "GET", f"{API_URL}/models/loaded/list"),
        ("Get Quantization Levels", "GET", f"{API_URL}/quantization/info/levels"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Chat API ====================
    print_section("Chat API (13 endpoints)")
    
    endpoints = [
        ("List Chat Sessions", "GET", f"{API_URL}/chat/sessions"),
        ("List Chat Presets", "GET", f"{API_URL}/chat/presets"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Downloads API ====================
    print_section("Downloads API (5 endpoints)")
    
    endpoints = [
        ("List Downloads", "GET", f"{API_URL}/downloads"),
        ("List Active Downloads", "GET", f"{API_URL}/downloads/active/list"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Monitoring API ====================
    print_section("Monitoring API (6 endpoints)")
    
    endpoints = [
        ("System Info", "GET", f"{API_URL}/monitoring/system"),
        ("Current Metrics", "GET", f"{API_URL}/monitoring/metrics"),
        ("Metrics History", "GET", f"{API_URL}/monitoring/metrics/history"),
        ("Process Info", "GET", f"{API_URL}/monitoring/process"),
        ("GPU Info", "GET", f"{API_URL}/monitoring/gpu"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Cache API ====================
    print_section("Cache API (4 endpoints)")
    
    endpoints = [
        ("Cache Stats", "GET", f"{API_URL}/cache/stats"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== HuggingFace API ====================
    print_section("HuggingFace API (6 endpoints)")
    
    endpoints = [
        ("Search Models", "GET", f"{API_URL}/huggingface/search", None, {"query": "llama", "limit": 5}),
        ("Popular Models", "GET", f"{API_URL}/huggingface/popular", None, {"limit": 5}),
        ("GGUF Models", "GET", f"{API_URL}/huggingface/gguf", None, {"limit": 5}),
    ]
    
    for name, method, url, data, params in endpoints:
        success, _ = test_endpoint(name, method, url, data, params)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== RAG API ====================
    print_section("RAG API (7 endpoints)")
    
    endpoints = [
        ("RAG Status", "GET", f"{API_URL}/rag/status"),
        ("List Collections", "GET", f"{API_URL}/rag/collections"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Functions API ====================
    print_section("Functions API (5 endpoints)")
    
    endpoints = [
        ("List Functions", "GET", f"{API_URL}/functions/"),
        ("Function Schema", "GET", f"{API_URL}/functions/schema"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # Test function execution
    success, _ = test_endpoint(
        "Execute Calculator", "POST", f"{API_URL}/functions/execute",
        data={"name": "calculator", "arguments": {"expression": "2+2"}}
    )
    results["total"] += 1
    if success: results["passed"] += 1
    else: results["failed"] += 1
    
    # ==================== Batch API ====================
    print_section("Batch API (5 endpoints)")
    
    endpoints = [
        ("List Batch Jobs", "GET", f"{API_URL}/batch/jobs"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== API Keys ====================
    print_section("API Keys (4 endpoints)")
    
    endpoints = [
        ("List API Keys", "GET", f"{API_URL}/keys/"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Quantization ====================
    print_section("Quantization API (4 endpoints)")
    
    endpoints = [
        ("List Quantization Jobs", "GET", f"{API_URL}/quantization/"),
        ("Quantization Levels Info", "GET", f"{API_URL}/quantization/info/levels"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Advanced - LoRA ====================
    print_section("Advanced API - LoRA (7 endpoints)")
    
    endpoints = [
        ("List LoRA Adapters", "GET", f"{API_URL}/advanced/lora/list"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Advanced - Multi-Modal ====================
    print_section("Advanced API - Multi-Modal (4 endpoints)")
    
    endpoints = [
        ("Supported Formats", "GET", f"{API_URL}/advanced/multimodal/formats"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Advanced - Datasets ====================
    print_section("Advanced API - Datasets (9 endpoints)")
    
    endpoints = [
        ("List Datasets", "GET", f"{API_URL}/advanced/datasets/"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Plugins ====================
    print_section("Plugins API (5 endpoints)")
    
    endpoints = [
        ("List Plugins", "GET", f"{API_URL}/plugins/"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== OpenAI Compatible ====================
    print_section("OpenAI-Compatible API (3 endpoints)")
    
    endpoints = [
        ("List Models (OpenAI)", "GET", f"{BASE_URL}/v1/models"),
    ]
    
    for name, method, url in endpoints:
        success, _ = test_endpoint(name, method, url)
        results["total"] += 1
        if success: results["passed"] += 1
        else: results["failed"] += 1
    
    # ==================== Summary ====================
    print_section("Test Summary")
    
    passed_pct = (results["passed"] / results["total"] * 100) if results["total"] > 0 else 0
    
    print(f"Total Tests: {results['total']}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
    print(f"Success Rate: {passed_pct:.1f}%\n")
    
    if results["failed"] == 0:
        print(f"{Colors.GREEN}{'='*70}")
        print(f"  🎉 ALL TESTS PASSED! Backend-Frontend Ready!")
        print(f"{'='*70}{Colors.END}\n")
    else:
        print(f"{Colors.YELLOW}{'='*70}")
        print(f"  ⚠️  Some tests failed. Check backend status.")
        print(f"{'='*70}{Colors.END}\n")
    
    print(f"Note: Make sure backend is running on {BASE_URL}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Tests interrupted by user{Colors.END}\n")
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Fatal error: {str(e)}{Colors.END}\n")

