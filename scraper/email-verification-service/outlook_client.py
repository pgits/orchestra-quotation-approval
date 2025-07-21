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
    
    def get_latest_verification_code(self, sender: str = 'do_not_reply@tdsynnex.com', max_age_minutes: int = 10, ignore_time_window: bool = False, return_verification_id: bool = False, verbose_debug: bool = False) -> Optional[str]:
        """
        Get the latest verification code from emails from specified sender
        
        Args:
            sender: Email address to filter by
            max_age_minutes: Maximum age of email to consider (ignored if ignore_time_window=True)
            ignore_time_window: If True, search all emails regardless of age
            return_verification_id: If True, return verificationId instead of verification code
            verbose_debug: If True, log the full email content before extraction
            
        Returns:
            Verification code string or verificationId if found, None otherwise
        """
        if ignore_time_window:
            logger.info(f"🔍 Searching for {'verificationId' if return_verification_id else 'verification code'} from {sender} (ignoring time window)")
        else:
            logger.info(f"🔍 Searching for {'verificationId' if return_verification_id else 'verification code'} from {sender} (max age: {max_age_minutes} minutes)")
        
        # Search for emails from the specified sender
        if ignore_time_window:
            # When ignoring time window, get recent emails and filter client-side
            params = {
                '$orderby': 'receivedDateTime desc',
                '$top': 100,  # Get more emails to filter from
                '$select': 'subject,body,receivedDateTime,bodyPreview,sender'
            }
        else:
            # Calculate time filter
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            cutoff_time_str = cutoff_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            params = {
                '$filter': f"from/emailAddress/address eq '{sender}' and receivedDateTime ge {cutoff_time_str}",
                '$orderby': 'receivedDateTime desc',
                '$top': 10,
                '$select': 'subject,body,receivedDateTime,bodyPreview'
            }
        
        try:
            result = self._make_graph_request(f"users/{self.user_email}/messages", params=params)
            
            all_messages = result.get('value', [])
            
            if ignore_time_window:
                # Filter messages by sender client-side
                messages = []
                for msg in all_messages:
                    msg_sender = msg.get('sender', {}).get('emailAddress', {}).get('address', '')
                    if msg_sender.lower() == sender.lower():
                        messages.append(msg)
                        if len(messages) >= 50:  # Limit results
                            break
            else:
                messages = all_messages
            
            logger.info(f"📧 Found {len(messages)} emails from {sender}")
            
            for message in messages:
                # First check if this is actually a verification email
                if not self._is_verification_email(message):
                    if verbose_debug:
                        logger.info("⏭️  Skipping non-verification email")
                    continue
                
                if return_verification_id:
                    verification_id = self._extract_verification_id(message, verbose_debug)
                    if verification_id:
                        logger.info(f"✅ Found verificationId: {verification_id}")
                        return verification_id
                else:
                    verification_code = self._extract_verification_code(message, verbose_debug)
                    if verification_code:
                        logger.info(f"✅ Found verification code: {verification_code}")
                        return verification_code
            
            search_type = "verificationId" if return_verification_id else "verification code"
            logger.warning(f"⚠️ No {search_type} found in {len(messages)} emails from {sender}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching for verification code/ID: {e}")
            return None
    
    def _is_verification_email(self, message: Dict) -> bool:
        """
        Check if an email is actually a verification/2FA email
        
        Args:
            message: Email message from Graph API
            
        Returns:
            True if this appears to be a verification email, False otherwise
        """
        # Get email content
        subject = message.get('subject', '')
        body_preview = message.get('bodyPreview', '')
        
        # Get full body content if available
        body_content = ''
        if 'body' in message:
            body_content = message['body'].get('content', '')
        
        # Combine all text content for searching
        full_text = f"{subject} {body_preview} {body_content}".lower()
        
        # Look for specific verification email patterns
        verification_patterns = [
            'enter this code into the verification field',
            'verification code',
            'verification field',
            'enter this code',
            'authentication code',
            'security code',
            'login verification',
            'two-factor authentication',
            '2fa code',
            'expires at',
            'new login location',
            'login attempt'
        ]
        
        # Check if any verification patterns are found
        for pattern in verification_patterns:
            if pattern in full_text:
                logger.debug(f"✅ Identified as verification email (matched: '{pattern}')")
                return True
        
        logger.debug("❌ Not identified as verification email")
        return False
    
    def _extract_verification_code(self, message: Dict, verbose_debug: bool = False) -> Optional[str]:
        """
        Extract verification code from email message
        
        Args:
            message: Email message from Graph API
            verbose_debug: If True, log full email content
            
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
        
        if verbose_debug:
            logger.info("=" * 80)
            logger.info("📧 VERBOSE DEBUG: FULL EMAIL CONTENT")
            logger.info("=" * 80)
            logger.info(f"📧 Subject: {subject}")
            logger.info(f"📧 Received Time: {message.get('receivedDateTime', 'Unknown')}")
            logger.info(f"📧 Body Preview: {body_preview}")
            logger.info("-" * 40)
            logger.info("📧 Full Body Content:")
            logger.info(body_content[:2000] if body_content else "No body content")
            if len(body_content) > 2000:
                logger.info(f"... (truncated, full length: {len(body_content)} chars)")
            logger.info("-" * 40)
            logger.info(f"📧 Combined Search Text Length: {len(full_text)} chars")
            logger.info("=" * 80)
        else:
            logger.debug(f"📧 Email subject: {subject}")
            logger.debug(f"📧 Email preview: {body_preview[:100]}...")
        
        # Specific patterns for TD SYNNEX verification codes
        patterns = [
            r'PM PDT</span>:<br><br><span>(\d{6})</span>',  # Most specific - after PM PDT: with 6 digits
            r'expires at[^:]*:\s*<br><br><span>(\d{6})</span>',  # After "expires at" with 6 digits
            r'verification field[^:]*:\s*<br><br><span>(\d{6})</span>',  # After verification field with 6 digits
            r'<br><br><span>(\d{6})</span>(?!\d)',  # 6-digit code in span after br tags, not followed by more digits
            r':\s*<br><br><span>(\d{4,8})</span>',  # After colon, br tags, and span (general)
            r'(\d{6})(?!</span>\s*</td>.*(?:19|20)\d{2})',  # 6-digit not followed by year in same cell
            r'verification code[:\s]*(\d{4,8})',  # "verification code: 123456"
            r'authentication code[:\s]*(\d{4,8})',  # "authentication code: 123456"
            r'security code[:\s]*(\d{4,8})',  # "security code: 123456"
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
    
    def _extract_verification_id(self, message: Dict, verbose_debug: bool = False) -> Optional[str]:
        """
        Extract verificationId from email message body
        
        Args:
            message: Email message from Graph API
            verbose_debug: If True, log full email content
            
        Returns:
            VerificationId string if found, None otherwise
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
        
        if verbose_debug:
            logger.info("=" * 80)
            logger.info("📧 VERBOSE DEBUG: FULL EMAIL CONTENT (VerificationId Search)")
            logger.info("=" * 80)
            logger.info(f"📧 Subject: {subject}")
            logger.info(f"📧 Received Time: {message.get('receivedDateTime', 'Unknown')}")
            logger.info(f"📧 Body Preview: {body_preview}")
            logger.info("-" * 40)
            logger.info("📧 Full Body Content:")
            logger.info(body_content[:2000] if body_content else "No body content")
            if len(body_content) > 2000:
                logger.info(f"... (truncated, full length: {len(body_content)} chars)")
            logger.info("-" * 40)
            logger.info(f"📧 Combined Search Text Length: {len(full_text)} chars")
            logger.info("=" * 80)
        else:
            logger.debug(f"📧 Email subject: {subject}")
            logger.debug(f"📧 Email preview: {body_preview[:100]}...")
        
        # Common patterns for verificationId
        patterns = [
            r'verificationId[:\s]*([a-zA-Z0-9\-_]+)',  # "verificationId: abc123-def456"
            r'verification\s*id[:\s]*([a-zA-Z0-9\-_]+)',  # "verification id: abc123-def456"
            r'verification\s*ID[:\s]*([a-zA-Z0-9\-_]+)',  # "verification ID: abc123-def456"
            r'id[:\s]*([a-zA-Z0-9\-_]{8,})',  # "id: abc123def456" (at least 8 chars)
            r'ID[:\s]*([a-zA-Z0-9\-_]{8,})',  # "ID: abc123def456"
            r'([a-zA-Z0-9\-_]{16,})',  # Any alphanumeric string with dashes/underscores, at least 16 chars
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                verification_id = match.group(1)
                # Validate ID length and format (should be reasonably long and not just numbers)
                if len(verification_id) >= 8 and not verification_id.isdigit():
                    logger.info(f"✅ Extracted verificationId using pattern: {pattern}")
                    return verification_id
        
        logger.debug(f"⚠️ No verificationId found in email: {subject}")
        return None
    
    def post_verification_code(self, verification_code: str, target_url: str, timeout: int = 10) -> Dict:
        """
        POST verification code to target URL in the expected JSON format
        
        Args:
            verification_code: The verification code to submit
            target_url: URL to POST the verification code to
            timeout: Request timeout in seconds (default: 10)
            
        Returns:
            Dictionary with POST request results including status, response, and timing
        """
        import time
        
        logger.info(f"🚀 Posting verification code to {target_url}")
        
        # Prepare JSON payload - always use "verificationId" regardless of source
        payload = {"verificationId": verification_code}
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TD-SYNNEX-Email-Verification-Service/1.0'
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                target_url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Try to parse response as JSON, fallback to text
            try:
                response_body = response.json()
            except:
                response_body = response.text
            
            result = {
                'success': True,
                'status_code': response.status_code,
                'response_body': response_body,
                'url': target_url,
                'duration_ms': duration_ms,
                'headers_sent': headers,
                'payload_sent': payload
            }
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"✅ Successfully posted verification code - Status: {response.status_code}, Duration: {duration_ms}ms")
            else:
                logger.warning(f"⚠️ POST request returned non-success status: {response.status_code}")
                result['success'] = False
            
            return result
            
        except requests.exceptions.Timeout:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"❌ POST request timed out after {timeout} seconds")
            return {
                'success': False,
                'error': 'Request timeout',
                'url': target_url,
                'duration_ms': duration_ms,
                'timeout': timeout
            }
            
        except requests.exceptions.ConnectionError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Connection error posting verification code: {e}")
            return {
                'success': False,
                'error': f'Connection error: {str(e)}',
                'url': target_url,
                'duration_ms': duration_ms
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Unexpected error posting verification code: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'url': target_url,
                'duration_ms': duration_ms
            }
    
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