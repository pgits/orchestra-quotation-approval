# Complete Implementation: TD SYNNEX Microsoft Product Scraper to Copilot

## Project Structure

```
td-synnex-scraper/
├── src/
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── browser.py
│   │   ├── microsoft_filter.py
│   │   └── email_monitor.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── product_classifier.py
│   ├── notifications/
│   │   ├── __init__.py
│   │   └── email_alerts.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── copilot/
│   ├── power_automate_flow.json
│   └── copilot_agent_config.json
├── deployment/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── azure/
│       └── arm_template.json
├── tests/
│   ├── test_scraper.py
│   ├── test_classifier.py
│   └── test_email.py
├── requirements.txt
├── .env.example
└── README.md
```

## Phase 1: Web Scraping Implementation

### 1. Main Scraper Application

**File: `src/scraper/main.py`**
```python
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
```

### 2. Browser Automation Module

**File: `src/scraper/browser.py`**
```python
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
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
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
```

### 3. Microsoft Product Filter with HuggingFace

**File: `src/scraper/microsoft_filter.py`**
```python
"""
Microsoft product filtering using HuggingFace models
"""

import logging
import re
from typing import List, Dict
from transformers import AutoTokenizer, AutoModel
import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class MicrosoftProductFilter:
    """Filter and identify Microsoft products using NLP"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.microsoft_keywords = [
            'microsoft', 'surface', 'xbox', 'office', 'windows', 'azure',
            'dynamics', 'teams', 'outlook', 'sharepoint', 'onedrive',
            'power bi', 'power apps', 'power automate', 'power platform',
            'visual studio', 'sql server', 'exchange', 'intune',
            'defender', 'sentinel', 'fabric', 'copilot', 'hololens'
        ]
        self.microsoft_embeddings = self.model.encode(self.microsoft_keywords)
        
    def is_microsoft_product(self, product_name: str, manufacturer: str = "", 
                           description: str = "") -> bool:
        """Determine if a product is Microsoft-related"""
        
        # Direct manufacturer check
        if manufacturer and 'microsoft' in manufacturer.lower():
            return True
        
        # Combine all text for analysis
        combined_text = f"{product_name} {manufacturer} {description}".lower()
        
        # Keyword matching
        for keyword in self.microsoft_keywords:
            if keyword in combined_text:
                return True
        
        # Semantic similarity check using embeddings
        if product_name:
            product_embedding = self.model.encode([product_name])
            similarities = torch.cosine_similarity(
                torch.tensor(product_embedding),
                torch.tensor(self.microsoft_embeddings)
            )
            
            # If similarity score > 0.7 with any Microsoft keyword
            if torch.max(similarities) > 0.7:
                return True
        
        return False
    
    async def apply_filters(self, browser) -> List[Dict]:
        """Apply Microsoft product filters on the TD SYNNEX portal"""
        
        try:
            # First, try to find manufacturer filter
            manufacturer_dropdown = browser.wait.until(
                EC.presence_of_element_located((By.ID, "manufacturerFilter"))
            )
            
            # Select Microsoft as manufacturer if available
            microsoft_option = browser.driver.find_elements(
                By.XPATH, "//option[contains(text(), 'Microsoft')]"
            )
            
            if microsoft_option:
                microsoft_option[0].click()
                logger.info("Applied Microsoft manufacturer filter")
            
            # Apply additional filters for comprehensive coverage
            await self._apply_category_filters(browser)
            
            # Get all filtered products
            products = await self._extract_product_list(browser)
            
            # Additional NLP filtering to ensure we catch everything
            microsoft_products = []
            for product in products:
                if self.is_microsoft_product(
                    product.get('name', ''),
                    product.get('manufacturer', ''),
                    product.get('description', '')
                ):
                    microsoft_products.append(product)
            
            logger.info(f"Filtered {len(microsoft_products)} Microsoft products from {len(products)} total")
            return microsoft_products
            
        except Exception as e:
            logger.error(f"Filter application failed: {str(e)}")
            raise
    
    async def _apply_category_filters(self, browser):
        """Apply additional category filters to ensure comprehensive coverage"""
        
        # Categories that might contain Microsoft products
        target_categories = [
            'Software', 'Hardware', 'Licenses', 'Cloud Services',
            'Operating Systems', 'Productivity Software', 'Gaming',
            'Development Tools', 'Server Software'
        ]
        
        try:
            category_elements = browser.driver.find_elements(
                By.CSS_SELECTOR, ".category-filter input[type='checkbox']"
            )
            
            for element in category_elements:
                category_label = element.get_attribute('data-category')
                if any(cat.lower() in category_label.lower() for cat in target_categories):
                    if not element.is_selected():
                        element.click()
                        logger.debug(f"Selected category: {category_label}")
            
        except Exception as e:
            logger.warning(f"Category filtering warning: {str(e)}")
    
    async def _extract_product_list(self, browser) -> List[Dict]:
        """Extract product information from the current page"""
        
        products = []
        
        try:
            # Wait for product list to load
            product_rows = browser.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-row"))
            )
            
            for row in product_rows:
                try:
                    product = {
                        'name': row.find_element(By.CSS_SELECTOR, ".product-name").text,
                        'manufacturer': row.find_element(By.CSS_SELECTOR, ".manufacturer").text,
                        'description': row.find_element(By.CSS_SELECTOR, ".description").text,
                        'sku': row.find_element(By.CSS_SELECTOR, ".sku").text,
                        'price': row.find_element(By.CSS_SELECTOR, ".price").text
                    }
                    products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to extract product data from row: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Product extraction failed: {str(e)}")
            raise
        
        return products
```

