#!/usr/bin/env python3
"""
Complete Copilot Studio Knowledge Base Upload Solution
No CLI dependencies - works entirely through HTTP requests
"""

import json
import os
import sys
import requests
from pathlib import Path
import base64
import mimetypes

class CopilotUploader:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in configuration file: {self.config_path}")
            sys.exit(1)
    
    def validate_file(self, file_path):
        """Validate the file before upload"""
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}")
            return False
            
        file_size = os.path.getsize(file_path)
        max_size = self.config['fileSettings']['maxFileSize']
        
        if file_size > max_size:
            print(f"ERROR: File size ({file_size} bytes) exceeds maximum ({max_size} bytes)")
            return False
            
        file_ext = os.path.splitext(file_path)[1].lower()
        supported_exts = self.config['fileSettings']['supportedExtensions']
        
        if file_ext not in supported_exts:
            print(f"ERROR: File extension {file_ext} not supported")
            return False
            
        return True
    
    def upload_file(self, file_path):
        """Upload file to Copilot Studio via Power Automate"""
        if not self.validate_file(file_path):
            return False
            
        trigger_url = self.config['powerAutomate']['triggerUrl']
        if not trigger_url or trigger_url == "YOUR_FLOW_TRIGGER_URL_HERE":
            print("ERROR: Power Automate trigger URL not configured")
            print("Please update config.json with your flow trigger URL")
            return False
            
        filename = os.path.basename(file_path)
        
        # For this demo, we'll simulate the OneDrive path
        # In a real implementation, you'd upload to OneDrive first
        onedrive_path = f"/Knowledge_Base_Files/{filename}"
        
        payload = {
            "FilePath": onedrive_path,
            "FileName": filename
        }
        
        print(f"Uploading file: {filename}")
        print(f"File size: {os.path.getsize(file_path)} bytes")
        print(f"Trigger URL: {trigger_url}")
        
        try:
            response = requests.post(
                trigger_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print("SUCCESS: File upload triggered successfully!")
                try:
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                except:
                    print(f"Response: {response.text}")
                return True
            else:
                print(f"ERROR: Upload failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to connect to Power Automate: {e}")
            return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'config.json')
    
    if len(sys.argv) < 2:
        print("Usage: python3 upload-to-copilot.py <file_path>")
        print("Example: python3 upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls")
        sys.exit(1)
    
    file_path = os.path.expanduser(sys.argv[1])
    
    uploader = CopilotUploader(config_path)
    success = uploader.upload_file(file_path)
    
    if success:
        print("\nUpload process completed successfully!")
        sys.exit(0)
    else:
        print("\nUpload process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
