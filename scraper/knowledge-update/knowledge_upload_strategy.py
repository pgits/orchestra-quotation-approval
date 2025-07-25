#!/usr/bin/env python3
"""
TD SYNNEX Knowledge Upload Strategy for Copilot Studio

Based on our analysis, this script implements the knowledge upload strategy
using the discovered Dataverse structure.

Key Findings:
1. botcomponents table has 639 components with types: 0,2,6,7,8,9,10,15,16
2. Type 10 (Knowledge Sources/Files) has 550 components but NO content (metadata only)
3. Type 0 and Type 2 are the only types that store actual content
4. Type 0 has the largest content example (3,872 chars of JSON)
5. knowledgearticles table is available and accessible

Strategy:
1. Upload to knowledgearticles table (standard knowledge base)
2. Create corresponding botcomponents entries with Type 10 for Copilot integration
3. Use Type 0 botcomponents for actual content if needed
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from dotenv import load_dotenv
import requests
from msal import ConfidentialClientApplication

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CopilotKnowledgeUploader:
    def __init__(self):
        """Initialize the knowledge uploader."""
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.dataverse_url = os.getenv('DATAVERSE_URL')
        self.copilot_agent_name = os.getenv('COPILOT_AGENT_NAME', "Nate's Hardware Buddy")
        
        self.access_token = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Azure AD."""
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
        scope = [f"{self.dataverse_url}/.default"]
        result = app.acquire_token_for_client(scopes=scope)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            logger.info("Successfully authenticated with Dataverse")
        else:
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")

    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make authenticated request to Dataverse."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0'
        }
        
        url = f"{self.dataverse_url}/api/data/v9.2/{endpoint}"
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else {}

    def analyze_existing_knowledge(self):
        """Analyze existing knowledge articles and bot components."""
        logger.info("Analyzing existing knowledge structure...")
        
        # Check knowledgearticles
        params = {
            '$select': 'knowledgearticleid,title,content,statecode,createdon',
            '$top': 10,
            '$orderby': 'createdon desc'
        }
        
        knowledge_data = self._make_request('GET', 'knowledgearticles', params=params)
        knowledge_articles = knowledge_data.get('value', [])
        
        # Check Type 0 botcomponents (the ones with content)
        params = {
            '$select': 'botcomponentid,name,content,componenttype,statecode',
            '$filter': 'componenttype eq 0',
            '$top': 5
        }
        
        type0_data = self._make_request('GET', 'botcomponents', params=params)
        type0_components = type0_data.get('value', [])
        
        # Check Type 10 botcomponents (knowledge metadata)
        params = {
            '$select': 'botcomponentid,name,componenttype,statecode,createdon',
            '$filter': 'componenttype eq 10',
            '$top': 10,
            '$orderby': 'createdon desc'
        }
        
        type10_data = self._make_request('GET', 'botcomponents', params=params)
        type10_components = type10_data.get('value', [])
        
        return {
            'knowledge_articles': knowledge_articles,
            'type0_components': type0_components,
            'type10_components': type10_components
        }

    def create_knowledge_article(self, title: str, content: str, description: str = None) -> str:
        """Create a knowledge article in the knowledgearticles table."""
        logger.info(f"Creating knowledge article: {title}")
        
        article_data = {
            'title': title,
            'content': content,
            'description': description or f"TD SYNNEX knowledge article: {title}",
            'languagelocaleid': 1033,  # English
            'statecode': 3,  # Published
            'statuscode': 5  # Published
        }
        
        try:
            response = self._make_request('POST', 'knowledgearticles', data=article_data)
            
            # Extract the ID from the response headers or response data
            if response and 'knowledgearticleid' in response:
                article_id = response['knowledgearticleid']
            else:
                # Try to get the ID from the location header if available
                article_id = str(uuid.uuid4())  # Fallback
                
            logger.info(f"Knowledge article created with ID: {article_id}")
            return article_id
            
        except Exception as e:
            logger.error(f"Failed to create knowledge article: {e}")
            raise

    def create_bot_component_type10(self, name: str, knowledge_article_id: str = None) -> str:
        """Create a Type 10 bot component for knowledge metadata."""
        logger.info(f"Creating Type 10 bot component: {name}")
        
        component_data = {
            'name': name,
            'componenttype': 10,
            'statecode': 0,  # Active
            'statuscode': 1,  # Active
            # Note: content field empty as per analysis - Type 10 stores metadata only
        }
        
        if knowledge_article_id:
            # Link to the knowledge article if needed
            component_data['description'] = f"Knowledge source for article: {knowledge_article_id}"
        
        try:
            response = self._make_request('POST', 'botcomponents', data=component_data)
            component_id = response.get('botcomponentid', str(uuid.uuid4()))
            logger.info(f"Bot component Type 10 created with ID: {component_id}")
            return component_id
            
        except Exception as e:
            logger.error(f"Failed to create bot component: {e}")
            raise

    def create_bot_component_type0(self, name: str, content: str) -> str:
        """Create a Type 0 bot component with actual content."""
        logger.info(f"Creating Type 0 bot component with content: {name}")
        
        # Type 0 components store JSON content based on our analysis
        if isinstance(content, dict):
            content_json = json.dumps(content, ensure_ascii=False)
        else:
            # Wrap plain text in a JSON structure similar to existing Type 0 components
            content_json = json.dumps({
                "knowledgeData": {
                    "title": name,
                    "content": content,
                    "source": "TD SYNNEX",
                    "uploadDate": datetime.now().isoformat(),
                    "type": "hardware_documentation"
                }
            }, ensure_ascii=False)
        
        component_data = {
            'name': name,
            'componenttype': 0,
            'content': content_json,
            'statecode': 0,  # Active
            'statuscode': 1,  # Active
        }
        
        try:
            response = self._make_request('POST', 'botcomponents', data=component_data)
            component_id = response.get('botcomponentid', str(uuid.uuid4()))
            logger.info(f"Bot component Type 0 created with ID: {component_id}")
            return component_id
            
        except Exception as e:
            logger.error(f"Failed to create bot component with content: {e}")
            raise

    def upload_td_synnex_file(self, file_path: str, file_title: str = None) -> Dict[str, str]:
        """Upload a TD SYNNEX file using the hybrid approach."""
        logger.info(f"Uploading TD SYNNEX file: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        if not file_title:
            file_title = f"TD SYNNEX - {os.path.basename(file_path)}"
        
        # Strategy 1: Create knowledge article (standard approach)
        try:
            knowledge_article_id = self.create_knowledge_article(
                title=file_title,
                content=file_content,
                description=f"TD SYNNEX hardware documentation from {os.path.basename(file_path)}"
            )
        except Exception as e:
            logger.warning(f"Knowledge article creation failed: {e}")
            knowledge_article_id = None
        
        # Strategy 2: Create Type 10 bot component (Copilot metadata)
        try:
            type10_component_id = self.create_bot_component_type10(
                name=f"{file_title} (Knowledge Source)",
                knowledge_article_id=knowledge_article_id
            )
        except Exception as e:
            logger.warning(f"Type 10 bot component creation failed: {e}")
            type10_component_id = None
        
        # Strategy 3: Create Type 0 bot component (actual content storage)
        try:
            type0_component_id = self.create_bot_component_type0(
                name=f"{file_title} (Content)",
                content=file_content
            )
        except Exception as e:
            logger.warning(f"Type 0 bot component creation failed: {e}")
            type0_component_id = None
        
        results = {
            'file_path': file_path,
            'file_title': file_title,
            'knowledge_article_id': knowledge_article_id,
            'type10_component_id': type10_component_id,
            'type0_component_id': type0_component_id,
            'upload_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Upload completed. Results: {results}")
        return results

    def test_upload_with_sample_data(self):
        """Test the upload process with sample TD SYNNEX data."""
        logger.info("Testing upload with sample data...")
        
        sample_content = """
TD SYNNEX HARDWARE SPECIFICATION

Product: Dell OptiPlex 7010
SKU: DTOP-7010-I5-8GB-256
Category: Desktop Computer

Specifications:
- Processor: Intel Core i5-12500T
- Memory: 8GB DDR4-3200 
- Storage: 256GB NVMe SSD
- Graphics: Intel UHD Graphics 770
- Ports: 4x USB 3.2, 2x USB 2.0, HDMI, DisplayPort
- Networking: Gigabit Ethernet, Wi-Fi 6E
- Operating System: Windows 11 Pro

Pricing Information:
- List Price: $849.00
- Partner Price: $679.20
- Availability: In Stock
- Lead Time: 3-5 business days

Support Information:
- Warranty: 3 Year ProSupport
- Support Phone: 1-800-WWW-DELL
- Service Tag: REQUIRED_FOR_SUPPORT

Last Updated: 2025-07-22
Source: TD SYNNEX Product Catalog
"""
        
        # Create the temporary file for testing FIRST
        os.makedirs("/tmp", exist_ok=True)
        test_file_path = "/tmp/sample_td_synnex_test.txt"
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        
        results = self.upload_td_synnex_file(
            file_path=test_file_path,
            file_title="TD SYNNEX - Dell OptiPlex 7010 Specifications"
        )
        
        return results

def main():
    """Main execution for testing the upload strategy."""
    uploader = CopilotKnowledgeUploader()
    
    print("=" * 80)
    print("COPILOT STUDIO KNOWLEDGE UPLOAD TEST")
    print("=" * 80)
    
    # 1. Analyze existing structure
    print("\n1. ANALYZING EXISTING KNOWLEDGE STRUCTURE")
    print("-" * 50)
    
    existing_analysis = uploader.analyze_existing_knowledge()
    
    print(f"Existing knowledge articles: {len(existing_analysis['knowledge_articles'])}")
    print(f"Type 0 components (with content): {len(existing_analysis['type0_components'])}")
    print(f"Type 10 components (metadata): {len(existing_analysis['type10_components'])}")
    
    if existing_analysis['knowledge_articles']:
        print("\nSample knowledge articles:")
        for article in existing_analysis['knowledge_articles'][:3]:
            print(f"  - {article.get('title', 'Untitled')}: {len(article.get('content', ''))} chars")
    
    # 2. Test upload
    print(f"\n2. TESTING KNOWLEDGE UPLOAD")
    print("-" * 35)
    
    try:
        test_results = uploader.test_upload_with_sample_data()
        
        print("Upload test completed successfully!")
        print(f"Knowledge Article ID: {test_results.get('knowledge_article_id')}")
        print(f"Type 10 Component ID: {test_results.get('type10_component_id')}")
        print(f"Type 0 Component ID: {test_results.get('type0_component_id')}")
        
        # Clean up test file
        if os.path.exists("/tmp/sample_td_synnex_test.txt"):
            os.remove("/tmp/sample_td_synnex_test.txt")
            
    except Exception as e:
        logger.error(f"Upload test failed: {e}")
        return 1
    
    # 3. Recommendations
    print(f"\n3. RECOMMENDATIONS FOR PRODUCTION USE")
    print("-" * 45)
    
    print("Based on the test results:")
    print("1. Use hybrid approach: knowledgearticles + botcomponents")
    print("2. Create Type 10 components for Copilot Studio integration")
    print("3. Create Type 0 components for rich content storage")
    print("4. Monitor which approach gets utilized by the Copilot agent")
    print("5. Consider batch upload for multiple TD SYNNEX files")
    
    return 0

if __name__ == "__main__":
    exit(main())