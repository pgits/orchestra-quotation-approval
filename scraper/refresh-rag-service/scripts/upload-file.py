#!/usr/bin/env python3
"""
Copilot Studio Knowledge Base File Upload Script
Automates the upload of ec-synnex files to the Copilot Studio agent
"""

import os
import json
import requests
import base64
from pathlib import Path
import logging
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CopilotKnowledgeUploader:
    def __init__(self, config_path="config/config.json"):
        """Initialize the uploader with configuration"""
        self.config = self.load_config(config_path)
        self.validate_config()
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {config_path}")
            raise
            
    def validate_config(self):
        """Validate required configuration parameters"""
        required_fields = [
            'powerAutomate.triggerUrl',
            'copilotStudio.agentId',
            'fileSettings.localFilePath'
        ]
        
        for field in required_fields:
            value = self.get_nested_value(self.config, field)
            if not value:
                logger.error(f"Missing required configuration: {field}")
                raise ValueError(f"Missing configuration: {field}")
                
    def get_nested_value(self, obj, key):
        """Get nested dictionary value using dot notation"""
        keys = key.split('.')
        for k in keys:
            obj = obj.get(k, {})
        return obj if obj != {} else None
        
    def upload_to_onedrive(self, file_path):
        """Upload file to OneDrive (placeholder - implement based on your OneDrive setup)"""
        # This is a placeholder - you would implement actual OneDrive upload logic
        # For now, we'll simulate by returning a fake OneDrive path
        filename = os.path.basename(file_path)
        return f"/Knowledge_Base_Files/{filename}", filename
        
    def trigger_power_automate_flow(self, onedrive_path, filename):
        """Trigger the Power Automate flow to update knowledge base"""
        trigger_url = self.config['powerAutomate']['triggerUrl']
        
        payload = {
            "FilePath": onedrive_path,
            "FileName": filename
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Triggering Power Automate flow for file: {filename}")
        
        try:
            response = requests.post(trigger_url, json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Flow triggered successfully. Status: {response.status_code}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger Power Automate flow: {e}")
            raise
            
    def upload_file(self, file_path=None):
        """Main upload process"""
        if not file_path:
            file_path = os.path.expanduser(self.config['fileSettings']['localFilePath'])
            
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Validate file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        supported_extensions = self.config['fileSettings']['supportedExtensions']
        
        if file_ext not in supported_extensions:
            logger.error(f"Unsupported file extension: {file_ext}")
            raise ValueError(f"Unsupported file extension: {file_ext}")
            
        # Check file size
        file_size = os.path.getsize(file_path)
        max_size = self.config['fileSettings']['maxFileSize']
        
        if file_size > max_size:
            logger.error(f"File size ({file_size} bytes) exceeds maximum ({max_size} bytes)")
            raise ValueError(f"File size exceeds maximum allowed size")
            
        logger.info(f"Starting upload process for: {file_path}")
        logger.info(f"File size: {file_size} bytes")
        
        # Upload to OneDrive (or prepare for direct upload)
        onedrive_path, filename = self.upload_to_onedrive(file_path)
        
        # Trigger Power Automate flow
        result = self.trigger_power_automate_flow(onedrive_path, filename)
        
        logger.info("Upload process completed successfully")
        return result
        
    def create_audit_log(self, action, details):
        """Create audit log entry"""
        if not self.config['logging']['enableAuditTrail']:
            return
            
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "agent_id": self.config['copilotStudio']['agentId']
        }
        
        log_file = "audit.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

def main():
    parser = argparse.ArgumentParser(description='Upload file to Copilot Studio knowledge base')
    parser.add_argument('--file', help='Path to file to upload')
    parser.add_argument('--config', default='config/config.json', help='Path to configuration file')
    
    args = parser.parse_args()
    
    try:
        uploader = CopilotKnowledgeUploader(args.config)
        result = uploader.upload_file(args.file)
        
        print(f"Upload completed successfully!")
        print(f"Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())