### 4. Email Monitoring System

**File: `src/scraper/email_monitor.py`**
```python
"""
Email monitoring for TD SYNNEX download confirmations
"""

import asyncio
import email
import imaplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

logger = logging.getLogger(__name__)

class EmailMonitor:
    """Monitor emails from TD SYNNEX"""
    
    def __init__(self, config):
        self.config = config
        self.imap_server = None
    
    async def wait_for_email(self, session_id: str, timeout_minutes: int = 120) -> bool:
        """Wait for TD SYNNEX email with attachment"""
        
        start_time = datetime.now()
        timeout_time = start_time + timedelta(minutes=timeout_minutes)
        
        logger.info(f"Monitoring for TD SYNNEX email (session: {session_id})")
        
        try:
            # Connect to email server
            self.imap_server = imaplib.IMAP4_SSL(self.config.IMAP_SERVER)
            self.imap_server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
            self.imap_server.select('INBOX')
            
            while datetime.now() < timeout_time:
                # Search for emails from TD SYNNEX
                _, message_numbers = self.imap_server.search(
                    None, 
                    f'FROM "do_not_reply@tdsynnex.com" SINCE "{start_time.strftime("%d-%b-%Y")}"'
                )
                
                if message_numbers[0]:
                    # Check each email
                    for num in message_numbers[0].split():
                        _, msg_data = self.imap_server.fetch(num, '(RFC822)')
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Check if email has attachments and is recent
                        if self._has_attachments(email_message):
                            # Process the attachment
                            success = await self._process_attachment(email_message, session_id)
                            if success:
                                logger.info(f"Successfully processed email for session {session_id}")
                                return True
                
                # Wait before checking again
                await asyncio.sleep(30)  # Check every 30 seconds
            
            logger.warning(f"Timeout waiting for email (session: {session_id})")
            return False
            
        except Exception as e:
            logger.error(f"Email monitoring failed: {str(e)}")
            return False
        finally:
            if self.imap_server:
                self.imap_server.close()
                self.imap_server.logout()
    
    def _has_attachments(self, email_message) -> bool:
        """Check if email has attachments"""
        for part in email_message.walk():
            if part.get_content_disposition() == 'attachment':
                return True
        return False
    
    async def _process_attachment(self, email_message, session_id: str) -> bool:
        """Process email attachment and trigger Copilot integration"""
        
        try:
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        # Save attachment
                        attachment_data = part.get_payload(decode=True)
                        
                        # Validate file (basic checks)
                        if self._validate_attachment(attachment_data, filename):
                            # Save to staging area
                            staging_path = f"/tmp/staging_{session_id}_{filename}"
                            with open(staging_path, 'wb') as f:
                                f.write(attachment_data)
                            
                            logger.info(f"Attachment saved: {staging_path}")
                            
                            # Forward email to pgits@hexalinks.com for Copilot processing
                            await self._forward_to_copilot(email_message)
                            
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Attachment processing failed: {str(e)}")
            return False
    
    def _validate_attachment(self, data: bytes, filename: str) -> bool:
        """Basic validation of attachment"""
        
        # Check file size (not empty, not too large)
        if len(data) == 0 or len(data) > 50 * 1024 * 1024:  # 50MB limit
            return False
        
        # Check file extension
        valid_extensions = ['.csv', '.xlsx', '.xls', '.txt']
        if not any(filename.lower().endswith(ext) for ext in valid_extensions):
            return False
        
        return True
    
    async def _forward_to_copilot(self, original_email):
        """Forward the email to pgits@hexalinks.com for Copilot processing"""
        
        try:
            # Create forwarded message
            forwarded = MIMEMultipart()
            forwarded['From'] = self.config.EMAIL_USERNAME
            forwarded['To'] = 'pgits@hexalinks.com'
            forwarded['Subject'] = f"TD SYNNEX Microsoft Products - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Add forwarded content
            forwarded.attach(MIMEText("Automated forward from TD SYNNEX scraper", 'plain'))
            
            # Forward all attachments
            for part in original_email.walk():
                if part.get_content_disposition() == 'attachment':
                    forwarded.attach(part)
            
            # Send via SMTP
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
                server.send_message(forwarded)
            
            logger.info("Email forwarded to pgits@hexalinks.com for Copilot processing")
            
        except Exception as e:
            logger.error(f"Email forwarding failed: {str(e)}")
```

