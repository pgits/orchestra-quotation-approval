"""
Product classifier model for enhanced Microsoft product detection
"""

import logging
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

class ProductClassifier:
    """Product classification using keyword matching and TF-IDF similarity"""
    
    def __init__(self):
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
        
        # Define Microsoft product categories
        self.microsoft_categories = [
            "Microsoft Windows Operating System",
            "Microsoft Office Suite",
            "Microsoft Surface Hardware",
            "Microsoft Xbox Gaming",
            "Microsoft Azure Cloud Services",
            "Microsoft Development Tools",
            "Microsoft Security Products",
            "Microsoft Business Solutions",
            "Microsoft Server Products"
        ]
        
        # Define competitor categories for negative classification
        self.competitor_categories = [
            "Apple Products",
            "Google Products",
            "Amazon Web Services",
            "Oracle Software",
            "IBM Solutions",
            "Adobe Creative Suite",
            "Salesforce CRM",
            "VMware Virtualization"
        ]
        
        # Fit vectorizer with all categories
        all_categories = self.microsoft_categories + self.competitor_categories
        self.category_vectors = self.vectorizer.fit_transform(all_categories)
    
    def classify_product(self, product_info: Dict) -> Tuple[bool, float, str]:
        """
        Classify if a product is Microsoft-related
        
        Returns:
            tuple: (is_microsoft, confidence_score, category)
        """
        
        # Combine product information for classification
        text = f"{product_info.get('name', '')} {product_info.get('description', '')}"
        
        if not text.strip():
            return False, 0.0, "Unknown"
        
        try:
            # Check manufacturer first
            manufacturer = product_info.get('manufacturer', '').lower()
            if 'microsoft' in manufacturer:
                return True, 0.95, "Microsoft Product (Manufacturer)"
            
            # Use TF-IDF similarity for classification
            product_vector = self.vectorizer.transform([text])
            similarities = cosine_similarity(product_vector, self.category_vectors)
            
            # Get top prediction
            top_idx = np.argmax(similarities)
            top_score = similarities[0, top_idx]
            
            all_categories = self.microsoft_categories + self.competitor_categories
            top_label = all_categories[top_idx]
            
            # Check if top prediction is a Microsoft category
            is_microsoft = top_label in self.microsoft_categories
            
            return is_microsoft, float(top_score), top_label
            
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            # Fallback to simple keyword matching
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in ['microsoft', 'windows', 'office', 'xbox', 'surface']):
                return True, 0.7, "Microsoft Product (Keyword Match)"
            return False, 0.0, "Unknown"
    
    def batch_classify(self, products: List[Dict]) -> List[Tuple[Dict, bool, float, str]]:
        """
        Classify multiple products in batch
        
        Returns:
            List of tuples: (product, is_microsoft, confidence, category)
        """
        
        results = []
        
        for product in products:
            is_microsoft, confidence, category = self.classify_product(product)
            results.append((product, is_microsoft, confidence, category))
        
        # Log summary
        microsoft_count = sum(1 for _, is_ms, _, _ in results if is_ms)
        logger.info(f"Batch classification complete: {microsoft_count}/{len(products)} Microsoft products")
        
        return results
    
    def get_high_confidence_microsoft_products(self, products: List[Dict], 
                                             min_confidence: float = 0.8) -> List[Dict]:
        """
        Filter products to only high-confidence Microsoft products
        """
        
        classified = self.batch_classify(products)
        
        high_confidence = [
            product for product, is_microsoft, confidence, _ in classified
            if is_microsoft and confidence >= min_confidence
        ]
        
        logger.info(f"Found {len(high_confidence)} high-confidence Microsoft products")
        return high_confidence