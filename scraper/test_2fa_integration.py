#!/usr/bin/env python3
"""
Test 2FA Integration
Simple test to verify 2FA handler works correctly
"""

import sys
import time
import threading
import requests
from integrated_verification_handler import IntegratedTwoFactorHandler

def test_2fa_handler():
    """Test the 2FA handler functionality"""
    print("Testing 2FA Handler...")
    
    # Initialize handler
    handler = IntegratedTwoFactorHandler()
    
    # Test 1: Basic initialization
    print("✅ Handler initialized successfully")
    
    # Test 2: Start listening
    handler.verification_listener.start_waiting()
    print("✅ Started listening for verification code")
    
    # Test 3: Check status
    status = handler.verification_listener.get_status()
    print(f"✅ Status: {status}")
    
    # Test 4: Simulate receiving verification code
    success = handler.verification_listener.set_verification_code("123456")
    print(f"✅ Set verification code: {success}")
    
    # Test 5: Get verification code
    code = handler.verification_listener.get_verification_code(timeout_seconds=5)
    print(f"✅ Retrieved verification code: {code}")
    
    print("🎉 All tests passed!")

def test_api_integration():
    """Test the API integration"""
    print("\nTesting API Integration...")
    
    # Start the API server in a separate thread
    from run_verification_api import app
    import threading
    
    def run_api():
        app.run(host='localhost', port=5001, debug=False)
    
    # Start API server in background
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:5001/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        
        # Test start listening
        response = requests.post("http://localhost:5001/2fa-start", timeout=5)
        print(f"✅ Start listening: {response.status_code}")
        
        # Test status
        response = requests.get("http://localhost:5001/2fa-status", timeout=5)
        print(f"✅ Status check: {response.status_code}")
        
        # Test send verification code
        response = requests.post(
            "http://localhost:5001/2fa-challenge",
            json={"verificationId": "123456"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"✅ Send verification code: {response.status_code}")
        
        # Test stop listening
        response = requests.post("http://localhost:5001/2fa-stop", timeout=5)
        print(f"✅ Stop listening: {response.status_code}")
        
        print("🎉 API integration tests passed!")
        
    except Exception as e:
        print(f"❌ API integration test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing 2FA Integration Components")
    print("=" * 50)
    
    # Test the handler directly
    test_2fa_handler()
    
    # Test the API integration
    test_api_integration()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\nTo test with real scraper:")
    print("1. Start the API server: python3 run_verification_api.py")
    print("2. Run the scraper: python3 production_scraper_with_2fa.py")
    print("3. When 2FA challenge appears, send code with:")
    print("   curl -X POST http://localhost:5000/2fa-challenge -H 'Content-Type: application/json' -d '{\"verificationId\": \"YOUR_CODE\"}'")