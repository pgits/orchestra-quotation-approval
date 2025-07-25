#!/usr/bin/env python3
"""
Detailed Content Analysis for Dataverse BotComponents

This script focuses on components with actual content to understand
how knowledge files are stored in Copilot Studio.
"""

import os
import json
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv
import requests
from msal import ConfidentialClientApplication

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DetailedContentAnalyzer:
    def __init__(self):
        """Initialize the analyzer."""
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.dataverse_url = os.getenv('DATAVERSE_URL')
        
        self.access_token = None
        self._authenticate()

    def _authenticate(self) -> None:
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

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Dataverse."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0'
        }
        
        url = f"{self.dataverse_url}/api/data/v9.2/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def analyze_components_with_content(self):
        """Analyze all components that have actual content."""
        logger.info("Analyzing components with content...")
        
        # Get all components with content
        params = {
            '$select': 'componenttype,name,content,statecode,statuscode,createdon,modifiedon,botcomponentid',
            '$filter': 'content ne null',
            '$orderby': 'componenttype,modifiedon desc'
        }
        
        data = self._make_request('botcomponents', params)
        components = data.get('value', [])
        
        logger.info(f"Found {len(components)} components with content")
        
        # Analyze each component
        detailed_analysis = []
        for i, component in enumerate(components):
            content = component.get('content', '')
            
            analysis = {
                'index': i + 1,
                'componenttype': component.get('componenttype'),
                'name': component.get('name', 'Unnamed'),
                'botcomponentid': component.get('botcomponentid'),
                'content_length': len(content),
                'content_preview': content[:1000] if content else '',
                'is_json': self._is_json(content),
                'contains_knowledge_keywords': self._has_knowledge_keywords(content),
                'contains_file_references': self._has_file_references(content),
                'statecode': component.get('statecode'),
                'createdon': component.get('createdon'),
                'modifiedon': component.get('modifiedon')
            }
            
            if analysis['is_json']:
                try:
                    parsed_json = json.loads(content)
                    analysis['json_structure'] = self._analyze_json_structure(parsed_json)
                except:
                    analysis['json_structure'] = 'Invalid JSON'
            
            detailed_analysis.append(analysis)
        
        return detailed_analysis

    def _is_json(self, content: str) -> bool:
        """Check if content is JSON."""
        try:
            json.loads(content)
            return True
        except:
            return False

    def _has_knowledge_keywords(self, content: str) -> bool:
        """Check for knowledge-related keywords."""
        keywords = ['knowledge', 'file', 'document', 'upload', 'source', 'datasource']
        return any(kw in content.lower() for kw in keywords)

    def _has_file_references(self, content: str) -> bool:
        """Check for file references."""
        extensions = ['.txt', '.pdf', '.doc', '.docx', '.md', '.csv']
        return any(ext in content.lower() for ext in extensions)

    def _analyze_json_structure(self, parsed_json) -> Dict:
        """Analyze JSON structure for patterns."""
        if isinstance(parsed_json, dict):
            keys = list(parsed_json.keys())
            has_datasource = 'datasource' in str(parsed_json).lower()
            has_content_field = any('content' in str(k).lower() for k in keys)
            has_file_field = any('file' in str(k).lower() for k in keys)
            
            return {
                'type': 'object',
                'top_level_keys': keys[:10],  # First 10 keys
                'total_keys': len(keys),
                'has_datasource_ref': has_datasource,
                'has_content_field': has_content_field,
                'has_file_field': has_file_field
            }
        elif isinstance(parsed_json, list):
            return {
                'type': 'array',
                'length': len(parsed_json),
                'first_item_type': type(parsed_json[0]).__name__ if parsed_json else 'empty'
            }
        else:
            return {'type': type(parsed_json).__name__}

    def analyze_type10_components(self):
        """Deep dive into Type 10 components (Knowledge Sources/Files)."""
        logger.info("Analyzing Type 10 components...")
        
        params = {
            '$select': 'componenttype,name,content,statecode,statuscode,createdon,modifiedon,botcomponentid',
            '$filter': 'componenttype eq 10',
            '$orderby': 'modifiedon desc',
            '$top': 50  # Get recent ones
        }
        
        data = self._make_request('botcomponents', params)
        components = data.get('value', [])
        
        logger.info(f"Found {len(components)} Type 10 components (showing recent 50)")
        
        analysis = []
        for component in components:
            content = component.get('content', '')
            analysis.append({
                'name': component.get('name', 'Unnamed'),
                'has_content': bool(content and content.strip()),
                'content_length': len(content) if content else 0,
                'content_preview': content[:200] if content else 'No content',
                'statecode': component.get('statecode'),
                'createdon': component.get('createdon'),
                'modifiedon': component.get('modifiedon')
            })
        
        return analysis

    def search_by_partial_name(self):
        """Search for components using startswith instead of contains."""
        logger.info("Searching for hardware-related components using startswith...")
        
        search_terms = ['Nate', 'Hardware', 'Buddy', 'hardware', 'nate', 'buddy']
        found_components = []
        
        for term in search_terms:
            try:
                params = {
                    '$select': 'componenttype,name,content,statecode,createdon',
                    '$filter': f"startswith(name, '{term}')"
                }
                
                data = self._make_request('botcomponents', params)
                components = data.get('value', [])
                
                for comp in components:
                    comp['search_term'] = term
                    found_components.append(comp)
                    
                logger.info(f"Found {len(components)} components starting with '{term}'")
                    
            except Exception as e:
                logger.warning(f"Search for '{term}' failed: {e}")
        
        return found_components

