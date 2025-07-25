#!/usr/bin/env python3
"""
Explore Dataverse tables to find Copilot Studio related tables
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def explore_dataverse_tables():
    """Explore what tables exist in the Dataverse environment"""
    
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    dataverse_url = os.getenv('DATAVERSE_URL')
    
    print("🔍 Exploring Dataverse Tables...")
    print(f"   Environment: {dataverse_url}")
    print()
    
    # Authenticate
    authority_url = f"https://login.microsoftonline.com/{tenant_id}"
    token_url = f"{authority_url}/oauth2/v2.0/token"
    
    dataverse_resource = dataverse_url.rstrip('/')
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': f"{dataverse_resource}/.default"
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        access_token = token_info['access_token']
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0'
    }
    
    # Get list of entity sets (tables)
    print("📋 Getting list of entity sets (tables)...")
    
    try:
        api_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0/$metadata"
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            print("✅ Retrieved metadata successfully")
            print(f"📊 Metadata size: {len(response.text)} characters")
            
            # Look for Copilot/Bot related table names in metadata
            metadata = response.text.lower()
            
            copilot_keywords = [
                'copilot', 'bot', 'agent', 'knowledge', 'component', 
                'msdyn_copilot', 'msdyn_bot', 'conversation'
            ]
            
            print("\n🔍 Searching for Copilot/Bot related tables...")
            for keyword in copilot_keywords:
                if keyword in metadata:
                    print(f"   ✅ Found references to: {keyword}")
                else:
                    print(f"   ❌ No references to: {keyword}")
            
        else:
            print(f"❌ Failed to get metadata: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error getting metadata: {e}")
    
    # Try to get entity definitions directly
    print("\n📋 Trying to get entity definitions...")
    
    try:
        api_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0/EntityDefinitions"
        params = {'$select': 'LogicalName,DisplayName', '$top': 100}
        response = requests.get(api_url, headers=headers, params=params)
        
        if response.status_code == 200:
            entities = response.json()
            print(f"✅ Found {len(entities.get('value', []))} entities")
            
            # Look for Copilot related entities
            copilot_entities = []
            for entity in entities.get('value', []):
                logical_name = entity.get('LogicalName', '').lower()
                display_name = entity.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', '').lower()
                
                if any(keyword in logical_name or keyword in display_name for keyword in 
                       ['copilot', 'bot', 'agent', 'knowledge', 'component', 'conversation']):
                    copilot_entities.append(entity)
            
            if copilot_entities:
                print(f"\n🎯 Found {len(copilot_entities)} Copilot/Bot related entities:")
                for entity in copilot_entities:
                    logical_name = entity.get('LogicalName', 'Unknown')
                    display_name = entity.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'Unknown')
                    print(f"   • {logical_name} ({display_name})")
            else:
                print("⚠️ No Copilot/Bot related entities found")
            
        else:
            print(f"❌ Failed to get entities: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting entities: {e}")
    
    # Try some common table names
    print("\n🧪 Testing common Copilot Studio table names...")
    
    common_tables = [
        'copilot_components',
        'msdyn_copilotcomponent',
        'msdyn_copilotknowledge', 
        'msdyn_copilotknowledgeinteraction',
        'msdyn_copilotinteraction',
        'msdyn_copilotinteractions',
        'msdyn_botcomponent',
        'msdyn_bot',
        'msdyn_conversationagent',
        'bots',
        'botcomponents'
    ]
    
    for table_name in common_tables:
        try:
            test_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0/{table_name}"
            response = requests.get(f"{test_url}?$top=1", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {table_name} - EXISTS")
                data = response.json()
                if 'value' in data:
                    print(f"      Records: {len(data['value'])}")
            elif response.status_code == 404:
                print(f"   ❌ {table_name} - Not found")
            else:
                print(f"   ⚠️  {table_name} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {table_name} - Error: {str(e)[:50]}")

if __name__ == "__main__":
    explore_dataverse_tables()