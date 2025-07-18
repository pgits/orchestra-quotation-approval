import azure.functions as func
import logging
import json
import os
import time
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
import tempfile
import shutil

app = func.FunctionApp()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AzureTDSynnexScraper:
    """Azure Functions version of TD SYNNEX scraper"""
    
    def __init__(self):
        # Load credentials from environment
        self.td_username = os.environ.get('TDSYNNEX_USERNAME')
        self.td_password = os.environ.get('TDSYNNEX_PASSWORD')
        self.email_username = os.environ.get('EMAIL_USERNAME')
        self.email_password = os.environ.get('EMAIL_PASSWORD')
        
        # TD SYNNEX Portal URLs
        self.portal_url = "https://ec.synnex.com/ecx/eServices/priceAvailabilityDownload.html"
        self.login_url = "https://ec.synnex.com/ecx/login.html"
        
        # Browser setup
        self.driver = None
        self.wait = None
        
        # Create temporary directory for downloads
        self.temp_dir = tempfile.mkdtemp()
        self.download_dir = os.path.join(self.temp_dir, "downloads")
        os.makedirs(self.download_dir, exist_ok=True)
        
        logger.info(f"Azure scraper initialized")
        logger.info(f"Portal URL: {self.portal_url}")
        logger.info(f"Username: {self.td_username[:3]}***" if self.td_username else "No username")
    
    def validate_credentials(self):
        """Validate that required credentials are present"""
        if not self.td_username or not self.td_password:
            logger.error("Missing TD SYNNEX credentials!")
            return False
        return True
    
    def ensure_chrome_installed(self):
        """Ensure Chrome is installed and available"""
        import subprocess
        
        try:
            # Check if Chrome is already available
            chrome_paths = [
                '/usr/bin/google-chrome-stable',
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/tmp/chrome_install/chrome-linux64/chrome'
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    logger.info(f"Chrome found at: {chrome_path}")
                    os.environ['CHROME_BIN'] = chrome_path
                    return True
            
            # If no Chrome found, try to install using our Python installer
            logger.warning("Chrome not found, attempting installation...")
            
            try:
                # Import and run the Chrome installer
                from chrome_installer import install_chrome_azure_functions
                
                if install_chrome_azure_functions():
                    logger.info("Chrome installed successfully via Python installer")
                    return True
                else:
                    logger.error("Python Chrome installer failed")
                    
            except ImportError:
                logger.error("Chrome installer module not found")
            except Exception as e:
                logger.error(f"Failed to install Chrome via Python installer: {e}")
            
            # Fallback: try bash installation script
            try:
                if os.path.exists('/home/site/wwwroot/startup.sh'):
                    subprocess.run(['bash', '/home/site/wwwroot/startup.sh'], check=True)
                    logger.info("Chrome installation script executed")
                else:
                    logger.warning("No installation script found")
                    
            except Exception as e:
                logger.error(f"Failed to install Chrome via bash script: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking Chrome installation: {e}")
            return False
    
    def initialize_browser(self):
        """Initialize Chrome browser with Azure-appropriate options"""
        logger.info("🌐 Initializing Chrome browser for Azure...")
        
        # Ensure Chrome is installed
        if not self.ensure_chrome_installed():
            logger.error("Chrome installation failed")
            return False
        
        chrome_options = Options()
        # Azure Functions requires headless mode
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Configure download settings
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            # Set Chrome binary path if available
            chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/google-chrome-stable')
            if os.path.exists(chrome_bin):
                chrome_options.binary_location = chrome_bin
                logger.info(f"Using Chrome binary: {chrome_bin}")
            
            # Set ChromeDriver path if available
            chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')
            
            if os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info(f"Using ChromeDriver: {chromedriver_path}")
            else:
                # Fallback to webdriver-manager for automatic driver management
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Using webdriver-manager for ChromeDriver")
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 30)  # Increased timeout for Azure
            logger.info("✅ Browser initialized successfully")
            return True
        except WebDriverException as e:
            logger.error(f"❌ Failed to initialize browser: {str(e)}")
            logger.error(f"Chrome binary path: {chrome_bin}")
            logger.error(f"ChromeDriver path: {chromedriver_path}")
            return False
    
    def handle_cookie_popup(self):
        """Handle cookie consent popup if present"""
        logger.info("🍪 Checking for cookie popup...")
        
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
                        time.sleep(3)
                        return True
                        
                except Exception as e:
                    logger.debug(f"Cookie selector failed ({description}): {e}")
                    continue
            
            time.sleep(1)
        
        logger.info("No cookie popup detected or already handled")
        return False

    def login_to_portal(self):
        """Login to TD SYNNEX portal"""
        logger.info("🔐 Logging into TD SYNNEX portal...")
        
        try:
            self.driver.get(self.login_url)
            logger.info(f"Navigated to: {self.login_url}")
            
            time.sleep(3)
            self.handle_cookie_popup()
            
            # Find and fill email field
            logger.info("Locating email field...")
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "inputEmailAddress"))
            )
            email_field.clear()
            self.driver.execute_script("arguments[0].value = '';", email_field)
            time.sleep(0.5)
            email_field.send_keys(self.td_username)
            
            # Find and fill password
            logger.info("Locating password field...")
            password_field = self.driver.find_element(By.ID, "inputPassword")
            password_field.clear()
            self.driver.execute_script("arguments[0].value = '';", password_field)
            time.sleep(0.5)
            password_field.send_keys(self.td_password)
            
            # Check for CAPTCHA
            try:
                captcha_field = self.driver.find_element(By.ID, "captchaCode")
                if captcha_field.is_displayed():
                    logger.warning("⚠️ CAPTCHA detected! This may cause login to fail in headless mode.")
            except:
                logger.info("No CAPTCHA required")
            
            # Submit login form
            logger.info("Submitting login form...")
            login_button = self.driver.find_element(By.ID, "loginBtn")
            login_button.click()
            
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "login" not in current_url.lower():
                logger.info("✅ Login appears successful!")
                return True
            else:
                logger.error("❌ Login failed - still on login page")
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
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to navigate to download page: {str(e)}")
            return False
    
    def apply_microsoft_filters(self):
        """Apply filters to get Microsoft products"""
        logger.info("🔍 Applying Microsoft product filters...")
        
        try:
            # Find manufacturer filter input
            filter_selectors = [
                ("CSS", "input.filter-icon.manufactures-filter.float-right"),
                ("CSS", "input[class*='manufactures-filter']"),
                ("CSS", "input[placeholder*='Enter keywords to filter']"),
                ("XPATH", "//input[@class='filter-icon manufactures-filter float-right']"),
            ]
            
            manufacturer_filter_input = None
            for selector_type, selector in filter_selectors:
                try:
                    if selector_type == "CSS":
                        manufacturer_filter_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        manufacturer_filter_input = self.driver.find_element(By.XPATH, selector)
                    
                    if manufacturer_filter_input and manufacturer_filter_input.is_displayed():
                        break
                except:
                    continue
            
            if manufacturer_filter_input:
                manufacturer_filter_input.clear()
                manufacturer_filter_input.send_keys("Microsoft")
                manufacturer_filter_input.send_keys(Keys.RETURN)
                time.sleep(2)
                logger.info("✅ Applied Microsoft manufacturer filter")
            
            # Find and select Microsoft checkboxes
            microsoft_found = False
            all_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            
            for checkbox in all_checkboxes:
                try:
                    cb_value = checkbox.get_attribute('value') or ''
                    cb_name = checkbox.get_attribute('name') or ''
                    
                    # Check for Microsoft checkboxes
                    if ('19215' in cb_value and 'vendNo' in cb_name) or ('23073' in cb_value and 'mfg' in cb_name):
                        if not checkbox.is_selected():
                            try:
                                checkbox.click()
                                logger.info(f"✅ Selected Microsoft checkbox: {cb_value}")
                                microsoft_found = True
                                time.sleep(0.5)
                            except:
                                self.driver.execute_script("arguments[0].click();", checkbox)
                                logger.info(f"✅ Selected Microsoft checkbox via JS: {cb_value}")
                                microsoft_found = True
                except:
                    continue
            
            if not microsoft_found:
                logger.warning("⚠️ No Microsoft checkboxes found")
            
            # Enable additional options
            self.enable_short_description()
            self.set_file_format_cr_mac()
            self.set_field_delimiter_semicolon()
            self.enable_in_stock_only()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply filters: {str(e)}")
            return False
    
    def enable_short_description(self):
        """Enable Short Description checkbox"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, "input[name='fields'][value='short_desc']")
            if element and not element.is_selected():
                element.click()
                logger.info("✅ Enabled Short Description")
        except Exception as e:
            logger.debug(f"Short description enable failed: {e}")
    
    def set_file_format_cr_mac(self):
        """Set File Format to CR(Mac)"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, "input[name='fileFormat'][value='cr']")
            if element and not element.is_selected():
                element.click()
                logger.info("✅ Set file format to CR(Mac)")
        except Exception as e:
            logger.debug(f"CR(Mac) format set failed: {e}")
    
    def set_field_delimiter_semicolon(self):
        """Set Field Delimiter to semi-colon"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, "input[name='delimiter'][value=';']")
            if element and not element.is_selected():
                element.click()
                logger.info("✅ Set field delimiter to semicolon")
        except Exception as e:
            logger.debug(f"Semicolon delimiter set failed: {e}")
    
    def enable_in_stock_only(self):
        """Enable 'In Stock Only' checkbox"""
        try:
            element = self.driver.find_element(By.ID, "inStock")
            if element and not element.is_selected():
                element.click()
                logger.info("✅ Enabled 'In Stock Only'")
        except Exception as e:
            logger.debug(f"In stock only enable failed: {e}")
    
    def download_results(self):
        """Click the download button and handle popup"""
        logger.info("💾 Looking for download button...")
        
        try:
            # Find download button
            download_selectors = [
                ("XPATH", "//button[@onclick='javascript:submitForm(false);']"),
                ("XPATH", "//button[contains(@onclick, 'submitForm(false)')]"),
                ("CSS", "button.button-main.button-big"),
                ("XPATH", "//button[@class='button-main button-big' and contains(@onclick, 'submitForm')]"),
            ]
            
            download_button = None
            for selector_type, selector in download_selectors:
                try:
                    if selector_type == "CSS":
                        download_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        download_button = self.driver.find_element(By.XPATH, selector)
                    
                    if download_button and download_button.is_displayed():
                        logger.info(f"✅ Found download button")
                        break
                except:
                    continue
            
            if not download_button:
                logger.warning("⚠️ Could not find download button")
                return False
            
            # Click download button
            try:
                download_button.click()
                logger.info("✅ Clicked download button")
            except:
                self.driver.execute_script("arguments[0].click();", download_button)
                logger.info("✅ Clicked download button (JavaScript)")
            
            time.sleep(3)
            
            # Handle popup - look for OK button
            ok_button_selectors = [
                ("ID", "downloadFromEc"),
                ("CSS", "button[onclick*='downloadFromEc']"),
                ("CSS", "#downloadFromEc"),
                ("XPATH", "//button[@id='downloadFromEc']"),
                ("XPATH", "//button[contains(@onclick, 'downloadFromEc')]"),
                ("XPATH", "//button[text()='OK']"),
                ("XPATH", "//button[contains(text(), 'OK')]"),
            ]
            
            ok_button_found = False
            for selector_type, selector in ok_button_selectors:
                try:
                    if selector_type == "CSS":
                        ok_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        ok_button = self.driver.find_element(By.XPATH, selector)
                    elif selector_type == "ID":
                        ok_button = self.driver.find_element(By.ID, selector)
                    
                    if ok_button and ok_button.is_displayed():
                        logger.info(f"✅ Found OK button in popup")
                        
                        try:
                            ok_button.click()
                            logger.info("✅ Clicked OK button in popup")
                        except:
                            self.driver.execute_script("arguments[0].click();", ok_button)
                            logger.info("✅ Clicked OK button in popup (JavaScript)")
                        
                        ok_button_found = True
                        break
                except:
                    continue
            
            if not ok_button_found:
                logger.warning("⚠️ Could not find OK button in popup")
            
            time.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to download results: {str(e)}")
            return False
    
    def run_scraping(self):
        """Execute complete scraping process"""
        logger.info("🚀 Starting TD SYNNEX scraping process")
        
        try:
            if not self.validate_credentials():
                raise Exception("Invalid credentials")
            
            if not self.initialize_browser():
                raise Exception("Browser initialization failed")
            
            if not self.login_to_portal():
                raise Exception("Login failed")
            
            if not self.navigate_to_download_page():
                raise Exception("Navigation failed")
            
            if not self.apply_microsoft_filters():
                raise Exception("Filter application failed")
            
            if not self.download_results():
                raise Exception("Download request failed")
            
            logger.info("✅ Scraping process completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Scraping process failed: {str(e)}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🔒 Browser closed")
            except:
                pass
        
        # Clean up temporary directory
        try:
            shutil.rmtree(self.temp_dir)
            logger.info("🧹 Temporary files cleaned up")
        except:
            pass

@app.function_name(name="TDSynnexScraper")
@app.route(route="scrape", auth_level=func.AuthLevel.FUNCTION)
def scrape_tdsynnex(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to scrape TD SYNNEX Microsoft products
    """
    logging.info('🚀 TD SYNNEX Scraper function triggered')
    
    try:
        # Parse request body
        try:
            req_body = req.get_json()
            test_mode = req_body.get('test', False) if req_body else False
        except:
            test_mode = False
        
        # If test mode, return credentials check
        if test_mode:
            username = os.environ.get('TDSYNNEX_USERNAME')
            password = os.environ.get('TDSYNNEX_PASSWORD')
            
            if not username or not password:
                return func.HttpResponse(
                    json.dumps({
                        "error": "Missing TD SYNNEX credentials",
                        "message": "Please configure TDSYNNEX_USERNAME and TDSYNNEX_PASSWORD in Function App settings"
                    }),
                    status_code=400,
                    mimetype="application/json"
                )
            
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": "TD SYNNEX scraper is deployed and credentials are configured",
                    "timestamp": datetime.utcnow().isoformat(),
                    "credentials_found": True,
                    "username": username[:3] + "***" if username else None
                }),
                status_code=200,
                mimetype="application/json"
            )
        
        # Run actual scraping
        scraper = AzureTDSynnexScraper()
        success = scraper.run_scraping()
        
        if success:
            result = {
                "status": "success",
                "message": "TD SYNNEX scraping completed successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "scraping_completed": True
            }
        else:
            result = {
                "status": "error",
                "message": "TD SYNNEX scraping failed",
                "timestamp": datetime.utcnow().isoformat(),
                "scraping_completed": False
            }
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200 if success else 500,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"❌ Function failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Function failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.function_name(name="HealthCheck")
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "TD SYNNEX Scraper",
            "version": "1.0.0"
        }),
        status_code=200,
        mimetype="application/json"
    )