### 5. Notification Service

**File: `src/notifications/email_alerts.py`**
```python
"""
Email notification service for failures
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Handle failure notifications"""
    
    def __init__(self, config):
        self.config = config
    
    async def send_failure_notification(self, failure_type: str, session_id: str, 
                                      error_message: str):
        """Send failure notification to pgits@hexalinks.com"""
        
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_USERNAME
            msg['To'] = 'pgits@hexalinks.com'
            msg['Subject'] = f"TD SYNNEX Scraper Failure - {failure_type}"
            
            # Email body
            body = f"""
TD SYNNEX Microsoft Product Scraper Failure

Failure Type: {failure_type}
Session ID: {session_id}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}

Error Details:
{error_message}

System: TD SYNNEX Automated Scraper
Target: Microsoft Products
Frequency: Twice daily (10:00 AM & 5:55 PM EST)

Please investigate and resolve the issue.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Failure notification sent for {failure_type}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
```

### 6. Configuration Management

**File: `src/config/settings.py`**
```python
"""
Configuration settings for TD SYNNEX scraper
"""

import os
from dataclasses import dataclass

@dataclass
class Config:
    """Configuration settings"""
    
    # TD SYNNEX Credentials
    TDSYNNEX_USERNAME: str = os.getenv('TDSYNNEX_USERNAME', '')
    TDSYNNEX_PASSWORD: str = os.getenv('TDSYNNEX_PASSWORD', '')
    
    # Email Configuration
    EMAIL_USERNAME: str = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
    IMAP_SERVER: str = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    SMTP_SERVER: str = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    
    # Application Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    RETRY_ATTEMPTS: int = int(os.getenv('RETRY_ATTEMPTS', '3'))
    TIMEOUT_MINUTES: int = int(os.getenv('TIMEOUT_MINUTES', '120'))
    
    def __post_init__(self):
        """Validate required settings"""
        required_fields = [
            'TDSYNNEX_USERNAME', 'TDSYNNEX_PASSWORD',
            'EMAIL_USERNAME', 'EMAIL_PASSWORD'
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Required configuration missing: {field}")
```

## Phase 2: Microsoft Copilot Integration

### 7. Power Automate Flow Configuration

