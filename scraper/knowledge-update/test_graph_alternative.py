#!/usr/bin/env python3
"""
Test alternative approach using Microsoft Graph API for file management
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_graph_file_approach():
    """Test using Microsoft Graph for file operations instead of direct Dataverse"""
    
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    user_email = os.getenv('OUTLOOK_USER_EMAIL')
    
    print("🧪 Testing Microsoft Graph API approach...")
    print(f"   User: {user_email}")
    print()
    
    # Authenticate with Graph API (this we know works)
    authority_url = f"https://login.microsoftonline.com/{tenant_id}"
    token_url = f"{authority_url}/oauth2/v2.0/token"
    
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        access_token = token_info['access_token']
        print("✅ Microsoft Graph authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Check if user has OneDrive for Business
    print("📁 Testing OneDrive for Business access...")
    try:
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{user_email}/drive",
            headers=headers
        )
        if response.status_code == 200:
            drive_info = response.json()
            print(f"✅ OneDrive access available: {drive_info.get('name', 'Unknown')}")
            print(f"   Drive ID: {drive_info.get('id', 'Unknown')}")
            return True
        else:
            print(f"⚠️  OneDrive not available: {response.status_code}")
    except Exception as e:
        print(f"⚠️  OneDrive test failed: {e}")
    
    # Test 2: Check SharePoint access
    print("📚 Testing SharePoint sites access...")
    try:
        response = requests.get(
            "https://graph.microsoft.com/v1.0/sites",
            headers=headers,
            params={'search': 'hexalinks'}
        )
        if response.status_code == 200:
            sites_info = response.json()
            if sites_info.get('value'):
                print(f"✅ SharePoint sites found: {len(sites_info['value'])}")
                for site in sites_info['value'][:3]:  # Show first 3
                    print(f"   - {site.get('displayName', 'Unknown')}")
                return True
            else:
                print("⚠️  No SharePoint sites found")
        else:
            print(f"⚠️  SharePoint access failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️  SharePoint test failed: {e}")
    
    return False

if __name__ == "__main__":
    test_graph_file_approach()