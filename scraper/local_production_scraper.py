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
        
        try:
            # Use webdriver-manager to automatically download and manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("✅ Browser initialized successfully")
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
        """Apply filters to get Microsoft products"""
        logger.info("🔍 Applying Microsoft product filters...")
        
        try:
            # Look for manufacturer filter
            logger.info("Looking for manufacturer filter...")
            
            # Try different possible selectors for manufacturer filter
            manufacturer_selectors = [
                "select[name*='manufacturer']",
                "select[id*='manufacturer']", 
                "#manufacturerFilter",
                ".manufacturer-select",
                "select[name='mfg']",
                "select[name='vendor']"
            ]
            
            manufacturer_dropdown = None
            for selector in manufacturer_selectors:
                try:
                    manufacturer_dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"✅ Found manufacturer dropdown with selector: {selector}")
                    break
                except:
                    continue
            
            if manufacturer_dropdown:
                # Try to select Microsoft
                select = Select(manufacturer_dropdown)
                
                # Try different variations of Microsoft in the dropdown
                microsoft_options = [
                    'Microsoft', 'MICROSOFT', 'Microsoft Corporation', 'MSFT',
                    'Microsoft Corp', 'Microsoft Retail', 'MICROSOFT CORP', 
                    'MICROSOFT CORPORATION', 'MICROSOFT RETAIL'
                ]
                
                for option_text in microsoft_options:
                    try:
                        select.select_by_visible_text(option_text)
                        logger.info(f"✅ Selected manufacturer: {option_text}")
                        time.sleep(2)
                        return True
                    except:
                        continue
                
                # If exact match fails, try partial match
                all_options = [option.text for option in select.options]
                logger.info(f"Available manufacturer options: {all_options[:10]}...")  # Show first 10
                
                for option in select.options:
                    option_text_lower = option.text.lower()
                    if any(ms_variant in option_text_lower for ms_variant in ['microsoft', 'msft']):
                        select.select_by_visible_text(option.text)
                        logger.info(f"✅ Selected manufacturer (partial match): {option.text}")
                        time.sleep(2)
                        return True
            
            logger.warning("⚠️ Could not find or select Microsoft manufacturer filter")
            logger.info("Proceeding without manufacturer filter...")
            
            # Try to enable Short Description box
            self.enable_short_description()
            
            # Try to select "In Stock Only" checkbox
            self.enable_in_stock_only()
            
            # Try to trigger search/filter application
            self.trigger_search()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply filters: {str(e)}")
            return False
    
    def enable_short_description(self):
        """Enable Short Description checkbox/option"""
        logger.info("📝 Enabling Short Description option...")
        
        try:
            # Try different selectors for Short Description checkbox
            short_desc_selectors = [
                ("ID", "shortDescription", "Short Description ID"),
                ("ID", "shortDesc", "Short Desc ID"),
                ("ID", "includeShortDescription", "Include Short Description"),
                ("NAME", "shortDescription", "Short Description Name"),
                ("NAME", "shortDesc", "Short Desc Name"),
                ("CSS", "input[name*='shortdesc']", "Short Desc CSS Name"),
                ("CSS", "input[name*='description']", "Description CSS Name"),
                ("CSS", "input[id*='shortdesc']", "Short Desc CSS ID"),
                ("CSS", "input[id*='description']", "Description CSS ID"),
                ("XPATH", "//input[@type='checkbox' and contains(@name, 'description')]", "Description Checkbox"),
                ("XPATH", "//input[@type='checkbox' and contains(@id, 'description')]", "Description Checkbox ID"),
                ("XPATH", "//label[contains(text(), 'Short Description')]/..//input", "Short Description Label"),
                ("XPATH", "//label[contains(text(), 'Description')]/..//input", "Description Label"),
            ]
            
            for selector_type, selector, description in short_desc_selectors:
                try:
                    if selector_type == "ID":
                        element = self.driver.find_element(By.ID, selector)
                    elif selector_type == "NAME":
                        element = self.driver.find_element(By.NAME, selector)
                    elif selector_type == "CSS":
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        element = self.driver.find_element(By.XPATH, selector)
                    
                    if element and element.is_displayed():
                        # Check if it's a checkbox and not already checked
                        if element.get_attribute('type') == 'checkbox' and not element.is_selected():
                            element.click()
                            logger.info(f"✅ Enabled Short Description: {description}")
                            time.sleep(1)
                            return True
                        elif element.get_attribute('type') == 'checkbox' and element.is_selected():
                            logger.info(f"✅ Short Description already enabled: {description}")
                            return True
                        else:
                            # Try clicking anyway if it's not a checkbox
                            element.click()
                            logger.info(f"✅ Clicked Short Description option: {description}")
                            time.sleep(1)
                            return True
                            
                except Exception as e:
                    logger.debug(f"Short Description selector failed ({description}): {e}")
                    continue
            
            logger.warning("⚠️ Could not find Short Description option")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to enable Short Description: {str(e)}")
            return False
    
    def enable_in_stock_only(self):
        """Enable 'In Stock Only' checkbox with specific selectors"""
        logger.info("📦 Enabling 'In Stock Only' option...")
        
        try:
            # Try specific selectors for the "In Stock Only" checkbox
            in_stock_selectors = [
                ("NAME", "tab-realtime", "In Stock Only Name"),
                ("ID", "tab-realtime", "In Stock Only ID"),
                ("CSS", ".tab-realtime", "In Stock Only Class"),
                ("CSS", "input[name='tab-realtime']", "In Stock Only CSS Name"),
                ("CSS", "input[id='tab-realtime']", "In Stock Only CSS ID"),
                ("CSS", "input[class*='tab-realtime']", "In Stock Only CSS Class"),
                ("XPATH", "//input[@name='tab-realtime']", "In Stock Only XPath Name"),
                ("XPATH", "//input[@id='tab-realtime']", "In Stock Only XPath ID"),
                ("XPATH", "//input[@class='tab-realtime']", "In Stock Only XPath Class"),
                ("XPATH", "//input[contains(@class, 'tab-realtime')]", "In Stock Only XPath Class Contains"),
                ("XPATH", "//label[contains(text(), 'In Stock Only')]/..//input", "In Stock Only Label"),
                ("XPATH", "//label[contains(text(), 'In Stock')]/..//input", "In Stock Label"),
                ("XPATH", "//input[@type='checkbox' and contains(@name, 'realtime')]", "Realtime Checkbox"),
                ("XPATH", "//input[@type='checkbox' and contains(@id, 'realtime')]", "Realtime Checkbox ID"),
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
                        # Check if it's a checkbox and not already checked
                        if element.get_attribute('type') == 'checkbox':
                            if not element.is_selected():
                                element.click()
                                logger.info(f"✅ Enabled 'In Stock Only': {description}")
                                time.sleep(1)
                                return True
                            else:
                                logger.info(f"✅ 'In Stock Only' already enabled: {description}")
                                return True
                        else:
                            # Try clicking anyway if it's not a checkbox (might be a button/tab)
                            element.click()
                            logger.info(f"✅ Clicked 'In Stock Only' option: {description}")
                            time.sleep(1)
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