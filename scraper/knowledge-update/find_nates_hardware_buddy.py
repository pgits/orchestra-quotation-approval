#!/usr/bin/env python3
"""
Search for Nate's Hardware Buddy components and knowledge files
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def find_nates_hardware_buddy():
    """Search for Nate's Hardware Buddy bot and components"""
    
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    dataverse_url = os.getenv('DATAVERSE_URL')
    
    print("🔍 Searching for 'Nate's Hardware Buddy v.1'...")
    
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
    
    # Search for bots with various keywords
    print("\n🤖 Searching bots for 'Hardware', 'Nate', or 'Buddy'...")
    
    search_terms = ['hardware', 'nate', 'buddy', 'nathan']
    
    try:
        api_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0/bots"
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            bots_data = response.json()
            bots = bots_data.get('value', [])
            
            for bot in bots:
                name = str(bot.get('name', '')).lower()
                display_name = str(bot.get('displayname', '')).lower()
                
                # Check if any search term is in the name
                for term in search_terms:
                    if term in name or term in display_name:
                        print(f"   🎯 FOUND MATCHING BOT:")
                        print(f"      Name: {bot.get('name', 'Unknown')}")
                        print(f"      Display Name: {bot.get('displayname', 'Unknown')}")
                        print(f"      Bot ID: {bot.get('botid', 'Unknown')}")
                        print(f"      Created: {bot.get('createdon', 'Unknown')}")
                        print(f"      Modified: {bot.get('modifiedon', 'Unknown')}")
                        return bot.get('botid')
                        
            print("   ❌ No matching bots found")
    
    except Exception as e:
        print(f"❌ Error searching bots: {e}")
    
    # Search bot components for knowledge files
    print("\n📚 Searching bot components for knowledge/file components...")
    
    try:
        # Search for components with knowledge-related content types
        knowledge_types = [16, 15, 14, 13, 12]  # Common knowledge component types
        
        for comp_type in knowledge_types:
            search_params = {
                '$filter': f"componenttype eq {comp_type}",
                '$select': 'name,displayname,componenttype,botcomponentid,_parentbotid_value,createdon,content'
            }
            
            api_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0/botcomponents"
            response = requests.get(api_url, headers=headers, params=search_params)
            
            if response.status_code == 200:
                components = response.json().get('value', [])
                if components:
                    print(f"\n   📋 Component Type {comp_type}: {len(components)} found")
                    for comp in components:
                        name = comp.get('name', 'Unknown')
                        display_name = comp.get('displayname', 'Unknown')
                        parent_bot = comp.get('_parentbotid_value', 'None')
                        content = str(comp.get('content', ''))
                        
                        print(f"      • {name}")
                        if display_name and display_name != 'Unknown':
                            print(f"        Display: {display_name}")
                        print(f"        Parent Bot ID: {parent_bot}")
                        if content and len(content) > 10:
                            print(f"        Content: {content[:100]}...")
                        print()
    
    except Exception as e:
        print(f"❌ Error searching components: {e}")
    
    # Look at Copilot Studio URL we saw earlier
    print(f"\n🔗 Based on the Copilot Studio URL you provided:")
    print(f"   Environment: Default-33a7afba-68df-4fb5-84ba-abd928569b69")
    print(f"   Bot ID: e71b63c6-9653-f011-877a-000d3a593ad6")
    print(f"\n🧪 Let's check if this bot ID exists in the bots table...")
    
    try:
        # Try to find the specific bot from the URL
        target_bot_id = "e71b63c6-9653-f011-877a-000d3a593ad6"
        
        search_params = {
            '$filter': f"botid eq '{target_bot_id}'",
            '$select': 'name,displayname,botid,createdon,modifiedon'
        }
        
        api_url = f"{dataverse_url.rstrip('/')}/api/data/v9.0/bots"
        response = requests.get(api_url, headers=headers, params=search_params)
        
        if response.status_code == 200:
            bot_results = response.json().get('value', [])
            if bot_results:
                bot = bot_results[0]
                print(f"   ✅ FOUND THE BOT FROM URL!")
                print(f"      Name: {bot.get('name', 'Unknown')}")
                print(f"      Display Name: {bot.get('displayname', 'Unknown')}")
                print(f"      Bot ID: {bot.get('botid', 'Unknown')}")
                print(f"      Created: {bot.get('createdon', 'Unknown')}")
                return target_bot_id
            else:
                print(f"   ❌ Bot with ID {target_bot_id} not found in this environment")
        else:
            print(f"   ❌ Search failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error searching for specific bot: {e}")
    
    return None

if __name__ == "__main__":
    bot_id = find_nates_hardware_buddy()
    if bot_id:
        print(f"\n🎉 Successfully identified target bot: {bot_id}")
    else:
        print(f"\n⚠️ Could not find 'Nate's Hardware Buddy v.1' bot")
        print(f"   The bot might be in a different environment or have a different name")