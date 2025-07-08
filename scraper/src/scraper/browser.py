"""
TD SYNNEX Browser automation using Selenium
"""

import asyncio
import logging
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class TDSynnexBrowser:
    """Browser automation for TD SYNNEX portal"""
    
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.wait = None
    
    async def initialize(self):
        """Initialize the browser with appropriate options"""
        # Create download directory
        download_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(download_dir, exist_ok=True)
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Configure download settings
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            # Use webdriver-manager to automatically download and manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("Browser initialized successfully")
            logger.info(f"Downloads will be saved to: {download_dir}")
        except WebDriverException as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    def handle_cookie_popup(self):
        """Handle cookie consent popup if present"""
        logger.info("Checking for cookie popup...")
        
        # List of known cookie consent button selectors
        cookie_selectors = [
            ("ID", "onetrust-accept-btn-handler", "Accept All Cookies"),
            ("CSS", "#onetrust-accept-btn-handler", "Accept All (CSS)"),
            ("CSS", ".save-preference-btn-handler", "Save Preferences"),
            ("XPATH", "//button[contains(text(), 'Accept All')]", "Accept All Text"),
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
                        logger.info(f"Accepted cookies: {description}")
                        time.sleep(3)  # Wait for popup to disappear
                        return True
                        
                except Exception:
                    continue
            
            time.sleep(1)  # Wait 1 second before next attempt
        
        logger.info("No cookie popup detected or already handled")
        return False
    
    async def login(self):
        """Authenticate with TD SYNNEX portal"""
        try:
            # Navigate to login page
            login_url = "https://ec.synnex.com/ecx/login.html"
            self.driver.get(login_url)
            logger.info(f"Navigated to: {login_url}")
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Handle cookie popup
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
            email_field.send_keys(self.config.TDSYNNEX_USERNAME)
            logger.info("Email entered successfully")
            
            # Find and fill password
            logger.info("Locating password field...")
            password_field = self.driver.find_element(By.ID, "inputPassword")
            password_field.clear()
            time.sleep(0.5)
            password_field.clear()
            self.driver.execute_script("arguments[0].value = '';", password_field)
            time.sleep(0.5)
            password_field.send_keys(self.config.TDSYNNEX_PASSWORD)
            logger.info("Password entered successfully")
            
            # Submit login form
            logger.info("Submitting login form...")
            login_button = self.driver.find_element(By.ID, "loginBtn")
            login_button.click()
            
            # Wait for login to complete
            logger.info("Waiting for login to complete...")
            await asyncio.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            logger.info(f"Current URL after login: {current_url}")
            
            if "login" not in current_url.lower():
                logger.info("Login successful!")
                return True
            else:
                logger.error("Login failed - still on login page")
                return False
                
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
            portal_url = "https://ec.synnex.com/ecx/eServices/priceAvailabilityDownload.html"
            self.driver.get(portal_url)
            logger.info(f"Navigated to: {portal_url}")
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Check if we're on the right page
            page_title = self.driver.title
            logger.info(f"Page title: {page_title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            return False
    
    async def request_download(self):
        """Submit the download request"""
        try:
            logger.info("Looking for download button...")
            
            # Use the specific download button selector
            download_selectors = [
                ("XPATH", "//button[@onclick='javascript:submitForm(false);']", "Download button with submitForm"),
                ("CSS", "button.button-main.button-big", "Download button with main/big classes"),
                ("XPATH", "//button[.//span[text()='Download']]", "Download button by span text"),
            ]
            
            download_button = None
            for selector_type, selector, description in download_selectors:
                try:
                    if selector_type == "CSS":
                        download_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        download_button = self.driver.find_element(By.XPATH, selector)
                    
                    if download_button and download_button.is_displayed():
                        logger.info(f"Found download button: {description}")
                        break
                        
                except Exception:
                    continue
            
            if not download_button:
                logger.error("Could not find download button")
                return False
            
            # Click the download button
            try:
                download_button.click()
                logger.info("Clicked download button")
            except:
                # Try JavaScript click if regular click fails
                self.driver.execute_script("arguments[0].click();", download_button)
                logger.info("Clicked download button (JavaScript)")
            
            # Wait for popup to appear
            await asyncio.sleep(2)
            
            # Handle the download confirmation popup
            logger.info("Looking for 'Download Price and Availability' confirmation popup...")
            
            # First check for popup content to confirm it's the right dialog
            popup_content_found = False
            try:
                # Look for the specific popup content
                popup_content_selectors = [
                    ("XPATH", "//*[contains(text(), 'Download Price and Availability')]", "Download Price and Availability text"),
                    ("XPATH", "//*[contains(text(), 'This file will include up to')]", "File include count text"),
                    ("XPATH", "//*[contains(text(), 'email will be sent to')]", "Email notification text"),
                ]
                
                for selector_type, selector, description in popup_content_selectors:
                    try:
                        if selector_type == "XPATH":
                            popup_element = self.driver.find_element(By.XPATH, selector)
                        
                        if popup_element and popup_element.is_displayed():
                            logger.info(f"Found popup content: {description}")
                            logger.info(f"   Content: {popup_element.text[:100]}...")
                            popup_content_found = True
                            break
                            
                    except Exception as e:
                        logger.debug(f"Popup content selector failed ({description}): {e}")
                        continue
                
                if popup_content_found:
                    logger.info("Confirmed 'Download Price and Availability' popup is displayed")
                else:
                    logger.info("Popup content not found, but continuing to look for OK button")
                    
            except Exception as e:
                logger.debug(f"Error checking popup content: {e}")
            
            ok_button_selectors = [
                ("ID", "downloadFromEc", "Download From EC button (primary)"),
                ("CSS", "button[onclick*='downloadFromEc']", "Download button with onclick function"),
                ("CSS", "#downloadFromEc", "Download From EC ID selector"),
                ("CSS", ".button-main.button-big", "Main big button class"),
                ("XPATH", "//button[@id='downloadFromEc']", "Download From EC XPath"),
                ("XPATH", "//button[contains(@onclick, 'downloadFromEc')]", "Button with downloadFromEc onclick"),
                ("XPATH", "//button[contains(@class, 'button-main') and contains(text(), 'OK')]", "Main button with OK text"),
                ("XPATH", "//button[text()='OK']", "OK button text"),
                ("XPATH", "//button[contains(text(), 'OK')]", "OK button contains text"),
                ("XPATH", "//div[contains(@class, 'ui-dialog')]//button[contains(text(), 'OK')]", "OK button in ui-dialog"),
            ]
            
            ok_button_found = False
            for selector_type, selector, description in ok_button_selectors:
                try:
                    if selector_type == "CSS":
                        ok_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        ok_button = self.driver.find_element(By.XPATH, selector)
                    elif selector_type == "ID":
                        ok_button = self.driver.find_element(By.ID, selector)
                    
                    if ok_button and ok_button.is_displayed():
                        logger.info(f"Found OK button in popup: {description}")
                        logger.info(f"   Button text: '{ok_button.text}'")
                        
                        try:
                            ok_button.click()
                            logger.info("Clicked OK button in popup")
                        except:
                            self.driver.execute_script("arguments[0].click();", ok_button)
                            logger.info("Clicked OK button in popup (JavaScript)")
                        
                        ok_button_found = True
                        break
                        
                except Exception as e:
                    logger.debug(f"OK button selector failed ({description}): {e}")
                    continue
            
            if not ok_button_found:
                logger.warning("Could not find OK button in popup - download may have started anyway")
                # Save page source for debugging
                try:
                    page_source = self.driver.page_source
                    with open("debug_popup_page.html", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    logger.info("Saved page source to debug_popup_page.html for popup analysis")
                except:
                    pass
            
            # Wait for download to process
            logger.info("Waiting for download to process...")
            await asyncio.sleep(5)
            
            logger.info("Download request submitted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Download request failed: {str(e)}")
            return False
    
    async def close(self):
        """Clean up browser resources"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")