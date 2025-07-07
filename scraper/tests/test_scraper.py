"""
Tests for TD SYNNEX scraper functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.scraper.main import TDSynnexScraperOrchestrator
from src.scraper.browser import TDSynnexBrowser
from src.config.settings import Config


class TestScraperOrchestrator:
    
    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Config)
        config.TDSYNNEX_USERNAME = "test_user"
        config.TDSYNNEX_PASSWORD = "test_pass"
        config.EMAIL_USERNAME = "test@email.com"
        config.EMAIL_PASSWORD = "email_pass"
        config.IMAP_SERVER = "imap.test.com"
        config.SMTP_SERVER = "smtp.test.com"
        config.SMTP_PORT = 587
        config.LOG_LEVEL = "INFO"
        config.RETRY_ATTEMPTS = 3
        config.TIMEOUT_MINUTES = 120
        return config
    
    @pytest.fixture
    def orchestrator(self, mock_config):
        with patch('src.scraper.main.Config', return_value=mock_config):
            return TDSynnexScraperOrchestrator()
    
    @pytest.mark.asyncio
    async def test_scrape_microsoft_products_success(self, orchestrator):
        """Test successful scraping workflow"""
        
        # Mock all dependencies
        orchestrator.browser.initialize = AsyncMock()
        orchestrator.browser.login = AsyncMock()
        orchestrator.browser.navigate_to_download_page = AsyncMock()
        orchestrator.browser.request_download = AsyncMock(return_value=True)
        orchestrator.browser.close = AsyncMock()
        
        orchestrator.filter.apply_filters = AsyncMock(return_value=[
            {"name": "Surface Pro", "manufacturer": "Microsoft"},
            {"name": "Xbox Series X", "manufacturer": "Microsoft"}
        ])
        
        orchestrator.email_monitor.wait_for_email = AsyncMock(return_value=True)
        orchestrator.notifications.send_failure_notification = AsyncMock()
        
        # Execute
        result = await orchestrator.scrape_microsoft_products()
        
        # Verify
        assert result is True
        orchestrator.browser.initialize.assert_called_once()
        orchestrator.browser.login.assert_called_once()
        orchestrator.browser.navigate_to_download_page.assert_called_once()
        orchestrator.filter.apply_filters.assert_called_once()
        orchestrator.browser.request_download.assert_called_once()
        orchestrator.email_monitor.wait_for_email.assert_called_once()
        orchestrator.browser.close.assert_called_once()
        orchestrator.notifications.send_failure_notification.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_scrape_microsoft_products_download_failure(self, orchestrator):
        """Test handling of download request failure"""
        
        # Mock dependencies
        orchestrator.browser.initialize = AsyncMock()
        orchestrator.browser.login = AsyncMock()
        orchestrator.browser.navigate_to_download_page = AsyncMock()
        orchestrator.browser.request_download = AsyncMock(return_value=False)
        orchestrator.browser.close = AsyncMock()
        
        orchestrator.filter.apply_filters = AsyncMock(return_value=[])
        orchestrator.notifications.send_failure_notification = AsyncMock()
        
        # Execute
        result = await orchestrator.scrape_microsoft_products()
        
        # Verify
        assert result is False
        orchestrator.notifications.send_failure_notification.assert_called_once()
        assert "Failed to submit download request" in str(
            orchestrator.notifications.send_failure_notification.call_args
        )
    
    @pytest.mark.asyncio
    async def test_scrape_microsoft_products_email_timeout(self, orchestrator):
        """Test handling of email timeout"""
        
        # Mock dependencies
        orchestrator.browser.initialize = AsyncMock()
        orchestrator.browser.login = AsyncMock()
        orchestrator.browser.navigate_to_download_page = AsyncMock()
        orchestrator.browser.request_download = AsyncMock(return_value=True)
        orchestrator.browser.close = AsyncMock()
        
        orchestrator.filter.apply_filters = AsyncMock(return_value=[])
        orchestrator.email_monitor.wait_for_email = AsyncMock(return_value=False)
        orchestrator.notifications.send_failure_notification = AsyncMock()
        
        # Execute
        result = await orchestrator.scrape_microsoft_products()
        
        # Verify
        assert result is False
        orchestrator.notifications.send_failure_notification.assert_called_once()
        assert "Email not received within timeout period" in str(
            orchestrator.notifications.send_failure_notification.call_args
        )
    
    def test_setup_schedule(self, orchestrator):
        """Test scheduler configuration"""
        
        orchestrator.setup_schedule()
        
        # Get all jobs
        jobs = orchestrator.scheduler.get_jobs()
        
        # Verify two jobs are scheduled
        assert len(jobs) == 2
        
        # Verify job IDs
        job_ids = [job.id for job in jobs]
        assert 'morning_scrape' in job_ids
        assert 'evening_scrape' in job_ids


class TestBrowser:
    
    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Config)
        config.TDSYNNEX_USERNAME = "test_user"
        config.TDSYNNEX_PASSWORD = "test_pass"
        return config
    
    @pytest.fixture
    def browser(self, mock_config):
        return TDSynnexBrowser(mock_config)
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, browser):
        """Test successful browser initialization"""
        
        with patch('selenium.webdriver.Chrome') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            
            await browser.initialize()
            
            assert browser.driver == mock_driver
            assert browser.wait is not None
            mock_chrome.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_success(self, browser):
        """Test successful login"""
        
        # Mock driver and elements
        mock_driver = Mock()
        mock_username_field = Mock()
        mock_password_field = Mock()
        mock_login_button = Mock()
        
        browser.driver = mock_driver
        browser.wait = Mock()
        browser.wait.until = Mock(return_value=mock_username_field)
        
        mock_driver.find_element.side_effect = [
            mock_password_field,
            mock_login_button
        ]
        
        # Execute
        await browser.login()
        
        # Verify
        mock_driver.get.assert_called_once_with(
            "https://ec.synnex.com/ecx/eServices/priceAvailabilityDownload.html"
        )
        mock_username_field.send_keys.assert_called_once_with("test_user")
        mock_password_field.send_keys.assert_called_once_with("test_pass")
        mock_login_button.click.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])