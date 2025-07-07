"""
Tests for email monitoring and notification functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from src.scraper.email_monitor import EmailMonitor
from src.notifications.email_alerts import NotificationService
from src.config.settings import Config


class TestEmailMonitor:
    
    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Config)
        config.EMAIL_USERNAME = "test@email.com"
        config.EMAIL_PASSWORD = "test_pass"
        config.IMAP_SERVER = "imap.test.com"
        config.SMTP_SERVER = "smtp.test.com"
        config.SMTP_PORT = 587
        return config
    
    @pytest.fixture
    def email_monitor(self, mock_config):
        return EmailMonitor(mock_config)
    
    @pytest.mark.asyncio
    async def test_wait_for_email_success(self, email_monitor):
        """Test successful email reception"""
        
        # Mock IMAP server
        mock_imap = Mock()
        mock_imap.search.return_value = (None, [b'1 2'])
        
        # Mock email message with attachment
        mock_email = MagicMock()
        mock_email.walk.return_value = [
            Mock(get_content_disposition=lambda: 'attachment',
                 get_filename=lambda: 'products.csv',
                 get_payload=lambda decode: b'csv data')
        ]
        
        mock_imap.fetch.return_value = (None, [(None, mock_email.as_bytes())])
        
        # Mock email parsing
        with patch('email.message_from_bytes', return_value=mock_email):
            with patch('imaplib.IMAP4_SSL', return_value=mock_imap):
                with patch.object(email_monitor, '_process_attachment', 
                                return_value=True) as mock_process:
                    
                    result = await email_monitor.wait_for_email(
                        session_id="test_123",
                        timeout_minutes=1
                    )
                    
                    assert result is True
                    mock_process.assert_called_once()
                    mock_imap.login.assert_called_once_with(
                        "test@email.com", "test_pass"
                    )
    
    @pytest.mark.asyncio
    async def test_wait_for_email_timeout(self, email_monitor):
        """Test email timeout scenario"""
        
        # Mock IMAP server with no emails
        mock_imap = Mock()
        mock_imap.search.return_value = (None, [b''])
        
        with patch('imaplib.IMAP4_SSL', return_value=mock_imap):
            # Use very short timeout for testing
            result = await email_monitor.wait_for_email(
                session_id="test_123",
                timeout_minutes=0.01  # Very short timeout
            )
            
            assert result is False
    
    def test_has_attachments_true(self, email_monitor):
        """Test attachment detection - has attachments"""
        
        mock_email = MagicMock()
        mock_part = Mock()
        mock_part.get_content_disposition.return_value = 'attachment'
        mock_email.walk.return_value = [mock_part]
        
        assert email_monitor._has_attachments(mock_email) is True
    
    def test_has_attachments_false(self, email_monitor):
        """Test attachment detection - no attachments"""
        
        mock_email = MagicMock()
        mock_part = Mock()
        mock_part.get_content_disposition.return_value = 'inline'
        mock_email.walk.return_value = [mock_part]
        
        assert email_monitor._has_attachments(mock_email) is False
    
    def test_validate_attachment_valid_csv(self, email_monitor):
        """Test attachment validation - valid CSV"""
        
        data = b"product,price\nSurface Pro,999"
        filename = "products.csv"
        
        assert email_monitor._validate_attachment(data, filename) is True
    
    def test_validate_attachment_invalid_extension(self, email_monitor):
        """Test attachment validation - invalid extension"""
        
        data = b"some data"
        filename = "products.pdf"
        
        assert email_monitor._validate_attachment(data, filename) is False
    
    def test_validate_attachment_empty(self, email_monitor):
        """Test attachment validation - empty file"""
        
        data = b""
        filename = "products.csv"
        
        assert email_monitor._validate_attachment(data, filename) is False
    
    def test_validate_attachment_too_large(self, email_monitor):
        """Test attachment validation - file too large"""
        
        data = b"x" * (51 * 1024 * 1024)  # 51MB
        filename = "products.csv"
        
        assert email_monitor._validate_attachment(data, filename) is False


class TestNotificationService:
    
    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Config)
        config.EMAIL_USERNAME = "sender@email.com"
        config.EMAIL_PASSWORD = "sender_pass"
        config.SMTP_SERVER = "smtp.test.com"
        config.SMTP_PORT = 587
        return config
    
    @pytest.fixture
    def notification_service(self, mock_config):
        return NotificationService(mock_config)
    
    @pytest.mark.asyncio
    async def test_send_failure_notification(self, notification_service):
        """Test sending failure notification"""
        
        mock_smtp = Mock()
        
        with patch('smtplib.SMTP', return_value=mock_smtp):
            await notification_service.send_failure_notification(
                failure_type="Login Failure",
                session_id="test_123",
                error_message="Invalid credentials"
            )
            
            # Verify SMTP interactions
            mock_smtp.__enter__.return_value.starttls.assert_called_once()
            mock_smtp.__enter__.return_value.login.assert_called_once_with(
                "sender@email.com", "sender_pass"
            )
            mock_smtp.__enter__.return_value.send_message.assert_called_once()
            
            # Verify email content
            sent_message = mock_smtp.__enter__.return_value.send_message.call_args[0][0]
            assert sent_message['To'] == 'pgits@hexalinks.com'
            assert 'Login Failure' in sent_message['Subject']
    
    @pytest.mark.asyncio
    async def test_send_success_notification(self, notification_service):
        """Test sending success notification"""
        
        mock_smtp = Mock()
        
        with patch('smtplib.SMTP', return_value=mock_smtp):
            await notification_service.send_success_notification(
                session_id="test_123",
                product_count=150,
                file_path="/tmp/products.csv"
            )
            
            # Verify email was sent
            mock_smtp.__enter__.return_value.send_message.assert_called_once()
            
            # Verify email content
            sent_message = mock_smtp.__enter__.return_value.send_message.call_args[0][0]
            assert sent_message['To'] == 'pgits@hexalinks.com'
            assert '150 Microsoft Products' in sent_message['Subject']
    
    @pytest.mark.asyncio
    async def test_send_health_check(self, notification_service):
        """Test sending health check notification"""
        
        mock_smtp = Mock()
        
        with patch('smtplib.SMTP', return_value=mock_smtp):
            await notification_service.send_health_check()
            
            # Verify email was sent
            mock_smtp.__enter__.return_value.send_message.assert_called_once()
            
            # Verify email content
            sent_message = mock_smtp.__enter__.return_value.send_message.call_args[0][0]
            assert sent_message['To'] == 'pgits@hexalinks.com'
            assert 'Daily Health Check' in sent_message['Subject']
    
    @pytest.mark.asyncio
    async def test_notification_smtp_failure(self, notification_service):
        """Test handling of SMTP failures"""
        
        with patch('smtplib.SMTP', side_effect=Exception("SMTP error")):
            # Should not raise exception, just log the error
            await notification_service.send_failure_notification(
                failure_type="Test",
                session_id="test_123",
                error_message="Test error"
            )
            
            # Test passes if no exception is raised


if __name__ == "__main__":
    pytest.main([__file__])