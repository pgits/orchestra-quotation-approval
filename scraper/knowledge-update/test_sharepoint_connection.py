#!/usr/bin/env python3
"""
Test SharePoint connection and basic functionality
"""

import os
import sys
import logging
from dotenv import load_dotenv
from sharepoint_uploader import SharePointUploader

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_sharepoint_connection():
    """Test SharePoint connection and basic operations"""
    
    print("🧪 Testing SharePoint Connection...")
    
    try:
        # Initialize SharePoint uploader
        uploader = SharePointUploader(
            tenant_id=os.getenv('AZURE_TENANT_ID'),
            client_id=os.getenv('AZURE_CLIENT_ID'),
            client_secret=os.getenv('AZURE_CLIENT_SECRET'),
            site_url='https://hexalinks.sharepoint.com/sites/QuotationsTeam',
            folder_path='Shared Documents/Quotations-Team-Channel'
        )
        
        # Test connection
        print("\n🔗 Testing basic connection...")
        if uploader.test_connection():
            print("✅ SharePoint connection successful!")
        else:
            print("❌ SharePoint connection failed!")
            return False
        
        # List existing files
        print("\n📋 Listing existing TD SYNNEX files...")
        existing_files = uploader.list_existing_files()
        print(f"Found {len(existing_files)} existing files:")
        for file_info in existing_files:
            print(f"  📄 {file_info['name']} ({file_info['size']} bytes, modified: {file_info['modified']})")
        
        # Test upload with a small sample file
        print("\n⬆️ Testing file upload...")
        test_filename = "test-701601-0722-1234.txt"
        test_content = b"Sample TD SYNNEX price data for testing\nProduct1;123.45;In Stock\nProduct2;67.89;Low Stock"
        
        upload_result = uploader.upload_file(test_filename, test_content)
        
        if upload_result['success']:
            print(f"✅ Test file uploaded successfully!")
            print(f"   SharePoint URL: {upload_result['sharepoint_url']}")
            
            # Clean up test file
            print("\n🧹 Cleaning up test file...")
            delete_result = uploader.delete_file(test_filename)
            if delete_result['success']:
                print("✅ Test file cleaned up successfully!")
            else:
                print(f"⚠️ Failed to clean up test file: {delete_result.get('error')}")
        else:
            print(f"❌ Test file upload failed: {upload_result.get('error')}")
            return False
        
        print("\n🎉 All SharePoint tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ SharePoint test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sharepoint_connection()
    sys.exit(0 if success else 1)