#!/usr/bin/env python3
"""
Copilot Uploader
Handles uploading files to Copilot Studio knowledge base
"""

import os
import base64
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from azure.identity import ManagedIdentityCredential

logger = logging.getLogger(__name__)

class CopilotUploader:
    def __init__(self, config: dict, credential: ManagedIdentityCredential, telemetry_client=None):
        self.config = config
        self.credential = credential
        self.telemetry_client = telemetry_client
        
        # Copilot Studio configuration
        self.agent_id = config['AGENT_ID']
        self.environment_id = config['ENVIRONMENT_ID']
        self.file_pattern = config['FILE_PATTERN']
        
        # Power Platform API configuration
        self.power_platform_base_url = "https://service.powerapps.com/api/data/v9.2"
        self.copilot_components_endpoint = f"{self.power_platform_base_url}/msdyn_copilotcomponents"
        
        logger.info(f"Copilot Uploader initialized for agent: {self.agent_id}")
    
    def get_access_token(self) -> str:
        """Get access token for Power Platform API"""
        try:
            token = self.credential.get_token("https://service.powerapps.com/.default")
            return token.token
        except Exception as e:
            logger.error(f"Failed to get Power Platform access token: {e}")
            raise
    
    def find_existing_files(self) -> list:
        """Find existing knowledge files that match our pattern"""
        try:
            logger.info(f"Searching for existing files with pattern: {self.file_pattern}")
            
            access_token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Query for existing components that match our file pattern
            filter_query = f"contains(msdyn_name,'{self.file_pattern}') and _msdyn_parentcopilotcomponentid_value eq {self.agent_id}"
            
            params = {
                "$filter": filter_query,
                "$select": "msdyn_copilotcomponentid,msdyn_name,msdyn_componenttype"
            }
            
            response = requests.get(self.copilot_components_endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            existing_files = data.get('value', [])
            
            logger.info(f"Found {len(existing_files)} existing files to replace")
            
            for file_info in existing_files:
                logger.info(f"Existing file: {file_info.get('msdyn_name')} (ID: {file_info.get('msdyn_copilotcomponentid')})")
            
            return existing_files
            
        except Exception as e:
            logger.error(f"Error finding existing files: {e}", exc_info=True)
            if self.telemetry_client:
                self.telemetry_client.track_exception()
            return []
    
    def delete_existing_file(self, file_id: str, file_name: str) -> bool:
        """Delete an existing knowledge file"""
        try:
            logger.info(f"Deleting existing file: {file_name} (ID: {file_id})")
            
            access_token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            delete_url = f"{self.copilot_components_endpoint}({file_id})"
            
            response = requests.delete(delete_url, headers=headers)
            
            if response.status_code == 204:
                logger.info(f"Successfully deleted existing file: {file_name}")
                return True
            else:
                logger.warning(f"Could not delete existing file {file_name}: status {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Error deleting existing file {file_name}: {e}")
            return False
    
    def upload_file(self, filename: str, file_content: bytes) -> bool:
        """Upload file to Copilot Studio knowledge base"""
        try:
            logger.info(f"Starting upload to Copilot Studio: {filename}")
            
            # Validate file
            if not self.validate_file(filename, file_content):
                return False
            
            # Find and delete existing files
            existing_files = self.find_existing_files()
            for existing_file in existing_files:
                self.delete_existing_file(
                    existing_file['msdyn_copilotcomponentid'],
                    existing_file['msdyn_name']
                )
            
            # Prepare file data
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
            file_size = len(file_content)
            
            # Create new knowledge component
            access_token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            payload = {
                "msdyn_name": filename,
                "msdyn_componenttype": 192350002,  # Knowledge source component type
                "msdyn_parentcopilotcomponentid@odata.bind": f"/msdyn_copilotcomponents({self.agent_id})",
                "msdyn_knowledgesourcetype": 192350000,  # File type
                "msdyn_knowledgesourcesubtype": 192350001,  # Upload subtype
                "msdyn_componentstate": 192350000,  # Active state
                "msdyn_filecontent": file_content_b64,
                "msdyn_fileextension": file_ext,
                "msdyn_filesize": file_size
            }
            
            logger.info(f"Uploading file: {filename} ({file_size} bytes)")
            
            response = requests.post(self.copilot_components_endpoint, headers=headers, json=payload)
            
            if response.status_code == 201:
                result = response.json()
                component_id = result.get('msdyn_copilotcomponentid')
                
                logger.info(f"Successfully uploaded file to Copilot Studio: {filename}")
                logger.info(f"Component ID: {component_id}")
                
                if self.telemetry_client:
                    self.telemetry_client.track_event('FileUploadedToCopilot', {
                        'filename': filename,
                        'file_size': str(file_size),
                        'component_id': component_id,
                        'agent_id': self.agent_id
                    })
                
                # Wait a moment for processing to begin
                import time
                time.sleep(5)
                
                # Check processing status
                self.check_processing_status(component_id, filename)
                
                return True
                
            else:
                logger.error(f"Failed to upload file to Copilot Studio: {filename}")
                logger.error(f"Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
                if self.telemetry_client:
                    self.telemetry_client.track_event('FileUploadFailed', {
                        'filename': filename,
                        'status_code': str(response.status_code),
                        'error': response.text[:500]  # Truncate error message
                    })
                
                return False
                
        except Exception as e:
            logger.error(f"Error uploading file {filename}: {e}", exc_info=True)
            if self.telemetry_client:
                self.telemetry_client.track_exception()
            return False
    
    def validate_file(self, filename: str, file_content: bytes) -> bool:
        """Validate file before upload"""
        # Check file pattern
        if not filename.lower().startswith(self.file_pattern.lower()):
            logger.error(f"File {filename} does not match required pattern: {self.file_pattern}")
            return False
        
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        supported_extensions = self.config['SUPPORTED_EXTENSIONS']
        
        if file_ext not in supported_extensions:
            logger.error(f"File {filename} has unsupported extension: {file_ext}")
            return False
        
        # Check file size
        file_size = len(file_content)
        max_size = self.config['MAX_FILE_SIZE']
        
        if file_size > max_size:
            logger.error(f"File {filename} exceeds maximum size: {file_size} > {max_size}")
            return False
        
        if file_size == 0:
            logger.error(f"File {filename} is empty")
            return False
        
        logger.info(f"File validation passed: {filename} ({file_size} bytes)")
        return True
    
    def check_processing_status(self, component_id: str, filename: str):
        """Check the processing status of uploaded file"""
        try:
            logger.info(f"Checking processing status for: {filename}")
            
            access_token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            status_url = f"{self.copilot_components_endpoint}({component_id})"
            params = {
                "$select": "msdyn_copilotcomponentid,msdyn_name,msdyn_componentstate,msdyn_processingstate"
            }
            
            response = requests.get(status_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                component_state = data.get('msdyn_componentstate')
                processing_state = data.get('msdyn_processingstate')
                
                logger.info(f"Processing status for {filename}:")
                logger.info(f"  Component State: {component_state}")
                logger.info(f"  Processing State: {processing_state}")
                
                if self.telemetry_client:
                    self.telemetry_client.track_event('ProcessingStatusChecked', {
                        'filename': filename,
                        'component_id': component_id,
                        'component_state': str(component_state),
                        'processing_state': str(processing_state)
                    })
                
            else:
                logger.warning(f"Could not check processing status for {filename}: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Error checking processing status for {filename}: {e}")
    
    def get_agent_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the target Copilot Studio agent"""
        try:
            logger.info(f"Getting agent information for: {self.agent_id}")
            
            access_token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            agent_url = f"{self.copilot_components_endpoint}({self.agent_id})"
            params = {
                "$select": "msdyn_copilotcomponentid,msdyn_name,msdyn_componentstate"
            }
            
            response = requests.get(agent_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Agent info: {data.get('msdyn_name')} (State: {data.get('msdyn_componentstate')})")
                return data
            else:
                logger.warning(f"Could not get agent info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Error getting agent info: {e}")
            return None