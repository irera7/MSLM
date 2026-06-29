"""Quick test to check backend connectivity"""
import requests
import os

# Disable proxy
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
session = requests.Session()
session.trust_env = False  # Ignore system proxy settings

print("Testing backend connectivity...")
print("-" * 50)

try:
    response = session.get("http://localhost:8078/health", timeout=5)
    print(f"✓ Status Code: {response.status_code}")
    print(f"✓ Response: {response.json()}")
    print("\n✅ Backend is accessible!")
except requests.exceptions.ConnectionError as e:
    print(f"✗ Connection Error: {str(e)}")
    print("\n❌ Cannot connect to backend")
except requests.exceptions.Timeout:
    print("✗ Request timeout")
    print("\n❌ Backend is not responding")
except Exception as e:
    print(f"✗ Error: {str(e)}")
    print("\n❌ Unexpected error")

print("-" * 50)

