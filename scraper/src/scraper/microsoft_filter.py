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