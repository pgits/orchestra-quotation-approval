#!/usr/bin/env python3
"""
Test the service with the actual TD SYNNEX .eml file
"""

from file_processor import FileProcessor
import os

def test_eml_file():
    """Test processing the actual TD SYNNEX .eml file"""
    
    eml_path = "/Users/petergits/Downloads/TD SYNNEX ECExpress Price & Availability download.eml"
    
    print("🧪 Testing actual TD SYNNEX .eml file...")
    print(f"📁 File path: {eml_path}")
    
    # Check if file exists
    if not os.path.exists(eml_path):
        print("❌ .eml file not found!")
        return False
    
    # Read the file
    with open(eml_path, 'rb') as f:
        eml_content = f.read()
    
    print(f"📊 File size: {len(eml_content)} bytes")
    
    # Initialize file processor
    processor = FileProcessor(customer_number='701601')
    
    # Process the .eml file
    print("🔄 Processing .eml file...")
    processed_content = processor.process_file(
        filename="TD SYNNEX ECExpress Price & Availability download.eml",
        content=eml_content
    )
    
    if processed_content:
        print(f"✅ Successfully processed! Output size: {len(processed_content)} bytes")
        
        # Validate the processed content
        validation = processor.validate_file_content(processed_content)
        print("📋 Validation results:")
        print(f"   Valid: {validation['valid']}")
        print(f"   Encoding: {validation['encoding']}")
        print(f"   Lines: {validation['line_count']}")
        print(f"   Content type: {validation.get('content_type', 'unknown')}")
        
        if validation['errors']:
            print("⚠️ Validation errors:")
            for error in validation['errors']:
                print(f"   - {error}")
        
        return True
    else:
        print("❌ Failed to process .eml file")
        return False

if __name__ == "__main__":
    test_eml_file()