#!/usr/bin/env python3
"""
Debug the .eml file processing to see what's happening
"""

import email
import re

def debug_eml():
    """Debug the .eml file processing"""
    
    eml_path = "/Users/petergits/Downloads/TD SYNNEX ECExpress Price & Availability download.eml"
    
    print("🔍 Debug: Parsing .eml file...")
    
    with open(eml_path, 'rb') as f:
        eml_content = f.read()
    
    # Parse the email message
    msg = email.message_from_bytes(eml_content)
    
    print(f"📧 Email subject: {msg.get('Subject', 'No subject')}")
    print(f"📧 Email from: {msg.get('From', 'Unknown sender')}")
    print(f"📧 Email date: {msg.get('Date', 'Unknown date')}")
    print()
    
    print("📎 Looking for attachments...")
    attachment_count = 0
    
    for part in msg.walk():
        print(f"   Part content type: {part.get_content_type()}")
        print(f"   Part disposition: {part.get_content_disposition()}")
        
        # Check if this is an attachment
        if part.get_content_disposition() == 'attachment':
            attachment_count += 1
            attachment_filename = part.get_filename()
            print(f"   📎 Attachment {attachment_count}: '{attachment_filename}'")
            
            # Test our pattern matching
            if attachment_filename:
                pattern = re.compile(r'(\d{6})-(\d{4})-(\d{4})\.txt')
                match = pattern.match(attachment_filename)
                if match:
                    customer, mmdd, unique = match.groups()
                    print(f"      ✅ Pattern matches!")
                    print(f"      Customer: {customer}")
                    print(f"      MMDD: {mmdd}")
                    print(f"      Unique: {unique}")
                    
                    # Check if it's a .txt file
                    if attachment_filename.lower().endswith('.txt'):
                        print(f"      ✅ Is .txt file")
                        
                        # Check customer number
                        if customer == '701601':
                            print(f"      ✅ Customer number matches")
                        else:
                            print(f"      ❌ Customer number mismatch: {customer}")
                    else:
                        print(f"      ❌ Not a .txt file")
                else:
                    print(f"      ❌ Pattern doesn't match: {attachment_filename}")
        print()

if __name__ == "__main__":
    debug_eml()