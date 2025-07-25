#!/usr/bin/env python3
"""
Debug the file processor to see why it's not finding the attachment
"""

from file_processor import FileProcessor
import email

def debug_file_processor():
    """Debug the file processor step by step"""
    
    eml_path = "/Users/petergits/Downloads/TD SYNNEX ECExpress Price & Availability download.eml"
    
    print("🔍 Debug: File Processor...")
    
    with open(eml_path, 'rb') as f:
        eml_content = f.read()
    
    processor = FileProcessor(customer_number='701601')
    print(f"📊 File processor pattern: {processor.filename_pattern.pattern}")
    
    # Parse the email message manually to see what's happening
    msg = email.message_from_bytes(eml_content)
    
    print("📧 Walking through email parts...")
    for part in msg.walk():
        # Skip non-attachment parts
        if part.get_content_disposition() != 'attachment':
            continue
        
        attachment_filename = part.get_filename()
        if not attachment_filename:
            continue
        
        print(f"📎 Found attachment: {attachment_filename}")
        
        # Test our filename validation
        is_valid = processor._is_valid_td_synnex_filename(attachment_filename)
        print(f"   Valid TD SYNNEX filename: {is_valid}")
        
        if is_valid:
            print("   ✅ This should be processed!")
            
            # Try to get the attachment content
            try:
                attachment_content = part.get_payload(decode=True)
                if attachment_content:
                    print(f"   📊 Attachment size: {len(attachment_content)} bytes")
                    
                    # Test the content processing
                    processed = processor._process_txt_content(attachment_content)
                    print(f"   📊 Processed size: {len(processed)} bytes")
                    
                    # Show first few lines
                    content_str = processed.decode('utf-8')
                    lines = content_str.split('\n')[:5]
                    print(f"   📝 First few lines:")
                    for i, line in enumerate(lines):
                        print(f"      {i+1}: {line[:100]}{'...' if len(line) > 100 else ''}")
                        
                else:
                    print("   ❌ No attachment content found")
            except Exception as e:
                print(f"   ❌ Error getting attachment content: {e}")

if __name__ == "__main__":
    debug_file_processor()