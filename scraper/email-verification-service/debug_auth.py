#!/usr/bin/env python3
"""
Debug authentication with more detailed information
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def debug_authentication():
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    
    print("🔍 Azure AD Authentication Debug Information")
    print("=" * 60)
    print(f"Tenant ID: {tenant_id}")
    print(f"Client ID: {client_id}")
    print(f"Client Secret Length: {len(client_secret) if client_secret else 0}")
    print(f"Client Secret Format: {'GUID-like' if client_secret and len(client_secret) == 36 and client_secret.count('-') == 4 else 'Non-standard'}")
    
    if not all([tenant_id, client_id, client_secret]):
        print("❌ Missing required credentials")
        return False
    
    # Test different token endpoints
    endpoints = [
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
    ]
    
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    for i, token_url in enumerate(endpoints, 1):
        print(f"\n{i}. Testing endpoint: {token_url}")
        try:
            response = requests.post(token_url, data=token_data)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                token_info = response.json()
                print(f"   ✅ Success! Token received")
                print(f"   Token type: {token_info.get('token_type')}")
                print(f"   Expires in: {token_info.get('expires_in')} seconds")
                return True
            else:
                error_data = response.json()
                print(f"   ❌ Error: {error_data.get('error')}")
                print(f"   Description: {error_data.get('error_description')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("💡 Troubleshooting Tips:")
    print("1. Verify the client secret is the VALUE, not the Secret ID")
    print("2. Check if the secret has expired in Azure Portal")
    print("3. Ensure admin consent has been granted for the app")
    print("4. Verify the app has the correct API permissions:")
    print("   - Mail.Read (Application permission)")
    print("   - User.Read.All (Application permission)")
    print("5. Check if the app is enabled and not disabled")
    
    return False

if __name__ == "__main__":
    debug_authentication()