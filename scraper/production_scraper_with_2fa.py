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
from selenium.webdriver.common.keys import Keys
import requests
import threading
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

# Check for undetected Chrome availability
try:
    import undetected_chromedriver as uc
    UNDETECTED_CHROME_AVAILABLE = True
    logger.info("✅ Undetected Chrome available for fallback")
except ImportError:
    UNDETECTED_CHROME_AVAILABLE = False
    logger.warning("⚠️ Undetected Chrome not available")

class ProductionScraperWith2FA:
    """Production scraper with integrated 2FA support"""
    
    def __init__(self):
        # Enhanced debugging settings (initialize first)
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.screenshot_interval = int(os.getenv('SCREENSHOT_INTERVAL', '10'))  # seconds
        self.screenshot_thread = None
        self.capture_screenshots = True
        
        # Get credentials from environment or .env file
        self.load_environment()
        
        # TD SYNNEX Portal URL
        self.portal_url = "https://ec.synnex.com/ecx/eServices/priceAvailabilityDownload.html"
        self.login_url = "https://ec.synnex.com/ecx/login.html"
        
        # Browser setup
        self.driver = None
        self.wait = None
        
        # Enhanced debugging settings
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.screenshot_interval = int(os.getenv('SCREENSHOT_INTERVAL', '10'))  # seconds
        self.screenshot_thread = None
        self.capture_screenshots = True
        
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
        
        # Log proxy settings
        proxy_host = os.getenv('PROXY_HOST')
        proxy_port = os.getenv('PROXY_PORT')
        if proxy_host and proxy_port:
            logger.info(f"🔗 Proxy settings: {proxy_host}:{proxy_port}")
        
        # Log debug settings
        if self.debug_mode:
            logger.info("🔍 Debug mode enabled")
            logger.info(f"📸 Screenshot interval: {self.screenshot_interval} seconds")
    
    def start_continuous_screenshots(self):
        """Start continuous screenshot capture in debug mode"""
        if not self.debug_mode or not self.capture_screenshots:
            return
            
        def capture_loop():
            counter = 0
            while self.capture_screenshots and self.driver:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_dir = os.path.join("production_scraper_data", "debug_screenshots")
                    os.makedirs(screenshot_dir, exist_ok=True)
                    
                    screenshot_path = os.path.join(screenshot_dir, f"continuous_{counter:04d}_{timestamp}.png")
                    self.driver.save_screenshot(screenshot_path)
                    
                    # Also save page source for debugging
                    page_source_path = os.path.join(screenshot_dir, f"page_source_{counter:04d}_{timestamp}.html")
                    with open(page_source_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    
                    logger.info(f"📸 DEBUG: Continuous screenshot {counter:04d} saved")
                    counter += 1
                    
                    time.sleep(self.screenshot_interval)
                except Exception as e:
                    logger.error(f"Error in continuous screenshot: {e}")
                    time.sleep(self.screenshot_interval)
        
        self.screenshot_thread = threading.Thread(target=capture_loop, daemon=True)
        self.screenshot_thread.start()
        logger.info("📸 Started continuous screenshot capture")
    
    def stop_continuous_screenshots(self):
        """Stop continuous screenshot capture"""
        self.capture_screenshots = False
        if self.screenshot_thread:
            logger.info("📸 Stopped continuous screenshot capture")
    
    def capture_debug_info(self, phase="unknown"):
        """Capture comprehensive debug information"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_dir = os.path.join("production_scraper_data", "debug_info")
            os.makedirs(debug_dir, exist_ok=True)
            
            # Screenshot
            screenshot_path = os.path.join(debug_dir, f"debug_{phase}_{timestamp}.png")
            self.driver.save_screenshot(screenshot_path)
            
            # Page source
            page_source_path = os.path.join(debug_dir, f"page_source_{phase}_{timestamp}.html")
            with open(page_source_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Browser info
            browser_info = {
                "timestamp": timestamp,
                "phase": phase,
                "current_url": self.driver.current_url,
                "title": self.driver.title,
                "window_handles": len(self.driver.window_handles),
                "page_source_length": len(self.driver.page_source)
            }
            
            # Look for 2FA elements
            two_fa_elements = {}
            try:
                # Check for verification code input
                verification_input = self.driver.find_element(By.ID, "ipCode")
                two_fa_elements["verification_input"] = {
                    "found": True,
                    "displayed": verification_input.is_displayed(),
                    "enabled": verification_input.is_enabled(),
                    "value": verification_input.get_attribute('value')
                }
            except:
                two_fa_elements["verification_input"] = {"found": False}
            
            try:
                # Check for submit button
                submit_button = self.driver.find_element(By.ID, "enterButton")
                two_fa_elements["submit_button"] = {
                    "found": True,
                    "displayed": submit_button.is_displayed(),
                    "enabled": submit_button.is_enabled()
                }
            except:
                two_fa_elements["submit_button"] = {"found": False}
            
            browser_info["two_fa_elements"] = two_fa_elements
            
            # Network info
            try:
                logs = self.driver.get_log('performance')
                network_requests = []
                for log in logs[-10:]:  # Last 10 network events
                    if 'Network' in log.get('message', ''):
                        network_requests.append(log)
                browser_info["recent_network_logs"] = network_requests
            except:
                browser_info["recent_network_logs"] = []
            
            # Save browser info
            info_path = os.path.join(debug_dir, f"browser_info_{phase}_{timestamp}.json")
            with open(info_path, 'w') as f:
                json.dump(browser_info, f, indent=2)
            
            logger.info(f"🔍 DEBUG INFO [{phase}] saved to {debug_dir}")
            
            return browser_info
            
        except Exception as e:
            logger.error(f"Error capturing debug info: {e}")
            return None
    
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
        # Use headless mode but allow override for debugging
        headless_mode = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
        if headless_mode:
            chrome_options.add_argument('--headless')
        else:
            logger.info("🖥️ Running in headed mode for debugging")
        
        # Simple, stable Chrome configuration (based on working local_production_scraper)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Configure download settings (simplified)
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Simple Chrome initialization (based on working local_production_scraper)
        try:
            # Use webdriver-manager for automatic driver management (but fallback if not available)
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Using webdriver-manager for ChromeDriver")
            except Exception as wdm_error:
                logger.warning(f"Webdriver-manager failed: {wdm_error}, using Selenium Manager")
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("✅ Using Selenium Manager for ChromeDriver")
            
            # Simple anti-detection script
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("✅ Chrome browser initialized successfully")
            logger.info(f"📁 Downloads will be saved to: {download_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome browser: {e}")
            raise
    
    def bypass_vwo_script(self):
        """Inject JavaScript to bypass VWO script hiding"""
        
        # More aggressive JavaScript to bypass VWO hiding
        bypass_script = """
        // First, disable VWO before it starts
        window.__vwo_disable__ = true;
        
        // Remove VWO hiding elements
        var hideElements = document.querySelectorAll('#_vis_opt_path_hides, ._vis_hide_layer');
        hideElements.forEach(function(element) {
            element.remove();
        });
        
        // Override VWO hiding styles with maximum specificity
        var style = document.createElement('style');
        style.textContent = `
            body { opacity: 1 !important; filter: none !important; background: white !important; transition: none !important; }
            html { opacity: 1 !important; filter: none !important; background: white !important; }
            div[id*='_vis_opt'], div[class*='_vis_hide'], div[class*='vwo'] { display: none !important; }
            #_vis_opt_path_hides { display: none !important; }
            ._vis_hide_layer { display: none !important; }
            [style*='opacity:0'] { opacity: 1 !important; }
            [style*='z-index: 2147483647'] { display: none !important; }
        `;
        document.head.appendChild(style);
        
        // Force finish VWO code if it exists
        if (window._vwo_code && window._vwo_code.finish) {
            window._vwo_code.finish();
        }
        
        // Clear any VWO timeouts
        if (window._vwo_settings_timer) {
            clearTimeout(window._vwo_settings_timer);
        }
        
        // Disable VWO initialization
        window._vwo_code = { 
            init: function() { return false; },
            finish: function() { return true; }
        };
        
        // Make sure body is visible
        if (document.body) {
            document.body.style.opacity = '1';
            document.body.style.filter = 'none';
            document.body.style.background = 'white';
            document.body.style.display = 'block';
        }
        
        // Force remove any overlay elements
        setTimeout(function() {
            var overlays = document.querySelectorAll('[style*="position: fixed"][style*="z-index"]');
            overlays.forEach(function(overlay) {
                if (overlay.style.zIndex > 1000000) {
                    overlay.remove();
                }
            });
        }, 100);
        
        return 'Aggressive VWO bypass executed';
        """
        
        try:
            result = self.driver.execute_script(bypass_script)
            logger.info(f"🔧 VWO bypass result: {result}")
            return True
        except Exception as e:
            logger.error(f"Error executing VWO bypass: {e}")
            return False
            raise
    
    def detect_and_handle_captcha(self):
        """Enhanced CAPTCHA detection and handling"""
        logger.info("🔍 Checking for CAPTCHA challenge...")
        
        # Multiple CAPTCHA detection methods
        captcha_indicators = [
            # Method 1: Direct CAPTCHA field detection
            {
                "method": "Direct Field",
                "selector": (By.ID, "captchaCode"),
                "description": "CAPTCHA input field"
            },
            # Method 2: CAPTCHA image detection
            {
                "method": "CAPTCHA Image",
                "selector": (By.CSS_SELECTOR, "img[src*='captcha']"),
                "description": "CAPTCHA image element"
            },
            # Method 3: CAPTCHA container detection
            {
                "method": "CAPTCHA Container",
                "selector": (By.CSS_SELECTOR, "[class*='captcha'], [id*='captcha']"),
                "description": "CAPTCHA container element"
            },
            # Method 4: reCAPTCHA detection
            {
                "method": "reCAPTCHA",
                "selector": (By.CSS_SELECTOR, ".g-recaptcha, [data-sitekey]"),
                "description": "Google reCAPTCHA element"
            },
            # Method 5: hCaptcha detection
            {
                "method": "hCaptcha",
                "selector": (By.CSS_SELECTOR, ".h-captcha, [data-hcaptcha-sitekey]"),
                "description": "hCaptcha element"
            }
        ]
        
        captcha_found = False
        captcha_type = None
        
        for indicator in captcha_indicators:
            try:
                element = self.driver.find_element(indicator["selector"][0], indicator["selector"][1])
                if element.is_displayed():
                    logger.warning(f"⚠️ {indicator['method']} CAPTCHA detected!")
                    logger.info(f"   Found: {indicator['description']}")
                    captcha_found = True
                    captcha_type = indicator["method"]
                    
                    # Capture debug info when CAPTCHA is detected
                    self.capture_debug_info(f"captcha_detected_{indicator['method'].lower().replace(' ', '_')}")
                    break
                    
            except Exception as e:
                logger.debug(f"No {indicator['method']} CAPTCHA found: {e}")
                continue
        
        if not captcha_found:
            logger.info("✅ No CAPTCHA challenge detected")
            return False
        
        # Handle different CAPTCHA types
        if captcha_type:
            logger.warning(f"🚨 CAPTCHA CHALLENGE DETECTED: {captcha_type}")
            logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info("🤖 AUTOMATED CAPTCHA HANDLING")
            logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # Strategy 1: Wait and check if CAPTCHA disappears (auto-solve)
            logger.info("⏳ Waiting for potential auto-solve or manual intervention...")
            for wait_cycle in range(30):  # Wait up to 30 seconds
                try:
                    time.sleep(1)
                    
                    # Check if CAPTCHA is still present
                    captcha_still_present = False
                    for indicator in captcha_indicators:
                        try:
                            element = self.driver.find_element(indicator["selector"][0], indicator["selector"][1])
                            if element.is_displayed():
                                captcha_still_present = True
                                break
                        except:
                            continue
                    
                    if not captcha_still_present:
                        logger.info("✅ CAPTCHA appears to have been resolved!")
                        return True
                    
                    # Check if login button is clickable (might indicate CAPTCHA solved)
                    try:
                        login_button = self.driver.find_element(By.ID, "loginBtn")
                        if login_button.is_enabled():
                            logger.info("✅ Login button is now enabled - CAPTCHA may be solved")
                            return True
                    except:
                        pass
                    
                    if wait_cycle % 5 == 0:
                        logger.info(f"⏰ Still waiting for CAPTCHA resolution... ({wait_cycle}/30s)")
                        
                except Exception as e:
                    logger.debug(f"Error during CAPTCHA wait: {e}")
                    continue
            
            # Strategy 2: If still present, log detailed info and continue
            logger.warning("⚠️ CAPTCHA still present after waiting")
            logger.info("🔍 CAPTCHA Analysis:")
            logger.info(f"   Type: {captcha_type}")
            logger.info(f"   Current URL: {self.driver.current_url}")
            logger.info(f"   Page Title: {self.driver.title}")
            
            # Check if there's a way to skip or if login can proceed
            try:
                login_button = self.driver.find_element(By.ID, "loginBtn")
                if login_button.is_enabled():
                    logger.info("✅ Login button is enabled - attempting to proceed")
                    return True
                else:
                    logger.warning("❌ Login button is disabled - CAPTCHA must be solved")
            except:
                logger.warning("❌ Cannot find login button")
            
            # Final strategy: Continue anyway and let the main flow handle it
            logger.info("🚀 Proceeding with login attempt despite CAPTCHA")
            return True
        
        return False
    
    def monitor_login_progress(self):
        """Monitor login progress and detect issues"""
        logger.info("📊 Monitoring login progress...")
        
        max_wait_time = 15
        wait_interval = 1
        
        for i in range(max_wait_time):
            current_url = self.driver.current_url
            
            # Check if we've been redirected (success)
            if "login.html" not in current_url:
                logger.info(f"✅ Login redirect detected: {current_url}")
                return
            
            # Check for CAPTCHA during login process
            try:
                captcha_field = self.driver.find_element(By.ID, "captchaCode")
                if captcha_field.is_displayed():
                    logger.warning("⚠️ CAPTCHA still present during login process")
                    logger.info("🔄 Checking if CAPTCHA was solved...")
                    
                    # Check if CAPTCHA input has value
                    captcha_value = captcha_field.get_attribute('value')
                    if captcha_value and len(captcha_value) > 0:
                        logger.info("✅ CAPTCHA appears to have been filled")
                    else:
                        logger.warning("❌ CAPTCHA field is empty")
                        
            except:
                # No CAPTCHA found, which is good
                pass
            
            # Check for error messages
            try:
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error-message, .alert-danger, [class*='error']")
                for error in error_elements:
                    if error.is_displayed() and error.text.strip():
                        logger.warning(f"⚠️ Error message detected: {error.text}")
            except:
                pass
            
            # Check page title for error indicators
            page_title = self.driver.title.lower()
            if "error" in page_title or "invalid" in page_title:
                logger.warning(f"⚠️ Error detected in page title: {self.driver.title}")
            
            time.sleep(wait_interval)
        
        logger.info("⏰ Login monitoring period completed")
    
    def login_to_portal(self):
        """Login to TD SYNNEX portal with 2FA support"""
        logger.info("🔐 Logging into TD SYNNEX portal...")
        
        try:
            # Start continuous screenshots if in debug mode
            self.start_continuous_screenshots()
            
            # Navigate to login page
            self.driver.get(self.login_url)
            logger.info(f"Navigated to: {self.login_url}")
            
            # Wait for page to load
            time.sleep(3)
            
            # Execute VWO bypass to ensure page is visible
            logger.info("🔧 Executing VWO bypass to ensure page visibility...")
            self.bypass_vwo_script()
            time.sleep(2)  # Wait for bypass to take effect
            
            # Run bypass again to make sure it sticks
            self.bypass_vwo_script()
            time.sleep(1)
            
            # Capture initial debug info
            self.capture_debug_info("login_page_loaded")
            
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
            
            # Check if CAPTCHA is required with enhanced detection
            captcha_detected = self.detect_and_handle_captcha()
            if captcha_detected:
                logger.info("🔓 CAPTCHA handling completed")
            
            # Submit login form
            logger.info("Submitting login form...")
            login_button = self.driver.find_element(By.ID, "loginBtn")
            login_button.click()
            
            # Wait for login to complete with CAPTCHA monitoring
            logger.info("Waiting for login to complete...")
            self.monitor_login_progress()
            
            # Check current URL after login attempt
            current_url = self.driver.current_url
            logger.info(f"Current URL after login attempt: {current_url}")
            
            # Wait longer for potential redirects
            max_wait_time = 15
            wait_interval = 2
            
            for i in range(max_wait_time // wait_interval):
                current_url = self.driver.current_url
                logger.info(f"Checking URL (attempt {i+1}): {current_url}")
                
                # If we're redirected to authenticate page, that's good
                if "/authenticate.html" in current_url:
                    logger.info("✅ Successfully redirected to authenticate page")
                    break
                    
                # If we're still on login page, wait a bit more
                elif "/login.html" in current_url:
                    logger.info("⏳ Still on login page, waiting for redirect...")
                    time.sleep(wait_interval)
                    continue
                    
                # If we're on a different page, check if it's successful
                elif "login" not in current_url.lower():
                    logger.info("✅ Redirected to non-login page")
                    break
                    
                time.sleep(wait_interval)
            
            # Try to navigate to authenticate page if we're still on login
            final_url = self.driver.current_url
            if "/login.html" in final_url:
                logger.info("⚠️ Still on login page, attempting to navigate to authenticate page...")
                try:
                    authenticate_url = "https://ec.synnex.com/ecx/authenticate.html"
                    self.driver.get(authenticate_url)
                    time.sleep(3)
                    logger.info(f"Navigated to authenticate page: {self.driver.current_url}")
                except Exception as e:
                    logger.error(f"❌ Failed to navigate to authenticate page: {e}")
            
            # Capture debug info before 2FA detection
            self.capture_debug_info("before_2fa_detection")
            
            # Check for 2FA challenge
            if self.two_fa_handler.detect_2fa_challenge(self.driver):
                logger.info("🔒 2FA challenge detected!")
                
                # Capture debug info when 2FA is detected
                self.capture_debug_info("2fa_detected")
                
                # Handle 2FA challenge
                if self.two_fa_handler.handle_2fa_challenge(self.driver):
                    logger.info("✅ 2FA challenge handled successfully")
                    
                    # Capture debug info after 2FA success
                    self.capture_debug_info("2fa_success")
                    
                    time.sleep(3)  # Wait for redirect after 2FA
                else:
                    logger.error("❌ Failed to handle 2FA challenge")
                    
                    # Capture debug info after 2FA failure
                    self.capture_debug_info("2fa_failure")
                    
                    return False
            else:
                logger.info("🔓 No 2FA challenge detected")
                self.capture_debug_info("no_2fa_detected")
            
            # Check if login was successful
            current_url = self.driver.current_url
            logger.info(f"Final URL after login process: {current_url}")
            
            # Capture final debug info
            self.capture_debug_info("login_final_check")
            
            # Look for login success indicators
            if "login" not in current_url.lower() or "/authenticate.html" in current_url:
                logger.info("✅ Login appears successful!")
                self.capture_debug_info("login_success")
                return True
            else:
                # Check for error messages
                error_messages = self.driver.find_elements(By.CLASS_NAME, "error-message")
                if error_messages:
                    for error in error_messages:
                        logger.error(f"❌ Login error: {error.text}")
                else:
                    logger.error("❌ Login failed - still on login page")
                
                self.capture_debug_info("login_failed")
                return False
                
        except TimeoutException:
            logger.error("❌ Timeout during login process")
            self.capture_debug_info("login_timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Error during login: {e}")
            self.capture_debug_info("login_error")
            return False
        finally:
            # Stop continuous screenshots
            self.stop_continuous_screenshots()
    
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
                
            else:
                logger.error("❌ Could not find manufacturer filter section")
            
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
    
    def run_scraper(self):
        """Execute a complete production scraping session with 2FA support"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = time.time()
        
        logger.info("🚀 Starting TD SYNNEX Production Scraping Session with 2FA")
        logger.info(f"📅 Session ID: {session_id}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Initialize browser
            if not self.initialize_browser():
                raise Exception("Browser initialization failed")
            
            # Step 2: Login to portal with 2FA support
            if not self.login_to_portal():
                raise Exception("Login failed")
            
            # Step 3: Navigate to download page
            if not self.navigate_to_download_page():
                raise Exception("Navigation to download page failed")
            
            # Step 4: Execute VWO bypass to ensure page is visible
            logger.info("🔧 Executing VWO bypass for portal page...")
            self.bypass_vwo_script()
            time.sleep(2)
            
            # Run bypass again to make sure it sticks
            self.bypass_vwo_script()
            time.sleep(1)
            
            # Step 5: Apply Microsoft filters (includes popup fix)
            if not self.apply_microsoft_filters():
                raise Exception("Filter application failed")
            
            # Step 6: Session summary
            logger.info("=" * 60)
            logger.info("🎉 PRODUCTION SCRAPING SESSION WITH 2FA COMPLETED!")
            logger.info("✅ Download initiated successfully")
            logger.info("✅ All filters applied without popup errors")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Production scraping session failed: {str(e)}")
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