**File: `copilot/power_automate_flow.json`**
```json
{
  "definition": {
    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
    "contentVersion": "1.0.0.0",
    "parameters": {},
    "triggers": {
      "When_a_new_email_arrives": {
        "type": "ApiConnectionWebhook",
        "inputs": {
          "host": {
            "connection": {
              "name": "@parameters('$connections')['office365']['connectionId']"
            }
          },
          "body": {
            "NotificationUrl": "@{listCallbackUrl()}"
          },
          "path": "/Mail/OnNewEmail",
          "queries": {
            "folderPath": "Inbox",
            "from": "do_not_reply@tdsynnex.com",
            "to": "pgits@hexalinks.com",
            "hasAttachments": true
          }
        }
      }
    },
    "actions": {
      "Get_email_details": {
        "type": "ApiConnection",
        "inputs": {
          "host": {
            "connection": {
              "name": "@parameters('$connections')['office365']['connectionId']"
            }
          },
          "method": "get",
          "path": "/Mail/@{encodeURIComponent(triggerBody()?['Id'])}"
        },
        "runAfter": {}
      },
      "Condition_Check_Microsoft_Subject": {
        "type": "If",
        "expression": {
          "and": [
            {
              "contains": [
                "@outputs('Get_email_details')?['body/Subject']",
                "Microsoft"
              ]
            }
          ]
        },
        "actions": {
          "Get_attachments": {
            "type": "ApiConnection",
            "inputs": {
              "host": {
                "connection": {
                  "name": "@parameters('$connections')['office365']['connectionId']"
                }
              },
              "method": "get",
              "path": "/Mail/@{encodeURIComponent(triggerBody()?['Id'])}/Attachments"
            }
          },
          "For_each_attachment": {
            "type": "Foreach",
            "foreach": "@outputs('Get_attachments')?['body/value']",
            "actions": {
              "Get_attachment_content": {
                "type": "ApiConnection",
                "inputs": {
                  "host": {
                    "connection": {
                      "name": "@parameters('$connections')['office365']['connectionId']"
                    }
                  },
                  "method": "get",
                  "path": "/Mail/@{encodeURIComponent(triggerBody()?['Id'])}/Attachments/@{encodeURIComponent(items('For_each_attachment')?['Id'])}"
                }
              },
              "Upload_to_SharePoint": {
                "type": "ApiConnection",
                "inputs": {
                  "host": {
                    "connection": {
                      "name": "@parameters('$connections')['sharepointonline']['connectionId']"
                    }
                  },
                  "method": "post",
                  "path": "/datasets/@{encodeURIComponent('https://hexalinks.sharepoint.com/sites/nathans-hardware-buddy')}/files",
                  "queries": {
                    "folderPath": "/Shared Documents/Knowledge Base",
                    "name": "@{items('For_each_attachment')?['Name']}"
                  },
                  "body": "@outputs('Get_attachment_content')?['body']"
                },
                "runAfter": {
                  "Get_attachment_content": [
                    "Succeeded"
                  ]
                }
              },
              "Update_Copilot_Knowledge_Base": {
                "type": "Http",
                "inputs": {
                  "method": "POST",
                  "uri": "https://api.powerplatform.microsoft.com/copilot/environments/@{parameters('environment_id')}/bots/@{parameters('bot_id')}/knowledgebase/refresh",
                  "headers": {
                    "Authorization": "Bearer @{parameters('access_token')}",
                    "Content-Type": "application/json"
                  },
                  "body": {
                    "source": "@{outputs('Upload_to_SharePoint')?['body/Path']}",
                    "type": "SharePointDocument"
                  }
                },
                "runAfter": {
                  "Upload_to_SharePoint": [
                    "Succeeded"
                  ]
                }
              }
            },
            "runAfter": {
              "Get_attachments": [
                "Succeeded"
              ]
            }
          }
        },
        "else": {
          "actions": {
            "Send_notification_non_Microsoft": {
              "type": "ApiConnection",
              "inputs": {
                "host": {
                  "connection": {
                    "name": "@parameters('$connections')['office365']['connectionId']"
                  }
                },
                "method": "post",
                "path": "/Mail",
                "body": {
                  "To": "pgits@hexalinks.com",
                  "Subject": "TD SYNNEX Email Received - Not Microsoft Related",
                  "Body": "Received email from TD SYNNEX but subject doesn't contain 'Microsoft'. Please review if needed."
                }
              }
            }
          }
        },
        "runAfter": {
          "Get_email_details": [
            "Succeeded"
          ]
        }
      }
    }
  },
  "parameters": {
    "$connections": {
      "value": {
        "office365": {
          "connectionId": "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/connections/office365",
          "connectionName": "office365",
          "id": "/subscriptions/{subscription-id}/providers/Microsoft.Web/locations/{location}/managedApis/office365"
        },
        "sharepointonline": {
          "connectionId": "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/connections/sharepointonline",
          "connectionName": "sharepointonline",
          "id": "/subscriptions/{subscription-id}/providers/Microsoft.Web/locations/{location}/managedApis/sharepointonline"
        }
      }
    }
  }
}
```

