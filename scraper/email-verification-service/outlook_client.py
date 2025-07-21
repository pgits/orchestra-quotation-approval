#!/usr/bin/env python3
"""
Microsoft Graph API Client for Outlook Email Access
Handles authentication and email retrieval for verification codes
"""

import re
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OutlookClient:
    """Client for accessing Outlook emails via Microsoft Graph API"""
    
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
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 60 second buffer
            
            logger.info("✅ Successfully authenticated with Microsoft Graph API")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to authenticate with Microsoft Graph API: {e}")
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
            return response.json()
            
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
    
    def get_recent_emails(self, count: int = 10) -> List[Dict]:
        """Get recent emails for testing purposes"""
        logger.info(f"📧 Getting {count} recent emails...")
        
        params = {
            '$top': count,
            '$orderby': 'receivedDateTime desc',
            '$select': 'subject,sender,receivedDateTime,bodyPreview'
        }
        
        result = self._make_graph_request(f"users/{self.user_email}/messages", params=params)
        
        emails = []
        for message in result.get('value', []):
            emails.append({
                'subject': message.get('subject', ''),
                'sender': message.get('sender', {}).get('emailAddress', {}).get('address', ''),
                'received_time': message.get('receivedDateTime', ''),
                'body_preview': message.get('bodyPreview', '')
            })
        
        logger.info(f"✅ Retrieved {len(emails)} recent emails")
        return emails
    
    def get_latest_verification_code(self, sender: str = 'do_not_reply@tdsynnex.com', max_age_minutes: int = 10) -> Optional[str]:
        """
        Get the latest verification code from emails from specified sender
        
        Args:
            sender: Email address to filter by
            max_age_minutes: Maximum age of email to consider
            
        Returns:
            Verification code string if found, None otherwise
        """
        logger.info(f"🔍 Searching for verification code from {sender} (max age: {max_age_minutes} minutes)")
        
        # Calculate time filter
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        cutoff_time_str = cutoff_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Search for emails from the specified sender
        params = {
            '$filter': f"from/emailAddress/address eq '{sender}' and receivedDateTime ge {cutoff_time_str}",
            '$orderby': 'receivedDateTime desc',
            '$top': 10,
            '$select': 'subject,body,receivedDateTime,bodyPreview'
        }
        
        try:
            result = self._make_graph_request(f"users/{self.user_email}/messages", params=params)
            
            messages = result.get('value', [])
            logger.info(f"📧 Found {len(messages)} emails from {sender}")
            
            for message in messages:
                verification_code = self._extract_verification_code(message)
                if verification_code:
                    logger.info(f"✅ Found verification code: {verification_code}")
                    return verification_code
            
            logger.warning(f"⚠️ No verification code found in {len(messages)} emails from {sender}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching for verification code: {e}")
            return None
    
    def _extract_verification_code(self, message: Dict) -> Optional[str]:
        """
        Extract verification code from email message
        
        Args:
            message: Email message from Graph API
            
        Returns:
            Verification code string if found, None otherwise
        """
        # Get email content
        subject = message.get('subject', '')
        body_preview = message.get('bodyPreview', '')
        
        # Get full body content if available
        body_content = ''
        if 'body' in message:
            body_content = message['body'].get('content', '')
        
        # Combine all text content
        full_text = f"{subject} {body_preview} {body_content}"
        
        logger.debug(f"📧 Email subject: {subject}")
        logger.debug(f"📧 Email preview: {body_preview[:100]}...")
        
        # Common patterns for verification codes
        patterns = [
            r'verification code[:\s]*(\d{4,8})',  # "verification code: 123456"
            r'verification code is[:\s]*(\d{4,8})',  # "verification code is 123456"
            r'code[:\s]*(\d{4,8})',  # "code: 123456"
            r'security code[:\s]*(\d{4,8})',  # "security code: 123456"
            r'access code[:\s]*(\d{4,8})',  # "access code: 123456"
            r'your code[:\s]*(\d{4,8})',  # "your code: 123456"
            r'(\d{4,8})',  # Any 4-8 digit number (fallback)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                code = match.group(1)
                # Validate code length (typically 4-8 digits)
                if 4 <= len(code) <= 8:
                    logger.info(f"✅ Extracted verification code using pattern: {pattern}")
                    return code
        
        logger.debug(f"⚠️ No verification code found in email: {subject}")
        return None
    
    def get_emails_by_subject(self, subject_contains: str, max_age_minutes: int = 10) -> List[Dict]:
        """
        Get emails containing specific text in subject
        
        Args:
            subject_contains: Text that must be in email subject
            max_age_minutes: Maximum age of email to consider
            
        Returns:
            List of matching email messages
        """
        logger.info(f"🔍 Searching for emails with subject containing: {subject_contains}")
        
        # Calculate time filter
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        cutoff_time_str = cutoff_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        params = {
            '$filter': f"contains(subject, '{subject_contains}') and receivedDateTime ge {cutoff_time_str}",
            '$orderby': 'receivedDateTime desc',
            '$top': 10,
            '$select': 'subject,sender,body,receivedDateTime,bodyPreview'
        }
        
        try:
            result = self._make_graph_request(f"users/{self.user_email}/messages", params=params)
            messages = result.get('value', [])
            
            logger.info(f"📧 Found {len(messages)} emails with subject containing '{subject_contains}'")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error searching emails by subject: {e}")
            return []