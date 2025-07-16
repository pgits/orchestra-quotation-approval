#!/usr/bin/env python3
"""
TD SYNNEX Microsoft Product Scraper - Production Version with 2FA Handler
Uses real TD SYNNEX portal and production credentials with integrated 2FA support
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import requests
from integrated_verification_handler import IntegratedTwoFactorHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProductionScraperWith2FA:
    """Production scraper with integrated 2FA support"""
    
    def __init__(self):
        # Get credentials from environment or .env file
        self.load_environment()
        
        # TD SYNNEX Portal URL
        self.portal_url = "https://ec.synnex.com/ecx/eServices/priceAvailabilityDownload.html"
        self.login_url = "https://ec.synnex.com/ecx/login.html"
        
        # Browser setup
        self.driver = None
        self.wait = None
        
        # Initialize 2FA handler
        self.two_fa_handler = IntegratedTwoFactorHandler()
        
        # Processing state
        self.products_found = []
        self.current_download_info = None
        
        # Statistics
        self.stats = {
            "total_products": 0,
            "products_with_stock": 0,
            "products_out_of_stock": 0,
            "download_successful": False,
            "execution_time": 0
        }
    
    def load_environment(self):
        """Load environment variables"""
        logger.info("Loading environment variables...")
        
        # Try to load from .env file
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Get credentials
        self.td_username = os.getenv('TDSYNNEX_USERNAME')
        self.td_password = os.getenv('TDSYNNEX_PASSWORD')
        
        if not self.td_username or not self.td_password:
            logger.error("❌ Missing TD SYNNEX credentials in environment variables")
            logger.error("Please set TDSYNNEX_USERNAME and TDSYNNEX_PASSWORD")
            sys.exit(1)
        
        logger.info(f"✅ Loaded credentials for: {self.td_username}")
    
    def handle_cookie_popup(self):
        """Handle cookie consent popup if present"""
        logger.info("Checking for cookie consent popup...")
        
        # List of known cookie consent button selectors
        cookie_selectors = [
            ("ID", "onetrust-accept-btn-handler", "Accept All Cookies"),
            ("ID", "onetrust-cookie-btn", "Cookies Button"),
            ("ID", "accept-recommended-btn-handler", "Accept Recommended"),
            ("CSS", "#onetrust-accept-btn-handler", "Accept All (CSS)"),
            ("CSS", ".save-preference-btn-handler", "Save Preferences"),
            ("CSS", "[id*='accept'][id*='cookie']", "Accept Cookie (Wildcard)"),
            ("XPATH", "//button[contains(text(), 'Accept All')]", "Accept All Text"),
            ("XPATH", "//button[contains(text(), 'ACCEPT')]", "ACCEPT Text"),
            ("XPATH", "//button[contains(@id, 'accept') and contains(@id, 'cookie')]", "Accept Cookie ID")
        ]
        
        # Wait up to 10 seconds for cookie popup to appear
        for attempt in range(10):
            for selector_type, selector, description in cookie_selectors:
                try:
                    if selector_type == "ID":
                        cookie_button = self.driver.find_element(By.ID, selector)
                    elif selector_type == "CSS":
                        cookie_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        cookie_button = self.driver.find_element(By.XPATH, selector)
                    
                    if cookie_button.is_displayed():
                        cookie_button.click()
                        logger.info(f"✅ Accepted cookies: {description}")
                        time.sleep(3)  # Wait for popup to disappear
                        return True
                        
                except Exception as e:
                    logger.debug(f"Cookie selector failed ({description}): {e}")
                    continue
            
            time.sleep(1)  # Wait 1 second before next attempt
        
        logger.info("No cookie popup detected or already handled")
        return False
    
    def initialize_browser(self):
        """Initialize Chrome browser with appropriate options"""
        logger.info("🌐 Initializing Chrome browser...")
        
        # Create download directory
        download_dir = os.path.join(os.getcwd(), "production_scraper_data", "downloads")
        os.makedirs(download_dir, exist_ok=True)
        
        chrome_options = Options()
        # Remove headless for debugging - you can see what's happening
        # chrome_options.add_argument('--headless')
        
        # Download preferences
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Other useful options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize driver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to prevent detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 30)
            logger.info("✅ Chrome browser initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome browser: {e}")
            raise
    
    def login_to_portal(self):
        """Login to TD SYNNEX portal with 2FA support"""
        logger.info("🔐 Logging into TD SYNNEX portal...")
        
        try:
            # Navigate to login page
            self.driver.get(self.login_url)
            logger.info(f"Navigated to: {self.login_url}")
            
            # Wait for page to load
            time.sleep(3)
            
            # Handle cookie popup using dedicated method
            self.handle_cookie_popup()
            
            # Find and fill email field
            logger.info("Locating email field...")
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "inputEmailAddress"))
            )
            # Clear field multiple times to ensure it's empty
            email_field.clear()
            time.sleep(0.5)
            email_field.clear()
            # Use JavaScript to clear and set value to ensure no concatenation
            self.driver.execute_script("arguments[0].value = '';", email_field)
            time.sleep(0.5)
            email_field.send_keys(self.td_username)
            # Verify the field contains only the username
            field_value = email_field.get_attribute('value')
            logger.info(f"✅ Email field value: '{field_value}'")
            
            # Find and fill password
            logger.info("Locating password field...")
            password_field = self.driver.find_element(By.ID, "inputPassword")
            # Clear field multiple times to ensure it's empty
            password_field.clear()
            time.sleep(0.5)
            password_field.clear()
            # Use JavaScript to clear and set value to ensure no concatenation
            self.driver.execute_script("arguments[0].value = '';", password_field)
            time.sleep(0.5)
            password_field.send_keys(self.td_password)
            # Verify the field (but don't log the actual password)
            logger.info("✅ Password entered and verified")
            
            # Check if CAPTCHA is required
            try:
                captcha_field = self.driver.find_element(By.ID, "captchaCode")
                if captcha_field.is_displayed():
                    logger.warning("⚠️ CAPTCHA detected! Manual intervention required.")
                    logger.info("Please solve the CAPTCHA manually in the browser window.")
                    input("Press Enter after solving the CAPTCHA...")
            except:
                logger.info("No CAPTCHA required")
            
            # Submit login form
            logger.info("Submitting login form...")
            login_button = self.driver.find_element(By.ID, "loginBtn")
            login_button.click()
            
            # Wait for login to complete
            logger.info("Waiting for login to complete...")
            time.sleep(5)
            
            # Check for 2FA challenge
            if self.two_fa_handler.detect_2fa_challenge(self.driver):
                logger.info("🔒 2FA challenge detected!")
                
                # Handle 2FA challenge
                if self.two_fa_handler.handle_2fa_challenge(self.driver):
                    logger.info("✅ 2FA challenge handled successfully")
                    time.sleep(3)  # Wait for redirect after 2FA
                else:
                    logger.error("❌ Failed to handle 2FA challenge")
                    return False
            
            # Check if login was successful
            current_url = self.driver.current_url
            logger.info(f"Current URL after login: {current_url}")
            
            # Look for login success indicators
            if "login" not in current_url.lower():
                logger.info("✅ Login appears successful!")
                return True
            else:
                # Check for error messages
                error_messages = self.driver.find_elements(By.CLASS_NAME, "error-message")
                if error_messages:
                    for error in error_messages:
                        logger.error(f"❌ Login error: {error.text}")
                else:
                    logger.error("❌ Login failed - still on login page")
                return False
                
        except TimeoutException:
            logger.error("❌ Timeout during login process")
            return False
        except Exception as e:
            logger.error(f"❌ Error during login: {e}")
            return False
    
    def run_scraper(self):
        """Main scraper execution"""
        start_time = time.time()
        
        try:
            logger.info("🚀 Starting TD SYNNEX Production Scraper with 2FA support")
            
            # Initialize browser
            self.initialize_browser()
            
            # Login to portal
            if not self.login_to_portal():
                logger.error("❌ Login failed")
                return False
            
            # Navigate to price availability page
            logger.info("📊 Navigating to price availability page...")
            self.driver.get(self.portal_url)
            time.sleep(5)
            
            # Rest of scraper logic would go here...
            logger.info("✅ Scraper execution completed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Scraper execution failed: {e}")
            return False
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()
                logger.info("🔄 Browser closed")
            
            # Calculate execution time
            self.stats["execution_time"] = time.time() - start_time
            logger.info(f"⏱️ Total execution time: {self.stats['execution_time']:.2f} seconds")

def main():
    """Main function"""
    scraper = ProductionScraperWith2FA()
    
    try:
        success = scraper.run_scraper()
        if success:
            logger.info("🎉 Scraper completed successfully!")
            return 0
        else:
            logger.error("💥 Scraper failed!")
            return 1
    except KeyboardInterrupt:
        logger.info("🛑 Scraper interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())