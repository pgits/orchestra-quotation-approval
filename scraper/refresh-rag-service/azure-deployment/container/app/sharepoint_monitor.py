#!/usr/bin/env python3
"""
SharePoint Monitor
Handles monitoring SharePoint for new ec-synnex files
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import requests
from azure.identity import ManagedIdentityCredential

logger = logging.getLogger(__name__)

class SharePointMonitor:
    def __init__(self, config: dict, credential: ManagedIdentityCredential, telemetry_client=None):
        self.config = config
        self.credential = credential
        self.telemetry_client = telemetry_client
        
        # SharePoint configuration
        self.site_url = config['SHAREPOINT_SITE_URL']
        self.library_name = config['SHAREPOINT_LIBRARY_NAME']
        self.folder_path = config.get('SHAREPOINT_FOLDER_PATH', '')
        self.tenant = config['SHAREPOINT_TENANT']
        self.file_pattern = config['FILE_PATTERN']
        self.supported_extensions = config['SUPPORTED_EXTENSIONS']
        
        # Graph API endpoints
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        
        # Cache for processed files
        self.processed_files_cache = set()
        self.last_check_time = None
        
        logger.info(f"SharePoint Monitor initialized for site: {self.site_url}")
    
    def get_access_token(self) -> str:
        """Get access token for Microsoft Graph API"""
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default")
            return token.token
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise
    
    def get_site_id(self) -> str:
        """Get SharePoint site ID from URL"""
        try:
            access_token = self.get_access_token()
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Extract site path from URL
            site_path = self.site_url.replace(f"https://{self.tenant}.sharepoint.com", "")
            
            # Get site ID using Graph API
            url = f"{self.graph_base_url}/sites/{self.tenant}.sharepoint.com:{site_path}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            site_data = response.json()
            site_id = site_data['id']
            
            logger.info(f"Retrieved site ID: {site_id}")
            return site_id
            
        except Exception as e:
            logger.error(f"Failed to get site ID: {e}")
            raise
    
    def get_library_id(self, site_id: str) -> str:
        """Get document library ID"""
        try:
            access_token = self.get_access_token()
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Get all lists/libraries for the site
            url = f"{self.graph_base_url}/sites/{site_id}/lists"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            lists_data = response.json()
            
            # Find the library by name
            for list_item in lists_data.get('value', []):
                if list_item.get('displayName') == self.library_name:
                    library_id = list_item['id']
                    logger.info(f"Retrieved library ID: {library_id}")
                    return library_id
            
            raise ValueError(f"Library '{self.library_name}' not found")
            
        except Exception as e:
            logger.error(f"Failed to get library ID: {e}")
            raise
    
    def check_for_new_files(self) -> List[Dict[str, Any]]:
        """Check SharePoint for new ec-synnex files"""
        try:
            logger.info("Checking SharePoint for new files...")
            logger.info(f"Configuration: Site URL: {self.site_url}")
            logger.info(f"Configuration: Library: {self.library_name}")
            logger.info(f"Configuration: Folder Path: {self.folder_path}")
            logger.info(f"Configuration: File Pattern: {self.file_pattern}")
            logger.info(f"Configuration: Supported Extensions: {self.supported_extensions}")
            
            site_id = self.get_site_id()
            library_id = self.get_library_id(site_id)
            
            access_token = self.get_access_token()
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # First, let's get ALL files in the folder to see what's there
            if self.folder_path:
                # Get ALL files from specific folder first for debugging
                folder_url = f"{self.graph_base_url}/sites/{site_id}/drives/{library_id}/root:/{self.folder_path}:/children"
                all_files_url = folder_url
                all_files_params = {
                    "$select": "id,name,size,lastModifiedDateTime,@microsoft.graph.downloadUrl"
                }
                
                logger.info(f"Searching in folder: {self.folder_path}")
                logger.info(f"Full URL: {all_files_url}")
                
                # Get all files first to see what's in the folder
                all_files_response = requests.get(all_files_url, headers=headers, params=all_files_params)
                all_files_response.raise_for_status()
                all_files_data = all_files_response.json()
                
                logger.info(f"ALL FILES in folder '{self.folder_path}':")
                for file_item in all_files_data.get('value', []):
                    file_name = file_item.get('name', '')
                    file_size = file_item.get('size', 0)
                    logger.info(f"  - {file_name} ({file_size} bytes)")
                
                # Now get files with our specific pattern
                url = folder_url
                params = {
                    "$filter": f"startswith(name,'{self.file_pattern}') and file ne null",
                    "$select": "id,name,size,lastModifiedDateTime,@microsoft.graph.downloadUrl"
                }
            else:
                # Query for files matching our pattern in the root library
                filter_query = f"startswith(name,'{self.file_pattern}')"
                
                # If we have a last check time, only get files modified since then
                if self.last_check_time:
                    # Convert to ISO format for OData filter
                    last_check_iso = self.last_check_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    filter_query += f" and lastModifiedDateTime gt {last_check_iso}"
                
                url = f"{self.graph_base_url}/sites/{site_id}/lists/{library_id}/items"
                params = {
                    "$filter": filter_query,
                    "$expand": "driveItem",
                    "$select": "id,driveItem"
                }
                logger.info(f"Searching in root library with filter: {filter_query}")
                logger.info(f"Full URL: {url}")
            
            logger.info(f"Request params: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            items_data = response.json()
            new_files = []
            
            # Log all files found for debugging
            all_files = items_data.get('value', [])
            logger.info(f"Total files returned by SharePoint API: {len(all_files)}")
            
            for item in all_files:
                if self.folder_path:
                    # Direct file response from folder
                    file_name = item.get('name', '')
                    file_id = item.get('id', '')
                    file_size = item.get('size', 0)
                    modified_time = item.get('lastModifiedDateTime', '')
                    download_url = item.get('@microsoft.graph.downloadUrl', '')
                else:
                    # DriveItem response from list items
                    drive_item = item.get('driveItem', {})
                    
                    if not drive_item:
                        logger.info(f"Skipping item with no driveItem: {item}")
                        continue
                    
                    file_name = drive_item.get('name', '')
                    file_id = drive_item.get('id', '')
                    file_size = drive_item.get('size', 0)
                    modified_time = drive_item.get('lastModifiedDateTime', '')
                    download_url = drive_item.get('@microsoft.graph.downloadUrl', '')
                
                # Log details about each file found
                logger.info(f"File found: {file_name} (ID: {file_id}, Size: {file_size} bytes)")
                
                # Check if file matches our criteria and provide detailed reasons
                valid_file = self.is_valid_file(file_name, file_size)
                already_processed = file_id in self.processed_files_cache
                
                if not valid_file:
                    logger.info(f"File {file_name} rejected by validation:")
                    self.log_file_rejection_reason(file_name, file_size)
                elif already_processed:
                    logger.info(f"File {file_name} already processed (ID: {file_id})")
                else:
                    file_info = {
                        'id': file_id,
                        'name': file_name,
                        'size': file_size,
                        'modified_time': modified_time,
                        'download_url': download_url,
                        'site_id': site_id,
                        'library_id': library_id
                    }
                    
                    new_files.append(file_info)
                    logger.info(f"✓ New file accepted: {file_name} (ID: {file_id})")
            
            self.last_check_time = datetime.utcnow()
            
            if self.telemetry_client:
                self.telemetry_client.track_metric('NewFilesFound', len(new_files))
            
            logger.info(f"Summary: {len(all_files)} files found, {len(new_files)} new files accepted")
            return new_files
            
        except Exception as e:
            logger.error(f"Error checking for new files: {e}", exc_info=True)
            if self.telemetry_client:
                self.telemetry_client.track_exception()
            return []
    
    def is_valid_file(self, filename: str, file_size: int) -> bool:
        """Check if file meets our criteria"""
        # Check file pattern
        if not filename.lower().startswith(self.file_pattern.lower()):
            return False
        
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.supported_extensions:
            return False
        
        # Check file size
        max_size = self.config['MAX_FILE_SIZE']
        if file_size > max_size:
            logger.warning(f"File {filename} exceeds maximum size ({file_size} > {max_size})")
            return False
        
        return True
    
    def log_file_rejection_reason(self, filename: str, file_size: int):
        """Log detailed reasons why a file was rejected"""
        reasons = []
        
        # Check file pattern
        if not filename.lower().startswith(self.file_pattern.lower()):
            reasons.append(f"File name '{filename}' does not start with pattern '{self.file_pattern}'")
        
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.supported_extensions:
            reasons.append(f"File extension '{file_ext}' not in supported extensions {self.supported_extensions}")
        
        # Check file size
        max_size = self.config['MAX_FILE_SIZE']
        if file_size > max_size:
            reasons.append(f"File size {file_size} exceeds maximum size {max_size}")
        
        for reason in reasons:
            logger.info(f"  - {reason}")
    
    def download_file(self, file_info: Dict[str, Any]) -> Optional[bytes]:
        """Download file content from SharePoint"""
        try:
            logger.info(f"Downloading file: {file_info['name']}")
            
            # Use direct download URL if available
            download_url = file_info.get('download_url')
            
            if not download_url:
                # Fallback: construct download URL using Graph API
                access_token = self.get_access_token()
                headers = {"Authorization": f"Bearer {access_token}"}
                
                file_url = f"{self.graph_base_url}/sites/{file_info['site_id']}/drives/{file_info['library_id']}/items/{file_info['id']}/content"
                
                response = requests.get(file_url, headers=headers)
                response.raise_for_status()
                
                content = response.content
            else:
                # Download using direct URL (no auth needed for download URLs)
                response = requests.get(download_url)
                response.raise_for_status()
                
                content = response.content
            
            logger.info(f"Successfully downloaded {len(content)} bytes for file: {file_info['name']}")
            
            if self.telemetry_client:
                self.telemetry_client.track_metric('FileDownloadSize', len(content))
            
            return content
            
        except Exception as e:
            logger.error(f"Error downloading file {file_info['name']}: {e}", exc_info=True)
            if self.telemetry_client:
                self.telemetry_client.track_exception()
            return None
    
    def move_to_processed(self, file_info: Dict[str, Any]):
        """Move processed file to archive folder"""
        try:
            logger.info(f"Moving file to processed folder: {file_info['name']}")
            
            access_token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Create processed folder if it doesn't exist
            processed_folder_name = "Processed"
            
            # Move file to processed folder
            move_url = f"{self.graph_base_url}/sites/{file_info['site_id']}/drives/{file_info['library_id']}/items/{file_info['id']}"
            
            # Get current file info to construct new path
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            new_name = f"{processed_folder_name}/{timestamp}_{file_info['name']}"
            
            move_data = {
                "parentReference": {
                    "path": f"/drives/{file_info['library_id']}/root:/{processed_folder_name}"
                },
                "name": f"{timestamp}_{file_info['name']}"
            }
            
            response = requests.patch(move_url, headers=headers, json=move_data)
            
            if response.status_code == 200:
                logger.info(f"Successfully moved file to processed folder: {file_info['name']}")
                self.processed_files_cache.add(file_info['id'])
            else:
                logger.warning(f"Could not move file to processed folder (status {response.status_code}): {file_info['name']}")
                # Still mark as processed to avoid reprocessing
                self.processed_files_cache.add(file_info['id'])
            
        except Exception as e:
            logger.warning(f"Error moving file to processed folder: {e}")
            # Mark as processed anyway to avoid infinite reprocessing
            self.processed_files_cache.add(file_info['id'])
    
    def create_processed_folder(self, site_id: str, library_id: str) -> bool:
        """Create processed folder if it doesn't exist"""
        try:
            access_token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            folder_data = {
                "name": "Processed",
                "folder": {},
                "@microsoft.graph.conflictBehavior": "ignore"
            }
            
            url = f"{self.graph_base_url}/sites/{site_id}/drives/{library_id}/root/children"
            
            response = requests.post(url, headers=headers, json=folder_data)
            
            if response.status_code in [201, 409]:  # Created or already exists
                logger.info("Processed folder ensured")
                return True
            else:
                logger.warning(f"Could not create processed folder: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Error creating processed folder: {e}")
            return False