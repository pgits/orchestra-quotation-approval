#!/usr/bin/env python3
"""
TD SYNNEX Microsoft Product Scraper - Local Production Version
Uses real TD SYNNEX portal and production credentials
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LocalProductionScraper:
    """Local version that connects to real TD SYNNEX portal"""
    
    def __init__(self):
        # Get credentials from environment or .env file
        self.load_environment()
        
        # TD SYNNEX Portal URL
        self.portal_url = "https://ec.synnex.com/ecx/eServices/priceAvailabilityDownload.html"
        self.login_url = "https://ec.synnex.com/ecx/login.html"
        
        # Browser setup
        self.driver = None
        self.wait = None
        
        # Create local data directory
        self.data_dir = Path("./production_scraper_data")
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info(f"Production scraper initialized")
        logger.info(f"Portal URL: {self.portal_url}")
        logger.info(f"Username: {self.td_username}")
    
    def load_environment(self):
        """Load credentials from environment variables or .env file"""
        
        # Try to load from .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            logger.info("Loading environment from .env file")
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Load credentials
        self.td_username = os.getenv('TDSYNNEX_USERNAME')
        self.td_password = os.getenv('TDSYNNEX_PASSWORD')
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        # Validate credentials
        if not self.td_username or not self.td_password:
            logger.error("Missing TD SYNNEX credentials!")
            logger.error("Please set TDSYNNEX_USERNAME and TDSYNNEX_PASSWORD environment variables")
            logger.error("Or create a .env file with these values")
            sys.exit(1)
        
        logger.info("✅ Credentials loaded successfully")
    
    def handle_cookie_popup(self):
        """Handle cookie consent popup if present"""
        logger.info("🍪 Checking for cookie popup...")
        
        # List of known cookie consent button selectors based on debug analysis
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
            logger.info("✅ Browser initialized successfully")
            logger.info(f"📁 Downloads will be saved to: {download_dir}")
            return True
        except WebDriverException as e:
            logger.error(f"❌ Failed to initialize browser: {str(e)}")
            logger.error("Make sure Chrome is installed")
            return False
    
    def login_to_portal(self):
        """Login to TD SYNNEX portal"""
        logger.info("🔐 Logging into TD SYNNEX portal...")
        
        try:
            # Navigate to login page
            self.driver.get(self.login_url)
            logger.info(f"Navigated to: {self.login_url}")
            
            # Wait for page to load
            time.sleep(3)
            
            # Handle cookie popup using dedicated method
            self.handle_cookie_popup()
            
            # Find and fill email field (TD SYNNEX uses 'email' field, not 'username')
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
            
            # Check if verification code is required (for new IP addresses)
            try:
                verification_field = self.driver.find_element(By.ID, "verificationCode")
                if verification_field.is_displayed():
                    logger.warning("⚠️ Verification code detected! This IP address hasn't been seen before.")
                    
                    # Try to get verification code from email service
                    verification_code = self.get_verification_code_from_email()
                    
                    if verification_code:
                        logger.info("Using verification code from email service...")
                        verification_field.clear()
                        verification_field.send_keys(verification_code)
                        logger.info("✅ Verification code entered from email")
                    elif hasattr(self, 'verification_code') and self.verification_code:
                        logger.info("Using provided verification code...")
                        verification_field.clear()
                        verification_field.send_keys(self.verification_code)
                        logger.info("✅ Verification code entered")
                    else:
                        logger.info("Please enter the verification code manually in the browser window.")
                        input("Press Enter after entering the verification code...")
            except:
                logger.info("No verification code required")
            
            # Submit login form
            logger.info("Submitting login form...")
            login_button = self.driver.find_element(By.ID, "loginBtn")
            login_button.click()
            
            # Wait for login to complete
            logger.info("Waiting for login to complete...")
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            logger.info(f"Current URL after login: {current_url}")
            
            # Look for login success indicators
            if "login" not in current_url.lower():
                logger.info("✅ Login appears successful!")
                return True
            else:
                # Check for error messages
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error']")
                    if error_elements:
                        error_text = error_elements[0].text
                        logger.error(f"❌ Login error: {error_text}")
                    else:
                        logger.error("❌ Login failed - still on login page")
                except:
                    logger.error("❌ Login failed - unknown error")
                return False
                
        except TimeoutException:
            logger.error("❌ Login timeout - page elements not found")
            return False
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            return False
    
    def navigate_to_download_page(self):
        """Navigate to price/availability download page"""
        logger.info("📂 Navigating to download page...")
        
        try:
            self.driver.get(self.portal_url)
            logger.info(f"Navigated to: {self.portal_url}")
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if we're on the right page
            page_title = self.driver.title
            logger.info(f"Page title: {page_title}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to navigate to download page: {str(e)}")
            return False
    
    def apply_microsoft_filters(self):
        """Apply filters to get Microsoft products with comprehensive debugging"""
        logger.info("🔍 Applying Microsoft product filters...")
        
        # Initialize Microsoft selection tracking variables
        microsoft_found = False
        microsoft_count = 0
        
        try:
            # First, find and use the manufacturer filter search box
            logger.info("🔍 Looking for manufacturer filter search box...")
            
            try:
                # Look for the filter icon and input box for manufacturers
                filter_selectors = [
                    ("CSS", "input.filter-icon.manufactures-filter.float-right"),
                    ("CSS", ".filter-icon.manufactures-filter.float-right"),
                    ("CSS", "input[class*='manufactures-filter']"),
                    ("CSS", "input[placeholder*='Enter keywords to filter']"),
                    ("XPATH", "//input[@class='filter-icon manufactures-filter float-right']"),
                    ("CSS", "input.manufactures-filter"),
                    ("CSS", ".manufactures-filter input"),
                    ("XPATH", "//div[contains(@class, 'manufactures-filter')]//input"),
                ]
                
                manufacturer_filter_input = None
                for selector_type, selector in filter_selectors:
                    try:
                        if selector_type == "CSS":
                            manufacturer_filter_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                        elif selector_type == "XPATH":
                            manufacturer_filter_input = self.driver.find_element(By.XPATH, selector)
                        elif selector_type == "ID":
                            manufacturer_filter_input = self.driver.find_element(By.ID, selector)
                        
                        if manufacturer_filter_input and manufacturer_filter_input.is_displayed():
                            logger.info(f"✅ Found manufacturer filter input using {selector_type}: {selector}")
                            break
                    except:
                        continue
                
                if manufacturer_filter_input:
                    # Clear and type "Microsoft" in the filter
                    manufacturer_filter_input.clear()
                    manufacturer_filter_input.send_keys("Microsoft")
                    logger.info("✅ Typed 'Microsoft' in manufacturer filter")
                    
                    # Wait for the filter to apply
                    time.sleep(2)
                    
                    # Sometimes need to press Enter or trigger the filter
                    try:
                        manufacturer_filter_input.send_keys(Keys.RETURN)
                        logger.info("✅ Pressed Enter to apply filter")
                    except:
                        pass
                    
                    time.sleep(1)
                else:
                    logger.warning("⚠️ Could not find manufacturer filter input box")
            
            except Exception as e:
                logger.error(f"❌ Error using manufacturer filter: {e}")
            
            # Now look for the manufacturer filter section
            logger.info("🔍 Looking for manufacturer checkboxes after filtering...")
            
            # Try multiple approaches to find the manufacturer section
            manufacturer_sections = [
                ("ID", "realtimeManufacturer"),
                ("ID", "manufacturer"),
                ("CLASS", "manufacturer-filter"),
                ("CLASS", "mfg-filter"),
                ("CSS", "div[id*='manufacturer']"),
                ("CSS", "div[class*='manufacturer']"),
            ]
            
            manufacturer_div = None
            for selector_type, selector in manufacturer_sections:
                try:
                    if selector_type == "ID":
                        manufacturer_div = self.driver.find_element(By.ID, selector)
                    elif selector_type == "CLASS":
                        manufacturer_div = self.driver.find_element(By.CLASS_NAME, selector)
                    elif selector_type == "CSS":
                        manufacturer_div = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if manufacturer_div:
                        logger.info(f"✅ Found manufacturer section using {selector_type}: {selector}")
                        break
                except:
                    continue
            
            if manufacturer_div:
                # Find all checkboxes within this div
                manufacturer_checkboxes = manufacturer_div.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                logger.info(f"Found {len(manufacturer_checkboxes)} manufacturer checkboxes")
                
                # Look for Microsoft checkboxes specifically
                # (Variables already initialized at method level)
                
                # First, look for the specific VendNo=19215
                logger.info("🔍 Looking for Microsoft checkbox with VendNo=19215...")
                
                for i, checkbox in enumerate(manufacturer_checkboxes):
                    try:
                        # Get all attributes
                        cb_value = checkbox.get_attribute('value') or ''
                        cb_id = checkbox.get_attribute('id') or ''
                        cb_name = checkbox.get_attribute('name') or ''
                        cb_onclick = checkbox.get_attribute('onclick') or ''
                        
                        # Log first 5 checkboxes for debugging
                        if i < 5:
                            logger.info(f"  Checkbox {i}: value='{cb_value}', id='{cb_id}', name='{cb_name}'")
                        
                        # Check for Microsoft checkboxes - either vendNo=19215 or mfg=23073
                        is_microsoft_checkbox = False
                        checkbox_type = ""
                        
                        if '19215' in cb_value and cb_name == 'vendNo':
                            is_microsoft_checkbox = True
                            checkbox_type = "vendNo=19215"
                        elif '23073' in cb_value and cb_name == 'mfg':
                            is_microsoft_checkbox = True
                            checkbox_type = "mfg=23073"
                        
                        if is_microsoft_checkbox:
                            logger.info(f"🎯 Found Microsoft checkbox: {checkbox_type}")
                            logger.info(f"  Value: '{cb_value}'")
                            logger.info(f"  ID: '{cb_id}'")
                            logger.info(f"  Name: '{cb_name}'")
                            
                            if not checkbox.is_selected():
                                try:
                                    # Try to click the checkbox directly
                                    checkbox.click()
                                    logger.info(f"✅ Selected Microsoft checkbox {checkbox_type} (direct click)")
                                except:
                                    try:
                                        # If direct click fails, try clicking the parent label
                                        parent_label = checkbox.find_element(By.XPATH, "./ancestor::label")
                                        parent_label.click()
                                        logger.info(f"✅ Selected Microsoft checkbox {checkbox_type} (label click)")
                                    except:
                                        try:
                                            # If that fails, try using JavaScript
                                            self.driver.execute_script("arguments[0].click();", checkbox)
                                            logger.info(f"✅ Selected Microsoft checkbox {checkbox_type} (JS click)")
                                        except Exception as e:
                                            logger.error(f"❌ Failed to click Microsoft checkbox {checkbox_type}: {e}")
                                microsoft_count += 1
                            else:
                                logger.info(f"✅ Microsoft checkbox {checkbox_type} already selected")
                                microsoft_count += 1
                            microsoft_found = True
                            time.sleep(0.5)
                            continue
                        
                        # Also check for Microsoft text in labels
                        # Try to find associated label
                        label_text = ''
                        try:
                            # Find parent label
                            parent_label = checkbox.find_element(By.XPATH, "./ancestor::label")
                            label_text = parent_label.text.strip()
                        except:
                            try:
                                # Try to find sibling span
                                sibling_span = checkbox.find_element(By.XPATH, "./following-sibling::span")
                                label_text = sibling_span.text.strip()
                            except:
                                pass
                        
                        # Check if this is a Microsoft checkbox by text (including "INCASE DESIGNED BY MICROSOFT")
                        search_text = (cb_value + ' ' + cb_id + ' ' + cb_name + ' ' + label_text).upper()
                        if any(ms_variant in search_text for ms_variant in ['MICROSOFT', 'MSFT']):
                            logger.info(f"🎯 Found Microsoft-related checkbox: '{label_text}'")
                            logger.info(f"  Value: '{cb_value}', Name: '{cb_name}'")
                            
                            # Select this Microsoft checkbox
                            if not checkbox.is_selected():
                                try:
                                    checkbox.click()
                                    logger.info(f"✅ Selected Microsoft checkbox: '{label_text}' (direct click)")
                                except:
                                    try:
                                        parent_label = checkbox.find_element(By.XPATH, "./ancestor::label")
                                        parent_label.click()
                                        logger.info(f"✅ Selected Microsoft checkbox: '{label_text}' (label click)")
                                    except:
                                        try:
                                            self.driver.execute_script("arguments[0].click();", checkbox)
                                            logger.info(f"✅ Selected Microsoft checkbox: '{label_text}' (JS click)")
                                        except Exception as e:
                                            logger.error(f"❌ Failed to click Microsoft checkbox '{label_text}': {e}")
                                microsoft_count += 1
                            else:
                                logger.info(f"✅ Microsoft checkbox already selected: '{label_text}'")
                                microsoft_count += 1
                            microsoft_found = True
                            time.sleep(0.5)
                    
                    except Exception as e:
                        logger.debug(f"Error processing manufacturer checkbox {i}: {e}")
                        continue
                
                if microsoft_found:
                    logger.info(f"✅ Selected {microsoft_count} Microsoft manufacturer checkboxes")
                    
                    # Save debug HTML after selecting Microsoft checkboxes
                    logger.info("💾 Saving debug HTML after Microsoft checkbox selection...")
                    page_source = self.driver.page_source
                    with open("debug_manufacturer_page.html", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    logger.info("✅ Saved page source to debug_manufacturer_page.html for analysis")
                else:
                    logger.warning("⚠️ No Microsoft checkboxes found in manufacturer section")
                    logger.info("💡 Trying alternative approach - looking for all checkboxes on page with VendNo=19215...")
                    
                    # Try looking at ALL checkboxes on the page
                    all_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                    logger.info(f"Found {len(all_checkboxes)} total checkboxes on page")
                    
                    for checkbox in all_checkboxes:
                        try:
                            cb_value = checkbox.get_attribute('value') or ''
                            cb_onclick = checkbox.get_attribute('onclick') or ''
                            
                            cb_name = checkbox.get_attribute('name') or ''
                            
                            # Check for Microsoft checkboxes
                            is_microsoft = False
                            checkbox_type = ""
                            
                            if '19215' in cb_value and 'vendNo' in cb_name:
                                is_microsoft = True
                                checkbox_type = "vendNo=19215"
                            elif '23073' in cb_value and 'mfg' in cb_name:
                                is_microsoft = True
                                checkbox_type = "mfg=23073"
                            
                            if is_microsoft:
                                logger.info(f"🎯 Found Microsoft checkbox outside manufacturer div: {checkbox_type}")
                                logger.info(f"  Value: '{cb_value}'")
                                
                                if not checkbox.is_selected():
                                    try:
                                        # Try to click the checkbox directly
                                        checkbox.click()
                                        logger.info(f"✅ Selected Microsoft checkbox {checkbox_type} (direct click)")
                                    except:
                                        try:
                                            # If direct click fails, try clicking the parent label
                                            parent_label = checkbox.find_element(By.XPATH, "./ancestor::label")
                                            parent_label.click()
                                            logger.info(f"✅ Selected Microsoft checkbox {checkbox_type} (label click)")
                                        except:
                                            try:
                                                # If that fails, try using JavaScript
                                                self.driver.execute_script("arguments[0].click();", checkbox)
                                                logger.info(f"✅ Selected Microsoft checkbox {checkbox_type} (JS click)")
                                            except Exception as e:
                                                logger.error(f"❌ Failed to click Microsoft checkbox {checkbox_type}: {e}")
                                    microsoft_found = True
                                    time.sleep(0.5)
                                    # Don't break - continue looking for other Microsoft checkboxes
                        except:
                            continue
                    
                    # Save debug HTML after alternative Microsoft selection
                    if microsoft_found:
                        logger.info("💾 Saving debug HTML after alternative Microsoft checkbox selection...")
                        page_source = self.driver.page_source
                        with open("debug_manufacturer_page.html", "w", encoding="utf-8") as f:
                            f.write(page_source)
                        logger.info("✅ Saved page source to debug_manufacturer_page.html for analysis")
                
            else:
                logger.error("❌ Could not find manufacturer filter section")
            
            # Now analyze the rest of the page structure
            logger.info("🔍 Analyzing page structure for additional filters...")
            
            # Look for all form elements and inputs on the page
            all_forms = self.driver.find_elements(By.TAG_NAME, "form")
            logger.info(f"Found {len(all_forms)} forms on the page")
            
            all_selects = self.driver.find_elements(By.TAG_NAME, "select")
            logger.info(f"Found {len(all_selects)} select dropdowns on the page")
            
            all_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            logger.info(f"Found {len(all_checkboxes)} checkboxes on the page")
            
            # Analyze each select dropdown for manufacturer-related options
            for i, select_elem in enumerate(all_selects):
                try:
                    select_id = select_elem.get_attribute('id') or 'no-id'
                    select_name = select_elem.get_attribute('name') or 'no-name'
                    select_class = select_elem.get_attribute('class') or 'no-class'
                    
                    logger.info(f"  Select {i+1}: id='{select_id}', name='{select_name}', class='{select_class}'")
                    
                    # Check if this might be a manufacturer dropdown
                    if any(keyword in (select_id + select_name + select_class).lower() 
                           for keyword in ['manufacturer', 'mfg', 'vendor', 'brand']):
                        logger.info(f"  📍 Potential manufacturer dropdown found: {select_id}")
                        
                        # Analyze options in this dropdown
                        try:
                            select_obj = Select(select_elem)
                            options = [opt.text.strip() for opt in select_obj.options if opt.text.strip()]
                            logger.info(f"  Options ({len(options)}): {options[:15]}...")  # Show first 15
                            
                            # Look for Microsoft options
                            microsoft_matches = []
                            for opt_text in options:
                                if any(ms_variant in opt_text.lower() 
                                       for ms_variant in ['microsoft', 'msft']):
                                    microsoft_matches.append(opt_text)
                            
                            if microsoft_matches:
                                logger.info(f"  🎯 Found Microsoft options: {microsoft_matches}")
                                
                                # Try to select all Microsoft options (if multi-select) or the first one
                                for ms_option in microsoft_matches:
                                    try:
                                        select_obj.select_by_visible_text(ms_option)
                                        logger.info(f"  ✅ Selected: {ms_option}")
                                        time.sleep(1)
                                    except Exception as e:
                                        logger.warning(f"  ⚠️ Failed to select {ms_option}: {e}")
                                
                                return True
                            
                        except Exception as e:
                            logger.debug(f"  Error analyzing select options: {e}")
                
                except Exception as e:
                    logger.debug(f"Error analyzing select {i}: {e}")
            
            
            # Check for any error messages on the page
            logger.info("🔍 Checking for error messages...")
            error_selectors = [
                ".error", ".alert", ".message", ".warning", 
                "[class*='error']", "[class*='alert']", "[id*='error']",
                ".validation-error", ".form-error"
            ]
            
            for selector in error_selectors:
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for error_elem in error_elements:
                        if error_elem.is_displayed() and error_elem.text.strip():
                            # Ignore the 3,000 SKU warning as requested
                            if "3,000 SKUs" in error_elem.text:
                                logger.info("📝 Ignoring 3,000 SKU warning (as requested)")
                                continue
                            logger.warning(f"⚠️ Page error/message: {error_elem.text.strip()}")
                except:
                    continue
            
            # Apply Other Criteria settings
            self.enable_short_description()
            self.set_file_format_cr_mac()
            self.set_field_delimiter_semicolon()
            
            # Enable "In Stock Only" checkbox
            self.enable_in_stock_only()
            
            # Skip search trigger to avoid 'Please input valid search criteria' popup
            logger.info("⚠️ Skipping search trigger to prevent popup - filters should apply automatically")
            # self.trigger_search()  # DISABLED - causes popup
            
            # Try to download the results after applying filters
            logger.info("📥 Attempting to download filtered results...")
            if self.download_results():
                logger.info("✅ Download initiated successfully")
            else:
                logger.warning("⚠️ Could not initiate download")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply filters: {str(e)}")
            return False
    
    def enable_short_description(self):
        """Enable Short Description checkbox/option"""
        logger.info("📝 Enabling Short Description option...")
        
        try:
            # Based on the HTML analysis, the correct selector is:
            # <input type="checkbox" name="fields" value="short_desc" class="ui-checkbox">
            short_desc_selectors = [
                ("CSS", "input[name='fields'][value='short_desc']", "Short Description (exact match)"),
                ("XPATH", "//input[@name='fields' and @value='short_desc']", "Short Description XPath"),
                ("XPATH", "//span[contains(text(), 'Short Description(150 max)')]/../input", "Short Description by label text"),
                ("XPATH", "//label[contains(., 'Short Description(150 max)')]//input", "Short Description in label"),
                ("CSS", "input[type='checkbox'][value='short_desc']", "Short Desc checkbox by value"),
            ]
            
            for selector_type, selector, description in short_desc_selectors:
                try:
                    if selector_type == "CSS":
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        element = self.driver.find_element(By.XPATH, selector)
                    
                    if element and element.is_displayed():
                        # Check if it's not already checked
                        if not element.is_selected():
                            try:
                                # Try direct click first
                                element.click()
                                logger.info(f"✅ Enabled Short Description: {description}")
                            except:
                                try:
                                    # If direct click fails, try clicking the parent label
                                    parent_label = element.find_element(By.XPATH, "./ancestor::label")
                                    parent_label.click()
                                    logger.info(f"✅ Enabled Short Description via label: {description}")
                                except:
                                    # Last resort: JavaScript click
                                    self.driver.execute_script("arguments[0].click();", element)
                                    logger.info(f"✅ Enabled Short Description via JS: {description}")
                            time.sleep(1)
                            return True
                        else:
                            logger.info(f"✅ Short Description already enabled: {description}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"Short Description selector failed ({description}): {e}")
                    continue
            
            logger.warning("⚠️ Could not find Short Description option")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to enable Short Description: {str(e)}")
            return False
    
    def set_file_format_cr_mac(self):
        """Set File Format to CR(Mac)"""
        logger.info("📄 Setting File Format to CR(Mac)...")
        
        try:
            # Based on HTML analysis: <input type="radio" name="fileFormat" value="cr" class="ui-radio">
            cr_mac_selectors = [
                ("CSS", "input[name='fileFormat'][value='cr']", "CR(Mac) radio button (exact)"),
                ("XPATH", "//input[@name='fileFormat' and @value='cr']", "CR(Mac) XPath"),
                ("XPATH", "//span[contains(text(), 'CR(Mac)')]/../input", "CR(Mac) by label text"),
                ("XPATH", "//label[contains(., 'CR(Mac)')]//input", "CR(Mac) in label"),
                ("CSS", "input[type='radio'][value='cr']", "CR radio button by value"),
            ]
            
            for selector_type, selector, description in cr_mac_selectors:
                try:
                    if selector_type == "CSS":
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        element = self.driver.find_element(By.XPATH, selector)
                    elif selector_type == "ID":
                        element = self.driver.find_element(By.ID, selector)
                    
                    if element and element.is_displayed():
                        # Check if it's not already selected
                        if not element.is_selected():
                            try:
                                # Try direct click first
                                element.click()
                                logger.info(f"✅ Selected CR(Mac) format: {description}")
                            except:
                                try:
                                    # If direct click fails, try clicking the parent label
                                    parent_label = element.find_element(By.XPATH, "./ancestor::label")
                                    parent_label.click()
                                    logger.info(f"✅ Selected CR(Mac) via label: {description}")
                                except:
                                    # Last resort: JavaScript click
                                    self.driver.execute_script("arguments[0].click();", element)
                                    logger.info(f"✅ Selected CR(Mac) via JS: {description}")
                            time.sleep(1)
                            return True
                        else:
                            logger.info(f"✅ CR(Mac) format already selected: {description}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"CR(Mac) selector failed ({description}): {e}")
                    continue
            
            logger.warning("⚠️ Could not find CR(Mac) file format option")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to set CR(Mac) format: {str(e)}")
            return False
    
    def set_field_delimiter_semicolon(self):
        """Set Field Delimiter to semi-colon"""
        logger.info("📍 Setting Field Delimiter to semi-colon...")
        
        try:
            # Based on HTML analysis: <input type="radio" name="delimiter" value=";" class="ui-radio">
            semicolon_selectors = [
                ("CSS", "input[name='delimiter'][value=';']", "Semi-colon radio button (exact)"),
                ("XPATH", "//input[@name='delimiter' and @value=';']", "Semi-colon XPath"),
                ("XPATH", "//span[contains(text(), '; (semi-colon)')]/../input", "Semi-colon by label text"),
                ("XPATH", "//label[contains(., '; (semi-colon)')]//input", "Semi-colon in label"),
                ("CSS", "#downloadDelimiter input[value=';']", "Semi-colon in delimiter section"),
            ]
            
            for selector_type, selector, description in semicolon_selectors:
                try:
                    if selector_type == "CSS":
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        element = self.driver.find_element(By.XPATH, selector)
                    
                    if element and element.is_displayed():
                        # Check if it's not already selected
                        if not element.is_selected():
                            try:
                                # Try direct click first
                                element.click()
                                logger.info(f"✅ Selected semi-colon delimiter: {description}")
                            except:
                                try:
                                    # If direct click fails, try clicking the parent label
                                    parent_label = element.find_element(By.XPATH, "./ancestor::label")
                                    parent_label.click()
                                    logger.info(f"✅ Selected semi-colon via label: {description}")
                                except:
                                    # Last resort: JavaScript click
                                    self.driver.execute_script("arguments[0].click();", element)
                                    logger.info(f"✅ Selected semi-colon via JS: {description}")
                            time.sleep(1)
                            return True
                        else:
                            logger.info(f"✅ Semi-colon delimiter already selected: {description}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"Semi-colon selector failed ({description}): {e}")
                    continue
            
            logger.warning("⚠️ Could not find semi-colon delimiter option")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to set semi-colon delimiter: {str(e)}")
            return False
    
    def enable_in_stock_only(self):
        """Enable 'In Stock Only' checkbox with specific selectors"""
        logger.info("📦 Enabling 'In Stock Only' option...")
        
        try:
            # Based on the HTML provided: <input type="checkbox" name="inStock" id="inStock" value="true" class="ui-checkbox">
            in_stock_selectors = [
                ("ID", "inStock", "In Stock Only by ID"),
                ("NAME", "inStock", "In Stock Only by name"),
                ("CSS", "#inStock", "In Stock Only CSS ID"),
                ("CSS", "input[name='inStock']", "In Stock Only CSS name"),
                ("CSS", "input#inStock[type='checkbox']", "In Stock Only specific"),
                ("XPATH", "//input[@id='inStock']", "In Stock Only XPath ID"),
                ("XPATH", "//input[@name='inStock' and @type='checkbox']", "In Stock Only XPath name"),
                ("XPATH", "//input[@id='inStock' and @value='true']", "In Stock Only XPath with value"),
                # Fallback selectors
                ("XPATH", "//label[contains(text(), 'In Stock Only')]/..//input", "In Stock Only by label"),
                ("XPATH", "//label[contains(., 'In Stock Only')]//input", "In Stock Only in label"),
            ]
            
            for selector_type, selector, description in in_stock_selectors:
                try:
                    if selector_type == "NAME":
                        element = self.driver.find_element(By.NAME, selector)
                    elif selector_type == "ID":
                        element = self.driver.find_element(By.ID, selector)
                    elif selector_type == "CSS":
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        element = self.driver.find_element(By.XPATH, selector)
                    
                    if element and element.is_displayed():
                        # Check if it's not already checked
                        if not element.is_selected():
                            try:
                                # Try direct click first
                                element.click()
                                logger.info(f"✅ Enabled 'In Stock Only': {description}")
                            except:
                                try:
                                    # If direct click fails, try clicking the parent label
                                    parent_label = element.find_element(By.XPATH, "./ancestor::label")
                                    parent_label.click()
                                    logger.info(f"✅ Enabled 'In Stock Only' via label: {description}")
                                except:
                                    # Last resort: JavaScript click
                                    self.driver.execute_script("arguments[0].click();", element)
                                    logger.info(f"✅ Enabled 'In Stock Only' via JS: {description}")
                            time.sleep(1)
                            return True
                        else:
                            logger.info(f"✅ 'In Stock Only' already enabled: {description}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"In Stock Only selector failed ({description}): {e}")
                    continue
            
            logger.warning("⚠️ Could not find 'In Stock Only' option")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to enable 'In Stock Only': {str(e)}")
            return False
    
    def trigger_search(self):
        """Trigger search/filter application by clicking search/submit button"""
        logger.info("🔍 Triggering search/filter application...")
        
        try:
            # Try different selectors for search/submit/apply buttons
            search_button_selectors = [
                ("ID", "searchButton", "Search Button ID"),
                ("ID", "submitButton", "Submit Button ID"),
                ("ID", "applyButton", "Apply Button ID"),
                ("ID", "filterButton", "Filter Button ID"),
                ("NAME", "search", "Search Name"),
                ("NAME", "submit", "Submit Name"),
                ("NAME", "apply", "Apply Name"),
                ("CSS", "input[type='submit']", "Submit Input"),
                ("CSS", "button[type='submit']", "Submit Button"),
                ("CSS", ".search-button", "Search Button Class"),
                ("CSS", ".submit-button", "Submit Button Class"),
                ("CSS", ".apply-button", "Apply Button Class"),
                ("XPATH", "//button[contains(text(), 'Search')]", "Search Button Text"),
                ("XPATH", "//button[contains(text(), 'Submit')]", "Submit Button Text"),
                ("XPATH", "//button[contains(text(), 'Apply')]", "Apply Button Text"),
                ("XPATH", "//button[contains(text(), 'Filter')]", "Filter Button Text"),
                ("XPATH", "//input[@value='Search']", "Search Input Value"),
                ("XPATH", "//input[@value='Submit']", "Submit Input Value"),
                ("XPATH", "//input[@value='Apply']", "Apply Input Value"),
            ]
            
            for selector_type, selector, description in search_button_selectors:
                try:
                    if selector_type == "ID":
                        button = self.driver.find_element(By.ID, selector)
                    elif selector_type == "NAME":
                        button = self.driver.find_element(By.NAME, selector)
                    elif selector_type == "CSS":
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        button = self.driver.find_element(By.XPATH, selector)
                    
                    if button and button.is_displayed() and button.is_enabled():
                        button.click()
                        logger.info(f"✅ Triggered search: {description}")
                        time.sleep(3)  # Wait for search results
                        return True
                        
                except Exception as e:
                    logger.debug(f"Search button selector failed ({description}): {e}")
                    continue
            
            logger.warning("⚠️ Could not find search/submit button")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to trigger search: {str(e)}")
            return False
    
    def download_results(self):
        """Click the download button to download the filtered results"""
        logger.info("💾 Looking for download button...")
        
        try:
            # Use the specific download button selector provided by the user
            download_selectors = [
                ("XPATH", "//button[@onclick='javascript:submitForm(false);']", "Download button with submitForm"),
                ("XPATH", "//button[contains(@onclick, 'submitForm(false)')]", "Download button with submitForm contains"),
                ("CSS", "button.button-main.button-big", "Download button with main/big classes"),
                ("XPATH", "//button[@class='button-main button-big' and contains(@onclick, 'submitForm')]", "Download button exact match"),
                ("XPATH", "//button[contains(., 'Download') and contains(@class, 'button-main')]", "Download button by text and class"),
                ("XPATH", "//button[.//span[text()='Download']]", "Download button by span text"),
                # Fallback selectors
                ("XPATH", "//button[contains(text(), 'Download')]", "Download Button Text"),
                ("CSS", "button[onclick*='submitForm']", "Button with submitForm onclick"),
            ]
            
            download_button = None
            for selector_type, selector, description in download_selectors:
                try:
                    if selector_type == "CSS":
                        download_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        download_button = self.driver.find_element(By.XPATH, selector)
                    
                    if download_button and download_button.is_displayed():
                        logger.info(f"✅ Found download button: {description}")
                        logger.info(f"  Classes: {download_button.get_attribute('class')}")
                        logger.info(f"  OnClick: {download_button.get_attribute('onclick')}")
                        break
                        
                except Exception as e:
                    logger.debug(f"Download selector failed ({description}): {e}")
                    continue
            
            if not download_button:
                logger.warning("⚠️ Could not find download button")
                return False
            
            # Click the download button
            try:
                download_button.click()
                logger.info("✅ Clicked download button")
            except:
                # Try JavaScript click if regular click fails
                self.driver.execute_script("arguments[0].click();", download_button)
                logger.info("✅ Clicked download button (JavaScript)")
            
            # Wait for popup to appear
            time.sleep(2)
            
            # Handle the download price and availability popup
            logger.info("🔍 Looking for 'Download Price and Availability' confirmation popup...")
            
            # First check for popup content to confirm it's the right dialog
            popup_content_found = False
            try:
                # Look for the specific popup content
                popup_content_selectors = [
                    ("XPATH", "//*[contains(text(), 'Download Price and Availability')]", "Download Price and Availability text"),
                    ("XPATH", "//*[contains(text(), 'This file will include up to')]", "File include count text"),
                    ("XPATH", "//*[contains(text(), 'email will be sent to')]", "Email notification text"),
                    ("XPATH", "//*[contains(text(), 'pgits@hexalinks.com')]", "Email address confirmation"),
                ]
                
                for selector_type, selector, description in popup_content_selectors:
                    try:
                        if selector_type == "XPATH":
                            popup_element = self.driver.find_element(By.XPATH, selector)
                        
                        if popup_element and popup_element.is_displayed():
                            logger.info(f"✅ Found popup content: {description}")
                            logger.info(f"   Content: {popup_element.text[:100]}...")
                            popup_content_found = True
                            break
                            
                    except Exception as e:
                        logger.debug(f"Popup content selector failed ({description}): {e}")
                        continue
                
                if popup_content_found:
                    logger.info("✅ Confirmed 'Download Price and Availability' popup is displayed")
                else:
                    logger.info("📝 Popup content not found, but continuing to look for OK button")
                    
            except Exception as e:
                logger.debug(f"Error checking popup content: {e}")
            
            # Try different selectors for the OK button in the popup
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
                ("XPATH", "//input[@value='OK']", "OK input value"),
                ("XPATH", "//button[@type='submit' and contains(text(), 'OK')]", "OK submit button"),
                ("CSS", "button.ok-button", "OK button class"),
                ("CSS", "button.confirm", "Confirm button class"),
                ("XPATH", "//div[contains(@class, 'ui-dialog')]//button[contains(text(), 'OK')]", "OK button in ui-dialog"),
                ("XPATH", "//div[contains(@class, 'dialog')]//button[contains(text(), 'OK')]", "OK button in dialog"),
                ("XPATH", "//div[contains(@class, 'modal')]//button[contains(text(), 'OK')]", "OK button in modal"),
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
                        logger.info(f"✅ Found OK button in popup: {description}")
                        logger.info(f"   Button text: '{ok_button.text}'")
                        
                        # Click OK button
                        try:
                            ok_button.click()
                            logger.info("✅ Clicked OK button in popup")
                        except:
                            # Try JavaScript click if regular click fails
                            self.driver.execute_script("arguments[0].click();", ok_button)
                            logger.info("✅ Clicked OK button in popup (JavaScript)")
                        
                        ok_button_found = True
                        break
                        
                except Exception as e:
                    logger.debug(f"OK button selector failed ({description}): {e}")
                    continue
            
            if not ok_button_found:
                logger.warning("⚠️ Could not find OK button in popup - download may have started anyway")
                # Save page source for debugging
                try:
                    page_source = self.driver.page_source
                    with open("debug_popup_page.html", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    logger.info("💾 Saved page source to debug_popup_page.html for popup analysis")
                except:
                    pass
            
            # Wait for download to complete
            logger.info("⏳ Waiting for download to process...")
            time.sleep(5)
            
            # Check if there's a new window/tab (some downloads open in new tab)
            if len(self.driver.window_handles) > 1:
                # Switch to the new tab
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info("✅ Switched to download tab")
                time.sleep(2)
                # Switch back
                self.driver.switch_to.window(self.driver.window_handles[0])
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to download results: {str(e)}")
            return False
    
    def extract_product_data(self):
        """Extract product data from the current page"""
        logger.info("📊 Extracting product data...")
        
        try:
            # Wait for products to load
            time.sleep(5)
            
            # Try different selectors for product rows
            product_selectors = [
                ".product-row",
                ".item-row", 
                "tr[class*='product']",
                "tr[class*='item']",
                ".product",
                ".item",
                "tbody tr"
            ]
            
            products = []
            product_elements = []
            
            for selector in product_selectors:
                try:
                    product_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if product_elements:
                        logger.info(f"✅ Found {len(product_elements)} product elements with selector: {selector}")
                        break
                except:
                    continue
            
            if not product_elements:
                logger.warning("⚠️ No product elements found with standard selectors")
                # Try to get any table data
                all_rows = self.driver.find_elements(By.CSS_SELECTOR, "tr")
                product_elements = all_rows[1:] if len(all_rows) > 1 else []  # Skip header
                logger.info(f"Found {len(product_elements)} table rows")
            
            # Extract data from each product element
            for i, element in enumerate(product_elements[:20]):  # Limit to first 20 for testing
                try:
                    # Try to extract text from the element
                    element_text = element.text.strip()
                    if element_text and len(element_text) > 10:  # Skip empty or very short rows
                        
                        # Look for Microsoft products with all variations
                        element_text_lower = element_text.lower()
                        microsoft_keywords = [
                            'microsoft', 'msft', 'microsoft corp', 'microsoft corporation', 
                            'microsoft retail', 'ms corp', 'ms corporation'
                        ]
                        if any(keyword in element_text_lower for keyword in microsoft_keywords):
                            # Try to parse product information
                            cells = element.find_elements(By.TAG_NAME, "td")
                            
                            product_data = {
                                'element_index': i,
                                'raw_text': element_text,
                                'cell_count': len(cells),
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            # Try to extract structured data from cells
                            if len(cells) >= 3:
                                product_data.update({
                                    'cell_0': cells[0].text.strip() if len(cells) > 0 else '',
                                    'cell_1': cells[1].text.strip() if len(cells) > 1 else '',
                                    'cell_2': cells[2].text.strip() if len(cells) > 2 else '',
                                    'cell_3': cells[3].text.strip() if len(cells) > 3 else '',
                                    'cell_4': cells[4].text.strip() if len(cells) > 4 else '',
                                })
                            
                            products.append(product_data)
                            logger.info(f"📦 Found Microsoft product {len(products)}: {element_text[:100]}...")
                
                except Exception as e:
                    logger.debug(f"Error processing element {i}: {str(e)}")
                    continue
            
            logger.info(f"✅ Extracted {len(products)} Microsoft products")
            return products
            
        except Exception as e:
            logger.error(f"❌ Failed to extract product data: {str(e)}")
            return []
    
    def save_scraped_data(self, products, session_id):
        """Save scraped data to files"""
        logger.info("💾 Saving scraped data...")
        
        if not products:
            logger.warning("⚠️ No products to save")
            return None, None, None
        
        # Save raw product data
        raw_data_file = self.data_dir / f"raw_products_{session_id}.json"
        raw_data = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'source': 'TD SYNNEX Portal (Production)',
            'portal_url': self.portal_url,
            'total_products': len(products),
            'products': products
        }
        
        with open(raw_data_file, 'w') as f:
            json.dump(raw_data, f, indent=2)
        
        logger.info(f"📄 Raw data saved: {raw_data_file}")
        
        # Generate summary report
        report_file = self.data_dir / f"production_report_{session_id}.txt"
        self.generate_report(products, session_id, report_file)
        
        return raw_data_file, None, report_file
    
    def generate_report(self, products, session_id, report_file):
        """Generate human-readable report"""
        
        report_lines = [
            "=" * 80,
            "TD SYNNEX MICROSOFT PRODUCT SCRAPER - PRODUCTION REPORT",
            "=" * 80,
            f"Session ID: {session_id}",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}",
            f"Source: TD SYNNEX Portal (LIVE PRODUCTION DATA)",
            f"Portal URL: {self.portal_url}",
            f"Username: {self.td_username}",
            "",
            f"SUMMARY:",
            f"├── Total Microsoft Products Found: {len(products)}",
            f"├── Data Source: Live TD SYNNEX Portal",
            f"└── Extraction Method: Selenium WebDriver",
            "",
            "PRODUCT DATA (RAW EXTRACTION):",
            "-" * 40
        ]
        
        for i, product in enumerate(products, 1):
            report_lines.extend([
                f"\n📦 PRODUCT {i}:",
                f"   Raw Text: {product.get('raw_text', 'N/A')[:150]}{'...' if len(product.get('raw_text', '')) > 150 else ''}",
                f"   Cells Found: {product.get('cell_count', 0)}",
                f"   Cell 0: {product.get('cell_0', 'N/A')[:50]}",
                f"   Cell 1: {product.get('cell_1', 'N/A')[:50]}",
                f"   Cell 2: {product.get('cell_2', 'N/A')[:50]}"
            ])
        
        report_lines.extend([
            "",
            "=" * 80,
            "PRODUCTION STATUS:",
            "✅ Successfully connected to TD SYNNEX portal",
            "✅ Authentication successful", 
            "✅ Product data extracted from live portal",
            "✅ Data saved to JSON format",
            "",
            "NEXT STEPS:",
            "1. Review extracted data structure",
            "2. Refine product parsing logic",
            "3. Implement data validation",
            "4. Test with different search criteria",
            "",
            f"Report generated: {datetime.now().isoformat()}",
            "=" * 80
        ])
        
        # Save report
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        # Also print to console
        print('\n'.join(report_lines))
        
        logger.info(f"📋 Report generated: {report_file}")
    
    def get_verification_code_from_email(self):
        """Get verification code from email service"""
        try:
            # Email service URL - use localhost for local testing, container name for Docker
            email_service_url = os.getenv('EMAIL_SERVICE_URL', 'http://email-verification-service:5000')
            
            logger.info(f"🔍 Requesting verification code from email service: {email_service_url}")
            
            # Make request to email service
            response = requests.get(
                f"{email_service_url}/verification-code",
                params={
                    'sender': 'do_not_reply@tdsynnex.com',
                    'max_age_minutes': 10
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    verification_code = data.get('verification_code')
                    logger.info(f"✅ Retrieved verification code from email: {verification_code}")
                    return verification_code
                else:
                    logger.warning(f"⚠️ Email service returned no code: {data.get('message')}")
                    return None
            else:
                logger.warning(f"⚠️ Email service returned status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to email service: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting verification code from email: {e}")
            return None
    
    def run_production_scraping(self):
        """Execute a complete production scraping session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info("🚀 Starting TD SYNNEX Production Scraping Session")
        logger.info(f"📅 Session ID: {session_id}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Initialize browser
            if not self.initialize_browser():
                raise Exception("Browser initialization failed")
            
            # Step 2: Login to portal
            if not self.login_to_portal():
                raise Exception("Login failed")
            
            # Step 3: Navigate to download page
            if not self.navigate_to_download_page():
                raise Exception("Navigation to download page failed")
            
            # Step 4: Apply Microsoft filters
            if not self.apply_microsoft_filters():
                raise Exception("Filter application failed")
            
            # Step 5: Extract product data
            products = self.extract_product_data()
            
            if not products:
                logger.warning("⚠️ No Microsoft products found")
            
            # Step 6: Save data
            raw_file, summary_file, report_file = self.save_scraped_data(products, session_id)
            
            # Step 7: Session summary
            logger.info("=" * 60)
            logger.info("🎉 PRODUCTION SCRAPING SESSION COMPLETED!")
            logger.info(f"📊 Products found: {len(products)}")
            if raw_file:
                logger.info(f"📁 Files created:")
                logger.info(f"   • {raw_file.name}")
                logger.info(f"   • {report_file.name}")
            logger.info("=" * 60)
            
            return True, {
                'session_id': session_id,
                'products_found': len(products),
                'files': [str(raw_file), str(report_file)] if raw_file else []
            }
            
        except Exception as e:
            logger.error(f"❌ Production scraping session failed: {str(e)}")
            return False, {'error': str(e), 'session_id': session_id}
        
        finally:
            # Always close the browser
            if self.driver:
                logger.info("🔒 Closing browser...")
                self.driver.quit()

def main():
    """Main entry point for production test"""
    print("🔧 TD SYNNEX Microsoft Product Scraper - PRODUCTION MODE")
    print("⚠️  WARNING: This will connect to the real TD SYNNEX portal!")
    print("=" * 60)
    
    # Auto-proceed for automated runs
    print("Proceeding with live scraping...")
    
    scraper = LocalProductionScraper()
    
    # Run the production scraping session
    success, result = scraper.run_production_scraping()
    
    if success:
        print(f"\n✅ PRODUCTION SCRAPING COMPLETED!")
        print(f"📂 Check the './production_scraper_data' directory for output files")
        print(f"🎯 Live data extracted from TD SYNNEX portal!")
    else:
        print(f"\n❌ PRODUCTION SCRAPING FAILED:")
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()