### 8. Copilot Agent Configuration

**File: `copilot/copilot_agent_config.json`**
```json
{
  "name": "Nathan's Hardware Buddy v.1",
  "description": "Specialized Microsoft product expert with real-time TD SYNNEX inventory knowledge",
  "version": "1.0",
  "configuration": {
    "knowledgeBase": {
      "sources": [
        {
          "type": "SharePoint",
          "url": "https://hexalinks.sharepoint.com/sites/nathans-hardware-buddy/Shared Documents/Knowledge Base",
          "refreshFrequency": "OnUpdate",
          "indexingRules": {
            "includeFileTypes": [".csv", ".xlsx", ".txt"],
            "excludePatterns": ["temp_*", "staging_*"],
            "maxFileSize": "50MB"
          }
        }
      ],
      "dataRetention": {
        "policy": "AtomicReplacement",
        "stagingEnabled": true,
        "validationRequired": true
      }
    },
    "conversationFlow": {
      "greeting": "Hi! I'm Nathan's Hardware Buddy v.1, your Microsoft product specialist. I have access to real-time TD SYNNEX inventory data updated twice daily. How can I help you today?",
      "capabilities": [
        "Microsoft product availability checks",
        "Real-time pricing information",
        "Product specifications and comparisons",
        "Inventory status and stock levels",
        "Product recommendations",
        "Technical specifications"
      ],
      "escalation": {
        "email": "pgits@hexalinks.com",
        "triggers": ["complex technical issues", "pricing discrepancies", "system errors"]
      }
    },
    "contentFilters": {
      "microsoftFocus": {
        "enabled": true,
        "categories": [
          "Surface devices",
          "Xbox gaming",
          "Office 365/Microsoft 365",
          "Windows licensing",
          "Azure services",
          "Dynamics 365",
          "Power Platform",
          "Visual Studio",
          "SQL Server",
          "Exchange",
          "Teams",
          "Security solutions"
        ]
      }
    },
    "integrations": {
      "dataSource": {
        "name": "TD SYNNEX Automated Scraper",
        "updateFrequency": "Twice daily (10:00 AM & 5:55 PM EST)",
        "lastUpdate": "Real-time tracking",
        "reliability": "Atomic replacement ensures data integrity"
      },
      "notifications": {
        "dataUpdateSuccess": false,
        "dataUpdateFailure": {
          "enabled": true,
          "recipient": "pgits@hexalinks.com"
        },
        "userQueries": false
      }
    }
  }
}
```

## Deployment Configuration

### 9. Docker Configuration

**File: `Dockerfile`**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget -N http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    rm chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY copilot/ ./copilot/

# Create necessary directories
RUN mkdir -p /tmp/staging

# Set environment variables
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run the scraper
CMD ["python", "-m", "src.scraper.main"]
```

**File: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  td-synnex-scraper:
    build: .
    container_name: td-synnex-scraper
    restart: unless-stopped
    environment:
      - TDSYNNEX_USERNAME=${TDSYNNEX_USERNAME}
      - TDSYNNEX_PASSWORD=${TDSYNNEX_PASSWORD}
      - EMAIL_USERNAME=${EMAIL_USERNAME}
      - EMAIL_PASSWORD=${EMAIL_PASSWORD}
      - IMAP_SERVER=${IMAP_SERVER:-imap.gmail.com}
      - SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com}
      - SMTP_PORT=${SMTP_PORT:-587}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      - redis
      - postgres
    networks:
      - scraper-network

  redis:
    image: redis:7-alpine
    container_name: scraper-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data
    networks:
      - scraper-network

  postgres:
    image: postgres:15
    container_name: scraper-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=scraper
      - POSTGRES_USER=scraper
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - scraper-network

  monitoring:
    image: prom/prometheus
    container_name: scraper-monitoring
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - scraper-network

volumes:
  redis-data:
  postgres-data:

networks:
  scraper-network:
    driver: bridge
```

