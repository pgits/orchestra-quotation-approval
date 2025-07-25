#!/usr/bin/env python3
"""
Quick test script to validate Dataverse URL and authentication
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_dataverse_connection():
    """Test connection to Dataverse"""
    
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    dataverse_url = os.getenv('DATAVERSE_URL')
    
    print(f"🔧 Testing Dataverse connection...")
    print(f"   Tenant ID: {tenant_id}")
    print(f"   Client ID: {client_id}")
    print(f"   Dataverse URL: {dataverse_url}")
    print()
    
    # Step 1: Authenticate with Azure AD
    print("🔐 Step 1: Testing Azure AD authentication...")
    
    authority_url = f"https://login.microsoftonline.com/{tenant_id}"
    token_url = f"{authority_url}/oauth2/v2.0/token"
    
    # Use Dataverse scope
    dataverse_resource = dataverse_url.rstrip('/')
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': f"{dataverse_resource}/.default"
    }
    
    try:
        response = requests.post(token_url, data=token_data, timeout=30)
        response.raise_for_status()
        
        token_info = response.json()
        access_token = token_info['access_token']
        print("✅ Azure AD authentication successful")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Azure AD authentication failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return False
    
    # Step 2: Test Dataverse API access
    print("🔗 Step 2: Testing Dataverse API access...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0'
    }
    
    # Test basic API connectivity
    api_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0"
    
    try:
        # Try to get basic organization info
        response = requests.get(f"{api_url}/organizations", headers=headers, timeout=30)
        response.raise_for_status()
        
        org_data = response.json()
        print("✅ Dataverse API connection successful")
        
        if 'value' in org_data and len(org_data['value']) > 0:
            org_info = org_data['value'][0]
            print(f"   Organization: {org_info.get('friendlyname', 'Unknown')}")
            print(f"   Version: {org_info.get('version', 'Unknown')}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Dataverse API connection failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return False
    
    # Step 3: Test Copilot components table access
    print("🤖 Step 3: Testing Copilot components table access...")
    
    try:
        # Try to query copilot components table (might not exist yet)
        response = requests.get(
            f"{api_url}/copilot_components", 
            headers=headers, 
            params={'$top': 1, '$select': 'name'},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Copilot components table accessible")
            components_data = response.json()
            if 'value' in components_data:
                print(f"   Found {len(components_data['value'])} components")
        elif response.status_code == 404:
            print("⚠️  Copilot components table not found (may not exist yet)")
        else:
            print(f"⚠️  Copilot components table access returned status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Copilot components table test failed: {e}")
        print("   This may be normal if the table doesn't exist yet")
    
    print()
    print("✅ Overall connection test completed successfully!")
    print("🎯 Dataverse URL is working: " + dataverse_url)
    
    return True

if __name__ == "__main__":
    test_dataverse_connection()