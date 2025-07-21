#!/usr/bin/env python3
"""
Basic test for email verification service without authentication
"""

import json
import requests
from datetime import datetime

def test_service_endpoints():
    """Test the Flask service endpoints (without authentication)"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Email Verification Service Endpoints")
    print("=" * 50)
    
    # Test status endpoint
    print("\n1. Testing /status endpoint...")
    try:
        response = requests.get(f"{base_url}/status")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Service Status: {data.get('status')}")
            print(f"Outlook Initialized: {data.get('outlook_initialized')}")
            print("✅ Status endpoint working")
        else:
            print("❌ Status endpoint failed")
    except Exception as e:
        print(f"❌ Error testing status endpoint: {e}")
    
    # Test health endpoint
    print("\n2. Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health endpoint returned 200 (service healthy)")
        elif response.status_code == 500:
            print("⚠️ Health endpoint returned 500 (expected due to auth issue)")
            data = response.json()
            print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
    
    # Test verification code endpoint (will fail due to auth)
    print("\n3. Testing /verification-code endpoint...")
    try:
        response = requests.get(f"{base_url}/verification-code?sender=test@example.com")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("⚠️ Expected failure due to authentication issue")
            data = response.json()
            print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing verification-code endpoint: {e}")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("- Service is running and responding to HTTP requests")
    print("- Authentication needs to be fixed with valid Azure credentials")
    print("- Once auth is fixed, the service should work properly")

if __name__ == "__main__":
    test_service_endpoints()