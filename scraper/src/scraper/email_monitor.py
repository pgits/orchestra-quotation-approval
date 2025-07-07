"""
Email monitoring for TD SYNNEX download confirmations
"""

import asyncio
import email
import imaplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

logger = logging.getLogger(__name__)

class EmailMonitor:
    """Monitor emails from TD SYNNEX"""
    
    def __init__(self, config):
        self.config = config
        self.imap_server = None
    
    async def wait_for_email(self, session_id: str, timeout_minutes: int = 120) -> bool:
        """Wait for TD SYNNEX email with attachment"""
        
        start_time = datetime.now()
        timeout_time = start_time + timedelta(minutes=timeout_minutes)
        
        logger.info(f"Monitoring for TD SYNNEX email (session: {session_id})")
        
        try:
            # Connect to email server
            self.imap_server = imaplib.IMAP4_SSL(self.config.IMAP_SERVER)
            self.imap_server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
            self.imap_server.select('INBOX')
            
            while datetime.now() < timeout_time:
                # Search for emails from TD SYNNEX
                _, message_numbers = self.imap_server.search(
                    None, 
                    f'FROM "do_not_reply@tdsynnex.com" SINCE "{start_time.strftime("%d-%b-%Y")}"'
                )
                
                if message_numbers[0]:
                    # Check each email
                    for num in message_numbers[0].split():
                        _, msg_data = self.imap_server.fetch(num, '(RFC822)')
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Check if email has attachments and is recent
                        if self._has_attachments(email_message):
                            # Process the attachment
                            success = await self._process_attachment(email_message, session_id)
                            if success:
                                logger.info(f"Successfully processed email for session {session_id}")
                                return True
                
                # Wait before checking again
                await asyncio.sleep(30)  # Check every 30 seconds
            
            logger.warning(f"Timeout waiting for email (session: {session_id})")
            return False
            
        except Exception as e:
            logger.error(f"Email monitoring failed: {str(e)}")
            return False
        finally:
            if self.imap_server:
                self.imap_server.close()
                self.imap_server.logout()
    
    def _has_attachments(self, email_message) -> bool:
        """Check if email has attachments"""
        for part in email_message.walk():
            if part.get_content_disposition() == 'attachment':
                return True
        return False
    
    async def _process_attachment(self, email_message, session_id: str) -> bool:
        """Process email attachment and trigger Copilot integration"""
        
        try:
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        # Save attachment
                        attachment_data = part.get_payload(decode=True)
                        
                        # Validate file (basic checks)
                        if self._validate_attachment(attachment_data, filename):
                            # Save to staging area
                            staging_path = f"/tmp/staging_{session_id}_{filename}"
                            with open(staging_path, 'wb') as f:
                                f.write(attachment_data)
                            
                            logger.info(f"Attachment saved: {staging_path}")
                            
                            # Forward email to pgits@hexalinks.com for Copilot processing
                            await self._forward_to_copilot(email_message)
                            
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Attachment processing failed: {str(e)}")
            return False
    
    def _validate_attachment(self, data: bytes, filename: str) -> bool:
        """Basic validation of attachment"""
        
        # Check file size (not empty, not too large)
        if len(data) == 0 or len(data) > 50 * 1024 * 1024:  # 50MB limit
            return False
        
        # Check file extension
        valid_extensions = ['.csv', '.xlsx', '.xls', '.txt']
        if not any(filename.lower().endswith(ext) for ext in valid_extensions):
            return False
        
        return True
    
    async def _forward_to_copilot(self, original_email):
        """Forward the email to pgits@hexalinks.com for Copilot processing"""
        
        try:
            # Create forwarded message
            forwarded = MIMEMultipart()
            forwarded['From'] = self.config.EMAIL_USERNAME
            forwarded['To'] = 'pgits@hexalinks.com'
            forwarded['Subject'] = f"TD SYNNEX Microsoft Products - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Add forwarded content
            forwarded.attach(MIMEText("Automated forward from TD SYNNEX scraper", 'plain'))
            
            # Forward all attachments
            for part in original_email.walk():
                if part.get_content_disposition() == 'attachment':
                    forwarded.attach(part)
            
            # Send via SMTP
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
                server.send_message(forwarded)
            
            logger.info("Email forwarded to pgits@hexalinks.com for Copilot processing")
            
        except Exception as e:
            logger.error(f"Email forwarding failed: {str(e)}")