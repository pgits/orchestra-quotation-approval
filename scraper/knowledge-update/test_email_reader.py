#!/usr/bin/env python3
"""
Test Email Reading Functionality
Test the email attachment client to find TD SYNNEX .txt files from do_not_reply@tdsynnex.com
"""

import os
import sys
import logging
from dotenv import load_dotenv
from email_attachment_client import EmailAttachmentClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_email_reader():
    """Test email reading for TD SYNNEX attachments"""
    
    print("🧪 Testing Email Reader for TD SYNNEX attachments...")
    
    try:
        # Check required environment variables
        required_vars = ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'OUTLOOK_USER_EMAIL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            return False
        
        print("✅ Environment variables loaded")
        
        # Initialize email client
        print("\n🔗 Initializing email client...")
        email_client = EmailAttachmentClient(
            tenant_id=os.getenv('AZURE_TENANT_ID'),
            client_id=os.getenv('AZURE_CLIENT_ID'),
            client_secret=os.getenv('AZURE_CLIENT_SECRET'),
            user_email=os.getenv('OUTLOOK_USER_EMAIL')
        )
        
        # Test connection
        print("\n🔌 Testing connection...")
        if email_client.test_connection():
            print("✅ Email connection successful!")
        else:
            print("❌ Email connection failed!")
            return False
        
        # Search for latest TD SYNNEX attachment
        print("\n🔍 Searching for latest TD SYNNEX .txt attachment from do_not_reply@tdsynnex.com...")
        
        # Try different time windows
        time_windows = [60, 180, 360, 720, 1440]  # 1 hour, 3 hours, 6 hours, 12 hours, 24 hours
        
        latest_attachment = None
        
        for max_age_minutes in time_windows:
            print(f"  📅 Checking last {max_age_minutes} minutes...")
            latest_attachment = email_client.get_latest_td_synnex_attachment(max_age_minutes=max_age_minutes)
            
            if latest_attachment:
                print(f"✅ Found TD SYNNEX attachment within last {max_age_minutes} minutes!")
                break
        
        if latest_attachment:
            print("\n📄 Latest TD SYNNEX attachment found:")
            print(f"  📁 Filename: {latest_attachment['filename']}")
            print(f"  📧 From: {latest_attachment['sender']}")
            print(f"  📏 Size: {latest_attachment['size']} bytes")
            print(f"  📅 Received: {latest_attachment['received_time']}")
            print(f"  📧 Subject: {latest_attachment['subject']}")
            
            # Test downloading the attachment
            print("\n📥 Testing attachment download...")
            file_content = email_client.download_attachment(
                latest_attachment['message_id'],
                latest_attachment['attachment_id']
            )
            
            if file_content:
                print(f"✅ Successfully downloaded attachment ({len(file_content)} bytes)")
                
                # Show first few lines of content
                try:
                    content_str = file_content.decode('utf-8')
                    lines = content_str.split('\n')[:5]  # First 5 lines
                    print("\n📄 First few lines of content:")
                    for i, line in enumerate(lines, 1):
                        print(f"  {i}: {line[:100]}...")
                except UnicodeDecodeError:
                    print("📄 Content appears to be binary or non-UTF-8 encoded")
                
            else:
                print("❌ Failed to download attachment content")
                return False
                
        else:
            print("⚠️ No TD SYNNEX .txt attachments found")
            
            # Show attachment history for debugging
            print("\n📊 Getting recent attachment history...")
            history = email_client.get_attachment_history(days_back=7, limit=5)
            
            if history:
                print(f"Found {len(history)} recent attachments:")
                for i, attachment in enumerate(history, 1):
                    print(f"  {i}. {attachment['filename']} from {attachment['sender']} ({attachment['received_time']})")
            else:
                print("No recent attachments found in history")
        
        print("\n🎉 Email reader test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Email reader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email_reader()
    sys.exit(0 if success else 1)