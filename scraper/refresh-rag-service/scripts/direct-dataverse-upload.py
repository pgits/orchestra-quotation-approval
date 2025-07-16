#!/usr/bin/env python3
"""
Direct Dataverse Upload - No Power Automate Required
Uses Microsoft Graph API and Dataverse API directly
"""

import json
import os
import sys
import requests
import base64
from datetime import datetime
import msal

class DirectDataverseUploader:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        self.access_token = None
        
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Configuration file not found: {self.config_path}")
            sys.exit(1)
    
    def get_access_token(self):
        """Get access token using device code flow"""
        print("🔐 Authentication required...")
        print("You'll need to authenticate with your Microsoft 365 account.")
        print()
        
        # Public client application - no secrets required
        app = msal.PublicClientApplication(
            client_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46",  # Azure CLI client ID
            authority="https://login.microsoftonline.com/common"
        )
        
        # Scopes for Dataverse access
        scopes = ["https://service.powerapps.com//.default"]
        
        # Try to get token from cache first
        accounts = app.get_accounts()
        result = None
        
        if accounts:
            result = app.acquire_token_silent(scopes, account=accounts[0])
        
        if not result:
            # Interactive login required
            flow = app.initiate_device_flow(scopes=scopes)
            if "user_code" not in flow:
                raise ValueError("Failed to create device flow")
            
            print(flow["message"])
            sys.stdout.flush()
            
            result = app.acquire_token_by_device_flow(flow)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            print("✅ Authentication successful!")
            return True
        else:
            print(f"❌ Authentication failed: {result.get('error_description', 'Unknown error')}")
            return False
    
    def find_existing_files(self, agent_id, file_pattern):
        """Find existing knowledge files to replace"""
        if not self.access_token:
            return []
        
        dataverse_url = self.config.get('dataverse', {}).get('url', 'https://service.powerapps.com/api/data/v9.2')
        
        # Query Copilot components table
        query_url = f"{dataverse_url}/msdyn_copilotcomponents"
        query_filter = f"contains(msdyn_name,'{file_pattern}') and _msdyn_parentcopilotcomponentid_value eq {agent_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                query_url,
                headers=headers,
                params={'$filter': query_filter}
            )
            
            if response.status_code == 200:
                return response.json().get('value', [])
            else:
                print(f"Warning: Could not query existing files: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Warning: Error querying existing files: {e}")
            return []
    
    def delete_existing_file(self, file_id):
        """Delete an existing knowledge file"""
        if not self.access_token:
            return False
        
        dataverse_url = self.config.get('dataverse', {}).get('url', 'https://service.powerapps.com/api/data/v9.2')
        delete_url = f"{dataverse_url}/msdyn_copilotcomponents({file_id})"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.delete(delete_url, headers=headers)
            return response.status_code == 204
        except Exception as e:
            print(f"Warning: Could not delete existing file: {e}")
            return False
    
    def upload_knowledge_file(self, file_path, agent_id):
        """Upload file directly to Dataverse"""
        if not self.access_token:
            print("ERROR: Not authenticated")
            return False
        
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}")
            return False
        
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        file_size = len(file_content)
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        print(f"📁 Uploading: {filename}")
        print(f"📏 Size: {file_size} bytes")
        
        # Find and delete existing files
        file_pattern = self.config['fileSettings']['filePattern']
        existing_files = self.find_existing_files(agent_id, file_pattern)
        
        for existing_file in existing_files:
            print(f"🗑️  Deleting existing file: {existing_file.get('msdyn_name', 'Unknown')}")
            self.delete_existing_file(existing_file['msdyn_copilotcomponentid'])
        
        # Create new knowledge component
        dataverse_url = self.config.get('dataverse', {}).get('url', 'https://service.powerapps.com/api/data/v9.2')
        create_url = f"{dataverse_url}/msdyn_copilotcomponents"
        
        payload = {
            "msdyn_name": filename,
            "msdyn_componenttype": 192350002,  # Knowledge source
            "msdyn_parentcopilotcomponentid@odata.bind": f"/msdyn_copilotcomponents({agent_id})",
            "msdyn_knowledgesourcetype": 192350000,  # File
            "msdyn_knowledgesourcesubtype": 192350001,  # Upload
            "msdyn_componentstate": 192350000,  # Active
            "msdyn_filecontent": file_content_b64,
            "msdyn_fileextension": file_ext.lstrip('.'),
            "msdyn_filesize": file_size
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(create_url, headers=headers, json=payload)
            
            if response.status_code == 201:
                result = response.json()
                component_id = result.get('msdyn_copilotcomponentid')
                print(f"✅ File uploaded successfully!")
                print(f"🆔 Component ID: {component_id}")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def run(self, file_path=None):
        """Main execution"""
        if not file_path:
            file_path = os.path.expanduser(self.config['fileSettings']['localFilePath'])
        
        agent_id = self.config['copilotStudio']['agentId']
        if not agent_id or agent_id == "YOUR_AGENT_ID_HERE":
            print("ERROR: Agent ID not configured. Run: python3 scripts/config-wizard.py")
            return False
        
        # Authenticate
        if not self.get_access_token():
            return False
        
        # Upload file
        return self.upload_knowledge_file(file_path, agent_id)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 direct-dataverse-upload.py <file_path>")
        print("Example: python3 direct-dataverse-upload.py ~/Downloads/ec-synnex-701601-0708-0927.xls")
        sys.exit(1)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'config.json')
    
    uploader = DirectDataverseUploader(config_path)
    success = uploader.run(sys.argv[1])
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()