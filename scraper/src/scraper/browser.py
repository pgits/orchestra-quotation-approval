"""
TD SYNNEX Browser automation using Selenium
"""

import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class TDSynnexBrowser:
    """Browser automation for TD SYNNEX portal"""
    
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.wait = None
    
    async def initialize(self):
        """Initialize the browser with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Disable images for better performance
        
        try:
            # Try Chrome first, then Chromium (for multi-arch support)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Browser initialized with Chrome")
            except WebDriverException:
                # Fallback to Chromium (common on ARM64 containers)
                chrome_options.binary_location = '/usr/bin/chromium'
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Browser initialized with Chromium")
                
            self.wait = WebDriverWait(self.driver, 30)
            logger.info("Browser initialized successfully")
        except WebDriverException as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    async def login(self):
        """Authenticate with TD SYNNEX portal"""
        try:
            self.driver.get("https://ec.synnex.com/ecx/eServices/priceAvailabilityDownload.html")
            
            # Wait for login form
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            
            # Enter credentials
            username_field.send_keys(self.config.TDSYNNEX_USERNAME)
            password_field.send_keys(self.config.TDSYNNEX_PASSWORD)
            
            # Submit login
            login_button = self.driver.find_element(By.ID, "loginButton")
            login_button.click()
            
            # Wait for successful login
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
            )
            
            logger.info("Successfully logged into TD SYNNEX portal")
            
        except TimeoutException:
            logger.error("Login timeout - check credentials or portal availability")
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise
    
    async def navigate_to_download_page(self):
        """Navigate to the price/availability download page"""
        try:
            # Navigate to the specific download page
            self.driver.get("https://ec.synnex.com/ecx/eServices/priceAvailabilityDownload.html#")
            
            # Wait for page to load
            self.wait.until(
                EC.presence_of_element_located((By.ID, "downloadForm"))
            )
            
            logger.info("Successfully navigated to download page")
            
        except TimeoutException:
            logger.error("Timeout waiting for download page to load")
            raise
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            raise
    
    async def request_download(self):
        """Submit the download request"""
        try:
            # Find and click the download button
            download_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "downloadButton"))
            )
            
            download_button.click()
            
            # Wait for confirmation
            confirmation = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "download-confirmation"))
            )
            
            logger.info("Download request submitted successfully")
            return True
            
        except TimeoutException:
            logger.error("Timeout waiting for download confirmation")
            return False
        except Exception as e:
            logger.error(f"Download request failed: {str(e)}")
            return False
    
    async def close(self):
        """Clean up browser resources"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")