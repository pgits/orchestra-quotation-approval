#!/usr/bin/env python3
"""
Test script to verify Azure AD authentication
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_authentication():
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    
    print(f"Testing authentication with:")
    print(f"Tenant ID: {tenant_id}")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {'*' * len(client_secret) if client_secret else 'None'}")
    
    if not all([tenant_id, client_id, client_secret]):
        print("❌ Missing required credentials")
        return False
    
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    try:
        print("\n🔐 Testing authentication...")
        response = requests.post(token_url, data=token_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token_info = response.json()
            print("✅ Authentication successful!")
            print(f"Access token received (length: {len(token_info.get('access_token', ''))})")
            print(f"Token expires in: {token_info.get('expires_in', 0)} seconds")
            return True
        else:
            print("❌ Authentication failed!")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return False

if __name__ == "__main__":
    test_authentication()