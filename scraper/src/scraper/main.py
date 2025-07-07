#!/usr/bin/env python3
"""
TD SYNNEX Microsoft Product Scraper
Main orchestration module
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from .browser import TDSynnexBrowser
from .microsoft_filter import MicrosoftProductFilter
from .email_monitor import EmailMonitor
from ..notifications.email_alerts import NotificationService
from ..config.settings import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TDSynnexScraperOrchestrator:
    """Main orchestrator for TD SYNNEX scraping operations"""
    
    def __init__(self):
        self.config = Config()
        self.browser = TDSynnexBrowser(self.config)
        self.filter = MicrosoftProductFilter()
        self.email_monitor = EmailMonitor(self.config)
        self.notifications = NotificationService(self.config)
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('America/New_York'))
        
    async def scrape_microsoft_products(self):
        """Execute the complete scraping workflow"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Starting scraping session: {session_id}")
        
        try:
            # Step 1: Navigate to TD SYNNEX portal
            await self.browser.initialize()
            await self.browser.login()
            
            # Step 2: Navigate to price/availability download page
            await self.browser.navigate_to_download_page()
            
            # Step 3: Apply Microsoft product filters
            microsoft_products = await self.filter.apply_filters(self.browser)
            logger.info(f"Found {len(microsoft_products)} Microsoft products")
            
            # Step 4: Request download
            download_success = await self.browser.request_download()
            
            if download_success:
                logger.info("Download request submitted successfully")
                
                # Step 5: Monitor for email with attachment
                email_received = await self.email_monitor.wait_for_email(
                    session_id=session_id,
                    timeout_minutes=120  # 2 hours
                )
                
                if email_received:
                    logger.info(f"Email received for session {session_id}")
                    return True
                else:
                    raise Exception("Email not received within timeout period")
            else:
                raise Exception("Failed to submit download request")
                
        except Exception as e:
            logger.error(f"Scraping session {session_id} failed: {str(e)}")
            await self.notifications.send_failure_notification(
                failure_type="Scraping Failure",
                session_id=session_id,
                error_message=str(e)
            )
            return False
            
        finally:
            await self.browser.close()
    
    def setup_schedule(self):
        """Setup scheduled scraping jobs"""
        # Morning job: 10:00 AM EST
        self.scheduler.add_job(
            self.scrape_microsoft_products,
            CronTrigger(hour=10, minute=0, timezone=pytz.timezone('America/New_York')),
            id='morning_scrape',
            name='Morning Microsoft Product Scrape'
        )
        
        # Evening job: 5:55 PM EST
        self.scheduler.add_job(
            self.scrape_microsoft_products,
            CronTrigger(hour=17, minute=55, timezone=pytz.timezone('America/New_York')),
            id='evening_scrape',
            name='Evening Microsoft Product Scrape'
        )
        
        logger.info("Scheduled jobs configured: 10:00 AM EST and 5:55 PM EST")
    
    async def start(self):
        """Start the scraper service"""
        logger.info("Starting TD SYNNEX Scraper Service")
        self.setup_schedule()
        self.scheduler.start()
        
        try:
            # Keep the service running
            while True:
                await asyncio.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.scheduler.shutdown()

async def main():
    """Entry point"""
    orchestrator = TDSynnexScraperOrchestrator()
    await orchestrator.start()

if __name__ == "__main__":
    asyncio.run(main())