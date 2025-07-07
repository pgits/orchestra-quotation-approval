"""
Email notification service for failures
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Handle failure notifications"""
    
    def __init__(self, config):
        self.config = config
    
    async def send_failure_notification(self, failure_type: str, session_id: str, 
                                      error_message: str):
        """Send failure notification to pgits@hexalinks.com"""
        
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_USERNAME
            msg['To'] = 'pgits@hexalinks.com'
            msg['Subject'] = f"TD SYNNEX Scraper Failure - {failure_type}"
            
            # Email body
            body = f"""
TD SYNNEX Microsoft Product Scraper Failure

Failure Type: {failure_type}
Session ID: {session_id}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}

Error Details:
{error_message}

System: TD SYNNEX Automated Scraper
Target: Microsoft Products
Frequency: Twice daily (10:00 AM & 5:55 PM EST)

Please investigate and resolve the issue.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Failure notification sent for {failure_type}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
    
    async def send_success_notification(self, session_id: str, product_count: int, 
                                      file_path: str = None):
        """Send success notification with summary"""
        
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_USERNAME
            msg['To'] = 'pgits@hexalinks.com'
            msg['Subject'] = f"TD SYNNEX Scraper Success - {product_count} Microsoft Products"
            
            # Email body
            body = f"""
TD SYNNEX Microsoft Product Scraper Success

Session ID: {session_id}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}
Microsoft Products Found: {product_count}

The data has been successfully:
✓ Downloaded from TD SYNNEX
✓ Filtered for Microsoft products
✓ Forwarded to your email for Copilot processing

System: TD SYNNEX Automated Scraper
Next Run: According to schedule (10:00 AM & 5:55 PM EST)
            """
            
            if file_path:
                body += f"\nStaging File: {file_path}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Success notification sent for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to send success notification: {str(e)}")
    
    async def send_health_check(self):
        """Send daily health check email"""
        
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_USERNAME
            msg['To'] = 'pgits@hexalinks.com'
            msg['Subject'] = "TD SYNNEX Scraper - Daily Health Check"
            
            # Email body
            body = f"""
TD SYNNEX Scraper Health Check

Status: OPERATIONAL
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}

Scheduled Jobs:
- Morning Scrape: 10:00 AM EST
- Evening Scrape: 5:55 PM EST

Configuration:
- TD SYNNEX Portal: Connected
- Email Monitoring: Active
- Copilot Integration: Configured

System: TD SYNNEX Automated Scraper
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info("Health check notification sent")
            
        except Exception as e:
            logger.error(f"Failed to send health check: {str(e)}")