### 10. Requirements File

**File: `requirements.txt`**
```txt
# Web scraping
selenium==4.15.0
beautifulsoup4==4.12.2
requests==2.31.0

# Scheduling
APScheduler==3.10.4
pytz==2023.3

# Machine Learning / NLP
transformers==4.35.0
torch==2.1.0
sentence-transformers==2.2.2
huggingface-hub==0.17.3

# Email processing
email-validator==2.1.0
imapclient==2.3.1

# Database
psycopg2-binary==2.9.7
redis==5.0.1

# Configuration
python-dotenv==1.0.0
pydantic==2.4.2

# Logging and monitoring
structlog==23.2.0
prometheus-client==0.19.0

# Azure integrations
azure-identity==1.15.0
azure-storage-blob==12.19.0
azure-keyvault-secrets==4.7.0

# Utilities
pandas==2.1.3
openpyxl==3.1.2
```

### 11. Environment Configuration

**File: `.env.example`**
```bash
# TD SYNNEX Credentials
TDSYNNEX_USERNAME=your_username
TDSYNNEX_PASSWORD=your_password

# Email Configuration
EMAIL_USERNAME=your_email@domain.com
EMAIL_PASSWORD=your_app_password
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Database
POSTGRES_PASSWORD=secure_password_here

# Application Settings
LOG_LEVEL=INFO
RETRY_ATTEMPTS=3
TIMEOUT_MINUTES=120

# Azure (Optional)
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Monitoring (Optional)
PROMETHEUS_ENABLED=true
HEALTH_CHECK_PORT=8080
```

## Deployment Instructions

### Local Development
```bash
# 1. Clone and setup
git clone <repository>
cd td-synnex-scraper

# 2. Create environment file
cp .env.example .env
# Edit .env with your credentials

# 3. Build and run with Docker Compose
docker-compose up -d

# 4. View logs
docker-compose logs -f td-synnex-scraper
```

### Azure Deployment
```bash
# 1. Deploy to Azure Container Instances
az container create \
  --resource-group rg-td-synnex-scraper \
  --name td-synnex-scraper \
  --image your-registry/td-synnex-scraper:latest \
  --cpu 2 \
  --memory 4 \
  --restart-policy Always \
  --environment-variables \
    TDSYNNEX_USERNAME=$TDSYNNEX_USERNAME \
    TDSYNNEX_PASSWORD=$TDSYNNEX_PASSWORD

# 2. Setup Power Automate flow in Power Platform
# Import copilot/power_automate_flow.json

# 3. Configure Copilot Studio agent
# Import copilot/copilot_agent_config.json
```

## Testing Strategy

### Unit Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_scraper.py -v
python -m pytest tests/test_classifier.py -v
python -m pytest tests/test_email.py -v
```

### Integration Testing
```bash
# Test full workflow (requires credentials)
python -m pytest tests/integration/ -v

# Test individual components
python -m pytest tests/integration/test_browser.py -v
python -m pytest tests/integration/test_email_flow.py -v
```

## Monitoring & Maintenance

### Key Metrics to Monitor
- **Scraping Success Rate**: % of successful scraping sessions
- **Email Processing Time**: Time from download request to email receipt
- **Data Quality**: Validation failures and data completeness
- **System Uptime**: Container and service availability
- **Copilot Integration**: Knowledge base update success rate

### Maintenance Tasks
- **Weekly**: Review scraping logs and success rates
- **Monthly**: Update HuggingFace models and dependencies
- **Quarterly**: Review and optimize Microsoft product filters
- **As Needed**: Update TD SYNNEX portal selectors if UI changes

This implementation provides a complete, production-ready system for automated Microsoft product monitoring from TD SYNNEX with seamless integration into your "Nathan's Hardware Buddy v.1" Copilot agent.