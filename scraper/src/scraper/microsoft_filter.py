"""
Microsoft product filtering using keyword matching and basic ML
"""

import logging
import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

class MicrosoftProductFilter:
    """Filter and identify Microsoft products using keyword matching and basic ML"""
    
    def __init__(self):
        self.microsoft_keywords = [
            'microsoft', 'surface', 'xbox', 'office', 'windows', 'azure',
            'dynamics', 'teams', 'outlook', 'sharepoint', 'onedrive',
            'power bi', 'power apps', 'power automate', 'power platform',
            'visual studio', 'sql server', 'exchange', 'intune',
            'defender', 'sentinel', 'fabric', 'copilot', 'hololens'
        ]
        # Initialize TF-IDF vectorizer for text similarity
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
        self.keyword_vectors = self.vectorizer.fit_transform(self.microsoft_keywords)
        
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
        
        # Semantic similarity check using TF-IDF
        if product_name:
            try:
                product_vector = self.vectorizer.transform([product_name])
                similarities = cosine_similarity(product_vector, self.keyword_vectors)
                
                # If similarity score > 0.3 with any Microsoft keyword
                if np.max(similarities) > 0.3:
                    return True
            except Exception as e:
                logger.warning(f"Similarity check failed: {str(e)}")
        
        return False
    
    async def apply_filters(self, browser) -> List[Dict]:
        """Apply Microsoft product filters on the TD SYNNEX portal"""
        
        try:
            # Step 1: Use manufacturer filter search box to narrow down results
            await self._apply_manufacturer_filter(browser)
            
            # Step 2: Select Microsoft manufacturer checkboxes
            await self._select_microsoft_checkboxes(browser)
            
            # Step 3: Apply form field settings
            await self._apply_form_settings(browser)
            
            # Step 4: Trigger search
            await self._trigger_search(browser)
            
            # Step 5: Get all filtered products
            products = await self._extract_product_list(browser)
            
            # Step 6: Additional NLP filtering to ensure we catch everything
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
    
    async def _apply_manufacturer_filter(self, browser):
        """Apply manufacturer filter search box to narrow down results"""
        logger.info("Looking for manufacturer filter search box...")
        
        try:
            filter_selectors = [
                ("CSS", "input.filter-icon.manufactures-filter.float-right"),
                ("CSS", "input[class*='manufactures-filter']"),
                ("CSS", "input[placeholder*='Enter keywords to filter']"),
            ]
            
            manufacturer_filter_input = None
            for selector_type, selector in filter_selectors:
                try:
                    if selector_type == "CSS":
                        manufacturer_filter_input = browser.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if manufacturer_filter_input and manufacturer_filter_input.is_displayed():
                        logger.info(f"Found manufacturer filter input using {selector_type}: {selector}")
                        break
                except:
                    continue
            
            if manufacturer_filter_input:
                # Clear and type "Microsoft" in the filter
                manufacturer_filter_input.clear()
                manufacturer_filter_input.send_keys("Microsoft")
                logger.info("Typed 'Microsoft' in manufacturer filter")
                
                # Wait for the filter to apply
                await asyncio.sleep(2)
                
                # Press Enter to trigger the filter
                try:
                    manufacturer_filter_input.send_keys(Keys.RETURN)
                    logger.info("Pressed Enter to apply filter")
                except:
                    pass
                
                await asyncio.sleep(1)
            else:
                logger.warning("Could not find manufacturer filter input box")
                
        except Exception as e:
            logger.error(f"Error using manufacturer filter: {e}")
    
    async def _select_microsoft_checkboxes(self, browser):
        """Select all Microsoft manufacturer checkboxes"""
        logger.info("Looking for Microsoft manufacturer checkboxes...")
        
        try:
            # Find the manufacturer section
            manufacturer_sections = [
                ("ID", "realtimeManufacturer"),
                ("ID", "manufacturer"),
                ("CSS", "div[id*='manufacturer']"),
            ]
            
            manufacturer_div = None
            for selector_type, selector in manufacturer_sections:
                try:
                    if selector_type == "ID":
                        manufacturer_div = browser.driver.find_element(By.ID, selector)
                    elif selector_type == "CSS":
                        manufacturer_div = browser.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if manufacturer_div:
                        logger.info(f"Found manufacturer section using {selector_type}: {selector}")
                        break
                except:
                    continue
            
            if manufacturer_div:
                # Find all checkboxes within this div
                manufacturer_checkboxes = manufacturer_div.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                logger.info(f"Found {len(manufacturer_checkboxes)} manufacturer checkboxes")
                
                microsoft_count = 0
                for i, checkbox in enumerate(manufacturer_checkboxes):
                    try:
                        cb_value = checkbox.get_attribute('value') or ''
                        cb_name = checkbox.get_attribute('name') or ''
                        
                        # Check for Microsoft checkboxes
                        is_microsoft_checkbox = False
                        checkbox_type = ""
                        
                        if '19215' in cb_value and cb_name == 'vendNo':
                            is_microsoft_checkbox = True
                            checkbox_type = "vendNo=19215"
                        elif '23073' in cb_value and cb_name == 'mfg':
                            is_microsoft_checkbox = True
                            checkbox_type = "mfg=23073"
                        
                        if is_microsoft_checkbox:
                            logger.info(f"Found Microsoft checkbox: {checkbox_type}")
                            
                            if not checkbox.is_selected():
                                try:
                                    # Try clicking the parent label
                                    parent_label = checkbox.find_element(By.XPATH, "./ancestor::label")
                                    parent_label.click()
                                    logger.info(f"Selected Microsoft checkbox {checkbox_type} (label click)")
                                except:
                                    try:
                                        checkbox.click()
                                        logger.info(f"Selected Microsoft checkbox {checkbox_type} (direct click)")
                                    except:
                                        browser.driver.execute_script("arguments[0].click();", checkbox)
                                        logger.info(f"Selected Microsoft checkbox {checkbox_type} (JS click)")
                                microsoft_count += 1
                            await asyncio.sleep(0.5)
                            continue
                        
                        # Also check for Microsoft text in labels
                        label_text = ''
                        try:
                            parent_label = checkbox.find_element(By.XPATH, "./ancestor::label")
                            label_text = parent_label.text.strip()
                        except:
                            try:
                                sibling_span = checkbox.find_element(By.XPATH, "./following-sibling::span")
                                label_text = sibling_span.text.strip()
                            except:
                                pass
                        
                        # Check if this is a Microsoft checkbox by text
                        search_text = (cb_value + ' ' + cb_name + ' ' + label_text).upper()
                        if any(ms_variant in search_text for ms_variant in ['MICROSOFT', 'MSFT']):
                            logger.info(f"Found Microsoft-related checkbox: '{label_text}'")
                            
                            if not checkbox.is_selected():
                                try:
                                    parent_label = checkbox.find_element(By.XPATH, "./ancestor::label")
                                    parent_label.click()
                                    logger.info(f"Selected Microsoft checkbox: '{label_text}' (label click)")
                                except:
                                    try:
                                        checkbox.click()
                                        logger.info(f"Selected Microsoft checkbox: '{label_text}' (direct click)")
                                    except:
                                        browser.driver.execute_script("arguments[0].click();", checkbox)
                                        logger.info(f"Selected Microsoft checkbox: '{label_text}' (JS click)")
                                microsoft_count += 1
                            await asyncio.sleep(0.5)
                    
                    except Exception as e:
                        logger.debug(f"Error processing manufacturer checkbox {i}: {e}")
                        continue
                
                logger.info(f"Selected {microsoft_count} Microsoft manufacturer checkboxes")
            else:
                logger.error("Could not find manufacturer filter section")
                
        except Exception as e:
            logger.error(f"Failed to select Microsoft checkboxes: {str(e)}")
    
    async def _apply_form_settings(self, browser):
        """Apply form field settings: Short Description, Microsoft Excel, In Stock Only"""
        logger.info("Applying form field settings...")
        
        try:
            # Enable Short Description checkbox
            await self._enable_short_description(browser)
            
            # Set File Format to Microsoft Excel
            await self._set_file_format_excel(browser)
            
            # Skip field delimiter configuration as requested
            
            # Enable In Stock Only checkbox
            await self._enable_in_stock_only(browser)
            
        except Exception as e:
            logger.error(f"Failed to apply form settings: {str(e)}")
    
    async def _enable_short_description(self, browser):
        """Enable Short Description checkbox"""
        logger.info("Enabling Short Description option...")
        
        try:
            short_desc_selectors = [
                ("CSS", "input[name='fields'][value='short_desc']", "Short Description (exact match)"),
                ("XPATH", "//input[@name='fields' and @value='short_desc']", "Short Description XPath"),
            ]
            
            for selector_type, selector, description in short_desc_selectors:
                try:
                    if selector_type == "CSS":
                        element = browser.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        element = browser.driver.find_element(By.XPATH, selector)
                    
                    if element and element.is_displayed():
                        if not element.is_selected():
                            try:
                                parent_label = element.find_element(By.XPATH, "./ancestor::label")
                                parent_label.click()
                                logger.info(f"Enabled Short Description via label: {description}")
                            except:
                                element.click()
                                logger.info(f"Enabled Short Description: {description}")
                            await asyncio.sleep(1)
                            return True
                        else:
                            logger.info(f"Short Description already enabled: {description}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"Short Description selector failed ({description}): {e}")
                    continue
            
            logger.warning("Could not find Short Description option")
            return False
            
        except Exception as e:
            logger.error(f"Failed to enable Short Description: {str(e)}")
            return False
    
    async def _set_file_format_excel(self, browser):
        """Set File Format to Microsoft Excel"""
        logger.info("Setting File Format to Microsoft Excel...")
        
        try:
            excel_selectors = [
                ("CSS", "input[name='fileFormat'][value='xls']", "Microsoft Excel radio button"),
                ("XPATH", "//input[@name='fileFormat' and @value='xls']", "Microsoft Excel XPath"),
                ("ID", "downloadExcel", "Download Excel ID"),
            ]
            
            for selector_type, selector, description in excel_selectors:
                try:
                    if selector_type == "CSS":
                        element = browser.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        element = browser.driver.find_element(By.XPATH, selector)
                    elif selector_type == "ID":
                        element = browser.driver.find_element(By.ID, selector)
                    
                    if element and element.is_displayed():
                        if not element.is_selected():
                            try:
                                parent_label = element.find_element(By.XPATH, "./ancestor::label")
                                parent_label.click()
                                logger.info(f"Selected Microsoft Excel via label: {description}")
                            except:
                                element.click()
                                logger.info(f"Selected Microsoft Excel format: {description}")
                            await asyncio.sleep(1)
                            return True
                        else:
                            logger.info(f"Microsoft Excel format already selected: {description}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"Microsoft Excel selector failed ({description}): {e}")
                    continue
            
            logger.warning("Could not find Microsoft Excel file format option")
            return False
            
        except Exception as e:
            logger.error(f"Failed to set Microsoft Excel format: {str(e)}")
            return False
    
    async def _set_field_delimiter_semicolon(self, browser):
        """Set Field Delimiter to semi-colon"""
        logger.info("Setting Field Delimiter to semi-colon...")
        
        try:
            semicolon_selectors = [
                ("CSS", "input[name='delimiter'][value=';']", "Semi-colon radio button"),
                ("XPATH", "//input[@name='delimiter' and @value=';']", "Semi-colon XPath"),
            ]
            
            for selector_type, selector, description in semicolon_selectors:
                try:
                    if selector_type == "CSS":
                        element = browser.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        element = browser.driver.find_element(By.XPATH, selector)
                    
                    if element and element.is_displayed():
                        if not element.is_selected():
                            try:
                                parent_label = element.find_element(By.XPATH, "./ancestor::label")
                                parent_label.click()
                                logger.info(f"Selected semi-colon via label: {description}")
                            except:
                                element.click()
                                logger.info(f"Selected semi-colon delimiter: {description}")
                            await asyncio.sleep(1)
                            return True
                        else:
                            logger.info(f"Semi-colon delimiter already selected: {description}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"Semi-colon selector failed ({description}): {e}")
                    continue
            
            logger.warning("Could not find semi-colon delimiter option")
            return False
            
        except Exception as e:
            logger.error(f"Failed to set semi-colon delimiter: {str(e)}")
            return False
    
    async def _enable_in_stock_only(self, browser):
        """Enable In Stock Only checkbox"""
        logger.info("Enabling 'In Stock Only' option...")
        
        try:
            in_stock_selectors = [
                ("ID", "inStock", "In Stock Only by ID"),
                ("CSS", "#inStock", "In Stock Only CSS ID"),
                ("CSS", "input[name='inStock']", "In Stock Only CSS name"),
            ]
            
            for selector_type, selector, description in in_stock_selectors:
                try:
                    if selector_type == "ID":
                        element = browser.driver.find_element(By.ID, selector)
                    elif selector_type == "CSS":
                        element = browser.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if element and element.is_displayed():
                        if not element.is_selected():
                            try:
                                parent_label = element.find_element(By.XPATH, "./ancestor::label")
                                parent_label.click()
                                logger.info(f"Enabled 'In Stock Only' via label: {description}")
                            except:
                                element.click()
                                logger.info(f"Enabled 'In Stock Only': {description}")
                            await asyncio.sleep(1)
                            return True
                        else:
                            logger.info(f"'In Stock Only' already enabled: {description}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"In Stock Only selector failed ({description}): {e}")
                    continue
            
            logger.warning("Could not find 'In Stock Only' option")
            return False
            
        except Exception as e:
            logger.error(f"Failed to enable 'In Stock Only': {str(e)}")
            return False
    
    async def _trigger_search(self, browser):
        """Trigger search/filter application"""
        logger.info("Triggering search/filter application...")
        
        try:
            search_button_selectors = [
                ("CSS", "input[type='submit']", "Submit Input"),
                ("CSS", "button[type='submit']", "Submit Button"),
                ("XPATH", "//button[contains(text(), 'Search')]", "Search Button Text"),
                ("XPATH", "//input[@value='Submit']", "Submit Input Value"),
            ]
            
            for selector_type, selector, description in search_button_selectors:
                try:
                    if selector_type == "CSS":
                        button = browser.driver.find_element(By.CSS_SELECTOR, selector)
                    elif selector_type == "XPATH":
                        button = browser.driver.find_element(By.XPATH, selector)
                    
                    if button and button.is_displayed() and button.is_enabled():
                        button.click()
                        logger.info(f"Triggered search: {description}")
                        await asyncio.sleep(3)  # Wait for search results
                        return True
                        
                except Exception as e:
                    logger.debug(f"Search button selector failed ({description}): {e}")
                    continue
            
            logger.warning("Could not find search/submit button")
            return False
            
        except Exception as e:
            logger.error(f"Failed to trigger search: {str(e)}")
            return False
    
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