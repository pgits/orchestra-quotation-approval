#!/usr/bin/env python3
"""
Notification Service for TD SYNNEX Knowledge Update System
Handles Teams messages and email notifications for upload status

This service can be reused by other components (scraper, etc.) for consistent notifications.
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class NotificationService:
    """Unified notification service for Teams and email notifications"""
    
    def __init__(self):
        """Initialize notification service with environment variables"""
        load_dotenv()
        
        # Teams configuration
        self.teams_webhook_url = os.getenv('TEAMS_WEBHOOK_URL')
        self.teams_channel_name = os.getenv('TEAMS_CHANNEL_NAME', 'Quotation Teams')
        
        # Email configuration (Graph API)
        self.email_from = os.getenv('EMAIL_FROM', os.getenv('OUTLOOK_USER_EMAIL'))
        self.notification_email = os.getenv('NOTIFICATION_EMAIL', 'pgits@hexalinks.com')
        
        # Azure credentials for Graph API
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.user_email = os.getenv('OUTLOOK_USER_EMAIL')
        
        # Service identification
        self.service_name = os.getenv('SERVICE_NAME', 'TD SYNNEX Knowledge Update')
        self.environment = os.getenv('ENVIRONMENT', 'Production')
        
        logger.info(f"📢 NotificationService initialized for {self.service_name}")
        
    def _get_access_token(self) -> str:
        """Get access token for Microsoft Graph API"""
        try:
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data['access_token']
            
        except Exception as e:
            logger.error(f"❌ Failed to get access token: {e}")
            raise
        
    def send_upload_notification(self, 
                               success: bool,
                               filename: str,
                               final_filename: str = None,
                               error_message: str = None,
                               file_size: int = None,
                               sharepoint_url: str = None,
                               deleted_files: List[str] = None,
                               processing_time: float = None) -> Dict:
        """
        Send notification for upload completion (success or failure)
        
        Args:
            success: Whether the upload was successful
            filename: Original filename requested
            final_filename: Final filename used (may have incremental number)
            error_message: Error details if failed
            file_size: Size of uploaded file in bytes
            sharepoint_url: SharePoint URL of uploaded file
            deleted_files: List of files that were automatically deleted
            processing_time: Time taken for processing in seconds
            
        Returns:
            Dictionary with notification results
        """
        logger.info(f"📢 Sending upload notification - Success: {success}, File: {filename}")
        
        result = {
            'teams_sent': False,
            'email_sent': False,
            'errors': []
        }
        
        # Create notification content
        notification_data = self._create_upload_notification_content(
            success=success,
            filename=filename,
            final_filename=final_filename,
            error_message=error_message,
            file_size=file_size,
            sharepoint_url=sharepoint_url,
            deleted_files=deleted_files,
            processing_time=processing_time
        )
        
        # Send Teams notification
        if self.teams_webhook_url:
            try:
                teams_result = self._send_teams_message(notification_data['teams_content'])
                result['teams_sent'] = teams_result
                if teams_result:
                    logger.info("✅ Teams notification sent successfully")
                else:
                    logger.warning("⚠️ Teams notification failed")
            except Exception as e:
                error_msg = f"Teams notification error: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
        else:
            logger.warning("⚠️ No Teams webhook URL configured")
            
        # Send email notification (try Graph API first, fall back to SMTP if needed)
        email_result = False
        if self.tenant_id and self.client_id and self.client_secret:
            try:
                email_result = self._send_graph_email_notification(
                    subject=notification_data['email_subject'],
                    content=notification_data['email_content']
                )
                if email_result:
                    logger.info("✅ Email notification sent successfully via Graph API")
            except Exception as e:
                logger.warning(f"⚠️ Graph API email failed: {str(e)}, trying alternative method...")
        
        # If Graph API failed or not configured, try SMTP (if credentials available)
        smtp_username = os.getenv('EMAIL_USERNAME')
        smtp_password = os.getenv('EMAIL_PASSWORD')
        if not email_result and smtp_username and smtp_password:
            try:
                email_result = self._send_smtp_email_notification(
                    subject=notification_data['email_subject'],
                    content=notification_data['email_content']
                )
                if email_result:
                    logger.info("✅ Email notification sent successfully via SMTP")
            except Exception as e:
                logger.warning(f"⚠️ SMTP email also failed: {str(e)}")
        
        result['email_sent'] = email_result
        if not email_result:
            error_msg = "All email methods failed - check Azure app permissions or SMTP credentials"
            result['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
            
        return result
    
    def send_scraper_notification(self,
                                success: bool,
                                session_id: str,
                                execution_time: float,
                                files_triggered: int = 0,
                                error_message: str = None,
                                screenshots_saved: int = 0) -> Dict:
        """
        Send notification for scraper completion (for future use)
        
        Args:
            success: Whether the scraper was successful
            session_id: Unique session identifier
            execution_time: Time taken for scraping in seconds
            files_triggered: Number of files triggered for download
            error_message: Error details if failed
            screenshots_saved: Number of debug screenshots saved
            
        Returns:
            Dictionary with notification results
        """
        logger.info(f"📢 Sending scraper notification - Success: {success}, Session: {session_id}")
        
        # This can be implemented when we add scraper notifications
        return {'teams_sent': False, 'email_sent': False, 'errors': ['Not implemented yet']}
    
    def _create_upload_notification_content(self, success: bool, filename: str, 
                                          final_filename: str = None, error_message: str = None,
                                          file_size: int = None, sharepoint_url: str = None,
                                          deleted_files: List[str] = None, 
                                          processing_time: float = None) -> Dict:
        """Create notification content for both Teams and email"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        status_emoji = "✅" if success else "❌"
        status_text = "SUCCESS" if success else "FAILED"
        
        # Extract date from filename for display
        original_date = self._extract_date_from_filename(filename)
        final_date = self._extract_date_from_filename(final_filename) if final_filename else original_date
        
        # Format file size
        size_text = self._format_file_size(file_size) if file_size else "Unknown size"
        
        # Teams message content (JSON format for webhook)
        teams_content = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"TD SYNNEX Upload {status_text}: {filename}",
            "themeColor": "00FF00" if success else "FF0000",
            "sections": [
                {
                    "activityTitle": f"{status_emoji} TD SYNNEX Knowledge Update {status_text}",
                    "activitySubtitle": f"{self.service_name} - {self.environment}",
                    "activityImage": "https://img.icons8.com/color/48/000000/microsoft-teams-2019.png",
                    "facts": [
                        {"name": "Status", "value": status_text},
                        {"name": "Timestamp", "value": timestamp},
                        {"name": "Original File", "value": f"{filename} ({original_date})"},
                    ],
                    "markdown": True
                }
            ]
        }
        
        # Add success-specific information
        if success:
            success_facts = [
                {"name": "Final File", "value": f"{final_filename or filename} ({final_date})"},
                {"name": "File Size", "value": size_text}
            ]
            
            if processing_time:
                success_facts.append({"name": "Processing Time", "value": f"{processing_time:.2f} seconds"})
                
            if deleted_files:
                deleted_text = ", ".join(deleted_files)
                success_facts.append({"name": "Previous Files Deleted", "value": deleted_text})
                
            if sharepoint_url:
                teams_content["sections"][0]["potentialAction"] = [
                    {
                        "@type": "OpenUri",
                        "name": "View in SharePoint",
                        "targets": [{"os": "default", "uri": sharepoint_url}]
                    }
                ]
                
            teams_content["sections"][0]["facts"].extend(success_facts)
        else:
            # Add failure information
            teams_content["sections"][0]["facts"].append({
                "name": "Error", "value": error_message or "Unknown error"
            })
        
        # Email content (HTML format)
        email_subject = f"[{status_text}] TD SYNNEX Upload: {filename} ({original_date})"
        
        email_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2 style="color: {'#008000' if success else '#FF0000'};">
                {status_emoji} TD SYNNEX Knowledge Update {status_text}
            </h2>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Upload Details</h3>
                <ul>
                    <li><strong>Service:</strong> {self.service_name}</li>
                    <li><strong>Environment:</strong> {self.environment}</li>
                    <li><strong>Timestamp:</strong> {timestamp}</li>
                    <li><strong>Original File:</strong> {filename} ({original_date})</li>
        """
        
        if success:
            email_content += f"""
                    <li><strong>Final File:</strong> {final_filename or filename} ({final_date})</li>
                    <li><strong>File Size:</strong> {size_text}</li>
            """
            
            if processing_time:
                email_content += f"<li><strong>Processing Time:</strong> {processing_time:.2f} seconds</li>"
                
            if deleted_files:
                deleted_text = ", ".join(deleted_files)
                email_content += f"<li><strong>Previous Files Deleted:</strong> {deleted_text}</li>"
                
            if sharepoint_url:
                email_content += f"""
                    <li><strong>SharePoint:</strong> <a href="{sharepoint_url}">View File</a></li>
                """
        else:
            email_content += f"""
                    <li><strong>Error:</strong> {error_message or "Unknown error"}</li>
            """
        
        email_content += """
                </ul>
            </div>
            
            <p style="color: #666; font-size: 12px;">
                This is an automated notification from the TD SYNNEX Knowledge Update Service.
            </p>
        </body>
        </html>
        """
        
        return {
            'teams_content': teams_content,
            'email_subject': email_subject,
            'email_content': email_content
        }
    
    def _send_teams_message(self, message_content: Dict) -> bool:
        """Send message to Teams channel via webhook (supports both Teams webhooks and Power Automate)"""
        try:
            # Check if this is a Power Automate URL
            is_power_automate = 'powerautomate' in self.teams_webhook_url.lower()
            
            if is_power_automate:
                # For Power Automate, send a simplified JSON payload
                power_automate_payload = {
                    "title": message_content.get("summary", "TD SYNNEX Notification"),
                    "text": message_content["sections"][0]["activityTitle"],
                    "facts": message_content["sections"][0]["facts"],
                    "color": message_content.get("themeColor", "00FF00")
                }
                payload = power_automate_payload
            else:
                # For Teams webhook, use the original MessageCard format
                payload = message_content
            
            response = requests.post(
                self.teams_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            # Power Automate typically returns 202 (Accepted) on success
            if is_power_automate:
                return response.status_code in [200, 202]
            else:
                # Teams webhook returns "1" on success
                return response.text == "1"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Teams webhook request failed: {e}")
            return False
    
    def _send_graph_email_notification(self, subject: str, content: str) -> bool:
        """Send email notification via Microsoft Graph API"""
        try:
            # Get access token
            access_token = self._get_access_token()
            
            # Create email message
            email_message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": content
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": self.notification_email
                            }
                        }
                    ]
                }
            }
            
            # Send email via Graph API
            url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/sendMail"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=email_message, headers=headers)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Graph API email sending failed: {e}")
            return False
    
    def _send_smtp_email_notification(self, subject: str, content: str) -> bool:
        """Send email notification via SMTP (fallback method)"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.office365.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('EMAIL_USERNAME')
            smtp_password = os.getenv('EMAIL_PASSWORD')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = self.notification_email
            
            # Add HTML content
            msg.attach(MIMEText(content, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            logger.error(f"SMTP email sending failed: {e}")
            return False
    
    def _extract_date_from_filename(self, filename: str) -> str:
        """Extract and format date from TD SYNNEX filename"""
        if not filename:
            return "Unknown date"
            
        try:
            # TD SYNNEX format: 701601-MMDD-XXXX.txt
            parts = filename.split('-')
            if len(parts) >= 3 and parts[0] == '701601':
                month_day = parts[1]
                if len(month_day) == 4:
                    month = month_day[:2]
                    day = month_day[2:]
                    current_year = datetime.now().year
                    return f"{current_year}-{month}-{day}"
        except Exception:
            pass
            
        return "Unknown date"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def test_notifications(self) -> Dict:
        """Test notification system with sample data"""
        logger.info("🧪 Testing notification system...")
        
        return self.send_upload_notification(
            success=True,
            filename="701601-0725-1234.txt",
            final_filename="701601-0725-1234-1.txt",
            file_size=87049,
            sharepoint_url="https://hexalinks.sharepoint.com/sites/QuotationsTeam/test.txt",
            deleted_files=["701601-0724-5678.txt"],
            processing_time=2.5
        )

# Convenience functions for easy import and use
def send_upload_success(filename: str, final_filename: str = None, **kwargs) -> Dict:
    """Convenience function to send success notification"""
    service = NotificationService()
    return service.send_upload_notification(
        success=True,
        filename=filename,
        final_filename=final_filename,
        **kwargs
    )

def send_upload_failure(filename: str, error_message: str, **kwargs) -> Dict:
    """Convenience function to send failure notification"""
    service = NotificationService()
    return service.send_upload_notification(
        success=False,
        filename=filename,
        error_message=error_message,
        **kwargs
    )

def test_notifications() -> Dict:
    """Test the notification system"""
    service = NotificationService()
    return service.test_notifications()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test notifications
    result = test_notifications()
    print(f"Test result: {result}")