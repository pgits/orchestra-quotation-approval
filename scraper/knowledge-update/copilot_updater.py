#!/usr/bin/env python3
"""
Copilot Studio Knowledge Base Updater
Handles updating knowledge files in Microsoft Copilot Studio via Dataverse API
"""

import os
import json
import base64
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class CopilotUpdater:
    """Client for updating Copilot Studio knowledge base via Dataverse"""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, 
                 dataverse_url: str, agent_name: str = "Nate's Hardware Buddy v.1"):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.dataverse_url = dataverse_url
        self.agent_name = agent_name
        self.access_token = None
        self.token_expires_at = None
        
        # Microsoft authentication endpoints
        self.authority_url = f"https://login.microsoftonline.com/{tenant_id}"
        
        # Copilot Studio / Dataverse specific settings
        self.copilot_components_table = "copilot_components"
        self.max_file_size = 512 * 1024 * 1024  # 512MB limit
        
        logger.info(f"🤖 CopilotUpdater initialized for agent: {agent_name}")
        logger.info(f"🔗 Dataverse URL: {dataverse_url}")
        
        # Authenticate on initialization
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Microsoft using client credentials for Dataverse access"""
        logger.info("🔐 Authenticating with Microsoft for Dataverse access...")
        
        token_url = f"{self.authority_url}/oauth2/v2.0/token"
        
        # Use Dataverse scope instead of Graph
        dataverse_resource = self.dataverse_url.rstrip('/')
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': f"{dataverse_resource}/.default"
        }
        
        try:
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            
            token_info = response.json()
            self.access_token = token_info['access_token']
            
            # Calculate token expiration time
            expires_in = token_info.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("✅ Successfully authenticated with Dataverse")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to authenticate with Dataverse: {e}")
            raise Exception(f"Dataverse authentication failed: {e}")
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            logger.info("🔄 Token expired, refreshing...")
            self._authenticate()
    
    def _make_dataverse_request(self, endpoint: str, method: str = 'GET', 
                               data: Dict = None, params: Dict = None) -> Dict:
        """
        Make a request to Dataverse API
        
        Args:
            endpoint: API endpoint (without base URL)
            method: HTTP method
            data: JSON data for POST/PATCH requests
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        self._ensure_valid_token()
        
        url = f"{self.dataverse_url.rstrip('/')}/api/data/v9.0/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses (like for DELETE)
            if response.status_code == 204 or not response.content:
                return {'success': True}
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Dataverse API request failed: {e}")
            if hasattr(e, 'response') and e.response and e.response.content:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    logger.error(f"Error response: {e.response.text}")
            raise Exception(f"Dataverse API request failed: {e}")
    
    def test_connection(self) -> bool:
        """
        Test connection to Dataverse API
        
        Returns:
            True if connection successful, False otherwise
        """
        logger.info("🧪 Testing Dataverse connection...")
        
        try:
            # Test basic API connectivity with organizations endpoint
            response = self._make_dataverse_request("organizations")
            logger.info("✅ Dataverse connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Dataverse connection test failed: {e}")
            return False
    
    def get_existing_knowledge_files(self) -> List[Dict]:
        """
        Get list of existing knowledge files for the agent
        
        Returns:
            List of existing knowledge file records
        """
        logger.info(f"📋 Getting existing knowledge files for agent: {self.agent_name}")
        
        try:
            # Query for copilot components related to our agent
            # Note: This is a simplified query - actual schema may differ
            params = {
                '$filter': f"contains(name, '{self.agent_name}') or contains(displayname, '{self.agent_name}')",
                '$select': 'name,displayname,createdon,modifiedon,copilot_componentid'
            }
            
            response = self._make_dataverse_request(self.copilot_components_table, params=params)
            
            files = response.get('value', [])
            logger.info(f"✅ Found {len(files)} existing knowledge files")
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Error getting existing knowledge files: {e}")
            return []
    
    def update_knowledge_file(self, filename: str, content: bytes, force_update: bool = False) -> Dict:
        """
        Update or create a knowledge file in Copilot Studio
        
        Args:
            filename: Name of the file
            content: File content as bytes
            force_update: Whether to force update even if file exists
            
        Returns:
            Dictionary with update results
        """
        logger.info(f"🔄 Updating knowledge file: {filename}")
        
        result = {
            'success': False,
            'filename': filename,
            'action': 'none',
            'file_size': len(content),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Validate file size
            if len(content) > self.max_file_size:
                result['error'] = f'File too large: {len(content)} bytes (max: {self.max_file_size})'
                logger.error(result['error'])
                return result
            
            # Check if file already exists
            existing_files = self.get_existing_knowledge_files()
            existing_file = None
            
            for file_record in existing_files:
                if file_record.get('name', '').endswith(filename) or filename in file_record.get('displayname', ''):
                    existing_file = file_record
                    break
            
            if existing_file and not force_update:
                result['action'] = 'skipped'
                result['message'] = 'File already exists and force_update=False'
                result['existing_file_id'] = existing_file.get('copilot_componentid')
                logger.info("⏭️ File already exists, skipping update")
                return result
            
            # Prepare file data for Dataverse
            file_data = self._prepare_file_data(filename, content)
            
            if existing_file:
                # Update existing file
                result['action'] = 'updated'
                component_id = existing_file['copilot_componentid']
                
                logger.info(f"🔄 Updating existing file with ID: {component_id}")
                
                response = self._make_dataverse_request(
                    f"{self.copilot_components_table}({component_id})",
                    method='PATCH',
                    data=file_data
                )
                
                result['file_id'] = component_id
                
            else:
                # Create new file
                result['action'] = 'created'
                
                logger.info("🆕 Creating new knowledge file")
                
                response = self._make_dataverse_request(
                    self.copilot_components_table,
                    method='POST',
                    data=file_data
                )
                
                # Extract the ID from response headers or response data
                if 'copilot_componentid' in response:
                    result['file_id'] = response['copilot_componentid']
            
            result['success'] = True
            result['response'] = response
            
            logger.info(f"✅ Knowledge file {result['action']} successfully: {filename}")
            
            # Optionally trigger agent republishing
            if os.getenv('AUTO_PUBLISH_AGENT', 'false').lower() == 'true':
                self._publish_agent()
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Error updating knowledge file: {e}")
            return result
    
    def _prepare_file_data(self, filename: str, content: bytes) -> Dict:
        """
        Prepare file data for Dataverse API
        
        Args:
            filename: Name of the file
            content: File content as bytes
            
        Returns:
            Dictionary formatted for Dataverse API
        """
        # Encode content as base64
        content_base64 = base64.b64encode(content).decode('utf-8')
        
        # Prepare the data structure for Copilot components
        # Note: Actual schema may vary - this is based on common patterns
        file_data = {
            'name': f"{self.agent_name}_{filename}",
            'displayname': filename,
            'content': content_base64,
            'contenttype': self._get_content_type(filename),
            'contentsize': len(content),
            'description': f"TD SYNNEX price file uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'componenttype': 'knowledge_file',  # May need adjustment based on actual schema
            'statecode': 0,  # Active
            'statuscode': 1   # Active
        }
        
        return file_data
    
    def _get_content_type(self, filename: str) -> str:
        """
        Get MIME content type for file
        
        Args:
            filename: Name of the file
            
        Returns:
            MIME content type string
        """
        if filename.lower().endswith('.txt'):
            return 'text/plain'
        elif filename.lower().endswith('.csv'):
            return 'text/csv'
        elif filename.lower().endswith('.json'):
            return 'application/json'
        elif filename.lower().endswith('.xml'):
            return 'application/xml'
        else:
            return 'application/octet-stream'
    
    def delete_knowledge_file(self, file_id: str) -> Dict:
        """
        Delete a knowledge file from Copilot Studio
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            Dictionary with deletion results
        """
        logger.info(f"🗑️ Deleting knowledge file: {file_id}")
        
        result = {
            'success': False,
            'file_id': file_id,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            response = self._make_dataverse_request(
                f"{self.copilot_components_table}({file_id})",
                method='DELETE'
            )
            
            result['success'] = True
            result['response'] = response
            
            logger.info(f"✅ Knowledge file deleted successfully: {file_id}")
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Error deleting knowledge file: {e}")
            return result
    
    def _publish_agent(self) -> Dict:
        """
        Publish the Copilot Studio agent (if supported by API)
        
        Returns:
            Dictionary with publish results
        """
        logger.info(f"📤 Publishing Copilot Studio agent: {self.agent_name}")
        
        # Note: Agent publishing may require different API endpoints
        # This is a placeholder implementation
        
        result = {
            'success': False,
            'agent_name': self.agent_name,
            'timestamp': datetime.now().isoformat(),
            'message': 'Auto-publish not implemented - please publish manually in Copilot Studio'
        }
        
        logger.info("⚠️ Auto-publish not implemented - please publish agent manually in Copilot Studio")
        
        return result
    
    def get_knowledge_file_info(self, filename: str) -> Optional[Dict]:
        """
        Get information about a specific knowledge file
        
        Args:
            filename: Name of the file to search for
            
        Returns:
            File information dictionary if found, None otherwise
        """
        logger.info(f"🔍 Getting info for knowledge file: {filename}")
        
        existing_files = self.get_existing_knowledge_files()
        
        for file_record in existing_files:
            if file_record.get('name', '').endswith(filename) or filename in file_record.get('displayname', ''):
                logger.info(f"✅ Found knowledge file info: {filename}")
                return file_record
        
        logger.info(f"⚠️ Knowledge file not found: {filename}")
        return None