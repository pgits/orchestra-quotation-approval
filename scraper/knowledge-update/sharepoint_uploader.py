#!/usr/bin/env python3
"""
SharePoint File Uploader for TD SYNNEX Price Files
Handles uploading TD SYNNEX files to SharePoint for Copilot Studio access
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from urllib.parse import quote

logger = logging.getLogger(__name__)

class SharePointUploader:
    """Client for uploading files to SharePoint for Copilot Studio knowledge base"""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, 
                 site_url: str = "https://hexalinks.sharepoint.com/sites/QuotationsTeam",
                 folder_path: str = "Shared Documents/Quotations-Team-Channel"):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.site_url = site_url
        self.folder_path = folder_path
        self.access_token = None
        self.token_expires_at = None
        
        # Microsoft authentication endpoints
        self.authority_url = f"https://login.microsoftonline.com/{tenant_id}"
        
        # SharePoint settings
        self.max_file_size = 250 * 1024 * 1024  # 250MB limit for SharePoint
        
        logger.info(f"📁 SharePointUploader initialized")
        logger.info(f"🔗 Site URL: {site_url}")
        logger.info(f"📂 Folder: {folder_path}")
        
        # Authenticate on initialization
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Microsoft using client credentials for SharePoint access"""
        logger.info("🔐 Authenticating with Microsoft for SharePoint access...")
        
        token_url = f"{self.authority_url}/oauth2/v2.0/token"
        
        # Use SharePoint scope for Graph API access
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        try:
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            
            token_info = response.json()
            self.access_token = token_info['access_token']
            
            # Calculate token expiration time
            expires_in = token_info.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("✅ Successfully authenticated with SharePoint")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to authenticate with SharePoint: {e}")
            raise Exception(f"SharePoint authentication failed: {e}")
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            logger.info("🔄 Token expired, refreshing...")
            self._authenticate()
    
    def _get_site_id(self) -> str:
        """Get the SharePoint site ID from the site URL"""
        self._ensure_valid_token()
        
        # Extract site path from URL
        # https://hexalinks.sharepoint.com/sites/QuotationsTeam -> hexalinks.sharepoint.com:/sites/QuotationsTeam
        site_parts = self.site_url.replace('https://', '').split('/', 1)
        hostname = site_parts[0]
        site_path = f"/{site_parts[1]}" if len(site_parts) > 1 else ""
        
        site_identifier = f"{hostname}:{site_path}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            # Get site information using Graph API
            api_url = f"https://graph.microsoft.com/v1.0/sites/{site_identifier}"
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            
            site_info = response.json()
            site_id = site_info['id']
            
            logger.info(f"✅ Found site ID: {site_id}")
            return site_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get site ID: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to get SharePoint site ID: {e}")
    
    def _get_drive_id(self, site_id: str) -> str:
        """Get the default document library drive ID"""
        self._ensure_valid_token()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            # Try to get default drive for the site
            api_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive"
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                drive_info = response.json()
                drive_id = drive_info['id']
                logger.info(f"✅ Found drive ID: {drive_id}")
                return drive_id
            
            # If default drive fails, try to list drives and pick the first one
            logger.info("🔄 Default drive failed, trying to list all drives...")
            api_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                drives_info = response.json()
                drives = drives_info.get('value', [])
                
                if drives:
                    drive_id = drives[0]['id']
                    logger.info(f"✅ Found drive ID from drives list: {drive_id}")
                    return drive_id
            
            # If all fails, raise the original error
            logger.error(f"❌ Failed to get drive ID: {response.status_code} - {response.text}")
            raise Exception(f"Failed to get SharePoint drive ID: {response.status_code} - {response.text}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get drive ID: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to get SharePoint drive ID: {e}")
    
    def test_connection(self) -> bool:
        """
        Test connection to SharePoint site
        
        Returns:
            True if connection successful, False otherwise
        """
        logger.info("🧪 Testing SharePoint connection...")
        
        try:
            site_id = self._get_site_id()
            drive_id = self._get_drive_id(site_id)
            logger.info("✅ SharePoint connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ SharePoint connection test failed: {e}")
            return False
    
    def _generate_unique_filename(self, base_filename: str, existing_files: List[Dict]) -> str:
        """
        Generate a unique filename by adding incremental numbers if duplicates exist
        
        Args:
            base_filename: Original filename
            existing_files: List of existing files in SharePoint
            
        Returns:
            Unique filename with incremental number if needed
        """
        existing_names = {f['name'] for f in existing_files}
        
        # If no conflict, return original name
        if base_filename not in existing_names:
            return base_filename
        
        # Extract base name and extension
        if '.' in base_filename:
            name_part, ext = base_filename.rsplit('.', 1)
            ext = f'.{ext}'
        else:
            name_part = base_filename
            ext = ''
        
        # Find next available number
        counter = 1
        while True:
            new_filename = f"{name_part}-{counter}{ext}"
            if new_filename not in existing_names:
                logger.info(f"🔄 Filename conflict resolved: {base_filename} → {new_filename}")
                return new_filename
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 1000:
                import time
                timestamp = int(time.time())
                new_filename = f"{name_part}-{timestamp}{ext}"
                logger.warning(f"⚠️ Used timestamp fallback: {new_filename}")
                return new_filename

    def _delete_previous_td_synnex_file(self, current_filename: str, existing_files: List[Dict]) -> Dict:
        """
        Delete the previous TD SYNNEX file (excluding the current one being uploaded)
        
        Args:
            current_filename: Name of the file just uploaded
            existing_files: List of existing TD SYNNEX files
            
        Returns:
            Dictionary with deletion results
        """
        result = {
            'success': False,
            'deleted_files': [],
            'message': 'No previous files to delete'
        }
        
        try:
            # Filter out the current file and sort by modification date (newest first)
            previous_files = [
                f for f in existing_files 
                if f['name'] != current_filename and 
                f['name'].startswith('701601') and 
                f['name'].endswith('.txt')
            ]
            
            if not previous_files:
                result['success'] = True
                result['message'] = 'No previous TD SYNNEX files found to delete'
                return result
            
            # Sort by modification date (newest first)
            previous_files.sort(key=lambda x: x['modified'], reverse=True)
            
            # Delete the most recent previous file (not the brand new one we just uploaded)
            file_to_delete = previous_files[0]
            logger.info(f"🗑️ Deleting previous TD SYNNEX file: {file_to_delete['name']}")
            
            delete_result = self.delete_file(file_to_delete['name'])
            
            if delete_result['success']:
                result['success'] = True
                result['deleted_files'] = [file_to_delete['name']]
                result['message'] = f"Successfully deleted previous file: {file_to_delete['name']}"
                logger.info(f"✅ {result['message']}")
            else:
                result['message'] = f"Failed to delete previous file: {delete_result.get('error', 'Unknown error')}"
                logger.error(f"❌ {result['message']}")
            
            return result
            
        except Exception as e:
            result['message'] = f"Error during previous file deletion: {str(e)}"
            logger.error(f"❌ {result['message']}")
            return result

    def upload_file(self, filename: str, content: bytes, overwrite: bool = True, delete_previous: bool = True) -> Dict:
        """
        Upload a file to SharePoint with smart duplicate handling and automatic cleanup
        
        Args:
            filename: Name of the file
            content: File content as bytes
            overwrite: Whether to overwrite existing files (deprecated, now uses smart naming)
            delete_previous: Whether to delete the previous TD SYNNEX file after successful upload
            
        Returns:
            Dictionary with upload results including deletion info
        """
        logger.info(f"⬆️ Uploading file to SharePoint: {filename}")
        
        result = {
            'success': False,
            'original_filename': filename,
            'final_filename': filename,
            'file_size': len(content),
            'timestamp': datetime.now().isoformat(),
            'sharepoint_url': None,
            'delete_previous_result': None
        }
        
        try:
            # Validate file size
            if len(content) > self.max_file_size:
                result['error'] = f'File too large: {len(content)} bytes (max: {self.max_file_size})'
                logger.error(result['error'])
                return result
            
            # Get existing files first to handle naming conflicts and prepare for cleanup
            existing_files = self.list_existing_files("701601*.txt")
            
            # Generate unique filename if there are conflicts
            unique_filename = self._generate_unique_filename(filename, existing_files)
            result['final_filename'] = unique_filename
            
            # Get site and drive IDs
            site_id = self._get_site_id()
            drive_id = self._get_drive_id(site_id)
            
            self._ensure_valid_token()
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/octet-stream'
            }
            
            # Construct the upload path
            # Remove 'Shared Documents/' prefix if present in folder_path since it's implicit
            folder_clean = self.folder_path.replace('Shared Documents/', '').strip('/')
            if folder_clean:
                upload_path = f"{folder_clean}/{unique_filename}"
            else:
                upload_path = unique_filename
                
            # URL encode the path
            encoded_path = quote(upload_path, safe='/')
            
            # Upload file using Graph API
            api_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{encoded_path}:/content"
            
            logger.info(f"📤 Uploading to path: {upload_path}")
            
            response = requests.put(api_url, headers=headers, data=content)
            response.raise_for_status()
            
            file_info = response.json()
            
            result['success'] = True
            result['file_id'] = file_info.get('id')
            result['sharepoint_url'] = file_info.get('webUrl')
            result['download_url'] = file_info.get('@microsoft.graph.downloadUrl')
            
            logger.info(f"✅ File uploaded successfully: {unique_filename}")
            logger.info(f"🔗 SharePoint URL: {result['sharepoint_url']}")
            
            # Delete previous TD SYNNEX file if requested
            if delete_previous and unique_filename.startswith('701601') and unique_filename.endswith('.txt'):
                logger.info(f"🧹 Initiating cleanup of previous TD SYNNEX files...")
                delete_result = self._delete_previous_td_synnex_file(unique_filename, existing_files)
                result['delete_previous_result'] = delete_result
                
                if delete_result['success']:
                    logger.info(f"✅ Cleanup completed: {delete_result['message']}")
                else:
                    logger.warning(f"⚠️ Cleanup issue: {delete_result['message']}")
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Error uploading file: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return result
    
    def list_existing_files(self, pattern: str = "701601*.txt") -> List[Dict]:
        """
        List existing TD SYNNEX files in SharePoint
        
        Args:
            pattern: File pattern to search for
            
        Returns:
            List of existing file information
        """
        logger.info(f"📋 Listing existing files with pattern: {pattern}")
        
        try:
            site_id = self._get_site_id()
            drive_id = self._get_drive_id(site_id)
            
            self._ensure_valid_token()
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            
            # Get folder contents
            folder_clean = self.folder_path.replace('Shared Documents/', '').strip('/')
            if folder_clean:
                encoded_path = quote(folder_clean, safe='/')
                api_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{encoded_path}:/children"
            else:
                api_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
            
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            
            folder_contents = response.json()
            files = []
            
            for item in folder_contents.get('value', []):
                if item.get('file') and item.get('name', '').startswith('701601') and item.get('name', '').endswith('.txt'):
                    files.append({
                        'name': item['name'],
                        'id': item['id'],
                        'size': item['size'],
                        'created': item['createdDateTime'],
                        'modified': item['lastModifiedDateTime'],
                        'url': item['webUrl'],
                        'download_url': item.get('@microsoft.graph.downloadUrl')
                    })
            
            logger.info(f"✅ Found {len(files)} TD SYNNEX files")
            return files
            
        except Exception as e:
            logger.error(f"❌ Error listing files: {e}")
            return []
    
    def delete_file(self, filename: str) -> Dict:
        """
        Delete a file from SharePoint
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            Dictionary with deletion results
        """
        logger.info(f"🗑️ Deleting file from SharePoint: {filename}")
        
        result = {
            'success': False,
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            site_id = self._get_site_id()
            drive_id = self._get_drive_id(site_id)
            
            self._ensure_valid_token()
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            
            # Construct the file path
            folder_clean = self.folder_path.replace('Shared Documents/', '').strip('/')
            if folder_clean:
                file_path = f"{folder_clean}/{filename}"
            else:
                file_path = filename
                
            encoded_path = quote(file_path, safe='/')
            
            # Delete file using Graph API
            api_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{encoded_path}"
            
            response = requests.delete(api_url, headers=headers)
            response.raise_for_status()
            
            result['success'] = True
            logger.info(f"✅ File deleted successfully: {filename}")
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Error deleting file: {e}")
            return result
    
    def cleanup_old_files(self, keep_latest: int = 5) -> Dict:
        """
        Clean up old TD SYNNEX files, keeping only the most recent ones
        
        Args:
            keep_latest: Number of latest files to keep
            
        Returns:
            Dictionary with cleanup results
        """
        logger.info(f"🧹 Cleaning up old files, keeping latest {keep_latest}")
        
        result = {
            'success': False,
            'files_deleted': [],
            'files_kept': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            existing_files = self.list_existing_files()
            
            if len(existing_files) <= keep_latest:
                result['success'] = True
                result['files_kept'] = [f['name'] for f in existing_files]
                result['message'] = f"No cleanup needed. {len(existing_files)} files total."
                logger.info(result['message'])
                return result
            
            # Sort files by modification date (newest first)
            sorted_files = sorted(existing_files, 
                                key=lambda x: x['modified'], 
                                reverse=True)
            
            files_to_keep = sorted_files[:keep_latest]
            files_to_delete = sorted_files[keep_latest:]
            
            # Delete old files
            for file_info in files_to_delete:
                delete_result = self.delete_file(file_info['name'])
                if delete_result['success']:
                    result['files_deleted'].append(file_info['name'])
                else:
                    logger.error(f"Failed to delete {file_info['name']}: {delete_result.get('error')}")
            
            result['files_kept'] = [f['name'] for f in files_to_keep]
            result['success'] = True
            
            logger.info(f"✅ Cleanup completed. Deleted {len(result['files_deleted'])} files, kept {len(result['files_kept'])}")
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Error during cleanup: {e}")
            return result