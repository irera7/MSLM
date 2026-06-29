"""Test the two fixed endpoints"""
import requests
import os

# Disable proxy
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
session = requests.Session()
session.trust_env = False

BASE_URL = "http://localhost:8078"

print("Testing Fixed Endpoints")
print("=" * 60)

# Test 1: OpenAI Models endpoint (was 401)
print("\n1. Testing OpenAI Models endpoint...")
try:
    response = session.get(f"{BASE_URL}/v1/models")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ SUCCESS! Found {len(data.get('data', []))} models")
    else:
        print(f"   ❌ Still failing: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Test 2: RAG Collections endpoint (was 503)
print("\n2. Testing RAG Collections endpoint...")
try:
    response = session.get(f"{BASE_URL}/api/rag/collections")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ SUCCESS! Collections: {data}")
    else:
        print(f"   ❌ Still failing: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Test 3: RAG Status (should still work)
print("\n3. Testing RAG Status endpoint...")
try:
    response = session.get(f"{BASE_URL}/api/rag/status")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ SUCCESS! Available: {data.get('available')}")
        print(f"   Message: {data.get('message')}")
    else:
        print(f"   ❌ Failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("Tests Complete!")

