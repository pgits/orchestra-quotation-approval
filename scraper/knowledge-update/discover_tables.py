#!/usr/bin/env python3
"""
Simple script to discover what tables actually exist in the Dataverse environment.
"""

import os
import logging
from dotenv import load_dotenv
import requests
from msal import ConfidentialClientApplication

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TableDiscoverer:
    def __init__(self):
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.dataverse_url = os.getenv('DATAVERSE_URL')
        
        self.access_token = None
        self._authenticate()

    def _authenticate(self):
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
        scope = [f"{self.dataverse_url}/.default"]
        result = app.acquire_token_for_client(scopes=scope)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            logger.info("Authentication successful")
        else:
            raise Exception(f"Auth failed: {result.get('error_description')}")

    def discover_through_metadata(self):
        """Try to discover tables through the $metadata endpoint."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/xml'
        }
        
        try:
            url = f"{self.dataverse_url}/api/data/v9.2/$metadata"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse XML to find EntitySets
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            # Find all EntitySet elements
            entitysets = []
            for elem in root.iter():
                if 'EntitySet' in elem.tag:
                    name = elem.get('Name')
                    if name:
                        entitysets.append(name)
            
            return sorted(entitysets)
            
        except Exception as e:
            logger.error(f"Metadata discovery failed: {e}")
            return []

    def test_common_tables(self):
        """Test access to common Dataverse tables."""
        common_tables = [
            'systemuser', 'account', 'contact', 'lead', 'opportunity',
            'botcomponents', 'bot', 'botcomponentcollection',
            'msdyn_kmfederatedsearchconfigs', 'msdyn_kmpersonalizationsettings',
            'knowledgearticles', 'annotations', 'msdyn_conversationdatas',
            'msdyn_aiodimages', 'msdyn_dataflows'
        ]
        
        accessible_tables = []
        
        for table in common_tables:
            try:
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Accept': 'application/json',
                    'OData-MaxVersion': '4.0'
                }
                
                url = f"{self.dataverse_url}/api/data/v9.2/{table}"
                params = {'$top': 1}  # Just get one record to test access
                
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    record_count = len(data.get('value', []))
                    accessible_tables.append((table, record_count, 'accessible'))
                elif response.status_code == 404:
                    accessible_tables.append((table, 0, 'not_found'))
                else:
                    accessible_tables.append((table, 0, f'error_{response.status_code}'))
                    
            except Exception as e:
                accessible_tables.append((table, 0, f'exception: {str(e)[:50]}'))
        
        return accessible_tables

def main():
    discoverer = TableDiscoverer()
    
    print("=" * 60)
    print("DATAVERSE TABLE DISCOVERY")
    print("=" * 60)
    
    # Method 1: Metadata discovery
    print("\n1. METADATA-BASED DISCOVERY")
    print("-" * 30)
    
    entitysets = discoverer.discover_through_metadata()
    if entitysets:
        print(f"Found {len(entitysets)} entity sets:")
        
        # Group by category
        bot_related = [e for e in entitysets if 'bot' in e.lower()]
        knowledge_related = [e for e in entitysets if any(k in e.lower() for k in ['knowledge', 'km', 'copilot'])]
        file_related = [e for e in entitysets if any(f in e.lower() for f in ['file', 'document', 'annotation', 'attachment'])]
        
        print(f"\nBot-related ({len(bot_related)}):")
        for entity in bot_related[:10]:
            print(f"  - {entity}")
        
        print(f"\nKnowledge-related ({len(knowledge_related)}):")
        for entity in knowledge_related[:10]:
            print(f"  - {entity}")
        
        print(f"\nFile-related ({len(file_related)}):")
        for entity in file_related[:10]:
            print(f"  - {entity}")
        
        print(f"\nOther entities (first 20):")
        other = [e for e in entitysets if e not in bot_related + knowledge_related + file_related]
        for entity in other[:20]:
            print(f"  - {entity}")
    else:
        print("No entity sets discovered through metadata")
    
    # Method 2: Test common tables
    print(f"\n2. TESTING COMMON TABLE ACCESS")
    print("-" * 35)
    
    accessible = discoverer.test_common_tables()
    
    working_tables = [t for t in accessible if t[2] == 'accessible']
    not_found = [t for t in accessible if t[2] == 'not_found']
    errors = [t for t in accessible if not t[2] in ['accessible', 'not_found']]
    
    print(f"\nAccessible tables ({len(working_tables)}):")
    for table, count, status in working_tables:
        print(f"  - {table}: {status}")
    
    print(f"\nNot found ({len(not_found)}):")
    for table, count, status in not_found[:10]:
        print(f"  - {table}")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for table, count, status in errors[:5]:
            print(f"  - {table}: {status}")
    
    # Final recommendations
    print(f"\n3. RECOMMENDATIONS")
    print("-" * 20)
    
    if working_tables:
        print("Available tables for knowledge storage testing:")
        for table, count, status in working_tables:
            print(f"  - {table}")
        
        print("\nNext steps:")
        print("1. Focus on 'botcomponents' table (confirmed working)")
        print("2. Test knowledge upload using component type 0 (stores largest content)")
        print("3. If metadata discovery worked, explore bot/knowledge related entities")
    else:
        print("Limited table access. Recommend using Copilot Studio UI for uploads.")

if __name__ == "__main__":
    main()