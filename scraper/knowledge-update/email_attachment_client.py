#!/usr/bin/env python3
"""
Email Attachment Client for TD SYNNEX Price Files
Specialized client for finding and downloading TD SYNNEX price file attachments
"""

import re
import json
import email
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

class EmailAttachmentClient:
    """Client for accessing email attachments via Microsoft Graph API"""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, user_email: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_email = user_email
        self.access_token = None
        self.token_expires_at = None
        
        # Microsoft Graph API endpoints
        self.authority_url = f"https://login.microsoftonline.com/{tenant_id}"
        self.graph_url = "https://graph.microsoft.com/v1.0"
        
        # TD SYNNEX specific patterns
        self.td_synnex_senders = [
            'do_not_reply@tdsynnex.com',
            'noreply@tdsynnex.com',
            'notifications@tdsynnex.com'
        ]
        
        # Authentication
        self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Microsoft Graph API using client credentials"""
        logger.info("🔐 Authenticating with Microsoft Graph API...")
        
        token_url = f"{self.authority_url}/oauth2/v2.0/token"
        
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
            
            logger.info("✅ Successfully authenticated with Microsoft Graph API")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to authenticate: {e}")
            raise Exception(f"Authentication failed: {e}")
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            logger.info("🔄 Token expired, refreshing...")
            self._authenticate()
    
    def _make_graph_request(self, endpoint: str, method: str = 'GET', params: Dict = None) -> Dict:
        """Make a request to Microsoft Graph API"""
        self._ensure_valid_token()
        
        url = f"{self.graph_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            else:
                response = requests.request(method, url, headers=headers, json=params)
                
            response.raise_for_status()
            
            # Handle different response types
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' in content_type:
                return response.json()
            else:
                # Return raw content for non-JSON responses (like attachment downloads)
                return response.content
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Graph API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Graph API request failed: {e}")
    
    def test_connection(self):
        """Test connection to Microsoft Graph API"""
        logger.info("🧪 Testing connection to Microsoft Graph API...")
        
        # Test by getting user info
        user_info = self._make_graph_request(f"users/{self.user_email}")
        logger.info(f"✅ Connection test successful. User: {user_info.get('displayName', 'Unknown')}")
        
        return True
    
    def get_latest_td_synnex_attachment(self, max_age_minutes: int = 60) -> Optional[Dict]:
        """
        Get the latest TD SYNNEX price file attachment
        
        Args:
            max_age_minutes: Maximum age of email to consider
            
        Returns:
            Dictionary with attachment info if found, None otherwise
        """
        logger.info(f"🔍 Searching for latest TD SYNNEX price file attachment (max age: {max_age_minutes} minutes)")
        
        # Calculate time filter (use UTC timezone for comparison)
        from datetime import timezone
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        cutoff_time_str = cutoff_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Get all recent emails and filter in code (avoid complex OData filters)
        logger.info("📧 Getting all recent emails...")
        
        params = {
            '$orderby': 'receivedDateTime desc',
            '$top': 50,
            '$select': 'id,subject,receivedDateTime,hasAttachments,sender'
        }
        
        try:
            result = self._make_graph_request(f"users/{self.user_email}/messages", params=params)
            messages = result.get('value', [])
            
            logger.info(f"📧 Found {len(messages)} emails with attachments")
            
            for message in messages:
                # Check if message has attachments
                if not message.get('hasAttachments', False):
                    continue
                    
                # Check if message is from TD SYNNEX
                sender_address = message.get('sender', {}).get('emailAddress', {}).get('address', '').lower()
                if not any(td_sender.lower() in sender_address for td_sender in self.td_synnex_senders):
                    continue
                    
                logger.info(f"📧 Found TD SYNNEX email from {sender_address}")
                
                # Check if message is within time window
                received_time = datetime.fromisoformat(message.get('receivedDateTime', '').replace('Z', '+00:00'))
                if received_time < cutoff_time:
                    logger.info(f"⏭️ Email too old: {received_time}")
                    continue
                    
                attachment_info = self._check_message_for_td_synnex_files(message)
                if attachment_info:
                    logger.info(f"✅ Found TD SYNNEX price file: {attachment_info['filename']}")
                    return attachment_info
                        
        except Exception as e:
            logger.error(f"❌ Error searching emails: {e}")
        
        logger.warning("⚠️ No TD SYNNEX price file attachments found")
        return None
    
    def _check_message_for_td_synnex_files(self, message: Dict) -> Optional[Dict]:
        """
        Check if a message contains TD SYNNEX price file attachments
        
        Args:
            message: Email message from Graph API
            
        Returns:
            Dictionary with attachment info if TD SYNNEX price file found, None otherwise
        """
        message_id = message['id']
        subject = message.get('subject', '')
        received_time = message.get('receivedDateTime', '')
        
        # Skip if subject doesn't look like a price file notification
        if not self._is_price_file_email(subject):
            logger.debug(f"⏭️ Skipping non-price-file email: {subject}")
            return None
        
        try:
            # Get attachments for this message
            attachments_result = self._make_graph_request(
                f"users/{self.user_email}/messages/{message_id}/attachments",
                params={'$select': 'id,name,size,contentType'}
            )
            
            attachments = attachments_result.get('value', [])
            logger.debug(f"📎 Found {len(attachments)} attachments in message: {subject}")
            
            for attachment in attachments:
                if self._is_td_synnex_price_file(attachment['name']):
                    return {
                        'message_id': message_id,
                        'attachment_id': attachment['id'],
                        'filename': attachment['name'],
                        'size': attachment['size'],
                        'content_type': attachment.get('contentType', 'application/octet-stream'),
                        'subject': subject,
                        'received_time': received_time,
                        'sender': message.get('sender', {}).get('emailAddress', {}).get('address', '')
                    }
            
        except Exception as e:
            logger.error(f"❌ Error checking attachments for message {message_id}: {e}")
        
        return None
    
    def _is_price_file_email(self, subject: str) -> bool:
        """
        Check if email subject indicates it contains price file
        
        Args:
            subject: Email subject line
            
        Returns:
            True if subject indicates price file, False otherwise
        """
        subject_lower = subject.lower()
        
        price_indicators = [
            'price',
            'pricing',
            'availability',
            'ecexpress',
            'download',
            'file',
            'attachment',
            'catalog'
        ]
        
        return any(indicator in subject_lower for indicator in price_indicators)
    
    def _is_td_synnex_price_file(self, filename: str) -> bool:
        """
        Check if filename matches TD SYNNEX price file pattern
        
        Args:
            filename: Name of the file
            
        Returns:
            True if filename matches TD SYNNEX price file pattern
        """
        # Pattern: customernum-MMDD-unique.txt (e.g., 701601-0725-1108.txt)
        pattern = r'^\d{6}-\d{4}-\d{4}\.txt$'
        
        if re.match(pattern, filename):
            logger.debug(f"✅ Filename matches TD SYNNEX pattern: {filename}")
            return True
        
        # Also check for .eml files that might contain the .txt files
        if filename.lower().endswith('.eml'):
            # Check if the eml filename suggests it contains price data
            eml_indicators = ['price', 'download', 'ecexpress', 'availability']
            filename_lower = filename.lower()
            if any(indicator in filename_lower for indicator in eml_indicators):
                logger.debug(f"✅ EML file might contain price data: {filename}")
                return True
        
        logger.debug(f"❌ Filename doesn't match TD SYNNEX pattern: {filename}")
        return False
    
    def download_attachment(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """
        Download attachment content
        
        Args:
            message_id: ID of the email message
            attachment_id: ID of the attachment
            
        Returns:
            Attachment content as bytes if successful, None otherwise
        """
        logger.info(f"📥 Downloading attachment {attachment_id} from message {message_id}")
        
        try:
            # Get attachment content
            attachment_data = self._make_graph_request(
                f"users/{self.user_email}/messages/{message_id}/attachments/{attachment_id}/$value"
            )
            
            # The response should be the raw attachment content
            if isinstance(attachment_data, dict):
                # If we get JSON back, it might be base64 encoded
                content = attachment_data.get('contentBytes', '')
                if content:
                    import base64
                    return base64.b64decode(content)
            
            # If we get raw bytes, return them
            if isinstance(attachment_data, bytes):
                logger.info(f"✅ Downloaded attachment ({len(attachment_data)} bytes)")
                return attachment_data
            
            # Try to get attachment via different endpoint
            attachment_info = self._make_graph_request(
                f"users/{self.user_email}/messages/{message_id}/attachments/{attachment_id}"
            )
            
            content_bytes = attachment_info.get('contentBytes', '')
            if content_bytes:
                import base64
                content = base64.b64decode(content_bytes)
                logger.info(f"✅ Downloaded attachment ({len(content)} bytes)")
                return content
            
            logger.error("❌ No content found in attachment response")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error downloading attachment: {e}")
            return None
    
    def get_attachment_history(self, days_back: int = 7, limit: int = 10) -> List[Dict]:
        """
        Get history of TD SYNNEX price file attachments
        
        Args:
            days_back: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of attachment info dictionaries
        """
        logger.info(f"📊 Getting attachment history (last {days_back} days, limit: {limit})")
        
        # Calculate time filter
        cutoff_time = datetime.now() - timedelta(days=days_back)
        
        history = []
        
        # Use the same approach as get_latest_td_synnex_attachment - get all messages then filter
        # This avoids OData $filter issues that cause 400 Bad Request in some environments
        params = {
            '$orderby': 'receivedDateTime desc',
            '$top': limit * 10,  # Get more messages to filter through
            '$select': 'id,subject,receivedDateTime,hasAttachments,sender'
        }
        
        try:
            result = self._make_graph_request(f"users/{self.user_email}/messages", params=params)
            messages = result.get('value', [])
            
            logger.info(f"📧 Found {len(messages)} emails to check")
            
            for message in messages:
                if len(history) >= limit:
                    break
                
                # Check if message has attachments
                if not message.get('hasAttachments', False):
                    continue
                    
                # Check if message is from TD SYNNEX
                sender_address = message.get('sender', {}).get('emailAddress', {}).get('address', '').lower()
                if not any(td_sender.lower() in sender_address for td_sender in self.td_synnex_senders):
                    continue
                    
                # Check if message is within time window
                received_time = datetime.fromisoformat(message.get('receivedDateTime', '').replace('Z', '+00:00'))
                if received_time < cutoff_time:
                    continue
                        
                attachment_info = self._check_message_for_td_synnex_files(message)
                if attachment_info:
                    history.append(attachment_info)
                        
        except Exception as e:
            logger.error(f"❌ Error getting attachment history: {e}")
            return []
        
        # Sort by received time (newest first)
        history.sort(key=lambda x: x['received_time'], reverse=True)
        
        logger.info(f"✅ Found {len(history)} TD SYNNEX price files in history")
        return history[:limit]
    
    def find_attachment_by_filename(self, filename: str, days_back: int = 30) -> Optional[Dict]:
        """
        Find a specific attachment by filename
        
        Args:
            filename: Name of the file to find
            days_back: Number of days to search back
            
        Returns:
            Dictionary with attachment info if found, None otherwise
        """
        logger.info(f"🔍 Searching for attachment: {filename}")
        
        history = self.get_attachment_history(days_back=days_back, limit=100)
        
        for attachment_info in history:
            if attachment_info['filename'] == filename:
                logger.info(f"✅ Found attachment: {filename}")
                return attachment_info
        
        logger.warning(f"⚠️ Attachment not found: {filename}")
        return None