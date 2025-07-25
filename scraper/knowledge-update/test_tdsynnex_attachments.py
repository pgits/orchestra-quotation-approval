#!/usr/bin/env python3
"""
Test TD SYNNEX Attachment Reading
Check specific TD SYNNEX emails with attachments
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

def test_tdsynnex_attachments():
    """Test TD SYNNEX attachment reading"""
    
    print("🧪 Testing TD SYNNEX attachment reading...")
    
    try:
        # Get access token
        access_token = get_access_token()
        print("✅ Authentication successful")
        
        user_email = os.getenv('OUTLOOK_USER_EMAIL')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get recent messages to find TD SYNNEX emails
        print("\n🔍 Finding TD SYNNEX emails with attachments...")
        url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"
        params = {
            '$top': 100,
            '$select': 'id,subject,receivedDateTime,hasAttachments,from',
            '$orderby': 'receivedDateTime desc'
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"❌ Failed to get messages: {response.text}")
            return False
            
        all_messages = response.json().get('value', [])
        
        # Find TD SYNNEX emails with attachments
        td_synnex_attachments = []
        for message in all_messages:
            sender = message.get('from', {}).get('emailAddress', {}).get('address', '').lower()
            has_attachments = message.get('hasAttachments', False)
            subject = message.get('subject', '')
            
            if ('tdsynnex.com' in sender or 'do_not_reply@tdsynnex.com' in sender) and has_attachments:
                # Only check price & availability download emails
                if 'price & availability download' in subject.lower():
                    td_synnex_attachments.append(message)
        
        print(f"✅ Found {len(td_synnex_attachments)} TD SYNNEX price emails with attachments")
        
        if not td_synnex_attachments:
            print("⚠️ No TD SYNNEX price emails with attachments found")
            return False
        
        # Check the latest TD SYNNEX price email
        latest_message = td_synnex_attachments[0]
        message_id = latest_message['id']
        subject = latest_message.get('subject', 'No Subject')
        received = latest_message.get('receivedDateTime', '')
        sender = latest_message.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
        
        print(f"\n📧 Latest TD SYNNEX price email:")
        print(f"   From: {sender}")
        print(f"   Subject: {subject}")
        print(f"   Received: {received}")
        
        # Get attachments for this message
        print(f"\n📎 Getting attachments...")
        attachments_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{message_id}/attachments"
        att_params = {'$select': 'id,name,size,contentType'}
        
        att_response = requests.get(attachments_url, headers=headers, params=att_params)
        if att_response.status_code != 200:
            print(f"❌ Failed to get attachments: {att_response.text}")
            return False
        
        attachments = att_response.json().get('value', [])
        print(f"✅ Found {len(attachments)} attachments:")
        
        txt_attachments = []
        for i, att in enumerate(attachments, 1):
            att_name = att.get('name', 'Unknown')
            att_size = att.get('size', 0)
            att_id = att.get('id')
            content_type = att.get('contentType', 'unknown')
            
            print(f"  {i}. {att_name}")
            print(f"     Size: {att_size} bytes")
            print(f"     Type: {content_type}")
            print(f"     ID: {att_id}")
            
            # Check if this is a .txt file matching TD SYNNEX pattern
            if att_name.endswith('.txt'):
                txt_attachments.append(att)
                print(f"     🎯 TXT FILE FOUND!")
                
                # Check if it matches TD SYNNEX pattern (701601-MM-DD-XXXX.txt)
                import re
                pattern = r'^\d{6}-\d{2}-\d{2}-\d{4}\.txt$'
                if re.match(pattern, att_name):
                    print(f"     ✅ MATCHES TD SYNNEX PATTERN!")
            print()
        
        if txt_attachments:
            # Try to download the first .txt attachment
            txt_att = txt_attachments[0]
            att_name = txt_att['name']
            att_id = txt_att['id']
            
            print(f"📥 Attempting to download: {att_name}")
            
            # Download attachment content
            download_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{message_id}/attachments/{att_id}/$value"
            
            download_response = requests.get(download_url, headers=headers)
            
            if download_response.status_code == 200:
                content = download_response.content
                print(f"✅ Successfully downloaded {att_name} ({len(content)} bytes)")
                
                # Try to decode and show first few lines
                try:
                    content_str = content.decode('utf-8')
                    lines = content_str.split('\n')[:5]  # First 5 lines
                    print(f"\n📄 First few lines of {att_name}:")
                    for i, line in enumerate(lines, 1):
                        print(f"  {i}: {line[:100]}")
                        if i == 1 and ';' in line:
                            print(f"     ✅ SEMICOLON-SEPARATED FORMAT DETECTED!")
                except UnicodeDecodeError:
                    print("📄 Content appears to be binary or non-UTF-8 encoded")
                    
                # Save to file for inspection
                output_file = f"hexalinks_{att_name}"
                with open(output_file, 'wb') as f:
                    f.write(content)
                print(f"💾 Saved to: {output_file}")
                
            else:
                print(f"❌ Failed to download attachment: {download_response.status_code}")
                print(f"Response: {download_response.text}")
        else:
            print("⚠️ No .txt attachments found")
        
        print("\n🎉 TD SYNNEX attachment test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tdsynnex_attachments()
    sys.exit(0 if success else 1)