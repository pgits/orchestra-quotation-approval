#!/usr/bin/env python3
"""
Test the complete knowledge base update workflow with the TD SYNNEX data
"""

from file_processor import FileProcessor
from copilot_updater import CopilotUpdater
import os
from dotenv import load_dotenv

load_dotenv()

def test_knowledge_update():
    """Test the complete knowledge base update workflow"""
    
    eml_path = "/Users/petergits/Downloads/TD SYNNEX ECExpress Price & Availability download.eml"
    
    print("🚀 Testing Complete Knowledge Base Update Workflow")
    print("=" * 60)
    
    # Step 1: Process the .eml file
    print("📧 Step 1: Processing TD SYNNEX .eml file...")
    
    with open(eml_path, 'rb') as f:
        eml_content = f.read()
    
    processor = FileProcessor(customer_number='701601')
    processed_content = processor.process_file(
        filename="TD SYNNEX ECExpress Price & Availability download.eml",
        content=eml_content
    )
    
    if not processed_content:
        print("❌ Failed to process .eml file")
        return False
    
    print(f"✅ Successfully processed! Size: {len(processed_content)} bytes")
    
    # Step 2: Initialize Copilot Updater
    print("\n🤖 Step 2: Initializing Copilot Updater...")
    
    try:
        copilot_updater = CopilotUpdater(
            tenant_id=os.getenv('AZURE_TENANT_ID'),
            client_id=os.getenv('AZURE_CLIENT_ID'),
            client_secret=os.getenv('AZURE_CLIENT_SECRET'),
            dataverse_url=os.getenv('DATAVERSE_URL'),
            agent_name=os.getenv('COPILOT_AGENT_NAME', "Nate's Hardware Buddy v.1")
        )
        print("✅ Copilot Updater initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Copilot Updater: {e}")
        return False
    
    # Step 3: Test Dataverse connection
    print("\n🔗 Step 3: Testing Dataverse connection...")
    
    try:
        connection_test = copilot_updater.test_connection()
        if connection_test:
            print("✅ Dataverse connection successful")
        else:
            print("❌ Dataverse connection failed")
            return False
    except Exception as e:
        print(f"❌ Dataverse connection error: {e}")
        return False
    
    # Step 4: Check existing knowledge files
    print("\n📋 Step 4: Checking existing knowledge files...")
    
    try:
        existing_files = copilot_updater.get_existing_knowledge_files()
        print(f"✅ Found {len(existing_files)} existing knowledge files")
        for file_info in existing_files:
            print(f"   - {file_info.get('name', 'Unknown')}")
    except Exception as e:
        print(f"⚠️ Could not retrieve existing files: {e}")
    
    # Step 5: Update knowledge base
    print(f"\n🚀 Step 5: Updating knowledge base...")
    
    filename = "701601-0721-1627.txt"
    
    try:
        update_result = copilot_updater.update_knowledge_file(
            filename=filename,
            content=processed_content,
            force_update=True  # Force update for testing
        )
        
        print(f"📊 Update Results:")
        print(f"   Success: {update_result['success']}")
        print(f"   Action: {update_result['action']}")
        print(f"   File size: {update_result['file_size']} bytes")
        
        if update_result['success']:
            print(f"✅ Knowledge base updated successfully!")
            if 'file_id' in update_result:
                print(f"   File ID: {update_result['file_id']}")
        else:
            print(f"❌ Knowledge base update failed")
            if 'error' in update_result:
                print(f"   Error: {update_result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Knowledge base update error: {e}")
        return False
    
    print(f"\n🎉 Complete workflow test successful!")
    print(f"📈 Summary:")
    print(f"   - Processed .eml file: ✅")
    print(f"   - Extracted .txt attachment: ✅") 
    print(f"   - Connected to Dataverse: ✅")
    print(f"   - Updated knowledge base: ✅")
    agent_name = os.getenv('COPILOT_AGENT_NAME', "Nate's Hardware Buddy v.1")
    print(f"   - Agent: {agent_name}")
    
    return True

if __name__ == "__main__":
    success = test_knowledge_update()
    if success:
        print("\n✅ All tests passed! The knowledge-update service is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the logs above.")