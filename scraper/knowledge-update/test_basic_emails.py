#!/usr/bin/env python3
"""
Test Basic Email Reading
Simple test to see what emails we can access via Graph API
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_access_token():
    """Get access token for Microsoft Graph"""
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    response = requests.post(token_url, data=token_data)
    response.raise_for_status()
    
    return response.json()['access_token']

def test_basic_email_access():
    """Test basic email access without complex filters"""
    
    print("🧪 Testing basic email access...")
    
    try:
        # Get access token
        access_token = get_access_token()
        print("✅ Authentication successful")
        
        user_email = os.getenv('OUTLOOK_USER_EMAIL')
        
        # Test basic message listing
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Simple query - just get recent messages
        print("\n📧 Testing basic message listing...")
        url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"
        params = {
            '$top': 10,
            '$select': 'id,subject,receivedDateTime,hasAttachments,from',
            '$orderby': 'receivedDateTime desc'
        }
        
        response = requests.get(url, headers=headers, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            messages = response.json().get('value', [])
            print(f"✅ Found {len(messages)} recent messages")
            
            for i, message in enumerate(messages, 1):
                sender = message.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                subject = message.get('subject', 'No Subject')
                has_attachments = message.get('hasAttachments', False)
                received = message.get('receivedDateTime', '')
                
                print(f"  {i}. From: {sender}")
                print(f"     Subject: {subject[:50]}...")
                print(f"     Attachments: {has_attachments}")
                print(f"     Received: {received}")
                print()
                
            # Check each recent message for attachments manually since filters are complex
            print("\n📎 Checking messages for attachments manually...")
            
            messages_with_attachments = []
            
            for message in messages:
                if message.get('hasAttachments', False):
                    messages_with_attachments.append(message)
            
            print(f"✅ Found {len(messages_with_attachments)} messages with attachments")
            
            if messages_with_attachments:
                for i, message in enumerate(messages_with_attachments, 1):
                    sender = message.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                    subject = message.get('subject', 'No Subject')
                    received = message.get('receivedDateTime', '')
                    
                    print(f"  {i}. From: {sender}")
                    print(f"     Subject: {subject[:50]}...")
                    print(f"     Received: {received}")
                    
                    # Get attachments for this message
                    attachments_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{message['id']}/attachments"
                    att_params = {'$select': 'id,name,size,contentType'}
                    
                    att_response = requests.get(attachments_url, headers=headers, params=att_params)
                    if att_response.status_code == 200:
                        attachments = att_response.json().get('value', [])
                        print(f"     📎 Attachments ({len(attachments)}):")
                        for att in attachments:
                            att_name = att.get('name', 'Unknown')
                            att_size = att.get('size', 0)
                            print(f"        - {att_name} ({att_size} bytes)")
                            
                            # Check if this looks like a TD SYNNEX file
                            if att_name.endswith('.txt') and any(char.isdigit() for char in att_name):
                                print(f"        🎯 POTENTIAL TD SYNNEX FILE: {att_name}")
                    else:
                        print(f"     ❌ Failed to get attachments: {att_response.status_code}")
                    
                    # Check if this is from TD SYNNEX
                    if 'tdsynnex' in sender.lower():
                        print(f"     🎯 TD SYNNEX EMAIL FOUND!")
                    
                    print()
            else:
                print("  No messages with attachments found in recent messages")
                
            # Now search wider for TD SYNNEX emails (more messages)
            print("\n🔍 Searching more messages for TD SYNNEX emails...")
            params_wide = {
                '$top': 50,  # Get more messages
                '$select': 'id,subject,receivedDateTime,hasAttachments,from',
                '$orderby': 'receivedDateTime desc'
            }
            
            response3 = requests.get(url, headers=headers, params=params_wide)
            if response3.status_code == 200:
                all_messages = response3.json().get('value', [])
                print(f"📧 Checking {len(all_messages)} messages for TD SYNNEX senders...")
                
                td_synnex_messages = []
                for message in all_messages:
                    sender = message.get('from', {}).get('emailAddress', {}).get('address', '').lower()
                    if any(domain in sender for domain in ['tdsynnex.com', 'td-synnex.com', 'synnex.com']):
                        td_synnex_messages.append(message)
                
                print(f"🎯 Found {len(td_synnex_messages)} TD SYNNEX messages")
                
                for i, message in enumerate(td_synnex_messages, 1):
                    sender = message.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                    subject = message.get('subject', 'No Subject')
                    received = message.get('receivedDateTime', '')
                    has_attachments = message.get('hasAttachments', False)
                    
                    print(f"  {i}. From: {sender}")
                    print(f"     Subject: {subject}")
                    print(f"     Received: {received}")
                    print(f"     Has Attachments: {has_attachments}")
                    
                    if has_attachments:
                        print(f"     🎯 TD SYNNEX EMAIL WITH ATTACHMENTS!")
                    print()
            else:
                print(f"❌ Failed to get wider message list: {response3.text}")
                
        else:
            print(f"❌ Failed to get messages: {response.text}")
            
        print("\n🎉 Basic email test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_email_access()
    sys.exit(0 if success else 1)