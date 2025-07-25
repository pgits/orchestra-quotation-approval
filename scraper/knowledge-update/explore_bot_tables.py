#!/usr/bin/env python3
"""
Explore the bot and botcomponents tables structure
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def explore_bot_tables():
    """Explore the bots and botcomponents tables"""
    
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    dataverse_url = os.getenv('DATAVERSE_URL')
    
    print("🤖 Exploring Bot Tables...")
    
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
    
    # Explore bots table
    print("\n🤖 Exploring 'bots' table...")
    
    try:
        api_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0/bots"
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            bots_data = response.json()
            bots = bots_data.get('value', [])
            
            print(f"✅ Found {len(bots)} bot(s)")
            
            for i, bot in enumerate(bots):
                print(f"\n🤖 Bot {i+1}:")
                # Show key fields
                for key, value in bot.items():
                    if key in ['name', 'displayname', 'botid', 'createdon', 'modifiedon', 'statecode', 'statuscode']:
                        print(f"   {key}: {value}")
                    
                # Look for our Copilot
                name = bot.get('name', '').lower()
                display_name = bot.get('displayname', '').lower()
                if 'hardware' in name or 'hardware' in display_name or 'nate' in name or 'nate' in display_name:
                    print(f"   🎯 This might be 'Nate's Hardware Buddy v.1'!")
                    bot_id = bot.get('botid')
                    print(f"   Bot ID: {bot_id}")
            
        else:
            print(f"❌ Failed to get bots: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error exploring bots: {e}")
    
    # Explore botcomponents table
    print("\n🔧 Exploring 'botcomponents' table...")
    
    try:
        api_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0/botcomponents"
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            components_data = response.json()
            components = components_data.get('value', [])
            
            print(f"✅ Found {len(components)} component(s)")
            
            for i, component in enumerate(components):
                print(f"\n🔧 Component {i+1}:")
                # Show key fields
                for key, value in component.items():
                    if key in ['name', 'displayname', 'componenttype', 'content', 'createdon', 'modifiedon', 'botcomponentid', '_parentbotid_value']:
                        if key == 'content' and value and len(str(value)) > 100:
                            print(f"   {key}: {str(value)[:100]}... (truncated)")
                        else:
                            print(f"   {key}: {value}")
                
                # Check if this is a knowledge component
                component_type = component.get('componenttype')
                name = str(component.get('name', '')).lower()
                if component_type or 'knowledge' in name or 'file' in name:
                    print(f"   🎯 This might be a knowledge component!")
            
        else:
            print(f"❌ Failed to get botcomponents: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error exploring botcomponents: {e}")
    
    # Try to find knowledge-related components
    print("\n📚 Looking for knowledge-related components...")
    
    try:
        # Search for components with knowledge-related keywords
        search_params = {
            '$filter': "contains(name, 'knowledge') or contains(name, 'file') or contains(displayname, 'knowledge')",
            '$select': 'name,displayname,componenttype,botcomponentid,_parentbotid_value,createdon'
        }
        
        api_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0/botcomponents"
        response = requests.get(api_url, headers=headers, params=search_params)
        
        if response.status_code == 200:
            knowledge_components = response.json().get('value', [])
            print(f"✅ Found {len(knowledge_components)} knowledge-related components")
            
            for component in knowledge_components:
                print(f"   • {component.get('name', 'Unknown')}")
                print(f"     Type: {component.get('componenttype', 'Unknown')}")
                print(f"     ID: {component.get('botcomponentid', 'Unknown')}")
                print()
        else:
            print(f"⚠️ Knowledge search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error searching knowledge components: {e}")

if __name__ == "__main__":
    explore_bot_tables()