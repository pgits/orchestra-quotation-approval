#!/usr/bin/env python3
"""
Analyze Dataverse datasources table to understand how knowledge files are stored.

Based on the botcomponents analysis, Type 10 components appear to be metadata
that reference actual content stored in datasources.
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

class DataSourceAnalyzer:
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

    def list_all_tables(self):
        """List all available tables to understand the schema."""
        logger.info("Discovering available tables...")
        
        try:
            # Get entity definitions
            params = {
                '$select': 'LogicalName,DisplayName,IsCustomEntity',
                '$filter': 'IsValidForAdvancedFind eq true',
                '$orderby': 'LogicalName'
            }
            
            data = self._make_request('EntityDefinitions', params)
            entities = data.get('value', [])
            
            knowledge_related = []
            bot_related = []
            file_related = []
            
            for entity in entities:
                name = entity.get('LogicalName', '').lower()
                display_name = entity.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', '')
                
                if any(term in name for term in ['knowledge', 'file', 'document', 'datasource', 'source']):
                    knowledge_related.append((entity.get('LogicalName'), display_name))
                elif any(term in name for term in ['bot', 'copilot', 'chat']):
                    bot_related.append((entity.get('LogicalName'), display_name))
                elif any(term in name for term in ['attachment', 'blob', 'content']):
                    file_related.append((entity.get('LogicalName'), display_name))
            
            return {
                'total_entities': len(entities),
                'knowledge_related': knowledge_related,
                'bot_related': bot_related,
                'file_related': file_related,
                'all_entities': [(e.get('LogicalName'), e.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', '')) for e in entities[:50]]
            }
            
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return None

    def analyze_specific_tables(self):
        """Analyze specific tables that might contain knowledge data."""
        tables_to_check = [
            'msdyn_kmpersonalizationsetting',
            'msdyn_kmfederatedsearchconfig', 
            'msdyn_knowledgearticleimage',
            'msdyn_kbattachment',
            'knowledgearticle',
            'msdyn_copilotknowledgeinteraction',
            'msdyn_copilotknowledgesource',
            'annotation',  # Common attachment table
            'msdyn_dataflow',
            'msdyn_aiodimage',
            'msdyn_conversationdata'
        ]
        
        results = {}
        
        for table in tables_to_check:
            try:
                logger.info(f"Analyzing table: {table}")
                
                # Get basic info about the table
                params = {
                    '$top': 10,
                    '$orderby': 'createdon desc'
                }
                
                data = self._make_request(table, params)
                records = data.get('value', [])
                
                if records:
                    # Analyze first record to understand structure
                    first_record = records[0]
                    fields = list(first_record.keys())
                    
                    # Look for content or file-related fields
                    content_fields = [f for f in fields if any(term in f.lower() for term in ['content', 'data', 'file', 'document', 'body', 'text'])]
                    
                    results[table] = {
                        'total_records': len(records),
                        'sample_fields': fields[:20],  # First 20 fields
                        'content_fields': content_fields,
                        'has_content': bool(content_fields)
                    }
                else:
                    results[table] = {
                        'total_records': 0,
                        'sample_fields': [],
                        'content_fields': [],
                        'has_content': False
                    }
                    
            except Exception as e:
                logger.warning(f"Could not analyze table {table}: {e}")
                results[table] = {'error': str(e)}
        
        return results

    def search_for_hardware_content(self):
        """Search across multiple tables for hardware-related content."""
        search_tables = [
            'knowledgearticle',
            'annotation', 
            'msdyn_conversationdata',
            'msdyn_copilotknowledgeinteraction'
        ]
        
        hardware_findings = {}
        
        for table in search_tables:
            try:
                logger.info(f"Searching {table} for hardware content...")
                
                # Try different field names that might contain searchable text
                search_fields = ['subject', 'title', 'content', 'description', 'filename', 'documentbody']
                
                for field in search_fields:
                    try:
                        params = {
                            '$select': f'{field},createdon,modifiedon',
                            '$filter': f"{field} ne null",
                            '$top': 10
                        }
                        
                        data = self._make_request(table, params)
                        records = data.get('value', [])
                        
                        # Check for hardware-related content
                        hardware_records = []
                        for record in records:
                            field_value = str(record.get(field, '')).lower()
                            if any(term in field_value for term in ['hardware', 'nate', 'buddy', 'td synnex', 'synnex']):
                                hardware_records.append({
                                    'field': field,
                                    'value_preview': str(record.get(field, ''))[:200],
                                    'createdon': record.get('createdon'),
                                    'full_record_fields': list(record.keys())
                                })
                        
                        if hardware_records:
                            if table not in hardware_findings:
                                hardware_findings[table] = []
                            hardware_findings[table].extend(hardware_records)
                            
                    except Exception as e:
                        continue  # Field might not exist in this table
                        
            except Exception as e:
                logger.warning(f"Could not search table {table}: {e}")
        
        return hardware_findings

def main():
    """Main execution."""
    analyzer = DataSourceAnalyzer()
    
    print("=" * 80)
    print("DATAVERSE DATASOURCES & KNOWLEDGE STORAGE ANALYSIS")
    print("=" * 80)
    
    # 1. Discover available tables
    print("\n1. DISCOVERING AVAILABLE TABLES")
    print("-" * 40)
    
    table_info = analyzer.list_all_tables()
    if table_info:
        print(f"Total entities discovered: {table_info['total_entities']}")
        
        print(f"\nKnowledge-related tables ({len(table_info['knowledge_related'])}):")
        for table, display_name in table_info['knowledge_related']:
            print(f"  - {table}: {display_name}")
        
        print(f"\nBot-related tables ({len(table_info['bot_related'])}):")
        for table, display_name in table_info['bot_related']:
            print(f"  - {table}: {display_name}")
        
        print(f"\nFile-related tables ({len(table_info['file_related'])}):")
        for table, display_name in table_info['file_related']:
            print(f"  - {table}: {display_name}")
    
    # 2. Analyze specific tables
    print("\n2. ANALYZING SPECIFIC KNOWLEDGE TABLES")
    print("-" * 45)
    
    table_analysis = analyzer.analyze_specific_tables()
    
    tables_with_content = []
    for table, info in table_analysis.items():
        if isinstance(info, dict) and info.get('has_content'):
            tables_with_content.append((table, info))
    
    print(f"Tables with potential content fields: {len(tables_with_content)}")
    
    for table, info in tables_with_content:
        print(f"\n{table}:")
        print(f"  Records: {info['total_records']}")
        print(f"  Content fields: {info['content_fields']}")
        if len(info['sample_fields']) > 0:
            print(f"  Sample fields: {info['sample_fields'][:10]}")
    
    # 3. Search for hardware content
    print("\n3. SEARCHING FOR HARDWARE-RELATED CONTENT")
    print("-" * 45)
    
    hardware_findings = analyzer.search_for_hardware_content()
    
    if hardware_findings:
        print("Found hardware-related content in:")
        for table, records in hardware_findings.items():
            print(f"\n{table} ({len(records)} matches):")
            for record in records[:3]:  # Show first 3 matches
                print(f"  Field: {record['field']}")
                print(f"  Preview: {record['value_preview'][:150]}...")
                print(f"  Created: {record.get('createdon', 'Unknown')}")
                print(f"  Available fields: {record['full_record_fields'][:10]}")
                print()
    else:
        print("No hardware-related content found in searchable tables.")
    
    # 4. Final recommendations
    print("\n4. RECOMMENDATIONS FOR KNOWLEDGE UPLOAD")
    print("-" * 45)
    
    if tables_with_content:
        print("Recommended approach for TD SYNNEX file uploads:")
        print("1. Primary targets:")
        for table, info in tables_with_content[:3]:
            print(f"   - {table}: {len(info['content_fields'])} content fields")
        
        print("\n2. Upload strategy:")
        print("   - Test with 'knowledgearticle' table if available (standard knowledge)")
        print("   - Use 'annotation' table for file attachments")
        print("   - Consider 'msdyn_copilotknowledgesource' for Copilot-specific content")
        
        print("\n3. Content structure:")
        print("   - Use JSON format for structured data")
        print("   - Include metadata fields like title, description")
        print("   - Reference bot component ID for association")
    else:
        print("No clear content storage tables identified.")
        print("Recommend manual inspection of Copilot Studio interface for upload mechanism.")

if __name__ == "__main__":
    main()