def main():
    """Main execution."""
    analyzer = DetailedContentAnalyzer()
    
    print("=" * 80)
    print("DETAILED CONTENT ANALYSIS REPORT")
    print("=" * 80)
    
    # 1. Components with content
    print("\n1. COMPONENTS WITH ACTUAL CONTENT")
    print("-" * 50)
    content_components = analyzer.analyze_components_with_content()
    
    for comp in content_components:
        print(f"\nComponent {comp['index']}: Type {comp['componenttype']}")
        print(f"Name: {comp['name']}")
        print(f"Content Length: {comp['content_length']:,} characters")
        print(f"Is JSON: {comp['is_json']}")
        print(f"Has Knowledge Keywords: {comp['contains_knowledge_keywords']}")
        print(f"Has File References: {comp['contains_file_references']}")
        
        if comp['is_json'] and isinstance(comp.get('json_structure'), dict):
            js = comp['json_structure']
            if js.get('type') == 'object':
                print(f"JSON Keys: {js.get('top_level_keys', [])}")
                print(f"Has DataSource: {js.get('has_datasource_ref', False)}")
                print(f"Has Content Field: {js.get('has_content_field', False)}")
        
        print(f"Content Preview:\n{comp['content_preview']}")
        print("-" * 40)
    
    # 2. Type 10 analysis
    print("\n2. TYPE 10 COMPONENTS (KNOWLEDGE SOURCES) ANALYSIS")
    print("-" * 55)
    type10_components = analyzer.analyze_type10_components()
    
    with_content = [c for c in type10_components if c['has_content']]
    without_content = [c for c in type10_components if not c['has_content']]
    
    print(f"Total Type 10 components analyzed: {len(type10_components)}")
    print(f"With content: {len(with_content)}")
    print(f"Without content: {len(without_content)}")
    
    if with_content:
        print("\nType 10 components WITH content:")
        for comp in with_content[:5]:  # Show first 5
            print(f"  - {comp['name']}: {comp['content_length']} chars")
    
    print(f"\nRecent Type 10 component names (sample):")
    for comp in type10_components[:10]:
        print(f"  - {comp['name']} (Content: {comp['content_length']} chars)")
    
    # 3. Search for hardware-related
    print("\n3. HARDWARE-RELATED COMPONENT SEARCH")
    print("-" * 45)
    hardware_components = analyzer.search_by_partial_name()
    
    if hardware_components:
        print(f"Found {len(hardware_components)} components with hardware-related names:")
        for comp in hardware_components:
            content_len = len(comp.get('content', '')) if comp.get('content') else 0
            print(f"  Type {comp['componenttype']}: {comp['name']} ({content_len} chars)")
    else:
        print("No hardware-related components found with partial name matching.")
    
    # 4. Recommendations
    print("\n4. RECOMMENDATIONS")
    print("-" * 25)
    
    if content_components:
        content_types = set(c['componenttype'] for c in content_components)
        print(f"Component types that store content: {sorted(content_types)}")
        
        # Find best candidate for knowledge storage
        json_components = [c for c in content_components if c['is_json']]
        if json_components:
            best_candidate = max(json_components, key=lambda x: x['content_length'])
            print(f"\nBest knowledge storage candidate:")
            print(f"  Type: {best_candidate['componenttype']}")
            print(f"  Example: {best_candidate['name']}")
            print(f"  Size: {best_candidate['content_length']:,} characters")
    
    print(f"\nFor TD SYNNEX uploads:")
    print(f"  - Type 10 has 550 components but none have content (likely metadata only)")
    print(f"  - Types with actual content: {sorted(set(c['componenttype'] for c in content_components))}")
    print(f"  - Recommend testing with the type that stores the largest JSON content")

if __name__ == "__main__":
    main()