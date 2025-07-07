"""
Tests for Microsoft product classifier
"""

import pytest
from unittest.mock import Mock, patch
from src.models.product_classifier import ProductClassifier


class TestProductClassifier:
    
    @pytest.fixture
    def classifier(self):
        with patch('src.models.product_classifier.pipeline'):
            return ProductClassifier()
    
    def test_classify_product_microsoft_manufacturer(self, classifier):
        """Test classification with Microsoft as manufacturer"""
        
        product = {
            "name": "Random Product",
            "manufacturer": "Microsoft Corporation",
            "description": "Some product"
        }
        
        is_microsoft, confidence, category = classifier.classify_product(product)
        
        assert is_microsoft is True
        assert confidence >= 0.95
    
    def test_classify_product_microsoft_in_name(self, classifier):
        """Test classification with Microsoft in product name"""
        
        # Mock the classifier pipeline
        mock_result = {
            'labels': ['Microsoft Office Suite', 'Apple Products'],
            'scores': [0.85, 0.15]
        }
        
        classifier.classifier = Mock()
        classifier.classifier.return_value = mock_result
        
        product = {
            "name": "Microsoft Office 365",
            "manufacturer": "Unknown",
            "description": "Productivity suite"
        }
        
        is_microsoft, confidence, category = classifier.classify_product(product)
        
        assert is_microsoft is True
        assert confidence == 0.85
        assert category == 'Microsoft Office Suite'
    
    def test_classify_product_non_microsoft(self, classifier):
        """Test classification of non-Microsoft product"""
        
        # Mock the classifier pipeline
        mock_result = {
            'labels': ['Apple Products', 'Microsoft Surface Hardware'],
            'scores': [0.90, 0.10]
        }
        
        classifier.classifier = Mock()
        classifier.classifier.return_value = mock_result
        
        product = {
            "name": "MacBook Pro",
            "manufacturer": "Apple Inc.",
            "description": "Laptop computer"
        }
        
        is_microsoft, confidence, category = classifier.classify_product(product)
        
        assert is_microsoft is False
        assert confidence == 0.90
        assert category == 'Apple Products'
    
    def test_classify_product_empty_input(self, classifier):
        """Test classification with empty product info"""
        
        product = {
            "name": "",
            "manufacturer": "",
            "description": ""
        }
        
        is_microsoft, confidence, category = classifier.classify_product(product)
        
        assert is_microsoft is False
        assert confidence == 0.0
        assert category == "Unknown"
    
    def test_classify_product_fallback_keyword_match(self, classifier):
        """Test fallback to keyword matching on classifier failure"""
        
        # Make classifier raise exception
        classifier.classifier = Mock()
        classifier.classifier.side_effect = Exception("Model error")
        
        product = {
            "name": "Windows 11 Professional",
            "manufacturer": "Unknown",
            "description": "Operating system"
        }
        
        is_microsoft, confidence, category = classifier.classify_product(product)
        
        assert is_microsoft is True
        assert confidence == 0.7
        assert category == "Microsoft Product (Keyword Match)"
    
    def test_batch_classify(self, classifier):
        """Test batch classification of multiple products"""
        
        # Mock the classifier pipeline
        classifier.classifier = Mock()
        classifier.classifier.side_effect = [
            {'labels': ['Microsoft Surface Hardware'], 'scores': [0.95]},
            {'labels': ['Apple Products'], 'scores': [0.88]},
            {'labels': ['Microsoft Xbox Gaming'], 'scores': [0.92]}
        ]
        
        products = [
            {"name": "Surface Pro 9", "manufacturer": "Microsoft"},
            {"name": "iPad Pro", "manufacturer": "Apple"},
            {"name": "Xbox Series S", "manufacturer": "Microsoft"}
        ]
        
        results = classifier.batch_classify(products)
        
        assert len(results) == 3
        
        # Check first product (Surface)
        assert results[0][1] is True  # is_microsoft
        assert results[0][2] == 0.95  # confidence
        
        # Check second product (iPad)
        assert results[1][1] is False  # is_microsoft
        assert results[1][2] == 0.88  # confidence
        
        # Check third product (Xbox)
        assert results[2][1] is True  # is_microsoft
        assert results[2][2] == 0.92  # confidence
    
    def test_get_high_confidence_microsoft_products(self, classifier):
        """Test filtering for high confidence Microsoft products"""
        
        # Mock batch_classify
        classifier.batch_classify = Mock()
        classifier.batch_classify.return_value = [
            ({"name": "Surface Pro"}, True, 0.95, "Microsoft Surface Hardware"),
            ({"name": "MacBook"}, False, 0.90, "Apple Products"),
            ({"name": "Office 365"}, True, 0.85, "Microsoft Office Suite"),
            ({"name": "Windows 11"}, True, 0.75, "Microsoft Windows OS"),  # Below threshold
            ({"name": "iPhone"}, False, 0.88, "Apple Products")
        ]
        
        products = [
            {"name": "Surface Pro"},
            {"name": "MacBook"},
            {"name": "Office 365"},
            {"name": "Windows 11"},
            {"name": "iPhone"}
        ]
        
        high_confidence = classifier.get_high_confidence_microsoft_products(
            products, min_confidence=0.8
        )
        
        assert len(high_confidence) == 2
        assert high_confidence[0]["name"] == "Surface Pro"
        assert high_confidence[1]["name"] == "Office 365"


if __name__ == "__main__":
    pytest.main([__file__])